"""
AI Agent API 路由

提供 AI Agent 任务执行接口,支持工具调用、任务规划和结果存储。
使用 LangGraph 构建工作流,实现智能任务执行。

主要功能:
- 创建和执行 AI Agent 任务
- 工具调用和管理
- 任务规划和执行结果存储
- 与 LangGraph 工作流集成
"""
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

from backend.models import Task, AgentTask, AgentResult
# from backend.task_executor import task_executor  <-- Moved inside functions to avoid circular import
from backend.ai_agents.core.graph import create_agent_graph, initialize_tools
from backend.ai_agents.core.state import AgentState
from backend.api.task_utils import handle_task_error
import uuid
from pathlib import Path
import datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Agent"])

# 初始化 Agent 图和工具
agent_graph = create_agent_graph()
initialize_tools()


class APIResponse(BaseModel):
    """统一API响应模型"""
    code: int = Field(..., description="状态码", ge=100, le=599)
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")

class ToolDef(BaseModel):
    """
    工具定义模型
    
    Attributes:
        name: 工具名称
        args: 工具参数,字典格式
        description: 工具描述
    """
    name: str
    args: Dict[str, Any]
    description: str


class AgentRequest(BaseModel):
    """
    Agent 请求模型
    
    Attributes:
        tools: 可用工具列表
        memory_info: 记忆信息,用于上下文传递
        user_requirement: 用户需求描述
    """
    tools: List[ToolDef]
    memory_info: str = ""
    user_requirement: str


@router.post("/run", response_model=APIResponse)
async def run_agent(request: AgentRequest):
    """
    执行 AI Agent 任务 (异步后台执行)
    
    流程:
    1. 创建任务记录(Task表)
    2. 提交到 TaskExecutor 后台队列
    3. 立即返回任务ID
    
    Args:
        request: Agent 请求,包含工具列表和用户需求
        
    Returns:
        APIResponse: 包含任务ID
    """
    # Import locally to avoid circular import
    from backend.task_executor import task_executor
    
    try:
        logger.info(f"🤖 接收到 Agent 任务请求: {request.user_requirement[:50]}...")
        
        # 1. 准备配置
        target = "unknown"
        if request.tools:
            # 尝试从工具参数中获取目标
            for tool in request.tools:
                if "target" in tool.args:
                    target = tool.args["target"]
                    break
        
        scan_config = {
            "user_tools": [t.dict() for t in request.tools],
            "user_requirement": request.user_requirement,
            "memory_info": request.memory_info,
            "target": target
        }
        
        # 2. 创建任务记录 (使用统一的 Task 模型)
        task = await Task.create(
            task_name=f"AI Agent: {request.user_requirement[:20]}...",
            task_type="ai_agent_scan",
            target=target,
            status="pending",
            config=json.dumps(scan_config, ensure_ascii=False),
            progress=0
        )
        
        # 3. 提交到执行器
        await task_executor.start_task(
            task_id=task.id,
            target=target,
            scan_config=scan_config
        )
        
        logger.info(f"✅ Agent 任务已提交: {task.id}")
        
        return APIResponse(
            code=200,
            message="任务已提交后台执行",
            data={
                "task_id": task.id,
                "status": "pending"
            }
        )
    except Exception as e:
        logger.error(f"提交 Agent 任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")

# --- 新增核心功能接口 (Terminal#184-191) ---

class HeartbeatRequest(BaseModel):
    timestamp: float

class FinishRequest(BaseModel):
    exitCode: int
    stdout: str
    stderr: str

@router.delete("/task/{task_id}", response_model=APIResponse)
async def delete_task(task_id: int):
    """
    删除任务 (幂等)
    
    1. 如果任务正在运行，先强制中止
    2. 删除任务记录
    """
    # Import locally to avoid circular import
    from backend.task_executor import task_executor
    
    try:
        task = await Task.get_or_none(id=task_id)
        if not task:
            return APIResponse(code=200, message="任务不存在或已删除")
        
        # 如果正在运行，先中止
        if task.status == 'running':
            task_executor.abort_task(task_id)
            # 等待一小会儿让进程清理? 这里的逻辑主要是触发abort
        
        await task.delete()
        logger.info(f"任务 {task_id} 已删除")
        
        return APIResponse(code=200, message="任务删除成功")
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return APIResponse(code=500, message=f"删除任务失败: {str(e)}")

@router.post("/task/{task_id}/abort", response_model=APIResponse)
async def abort_task_endpoint(task_id: int):
    """
    中止任务
    
    发送终止信号，5s后强制Kill
    """
    # Import locally to avoid circular import
    from backend.task_executor import task_executor
    
    try:
        task = await Task.get_or_none(id=task_id)
        if not task:
            return APIResponse(code=404, message="任务不存在")
            
        if task.status not in ['running', 'pending', 'queued']:
             return APIResponse(code=200, message=f"任务当前状态({task.status})无需中止")

        task_executor.abort_task(task_id)
        
        # 更新状态为 aborted (task_executor 也会做，但这里立即响应)
        task.status = 'aborted'
        await task.save()
        
        return APIResponse(code=200, message="中止指令已发送")
    except Exception as e:
        logger.error(f"中止任务失败: {e}")
        return APIResponse(code=500, message=f"中止任务失败: {str(e)}")

@router.put("/task/{task_id}/plugin/{plugin_id}/heartbeat", response_model=APIResponse)
async def heartbeat(task_id: int, plugin_id: str, request: HeartbeatRequest):
    """
    插件心跳上报
    """
    # Import locally to avoid circular import
    from backend.task_executor import task_executor
    
    try:
        task_executor.update_heartbeat(task_id)
        return APIResponse(code=200, message="Heartbeat received")
    except Exception as e:
        # 心跳失败不应阻塞插件，但需记录
        logger.warning(f"Heartbeat update failed: {e}")
        return APIResponse(code=500, message="Heartbeat failed")

@router.post("/task/{task_id}/plugin/{plugin_id}/finish", response_model=APIResponse)
async def finish_plugin(task_id: int, plugin_id: str, request: FinishRequest):
    """
    插件执行完成回调
    """
    try:
        task = await Task.get_or_none(id=task_id)
        if not task:
            return APIResponse(code=404, message="Task not found")
        
        if request.exitCode == 0:
            task.status = 'completed'
            task.progress = 100
            # 尝试解析 stdout 为 JSON 结果
            try:
                task.result = request.stdout # 已经是 JSON string
            except:
                task.result = json.dumps({"raw_output": request.stdout})
        else:
            task.status = 'failed'
            task.result = json.dumps({"error": request.stderr or "Unknown error", "exit_code": request.exitCode})
            
        await task.save()
        logger.info(f"任务 {task_id} 回调完成: {task.status}")
        return APIResponse(code=200, message="Finish processed")
    except Exception as e:
        logger.error(f"Finish callback failed: {e}")
        return APIResponse(code=500, message=f"Finish callback failed: {str(e)}")

@router.get("/task/{task_id}/logs", response_model=APIResponse)
async def get_task_logs(task_id: int, tail: int = 500, keyword: str = ""):
    """
    获取任务的插件日志 (2.3)
    支持 tail 和 keyword 过滤
    """
    try:
        task = await Task.get_or_none(id=task_id)
        if not task:
            return APIResponse(code=404, message="Task not found")
        
        # Log location pattern: logs/plugins/{date}/{task_id}.log
        log_date = task.created_at.strftime("%Y-%m-%d")
        log_file = Path("logs") / "plugins" / log_date / f"{task_id}.log"
        
        if not log_file.exists():
            # Fallback search
            files = list(Path("logs").glob(f"plugins/*/{task_id}.log"))
            if files:
                log_file = files[0]
            else:
                return APIResponse(code=200, message="暂无日志", data="")

        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            if keyword:
                lines = [l for l in lines if keyword.lower() in l.lower()]
                
            if len(lines) > tail:
                lines = lines[-tail:]
                
            return APIResponse(code=200, message="获取成功", data="".join(lines))
        except Exception as e:
            return APIResponse(code=500, message=f"读取日志失败: {e}")
            
    except Exception as e:
        return APIResponse(code=500, message=f"获取日志失败: {str(e)}")

@router.get("/tasks/frozen", response_model=APIResponse)
async def get_frozen_tasks():
    """
    获取冻结任务列表 (4.3)
    冻结定义: 运行中 且 运行时长 > 80% 阈值
    """
    try:
        running_tasks = await Task.filter(status='running').all()
        frozen_tasks = []
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Thresholds (minutes)
        TIMEOUTS = {
            'scan_port': 15,
            'scan_waf': 5,
            'awvs_scan': 60,
            'default': 30
        }
        
        for task in running_tasks:
            if not task.created_at: continue
            
            created_at = task.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=datetime.timezone.utc)
                
            duration_minutes = (now - created_at).total_seconds() / 60
            threshold = TIMEOUTS.get(task.task_type, TIMEOUTS['default'])
            
            if duration_minutes > (threshold * 0.8):
                frozen_tasks.append({
                    "id": task.id,
                    "task_name": task.task_name,
                    "task_type": task.task_type,
                    "duration": f"{duration_minutes:.1f}",
                    "threshold": threshold,
                    "progress": task.progress
                })
                
        return APIResponse(code=200, message="获取成功", data=frozen_tasks)
    except Exception as e:
        logger.error(f"Get frozen tasks error: {e}")
        return APIResponse(code=500, message=f"获取冻结任务失败: {str(e)}")

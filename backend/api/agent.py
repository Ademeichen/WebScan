"""
AI Agent API 路由

提供 AI Agent 任务执行接口，支持工具调用、任务规划和结果存储。
使用 LangGraph 构建工作流，实现智能任务执行。

主要功能：
- 创建和执行 AI Agent 任务
- 工具调用和管理
- 任务规划和执行结果存储
- 与 LangGraph 工作流集成
"""
import json
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from models import AgentTask, AgentResult
from agent.core import agent_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI Agent"])


class ToolDef(BaseModel):
    """
    工具定义模型
    
    Attributes:
        name: 工具名称
        args: 工具参数，字典格式
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
        memory_info: 记忆信息，用于上下文传递
        user_requirement: 用户需求描述
    """
    tools: List[ToolDef]
    memory_info: str = ""
    user_requirement: str


@router.post("/run")
async def run_agent(request: AgentRequest):
    """
    执行 AI Agent 任务
    
    流程：
    1. 创建任务记录并保存到数据库
    2. 调用 LangGraph 工作流执行任务
    3. 保存执行结果到数据库
    
    工作流包括：
    - 规划节点：根据用户需求和可用工具生成执行计划
    - 执行节点：按照计划依次调用工具
    - 总结节点：汇总执行结果
    
    Args:
        request: Agent 请求，包含工具列表和用户需求
        
    Returns:
        Dict: 包含任务ID和执行结果的响应，结构如下:
            {
                "task_id": "任务ID",
                "data": {
                    "plan": "执行计划",
                    "results": ["执行结果列表"]
                }
            }
        
    Raises:
        HTTPException: 任务执行失败时抛出 500 错误
        
    Examples:
        >>> 执行简单的代码执行任务
        >>> {
        ...     "tools": [{
        ...         "name": "execute_code",
        ...         "args": {"code": "print('Hello')"},
        ...         "description": "执行Python代码"
        ...     }],
        ...     "user_requirement": "打印 Hello"
        ... }
    """
    try:
        logger.info(f"🤖 开始执行 Agent 任务: {request.user_requirement[:50]}...")
        
        # 1. 创建任务记录
        task_obj = await AgentTask.create(
            input_json=json.dumps(request.dict(), ensure_ascii=False),
            task_type="general",
            status="running"
        )
        
        # 2. 构建初始状态
        initial_state = {
            "user_tools": [t.dict() for t in request.tools],
            "user_requirement": request.user_requirement,
            "memory_info": request.memory_info,
            "plan_data": None,
            "execution_results": []
        }
        
        # 3. 调用 LangGraph 工作流执行任务
        final_state = await agent_app.ainvoke(initial_state)
        
        # 4. 构建最终输出
        final_output = {
            "plan": final_state.get("plan_data"),
            "results": final_state.get("execution_results")
        }

        # 5. 保存执行结果
        await AgentResult.create(
            task=task_obj,
            final_output=json.dumps(final_output, ensure_ascii=False)
        )
        
        # 6. 更新任务状态
        await task_obj.update_from_dict({"status": "completed"})
        await task_obj.save()
        
        logger.info(f"✅ Agent 任务执行完成: {task_obj.task_id}")
        
        return {
            "task_id": str(task_obj.task_id),
            "data": final_output
        }
    except Exception as e:
        logger.error(f"❌ Agent 任务执行失败: {str(e)}")
        if 'task_obj' in locals():
            await task_obj.update_from_dict({"status": "failed"})
            await task_obj.save()
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {str(e)}")


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_agent_task(task_id: str):
    """
    获取 Agent 任务详情
    
    根据任务 ID 获取任务的详细信息，包括输入、状态和执行结果。
    
    Args:
        task_id: 任务 ID
        
    Returns:
        Dict: 包含任务详细信息的响应，结构如下:
            {
                "task_id": "任务ID",
                "input_json": "输入JSON",
                "task_type": "任务类型",
                "status": "任务状态",
                "final_output": "执行结果",
                "created_at": "创建时间",
                "updated_at": "更新时间"
            }
        
    Raises:
        HTTPException: 当任务不存在时抛出 404 错误
        
    Examples:
        >>> 获取任务详情
        >>> GET /agent/tasks/123
    """
    try:
        task = await AgentTask.get_or_none(task_id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {
            "task_id": task.task_id,
            "input_json": task.input_json,
            "task_type": task.task_type,
            "status": task.status,
            "final_output": task.final_output,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 Agent 任务详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=Dict[str, Any])
async def list_agent_tasks(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    获取 Agent 任务列表
    
    支持按状态过滤和分页查询。
    
    Args:
        status: 按任务状态过滤，可选值: 'pending', 'running', 'completed', 'failed'
        page: 页码，从 1 开始
        page_size: 每页数量
        
    Returns:
        Dict: 包含任务列表和分页信息的响应，结构如下:
            {
                "tasks": [...],
                "total": 总数,
                "page": 当前页,
                "page_size": 每页数量,
                "total_pages": 总页数
            }
        
    Examples:
        >>> 获取所有运行中的任务
        >>> GET /agent/tasks?status=running
    """
    try:
        query = AgentTask.all()
        
        if status:
            query = query.filter(status=status)
        
        total = await query.count()
        
        tasks = await query \
            .order_by("-created_at") \
            .offset((page - 1) * page_size) \
            .limit(page_size)
        
        task_list = []
        for task in tasks:
            task_list.append({
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": task.status,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            })
        
        return {
            "tasks": task_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        logger.error(f"获取 Agent 任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

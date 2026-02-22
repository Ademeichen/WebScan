"""
AI Agents API 路由

提供Agent扫描任务的API接口。
"""
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from uuid import uuid4

from backend.models import Task, AgentResult, AgentTask
from backend.api.common import APIResponse
from backend.task_executor import task_executor
from ..core.state import AgentState
from ..core.graph import create_agent_graph
from ..code_execution.executor import UnifiedExecutor
from ..code_execution.environment import EnvironmentAwareness
from ..code_execution.code_generator import CodeGenerator
from ..code_execution.capability_enhancer import CapabilityEnhancer
from ..agent_config import agent_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai_agents", tags=["AI Agents"])


class AgentScanRequest(BaseModel):
    """
    Agent扫描请求模型
    
    Attributes:
        target: 扫描目标(URL/IP)
        enable_llm_planning: 是否启用LLM增强规划
        custom_tasks: 自定义任务列表(可选)
        need_custom_scan: 是否需要自定义扫描
        custom_scan_type: 自定义扫描类型
        custom_scan_requirements: 自定义扫描需求
        custom_scan_language: 自定义扫描语言
        need_capability_enhancement: 是否需要功能补充
        capability_requirement: 功能补充需求
    """
    target: str
    enable_llm_planning: Optional[bool] = None
    custom_tasks: Optional[list] = None
    need_custom_scan: Optional[bool] = False
    custom_scan_type: Optional[str] = None
    custom_scan_requirements: Optional[str] = None
    custom_scan_language: Optional[str] = "python"
    need_capability_enhancement: Optional[bool] = False
    capability_requirement: Optional[str] = None


class AgentScanResponse(BaseModel):
    """
    Agent扫描响应模型
    
    Attributes:
        task_id: 任务ID
        status: 任务状态
        message: 响应消息
    """
    task_id: str
    status: str
    message: str


class CodeGenerationRequest(BaseModel):
    """
    代码生成请求模型
    """
    scan_type: str
    target: str
    requirements: str = ""
    language: str = "python"
    additional_params: Dict[str, Any] = {}


class CodeExecutionRequest(BaseModel):
    """
    代码执行请求模型
    """
    code: str
    language: str = "python"
    target: Optional[str] = None


class CapabilityEnhancementRequest(BaseModel):
    """
    功能补充请求模型
    """
    requirement: str
    target: str
    capability_name: Optional[str] = None


# 内存级任务存储
agent_tasks: Dict[str, Dict[str, Any]] = {}


@router.post("/scan", response_model=AgentScanResponse)
async def start_agent_scan(
    request: AgentScanRequest,
    background_tasks: BackgroundTasks
):
    """
    启动Agent扫描任务
    
    创建Agent任务并在后台执行扫描工作流。
    """
    try:
        # 1. 构造扫描配置
        scan_config = request.dict()
        logger.info(f"[AI_AGENT] [INIT] 构造扫描配置 - 模块: API, 变量: scan_config, 值: {scan_config}")
        
        # 2. 更新全局配置 (如果需要)
        if request.enable_llm_planning is not None:
            old_value = agent_config.ENABLE_LLM_PLANNING
            agent_config.ENABLE_LLM_PLANNING = request.enable_llm_planning
            logger.info(f"[AI_AGENT] [CONFIG] 更新LLM规划配置 - 模块: API, 变量: ENABLE_LLM_PLANNING, 旧值: {old_value}, 新值: {request.enable_llm_planning}, 状态: updated")
            
        # 3. 创建任务记录 (Unified Task Model)
        task_obj = await Task.create(
            task_name=f"AI Agent Scan {request.target}",
            task_type="ai_agent_scan",
            target=request.target,
            status="pending",
            progress=0,
            config=json.dumps(scan_config, ensure_ascii=False)
        )
        
        task_id = task_obj.id
        logger.info(f"[AI_AGENT] [TASK_CREATE] 创建任务记录 - 模块: API, 变量: task_id, 值: {task_id}, 状态: created")
        
        # 4. 提交到任务执行器 (串行队列)
        await task_executor.start_task(
            task_id=task_id,
            target=request.target,
            scan_config=scan_config
        )
        
        logger.info(f"[AI_AGENT] [TASK_SUBMIT] 任务已提交到队列 - 模块: API, 变量: task_id, 值: {task_id}, 目标: {request.target}, 状态: queued")
        
        return AgentScanResponse(
            task_id=str(task_id),
            status="pending",
            message="Agent扫描任务已提交到队列"
        )
        
    except Exception as e:
        logger.error(f"[AI_AGENT] [ERROR] 启动Agent任务失败 - 模块: API, 错误: {str(e)}, 堆栈: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail=f"启动Agent任务失败: {str(e)}"
        )


async def _run_agent_task(task_id: str, initial_state: AgentState):
    """
    后台执行Agent任务
    
    Args:
        task_id: 任务ID
        initial_state: 初始状态
    """
    try:
        logger.info(f"🚀 开始执行Agent任务: {task_id}")
        
        # 创建Agent图并执行
        agent_graph = create_agent_graph()
        final_state = await agent_graph.invoke(initial_state)
        
        # 生成最终报告
        final_report = final_state.tool_results.get("final_report", {})
        
        # 保存执行结果到数据库
        await AgentResult.create(
            task=await AgentTask.get(task_id=task_id),
            final_output=json.dumps(final_report, ensure_ascii=False),
            execution_time=final_report.get("duration", 0)
        )
        
        # 更新任务状态
        task_obj = await AgentTask.get(task_id=task_id)
        await task_obj.update_from_dict({"status": "completed"})
        await task_obj.save()
        
        # 更新内存任务状态
        if task_id in agent_tasks:
            agent_tasks[task_id].update({
                "status": "completed",
                "result": final_report,
                "completed_at": asyncio.get_event_loop().time(),
                "progress": 100
            })
        
        logger.info(f"✅ Agent任务执行完成: {task_id}")
        
    except Exception as e:
        logger.error(f"❌ Agent任务执行失败 {task_id}: {str(e)}")
        
        # 更新任务状态为失败
        try:
            task_obj = await AgentTask.get(task_id=task_id)
            await task_obj.update_from_dict({"status": "failed"})
            await task_obj.save()
            
            # 保存错误结果
            await AgentResult.create(
                task=task_obj,
                final_output=json.dumps({"error": str(e)}, ensure_ascii=False),
                error_message=str(e)
            )
        except Exception as db_error:
            logger.error(f"❌ 更新数据库失败: {str(db_error)}")
        
        # 更新内存任务状态
        if task_id in agent_tasks:
            agent_tasks[task_id].update({
                "status": "failed",
                "error": str(e),
                "completed_at": asyncio.get_event_loop().time()
            })


@router.get("/tasks/{task_id}", response_model=APIResponse)
async def get_agent_task(task_id: str):
    """
    获取Agent任务详情
    """
    try:
        logger.info(f"[AI_AGENT] [TASK_DETAIL_START] 获取Agent任务详情 - 模块: API, 变量: task_id, 值: {task_id}")
        
        # 尝试转换为int (兼容 Task ID)
        db_task_id = None
        if task_id.isdigit():
            db_task_id = int(task_id)
            logger.info(f"[AI_AGENT] [TASK_DETAIL_CONVERT] Task ID转换 - 模块: API, 变量: task_id, 旧值: {task_id}, 新值: {db_task_id}")
            
        # 先从内存中获取
        if task_id in agent_tasks:
            task_info = agent_tasks[task_id]
            logger.info(f"[AI_AGENT] [TASK_DETAIL_MEMORY] 从内存获取任务信息 - 模块: API, 变量: task_id, 状态: found, 数据: {task_info}")
            return {
                "task_id": task_id,
                "target": task_info.get("target"),
                "status": task_info.get("status"),
                "progress": task_info.get("progress", 0),
                "created_at": task_info.get("created_at"),
                "completed_at": task_info.get("completed_at"),
                "result": task_info.get("result"),
                "error": task_info.get("error")
            }
        
        # 从数据库获取 (使用 Unified Task Model)
        task = None
        if db_task_id:
            logger.info(f"[AI_AGENT] [TASK_DETAIL_DB] 从数据库获取任务 - 模块: API, 变量: db_task_id, 状态: querying")
            task = await Task.get_or_none(id=db_task_id)
            
        # 如果找不到且 task_id 是 UUID 格式，尝试查找 AgentTask (兼容旧数据)
        if not task and len(task_id) > 20:
            logger.info(f"[AI_AGENT] [TASK_DETAIL_LEGACY] 尝试查找AgentTask - 模块: API, 变量: task_id, 状态: querying")
            task = await AgentTask.get_or_none(task_id=task_id)
            if task:
                logger.info(f"[AI_AGENT] [TASK_DETAIL_LEGACY_FOUND] 找到AgentTask - 模块: API, 变量: task_id, 状态: found")
                # 旧模型适配
                result = await AgentResult.get_or_none(task=task)
                return {
                    "task_id": str(task.task_id),
                    "input_json": task.input_json,
                    "task_type": task.task_type,
                    "status": task.status,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "final_output": result.final_output if result else None,
                    "execution_time": result.execution_time if result else None,
                    "error_message": result.error_message if result else None
                }
            else:
                logger.info(f"[AI_AGENT] [TASK_DETAIL_LEGACY_NOT_FOUND] AgentTask不存在 - 模块: API, 变量: task_id, 状态: not_found")
        
        if not task:
            logger.error(f"[AI_AGENT] [TASK_DETAIL_NOT_FOUND] 任务不存在 - 模块: API, 变量: task_id, 值: {task_id}, 状态: error")
            raise HTTPException(status_code=404, detail="任务不存在")
        
        logger.info(f"[AI_AGENT] [TASK_DETAIL_FOUND] 找到任务 - 模块: API, 变量: task_id, 值: {task.id}, 状态: {task.status}")
        
        # 返回 Task 模型数据
        return {
            "task_id": str(task.id),
            "task_type": task.task_type,
            "target": task.target,
            "status": task.status,
            "progress": task.progress,
            "config": task.config,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "final_output": task.result,
            "error_message": task.error_message
        }
        
    except HTTPException as http_ex:
        logger.error(f"[AI_AGENT] [ERROR] 获取Agent任务详情HTTP异常 - 模块: API, 错误: {str(http_ex)}")
        raise
    except Exception as e:
        logger.error(f"[AI_AGENT] [ERROR] 获取Agent任务详情失败 - 模块: API, 错误: {str(e)}, 堆栈: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_agent_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    获取Agent任务列表
    """
    try:
        logger.info(f"[AI_AGENT] [TASK_LIST_START] 获取Agent任务列表 - 模块: API, 参数: status={status}, task_type={task_type}, page={page}, page_size={page_size}")
        
        # 查询 Unified Task Model, 过滤 ai_agent_scan 类型
        query = Task.filter(task_type="ai_agent_scan")
        
        if status:
            query = query.filter(status=status)
            logger.info(f"[AI_AGENT] [TASK_LIST_FILTER] 应用状态过滤 - 模块: API, 过滤条件: status={status}")
        # 如果指定了 task_type (如 code_generation)，可以在 config 中查找或扩展 Task 字段
        # 目前简单处理: 如果 task_type 不是 ai_agent_scan，可能无法通过 Task.task_type 过滤准确
        # 但 Task.task_type 记录的是 "ai_agent_scan"。
        # 实际 Agent 的具体类型 (code/vuln) 可能存在 config 中。
        
        total = await query.count()
        logger.info(f"[AI_AGENT] [TASK_LIST_COUNT] 查询结果 - 模块: API, 总数: {total}")
        
        tasks = await query \
            .order_by("-created_at") \
            .offset((page - 1) * page_size) \
            .limit(page_size)
        
        task_list = []
        for task in tasks:
            task_list.append({
                "task_id": str(task.id),
                "task_type": task.task_type,
                "target": task.target,
                "status": task.status,
                "progress": task.progress,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            })
        
        logger.info(f"[AI_AGENT] [TASK_LIST_RESULT] 返回任务列表 - 模块: API, 任务数: {len(task_list)}, 页码: {page}")
        
        response_data = {
            "tasks": task_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
        logger.info(f"[AI_AGENT] [TASK_LIST_RETURN] 返回响应数据 - 模块: API, 数据: {response_data}")
        
        return APIResponse(
            code=200,
            message="获取成功",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"[AI_AGENT] [ERROR] 获取Agent任务列表失败 - 模块: API, 错误: {str(e)}, 堆栈: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/cancel", response_model=APIResponse)
async def cancel_agent_task(task_id: str):
    """
    取消Agent任务
    """
    try:
        logger.info(f"[AI_AGENT] [TASK_CANCEL_START] 取消Agent任务 - 模块: API, 变量: task_id, 值: {task_id}")
        
        # 尝试转换为int
        db_task_id = None
        if task_id.isdigit():
            db_task_id = int(task_id)
            logger.info(f"[AI_AGENT] [TASK_CANCEL_CONVERT] Task ID转换 - 模块: API, 变量: task_id, 旧值: {task_id}, 新值: {db_task_id}")
            
        # 1. 内存清理
        if task_id in agent_tasks:
            del agent_tasks[task_id]
            logger.info(f"✅ Agent任务已从内存中删除: {task_id}")
        
        # 2. 数据库状态更新 & 任务终止
        if db_task_id:
            logger.info(f"[AI_AGENT] [TASK_CANCEL_DB] 从数据库获取任务 - 模块: API, 变量: db_task_id, 状态: querying")
            task = await Task.get_or_none(id=db_task_id)
            if task:
                logger.info(f"[AI_AGENT] [TASK_CANCEL_FOUND] 找到任务 - 模块: API, 变量: task_id, 当前状态: {task.status}")
                # 调用任务执行器取消任务
                if task_executor:
                    logger.info(f"[AI_AGENT] [TASK_CANCEL_STOP] 通知执行器停止任务 - 模块: API, 变量: task_id, 状态: stopping")
                    await task_executor.cancel_task(db_task_id)
                
                # 确保数据库状态更新
                if task.status == "running" or task.status == "pending":
                    task.status = "cancelled"
                    await task.save()
                
                logger.info(f"[AI_AGENT] [TASK_CANCEL_SUCCESS] 任务已取消 - 模块: API, 变量: task_id, 新状态: {task.status}")
                
                return APIResponse(
                    code=200,
                    message="任务已取消",
                    data={
                        "task_id": str(task.id),
                        "status": "cancelled"
                    }
                )

        # 3. 兼容旧AgentTask (UUID)
        if len(task_id) > 20:
            task = await AgentTask.get_or_none(task_id=task_id)
            if task:
                if task.status == "running":
                    await task.update_from_dict({"status": "cancelled"})
                    await task.save()
                return {
                    "task_id": task_id,
                    "status": "cancelled",
                    "message": "任务已取消"
                }

        logger.error(f"[AI_AGENT] [TASK_CANCEL_NOT_FOUND] 任务不存在 - 模块: API, 变量: task_id, 值: {task_id}, 状态: error")
        raise HTTPException(status_code=404, detail="任务不存在")
        
    except HTTPException as http_ex:
        logger.error(f"[AI_AGENT] [ERROR] 取消Agent任务HTTP异常 - 模块: API, 错误: {str(http_ex)}")
        raise
    except Exception as e:
        logger.error(f"[AI_AGENT] [ERROR] 取消Agent任务失败 - 模块: API, 错误: {str(e)}, 堆栈: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}", response_model=APIResponse)
async def delete_agent_task(task_id: str):
    """
    删除Agent任务
    
    删除任务记录。如果任务正在运行，会先取消任务。
    """
    try:
        logger.info(f"[AI_AGENT] [TASK_DELETE_START] 删除Agent任务 - 模块: API, 变量: task_id, 值: {task_id}")
        
        # 尝试转换为int
        db_task_id = None
        if task_id.isdigit():
            db_task_id = int(task_id)
            logger.info(f"[AI_AGENT] [TASK_DELETE_CONVERT] Task ID转换 - 模块: API, 变量: task_id, 旧值: {task_id}, 新值: {db_task_id}")
            
        # 1. 内存清理
        if task_id in agent_tasks:
            del agent_tasks[task_id]
            logger.info(f"[AI_AGENT] [TASK_DELETE_MEMORY] 任务已从内存中删除 - 模块: API, 变量: task_id, 状态: deleted")
        
        # 2. 删除 Unified Task
        if db_task_id:
            logger.info(f"[AI_AGENT] [TASK_DELETE_DB] 从数据库获取任务 - 模块: API, 变量: db_task_id, 状态: querying")
            task = await Task.get_or_none(id=db_task_id)
            if task:
                logger.info(f"[AI_AGENT] [TASK_DELETE_FOUND] 找到任务 - 模块: API, 变量: task_id, 当前状态: {task.status}")
                # 如果正在运行，先取消
                if task.status == "running" or task.status == "pending":
                    if task_executor:
                        logger.info(f"[AI_AGENT] [TASK_DELETE_STOP] 任务正在运行，先取消 - 模块: API, 变量: task_id, 状态: cancelling")
                        await task_executor.cancel_task(db_task_id)
                
                # 删除数据库记录
                await task.delete()
                
                logger.info(f"[AI_AGENT] [TASK_DELETE_SUCCESS] 任务已删除 - 模块: API, 变量: task_id, 状态: deleted")
                
                return APIResponse(
                    code=200,
                    message="任务已删除",
                    data={
                        "task_id": str(db_task_id),
                        "status": "deleted"
                    }
                )

        # 3. 删除旧AgentTask
        if len(task_id) > 20:
            logger.info(f"[AI_AGENT] [TASK_DELETE_LEGACY] 尝试删除旧AgentTask - 模块: API, 变量: task_id, 状态: querying")
            task = await AgentTask.get_or_none(task_id=task_id)
            if task:
                await task.delete()
                # 关联的 AgentResult 会因为级联删除吗？ TortoiseORM默认可能不会，手动删除
                await AgentResult.filter(task=task).delete()
                logger.info(f"[AI_AGENT] [TASK_DELETE_LEGACY_SUCCESS] 旧AgentTask已删除 - 模块: API, 变量: task_id, 状态: deleted")
                return APIResponse(
                    code=200,
                    message="任务已删除",
                    data={
                        "task_id": task_id,
                        "status": "deleted"
                    }
                )

        logger.error(f"[AI_AGENT] [TASK_DELETE_NOT_FOUND] 任务不存在 - 模块: API, 变量: task_id, 值: {task_id}, 状态: error")
        raise HTTPException(status_code=404, detail="任务不存在")

    except HTTPException as http_ex:
        logger.error(f"[AI_AGENT] [ERROR] 删除Agent任务HTTP异常 - 模块: API, 错误: {str(http_ex)}")
        raise
    except Exception as e:
        logger.error(f"[AI_AGENT] [ERROR] 删除Agent任务失败 - 模块: API, 错误: {str(e)}, 堆栈: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools", response_model=APIResponse)
async def list_tools(category: Optional[str] = None) -> APIResponse:
    """
    获取可用工具列表
    
    列出所有已注册的扫描工具。
    
    Args:
        category: 按分类过滤(plugin/poc/general)
        
    Returns:
        APIResponse: 工具列表
        
    Examples:
        >>> 获取所有插件
        >>> GET /ai_agents/tools?category=plugin
    """
    try:
        from ..tools.registry import registry
        
        tools = registry.list_tools(category=category)
        
        return APIResponse(
            code=200,
            message="获取成功",
            data={
                "total": len(tools),
                "tools": tools
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 获取工具列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=APIResponse)
async def get_config() -> APIResponse:
    """
    获取Agent配置
    
    返回当前的Agent配置参数。
    
    Returns:
        APIResponse: 配置信息
    """
    return APIResponse(
        code=200,
        message="获取成功",
        data={
            "max_execution_time": agent_config.MAX_EXECUTION_TIME,
            "max_retries": agent_config.MAX_RETRIES,
            "max_concurrent_tools": agent_config.MAX_CONCURRENT_TOOLS,
            "tool_timeout": agent_config.TOOL_TIMEOUT,
            "enable_llm_planning": agent_config.ENABLE_LLM_PLANNING,
            "default_scan_tasks": agent_config.DEFAULT_SCAN_TASKS,
            "enable_memory": agent_config.ENABLE_MEMORY,
            "enable_kb_integration": agent_config.ENABLE_KB_INTEGRATION
        }
    )


@router.post("/config", response_model=APIResponse)
async def update_config(
    max_execution_time: Optional[int] = None,
    max_retries: Optional[int] = None,
    max_concurrent_tools: Optional[int] = None,
    tool_timeout: Optional[int] = None,
    enable_llm_planning: Optional[bool] = None,
    enable_memory: Optional[bool] = None,
    enable_kb_integration: Optional[bool] = None
) -> APIResponse:
    """
    更新Agent配置
    
    动态更新Agent的配置参数。
    
    Returns:
        APIResponse: 更新后的配置
    """
    if max_execution_time is not None:
        agent_config.MAX_EXECUTION_TIME = max_execution_time
    if max_retries is not None:
        agent_config.MAX_RETRIES = max_retries
    if max_concurrent_tools is not None:
        agent_config.MAX_CONCURRENT_TOOLS = max_concurrent_tools
    if tool_timeout is not None:
        agent_config.TOOL_TIMEOUT = tool_timeout
    if enable_llm_planning is not None:
        agent_config.ENABLE_LLM_PLANNING = enable_llm_planning
    if enable_memory is not None:
        agent_config.ENABLE_MEMORY = enable_memory
    if enable_kb_integration is not None:
        agent_config.ENABLE_KB_INTEGRATION = enable_kb_integration
    
    logger.info("✅ Agent配置已更新")
    
    return APIResponse(
        code=200,
        message="配置更新成功",
        data={
            "max_execution_time": agent_config.MAX_EXECUTION_TIME,
            "max_retries": agent_config.MAX_RETRIES,
            "max_concurrent_tools": agent_config.MAX_CONCURRENT_TOOLS,
            "tool_timeout": agent_config.TOOL_TIMEOUT,
            "enable_llm_planning": agent_config.ENABLE_LLM_PLANNING,
            "default_scan_tasks": agent_config.DEFAULT_SCAN_TASKS,
            "enable_memory": agent_config.ENABLE_MEMORY,
            "enable_kb_integration": agent_config.ENABLE_KB_INTEGRATION
        }
    )


@router.post("/code/generate", response_model=APIResponse)
async def generate_code(request: CodeGenerationRequest):
    """
    生成扫描代码
    
    Args:
        request: 代码生成请求
        
    Returns:
        Dict: 代码生成结果
    """
    try:
        logger.info(f"🔧 生成代码: scan_type={request.scan_type}, target={request.target}")
        
        code_generator = CodeGenerator()
        result = await code_generator.generate_code(
            scan_type=request.scan_type,
            target=request.target,
            requirements=request.requirements,
            language=request.language,
            additional_params=request.additional_params
        )
        

        return {
            "status": "success",
            "data": result.to_dict()
        }
        
    except Exception as e:
        logger.error(f"❌ 代码生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code/execute", response_model=APIResponse)
async def execute_code(request: CodeExecutionRequest):
    """
    执行代码
    
    Args:
        request: 代码执行请求
        
    Returns:
        Dict: 执行结果
    """
    try:
        logger.info(f"⚡ 执行代码: language={request.language}")
        
        executor = UnifiedExecutor(
            timeout=agent_config.TOOL_TIMEOUT,
            enable_sandbox=True
        )
        result = await executor.execute_code(
            code=request.code,
            language=request.language,
            target=request.target
        )
        
        logger.info(f"✅ 代码执行完成: status={result.status}")
        return {
            "status": "success",
            "data": result.to_dict()
        }
        
    except Exception as e:
        logger.error(f"❌ 代码执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code/generate-and-execute", response_model=APIResponse)
async def generate_and_execute_code(request: CodeGenerationRequest):
    """
    生成并执行代码
    
    Args:
        request: 代码生成请求
        
    Returns:
        Dict: 执行结果
    """
    try:
        logger.info(f"🔧 生成并执行代码: scan_type={request.scan_type}, target={request.target}")
        
        executor = UnifiedExecutor(
            timeout=agent_config.TOOL_TIMEOUT,
            enable_sandbox=True
        )
        result = await executor.generate_and_execute(
            scan_type=request.scan_type,
            target=request.target,
            requirements=request.requirements,
            language=request.language,
            additional_params=request.additional_params
        )
        

        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ 生成并执行代码失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capabilities/enhance", response_model=APIResponse)
async def enhance_capability(request: CapabilityEnhancementRequest):
    """
    增强功能
    
    Args:
        request: 功能补充请求
        
    Returns:
        Dict: 增强结果
    """
    try:
        logger.info(f"🚀 增强功能: requirement={request.requirement}")
        
        executor = UnifiedExecutor(
            timeout=agent_config.TOOL_TIMEOUT,
            enable_sandbox=True
        )
        result = await executor.enhance_and_execute(
            requirement=request.requirement,
            target=request.target,
            capability_name=request.capability_name
        )
        

        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ 功能增强失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities/list", response_model=APIResponse)
async def list_capabilities():
    """
    列出所有能力
    
    Returns:
        Dict: 能力列表
    """
    try:
        capability_enhancer = CapabilityEnhancer()
        capabilities = capability_enhancer.list_capabilities()
        
        return {
            "status": "success",
            "data": {
                "total": len(capabilities),
                "capabilities": capabilities
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 获取能力列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities/{capability_name}", response_model=APIResponse)
async def get_capability(capability_name: str):
    """
    获取能力详情
    
    Args:
        capability_name: 能力名称
        
    Returns:
        Dict: 能力详情
    """
    try:
        capability_enhancer = CapabilityEnhancer()
        capability = capability_enhancer.get_capability(capability_name)
        
        if not capability:
            raise HTTPException(status_code=404, detail=f"能力不存在: {capability_name}")
        
        return {
            "status": "success",
            "data": capability.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取能力详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/capabilities/{capability_name}", response_model=APIResponse)
async def remove_capability(capability_name: str):
    """
    移除能力
    
    Args:
        capability_name: 能力名称
        
    Returns:
        Dict: 移除结果
    """
    try:
        capability_enhancer = CapabilityEnhancer()
        success = capability_enhancer.remove_capability(capability_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"能力不存在: {capability_name}")
        
        logger.info(f"✅ 能力已移除: {capability_name}")
        return {
            "status": "success",
            "message": f"能力已移除: {capability_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 移除能力失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environment/info", response_model=APIResponse)
async def get_environment_info():
    """
    获取环境信息
    
    Returns:
        Dict: 环境信息
    """
    try:
        env_awareness = EnvironmentAwareness()
        env_info = env_awareness.get_environment_report()
        
        return {
            "status": "success",
            "data": env_info
        }
        
    except Exception as e:
        logger.error(f"❌ 获取环境信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environment/tools", response_model=APIResponse)
async def get_available_tools():
    """
    获取可用工具列表
    
    Returns:
        Dict: 可用工具列表
    """
    try:
        env_awareness = EnvironmentAwareness()
        tools = env_awareness.available_tools
        
        return {
            "status": "success",
            "data": {
                "total": len(tools),
                "tools": tools
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 获取可用工具失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environment/tools/{tool_name}")
async def check_tool(tool_name: str) -> Dict[str, Any]:
    """
    检查工具是否可用
    
    Args:
        tool_name: 工具名称
        
    Returns:
        Dict: 工具可用性
    """
    try:
        env_awareness = EnvironmentAwareness()
        is_available = env_awareness.is_tool_available(tool_name)
        
        return {
            "status": "success",
            "data": {
                "tool_name": tool_name,
                "available": is_available
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 检查工具可用性失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

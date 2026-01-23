"""
AI Agents API 路由

提供Agent扫描任务的API接口。
"""
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from uuid import uuid4

from models import AgentTask, AgentResult
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
        target: 扫描目标（URL/IP）
        enable_llm_planning: 是否启用LLM增强规划
        custom_tasks: 自定义任务列表（可选）
    """
    target: str
    enable_llm_planning: Optional[bool] = None
    custom_tasks: Optional[list] = None


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
    
    Args:
        request: 扫描请求
        background_tasks: FastAPI后台任务
        
    Returns:
        AgentScanResponse: 任务创建响应
        
    Raises:
        HTTPException: 任务创建失败时抛出500错误
        
    Examples:
        >>> 启动Agent扫描
        >>> POST /ai_agents/scan
        >>> {
        ...     "target": "http://example.com",
        ...     "enable_llm_planning": true
        ... }
    """
    try:
        # 生成任务ID
        task_id = str(uuid4())
        
        # 创建数据库记录
        task_obj = await AgentTask.create(
            task_id=task_id,
            input_json=json.dumps(request.dict(), ensure_ascii=False),
            task_type="agent_scan",
            status="running"
        )
        
        # 更新配置
        if request.enable_llm_planning is not None:
            agent_config.ENABLE_LLM_PLANNING = request.enable_llm_planning
        
        # 初始化Agent状态
        initial_state = AgentState(
            target=request.target,
            task_id=task_id
        )
        
        # 如果有自定义任务，使用自定义任务
        if request.custom_tasks:
            initial_state.planned_tasks = request.custom_tasks.copy()
        
        # 设置自定义扫描参数
        if request.need_custom_scan:
            initial_state.update_context("need_custom_scan", True)
            initial_state.update_context("custom_scan_type", request.custom_scan_type)
            initial_state.update_context("custom_scan_requirements", request.custom_scan_requirements)
            initial_state.update_context("custom_scan_language", request.custom_scan_language)
        
        # 设置功能补充参数
        if request.need_capability_enhancement:
            initial_state.update_context("need_capability_enhancement", True)
            initial_state.update_context("capability_requirement", request.capability_requirement)
        
        # 保存任务到内存
        agent_tasks[task_id] = {
            "task_id": task_id,
            "target": request.target,
            "status": "running",
            "created_at": asyncio.get_event_loop().time(),
            "progress": 0
        }
        
        # 在后台执行Agent工作流
        background_tasks.add_task(
            _run_agent_task(task_id, initial_state)
        )
        
        logger.info(f"✅ Agent任务已启动: {task_id} -> {request.target}")
        
        return AgentScanResponse(
            task_id=task_id,
            status="running",
            message="Agent扫描任务已启动"
        )
        
    except Exception as e:
        logger.error(f"❌ 启动Agent任务失败: {str(e)}")
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


@router.get("/tasks/{task_id}")
async def get_agent_task(task_id: str) -> Dict[str, Any]:
    """
    获取Agent任务详情
    
    根据任务ID获取任务的详细信息。
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict: 任务详情
        
    Raises:
        HTTPException: 任务不存在时抛出404错误
        
    Examples:
        >>> 获取任务详情
        >>> GET /ai_agents/tasks/123e4567-e89b-12d3-a456-426614174000
    """
    try:
        # 先从内存中获取
        if task_id in agent_tasks:
            task_info = agent_tasks[task_id]
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
        
        # 从数据库获取
        task = await AgentTask.get_or_none(task_id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取结果
        result = await AgentResult.get_or_none(task=task)
        
        return {
            "task_id": task_id,
            "input_json": task.input_json,
            "task_type": task.task_type,
            "status": task.status,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "final_output": result.final_output if result else None,
            "execution_time": result.execution_time if result else None,
            "error_message": result.error_message if result else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取Agent任务详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_agent_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    获取Agent任务列表
    
    支持按状态和类型过滤，以及分页查询。
    
    Args:
        status: 按任务状态过滤
        task_type: 按任务类型过滤
        page: 页码，从1开始
        page_size: 每页数量
        
    Returns:
        Dict: 任务列表和分页信息
        
    Examples:
        >>> 获取所有运行中的任务
        >>> GET /ai_agents/tasks?status=running
    """
    try:
        query = AgentTask.all()
        
        if status:
            query = query.filter(status=status)
        if task_type:
            query = query.filter(task_type=task_type)
        
        total = await query.count()
        
        tasks = await query \
            .order_by("-created_at") \
            .offset((page - 1) * page_size) \
            .limit(page_size)
        
        task_list = []
        for task in tasks:
            task_list.append({
                "task_id": str(task.task_id),
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
        logger.error(f"❌ 获取Agent任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def cancel_agent_task(task_id: str) -> Dict[str, Any]:
    """
    取消Agent任务
    
    取消指定的Agent任务。
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict: 取消结果
        
    Raises:
        HTTPException: 任务不存在时抛出404错误
        
    Examples:
        >>> 取消任务
        >>> DELETE /ai_agents/tasks/123e4567-e89b-12d3-a456-426614174000
    """
    try:
        # 从内存中删除
        if task_id in agent_tasks:
            del agent_tasks[task_id]
            logger.info(f"✅ Agent任务已从内存中删除: {task_id}")
        
        # 更新数据库状态
        task = await AgentTask.get_or_none(task_id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.status == "running":
            await task.update_from_dict({"status": "cancelled"})
            await task.save()
            logger.info(f"✅ Agent任务已取消: {task_id}")
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "任务已取消"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 取消Agent任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools(category: Optional[str] = None) -> Dict[str, Any]:
    """
    获取可用工具列表
    
    列出所有已注册的扫描工具。
    
    Args:
        category: 按分类过滤（plugin/poc/general）
        
    Returns:
        Dict: 工具列表
        
    Examples:
        >>> 获取所有插件
        >>> GET /ai_agents/tools?category=plugin
    """
    try:
        from ..tools.registry import registry
        
        tools = registry.list_tools(category=category)
        
        return {
            "total": len(tools),
            "tools": tools
        }
        
    except Exception as e:
        logger.error(f"❌ 获取工具列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """
    获取Agent配置
    
    返回当前的Agent配置参数。
    
    Returns:
        Dict: 配置信息
    """
    return {
        "max_execution_time": agent_config.MAX_EXECUTION_TIME,
        "max_retries": agent_config.MAX_RETRIES,
        "max_concurrent_tools": agent_config.MAX_CONCURRENT_TOOLS,
        "tool_timeout": agent_config.TOOL_TIMEOUT,
        "enable_llm_planning": agent_config.ENABLE_LLM_PLANNING,
        "default_scan_tasks": agent_config.DEFAULT_SCAN_TASKS,
        "enable_memory": agent_config.ENABLE_MEMORY,
        "enable_kb_integration": agent_config.ENABLE_KB_INTEGRATION
    }


@router.post("/config")
async def update_config(
    max_execution_time: Optional[int] = None,
    max_retries: Optional[int] = None,
    max_concurrent_tools: Optional[int] = None,
    tool_timeout: Optional[int] = None,
    enable_llm_planning: Optional[bool] = None,
    enable_memory: Optional[bool] = None,
    enable_kb_integration: Optional[bool] = None
) -> Dict[str, Any]:
    """
    更新Agent配置
    
    动态更新Agent的配置参数。
    
    Returns:
        Dict: 更新后的配置
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
    
    return await get_config()

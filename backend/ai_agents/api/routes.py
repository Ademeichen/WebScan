"""
AI Agents API 路由

提供Agent扫描任务的API接口。

优化内容:
- 集成POC搜索、执行和批量执行API
- 集成工作流执行指标API
- 添加统一的错误处理和响应格式
- 增强错误处理和日志记录
"""
import json
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from enum import Enum

from backend.models import Task
from backend.api.common import APIResponse
from backend.task_executor import task_executor
from ..core.state import AgentState
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


@router.post("/scan", response_model=AgentScanResponse)
async def start_agent_scan(
    request: AgentScanRequest
):
    """
    启动Agent扫描任务
    
    创建Agent任务并在后台执行扫描工作流。
    """
    try:
        # 1. 构造扫描配置
        scan_config = request.model_dump()
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
        
        # 从数据库获取 (使用 Unified Task Model)
        task = None
        if db_task_id:
            logger.info(f"[AI_AGENT] [TASK_DETAIL_DB] 从数据库获取任务 - 模块: API, 变量: db_task_id, 状态: querying")
            task = await Task.get_or_none(id=db_task_id)
        
        if not task:
            logger.error(f"[AI_AGENT] [TASK_DETAIL_NOT_FOUND] 任务不存在 - 模块: API, 变量: task_id, 值: {task_id}, 状态: error")
            raise HTTPException(status_code=404, detail="任务不存在")
        
        logger.info(f"[AI_AGENT] [TASK_DETAIL_FOUND] 找到任务 - 模块: API, 变量: task_id, 值: {task.id}, 状态: {task.status}")
        
        # 返回 Task 模型数据
        return APIResponse(
            code=200,
            message="获取成功",
            data={
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
        )
        
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
        
        # 数据库状态更新 & 任务终止
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
        
        # 删除 Unified Task
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
        APIResponse: 能力列表
    """
    try:
        capability_enhancer = CapabilityEnhancer()
        capabilities = capability_enhancer.list_capabilities()
        
        return APIResponse(
            code=200,
            message="获取成功",
            data={
                "total": len(capabilities),
                "capabilities": capabilities
            }
        )
        
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
        APIResponse: 环境信息
    """
    try:
        env_awareness = EnvironmentAwareness()
        env_info = env_awareness.get_environment_report()
        
        return APIResponse(
            code=200,
            message="获取成功",
            data=env_info
        )
        
    except Exception as e:
        logger.error(f"❌ 获取环境信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environment/tools", response_model=APIResponse)
async def get_available_tools():
    """
    获取可用工具列表
    
    Returns:
        APIResponse: 可用工具列表
    """
    try:
        env_awareness = EnvironmentAwareness()
        tools = env_awareness.available_tools
        
        return APIResponse(
            code=200,
            message="获取成功",
            data={
                "total": len(tools),
                "tools": tools
            }
        )
        
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


@router.get("/resources/usage", response_model=APIResponse)
async def get_resource_usage():
    """
    获取资源使用情况
    
    Returns:
        APIResponse: 资源使用情况
    """
    try:
        from ..utils.resource_limiter import get_default_limiter
        
        limiter = get_default_limiter()
        usage = await limiter.get_current_usage()
        
        return APIResponse(
            code=200,
            message="获取成功",
            data=usage.to_dict()
        )
        
    except Exception as e:
        logger.error(f"❌ 获取资源使用情况失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/statistics", response_model=APIResponse)
async def get_resource_statistics():
    """
    获取资源统计信息
    
    Returns:
        APIResponse: 资源统计信息
    """
    try:
        from ..utils.resource_limiter import get_default_limiter
        
        limiter = get_default_limiter()
        stats = limiter.get_statistics()
        
        return APIResponse(
            code=200,
            message="获取成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"❌ 获取资源统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 从 agent.py 合并的端点 ============

class HeartbeatRequest(BaseModel):
    """插件心跳请求模型"""
    timestamp: float


class FinishRequest(BaseModel):
    """插件完成请求模型"""
    exitCode: int
    stdout: str
    stderr: str


@router.put("/tasks/{task_id}/plugin/{plugin_id}/heartbeat", response_model=APIResponse)
async def plugin_heartbeat(task_id: int, plugin_id: str, request: HeartbeatRequest):
    """
    插件心跳上报
    
    Args:
        task_id: 任务ID
        plugin_id: 插件ID
        request: 心跳请求
        
    Returns:
        APIResponse: 心跳处理结果
    """
    try:
        task_executor.update_heartbeat(task_id)
        return APIResponse(code=200, message="Heartbeat received")
    except Exception as e:
        logger.warning(f"Heartbeat update failed: {e}")
        return APIResponse(code=500, message="Heartbeat failed")


@router.post("/tasks/{task_id}/plugin/{plugin_id}/finish", response_model=APIResponse)
async def plugin_finish(task_id: int, plugin_id: str, request: FinishRequest):
    """
    插件执行完成回调
    
    Args:
        task_id: 任务ID
        plugin_id: 插件ID
        request: 完成请求
        
    Returns:
        APIResponse: 完成处理结果
    """
    try:
        logger.info(f"[插件完成] 收到完成回调 | 任务ID: {task_id} | 插件: {plugin_id} | 退出码: {request.exitCode}")
        task = await Task.get_or_none(id=task_id)
        if not task:
            logger.warning(f"[插件完成] 任务不存在 | 任务ID: {task_id}")
            return APIResponse(code=404, message="Task not found")
        
        if request.exitCode == 0:
            logger.info(f"[插件完成] 执行成功 | 任务ID: {task_id} | 插件: {plugin_id}")
            task.status = 'completed'
            task.progress = 100
            try:
                task.result = request.stdout
            except:
                task.result = json.dumps({"raw_output": request.stdout})
        else:
            logger.warning(f"[插件完成] 执行失败 | 任务ID: {task_id} | 插件: {plugin_id} | 退出码: {request.exitCode} | 错误: {request.stderr}")
            task.status = 'failed'
            task.result = json.dumps({"error": request.stderr or "Unknown error", "exit_code": request.exitCode})
            
        await task.save()
        logger.info(f"[插件完成] 任务状态已更新 | 任务ID: {task_id} | 状态: {task.status}")
        return APIResponse(code=200, message="Finish processed")
    except Exception as e:
        logger.error(f"Finish callback failed: {e}")
        return APIResponse(code=500, message=f"Finish callback failed: {str(e)}")


@router.get("/tasks/{task_id}/logs", response_model=APIResponse)
async def get_task_logs(task_id: int, tail: int = 500, keyword: str = ""):
    """
    获取任务的插件日志
    
    Args:
        task_id: 任务ID
        tail: 返回最后N行日志
        keyword: 关键词过滤
        
    Returns:
        APIResponse: 日志内容
    """
    from pathlib import Path
    
    try:
        task = await Task.get_or_none(id=task_id)
        if not task:
            return APIResponse(code=404, message="Task not found")
        
        log_date = task.created_at.strftime("%Y-%m-%d")
        log_file = Path("logs") / "plugins" / log_date / f"{task_id}.log"
        
        if not log_file.exists():
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
    获取冻结任务列表
    
    冻结定义: 运行中 且 运行时长 > 80% 阈值
        
    Returns:
        APIResponse: 冻结任务列表
    """
    import datetime
    
    try:
        running_tasks = await Task.filter(status='running').all()
        frozen_tasks = []
        now = datetime.datetime.now(datetime.timezone.utc)
        
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


# ============ POC API 端点 ============

class POCSearchRequest(BaseModel):
    """POC搜索请求模型"""
    cve_id: str


class POCExecuteRequest(BaseModel):
    """POC执行请求模型"""
    target: str
    cve_id: Optional[str] = None
    poc_name: Optional[str] = None
    timeout: Optional[float] = 300.0


class POCBatchExecuteRequest(BaseModel):
    """批量POC执行请求模型"""
    targets: List[str]
    cve_ids: List[str]


@router.post("/poc/search", response_model=APIResponse)
async def search_poc(request: POCSearchRequest):
    """
    搜索POC
    
    通过CVE编号搜索可用的POC。
    
    Args:
        request: 包含CVE编号的搜索请求
        
    Returns:
        APIResponse: POC搜索结果
    """
    try:
        logger.info(f"[POC_SEARCH] 搜索POC - CVE: {request.cve_id}")
        
        from backend.ai_agents.poc_system.poc_manager import poc_manager
        
        poc_infos = await poc_manager.sync_from_seebug(keyword=request.cve_id, limit=10)
        
        data = {
            "cve_id": request.cve_id,
            "count": len(poc_infos),
            "results": [
                {
                    "title": poc.poc_name,
                    "description": poc.description,
                    "severity": poc.severity,
                    "poc_id": poc.poc_id,
                    "source": poc.source
                }
                for poc in poc_infos
            ]
        }
        
        logger.info(f"[POC_SEARCH] 搜索完成 - 找到 {len(poc_infos)} 个POC")
        return APIResponse(code=200, message=f"找到 {len(poc_infos)} 个POC", data=data)
        
    except Exception as e:
        logger.error(f"[POC_SEARCH_ERROR] 搜索POC失败 - 错误: {str(e)}")
        return APIResponse(code=500, message=f"搜索POC失败: {str(e)}")


@router.post("/poc/execute", response_model=APIResponse)
async def execute_poc(request: POCExecuteRequest):
    """
    执行POC检测
    
    执行单个POC漏洞检测。
    
    Args:
        request: 包含目标、CVE编号或POC名称的执行请求
        
    Returns:
        APIResponse: POC执行结果
    """
    try:
        logger.info(f"[POC_EXECUTE] 执行POC - 目标: {request.target}, CVE: {request.cve_id}, POC: {request.poc_name}")
        
        from backend.ai_agents.poc_system.poc_manager import poc_manager
        from backend.ai_agents.poc_system.verification_engine import verification_engine
        
        poc_id = request.poc_name or request.cve_id
        if not poc_id:
            return APIResponse(code=400, message="必须提供 cve_id 或 poc_name")
        
        verification_task = await poc_manager.create_verification_task(
            poc_id=poc_id,
            target=request.target
        )
        
        result = await verification_engine.execute_verification_task(verification_task)
        
        data = {
            "cve_id": request.cve_id,
            "target": result.target,
            "success": result.error is None,
            "vulnerable": result.vulnerable,
            "poc_name": result.poc_name,
            "execution_time": result.execution_time,
            "error": result.error,
            "message": result.message
        }
        
        message = "POC执行完成" if result.vulnerable else "POC执行完成，未发现漏洞"
        logger.info(f"[POC_EXECUTE] 执行完成 - 成功: {result.error is None}, 有漏洞: {result.vulnerable}")
        
        return APIResponse(code=200, message=message, data=data)
        
    except Exception as e:
        logger.error(f"[POC_EXECUTE_ERROR] 执行POC失败 - 错误: {str(e)}")
        return APIResponse(code=500, message=f"执行POC失败: {str(e)}")


@router.post("/poc/batch-execute", response_model=APIResponse)
async def batch_execute_poc(request: POCBatchExecuteRequest):
    """
    批量执行POC检测
    
    对多个目标执行多个CVE的POC检测。
    
    Args:
        request: 包含目标列表和CVE编号列表的批量执行请求
        
    Returns:
        APIResponse: 批量执行结果
    """
    try:
        logger.info(f"[POC_BATCH] 批量执行POC - 目标数: {len(request.targets)}, CVE数: {len(request.cve_ids)}")
        
        from backend.ai_agents.poc_system.poc_manager import poc_manager
        from backend.ai_agents.poc_system.verification_engine import verification_engine
        
        verification_tasks = []
        for target in request.targets:
            for cve_id in request.cve_ids:
                try:
                    task = await poc_manager.create_verification_task(
                        poc_id=cve_id,
                        target=target
                    )
                    verification_tasks.append(task)
                except Exception as e:
                    logger.warning(f"[POC_BATCH] 创建任务失败: {cve_id} -> {target}, 错误: {str(e)}")
        
        results = await verification_engine.execute_batch_verification(verification_tasks)
        
        data = {
            "total": len(results),
            "successful": sum(1 for r in results if r.error is None),
            "vulnerable": sum(1 for r in results if r.vulnerable),
            "results": [
                {
                    "cve_id": r.poc_id,
                    "target": r.target,
                    "success": r.error is None,
                    "vulnerable": r.vulnerable,
                    "execution_time": r.execution_time
                }
                for r in results
            ]
        }
        
        logger.info(f"[POC_BATCH] 批量执行完成 - 总任务: {len(results)}")
        return APIResponse(code=200, message=f"批量POC执行完成: {len(results)} 个任务", data=data)
        
    except Exception as e:
        logger.error(f"[POC_BATCH_ERROR] 批量执行POC失败 - 错误: {str(e)}")
        return APIResponse(code=500, message=f"批量执行POC失败: {str(e)}")


# ============ 工作流指标 API 端点 ============

@router.get("/workflow/metrics", response_model=APIResponse)
async def get_execution_metrics(task_id: Optional[str] = None):
    """
    获取工作流执行指标
    
    获取节点执行时间、重试次数、跳过状态等指标。
    
    Args:
        task_id: 可选的任务ID，用于过滤特定任务的指标
        
    Returns:
        APIResponse: 执行指标数据
    """
    try:
        logger.info(f"[WORKFLOW_METRICS] 获取执行指标 - 任务ID: {task_id}")
        
        from backend.ai_agents.core.execution_optimizer import get_execution_optimizer
        
        optimizer = get_execution_optimizer()
        summary = optimizer.get_execution_summary(task_id)
        metrics = optimizer.get_execution_metrics(task_id)
        
        data = {
            "summary": summary,
            "metrics": [
                {
                    "node_name": m.node_name,
                    "task_id": m.task_id,
                    "duration": m.duration,
                    "success": m.success,
                    "retries": m.retries,
                    "skipped": m.skipped,
                    "error": m.error,
                    "timestamp": m.timestamp
                }
                for m in metrics
            ]
        }
        
        logger.info(f"[WORKFLOW_METRICS] 获取完成 - 指标数: {len(metrics)}")
        return APIResponse(code=200, message="获取执行指标成功", data=data)
        
    except Exception as e:
        logger.error(f"[WORKFLOW_METRICS_ERROR] 获取执行指标失败 - 错误: {str(e)}")
        return APIResponse(code=500, message=f"获取执行指标失败: {str(e)}")

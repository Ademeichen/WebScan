"""
新增API端点

添加代码生成、功能补充、环境信息查询等新的API端点。
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..code_execution.executor import UnifiedExecutor
from ..code_execution.environment import EnvironmentAwareness
from ..code_execution.code_generator import CodeGenerator
from ..code_execution.capability_enhancer import CapabilityEnhancer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai_agents", tags=["AI Agents"])


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


@router.post("/code/generate")
async def generate_code(request: CodeGenerationRequest) -> Dict[str, Any]:
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
        
        logger.info(f"✅ 代码生成完成")
        return {
            "status": "success",
            "data": result.to_dict()
        }
        
    except Exception as e:
        logger.error(f"❌ 代码生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code/execute")
async def execute_code(request: CodeExecutionRequest) -> Dict[str, Any]:
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


@router.post("/code/generate-and-execute")
async def generate_and_execute_code(request: CodeGenerationRequest) -> Dict[str, Any]:
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
        
        logger.info(f"✅ 生成并执行代码完成")
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ 生成并执行代码失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capabilities/enhance")
async def enhance_capability(request: CapabilityEnhancementRequest) -> Dict[str, Any]:
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
        
        logger.info(f"✅ 功能增强完成")
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ 功能增强失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities/list")
async def list_capabilities() -> Dict[str, Any]:
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


@router.get("/capabilities/{capability_name}")
async def get_capability(capability_name: str) -> Dict[str, Any]:
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


@router.delete("/capabilities/{capability_name}")
async def remove_capability(capability_name: str) -> Dict[str, Any]:
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


@router.get("/environment/info")
async def get_environment_info() -> Dict[str, Any]:
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


@router.get("/environment/tools")
async def get_available_tools() -> Dict[str, Any]:
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


from ..config import agent_config

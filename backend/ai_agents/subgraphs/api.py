"""
子图API接口

提供各子图的REST API端点，供前端调用。
"""
import logging
from typing import Dict, Any, List, Optional, Generic, TypeVar
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from .orchestrator import ScanOrchestrator
from .dto import (
    ScanPlanDTO, ToolExecutionResultDTO, CodeScanResultDTO,
    POCVerificationResultDTO, ReportDTO, OrchestratorResultDTO,
    TaskStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subgraphs", tags=["Subgraphs"])

orchestrator = ScanOrchestrator()

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    success: bool = True
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    class Config:
        arbitrary_types_allowed = True


class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = False
    code: int
    message: str
    detail: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


def success_response(data: Any, message: str = "success") -> Dict[str, Any]:
    """创建成功响应"""
    if hasattr(data, 'to_dict'):
        response_data = data.to_dict()
    elif isinstance(data, dict):
        response_data = data
    elif isinstance(data, list):
        response_data = [item.to_dict() if hasattr(item, 'to_dict') else item for item in data]
    else:
        response_data = data
    
    return {
        "success": True,
        "code": 200,
        "message": message,
        "data": response_data,
        "timestamp": datetime.now().isoformat()
    }


def error_response(code: int, message: str, detail: str = None) -> Dict[str, Any]:
    """创建错误响应"""
    return {
        "success": False,
        "code": code,
        "message": message,
        "detail": detail,
        "timestamp": datetime.now().isoformat()
    }


class PlanningRequest(BaseModel):
    """规划请求模型"""
    target: str
    task_id: str
    target_context: Optional[Dict[str, Any]] = None


class ToolScanRequest(BaseModel):
    """工具扫描请求模型"""
    target: str
    task_id: str
    planned_tasks: List[str]
    target_context: Optional[Dict[str, Any]] = None


class CodeScanRequest(BaseModel):
    """代码扫描请求模型"""
    target: str
    task_id: str
    need_custom_scan: bool = False
    custom_scan_type: Optional[str] = None
    custom_scan_requirements: Optional[str] = None
    need_capability_enhancement: bool = False
    capability_requirement: Optional[str] = None


class POCVerificationRequest(BaseModel):
    """POC验证请求模型"""
    target: str
    task_id: str
    poc_tasks: List[Dict[str, Any]]


class ReportRequest(BaseModel):
    """报告生成请求模型"""
    target: str
    task_id: str
    tool_results: Dict[str, Any] = Field(default_factory=dict)
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list)
    target_context: Optional[Dict[str, Any]] = None
    report_format: str = "json"


class FullScanRequest(BaseModel):
    """完整扫描请求模型"""
    target: str
    task_id: str
    target_context: Optional[Dict[str, Any]] = None
    custom_tasks: Optional[List[str]] = None
    enable_llm_planning: bool = False


@router.post("/planning")
async def execute_planning(request: PlanningRequest):
    """
    执行规划阶段
    
    快速获取扫描计划，不执行实际扫描。
    执行时间: < 10秒
    """
    logger.info(f"[{request.task_id}] 📋 API调用: 执行规划")
    
    try:
        result = await orchestrator.execute_planning_only(
            target=request.target,
            task_id=request.task_id,
            target_context=request.target_context
        )
        return success_response(result, "规划完成")
    except Exception as e:
        logger.error(f"[{request.task_id}] ❌ 规划失败: {str(e)}")
        return error_response(500, "规划失败", str(e))


@router.post("/tool-scan")
async def execute_tool_scan(request: ToolScanRequest):
    """
    执行工具扫描
    
    执行固定工具扫描任务。
    执行时间: < 2分钟
    """
    logger.info(f"[{request.task_id}] 🔧 API调用: 执行工具扫描")
    
    try:
        result = await orchestrator.execute_tool_scan_only(
            target=request.target,
            task_id=request.task_id,
            planned_tasks=request.planned_tasks,
            target_context=request.target_context
        )
        return success_response(result, "工具扫描完成")
    except Exception as e:
        logger.error(f"[{request.task_id}] ❌ 工具扫描失败: {str(e)}")
        return error_response(500, "工具扫描失败", str(e))


@router.post("/code-scan")
async def execute_code_scan(request: CodeScanRequest):
    """
    执行代码扫描
    
    执行自定义代码扫描或功能增强。
    执行时间: < 1分钟
    """
    logger.info(f"[{request.task_id}] 💻 API调用: 执行代码扫描")
    
    try:
        from .code_scan import CodeScanGraph, CodeScanState
        
        state = CodeScanState(
            target=request.target,
            task_id=request.task_id,
            need_custom_scan=request.need_custom_scan,
            custom_scan_type=request.custom_scan_type,
            custom_scan_requirements=request.custom_scan_requirements,
            need_capability_enhancement=request.need_capability_enhancement,
            capability_requirement=request.capability_requirement
        )
        
        graph = CodeScanGraph()
        state = await graph.execute(state)
        return success_response(graph.get_result_dto(state), "代码扫描完成")
    except Exception as e:
        logger.error(f"[{request.task_id}] ❌ 代码扫描失败: {str(e)}")
        return error_response(500, "代码扫描失败", str(e))


@router.post("/poc-verification")
async def execute_poc_verification(request: POCVerificationRequest):
    """
    执行POC验证
    
    执行POC漏洞验证任务。
    执行时间: < 1分钟
    """
    logger.info(f"[{request.task_id}] 🔬 API调用: 执行POC验证")
    
    try:
        from .poc_verification import POCVerificationGraph, POCVerificationState
        
        state = POCVerificationState(
            target=request.target,
            task_id=request.task_id,
            poc_tasks=request.poc_tasks
        )
        
        graph = POCVerificationGraph()
        state = await graph.execute(state)
        return success_response(graph.get_result_dto(state), "POC验证完成")
    except Exception as e:
        logger.error(f"[{request.task_id}] ❌ POC验证失败: {str(e)}")
        return error_response(500, "POC验证失败", str(e))


@router.post("/report")
async def generate_report(request: ReportRequest):
    """
    生成扫描报告
    
    根据扫描结果生成报告。
    执行时间: < 30秒
    """
    logger.info(f"[{request.task_id}] 📝 API调用: 生成报告")
    
    try:
        from .report import ReportGraph, ReportState
        
        state = ReportState(
            target=request.target,
            task_id=request.task_id,
            tool_results=request.tool_results,
            vulnerabilities=request.vulnerabilities,
            target_context=request.target_context or {},
            report_format=request.report_format
        )
        
        graph = ReportGraph()
        state = await graph.execute(state)
        return success_response(graph.get_result_dto(state), "报告生成完成")
    except Exception as e:
        logger.error(f"[{request.task_id}] ❌ 报告生成失败: {str(e)}")
        return error_response(500, "报告生成失败", str(e))


@router.post("/full-scan")
async def execute_full_scan(request: FullScanRequest):
    """
    执行完整扫描
    
    执行完整的扫描流程，包括规划、扫描、验证和报告生成。
    """
    logger.info(f"[{request.task_id}] 🚀 API调用: 执行完整扫描")
    
    try:
        result = await orchestrator.execute_scan(
            target=request.target,
            task_id=request.task_id,
            target_context=request.target_context,
            custom_tasks=request.custom_tasks,
            enable_llm_planning=request.enable_llm_planning
        )
        return success_response(result, "完整扫描完成")
    except Exception as e:
        logger.error(f"[{request.task_id}] ❌ 完整扫描失败: {str(e)}")
        return error_response(500, "完整扫描失败", str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "subgraphs-api",
        "graphs": [
            {"name": "PlanningGraph", "timeout": "10s"},
            {"name": "ToolExecutionGraph", "timeout": "120s"},
            {"name": "CodeScanGraph", "timeout": "60s"},
            {"name": "POCVerificationGraph", "timeout": "60s"},
            {"name": "ReportGraph", "timeout": "30s"}
        ]
    }

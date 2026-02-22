"""
POC 验证 API 路由

提供 POC 验证相关的 API 接口,包括创建验证任务、查询任务状态、暂停/继续/取消任务、获取验证结果、生成报告等。
"""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from backend.models import POCVerificationTask, POCVerificationResult
from backend.ai_agents.poc_system import (
    poc_manager,

    verification_engine,
    result_analyzer,
    report_generator
)
from backend.config import settings
from backend.api.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/poc/verification", tags=["POC验证"])


class CreateVerificationTaskRequest(BaseModel):
    """
    创建验证任务请求模型
    """
    poc_id: str = Field(..., description="POC ID")
    target: str = Field(..., description="验证目标")
    priority: int = Field(default=5, ge=1, le=10, description="优先级(1-10)")
    task_id: Optional[str] = Field(None, description="关联的任务 ID")


class CreateBatchVerificationTaskRequest(BaseModel):
    """
    批量创建验证任务请求模型
    """
    poc_tasks: List[Dict[str, Any]] = Field(..., description="POC 任务列表")
    target: str = Field(..., description="验证目标")
    task_id: Optional[str] = Field(None, description="关联的任务 ID")


class ImportTargetsRequest(BaseModel):
    """
    导入目标请求模型
    """
    source_type: str = Field(..., description="数据源类型:csv, json, excel, manual")
    data: Optional[str] = Field(None, description="数据内容(CSV/JSON)")
    file_path: Optional[str] = Field(None, description="文件路径")
    targets: Optional[List[Dict[str, Any]]] = Field(None, description="手动输入的目标列表")


class GenerateReportRequest(BaseModel):
    """
    生成报告请求模型
    """
    task_id: UUID = Field(..., description="任务 ID")
    format: str = Field(default="html", description="报告格式:html, json, pdf")
    output_path: Optional[str] = Field(None, description="输出文件路径")


@router.post("/tasks", response_model=Dict[str, Any])
async def create_verification_task(request: CreateVerificationTaskRequest):
    """
    创建 POC 验证任务
    
    创建单个 POC 验证任务并立即执行。
    
    Args:
        request: 验证任务请求
        
    Returns:
        Dict: 包含任务信息和执行结果的响应
        
    Raises:
        HTTPException: 创建失败时抛出错误
    """
    try:
        logger.info(f"📋 创建 POC 验证任务: {request.poc_id} -> {request.target}")
        
        # 检查 POC 验证是否启用
        if not settings.POC_VERIFICATION_ENABLED:
            raise HTTPException(status_code=403, detail="POC 验证功能已禁用")
        
        # 创建验证任务
        verification_task = await poc_manager.create_verification_task(
            poc_id=request.poc_id,
            target=request.target,
            priority=request.priority,
            task_id=request.task_id
        )
        
        # 执行验证
        result = await verification_engine.execute_verification_task(
            verification_task
        )
        
        # 分析结果
        analysis = await result_analyzer.analyze_single_result(result)
        
        logger.info(f"✅ POC 验证任务创建并执行完成: {verification_task.id}")
        
        return {
            "code": 200,
            "message": "POC 验证任务创建成功",
            "data": {
                "task": {
                    "task_id": str(verification_task.id),
                    "poc_name": verification_task.poc_name,
                    "poc_id": verification_task.poc_id,
                    "target": verification_task.target,
                    "status": verification_task.status,
                    "progress": verification_task.progress,
                    "created_at": verification_task.created_at.isoformat()
                },
                "result": {
                    "result_id": result.id,
                    "vulnerable": result.vulnerable,
                    "message": result.message,
                    "confidence": result.confidence,
                    "severity": result.severity,
                    "cvss_score": result.cvss_score,
                    "execution_time": result.execution_time
                },
                "analysis": {
                    "is_false_positive": analysis.is_false_positive,
                    "risk_level": analysis.risk_level,
                    "recommendations": analysis.recommendations
                }
            }
        }
    except Exception as e:
        logger.error(f"❌ 创建 POC 验证任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/tasks/batch", response_model=Dict[str, Any])
async def create_batch_verification_tasks(request: CreateBatchVerificationTaskRequest):
    """
    批量创建 POC 验证任务
    
    批量创建多个 POC 验证任务并并发执行。
    
    Args:
        request: 批量验证任务请求
        
    Returns:
        Dict: 包含任务列表和执行结果的响应
        
    Raises:
        HTTPException: 创建失败时抛出错误
    """
    try:
        logger.info(f"📋 批量创建 POC 验证任务,数量: {len(request.poc_tasks)}")
        
        # 检查 POC 验证是否启用
        if not settings.POC_VERIFICATION_ENABLED:
            raise HTTPException(status_code=403, detail="POC 验证功能已禁用")
        
        # 创建验证任务
        verification_tasks = []
        for poc_task in request.poc_tasks:
            verification_task = await poc_manager.create_verification_task(
                poc_id=poc_task.get("poc_id"),
                target=request.target,
                priority=poc_task.get("priority", 5),
                task_id=request.task_id
            )
            verification_tasks.append(verification_task)
        
        # 批量执行验证
        results = await verification_engine.execute_batch_verification(
            verification_tasks
        )
        
        # 批量分析结果
        analysis_summary = await result_analyzer.analyze_batch_results(results)
        

        
        return {
            "code": 200,
            "message": "批量 POC 验证任务创建成功",
            "data": {
                "tasks": [
                    {
                        "task_id": str(task.id),
                        "poc_name": task.poc_name,
                        "poc_id": task.poc_id,
                        "target": task.target,
                        "status": task.status,
                        "progress": task.progress
                    }
                    for task in verification_tasks
                ],
                "results_count": len(results),
                "analysis": {
                    "total_results": analysis_summary.total_results,
                    "vulnerable_count": analysis_summary.vulnerable_count,
                    "false_positive_count": analysis_summary.false_positive_count,
                    "true_positive_count": analysis_summary.true_positive_count,
                    "severity_distribution": analysis_summary.severity_distribution,
                    "average_confidence": analysis_summary.average_confidence,
                    "high_risk_targets": analysis_summary.high_risk_targets,
                    "recommendations": analysis_summary.recommendations
                }
            }
        }
    except Exception as e:
        logger.error(f"❌ 批量创建 POC 验证任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量创建任务失败: {str(e)}")


@router.get("/tasks", response_model=Dict[str, Any])
async def list_verification_tasks(
    status: Optional[str] = Query(None, description="任务状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    列出 POC 验证任务
    
    获取 POC 验证任务列表,支持按状态过滤和分页查询。
    
    Args:
        status: 任务状态过滤
        page: 页码
        page_size: 每页数量
        
    Returns:
        Dict: 包含任务列表的响应
    """
    try:
        query = POCVerificationTask.all()
        
        if status:
            query = query.filter(status=status)
        
        total = await query.count()
        tasks = await query.order_by("-created_at").offset(
            (page - 1) * page_size
        ).limit(page_size)
        
        task_list = []
        for task in tasks:
            # 获取最新结果
            latest_result = await POCVerificationResult.filter(
                verification_task=task.id
            ).order_by("-created_at").first()
            
            task_list.append({
                "task_id": str(task.id),
                "poc_name": task.poc_name,
                "poc_id": task.poc_id,
                "target": task.target,
                "status": task.status,
                "progress": task.progress,
                "priority": task.priority,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "latest_result": {
                    "vulnerable": latest_result.vulnerable if latest_result else None,
                    "message": latest_result.message if latest_result else None,
                    "confidence": latest_result.confidence if latest_result else None
                } if latest_result else None
            })
        
        return {
            "code": 200,
            "message": "查询验证任务成功",
            "data": {
                "items": task_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except Exception as e:
        logger.error(f"❌ 查询验证任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询任务失败: {str(e)}")


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_verification_task(task_id: UUID):
    """
    获取 POC 验证任务详情
    
    获取指定 POC 验证任务的详细信息,包括所有验证结果。
    
    Args:
        task_id: 任务 ID
        
    Returns:
        Dict: 包含任务详情和结果列表的响应
        
    Raises:
        HTTPException: 任务不存在时抛出 404 错误
    """
    try:
        task = await POCVerificationTask.get_or_none(id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="验证任务不存在")
        
        # 获取所有结果
        results = await POCVerificationResult.filter(
            verification_task=task.id
        ).order_by("-created_at")
        
        result_list = []
        for result in results:
            result_list.append({
                "result_id": result.id,
                "poc_name": result.poc_name,
                "poc_id": result.poc_id,
                "target": result.target,
                "vulnerable": result.vulnerable,
                "message": result.message,
                "output": result.output,
                "error": result.error,
                "execution_time": result.execution_time,
                "confidence": result.confidence,
                "severity": result.severity,
                "cvss_score": result.cvss_score,
                "created_at": result.created_at.isoformat()
            })
        
        return {
            "code": 200,
            "message": "查询验证任务成功",
            "data": {
                "task": {
                    "task_id": str(task.id),
                    "poc_name": task.poc_name,
                    "poc_id": task.poc_id,
                    "target": task.target,
                    "status": task.status,
                    "progress": task.progress,
                    "priority": task.priority,
                    "config": task.config,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat()
                },
                "results": result_list,
                "results_count": len(result_list),
                "vulnerable_count": sum(1 for r in result_list if r["vulnerable"])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 查询验证任务详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询任务详情失败: {str(e)}")


@router.post("/tasks/{task_id}/pause", response_model=Dict[str, Any])
async def pause_verification_task(task_id: UUID):
    """
    暂停 POC 验证任务
    
    暂停正在执行的 POC 验证任务。
    
    Args:
        task_id: 任务 ID
        
    Returns:
        Dict: 暂停结果
    """
    try:
        success = await verification_engine.pause_verification_task(str(task_id))
        
        if success:
            return {
                "code": 200,
                "message": "验证任务已暂停"
            }
        else:
            raise HTTPException(status_code=400, detail="任务状态不允许暂停")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 暂停验证任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"暂停任务失败: {str(e)}")


@router.post("/tasks/{task_id}/resume", response_model=Dict[str, Any])
async def resume_verification_task(task_id: UUID):
    """
    继续 POC 验证任务
    
    继续已暂停的 POC 验证任务。
    
    Args:
        task_id: 任务 ID
        
    Returns:
        Dict: 继续结果
    """
    try:
        success = await verification_engine.resume_verification_task(str(task_id))
        
        if success:
            return {
                "code": 200,
                "message": "验证任务已继续"
            }
        else:
            raise HTTPException(status_code=400, detail="任务状态不允许继续")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 继续验证任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"继续任务失败: {str(e)}")


@router.post("/tasks/{task_id}/cancel", response_model=Dict[str, Any])
async def cancel_verification_task(task_id: UUID):
    """
    取消 POC 验证任务
    
    取消正在执行或等待执行的 POC 验证任务。
    
    Args:
        task_id: 任务 ID
        
    Returns:
        Dict: 取消结果
    """
    try:
        success = await verification_engine.cancel_verification_task(str(task_id))
        
        if success:
            return {
                "code": 200,
                "message": "验证任务已取消"
            }
        else:
            raise HTTPException(status_code=400, detail="任务状态不允许取消")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 取消验证任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.get("/tasks/{task_id}/results", response_model=Dict[str, Any])
async def get_verification_results(task_id: UUID):
    """
    获取 POC 验证结果
    
    获取指定 POC 验证任务的所有验证结果。
    
    Args:
        task_id: 任务 ID
        
    Returns:
        Dict: 包含验证结果列表的响应
    """
    try:
        task = await POCVerificationTask.get_or_none(id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="验证任务不存在")
        
        # 获取所有结果
        results = await POCVerificationResult.filter(
            verification_task=task.id
        ).order_by("-created_at")
        
        result_list = []
        for result in results:
            result_list.append({
                "result_id": result.id,
                "poc_name": result.poc_name,
                "poc_id": result.poc_id,
                "target": result.target,
                "vulnerable": result.vulnerable,
                "message": result.message,
                "output": result.output,
                "error": result.error,
                "execution_time": result.execution_time,
                "confidence": result.confidence,
                "severity": result.severity,
                "cvss_score": result.cvss_score,
                "created_at": result.created_at.isoformat()
            })
        
        return {
            "code": 200,
            "message": "查询验证结果成功",
            "data": {
                "task_id": str(task_id),
                "results": result_list,
                "total_count": len(result_list),
                "vulnerable_count": sum(1 for r in result_list if r["vulnerable"]),
                "not_vulnerable_count": sum(1 for r in result_list if not r["vulnerable"])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 查询验证结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询验证结果失败: {str(e)}")


@router.post("/tasks/{task_id}/report", response_model=Dict[str, Any])
async def generate_verification_report(
    task_id: UUID,
    format: str = Query("html", description="报告格式"),
    output_path: Optional[str] = Query(None, description="输出文件路径")
):
    """
    生成 POC 验证报告
    
    生成指定 POC 验证任务的报告,支持 HTML、JSON、PDF 格式。
    
    Args:
        task_id: 任务 ID
        format: 报告格式(html, json, pdf)
        output_path: 输出文件路径
        
    Returns:
        Dict: 包含报告内容的响应
    """
    try:
        task = await POCVerificationTask.get_or_none(id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="验证任务不存在")
        
        # 生成报告
        report = await report_generator.generate_report(
            verification_task=task,
            format=format,
            output_path=output_path
        )
        
        return {
            "code": 200,
            "message": "报告生成成功",
            "data": {
                "task_id": str(task_id),
                "format": format,
                "report": report if not output_path else f"报告已保存到: {output_path}",
                "generated_at": task.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 生成验证报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_verification_statistics():
    """
    获取 POC 验证统计信息
    
    获取 POC 验证引擎的统计信息。
    
    Returns:
        Dict: 包含统计信息的响应
    """
    try:
        stats = await verification_engine.get_engine_statistics()
        
        return {
            "code": 200,
            "message": "查询统计信息成功",
            "data": stats
        }
    except Exception as e:
        logger.error(f"❌ 查询统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询统计信息失败: {str(e)}")


@router.get("/poc/registry", response_model=Dict[str, Any])
async def get_poc_registry():
    """
    获取 POC 注册表
    
    获取所有已注册的 POC 列表。
    
    Returns:
        Dict: 包含 POC 列表的响应
    """
    try:
        pocs = poc_manager.get_all_pocs()
        
        poc_list = []
        for poc in pocs:
            poc_list.append(poc.to_dict())
        
        return {
            "code": 200,
            "message": "查询 POC 注册表成功",
            "data": {
                "total": len(poc_list),
                "pocs": poc_list
            }
        }
    except Exception as e:
        logger.error(f"❌ 查询 POC 注册表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询 POC 注册表失败: {str(e)}")


@router.post("/poc/sync", response_model=Dict[str, Any])
async def sync_pocs_from_seebug(
    keyword: str = Query("", description="搜索关键词"),
    limit: int = Query(100, ge=1, le=1000, description="同步数量限制"),
    force_refresh: bool = Query(False, description="是否强制刷新缓存")
):
    """
    从 Seebug 同步 POC
    
    从 Seebug 平台同步 POC 脚本到本地注册表。
    
    Args:
        keyword: 搜索关键词
        limit: 同步数量限制
        force_refresh: 是否强制刷新缓存
        
    Returns:
        Dict: 包含同步结果的响应
    """
    try:
        poc_metadata_list = await poc_manager.sync_from_seebug(
            keyword=keyword,
            limit=limit,
            force_refresh=force_refresh
        )
        
        poc_list = []
        for poc in poc_metadata_list:
            poc_list.append(poc.to_dict())
        
        return {
            "code": 200,
            "message": "POC 同步成功",
            "data": {
                "synced_count": len(poc_list),
                "pocs": poc_list,
                "cache_stats": poc_manager.get_cache_stats()
            }
        }
    except Exception as e:
        logger.error(f"❌ 同步 POC 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"同步 POC 失败: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    健康检查
    
    检查 POC 验证系统的健康状态。
    
    Returns:
        Dict: 包含健康状态的响应
    """
    try:
        stats = await verification_engine.get_engine_statistics()
        
        return {
            "code": 200,
            "message": "POC 验证系统运行正常",
            "data": {
                "status": "healthy",
                "enabled": settings.POC_VERIFICATION_ENABLED,
                "config": {
                    "max_concurrent_executions": settings.POC_MAX_CONCURRENT_EXECUTIONS,
                    "execution_timeout": settings.POC_EXECUTION_TIMEOUT,
                    "max_retries": settings.POC_RETRY_MAX_COUNT,
                    "result_accuracy_threshold": settings.POC_RESULT_ACCURACY_THRESHOLD,
                    "cache_enabled": settings.POC_CACHE_ENABLED,
                    "cache_ttl": settings.POC_CACHE_TTL
                },
                "statistics": stats
            }
        }
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {str(e)}")
        return {
            "code": 500,
            "message": "POC 验证系统异常",
            "data": {
                "status": "unhealthy",
                "error": str(e)
            }
        }

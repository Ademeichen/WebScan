"""
报告管理相关的 API 路由
已迁移至数据库存储（Tortoise-ORM）
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


# 请求模型
class ReportCreate(BaseModel):
    task_id: int
    report_name: str
    report_type: str  # pdf, html, json, etc.


class ReportUpdate(BaseModel):
    report_name: Optional[str] = None
    content: Optional[Dict[str, Any]] = None


# 响应模型
class ReportResponse(BaseModel):
    id: int
    task_id: int
    report_name: str
    report_type: str
    content: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class APIResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


@router.get("/", response_model=APIResponse)
async def list_reports(
    task_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20
):
    """
    获取报告列表（使用数据库）
    """
    try:
        from models import Report
        
        # 构建查询条件
        query = Report.all()
        
        # 过滤条件
        if task_id:
            query = query.filter(task_id=task_id)
        
        # 排序（最新的在前）
        query = query.order_by('-created_at')
        
        # 获取总数
        total = await query.count()
        
        # 分页查询
        reports = await query.offset(skip).limit(limit)
        
        # 转换为字典格式
        report_list = []
        for report in reports:
            report_dict = {
                "id": report.id,
                "task_id": report.task_id,
                "report_name": report.report_name,
                "report_type": report.report_type,
                "content": json.loads(report.content) if report.content else None,
                "created_at": report.created_at,
                "updated_at": report.updated_at
            }
            report_list.append(report_dict)
        
        return APIResponse(
            code=200,
            message="获取成功",
            data={
                "reports": report_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        logger.error(f"获取报告列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=APIResponse)
async def create_report(report: ReportCreate):
    """
    创建新报告（使用数据库）
    """
    try:
        from models import Report
        
        # 验证任务是否存在
        from models import Task
        task = await Task.get_or_none(id=report.task_id)
        if not task:
            raise HTTPException(status_code=400, detail="任务不存在")
        
        # 创建报告记录
        new_report = await Report.create(
            task_id=report.task_id,
            report_name=report.report_name,
            report_type=report.report_type,
            content=None
        )
        
        logger.info(f"创建报告: {report.report_name} (ID: {new_report.id})")
        
        # TODO: 根据任务数据生成报告内容
        # new_report['content'] = generate_report_content(report.task_id, report.report_type)
        
        # 转换为字典格式
        report_dict = {
            "id": new_report.id,
            "task_id": new_report.task_id,
            "report_name": new_report.report_name,
            "report_type": new_report.report_type,
            "content": None,
            "created_at": new_report.created_at,
            "updated_at": new_report.updated_at
        }
        
        return APIResponse(code=200, message="报告创建成功", data=report_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}", response_model=APIResponse)
async def get_report(report_id: int):
    """
    获取报告详情（使用数据库）
    """
    try:
        from models import Report
        
        report = await Report.get_or_none(id=report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        # 转换为字典格式
        report_dict = {
            "id": report.id,
            "task_id": report.task_id,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "content": json.loads(report.content) if report.content else None,
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
        
        return APIResponse(code=200, message="获取成功", data=report_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{report_id}", response_model=APIResponse)
async def update_report(report_id: int, report_update: ReportUpdate):
    """
    更新报告（使用数据库）
    """
    try:
        from models import Report
        
        report = await Report.get_or_none(id=report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        # 构建更新数据
        update_data = {}
        if report_update.report_name:
            update_data['report_name'] = report_update.report_name
        if report_update.content is not None:
            update_data['content'] = json.dumps(report_update.content)
        
        # 更新报告
        if update_data:
            for key, value in update_data.items():
                setattr(report, key, value)
            await report.save()
        
        # 重新获取更新后的报告
        report = await Report.get(id=report_id)
        
        logger.info(f"更新报告: {report_id}")
        
        # 转换为字典格式
        report_dict = {
            "id": report.id,
            "task_id": report.task_id,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "content": json.loads(report.content) if report.content else None,
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
        
        return APIResponse(code=200, message="更新成功", data=report_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{report_id}", response_model=APIResponse)
async def delete_report(report_id: int):
    """
    删除报告（使用数据库）
    """
    try:
        from models import Report
        
        report = await Report.get_or_none(id=report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        report_name = report.report_name
        
        # 删除报告
        await report.delete()
        
        logger.info(f"删除报告: {report_name} (ID: {report_id})")
        return APIResponse(code=200, message="删除成功", data=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/export", response_model=APIResponse)
async def export_report(report_id: int, format: str = "json"):
    """
    导出报告（使用数据库）
    """
    try:
        from models import Report
        
        report = await Report.get_or_none(id=report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        # TODO: 根据格式导出报告
        # if format == "pdf":
        #     return generate_pdf_report(report)
        # elif format == "html":
        #     return generate_html_report(report)
        
        logger.info(f"导出报告: {report_id} (格式: {format})")
        
        # 转换为字典格式
        report_dict = {
            "id": report.id,
            "task_id": report.task_id,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "content": json.loads(report.content) if report.content else None,
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
        
        return APIResponse(code=200, message="导出成功", data=report_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

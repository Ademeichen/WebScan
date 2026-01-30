"""
报告管理相关的 API 路由
已迁移至数据库存储(Tortoise-ORM)
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import json
from urllib.parse import quote
from models import Report, Task, Vulnerability

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_html_report(report_data):
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>{report_data.get('report_name', '安全扫描报告')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #e9ecef; }}
            .vuln {{ border: 1px solid #ddd; margin-bottom: 20px; padding: 20px; border-radius: 8px; background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            .critical {{ border-left: 5px solid #c0392b; }}
            .high {{ border-left: 5px solid #e74c3c; }}
            .medium {{ border-left: 5px solid #f39c12; }}
            .low {{ border-left: 5px solid #3498db; }}
            .info {{ border-left: 5px solid #95a5a6; }}
            .label {{ font-weight: bold; color: #555; }}
            .vuln-title {{ margin-top: 0; }}
            .stats-list {{ list-style: none; padding: 0; display: flex; gap: 20px; }}
            .stats-item {{ text-align: center; padding: 10px; background: #fff; border-radius: 4px; min-width: 80px; border: 1px solid #eee; }}
            .stats-count {{ display: block; font-size: 24px; font-weight: bold; }}
            .stats-label {{ font-size: 12px; color: #777; }}
        </style>
    </head>
    <body>
        <h1>{report_data.get('report_name', '安全扫描报告')}</h1>
        
        <div class="summary">
            <h2>扫描摘要</h2>
            <p><span class="label">任务名称:</span> {report_data.get('task_name', 'N/A')}</p>
            <p><span class="label">目标:</span> {report_data.get('target', 'N/A')}</p>
            <p><span class="label">扫描时间:</span> {report_data.get('scan_time', 'N/A')}</p>
            
            <h3>漏洞统计</h3>
            <ul class="stats-list">
                <li class="stats-item" style="border-top: 3px solid #c0392b;">
                    <span class="stats-count" style="color: #c0392b;">{report_data.get('summary', {}).get('critical', 0)}</span>
                    <span class="stats-label">严重</span>
                </li>
                <li class="stats-item" style="border-top: 3px solid #e74c3c;">
                    <span class="stats-count" style="color: #e74c3c;">{report_data.get('summary', {}).get('high', 0)}</span>
                    <span class="stats-label">高危</span>
                </li>
                <li class="stats-item" style="border-top: 3px solid #f39c12;">
                    <span class="stats-count" style="color: #f39c12;">{report_data.get('summary', {}).get('medium', 0)}</span>
                    <span class="stats-label">中危</span>
                </li>
                <li class="stats-item" style="border-top: 3px solid #3498db;">
                    <span class="stats-count" style="color: #3498db;">{report_data.get('summary', {}).get('low', 0)}</span>
                    <span class="stats-label">低危</span>
                </li>
                <li class="stats-item" style="border-top: 3px solid #95a5a6;">
                    <span class="stats-count" style="color: #95a5a6;">{report_data.get('summary', {}).get('info', 0)}</span>
                    <span class="stats-label">信息</span>
                </li>
            </ul>
        </div>
        
        <h2>漏洞详情</h2>
    """
    
    for vuln in report_data.get('vulnerabilities', []):
        severity = vuln.get('severity', 'info')
        severity_class = severity.lower() if severity else 'info'
        
        html += f"""
        <div class="vuln {severity_class}">
            <h3 class="vuln-title">{vuln.get('title', 'Unknown Vulnerability')}</h3>
            <p><span class="label">等级:</span> {severity}</p>
            <p><span class="label">URL:</span> {vuln.get('url', 'N/A')}</p>
            <p><span class="label">描述:</span></p>
            <p>{vuln.get('description', 'N/A')}</p>
            <p><span class="label">修复建议:</span></p>
            <p>{vuln.get('remediation', 'N/A')}</p>
        </div>
        """
        
    html += """
    </body>
    </html>
    """
    return html


# 请求模型
class ReportCreate(BaseModel):
    task_id: int
    name: str  # Frontend sends 'name'
    format: str  # Frontend sends 'format'
    content: Optional[List[str]] = []  # Frontend sends 'content' list


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
    获取报告列表(使用数据库)
    """
    try:
        query = Report.all()
        
        # 过滤条件
        if task_id:
            query = query.filter(task_id=task_id)
        
        # 排序(最新的在前)
        query = query.order_by('-created_at')
        
        # 获取总数
        total = await query.count()
        
        # 分页查询
        reports = await query.prefetch_related('task').offset(skip).limit(limit)
        
        # 转换为字典格式
        report_list = []
        for report in reports:
            content_str = report.content or ""
            size_bytes = len(content_str.encode('utf-8'))
            if size_bytes < 1024:
                size = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size = f"{size_bytes / 1024:.1f} KB"
            else:
                size = f"{size_bytes / (1024 * 1024):.1f} MB"

            report_dict = {
                "id": report.id,
                "task_id": report.task_id,
                "task_name": report.task.task_name if report.task else "Unknown Task",
                "report_name": report.report_name,
                "report_type": report.report_type,
                "content": json.loads(report.content) if report.content else None,
                "size": size,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": report.updated_at.strftime("%Y-%m-%d %H:%M:%S")
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
    创建新报告(使用数据库)
    """
    try:
        task = await Task.get_or_none(id=report.task_id)
        if not task:
            raise HTTPException(status_code=400, detail="任务不存在")
        
        # 生成报告内容
        vulns = await Vulnerability.filter(task_id=task.id).all()
        vuln_list = []
        stats = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for v in vulns:
            vuln_list.append({
                "title": v.title,
                "severity": v.severity,
                "url": v.url,
                "description": v.description,
                "remediation": v.remediation
            })
            s = v.severity.lower()
            if s in stats:
                stats[s] += 1
            else:
                stats["info"] += 1

        report_content = {
            "task_name": task.task_name,
            "target": task.target,
            "scan_time": str(task.created_at),
            "summary": stats,
            "vulnerabilities": vuln_list
        }

        # 创建报告记录
        new_report = await Report.create(
            task_id=report.task_id,
            report_name=report.name,
            report_type=report.format,
            content=json.dumps(report_content)
        )
        
        logger.info(f"创建报告: {report.name} (ID: {new_report.id})")
        
        # 转换为字典格式
        report_dict = {
            "id": new_report.id,
            "task_id": new_report.task_id,
            "report_name": new_report.report_name,
            "report_type": new_report.report_type,
            "content": report_content,
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
    获取报告详情(使用数据库)
    """
    try:
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
    更新报告(使用数据库)
    """
    try:
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
    删除报告(使用数据库)
    """
    try:
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

@router.get("/{report_id}/export")
async def export_report(report_id: int, format: str = "json"):
    """
    导出报告(使用数据库)
    """
    try:
        report = await Report.get_or_none(id=report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        content = json.loads(report.content) if report.content else {}
        
        if format == "html":
            html_content = generate_html_report(content)
            filename = quote(f"{report.report_name}.html")
            return Response(
                content=html_content,
                media_type="text/html",
                headers={"Content-Disposition": f"attachment; filename={filename}; filename*=utf-8''{filename}"}
            )
        elif format == "json":
            filename = quote(f"{report.report_name}.json")
            return JSONResponse(
                content=content,
                headers={"Content-Disposition": f"attachment; filename={filename}; filename*=utf-8''{filename}"}
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}。目前仅支持 html 和 json。")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

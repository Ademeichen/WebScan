"""
报告管理相关的 API 路由
已迁移至数据库存储(Tortoise-ORM)

优化功能：
- 报告预览API
- 报告对比API
- 多格式导出（HTML、PDF、JSON、Markdown）
- AWVS报告集成
- 完善错误处理
"""
from fastapi import APIRouter, HTTPException, Response, Query, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import json
import asyncio
from urllib.parse import quote
from enum import Enum

from backend.models import Report, Task, Vulnerability
from backend.api.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class ReportFormat(str, Enum):
    """报告格式枚举"""
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"


SEVERITY_CONFIG = {
    "critical": {"color": "#c0392b", "label": "严重"},
    "high": {"color": "#e74c3c", "label": "高危"},
    "medium": {"color": "#f39c12", "label": "中危"},
    "low": {"color": "#3498db", "label": "低危"},
    "info": {"color": "#95a5a6", "label": "信息"}
}


class ReportCreate(BaseModel):
    """创建报告请求模型"""
    task_id: int
    name: str = Field(..., description="报告名称")
    format: str = Field(default="json", description="报告格式")
    content: Optional[Dict[str, Any]] = None
    include_awvs: bool = Field(default=False, description="是否包含AWVS数据")


class ReportUpdate(BaseModel):
    """更新报告请求模型"""
    report_name: Optional[str] = None
    content: Optional[Dict[str, Any]] = None


class ReportCompareRequest(BaseModel):
    """报告对比请求模型"""
    report_id_1: int
    report_id_2: int


class ReportResponse(BaseModel):
    """报告响应模型"""
    id: int
    task_id: int
    report_name: str
    report_type: str
    content: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


def calculate_risk_score(vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    计算风险评分
    
    Args:
        vulnerabilities: 漏洞列表
        
    Returns:
        风险评估结果
    """
    if not vulnerabilities:
        return {"score": 0.0, "level": "info", "label": "无风险", "color": "#95a5a6"}
    
    severity_scores = {"critical": 10.0, "high": 8.0, "medium": 5.0, "low": 3.0, "info": 1.0}
    base_score = 0.0
    
    for vuln in vulnerabilities:
        severity = vuln.get("severity", "info").lower()
        base_score += severity_scores.get(severity, 1.0)
    
    max_possible = len(vulnerabilities) * 10.0
    normalized_score = min(100.0, (base_score / max_possible) * 100) if max_possible > 0 else 0.0
    
    if normalized_score >= 80:
        level, label, color = "critical", "极高风险", "#c0392b"
    elif normalized_score >= 60:
        level, label, color = "high", "高风险", "#e74c3c"
    elif normalized_score >= 40:
        level, label, color = "medium", "中等风险", "#f39c12"
    elif normalized_score >= 20:
        level, label, color = "low", "低风险", "#3498db"
    else:
        level, label, color = "info", "信息", "#95a5a6"
    
    return {
        "score": round(normalized_score, 2),
        "level": level,
        "label": label,
        "color": color
    }


def generate_html_report(report_data: Dict[str, Any]) -> str:
    """
    生成HTML格式报告
    
    Args:
        report_data: 报告数据
        
    Returns:
        HTML报告内容
    """
    risk = calculate_risk_score(report_data.get('vulnerabilities', []))
    summary = report_data.get('summary', {})
    
    vuln_items = ""
    for vuln in report_data.get('vulnerabilities', []):
        severity = vuln.get('severity', 'info').lower()
        config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG['info'])
        
        vuln_items += f"""
        <div class="vuln-item" style="border-left: 5px solid {config['color']};">
            <h3 class="vuln-title">{vuln.get('title', 'Unknown Vulnerability')}</h3>
            <p><span class="label">等级:</span> <span style="color: {config['color']}; font-weight: bold;">{config['label']}</span></p>
            <p><span class="label">URL:</span> {vuln.get('url', 'N/A')}</p>
            <p><span class="label">描述:</span></p>
            <p>{vuln.get('description', 'N/A')}</p>
            <p><span class="label">修复建议:</span></p>
            <p>{vuln.get('remediation', 'N/A')}</p>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{report_data.get('report_name', '安全扫描报告')}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; margin-bottom: 30px; }}
            .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
            .header .meta {{ font-size: 14px; opacity: 0.9; }}
            
            .risk-gauge {{ background: white; border-radius: 10px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .risk-gauge h2 {{ color: #333; margin-bottom: 20px; }}
            .gauge-container {{ display: flex; align-items: center; gap: 30px; flex-wrap: wrap; }}
            .gauge {{ width: 200px; height: 200px; position: relative; }}
            .gauge-value {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 48px; font-weight: bold; }}
            .risk-details {{ flex: 1; min-width: 300px; }}
            .risk-level {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
            
            .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .card {{ background: white; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .card .count {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
            .card .label {{ font-size: 14px; color: #666; }}
            
            .section {{ background: white; border-radius: 10px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .section h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
            
            .vuln-item {{ border: 1px solid #eee; border-radius: 8px; padding: 20px; margin-bottom: 15px; }}
            .vuln-title {{ margin-top: 0; color: #333; }}
            .label {{ font-weight: bold; color: #555; }}
            
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            
            @media print {{
                body {{ background: white; }}
                .section, .card, .vuln-item {{ box-shadow: none; border: 1px solid #ddd; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔒 安全扫描报告</h1>
                <div class="meta">
                    <p>报告名称: {report_data.get('report_name', 'N/A')}</p>
                    <p>任务名称: {report_data.get('task_name', 'N/A')}</p>
                    <p>目标: {report_data.get('target', 'N/A')}</p>
                    <p>扫描时间: {report_data.get('scan_time', 'N/A')}</p>
                </div>
            </div>
            
            <div class="risk-gauge">
                <h2>📊 风险评估</h2>
                <div class="gauge-container">
                    <div class="gauge">
                        <svg viewBox="0 0 200 200">
                            <circle cx="100" cy="100" r="80" fill="none" stroke="#eee" stroke-width="20"/>
                            <circle cx="100" cy="100" r="80" fill="none" stroke="{risk['color']}" stroke-width="20"
                                stroke-dasharray="{risk['score'] * 5.03} 503"
                                stroke-linecap="round" transform="rotate(-90 100 100)"/>
                        </svg>
                        <div class="gauge-value" style="color: {risk['color']};">{risk['score']}</div>
                    </div>
                    <div class="risk-details">
                        <div class="risk-level" style="color: {risk['color']};">风险等级: {risk['label']}</div>
                        <p>综合风险评分基于漏洞数量、严重程度计算得出。</p>
                    </div>
                </div>
            </div>
            
            <div class="summary-cards">
                <div class="card" style="border-top: 4px solid #c0392b;">
                    <div class="label">严重</div>
                    <div class="count" style="color: #c0392b;">{summary.get('critical', 0)}</div>
                </div>
                <div class="card" style="border-top: 4px solid #e74c3c;">
                    <div class="label">高危</div>
                    <div class="count" style="color: #e74c3c;">{summary.get('high', 0)}</div>
                </div>
                <div class="card" style="border-top: 4px solid #f39c12;">
                    <div class="label">中危</div>
                    <div class="count" style="color: #f39c12;">{summary.get('medium', 0)}</div>
                </div>
                <div class="card" style="border-top: 4px solid #3498db;">
                    <div class="label">低危</div>
                    <div class="count" style="color: #3498db;">{summary.get('low', 0)}</div>
                </div>
                <div class="card" style="border-top: 4px solid #95a5a6;">
                    <div class="label">信息</div>
                    <div class="count" style="color: #95a5a6;">{summary.get('info', 0)}</div>
                </div>
            </div>
            
            <div class="section">
                <h2>🔍 漏洞详情</h2>
                {vuln_items if vuln_items else '<p>未发现漏洞</p>'}
            </div>
            
            <div class="footer">
                <p>报告由 AI_WebSecurity 自动生成 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def generate_markdown_report(report_data: Dict[str, Any]) -> str:
    """
    生成Markdown格式报告
    
    Args:
        report_data: 报告数据
        
    Returns:
        Markdown报告内容
    """
    risk = calculate_risk_score(report_data.get('vulnerabilities', []))
    summary = report_data.get('summary', {})
    
    md = f"""# {report_data.get('report_name', '安全扫描报告')}

## 基本信息

- **任务名称**: {report_data.get('task_name', 'N/A')}
- **目标**: {report_data.get('target', 'N/A')}
- **扫描时间**: {report_data.get('scan_time', 'N/A')}

## 风险评估

- **风险评分**: {risk['score']}
- **风险等级**: {risk['label']}

## 漏洞统计

| 严重程度 | 数量 |
|---------|------|
| 严重 | {summary.get('critical', 0)} |
| 高危 | {summary.get('high', 0)} |
| 中危 | {summary.get('medium', 0)} |
| 低危 | {summary.get('low', 0)} |
| 信息 | {summary.get('info', 0)} |

## 漏洞详情

"""
    for vuln in report_data.get('vulnerabilities', []):
        severity = vuln.get('severity', 'info').lower()
        config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG['info'])
        
        md += f"""### {vuln.get('title', 'Unknown Vulnerability')}

- **严重程度**: {config['label']}
- **URL**: {vuln.get('url', 'N/A')}
- **描述**: {vuln.get('description', 'N/A')}
- **修复建议**: {vuln.get('remediation', 'N/A')}

---

"""
    
    md += f"\n---\n*报告由 AI_WebSecurity 自动生成 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
    
    return md


@router.get("/", response_model=APIResponse)
async def list_reports(
    task_id: Optional[int] = None,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    获取报告列表
    
    Args:
        task_id: 可选，按任务ID过滤
        skip: 跳过数量
        limit: 返回数量
        
    Returns:
        APIResponse: 报告列表
    """
    try:
        logger.info("[报告列表] 开始获取报告列表")
        query = Report.all()
        
        if task_id:
            query = query.filter(task_id=task_id)
        
        query = query.order_by('-created_at')
        
        total = await query.count()
        
        reports = await query.prefetch_related('task').offset(skip).limit(limit)
        logger.info(f"[报告列表] 获取成功 | 报告数量: {total}")
        
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
                "created_at": report.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": report.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
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
        logger.error(f"[报告列表] 获取失败 | 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取报告列表失败: {str(e)}")


@router.post("/", response_model=APIResponse)
async def create_report(report: ReportCreate):
    """
    创建新报告
    
    Args:
        report: 报告创建请求
        
    Returns:
        APIResponse: 创建的报告信息
    """
    try:
        logger.info(f"[创建报告] 开始处理请求 | 任务ID: {report.task_id} | 报告名称: {report.name} | 格式: {report.format}")
        
        task = await Task.get_or_none(id=report.task_id)
        if not task:
            logger.warning(f"[创建报告] 任务不存在 | 任务ID: {report.task_id}")
            raise HTTPException(status_code=400, detail="任务不存在")
        
        logger.info(f"[创建报告] 查询任务漏洞 | 任务ID: {report.task_id}")
        vulns = await Vulnerability.filter(task_id=task.id).all()
        logger.info(f"[创建报告] 漏洞查询完成 | 漏洞数量: {len(vulns)}")
        
        vuln_list = []
        stats = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for v in vulns:
            vuln_list.append({
                "id": v.id,
                "title": v.title,
                "name": v.title,
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

        logger.info(f"[创建报告] 漏洞统计 | critical: {stats['critical']}, high: {stats['high']}, medium: {stats['medium']}, low: {stats['low']}, info: {stats['info']}")

        report_content = {
            "task_name": task.task_name,
            "target": task.target,
            "scan_time": str(task.created_at),
            "summary": stats,
            "vulnerabilities": vuln_list
        }

        if report.include_awvs and task.task_type == 'awvs_scan':
            awvs_vulns = await Vulnerability.filter(task_id=task.id, source='awvs').all()
            report_content['awvs_vulnerabilities'] = [{
                "id": v.id,
                "title": v.title,
                "severity": v.severity,
                "url": v.url,
                "description": v.description,
                "source_id": v.source_id
            } for v in awvs_vulns]
            logger.info(f"[创建报告] AWVS漏洞集成 | 数量: {len(awvs_vulns)}")

        logger.info(f"[创建报告] 创建报告记录 | 任务ID: {report.task_id}")
        new_report = await Report.create(
            task_id=report.task_id,
            report_name=report.name,
            report_type=report.format,
            content=json.dumps(report_content)
        )
        
        logger.info(f"[创建报告] 报告创建成功 | 报告ID: {new_report.id} | 报告名称: {report.name}")
        
        risk = calculate_risk_score(vuln_list)
        
        report_dict = {
            "id": new_report.id,
            "task_id": new_report.task_id,
            "task_type": task.task_type,
            "target_url": task.target,
            "report_name": new_report.report_name,
            "report_type": new_report.report_type,
            "content": report_content,
            "created_at": new_report.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": new_report.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_vulnerabilities": sum(stats.values()),
            "critical_count": stats.get('critical', 0),
            "high_count": stats.get('high', 0),
            "medium_count": stats.get('medium', 0),
            "low_count": stats.get('low', 0),
            "info_count": stats.get('info', 0),
            "risk_assessment": risk
        }
        
        return APIResponse(code=200, message="报告创建成功", data=report_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[创建报告] 创建失败 | 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建报告失败: {str(e)}")


@router.get("/{report_id}", response_model=APIResponse)
async def get_report(report_id: int):
    """
    获取报告详情
    
    Args:
        report_id: 报告ID
        
    Returns:
        APIResponse: 报告详情
    """
    try:
        logger.info(f"[报告详情] 开始获取报告 | 报告ID: {report_id}")
        report = await Report.filter(id=report_id).prefetch_related('task').first()
        
        if not report:
            logger.warning(f"[报告详情] 报告不存在 | 报告ID: {report_id}")
            raise HTTPException(status_code=404, detail="报告不存在")
        
        logger.info(f"[报告详情] 报告获取成功 | 报告ID: {report_id}")
        
        content_data = json.loads(report.content) if report.content else {}
        summary = content_data.get('summary', {})
        
        risk = calculate_risk_score(content_data.get('vulnerabilities', []))

        report_dict = {
            "id": report.id,
            "task_id": report.task_id,
            "task_type": report.task.task_type if report.task else None,
            "target_url": report.task.target if report.task else None,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "content": content_data,
            "created_at": report.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": report.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_vulnerabilities": sum(summary.values()) if summary else 0,
            "critical_count": summary.get('critical', 0),
            "high_count": summary.get('high', 0),
            "medium_count": summary.get('medium', 0),
            "low_count": summary.get('low', 0),
            "info_count": summary.get('info', 0),
            "risk_assessment": risk
        }
        
        return APIResponse(code=200, message="获取成功", data=report_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[报告详情] 获取失败 | 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取报告详情失败: {str(e)}")


@router.put("/{report_id}", response_model=APIResponse)
async def update_report(report_id: int, report_update: ReportUpdate):
    """
    更新报告
    
    Args:
        report_id: 报告ID
        report_update: 更新请求
        
    Returns:
        APIResponse: 更新后的报告信息
    """
    try:
        report = await Report.get_or_none(id=report_id)

        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        update_data = {}
        if report_update.report_name:
            update_data['report_name'] = report_update.report_name
        if report_update.content is not None:
            update_data['content'] = json.dumps(report_update.content)

        if update_data:
            for key, value in update_data.items():
                setattr(report, key, value)
            await report.save()

        report = await Report.filter(id=report_id).prefetch_related('task').first()
        
        logger.info(f"[更新报告] 更新成功 | 报告ID: {report_id}")
        
        content_data = json.loads(report.content) if report.content else {}
        summary = content_data.get('summary', {})

        report_dict = {
            "id": report.id,
            "task_id": report.task_id,
            "task_type": report.task.task_type if report.task else None,
            "target_url": report.task.target if report.task else None,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "content": content_data,
            "created_at": report.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": report.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_vulnerabilities": sum(summary.values()) if summary else 0,
            "critical_count": summary.get('critical', 0),
            "high_count": summary.get('high', 0),
            "medium_count": summary.get('medium', 0),
            "low_count": summary.get('low', 0),
            "info_count": summary.get('info', 0),
        }
        
        return APIResponse(code=200, message="更新成功", data=report_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[更新报告] 更新失败 | 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新报告失败: {str(e)}")


@router.delete("/{report_id}", response_model=APIResponse)
async def delete_report(report_id: int):
    """
    删除报告
    
    Args:
        report_id: 报告ID
        
    Returns:
        APIResponse: 删除结果
    """
    try:
        report = await Report.get_or_none(id=report_id)

        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        report_name = report.report_name

        await report.delete()

        logger.info(f"[删除报告] 删除成功 | 报告: {report_name} (ID: {report_id})")
        return APIResponse(code=200, message="删除成功", data=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[删除报告] 删除失败 | 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除报告失败: {str(e)}")


@router.get("/{report_id}/export")
async def export_report(
    report_id: int, 
    format: str = Query("json", description="导出格式: json, html, markdown, pdf")
):
    """
    导出报告
    
    Args:
        report_id: 报告ID
        format: 导出格式 (json, html, markdown, pdf)
        
    Returns:
        Response: 导出的报告文件
    """
    try:
        report = await Report.get_or_none(id=report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        content = json.loads(report.content) if report.content else {}
        content['report_name'] = report.report_name
        
        format = format.lower()
        
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
        elif format == "markdown" or format == "md":
            md_content = generate_markdown_report(content)
            filename = quote(f"{report.report_name}.md")
            return PlainTextResponse(
                content=md_content,
                media_type="text/markdown",
                headers={"Content-Disposition": f"attachment; filename={filename}; filename*=utf-8''{filename}"}
            )
        elif format == "pdf":
            html_content = generate_html_report(content)
            filename = quote(f"{report.report_name}.html")
            return Response(
                content=html_content,
                media_type="text/html",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}; filename*=utf-8''{filename}",
                    "X-Export-Format": "pdf-ready"
                }
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}。支持的格式: html, json, markdown, pdf")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[导出报告] 导出失败 | 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出报告失败: {str(e)}")


@router.get("/{report_id}/preview", response_model=APIResponse)
async def preview_report(report_id: int):
    """
    预览报告
    
    Args:
        report_id: 报告ID
        
    Returns:
        APIResponse: 报告预览数据
    """
    try:
        logger.info(f"[报告预览] 开始预览 | 报告ID: {report_id}")
        report = await Report.filter(id=report_id).prefetch_related('task').first()
        
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        content_data = json.loads(report.content) if report.content else {}
        summary = content_data.get('summary', {})
        vulnerabilities = content_data.get('vulnerabilities', [])
        
        risk = calculate_risk_score(vulnerabilities)
        
        preview_data = {
            "id": report.id,
            "report_name": report.report_name,
            "task_name": content_data.get('task_name'),
            "target": content_data.get('target'),
            "scan_time": content_data.get('scan_time'),
            "summary": summary,
            "risk_assessment": risk,
            "vulnerabilities_preview": vulnerabilities[:5],
            "total_vulnerabilities": len(vulnerabilities),
            "has_more": len(vulnerabilities) > 5,
            "export_formats": ["json", "html", "markdown", "pdf"]
        }
        
        logger.info(f"[报告预览] 预览成功 | 报告ID: {report_id}")
        return APIResponse(code=200, message="获取预览成功", data=preview_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[报告预览] 预览失败 | 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"预览报告失败: {str(e)}")


@router.post("/compare", response_model=APIResponse)
async def compare_reports(request: ReportCompareRequest):
    """
    对比两个报告
    
    Args:
        request: 对比请求
        
    Returns:
        APIResponse: 对比结果
    """
    try:
        logger.info(f"[报告对比] 开始对比 | 报告1: {request.report_id_1} | 报告2: {request.report_id_2}")
        
        report1 = await Report.get_or_none(id=request.report_id_1)
        report2 = await Report.get_or_none(id=request.report_id_2)
        
        if not report1:
            raise HTTPException(status_code=404, detail=f"报告 {request.report_id_1} 不存在")
        if not report2:
            raise HTTPException(status_code=404, detail=f"报告 {request.report_id_2} 不存在")
        
        content1 = json.loads(report1.content) if report1.content else {}
        content2 = json.loads(report2.content) if report2.content else {}
        
        summary1 = content1.get('summary', {})
        summary2 = content2.get('summary', {})
        
        vulns1 = {v.get('id', v.get('title')): v for v in content1.get('vulnerabilities', [])}
        vulns2 = {v.get('id', v.get('title')): v for v in content2.get('vulnerabilities', [])}
        
        new_vulns = []
        fixed_vulns = []
        persistent_vulns = []
        
        for vuln_id, vuln in vulns2.items():
            if vuln_id not in vulns1:
                new_vulns.append(vuln)
            else:
                persistent_vulns.append(vuln)
        
        for vuln_id, vuln in vulns1.items():
            if vuln_id not in vulns2:
                fixed_vulns.append(vuln)
        
        risk1 = calculate_risk_score(content1.get('vulnerabilities', []))
        risk2 = calculate_risk_score(content2.get('vulnerabilities', []))
        
        comparison = {
            "report_1": {
                "id": report1.id,
                "name": report1.report_name,
                "target": content1.get('target'),
                "scan_time": content1.get('scan_time'),
                "summary": summary1,
                "risk_assessment": risk1
            },
            "report_2": {
                "id": report2.id,
                "name": report2.report_name,
                "target": content2.get('target'),
                "scan_time": content2.get('scan_time'),
                "summary": summary2,
                "risk_assessment": risk2
            },
            "changes": {
                "new_vulnerabilities": {
                    "count": len(new_vulns),
                    "items": new_vulns[:10]
                },
                "fixed_vulnerabilities": {
                    "count": len(fixed_vulns),
                    "items": fixed_vulns[:10]
                },
                "persistent_vulnerabilities": {
                    "count": len(persistent_vulns)
                }
            },
            "summary_diff": {
                "critical": summary2.get('critical', 0) - summary1.get('critical', 0),
                "high": summary2.get('high', 0) - summary1.get('high', 0),
                "medium": summary2.get('medium', 0) - summary1.get('medium', 0),
                "low": summary2.get('low', 0) - summary1.get('low', 0),
                "info": summary2.get('info', 0) - summary1.get('info', 0)
            },
            "risk_diff": {
                "score": risk2['score'] - risk1['score'],
                "improved": risk2['score'] < risk1['score']
            }
        }
        
        logger.info(f"[报告对比] 对比完成 | 新增: {len(new_vulns)} | 修复: {len(fixed_vulns)}")
        return APIResponse(code=200, message="对比完成", data=comparison)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[报告对比] 对比失败 | 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"报告对比失败: {str(e)}")


@router.get("/task/{task_id}/latest", response_model=APIResponse)
async def get_latest_report_by_task(task_id: int):
    """
    获取指定任务的最新报告
    
    Args:
        task_id: 任务ID
        
    Returns:
        APIResponse: 最新报告信息
    """
    try:
        logger.info(f"[最新报告] 开始获取 | 任务ID: {task_id}")
        
        task = await Task.get_or_none(id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        report = await Report.filter(task_id=task_id).order_by('-created_at').first()
        
        if not report:
            return APIResponse(code=404, message="该任务暂无报告", data=None)
        
        content_data = json.loads(report.content) if report.content else {}
        summary = content_data.get('summary', {})
        
        risk = calculate_risk_score(content_data.get('vulnerabilities', []))
        
        report_dict = {
            "id": report.id,
            "task_id": report.task_id,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "content": content_data,
            "created_at": report.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": report.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_vulnerabilities": sum(summary.values()) if summary else 0,
            "risk_assessment": risk
        }
        
        logger.info(f"[最新报告] 获取成功 | 任务ID: {task_id} | 报告ID: {report.id}")
        return APIResponse(code=200, message="获取成功", data=report_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[最新报告] 获取失败 | 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取最新报告失败: {str(e)}")


@router.post("/{report_id}/regenerate", response_model=APIResponse)
async def regenerate_report(report_id: int, background_tasks: BackgroundTasks):
    """
    重新生成报告
    
    Args:
        report_id: 报告ID
        background_tasks: 后台任务
        
    Returns:
        APIResponse: 重新生成结果
    """
    try:
        logger.info(f"[重新生成] 开始 | 报告ID: {report_id}")
        
        report = await Report.get_or_none(id=report_id).prefetch_related('task')
        
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        task = report.task
        if not task:
            raise HTTPException(status_code=400, detail="关联任务不存在")
        
        vulns = await Vulnerability.filter(task_id=task.id).all()
        
        vuln_list = []
        stats = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for v in vulns:
            vuln_list.append({
                "id": v.id,
                "title": v.title,
                "severity": v.severity,
                "url": v.url,
                "description": v.description,
                "remediation": v.remediation
            })
            s = v.severity.lower()
            if s in stats:
                stats[s] += 1
        
        report_content = {
            "task_name": task.task_name,
            "target": task.target,
            "scan_time": str(task.created_at),
            "summary": stats,
            "vulnerabilities": vuln_list,
            "regenerated_at": datetime.now().isoformat()
        }
        
        report.content = json.dumps(report_content)
        await report.save()
        
        risk = calculate_risk_score(vuln_list)
        
        logger.info(f"[重新生成] 完成 | 报告ID: {report_id}")
        
        return APIResponse(
            code=200, 
            message="报告重新生成成功", 
            data={
                "report_id": report.id,
                "total_vulnerabilities": len(vuln_list),
                "risk_assessment": risk
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[重新生成] 失败 | 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重新生成报告失败: {str(e)}")

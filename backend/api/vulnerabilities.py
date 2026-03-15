"""
漏洞管理 API 路由

提供漏洞详情查询、更新、统计等功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from tortoise.functions import Count
from tortoise.expressions import Q

from backend.models import Task, Vulnerability, VulnerabilityKB
from backend.api.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def standardize_severity(severity_val) -> str:
    """标准化严重程度"""
    if isinstance(severity_val, int):
        if severity_val >= 4: return 'Critical'
        if severity_val == 3: return 'High'
        if severity_val == 2: return 'Medium'
        if severity_val == 1: return 'Low'
        return 'Info'
    
    if isinstance(severity_val, str):
        s = severity_val.lower()
        if s == 'critical': return 'Critical'
        if s == 'high': return 'High'
        if s == 'medium': return 'Medium'
        if s == 'low': return 'Low'
        if s == 'info': return 'Info'
        return severity_val.capitalize()
    
    return 'Info'


class VulnerabilityUpdate(BaseModel):
    """漏洞更新请求模型"""
    status: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    remediation: Optional[str] = None


@router.get("/", response_model=APIResponse)
async def list_vulnerabilities(
    severity: Optional[str] = None,
    vuln_type: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    task_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    获取漏洞列表
    
    支持按严重程度、类型、来源、状态等过滤
    """
    try:
        query = Vulnerability.all()
        
        if severity:
            query = query.filter(severity__icontains=severity)
        if vuln_type:
            query = query.filter(vuln_type__icontains=vuln_type)
        if source:
            query = query.filter(source__icontains=source)
        if status:
            query = query.filter(status__icontains=status)
        if task_id:
            query = query.filter(task_id=task_id)
        if search:
            query = query.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) | 
                Q(url__icontains=search)
            )
        
        query = query.order_by('-created_at')
        
        total = await query.count()
        vulns = await query.offset(skip).limit(limit)
        
        vuln_list = []
        for vuln in vulns:
            vuln_list.append({
                "id": vuln.id,
                "title": vuln.title,
                "type": vuln.vuln_type,
                "severity": standardize_severity(vuln.severity),
                "status": vuln.status,
                "url": vuln.url,
                "description": vuln.description[:200] + '...' if vuln.description and len(vuln.description) > 200 else vuln.description,
                "source": vuln.source,
                "task_id": vuln.task_id,
                "created_at": vuln.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if vuln.created_at else None,
                "updated_at": vuln.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if vuln.updated_at else None
            })
        
        return APIResponse(
            code=200,
            message="获取成功",
            data={
                "vulnerabilities": vuln_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        logger.error(f"获取漏洞列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=APIResponse)
async def get_vulnerability_statistics():
    """
    获取漏洞统计信息
    
    包括总数、各严重程度数量、各类型数量等
    """
    try:
        total = await Vulnerability.all().count()
        
        severity_stats = await Vulnerability.all().group_by('severity').annotate(count=Count('id')).values('severity', 'count')
        severity_counts = {}
        for item in severity_stats:
            s = standardize_severity(item['severity'])
            severity_counts[s] = severity_counts.get(s, 0) + item['count']
        
        type_stats = await Vulnerability.all().group_by('vuln_type').annotate(count=Count('id')).values('vuln_type', 'count')
        type_counts = {item['vuln_type'] or 'Unknown': item['count'] for item in type_stats}
        
        status_stats = await Vulnerability.all().group_by('status').annotate(count=Count('id')).values('status', 'count')
        status_counts = {item['status'] or 'open': item['count'] for item in status_stats}
        
        source_stats = await Vulnerability.all().group_by('source').annotate(count=Count('id')).values('source', 'count')
        source_counts = {item['source'] or 'unknown': item['count'] for item in source_stats}
        
        return APIResponse(
            code=200,
            message="获取成功",
            data={
                "total": total,
                "by_severity": severity_counts,
                "by_type": type_counts,
                "by_status": status_counts,
                "by_source": source_counts
            }
        )
    except Exception as e:
        logger.error(f"获取漏洞统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vuln_id}", response_model=APIResponse)
async def get_vulnerability_detail(vuln_id: int):
    """
    获取漏洞详情
    
    优先级：
    1. Vulnerability表 - 扫描任务发现的漏洞（与任务关联）
    2. VulnerabilityKB表 - 外部数据源的漏洞知识库（不与任务关联）
    
    如果Vulnerability表中不存在，会尝试从外部数据源获取并存储到VulnerabilityKB表。
    """
    try:
        from backend.api.kb import fetch_seebug_data, fetch_exploit_db_data
        from backend.models import Vulnerability, VulnerabilityKB
        
        vuln = await Vulnerability.get_or_none(id=vuln_id).prefetch_related('task')
        
        if vuln:
            task_info = None
            if vuln.task:
                task_info = {
                    "id": vuln.task.id,
                    "task_name": vuln.task.task_name,
                    "task_type": vuln.task.task_type,
                    "target": vuln.task.target,
                    "status": vuln.task.status
                }
            
            vuln_data = {
                "id": vuln.id,
                "title": vuln.title,
                "type": vuln.vuln_type,
                "severity": standardize_severity(vuln.severity),
                "status": vuln.status,
                "url": vuln.url,
                "description": vuln.description,
                "payload": vuln.payload,
                "evidence": vuln.evidence,
                "remediation": vuln.remediation,
                "source": vuln.source,
                "source_id": vuln.source_id,
                "task_id": vuln.task_id,
                "task": task_info,
                "cvss_score": None,
                "affected_product": vuln.url,
                "discovered_at": vuln.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if vuln.created_at else None,
                "created_at": vuln.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if vuln.created_at else None,
                "updated_at": vuln.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if vuln.updated_at else None
            }
            
            return APIResponse(
                code=200,
                message="获取成功",
                data=vuln_data
            )
        
        logger.info(f"漏洞ID {vuln_id} 不存在于Vulnerability表，尝试从外部数据源获取并存储到VulnerabilityKB表")
        vuln_kb_data = None
        
        try:
            from backend.utils.seebug_utils import seebug_utils
            seebug_utils_instance = seebug_utils()
            
            if seebug_utils_instance.is_available():
                logger.info("尝试从 Seebug 获取漏洞详情")
                detail_result = await seebug_utils_instance.get_vulnerability_detail(str(vuln_id))
                
                if detail_result.get("status") == "success":
                    vuln_kb_data = detail_result.get("data", {})
                    logger.info(f"从 Seebug 获取到漏洞: {vuln_kb_data.get('name', 'Unknown')}")
                else:
                    logger.warning(f"Seebug 获取漏洞失败: {detail_result.get('msg', 'Unknown')}")
            
            if not vuln_kb_data:
                logger.info("Seebug 未获取到漏洞，尝试其他数据源")
        except Exception as e:
            logger.error(f"尝试从 Seebug 获取漏洞详情失败: {str(e)}")
            from backend.utils.seebug_utils import seebug_utils
            seebug_utils_instance = seebug_utils()
            
            if seebug_utils_instance.is_available():
                logger.info("尝试从 Seebug 获取漏洞详情")
                detail_result = await seebug_utils_instance.get_vulnerability_detail(str(vuln_id))
                
                if detail_result.get("status") == "success":
                    vuln_kb_data = detail_result.get("data", {})
                    logger.info(f"从 Seebug 获取到漏洞: {vuln_kb_data.get('name', 'Unknown')}")
                else:
                    logger.warning(f"Seebug 获取漏洞失败: {detail_result.get('msg', 'Unknown')}")
            
            if not vuln_kb_data:
                logger.info("Seebug 未获取到漏洞，尝试其他数据源")
        
        if vuln_kb_data:
            try:
                exists = await VulnerabilityKB.get_or_none(cve_id=vuln_kb_data.get('cve_id'))
                if not exists:
                    await VulnerabilityKB.create(
                        cve_id=vuln_kb_data.get('cve_id'),
                        name=vuln_kb_data.get('name', 'Unknown Vulnerability'),
                        description=vuln_kb_data.get('description', ''),
                        severity=vuln_kb_data.get('severity', 'Info'),
                        cvss_score=vuln_kb_data.get('cvss_score', 0.0),
                        affected_product=vuln_kb_data.get('affected_product', ''),
                        affected_versions=vuln_kb_data.get('affected_versions', ''),
                        poc_code=vuln_kb_data.get('poc_code', ''),
                        remediation=vuln_kb_data.get('remediation', ''),
                        references=vuln_kb_data.get('references', None),
                        has_poc=True,
                        source='seebug',
                        ssvid=str(vuln_kb_data.get('ssvid', ''))
                    )
                    logger.info(f"漏洞已保存到VulnerabilityKB表: {vuln_kb_data.get('name')}")
                
                vuln_kb = await VulnerabilityKB.get(cve_id=vuln_kb_data.get('cve_id'))
                
                task_info = None
                
                vuln_data = {
                    "id": vuln_kb.id,
                    "title": vuln_kb.name,
                    "type": vuln_kb.name,
                    "severity": standardize_severity(vuln_kb.severity),
                    "status": 'open',
                    "url": vuln_kb.affected_product,
                    "description": vuln_kb.description,
                    "payload": vuln_kb.poc_code,
                    "evidence": '',
                    "remediation": vuln_kb.remediation,
                    "source": vuln_kb.source,
                    "source_id": vuln_kb.ssvid,
                    "task_id": None,
                    "task": task_info,
                    "cvss_score": vuln_kb.cvss_score,
                    "affected_product": vuln_kb.affected_product,
                    "discovered_at": vuln_kb.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if vuln_kb.created_at else None,
                    "created_at": vuln_kb.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if vuln_kb.created_at else None,
                    "updated_at": vuln_kb.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if vuln_kb.updated_at else None
                }
                
                return APIResponse(
                    code=200,
                    message="获取成功",
                    data=vuln_data
                )
            except Exception as e:
                logger.error(f"保存漏洞到VulnerabilityKB表失败: {e}")
                raise HTTPException(status_code=500, detail=f"保存漏洞失败: {str(e)}")
        else:
            raise HTTPException(status_code=404, detail="漏洞不存在，且无法从外部数据源获取")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取漏洞详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vuln_id}/related", response_model=APIResponse)
async def get_related_vulnerabilities(vuln_id: int, limit: int = 5):
    """
    获取相关漏洞
    
    根据漏洞类型、严重程度等查找相关漏洞
    """
    try:
        current_vuln = await Vulnerability.get_or_none(id=vuln_id)
        if not current_vuln:
            return APIResponse(
                code=200,
                message="当前漏洞不存在",
                data=[]
            )
        
        related = []
        
        same_type_vulns = await Vulnerability.filter(
            vuln_type=current_vuln.vuln_type,
            id__not=vuln_id
        ).order_by('-created_at').limit(limit)
        
        for v in same_type_vulns:
            related.append({
                "id": v.id,
                "title": v.title,
                "type": v.vuln_type,
                "severity": standardize_severity(v.severity),
                "status": v.status,
                "url": v.url,
                "source": v.source,
                "created_at": v.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if v.created_at else None
            })
        
        if len(related) < limit:
            same_severity_vulns = await Vulnerability.filter(
                severity=current_vuln.severity,
                id__not=vuln_id
            ).exclude(id__in=[v['id'] for v in related]).order_by('-created_at').limit(limit - len(related))
            
            for v in same_severity_vulns:
                related.append({
                    "id": v.id,
                    "title": v.title,
                    "type": v.vuln_type,
                    "severity": standardize_severity(v.severity),
                    "status": v.status,
                    "url": v.url,
                    "source": v.source,
                    "created_at": v.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if v.created_at else None
                })
        
        return APIResponse(
            code=200,
            message="获取成功",
            data=related
        )
    except Exception as e:
        logger.error(f"获取相关漏洞失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{vuln_id}", response_model=APIResponse)
async def update_vulnerability(vuln_id: int, update_data: VulnerabilityUpdate):
    """
    更新漏洞信息
    
    更新漏洞状态、严重程度、描述等
    """
    try:
        vuln = await Vulnerability.get_or_none(id=vuln_id)
        if not vuln:
            raise HTTPException(status_code=404, detail="漏洞不存在")
        
        if update_data.status:
            valid_statuses = ['open', 'fixed', 'ignored', 'reopened']
            if update_data.status.lower() not in valid_statuses:
                raise HTTPException(status_code=400, detail=f"无效的状态值，可选值: {valid_statuses}")
            vuln.status = update_data.status.lower()
        
        if update_data.severity:
            vuln.severity = standardize_severity(update_data.severity)
        
        if update_data.description is not None:
            vuln.description = update_data.description
        
        if update_data.remediation is not None:
            vuln.remediation = update_data.remediation
        
        await vuln.save()
        
        return APIResponse(
            code=200,
            message="更新成功",
            data={
                "id": vuln.id,
                "status": vuln.status,
                "severity": vuln.severity
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新漏洞失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{vuln_id}", response_model=APIResponse)
async def delete_vulnerability(vuln_id: int):
    """
    删除漏洞
    
    根据漏洞ID删除漏洞记录
    """
    try:
        vuln = await Vulnerability.get_or_none(id=vuln_id)
        if not vuln:
            raise HTTPException(status_code=404, detail="漏洞不存在")
        
        await vuln.delete()
        
        return APIResponse(
            code=200,
            message="删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除漏洞失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{vuln_id}/mark-fixed", response_model=APIResponse)
async def mark_vulnerability_fixed(vuln_id: int):
    """
    标记漏洞为已修复
    """
    try:
        vuln = await Vulnerability.get_or_none(id=vuln_id)
        if not vuln:
            raise HTTPException(status_code=404, detail="漏洞不存在")
        
        vuln.status = 'fixed'
        await vuln.save()
        
        return APIResponse(
            code=200,
            message="已标记为已修复",
            data={
                "id": vuln.id,
                "status": vuln.status
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记漏洞失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

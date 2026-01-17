"""
系统设置相关的 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from tortoise.functions import Count
from models import Task, Vulnerability

logger = logging.getLogger(__name__)

router = APIRouter()


# 响应模型
class APIResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


@router.get("/", response_model=APIResponse)
async def get_settings():
    """
    获取系统设置
    """
    try:
        # TODO: 从数据库或配置文件读取实际设置
        settings_data = {
            "general": {
                "systemName": "WebScan AI",
                "language": "zh-CN",
                "timezone": "Asia/Shanghai",
                "autoUpdate": True
            },
            "scan": {
                "defaultDepth": "2",
                "defaultConcurrency": 5,
                "requestTimeout": 30
            },
            "notification": {
                "emailEnabled": False,
                "smtpServer": "",
                "events": ["high-vulnerability"]
            },
            "security": {
                "sessionTimeout": 120,
                "requireHttps": True
            }
        }
        
        return APIResponse(
            code=200,
            message="获取成功",
            data=settings_data
        )
    except Exception as e:
        logger.error(f"获取系统设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




@router.put("/", response_model=APIResponse)
async def update_settings(settings: Dict[str, Any]):
    """
    更新系统设置
    """
    try:
        # TODO: 将设置保存到数据库或配置文件
        logger.info(f"更新系统设置: {settings}")
        
        return APIResponse(
            code=200,
            message="更新成功",
            data=settings
        )
    except Exception as e:
        logger.error(f"更新系统设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-info", response_model=APIResponse)
async def get_system_info():
    """
    获取系统信息
    """
    try:
        system_info = {
            "version": "1.0.0",
            "uptime": "2天 3小时 45分钟",
            "cpuUsage": "25%",
            "memoryUsage": "45%",
            "diskUsage": "60%"
        }
        
        return APIResponse(
            code=200,
            message="获取成功",
            data=system_info
        )
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=APIResponse)
async def get_statistics(period: int = 7):
    """
    获取统计信息
    """
    try:
        # 1. 今日扫描任务
        today = datetime.now().date()
        today_scans = await Task.filter(
            created_at__gte=datetime.combine(today, datetime.min.time())
        ).count()
        
        # 2. 未修复高危漏洞 (Critical + High)
        high_risk_vulns = await Vulnerability.filter(
            severity__in=['Critical', 'High'],
            status='open'
        ).count()
        
        # 3. 已完成扫描
        completed_scans = await Task.filter(status='completed').count()
        
        # 4. 趋势数据
        trend_data = []
        for i in range(period - 1, -1, -1):
            date = today - timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            # Count vulns created on this day
            daily_counts = await Vulnerability.filter(
                created_at__gte=datetime.combine(date, datetime.min.time()),
                created_at__lt=datetime.combine(next_date, datetime.min.time())
            ).group_by('severity').annotate(count=Count('id')).values('severity', 'count')
            
            day_stats = {
                'date': date.strftime("%m/%d"),
                'high': 0,
                'medium': 0,
                'low': 0
            }
            
            for item in daily_counts:
                sev = str(item['severity']).lower()
                if sev == 'critical':
                    day_stats['high'] += item['count'] # Merge critical into high for chart compatibility
                elif sev in day_stats:
                    day_stats[sev] += item['count']
            
            trend_data.append(day_stats)
            
        return APIResponse(
            code=200,
            message="获取成功",
            data={
                "today_scans": today_scans,
                "high_risk_vulns": high_risk_vulns,
                "weekly_trend": 0,
                "completed_scans": completed_scans,
                "trend_data": trend_data
            }
        )
    except Exception as e:
        logger.error(f"获取统计数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

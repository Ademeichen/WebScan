"""
系统设置相关的 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

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
async def get_statistics():
    """
    获取统计信息（用于仪表盘）
    """
    try:
        from models import Task, Vulnerability, POCScanResult
        from datetime import datetime, timedelta, time
        
        now = datetime.now()
        today_start = datetime.combine(now.date(), time.min)
        
        # 1. 今日扫描任务数量
        today_scans = await Task.filter(created_at__gte=today_start).count()
        
        # 2. 高危漏洞数量 (包括 Vulnerability 和 POCScanResult)
        # 注意: 这里的 severity 可能是 "Critical", "High" 等，需要根据实际存储的值匹配
        # 假设 severity 存储的是标准化后的值 (Critical, High, Medium, Low, Info)
        high_risk_vulns_scan = await Vulnerability.filter(severity__in=["Critical", "High"]).count()
        high_risk_vulns_poc = await POCScanResult.filter(vulnerable=True, severity__in=["Critical", "High"]).count()
        high_risk_vulns = high_risk_vulns_scan + high_risk_vulns_poc
        
        # 3. 已完成扫描总数
        completed_scans = await Task.filter(status="completed").count()
        
        # 4. 趋势数据 (最近7天漏洞趋势)
        trend_data = await generate_real_trend_data(7)
            
        # 5. 周环比 (简单计算：本周总数 vs 上周总数)
        week_start = now - timedelta(days=7)
        last_week_start = now - timedelta(days=14)
        
        this_week_count = await Task.filter(created_at__gte=week_start).count()
        last_week_count = await Task.filter(created_at__gte=last_week_start, created_at__lt=week_start).count()
        
        if last_week_count == 0:
            weekly_trend = 100 if this_week_count > 0 else 0
        else:
            weekly_trend = int(((this_week_count - last_week_count) / last_week_count) * 100)

        statistics = {
            "today_scans": today_scans,
            "high_risk_vulns": high_risk_vulns,
            "weekly_trend": weekly_trend,
            "completed_scans": completed_scans,
            "trend_data": trend_data
        }
        
        logger.info("获取统计数据成功")
        return APIResponse(
            code=200,
            message="获取成功",
            data=statistics
        )
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_real_trend_data(days: int) -> List[Dict[str, Any]]:
    """
    从数据库生成趋势数据
    """
    from models import Vulnerability
    from datetime import datetime, timedelta, time
    
    trend_data = []
    today = datetime.now().date()
    
    for i in range(days):
        date = today - timedelta(days=days - 1 - i)
        date_start = datetime.combine(date, time.min)
        date_end = datetime.combine(date, time.max)
        
        high = await Vulnerability.filter(
            created_at__range=(date_start, date_end),
            severity__in=['High', 'Critical']
        ).count()
        
        medium = await Vulnerability.filter(
            created_at__range=(date_start, date_end),
            severity='Medium'
        ).count()
        
        low = await Vulnerability.filter(
            created_at__range=(date_start, date_end),
            severity='Low'
        ).count()
        
        trend_data.append({
            "date": f"{date.month}/{date.day}",
            "high": high,
            "medium": medium,
            "low": low
        })
    
    return trend_data

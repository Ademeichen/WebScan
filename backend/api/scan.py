"""
扫描功能相关的 API 路由
整合原有的 backend.plugins 功能模块，统一使用异步任务执行
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import logging
import asyncio
import json

logger = logging.getLogger(__name__)

router = APIRouter()


# 请求模型
class IPRequest(BaseModel):
    ip: str


class URLRequest(BaseModel):
    url: str


class DomainRequest(BaseModel):
    domain: str


class PortScanRequest(BaseModel):
    ip: str
    ports: Optional[str] = "1-1000"  # 默认扫描端口范围


class SubdomainRequest(BaseModel):
    domain: str
    deep_scan: Optional[bool] = False


# 响应模型
class APIResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


# ==================== 端口扫描 ====================
@router.post("/port-scan", response_model=APIResponse)
async def port_scan(request: PortScanRequest):
    """
    端口扫描 (异步)
    """
    try:
        from backend.plugins.common.common import check_ip
        
        if not check_ip(request.ip):
            raise HTTPException(status_code=400, detail="请填写正确的IP地址")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"Port Scan: {request.ip}",
            task_type='scan_port',
            target=request.ip,
            status="pending",
            progress=0,
            config=json.dumps({'ports': request.ports}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=request.ip,
            scan_config={'ports': request.ports}
        ))
        
        return APIResponse(code=200, message="端口扫描任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"端口扫描启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 信息泄露检测 ====================
@router.post("/info-leak", response_model=APIResponse)
async def info_leak(request: URLRequest):
    """
    信息泄露检测 (异步)
    """
    try:
        from backend.plugins.common.common import check_url
        
        url = check_url(request.url)
        if not url:
            raise HTTPException(status_code=400, detail="请填写正确的URL地址")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"Info Leak: {url}",
            task_type='scan_infoleak',
            target=url,
            status="pending",
            progress=0,
            config=json.dumps({}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=url,
            scan_config={}
        ))
        
        return APIResponse(code=200, message="信息泄露检测任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"信息泄露检测启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 旁站扫描 ====================
@router.post("/web-side", response_model=APIResponse)
async def web_side_scan(request: IPRequest):
    """
    获取旁站信息 (异步)
    """
    try:
        from backend.plugins.common.common import check_ip
        
        if not check_ip(request.ip):
            raise HTTPException(status_code=400, detail="请填写正确的IP地址")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"Web Side: {request.ip}",
            task_type='scan_webside',
            target=request.ip,
            status="pending",
            progress=0,
            config=json.dumps({}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=request.ip,
            scan_config={}
        ))
        
        return APIResponse(code=200, message="旁站扫描任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"旁站扫描启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 网站基本信息 ====================
@router.post("/baseinfo", response_model=APIResponse)
async def get_base_info(request: URLRequest):
    """
    获取网站基本信息 (异步)
    """
    try:
        from backend.plugins.common.common import check_url
        
        url = check_url(request.url)
        if not url:
            raise HTTPException(status_code=400, detail="请填写正确的URL地址")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"Base Info: {url}",
            task_type='scan_baseinfo',
            target=url,
            status="pending",
            progress=0,
            config=json.dumps({}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=url,
            scan_config={}
        ))
        
        return APIResponse(code=200, message="网站基本信息获取任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"获取网站基本信息启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 网站权重 ====================
@router.post("/web-weight", response_model=APIResponse)
async def get_web_weight(request: URLRequest):
    """
    获取网站权重 (异步)
    """
    try:
        from backend.plugins.common.common import check_url
        
        url = check_url(request.url)
        if not url:
            raise HTTPException(status_code=400, detail="请填写正确的URL地址")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"Web Weight: {url}",
            task_type='scan_webweight',
            target=url,
            status="pending",
            progress=0,
            config=json.dumps({}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=url,
            scan_config={}
        ))
        
        return APIResponse(code=200, message="网站权重获取任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"获取网站权重启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== IP定位 ====================
@router.post("/ip-locating", response_model=APIResponse)
async def ip_locating(request: IPRequest):
    """
    IP定位 (异步)
    """
    try:
        from backend.plugins.common.common import check_ip
        
        if not check_ip(request.ip):
            raise HTTPException(status_code=400, detail="请填写正确的IP地址")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"IP Locating: {request.ip}",
            task_type='scan_iplocating',
            target=request.ip,
            status="pending",
            progress=0,
            config=json.dumps({}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=request.ip,
            scan_config={}
        ))
        
        return APIResponse(code=200, message="IP定位任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"IP定位启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CDN检测 ====================
@router.post("/cdn-check", response_model=APIResponse)
async def cdn_check(request: URLRequest):
    """
    CDN检测 (异步)
    """
    try:
        from backend.plugins.common.common import check_url
        
        url = check_url(request.url)
        if not url:
            raise HTTPException(status_code=400, detail="请填写正确的URL地址")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"CDN Check: {url}",
            task_type='scan_cdn',
            target=url,
            status="pending",
            progress=0,
            config=json.dumps({}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=url,
            scan_config={}
        ))
        
        return APIResponse(code=200, message="CDN检测任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"CDN检测启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WAF检测 ====================
@router.post("/waf-check", response_model=APIResponse)
async def waf_check(request: URLRequest):
    """
    WAF检测 (异步)
    """
    try:
        from backend.plugins.common.common import check_url
        
        url = check_url(request.url)
        if not url:
            raise HTTPException(status_code=400, detail="请填写正确的URL地址")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"WAF Check: {url}",
            task_type='scan_waf',
            target=url,
            status="pending",
            progress=0,
            config=json.dumps({}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=url,
            scan_config={}
        ))
        
        return APIResponse(code=200, message="WAF检测任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"WAF检测启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CMS指纹识别 ====================
@router.post("/what-cms", response_model=APIResponse)
async def what_cms(request: URLRequest):
    """
    CMS指纹识别 (异步)
    """
    try:
        from backend.plugins.common.common import check_url
        
        url = check_url(request.url)
        if not url:
            raise HTTPException(status_code=400, detail="请填写正确的URL地址")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"CMS Detect: {url}",
            task_type='scan_cms',
            target=url,
            status="pending",
            progress=0,
            config=json.dumps({}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=url,
            scan_config={}
        ))
        
        return APIResponse(code=200, message="CMS指纹识别任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"CMS指纹识别启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 子域名扫描 ====================
@router.post("/subdomain", response_model=APIResponse)
async def subdomain_scan(request: SubdomainRequest):
    """
    子域名扫描 (异步)
    """
    try:
        if not request.domain:
            raise HTTPException(status_code=400, detail="请填写正确的域名")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"Subdomain: {request.domain}",
            task_type='scan_subdomain',
            target=request.domain,
            status="pending",
            progress=0,
            config=json.dumps({'deep_scan': request.deep_scan}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=request.domain,
            scan_config={'deep_scan': request.deep_scan}
        ))
        
        return APIResponse(code=200, message="子域名扫描任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"子域名扫描启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 目录扫描 ====================
@router.post("/dir-scan", response_model=APIResponse)
async def dir_scan(request: URLRequest):
    """
    目录扫描 (异步)
    """
    try:
        from backend.plugins.common.common import check_url
        
        url = check_url(request.url)
        if not url:
            raise HTTPException(status_code=400, detail="请填写正确的URL地址")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"Dir Scan: {url}",
            task_type='scan_dir',
            target=url,
            status="pending",
            progress=0,
            config=json.dumps({}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=url,
            scan_config={}
        ))
        
        return APIResponse(code=200, message="目录扫描任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"目录扫描启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 综合扫描 ====================
@router.post("/comprehensive", response_model=APIResponse)
async def comprehensive_scan(request: URLRequest):
    """
    综合扫描 (异步)
    """
    try:
        from backend.plugins.common.common import check_url
        
        url = check_url(request.url)
        if not url:
            raise HTTPException(status_code=400, detail="请填写正确的URL地址")
        
        from models import Task
        new_task = await Task.create(
            task_name=f"Comprehensive: {url}",
            task_type='scan_comprehensive',
            target=url,
            status="pending",
            progress=0,
            config=json.dumps({}),
            result=None
        )
        
        from task_executor import task_executor
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=url,
            scan_config={}
        ))
        
        return APIResponse(code=200, message="综合扫描任务已启动", data={"task_id": new_task.id})
    except Exception as e:
        logger.error(f"综合扫描启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

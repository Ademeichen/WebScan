"""
POC 漏洞扫描 API 路由
提供中间件和框架的 CVE 漏洞检测接口

支持的 POC 类型:
- WebLogic: CVE-2020-2551, CVE-2018-2628, CVE-2018-2894, CVE-2020-14756, CVE-2023-21839
- Struts2: S2-009, S2-032
- Tomcat: CVE-2017-12615, CVE-2022-22965, CVE-2022-47986
- JBoss: CVE-2017-12149
- Nexus: CVE-2020-10199
- Drupal: CVE-2018-7600

主要功能:
- 创建和管理 POC 扫描任务
- 执行单个或批量 POC 漏洞检测
- 获取 POC 类型和详细信息
- 扫描结果存储和查询
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional, Any, Dict
import asyncio
import json
import logging
from datetime import datetime

from backend.poc import (
    cve_2020_2551_poc, cve_2018_2628_poc, cve_2018_2894_poc, cve_2020_14756_poc, cve_2023_21839_poc,
    struts2_009_poc, struts2_032_poc, cve_2017_12615_poc, cve_2022_22965_poc, cve_2022_47986_poc,
    cve_2017_12149_poc, cve_2020_10199_poc, cve_2018_7600_poc
)
from backend.api.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/poc", tags=["POC扫描"])


# 请求/响应模型
class POCScanRequest(BaseModel):
    """
    POC 扫描请求模型
    
    Attributes:
        target: 扫描目标 URL
        poc_types: POC 类型列表,如果不指定则扫描所有类型
        timeout: 超时时间(秒),默认 10 秒
    """
    target: str
    poc_types: Optional[List[str]] = None
    timeout: int = 10


class POCScanResult(BaseModel):
    """
    POC 扫描结果模型
    
    Attributes:
        poc_type: POC 类型
        target: 扫描目标
        vulnerable: 是否存在漏洞
        message: 扫描消息
        timestamp: 扫描时间戳
    """
    poc_type: str
    target: str
    vulnerable: bool
    message: str
    timestamp: str





# POC 映射表
POC_FUNCTIONS = {
    "weblogic_cve_2020_2551": cve_2020_2551_poc,
    "weblogic_cve_2018_2628": cve_2018_2628_poc,
    "weblogic_cve_2018_2894": cve_2018_2894_poc,
    "weblogic_cve_2020_14756": cve_2020_14756_poc,
    "weblogic_cve_2023_21839": cve_2023_21839_poc,
    "struts2_009": struts2_009_poc,
    "struts2_032": struts2_032_poc,
    "tomcat_cve_2017_12615": cve_2017_12615_poc,
    "tomcat_cve_2022_22965": cve_2022_22965_poc,
    "tomcat_cve_2022_47986": cve_2022_47986_poc,
    "jboss_cve_2017_12149": cve_2017_12149_poc,
    "nexus_cve_2020_10199": cve_2020_10199_poc,
    "drupal_cve_2018_7600": cve_2018_7600_poc,
}


@router.get("/types", response_model=APIResponse)
async def get_available_poc_types():
    """
    获取所有可用的 POC 类型
    
    返回系统支持的所有 POC 类型列表。
    
    Returns:
        APIResponse: POC 类型列表,包含value和label字段
        
    Examples:
        >>> 获取 POC 类型
        >>> GET /poc/types
        >>> {
        ...     "code": 200,
        ...     "message": "获取成功",
        ...     "data": [
        ...         {"value": "weblogic_cve_2020_2551", "label": "WebLogic CVE-2020-2551"},
        ...         {"value": "struts2_009", "label": "Struts2 S2-009"}
        ...     ]
        ... }
    """
    from backend.api.common import APIResponse
    
    poc_types = []
    for poc_key in POC_FUNCTIONS.keys():
        label = poc_key.replace('_', ' ').title()
        poc_types.append({
            "value": poc_key,
            "label": label
        })
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=poc_types
    ).model_dump()


@router.post("/scan", response_model=APIResponse)
async def scan_poc(request: POCScanRequest):
    """
    创建 POC 扫描任务(异步执行)
    
    创建一个新的 POC 扫描任务并启动异步执行。
    支持指定多个 POC 类型,如果不指定则扫描所有类型。
    
    Args:
        request: POC 扫描请求,包含目标 URL、POC 类型和超时时间
        
    Returns:
        APIResponse: 包含任务信息的响应,结构如下:
            {
                "code": 200,
                "message": "POC 扫描任务已创建",
                "data": {
                    "task_id": 任务ID,
                    "status": "pending",
                    "target": "目标URL",
                    "poc_count": POC数量
                }
            }
        
    Raises:
        HTTPException: 创建任务失败时抛出 500 错误
        
    Examples:
        >>> 扫描指定目标的所有 POC
        >>> POST /poc/scan
        >>> {
        ...     "target": "https://www.baidu.com",
        ...     "poc_types": ["weblogic_cve_2020_2551"],
        ...     "timeout": 10
        ... }
    """
    try:
        logger.info(f"[POC扫描] 开始处理请求 | 目标: {request.target} | POC类型: {request.poc_types}")
        
        from backend.models import Task
        from task_executor import task_executor
        
        # 1. 创建任务记录
        poc_types = request.poc_types if request.poc_types else list(POC_FUNCTIONS.keys())
        task_name = f"POC Scan: {request.target}"
        if len(poc_types) == 1:
            task_name = f"POC Scan ({poc_types[0]}): {request.target}"
        
        logger.info(f"[POC扫描] 创建任务 | 目标: {request.target} | POC数量: {len(poc_types)}")
        new_task = await Task.create(
            task_name=task_name,
            task_type="poc_scan",
            target=request.target,
            status="pending",
            progress=0,
            config=json.dumps({
                "poc_types": poc_types,
                "timeout": request.timeout
            }),
            result=None
        )
        logger.info(f"[POC扫描] 任务创建成功 | 任务ID: {new_task.id}")
        
        # 2. 启动异步任务
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=request.target,
            scan_config={
                "poc_types": poc_types,
                "timeout": request.timeout
            }
        ))
        logger.info(f"[POC扫描] 任务已启动执行 | 任务ID: {new_task.id}")
        
        # 3. 返回任务信息
        return APIResponse(
            code=200,
            message="POC 扫描任务已创建",
            data={
                "task_id": new_task.id,
                "status": "pending",
                "target": request.target,
                "poc_count": len(poc_types)
            }
        )
        
    except Exception as e:
        logger.error(f"[POC扫描] 任务执行失败 | 目标: {request.target} | 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/info/{poc_type}")
async def get_poc_info(poc_type: str):
    """
    获取 POC 详细信息
    
    获取指定 POC 类型的详细信息,包括名称、描述、严重程度和 CVE 编号。
    支持按类别查询（如 weblogic）或按具体POC类型查询（如 weblogic_cve_2020_2551）。
    
    Args:
        poc_type: POC 类型或类别
        
    Returns:
        Dict: POC 详细信息或该类别下的所有POC信息
        
    Raises:
        HTTPException: POC 类型不存在时抛出 404 错误
        
    Examples:
        >>> 获取 WebLogic 类别的所有POC信息
        >>> GET /poc/info/weblogic
        >>> 获取 WebLogic CVE-2020-2551 信息
        >>> GET /poc/info/weblogic_cve_2020_2551
    """
    poc_info = {
        "weblogic_cve_2020_2551": {
            "name": "WebLogic CVE-2020-2551",
            "description": "WebLogic Server 反序列化漏洞",
            "severity": "高危",
            "cve": "CVE-2020-2551",
            "category": "weblogic"
        },
        "weblogic_cve_2018_2628": {
            "name": "WebLogic CVE-2018-2628",
            "description": "WebLogic Server 反序列化漏洞",
            "severity": "高危",
            "cve": "CVE-2018-2628",
            "category": "weblogic"
        },
        "weblogic_cve_2018_2894": {
            "name": "WebLogic CVE-2018-2894",
            "description": "WebLogic Server 任意文件上传漏洞",
            "severity": "高危",
            "cve": "CVE-2018-2894",
            "category": "weblogic"
        },
        "weblogic_cve_2020_14756": {
            "name": "WebLogic CVE-2020-14756",
            "description": "WebLogic Server 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2020-14756",
            "category": "weblogic"
        },
        "weblogic_cve_2023_21839": {
            "name": "WebLogic CVE-2023-21839",
            "description": "WebLogic Server 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2023-21839",
            "category": "weblogic"
        },
        "struts2_009": {
            "name": "Struts2 S2-009",
            "description": "Struts2 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2011-3923",
            "category": "struts2"
        },
        "struts2_032": {
            "name": "Struts2 S2-032",
            "description": "Struts2 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2016-3081",
            "category": "struts2"
        },
        "tomcat_cve_2017_12615": {
            "name": "Tomcat CVE-2017-12615",
            "description": "Tomcat 任意文件写入漏洞",
            "severity": "高危",
            "cve": "CVE-2017-12615",
            "category": "tomcat"
        },
        "tomcat_cve_2022_22965": {
            "name": "Tomcat CVE-2022-22965",
            "description": "Spring Framework 远程代码执行漏洞 (Spring4Shell)",
            "severity": "高危",
            "cve": "CVE-2022-22965",
            "category": "tomcat"
        },
        "tomcat_cve_2022_47986": {
            "name": "Tomcat CVE-2022-47986",
            "description": "Aspera Faspex 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2022-47986",
            "category": "tomcat"
        },
        "jboss_cve_2017_12149": {
            "name": "JBoss CVE-2017-12149",
            "description": "JBoss 反序列化漏洞",
            "severity": "高危",
            "cve": "CVE-2017-12149",
            "category": "jboss"
        },
        "nexus_cve_2020_10199": {
            "name": "Nexus CVE-2020-10199",
            "description": "Nexus Repository Manager 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2020-10199",
            "category": "nexus"
        },
        "drupal_cve_2018_7600": {
            "name": "Drupal CVE-2018-7600",
            "description": "Drupal 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2018-7600",
            "category": "drupal"
        }
    }
    
    if poc_type in poc_info:
        return poc_info[poc_type]
    
    categories = ["weblogic", "struts2", "tomcat", "jboss", "nexus", "drupal"]
    if poc_type in categories:
        category_pocs = {k: v for k, v in poc_info.items() if v.get("category") == poc_type}
        if category_pocs:
            return category_pocs
    
    raise HTTPException(status_code=404, detail=f"未知的 POC 类型: {poc_type}")


@router.get("/download/{poc_type}")
async def download_poc(poc_type: str):
    """
    下载 POC 脚本
    
    下载指定 POC 类型的脚本代码，用于离线分析或自定义修改。
    
    Args:
        poc_type: POC 类型
        
    Returns:
        Dict: 包含 POC 代码的响应
        
    Raises:
        HTTPException: POC 类型不存在时抛出 404 错误
    """
    if poc_type not in POC_FUNCTIONS:
        raise HTTPException(status_code=404, detail=f"未知的 POC 类型: {poc_type}")
    
    try:
        import inspect
        poc_func = POC_FUNCTIONS[poc_type]
        source_code = inspect.getsource(poc_func)
        
        poc_info_map = {
            "weblogic_cve_2020_2551": {"name": "WebLogic CVE-2020-2551", "cve": "CVE-2020-2551", "severity": "高危"},
            "weblogic_cve_2018_2628": {"name": "WebLogic CVE-2018-2628", "cve": "CVE-2018-2628", "severity": "高危"},
            "weblogic_cve_2018_2894": {"name": "WebLogic CVE-2018-2894", "cve": "CVE-2018-2894", "severity": "高危"},
            "weblogic_cve_2020_14756": {"name": "WebLogic CVE-2020-14756", "cve": "CVE-2020-14756", "severity": "高危"},
            "weblogic_cve_2023_21839": {"name": "WebLogic CVE-2023-21839", "cve": "CVE-2023-21839", "severity": "高危"},
            "struts2_009": {"name": "Struts2 S2-009", "cve": "CVE-2011-3923", "severity": "高危"},
            "struts2_032": {"name": "Struts2 S2-032", "cve": "CVE-2016-3081", "severity": "高危"},
            "tomcat_cve_2017_12615": {"name": "Tomcat CVE-2017-12615", "cve": "CVE-2017-12615", "severity": "高危"},
            "tomcat_cve_2022_22965": {"name": "Tomcat CVE-2022-22965", "cve": "CVE-2022-22965", "severity": "高危"},
            "tomcat_cve_2022_47986": {"name": "Tomcat CVE-2022-47986", "cve": "CVE-2022-47986", "severity": "高危"},
            "jboss_cve_2017_12149": {"name": "JBoss CVE-2017-12149", "cve": "CVE-2017-12149", "severity": "高危"},
            "nexus_cve_2020_10199": {"name": "Nexus CVE-2020-10199", "cve": "CVE-2020-10199", "severity": "高危"},
            "drupal_cve_2018_7600": {"name": "Drupal CVE-2018-7600", "cve": "CVE-2018-7600", "severity": "高危"}
        }
        
        info = poc_info_map.get(poc_type, {"name": poc_type, "cve": "Unknown", "severity": "Unknown"})
        
        return {
            "poc_type": poc_type,
            "name": info["name"],
            "cve": info["cve"],
            "severity": info["severity"],
            "source_code": source_code,
            "language": "python",
            "download_time": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"下载 POC 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载 POC 失败: {str(e)}")




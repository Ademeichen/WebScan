"""
POC 漏洞扫描 API 路由
提供中间件和框架的 CVE 漏洞检测接口

支持的 POC 类型：
- WebLogic: CVE-2020-2551, CVE-2018-2628, CVE-2018-2894, CVE-2020-14756, CVE-2023-21839
- Struts2: S2-009, S2-032
- Tomcat: CVE-2017-12615, CVE-2022-22965, CVE-2022-47986
- JBoss: CVE-2017-12149
- Nexus: CVE-2020-10199
- Drupal: CVE-2018-7600

主要功能：
- 创建和管理 POC 扫描任务
- 执行单个或批量 POC 漏洞检测
- 获取 POC 类型和详细信息
- 扫描结果存储和查询
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import asyncio
import json
import logging
from datetime import datetime

from backend.poc import (
    cve_2020_2551_poc, cve_2018_2628_poc, cve_2018_2894_poc, cve_2020_14756_poc, cve_2023_21839_poc,
    struts2_009_poc, struts2_032_poc, cve_2017_12615_poc, cve_2022_22965_poc, cve_2022_47986_poc,
    cve_2017_12149_poc, cve_2020_10199_poc, cve_2018_7600_poc
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/poc", tags=["POC扫描"])


# 请求/响应模型
class POCScanRequest(BaseModel):
    """
    POC 扫描请求模型
    
    Attributes:
        target: 扫描目标 URL
        poc_types: POC 类型列表，如果不指定则扫描所有类型
        timeout: 超时时间（秒），默认 10 秒
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


class APIResponse(BaseModel):
    """
    统一 API 响应模型
    
    Attributes:
        code: 响应状态码，200 表示成功
        message: 响应消息
        data: 响应数据，可选
    """
    code: int
    message: str
    data: Optional[Any] = None


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


@router.get("/types", response_model=List[str])
async def get_available_poc_types():
    """
    获取所有可用的 POC 类型
    
    返回系统支持的所有 POC 类型列表。
    
    Returns:
        List[str]: POC 类型列表
        
    Examples:
        >>> 获取 POC 类型
        >>> GET /poc/types
        >>> ["weblogic_cve_2020_2551", "struts2_009", ...]
    """
    return list(POC_FUNCTIONS.keys())


@router.post("/scan", response_model=APIResponse)
async def scan_poc(request: POCScanRequest):
    """
    创建 POC 扫描任务（异步执行）
    
    创建一个新的 POC 扫描任务并启动异步执行。
    支持指定多个 POC 类型，如果不指定则扫描所有类型。
    
    Args:
        request: POC 扫描请求，包含目标 URL、POC 类型和超时时间
        
    Returns:
        APIResponse: 包含任务信息的响应，结构如下:
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
        from models import Task
        from task_executor import task_executor
        
        # 1. 创建任务记录
        poc_types = request.poc_types if request.poc_types else list(POC_FUNCTIONS.keys())
        task_name = f"POC Scan: {request.target}"
        if len(poc_types) == 1:
            task_name = f"POC Scan ({poc_types[0]}): {request.target}"
            
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
        
        # 2. 启动异步任务
        asyncio.create_task(task_executor.start_task(
            task_id=new_task.id,
            target=request.target,
            scan_config={
                "poc_types": poc_types,
                "timeout": request.timeout
            }
        ))
        
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
        logger.error(f"创建 POC 扫描任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/scan/{poc_type}", response_model=POCScanResult)
async def scan_single_poc(poc_type: str, target: str, timeout: int = 10):
    """
    执行单个 POC 漏洞扫描（并保存记录）
    
    对指定目标执行单个 POC 漏洞检测，并将结果保存到数据库。
    
    Args:
        poc_type: POC 类型
        target: 扫描目标 URL
        timeout: 超时时间（秒），默认 10 秒
        
    Returns:
        POCScanResult: 扫描结果，结构如下:
            {
                "poc_type": "POC类型",
                "target": "目标URL",
                "vulnerable": true/false,
                "message": "扫描消息",
                "timestamp": "时间戳"
            }
        
    Raises:
        HTTPException: POC 类型不存在或扫描失败时抛出错误
        
    Examples:
        >>> 扫描 WebLogic CVE-2020-2551
        >>> POST /poc/scan/weblogic_cve_2020_2551?target=https://www.baidu.com&timeout=10
    """
    if poc_type not in POC_FUNCTIONS:
        raise HTTPException(status_code=400, detail=f"未知的 POC 类型: {poc_type}")
    
    try:
        from models import Task, POCScanResult as DBPOCResult
        
        # 1. 创建任务记录
        task = await Task.create(
            task_name=f"Single POC: {poc_type} - {target}",
            task_type="poc_scan",
            target=target,
            status="running",
            progress=0,
            config=json.dumps({"poc_types": [poc_type], "timeout": timeout})
        )

        # 2. 执行扫描
        poc_func = POC_FUNCTIONS[poc_type]
        loop = asyncio.get_running_loop()
        is_vulnerable, message = await loop.run_in_executor(
            None, poc_func, target, timeout
        )
        
        # 3. 保存结果到数据库
        await DBPOCResult.create(
            task=task,
            poc_type=poc_type,
            target=target,
            vulnerable=is_vulnerable,
            message=message,
            severity="High" # 默认为高危，后续可根据POC信息调整
        )

        # 4. 更新任务状态
        task.status = "completed"
        task.progress = 100
        task.result = json.dumps({
            "vulnerable": is_vulnerable,
            "message": message
        })
        await task.save()
        
        return POCScanResult(
            poc_type=poc_type,
            target=target,
            vulnerable=is_vulnerable,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"单次 POC 扫描失败: {str(e)}")
        # 尝试更新任务为失败
        try:
            if 'task' in locals():
                task.status = "failed"
                task.error_message = str(e)
                await task.save()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"POC 扫描失败: {str(e)}")


@router.get("/info/{poc_type}")
async def get_poc_info(poc_type: str):
    """
    获取 POC 详细信息
    
    获取指定 POC 类型的详细信息，包括名称、描述、严重程度和 CVE 编号。
    
    Args:
        poc_type: POC 类型
        
    Returns:
        Dict: POC 详细信息，结构如下:
            {
                "name": "POC名称",
                "description": "POC描述",
                "severity": "严重程度",
                "cve": "CVE编号"
            }
        
    Raises:
        HTTPException: POC 类型不存在时抛出 404 错误
        
    Examples:
        >>> 获取 WebLogic CVE-2020-2551 信息
        >>> GET /poc/info/weblogic_cve_2020_2551
    """
    poc_info = {
        "weblogic_cve_2020_2551": {
            "name": "WebLogic CVE-2020-2551",
            "description": "WebLogic Server 反序列化漏洞",
            "severity": "高危",
            "cve": "CVE-2020-2551"
        },
        "weblogic_cve_2018_2628": {
            "name": "WebLogic CVE-2018-2628",
            "description": "WebLogic Server 反序列化漏洞",
            "severity": "高危",
            "cve": "CVE-2018-2628"
        },
        "weblogic_cve_2018_2894": {
            "name": "WebLogic CVE-2018-2894",
            "description": "WebLogic Server 任意文件上传漏洞",
            "severity": "高危",
            "cve": "CVE-2018-2894"
        },
        "weblogic_cve_2020_14756": {
            "name": "WebLogic CVE-2020-14756",
            "description": "WebLogic Server 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2020-14756"
        },
        "weblogic_cve_2023_21839": {
            "name": "WebLogic CVE-2023-21839",
            "description": "WebLogic Server 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2023-21839"
        },
        "struts2_009": {
            "name": "Struts2 S2-009",
            "description": "Struts2 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2011-3923"
        },
        "struts2_032": {
            "name": "Struts2 S2-032",
            "description": "Struts2 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2016-3081"
        },
        "tomcat_cve_2017_12615": {
            "name": "Tomcat CVE-2017-12615",
            "description": "Tomcat 任意文件写入漏洞",
            "severity": "高危",
            "cve": "CVE-2017-12615"
        },
        "tomcat_cve_2022_22965": {
            "name": "Tomcat CVE-2022-22965",
            "description": "Spring Framework 远程代码执行漏洞 (Spring4Shell)",
            "severity": "高危",
            "cve": "CVE-2022-22965"
        },
        "tomcat_cve_2022_47986": {
            "name": "Tomcat CVE-2022-47986",
            "description": "Aspera Faspex 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2022-47986"
        },
        "jboss_cve_2017_12149": {
            "name": "JBoss CVE-2017-12149",
            "description": "JBoss 反序列化漏洞",
            "severity": "高危",
            "cve": "CVE-2017-12149"
        },
        "nexus_cve_2020_10199": {
            "name": "Nexus CVE-2020-10199",
            "description": "Nexus Repository Manager 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2020-10199"
        },
        "drupal_cve_2018_7600": {
            "name": "Drupal CVE-2018-7600",
            "description": "Drupal 远程代码执行漏洞",
            "severity": "高危",
            "cve": "CVE-2018-7600"
        }
    }
    
    if poc_type not in poc_info:
        raise HTTPException(status_code=404, detail=f"未知的 POC 类型: {poc_type}")
    
    return poc_info[poc_type]

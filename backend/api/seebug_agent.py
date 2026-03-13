"""
Seebug Agent API路由模块

提供Seebug_Agent功能的API接口，包括：
- Seebug漏洞搜索
- 漏洞详情获取
- API状态检查
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
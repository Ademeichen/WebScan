"""
API 装饰器模块

提供公共的装饰器函数，包括错误处理、日志记录等
"""
from functools import wraps
import logging
from fastapi import HTTPException

from backend.api.common import APIResponse

logger = logging.getLogger(__name__)


def error_handler(func):
    """
    错误处理装饰器
    
    统一处理API函数中的异常，返回标准化的错误响应
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")
    return wrapper


def log_request(func):
    """
    请求日志装饰器
    
    记录API请求的开始和结束
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info(f"Starting {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            logger.info(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Failed {func.__name__}: {str(e)}")
            raise
    return wrapper


def validate_request(*required_fields):
    """
    请求验证装饰器
    
    验证请求中是否包含必需的字段
    
    Args:
        *required_fields: 必需的字段名
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = args[0] if args else None
            if request and hasattr(request, 'body'):
                body = await request.json()
                for field in required_fields:
                    if field not in body or not body[field]:
                        raise HTTPException(
                            status_code=400,
                            detail=f"缺少必需字段: {field}"
                        )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

"""
API 公共模块

提供统一的API响应模型和公共工具函数
"""
from pydantic import BaseModel
from typing import Optional, Any


class APIResponse(BaseModel):
    """
    统一 API 响应模型
    
    Attributes:
        code: 响应状态码,200 表示成功
        message: 响应消息
        data: 响应数据,可选
    """
    code: int
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    """
    分页响应模型
    
    Attributes:
        items: 数据项列表
        total: 总数量
        page: 当前页码
        page_size: 每页数量
        total_pages: 总页数
    """
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int

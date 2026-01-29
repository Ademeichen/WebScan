"""
通知 API

提供通知管理功能，包括：
- 获取通知列表
- 创建通知
- 标记通知为已读
- 删除通知
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["通知管理"])


class Notification(BaseModel):
    """通知模型"""
    id: int = Field(..., description="通知ID")
    title: str = Field(..., description="通知标题")
    message: str = Field(..., description="通知内容")
    type: str = Field(..., description="通知类型")
    time: str = Field(..., description="通知时间")
    read: bool = Field(default=False, description="是否已读")


class CreateNotification(BaseModel):
    """创建通知模型"""
    title: str = Field(..., description="通知标题")
    message: str = Field(..., description="通知内容")
    type: str = Field(..., description="通知类型")


class APIResponse(BaseModel):
    """统一API响应模型"""
    code: int = Field(..., description="状态码")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


# 模拟通知数据库
MOCK_NOTIFICATIONS = [
    {
        "id": 1,
        "title": "高危漏洞发现",
        "message": "在 shop.www.baidu.com 发现 SQL 注入漏洞",
        "type": "high-vulnerability",
        "time": "5分钟前",
        "read": False
    },
    {
        "id": 2,
        "title": "扫描任务完成",
        "message": "企业官网安全扫描已完成",
        "type": "scan-complete",
        "time": "1小时前",
        "read": False
    },
    {
        "id": 3,
        "title": "系统更新",
        "message": "漏洞库已更新到最新版本",
        "type": "system-update",
        "time": "2小时前",
        "read": True
    }
]

NOTIFICATION_ID_COUNTER = 4


@router.get("/", response_model=APIResponse, summary="获取通知列表")
async def get_notifications(skip: int = 0, limit: int = 50, unread_only: bool = False):
    """
    获取通知列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        unread_only: 是否只返回未读通知
        
    Returns:
        APIResponse: 包含通知列表的响应
        
    Examples:
        >>> GET /api/notifications/
        >>> {
        ...     "code": 200,
        ...     "message": "获取通知列表成功",
        ...     "data": {
        ...         "notifications": [...],
        ...         "total": 3,
        ...         "unread_count": 2
        ...     }
        ... }
    """
    try:
        notifications = MOCK_NOTIFICATIONS.copy()
        
        # 过滤未读通知
        if unread_only:
            notifications = [n for n in notifications if not n["read"]]
        
        # 排序（最新的在前）
        notifications.reverse()
        
        # 分页
        total = len(notifications)
        paginated_notifications = notifications[skip:skip + limit]
        
        # 统计未读数量
        unread_count = sum(1 for n in MOCK_NOTIFICATIONS if not n["read"])
        
        logger.info(f"获取通知列表成功: 共 {total} 条通知，{unread_count} 条未读")
        
        return APIResponse(
            code=200,
            message="获取通知列表成功",
            data={
                "notifications": paginated_notifications,
                "total": total,
                "unread_count": unread_count
            }
        )
    except Exception as e:
        logger.error(f"获取通知列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取通知列表失败: {str(e)}")


@router.get("/{notification_id}", response_model=APIResponse, summary="获取通知详情")
async def get_notification(notification_id: int):
    """
    获取单个通知的详细信息
    
    Args:
        notification_id: 通知ID
        
    Returns:
        APIResponse: 包含通知详情的响应
        
    Raises:
        HTTPException: 当通知不存在时抛出404错误
        
    Examples:
        >>> GET /api/notifications/1
        >>> {
        ...     "code": 200,
        ...     "message": "获取通知详情成功",
        ...     "data": {...}
        ... }
    """
    try:
        notification = next((n for n in MOCK_NOTIFICATIONS if n["id"] == notification_id), None)
        if not notification:
            raise HTTPException(status_code=404, detail="通知不存在")
        
        logger.info(f"获取通知详情成功: {notification_id}")
        
        return APIResponse(
            code=200,
            message="获取通知详情成功",
            data=notification
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取通知详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取通知详情失败: {str(e)}")


@router.post("/", response_model=APIResponse, summary="创建通知")
async def create_notification(notification_data: CreateNotification):
    """
    创建新通知
    
    Args:
        notification_data: 通知数据
        
    Returns:
        APIResponse: 包含创建的通知的响应
        
    Examples:
        >>> POST /api/notifications/
        >>> {
        ...     "title": "新通知",
        ...     "message": "通知内容",
        ...     "type": "info"
        ... }
        >>> {
        ...     "code": 200,
        ...     "message": "创建通知成功",
        ...     "data": {...}
        ... }
    """
    try:
        global NOTIFICATION_ID_COUNTER
        
        new_notification = {
            "id": NOTIFICATION_ID_COUNTER,
            "title": notification_data.title,
            "message": notification_data.message,
            "type": notification_data.type,
            "time": "刚刚",
            "read": False
        }
        
        MOCK_NOTIFICATIONS.append(new_notification)
        NOTIFICATION_ID_COUNTER += 1
        
        logger.info(f"创建通知成功: {notification_data.title}")
        
        return APIResponse(
            code=200,
            message="创建通知成功",
            data=new_notification
        )
    except Exception as e:
        logger.error(f"创建通知失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建通知失败: {str(e)}")


@router.put("/{notification_id}/read", response_model=APIResponse, summary="标记通知为已读")
async def mark_as_read(notification_id: int):
    """
    标记通知为已读
    
    Args:
        notification_id: 通知ID
        
    Returns:
        APIResponse: 包含更新后通知的响应
        
    Raises:
        HTTPException: 当通知不存在时抛出404错误
        
    Examples:
        >>> PUT /api/notifications/1/read
        >>> {
        ...     "code": 200,
        ...     "message": "标记为已读成功",
        ...     "data": {...}
        ... }
    """
    try:
        notification = next((n for n in MOCK_NOTIFICATIONS if n["id"] == notification_id), None)
        if not notification:
            raise HTTPException(status_code=404, detail="通知不存在")
        
        notification["read"] = True
        
        logger.info(f"标记通知为已读成功: {notification_id}")
        
        return APIResponse(
            code=200,
            message="标记为已读成功",
            data=notification
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记通知为已读失败: {e}")
        raise HTTPException(status_code=500, detail=f"标记通知为已读失败: {str(e)}")


@router.put("/read-all", response_model=APIResponse, summary="标记所有通知为已读")
async def mark_all_as_read():
    """
    标记所有通知为已读
    
    Returns:
        APIResponse: 包含更新后通知列表的响应
        
    Examples:
        >>> PUT /api/notifications/read-all
        >>> {
        ...     "code": 200,
        ...     "message": "标记所有通知为已读成功",
        ...     "data": {...}
        ... }
    """
    try:
        for notification in MOCK_NOTIFICATIONS:
            notification["read"] = True
        
        logger.info("标记所有通知为已读成功")
        
        return APIResponse(
            code=200,
            message="标记所有通知为已读成功",
            data={"updated_count": len(MOCK_NOTIFICATIONS)}
        )
    except Exception as e:
        logger.error(f"标记所有通知为已读失败: {e}")
        raise HTTPException(status_code=500, detail=f"标记所有通知为已读失败: {str(e)}")


@router.delete("/{notification_id}", response_model=APIResponse, summary="删除通知")
async def delete_notification(notification_id: int):
    """
    删除通知
    
    Args:
        notification_id: 通知ID
        
    Returns:
        APIResponse: 删除成功的响应
        
    Raises:
        HTTPException: 当通知不存在时抛出404错误
        
    Examples:
        >>> DELETE /api/notifications/1
        >>> {
        ...     "code": 200,
        ...     "message": "删除通知成功",
        ...     "data": null
        ... }
    """
    try:
        notification_index = next((i for i, n in enumerate(MOCK_NOTIFICATIONS) if n["id"] == notification_id), None)
        if notification_index is None:
            raise HTTPException(status_code=404, detail="通知不存在")
        
        MOCK_NOTIFICATIONS.pop(notification_index)
        
        logger.info(f"删除通知成功: {notification_id}")
        
        return APIResponse(
            code=200,
            message="删除通知成功",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除通知失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除通知失败: {str(e)}")


@router.delete("/", response_model=APIResponse, summary="删除所有已读通知")
async def delete_read_notifications():
    """
    删除所有已读通知
    
    Returns:
        APIResponse: 删除成功的响应
        
    Examples:
        >>> DELETE /api/notifications/
        >>> {
        ...     "code": 200,
        ...     "message": "删除已读通知成功",
        ...     "data": {"deleted_count": 2}
        ... }
    """
    try:
        initial_count = len(MOCK_NOTIFICATIONS)
        MOCK_NOTIFICATIONS[:] = [n for n in MOCK_NOTIFICATIONS if not n["read"]]
        deleted_count = initial_count - len(MOCK_NOTIFICATIONS)
        
        logger.info(f"删除已读通知成功: 共删除 {deleted_count} 条通知")
        
        return APIResponse(
            code=200,
            message="删除已读通知成功",
            data={"deleted_count": deleted_count}
        )
    except Exception as e:
        logger.error(f"删除已读通知失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除已读通知失败: {str(e)}")


@router.get("/count/unread", response_model=APIResponse, summary="获取未读通知数量")
async def get_unread_count():
    """
    获取未读通知数量
    
    Returns:
        APIResponse: 包含未读通知数量的响应
        
    Examples:
        >>> GET /api/notifications/count/unread
        >>> {
        ...     "code": 200,
        ...     "message": "获取未读通知数量成功",
        ...     "data": {"unread_count": 2}
        ... }
    """
    try:
        unread_count = sum(1 for n in MOCK_NOTIFICATIONS if not n["read"])
        
        logger.info(f"获取未读通知数量成功: {unread_count}")
        
        return APIResponse(
            code=200,
            message="获取未读通知数量成功",
            data={"unread_count": unread_count}
        )
    except Exception as e:
        logger.error(f"获取未读通知数量失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取未读通知数量失败: {str(e)}")

"""
用户信息 API

提供用户信息管理功能,包括:
- 获取用户信息
- 更新用户信息
- 用户权限管理
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Any
from datetime import datetime
import logging
from tortoise import Tortoise
from backend.api.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["用户管理"])


class UserInfo(BaseModel):
    """用户信息模型"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    role: str = Field(default="user", description="用户角色")
    avatar: Optional[str] = Field(None, description="头像URL")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    permissions: List[str] = Field(default_factory=list, description="用户权限列表")


class UpdateUserInfo(BaseModel):
    """更新用户信息模型"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    avatar: Optional[str] = Field(None, description="头像URL")


async def get_user_or_404(user_id: int):
    """获取用户或返回404错误"""
    from backend.models import User
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.get("/profile", response_model=APIResponse, summary="获取用户信息")
async def get_user_profile(user_id: int = 1):
    """
    获取当前登录用户的详细信息
    
    Args:
        user_id: 用户ID,默认为1(管理员)
        
    Returns:
        APIResponse: 包含用户信息的响应
        
    Raises:
        HTTPException: 当用户不存在时抛出404错误
        
    Examples:
        >>> GET /api/user/profile
        >>> {
        ...     "code": 200,
        ...     "message": "获取用户信息成功",
        ...     "data": {
        ...         "id": 1,
        ...         "username": "admin",
        ...         "email": "admin@webscan.ai",
        ...         "role": "administrator",
        ...         "avatar": null,
        ...         "last_login": "2024-11-17T20:00:00",
        ...         "permissions": ["scan:create", "scan:read", ...]
        ...     }
        ... }
    """
    try:
        user = await get_user_or_404(user_id)
        
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "avatar": user.avatar,
            "last_login": user.last_login,
            "permissions": user.get_permissions()
        }
        
        logger.info(f"获取用户信息成功: {user.username}")
        
        return APIResponse(
            code=200,
            message="获取用户信息成功",
            data=user_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")


@router.put("/profile", response_model=APIResponse, summary="更新用户信息")
async def update_user_profile(user_id: int = 1, update_data: UpdateUserInfo = None):
    """
    更新当前登录用户的信息
    
    Args:
        user_id: 用户ID,默认为1(管理员)
        update_data: 要更新的用户信息
        
    Returns:
        APIResponse: 包含更新后用户信息的响应
        
    Raises:
        HTTPException: 当用户不存在或更新失败时抛出错误
        
    Examples:
        >>> PUT /api/user/profile
        >>> {
        ...     "email": "newemail@example.com",
        ...     "avatar": "https://example.com/avatar.jpg"
        ... }
        >>> {
        ...     "code": 200,
        ...     "message": "更新用户信息成功",
        ...     "data": {...}
        ... }
    """
    try:
        if not update_data:
            raise HTTPException(status_code=400, detail="请提供要更新的数据")
        
        user = await get_user_or_404(user_id)
        
        if update_data.email:
            user.email = update_data.email
        if update_data.avatar:
            user.avatar = update_data.avatar
        
        await user.save()
        
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "avatar": user.avatar,
            "last_login": user.last_login,
            "permissions": user.get_permissions()
        }
        
        logger.info(f"更新用户信息成功: {user.username}")
        
        return APIResponse(
            code=200,
            message="更新用户信息成功",
            data=user_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新用户信息失败: {str(e)}")


@router.get("/permissions", response_model=APIResponse, summary="获取用户权限")
async def get_user_permissions(user_id: int = 1):
    """
    获取当前用户的权限列表
    
    Args:
        user_id: 用户ID,默认为1(管理员)
        
    Returns:
        APIResponse: 包含用户权限列表的响应
        
    Examples:
        >>> GET /api/user/permissions
        >>> {
        ...     "code": 200,
        ...     "message": "获取用户权限成功",
        ...     "data": {
        ...         "permissions": ["scan:create", "scan:read", ...]
        ...     }
        ... }
    """
    try:
        user = await get_user_or_404(user_id)
        
        logger.info(f"获取用户权限成功: {user.username}")
        
        return APIResponse(
            code=200,
            message="获取用户权限成功",
            data={"permissions": user.get_permissions()}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户权限失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户权限失败: {str(e)}")


@router.get("/list", response_model=APIResponse, summary="获取用户列表")
async def get_user_list(skip: int = 0, limit: int = 20):
    """
    获取用户列表(仅管理员可用)
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        
    Returns:
        APIResponse: 包含用户列表的响应
        
    Examples:
        >>> GET /api/user/list?skip=0&limit=20
        >>> {
        ...     "code": 200,
        ...     "message": "获取用户列表成功",
        ...     "data": {
        ...         "users": [...],
        ...         "total": 2
        ...     }
        ... }
    """
    try:
        from backend.models import User
        
        total = await User.all().count()
        users = await User.all().order_by("-created_at").offset(skip).limit(limit)
        
        safe_users = []
        for user in users:
            safe_user = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "avatar": user.avatar,
                "last_login": user.last_login
            }
            safe_users.append(safe_user)
        
        logger.info(f"获取用户列表成功: 共 {total} 个用户")
        
        return APIResponse(
            code=200,
            message="获取用户列表成功",
            data={
                "users": safe_users,
                "total": total
            }
        )
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")

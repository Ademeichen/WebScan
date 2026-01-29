"""
用户信息 API

提供用户信息管理功能，包括：
- 获取用户信息
- 更新用户信息
- 用户权限管理
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

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


class APIResponse(BaseModel):
    """统一API响应模型"""
    code: int = Field(..., description="状态码")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")

# TODO
# 模拟用户数据库
MOCK_USERS = {
    1: {
        "id": 1,
        "username": "admin",
        "email": "admin@webscan.ai",
        "role": "administrator",
        "avatar": None,
        "last_login": datetime.now(),
        "permissions": [
            "scan:create",
            "scan:read",
            "scan:update",
            "scan:delete",
            "report:generate",
            "report:read",
            "report:delete",
            "settings:manage",
            "user:manage"
        ]
    },
    2: {
        "id": 2,
        "username": "user",
        "email": "user@webscan.ai",
        "role": "user",
        "avatar": None,
        "last_login": datetime.now(),
        "permissions": [
            "scan:create",
            "scan:read",
            "report:generate",
            "report:read"
        ]
    }
}


@router.get("/profile", response_model=APIResponse, summary="获取用户信息")
async def get_user_profile(user_id: int = 1):
    """
    获取当前登录用户的详细信息
    
    Args:
        user_id: 用户ID，默认为1（管理员）
        
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
        user_data = MOCK_USERS.get(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        logger.info(f"获取用户信息成功: {user_data['username']}")
        
        return APIResponse(
            code=200,
            message="获取用户信息成功",
            data=UserInfo(**user_data).dict()
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
        user_id: 用户ID，默认为1（管理员）
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
        
        user_data = MOCK_USERS.get(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 更新用户信息
        if update_data.email:
            user_data["email"] = update_data.email
        if update_data.avatar:
            user_data["avatar"] = update_data.avatar
        
        logger.info(f"更新用户信息成功: {user_data['username']}")
        
        return APIResponse(
            code=200,
            message="更新用户信息成功",
            data=UserInfo(**user_data).dict()
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
        user_id: 用户ID，默认为1（管理员）
        
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
        user_data = MOCK_USERS.get(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        logger.info(f"获取用户权限成功: {user_data['username']}")
        
        return APIResponse(
            code=200,
            message="获取用户权限成功",
            data={"permissions": user_data["permissions"]}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户权限失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户权限失败: {str(e)}")


@router.get("/list", response_model=APIResponse, summary="获取用户列表")
async def get_user_list(skip: int = 0, limit: int = 20):
    """
    获取用户列表（仅管理员可用）
    
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
        users = list(MOCK_USERS.values())
        total = len(users)
        
        # 分页
        paginated_users = users[skip:skip + limit]
        
        # 移除敏感信息
        safe_users = []
        for user in paginated_users:
            safe_user = {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "avatar": user["avatar"],
                "last_login": user["last_login"]
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

"""
POC 脚本文件管理 API

提供 POC 脚本文件的管理接口，支持查询、获取功能
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import glob
import stat
import logging
from datetime import datetime
from pathlib import Path

from backend.ai_agents.utils.file_sync import file_sync_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/poc/files", tags=["POC文件管理"])


# 响应模型
class POCFileInfo(BaseModel):
    """
    POC 文件信息模型
    """
    file_path: str
    file_name: str
    directory: str
    size: int
    created_at: str
    modified_at: str
    content: Optional[str] = None


class POCFileList(BaseModel):
    """
    POC 文件列表模型
    """
    total: int
    files: List[POCFileInfo]


class APIResponse(BaseModel):
    """
    统一 API 响应模型
    """
    code: int
    message: str
    data: Optional[Any] = None


class FileAccessLayer:
    """
    文件访问抽象层
    
    统一管理两个目录中的POC脚本文件
    """
    
    def __init__(self):
        """
        初始化文件访问抽象层
        """
        self.base_poc_dir = file_sync_manager.base_poc_dir
        self.seebug_generated_dir = file_sync_manager.seebug_generated_dir
    
    def get_all_files(self) -> List[Dict[str, Any]]:
        """
        获取所有POC脚本文件
        
        Returns:
            List[Dict[str, Any]]: 文件信息列表
        """
        files = []
        
        # 从base_poc目录获取文件
        files.extend(self._get_files_from_directory(self.base_poc_dir))
        
        # 从seebug_generated目录获取文件
        # 注意：这里只添加不在base_poc目录中的文件
        seebug_files = self._get_files_from_directory(self.seebug_generated_dir)
        base_file_paths = {f['file_path'] for f in files}
        for file_info in seebug_files:
            if file_info['file_path'] not in base_file_paths:
                files.append(file_info)
        
        return files
    
    def _get_files_from_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """
        从指定目录获取POC脚本文件
        
        Args:
            directory: 目录路径
            
        Returns:
            List[Dict[str, Any]]: 文件信息列表
        """
        files = []
        
        for file_path in directory.rglob("*.py"):
            if file_path.name == "__init__.py":
                continue
            
            try:
                # 获取文件信息
                stat_info = file_path.stat()
                file_info = {
                    "file_path": str(file_path.relative_to(self.base_poc_dir)) if directory == self.base_poc_dir else str(file_path.relative_to(self.seebug_generated_dir)),
                    "file_name": file_path.name,
                    "directory": str(file_path.parent.relative_to(directory)),
                    "size": stat_info.st_size,
                    "created_at": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "full_path": str(file_path)
                }
                files.append(file_info)
            except Exception as e:
                logger.error(f"获取文件信息失败: {file_path}, 错误: {str(e)}")
        
        return files
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        获取单个POC脚本文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 文件内容，如果文件不存在返回None
        """
        # 先尝试从base_poc目录读取
        base_file_path = self.base_poc_dir / file_path
        if base_file_path.exists():
            try:
                with open(base_file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"读取文件失败: {base_file_path}, 错误: {str(e)}")
                return None
        
        # 再尝试从seebug_generated目录读取
        seebug_file_path = self.seebug_generated_dir / file_path
        if seebug_file_path.exists():
            try:
                with open(seebug_file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"读取文件失败: {seebug_file_path}, 错误: {str(e)}")
                return None
        
        return None
    
    def search_files(self, **kwargs) -> List[Dict[str, Any]]:
        """
        按条件搜索POC脚本文件
        
        Args:
            kwargs: 搜索条件，包括name、directory、created_after、modified_after等
            
        Returns:
            List[Dict[str, Any]]: 符合条件的文件信息列表
        """
        all_files = self.get_all_files()
        filtered_files = []
        
        for file_info in all_files:
            # 按文件名搜索
            if 'name' in kwargs and kwargs['name']:
                if kwargs['name'] not in file_info['file_name']:
                    continue
            
            # 按目录搜索
            if 'directory' in kwargs and kwargs['directory']:
                if kwargs['directory'] not in file_info['directory']:
                    continue
            
            # 按创建时间搜索
            if 'created_after' in kwargs and kwargs['created_after']:
                try:
                    created_time = datetime.fromisoformat(file_info['created_at'])
                    if created_time < datetime.fromisoformat(kwargs['created_after']):
                        continue
                except:
                    pass
            
            # 按修改时间搜索
            if 'modified_after' in kwargs and kwargs['modified_after']:
                try:
                    modified_time = datetime.fromisoformat(file_info['modified_at'])
                    if modified_time < datetime.fromisoformat(kwargs['modified_after']):
                        continue
                except:
                    pass
            
            filtered_files.append(file_info)
        
        return filtered_files


# 创建文件访问抽象层实例
file_access_layer = FileAccessLayer()


@router.get("/list", response_model=POCFileList)
async def get_poc_files(
    name: Optional[str] = Query(None, description="按文件名搜索"),
    directory: Optional[str] = Query(None, description="按目录搜索"),
    created_after: Optional[str] = Query(None, description="按创建时间搜索，格式：2026-01-30T18:00:00"),
    modified_after: Optional[str] = Query(None, description="按修改时间搜索，格式：2026-01-30T18:00:00"),
    limit: int = Query(100, description="返回结果数量限制"),
    offset: int = Query(0, description="返回结果偏移量")
):
    """
    获取POC脚本文件列表
    
    支持按文件名、目录、创建时间、修改时间等条件进行搜索。
    
    Args:
        name: 文件名搜索关键词
        directory: 目录搜索关键词
        created_after: 创建时间下限
        modified_after: 修改时间下限
        limit: 返回结果数量限制
        offset: 返回结果偏移量
        
    Returns:
        POCFileList: 文件列表，包含总数和文件信息
    """
    try:
        # 构建搜索条件
        search_kwargs = {}
        if name:
            search_kwargs['name'] = name
        if directory:
            search_kwargs['directory'] = directory
        if created_after:
            search_kwargs['created_after'] = created_after
        if modified_after:
            search_kwargs['modified_after'] = modified_after
        
        # 搜索文件
        files = file_access_layer.search_files(**search_kwargs)
        
        # 应用分页
        total = len(files)
        paginated_files = files[offset:offset+limit]
        
        # 转换为响应模型
        file_infos = []
        for file_info in paginated_files:
            file_info_model = POCFileInfo(
                file_path=file_info['file_path'],
                file_name=file_info['file_name'],
                directory=file_info['directory'],
                size=file_info['size'],
                created_at=file_info['created_at'],
                modified_at=file_info['modified_at']
            )
            file_infos.append(file_info_model)
        
        return POCFileList(total=total, files=file_infos)
        
    except Exception as e:
        logger.error(f"获取POC文件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@router.get("/content/{file_path:path}", response_model=APIResponse)
async def get_poc_file_content(file_path: str):
    """
    获取单个POC脚本文件内容
    
    Args:
        file_path: 文件路径，相对于backend/poc目录
        
    Returns:
        APIResponse: 包含文件内容的响应
    """
    try:
        # 获取文件内容
        content = file_access_layer.get_file_content(file_path)
        
        if content is None:
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        return APIResponse(
            code=200,
            message="获取文件内容成功",
            data={
                "file_path": file_path,
                "content": content
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件内容失败: {file_path}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件内容失败: {str(e)}")


@router.get("/info/{file_path:path}", response_model=POCFileInfo)
async def get_poc_file_info(file_path: str):
    """
    获取单个POC脚本文件信息
    
    Args:
        file_path: 文件路径，相对于backend/poc目录
        
    Returns:
        POCFileInfo: 文件信息
    """
    try:
        # 获取所有文件
        all_files = file_access_layer.get_all_files()
        
        # 查找指定文件
        for file_info in all_files:
            if file_info['file_path'] == file_path:
                return POCFileInfo(
                    file_path=file_info['file_path'],
                    file_name=file_info['file_name'],
                    directory=file_info['directory'],
                    size=file_info['size'],
                    created_at=file_info['created_at'],
                    modified_at=file_info['modified_at']
                )
        
        raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件信息失败: {file_path}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")


@router.get("/directories", response_model=List[str])
async def get_poc_directories():
    """
    获取所有POC脚本目录
    
    Returns:
        List[str]: 目录列表
    """
    try:
        directories = set()
        
        # 从base_poc目录获取目录
        for directory in file_access_layer.base_poc_dir.iterdir():
            if directory.is_dir() and not directory.name.startswith('.') and directory.name != "__pycache__":
                directories.add(str(directory.relative_to(file_access_layer.base_poc_dir)))
        
        # 从seebug_generated目录获取目录
        for directory in file_access_layer.seebug_generated_dir.iterdir():
            if directory.is_dir() and not directory.name.startswith('.') and directory.name != "__pycache__":
                directories.add(str(directory.relative_to(file_access_layer.seebug_generated_dir)))
        
        return list(directories)
        
    except Exception as e:
        logger.error(f"获取目录列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取目录列表失败: {str(e)}")


@router.post("/sync", response_model=APIResponse)
async def sync_poc_files():
    """
    手动触发POC脚本文件同步
    
    同步backend/poc和Seebug_Agent/generated_pocs目录中的文件。
    
    Returns:
        APIResponse: 同步结果
    """
    try:
        # 执行文件同步
        sync_result = file_sync_manager.sync_files()
        
        return APIResponse(
            code=200,
            message="文件同步成功",
            data={
                "added": len(sync_result['added']),
                "updated": len(sync_result['updated']),
                "deleted": len(sync_result['deleted'])
            }
        )
        
    except Exception as e:
        logger.error(f"文件同步失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件同步失败: {str(e)}")


@router.get("/sync/status", response_model=APIResponse)
async def get_sync_status():
    """
    获取文件同步状态
    
    Returns:
        APIResponse: 同步状态
    """
    try:
        # 获取同步状态
        status = file_sync_manager.get_sync_status()
        
        return APIResponse(
            code=200,
            message="获取同步状态成功",
            data=status
        )
        
    except Exception as e:
        logger.error(f"获取同步状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取同步状态失败: {str(e)}")

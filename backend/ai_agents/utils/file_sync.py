"""
文件同步模块

负责确保backend/poc和Seebug_Agent/generated_pocs目录文件一致
支持定时同步与事件触发同步相结合的方式
"""
import os
import logging
import hashlib
import shutil
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class FileSyncManager:
    """
    文件同步管理器
    
    负责管理两个目录之间的文件同步
    """
    
    def __init__(self):
        """
        初始化文件同步管理器
        """
        # 计算基础POC目录路径
        current_file = os.path.abspath(__file__)
        utils_dir = os.path.dirname(current_file)
        ai_agents_dir = os.path.dirname(utils_dir)
        backend_dir = os.path.dirname(ai_agents_dir)
        self.base_poc_dir = Path(backend_dir) / "poc"
        
        # 计算Seebug生成目录路径
        project_root = os.path.dirname(backend_dir)
        self.seebug_generated_dir = Path(project_root) / "Seebug_Agent" / "generated_pocs"
        
        # 确保目录存在
        self.seebug_generated_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"✅ 文件同步管理器初始化完成")
        logger.info(f"  基础POC目录: {self.base_poc_dir}")
        logger.info(f"  Seebug生成目录: {self.seebug_generated_dir}")
    
    def get_file_hash(self, file_path: Path) -> str:
        """
        获取文件的MD5哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件的MD5哈希值
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"❌ 计算文件哈希失败: {file_path}, 错误: {str(e)}")
            return ""
    
    def sync_files(self) -> Dict[str, List[str]]:
        """
        执行文件同步
        
        Returns:
            Dict[str, List[str]]: 同步结果，包含新增、更新、删除的文件列表
        """
        logger.info("🔄 开始执行文件同步")
        
        result = {
            "added": [],
            "updated": [],
            "deleted": []
        }
        
        try:
            # 1. 同步从base_poc到seebug_generated
            result.update(self._sync_directories(self.base_poc_dir, self.seebug_generated_dir))
            
            # 2. 同步从seebug_generated到base_poc
            # 注意：这里只同步新增文件，不覆盖已存在的文件
            reverse_result = self._sync_directories(self.seebug_generated_dir, self.base_poc_dir, only_add=True)
            result["added"].extend(reverse_result["added"])
            
            logger.info(f"✅ 文件同步完成")
            logger.info(f"  新增文件: {len(result['added'])}")
            logger.info(f"  更新文件: {len(result['updated'])}")
            logger.info(f"  删除文件: {len(result['deleted'])}")
            
        except Exception as e:
            logger.error(f"❌ 文件同步失败: {str(e)}")
        
        return result
    
    def _sync_directories(self, source_dir: Path, target_dir: Path, only_add: bool = False) -> Dict[str, List[str]]:
        """
        同步两个目录
        
        Args:
            source_dir: 源目录
            target_dir: 目标目录
            only_add: 是否只添加新文件，不更新或删除
            
        Returns:
            Dict[str, List[str]]: 同步结果
        """
        result = {
            "added": [],
            "updated": [],
            "deleted": []
        }
        
        # 遍历源目录
        for source_path in source_dir.rglob("*.py"):
            if source_path.name == "__init__.py":
                continue
            
            # 计算相对路径
            relative_path = source_path.relative_to(source_dir)
            target_path = target_dir / relative_path
            
            # 确保目标目录存在
            target_path.parent.mkdir(exist_ok=True, parents=True)
            
            # 检查文件是否需要同步
            if not target_path.exists():
                # 文件不存在，需要新增
                shutil.copy2(source_path, target_path)
                result["added"].append(str(relative_path))
                logger.info(f"➕ 新增文件: {relative_path}")
            elif not only_add:
                # 文件存在，检查是否需要更新
                source_hash = self.get_file_hash(source_path)
                target_hash = self.get_file_hash(target_path)
                
                if source_hash != target_hash:
                    # 文件内容不同，需要更新
                    # 使用临时文件替换方式确保原子性
                    temp_path = target_path.with_suffix(f".{int(time.time())}.tmp")
                    shutil.copy2(source_path, temp_path)
                    os.replace(temp_path, target_path)
                    result["updated"].append(str(relative_path))
                    logger.info(f"🔄 更新文件: {relative_path}")
        
        if not only_add:
            # 检查目标目录中是否有源目录中不存在的文件
            for target_path in target_dir.rglob("*.py"):
                if target_path.name == "__init__.py":
                    continue
                
                relative_path = target_path.relative_to(target_dir)
                source_path = source_dir / relative_path
                
                if not source_path.exists():
                    # 文件不存在于源目录，需要删除
                    target_path.unlink()
                    result["deleted"].append(str(relative_path))
                    logger.info(f"➖ 删除文件: {relative_path}")
        
        return result
    
    async def start_periodic_sync(self, interval: int = 300):
        """
        开始定时同步
        
        Args:
            interval: 同步间隔（秒），默认300秒（5分钟）
        """
        logger.info(f"⏰ 开始定时同步，间隔: {interval}秒")
        
        while True:
            try:
                self.sync_files()
            except Exception as e:
                logger.error(f"❌ 定时同步失败: {str(e)}")
            
            await asyncio.sleep(interval)
    
    def trigger_sync(self, file_path: Optional[str] = None):
        """
        触发事件同步
        
        Args:
            file_path: 触发同步的文件路径，如果为None则执行全量同步
        """
        logger.info(f"⚡ 触发事件同步: {file_path}")
        
        if file_path:
            # 执行单个文件同步
            try:
                file_path = Path(file_path)
                if file_path.exists() and file_path.suffix == ".py" and file_path.name != "__init__.py":
                    # 确定源目录和目标目录
                    if str(self.base_poc_dir) in str(file_path):
                        source_dir = self.base_poc_dir
                        target_dir = self.seebug_generated_dir
                    elif str(self.seebug_generated_dir) in str(file_path):
                        source_dir = self.seebug_generated_dir
                        target_dir = self.base_poc_dir
                    else:
                        logger.warning(f"⚠️ 文件不在同步目录中: {file_path}")
                        return
                    
                    # 同步单个文件
                    relative_path = file_path.relative_to(source_dir)
                    target_path = target_dir / relative_path
                    
                    target_path.parent.mkdir(exist_ok=True, parents=True)
                    
                    # 使用临时文件替换方式确保原子性
                    temp_path = target_path.with_suffix(f".{int(time.time())}.tmp")
                    shutil.copy2(file_path, temp_path)
                    os.replace(temp_path, target_path)
                    
                    logger.info(f"✅ 单个文件同步完成: {relative_path}")
            except Exception as e:
                logger.error(f"❌ 单个文件同步失败: {file_path}, 错误: {str(e)}")
        else:
            # 执行全量同步
            self.sync_files()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        获取同步状态
        
        Returns:
            Dict[str, Any]: 同步状态信息
        """
        status = {
            "base_poc_dir": str(self.base_poc_dir),
            "seebug_generated_dir": str(self.seebug_generated_dir),
            "base_poc_files": [],
            "seebug_generated_files": [],
            "sync_time": datetime.now().isoformat()
        }
        
        # 获取base_poc目录中的文件
        for file_path in self.base_poc_dir.rglob("*.py"):
            if file_path.name != "__init__.py":
                relative_path = file_path.relative_to(self.base_poc_dir)
                status["base_poc_files"].append({
                    "path": str(relative_path),
                    "size": file_path.stat().st_size,
                    "mtime": file_path.stat().st_mtime,
                    "hash": self.get_file_hash(file_path)
                })
        
        # 获取seebug_generated目录中的文件
        for file_path in self.seebug_generated_dir.rglob("*.py"):
            if file_path.name != "__init__.py":
                relative_path = file_path.relative_to(self.seebug_generated_dir)
                status["seebug_generated_files"].append({
                    "path": str(relative_path),
                    "size": file_path.stat().st_size,
                    "mtime": file_path.stat().st_mtime,
                    "hash": self.get_file_hash(file_path)
                })
        
        return status

# 全局文件同步管理器实例
file_sync_manager = FileSyncManager()

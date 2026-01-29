"""
POC 脚本管理器

负责 POC 脚本的管理，包括从 Seebug 同步、本地加载、版本控制等。
"""
import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from backend.config import settings
from backend.models import POCVerificationTask, POCVerificationResult
from backend.api.kb import search_seebug_poc, download_seebug_poc

logger = logging.getLogger(__name__)


class POCMetadata:
    """
    POC 元数据类
    
    用于存储 POC 的元信息，包括名称、类型、严重度等。
    """
    
    def __init__(
        self,
        poc_name: str,
        poc_id: str,
        poc_type: str = "web",
        severity: str = "medium",
        cvss_score: Optional[float] = None,
        description: Optional[str] = None,
        author: Optional[str] = None,
        source: str = "seebug",
        version: str = "1.0",
        tags: List[str] = None
    ):
        self.poc_name = poc_name
        self.poc_id = poc_id
        self.poc_type = poc_type
        self.severity = severity
        self.cvss_score = cvss_score
        self.description = description
        self.author = author
        self.source = source
        self.version = version
        self.tags = tags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict: 包含所有元信息的字典
        """
        return {
            "poc_name": self.poc_name,
            "poc_id": self.poc_id,
            "poc_type": self.poc_type,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "description": self.description,
            "author": self.author,
            "source": self.source,
            "version": self.version,
            "tags": self.tags
        }


class POCManager:
    """
    POC 管理器类
    
    负责管理 POC 脚本的生命周期，包括：
    - 从 Seebug 同步 POC
    - 本地自定义 POC 脚本加载
    - POC 版本控制
    - POC 缓存管理
    - POC 元数据管理
    """
    
    def __init__(self):
        """
        初始化 POC 管理器
        """
        self.poc_registry: Dict[str, POCMetadata] = {}
        self.poc_cache: Dict[str, Dict[str, Any]] = {}
        self.poc_versions: Dict[str, List[str]] = {}
        
        logger.info("✅ POC 管理器初始化完成")
    
    async def sync_from_seebug(
        self,
        keyword: str = "",
        limit: int = 100,
        force_refresh: bool = False
    ) -> List[POCMetadata]:
        """
        从 Seebug 同步 POC
        
        Args:
            keyword: 搜索关键词，为空时同步所有 POC
            limit: 同步数量限制
            force_refresh: 是否强制刷新缓存
            
        Returns:
            List[POCMetadata]: POC 元数据列表
        """
        try:
            logger.info(f"🔍 开始从 Seebug 同步 POC，关键词: {keyword}, 限制: {limit}")
            
            # 检查缓存
            cache_key = f"seebug_{keyword}_{limit}"
            if not force_refresh and cache_key in self.poc_cache:
                cache_time = self.poc_cache[cache_key]["timestamp"]
                cache_age = (datetime.now() - cache_time).total_seconds()
                
                if cache_age < settings.POC_CACHE_TTL:
                    logger.info(f"✅ 使用缓存数据，缓存年龄: {cache_age}秒")
                    return self.poc_cache[cache_key]["pocs"]
            
            # 从 Seebug 搜索 POC
            poc_list = await search_seebug_poc(keyword=keyword, page=1, page_size=limit)
            
            if not poc_list:
                logger.warning(f"⚠️ 从 Seebug 未获取到 POC 数据")
                return []
            
            # 转换为 POC 元数据
            poc_metadata_list = []
            for poc_item in poc_list:
                metadata = POCMetadata(
                    poc_name=poc_item.get("name", ""),
                    poc_id=str(poc_item.get("ssvid", "")),
                    poc_type=poc_item.get("type", "web"),
                    severity=poc_item.get("severity", "medium"),
                    cvss_score=poc_item.get("cvss_score"),
                    description=poc_item.get("description"),
                    author=poc_item.get("author"),
                    source="seebug",
                    version="1.0",
                    tags=poc_item.get("tags", [])
                )
                poc_metadata_list.append(metadata)
                
                # 注册到 POC 注册表
                self.poc_registry[metadata.poc_id] = metadata
            
            # 更新缓存
            self.poc_cache[cache_key] = {
                "timestamp": datetime.now(),
                "pocs": poc_metadata_list
            }
            
            logger.info(f"✅ 从 Seebug 同步完成，获取 {len(poc_metadata_list)} 个 POC")
            return poc_metadata_list
            
        except Exception as e:
            logger.error(f"❌ 从 Seebug 同步 POC 失败: {str(e)}")
            return []
    
    async def download_poc_from_seebug(self, ssvid: int) -> Optional[str]:
        """
        从 Seebug 下载 POC 代码
        
        Args:
            ssvid: POC 的 SSVID
            
        Returns:
            Optional[str]: POC 代码，失败返回 None
        """
        try:
            logger.info(f"📥 开始从 Seebug 下载 POC，SSVID: {ssvid}")
            
            # 检查缓存
            cache_key = f"poc_code_{ssvid}"
            if cache_key in self.poc_cache:
                logger.info(f"✅ 使用缓存的 POC 代码")
                return self.poc_cache[cache_key]["code"]
            
            # 从 Seebug 下载 POC
            poc_code = await download_seebug_poc(ssvid)
            
            if not poc_code:
                logger.warning(f"⚠️ 从 Seebug 下载 POC 失败，SSVID: {ssvid}")
                return None
            
            # 更新缓存
            self.poc_cache[cache_key] = {
                "timestamp": datetime.now(),
                "code": poc_code
            }
            
            logger.info(f"✅ 从 Seebug 下载 POC 完成，代码长度: {len(poc_code)}")
            return poc_code
            
        except Exception as e:
            logger.error(f"❌ 从 Seebug 下载 POC 失败: {str(e)}")
            return None
    
    async def load_local_poc(self, poc_path: str) -> Optional[POCMetadata]:
        """
        加载本地自定义 POC 脚本
        
        Args:
            poc_path: POC 文件路径
            
        Returns:
            Optional[POCMetadata]: POC 元数据，失败返回 None
        """
        try:
            logger.info(f"📂 开始加载本地 POC，路径: {poc_path}")
            
            path = Path(poc_path)
            if not path.exists():
                logger.warning(f"⚠️ POC 文件不存在: {poc_path}")
                return None
            
            # 读取 POC 文件
            with open(path, 'r', encoding='utf-8') as f:
                poc_code = f.read()
            
            # 解析 POC 元数据（从注释中提取）
            poc_name = path.stem
            poc_id = f"local_{poc_name}"
            
            metadata = POCMetadata(
                poc_name=poc_name,
                poc_id=poc_id,
                poc_type="local",
                severity="medium",
                description=f"本地自定义 POC: {poc_name}",
                source="local",
                version="1.0",
                tags=["custom"]
            )
            
            # 注册到 POC 注册表
            self.poc_registry[metadata.poc_id] = metadata
            
            logger.info(f"✅ 加载本地 POC 完成: {poc_name}")
            return metadata
            
        except Exception as e:
            logger.error(f"❌ 加载本地 POC 失败: {str(e)}")
            return None
    
    async def load_local_pocs_from_directory(
        self,
        directory: str,
        pattern: str = "*.py"
    ) -> List[POCMetadata]:
        """
        从目录批量加载本地 POC 脚本
        
        Args:
            directory: POC 目录路径
            pattern: 文件匹配模式
            
        Returns:
            List[POCMetadata]: POC 元数据列表
        """
        try:
            logger.info(f"📂 开始从目录加载 POC，路径: {directory}, 模式: {pattern}")
            
            dir_path = Path(directory)
            if not dir_path.exists():
                logger.warning(f"⚠️ 目录不存在: {directory}")
                return []
            
            # 遍历目录加载 POC
            poc_metadata_list = []
            for poc_file in dir_path.glob(pattern):
                metadata = await self.load_local_poc(str(poc_file))
                if metadata:
                    poc_metadata_list.append(metadata)
            
            logger.info(f"✅ 从目录加载 POC 完成，获取 {len(poc_metadata_list)} 个 POC")
            return poc_metadata_list
            
        except Exception as e:
            logger.error(f"❌ 从目录加载 POC 失败: {str(e)}")
            return []
    
    def get_poc_metadata(self, poc_id: str) -> Optional[POCMetadata]:
        """
        获取 POC 元数据
        
        Args:
            poc_id: POC ID
            
        Returns:
            Optional[POCMetadata]: POC 元数据，不存在返回 None
        """
        return self.poc_registry.get(poc_id)
    
    def get_all_pocs(self) -> List[POCMetadata]:
        """
        获取所有已注册的 POC
        
        Returns:
            List[POCMetadata]: 所有 POC 元数据列表
        """
        return list(self.poc_registry.values())
    
    def get_pocs_by_type(self, poc_type: str) -> List[POCMetadata]:
        """
        按类型获取 POC
        
        Args:
            poc_type: POC 类型
            
        Returns:
            List[POCMetadata]: 指定类型的 POC 列表
        """
        return [
            poc for poc in self.poc_registry.values()
            if poc.poc_type == poc_type
        ]
    
    def get_pocs_by_severity(self, severity: str) -> List[POCMetadata]:
        """
        按严重度获取 POC
        
        Args:
            severity: 严重度（critical, high, medium, low, info）
            
        Returns:
            List[POCMetadata]: 指定严重度的 POC 列表
        """
        return [
            poc for poc in self.poc_registry.values()
            if poc.severity == severity
        ]
    
    def update_poc_version(self, poc_id: str, new_version: str):
        """
        更新 POC 版本
        
        Args:
            poc_id: POC ID
            new_version: 新版本号
        """
        if poc_id in self.poc_registry:
            self.poc_registry[poc_id].version = new_version
            logger.info(f"✅ 更新 POC 版本: {poc_id} -> {new_version}")
        else:
            logger.warning(f"⚠️ POC 不存在: {poc_id}")
    
    def clear_cache(self):
        """
        清除 POC 缓存
        """
        self.poc_cache.clear()
        logger.info("✅ POC 缓存已清除")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 包含缓存统计信息的字典
        """
        return {
            "poc_count": len(self.poc_registry),
            "cache_entries": len(self.poc_cache),
            "cache_size_mb": sum(
                len(str(poc)) for poc in self.poc_cache.values()
            ) / (1024 * 1024)
        }
    
    async def create_verification_task(
        self,
        poc_id: str,
        target: str,
        priority: int = 5,
        task_id: Optional[str] = None
    ) -> POCVerificationTask:
        """
        创建 POC 验证任务
        
        Args:
            poc_id: POC ID
            target: 验证目标
            priority: 优先级
            task_id: 关联的任务 ID
            
        Returns:
            POCVerificationTask: 创建的验证任务
        """
        try:
            # 获取 POC 元数据
            poc_metadata = self.get_poc_metadata(poc_id)
            if not poc_metadata:
                raise ValueError(f"POC 不存在: {poc_id}")
            
            # 创建验证任务
            verification_task = await POCVerificationTask.create(
                task_id=task_id,
                poc_name=poc_metadata.poc_name,
                poc_id=poc_id,
                poc_code=await self.get_poc_code(poc_id),
                target=target,
                priority=priority,
                status="pending",
                progress=0,
                config={
                    "poc_metadata": poc_metadata.to_dict(),
                    "source": poc_metadata.source
                }
            )
            
            logger.info(f"✅ 创建 POC 验证任务: {poc_metadata.poc_name} -> {target}")
            return verification_task
            
        except Exception as e:
            logger.error(f"❌ 创建 POC 验证任务失败: {str(e)}")
            raise
    
    async def get_poc_code(self, poc_id: str) -> Optional[str]:
        """
        获取 POC 代码
        
        Args:
            poc_id: POC ID
            
        Returns:
            Optional[str]: POC 代码
        """
        # 检查缓存
        cache_key = f"poc_code_{poc_id}"
        if cache_key in self.poc_cache:
            return self.poc_cache[cache_key]["code"]
        
        # 如果是本地 POC，从文件读取
        if poc_id.startswith("local_"):
            poc_name = poc_id.replace("local_", "")
            local_path = Path("pocs") / f"{poc_name}.py"
            if local_path.exists():
                with open(local_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        # 如果是 Seebug POC，从缓存或重新下载
        ssvid = poc_id.replace("seebug_", "")
        try:
            return await self.download_poc_from_seebug(int(ssvid))
        except (ValueError, TypeError):
            return None


# 全局 POC 管理器实例
poc_manager = POCManager()

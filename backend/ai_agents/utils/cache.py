"""
缓存管理模块

提供统一的缓存管理功能，支持TTL、统计信息等
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    缓存管理器
    
    提供统一的缓存管理接口，支持TTL、统计信息等功能
    """
    
    def __init__(self, ttl: int = 3600):
        """
        初始化缓存管理器
        
        Args:
            ttl: 缓存过期时间(秒)，默认3600秒(1小时)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
        logger.info(f"✅ 缓存管理器初始化完成, TTL: {ttl}秒")
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存数据，不存在或已过期返回None
        """
        if key not in self.cache:
            return None
        
        cache_item = self.cache[key]
        cache_age = (datetime.now() - cache_item["timestamp"]).total_seconds()
        
        if cache_age > self.ttl:
            del self.cache[key]
            logger.debug(f"缓存已过期: {key}")
            return None
        
        logger.debug(f"缓存命中: {key}")
        return cache_item["data"]
    
    def set(self, key: str, data: Any):
        """
        设置缓存
        
        Args:
            key: 缓存键
            data: 缓存数据
        """
        self.cache[key] = {
            "timestamp": datetime.now(),
            "data": data
        }
        logger.debug(f"缓存已设置: {key}")
    
    def delete(self, key: str):
        """
        删除缓存
        
        Args:
            key: 缓存键
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"缓存已删除: {key}")
    
    def clear(self):
        """
        清除所有缓存
        """
        self.cache.clear()
        logger.info("✅ 所有缓存已清除")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 包含缓存统计信息的字典
        """
        cache_size_mb = sum(
            len(str(item)) for item in self.cache.values()
        ) / (1024 * 1024)
        
        return {
            "cache_entries": len(self.cache),
            "cache_size_mb": round(cache_size_mb, 2),
            "ttl": self.ttl
        }
    
    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在且未过期
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 缓存是否存在且未过期
        """
        if key not in self.cache:
            return False
        
        cache_item = self.cache[key]
        cache_age = (datetime.now() - cache_item["timestamp"]).total_seconds()
        
        return cache_age <= self.ttl
    
    def get_age(self, key: str) -> Optional[float]:
        """
        获取缓存年龄
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[float]: 缓存年龄(秒)，不存在返回None
        """
        if key not in self.cache:
            return None
        
        cache_item = self.cache[key]
        return (datetime.now() - cache_item["timestamp"]).total_seconds()

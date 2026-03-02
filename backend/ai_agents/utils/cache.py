"""
缓存管理模块

提供统一的缓存管理功能，支持TTL、统计信息等
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import threading

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
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        logger.info(f"✅ 缓存管理器初始化完成, TTL: {ttl}秒")
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存数据，不存在或已过期返回None
        """
        with self._lock:
            if key not in self.cache:
                self._misses += 1
                logger.debug(f"缓存未命中: {key}")
                return None
            
            cache_item = self.cache[key]
            cache_age = (datetime.now() - cache_item["timestamp"]).total_seconds()
            
            if cache_age > self.ttl:
                del self.cache[key]
                self._misses += 1
                self._evictions += 1
                logger.debug(f"缓存已过期: {key}")
                return None
            
            self._hits += 1
            logger.debug(f"缓存命中: {key}")
            return cache_item["data"]
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """
        设置缓存
        
        Args:
            key: 缓存键
            data: 缓存数据
            ttl: 可选的自定义TTL(秒)
        """
        with self._lock:
            self.cache[key] = {
                "timestamp": datetime.now(),
                "data": data,
                "ttl": ttl if ttl is not None else self.ttl
            }
            logger.debug(f"缓存已设置: {key}")
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功删除
        """
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"缓存已删除: {key}")
                return True
            return False
    
    def clear(self):
        """
        清除所有缓存
        """
        with self._lock:
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"✅ 所有缓存已清除, 共 {count} 个条目")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 包含缓存统计信息的字典
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0
            
            cache_size_bytes = sum(
                len(str(item)) for item in self.cache.values()
            )
            cache_size_mb = cache_size_bytes / (1024 * 1024)
            
            return {
                "cache_entries": len(self.cache),
                "cache_size_bytes": cache_size_bytes,
                "cache_size_mb": round(cache_size_mb, 4),
                "ttl": self.ttl,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 2)
            }
    
    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在且未过期
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 缓存是否存在且未过期
        """
        with self._lock:
            if key not in self.cache:
                return False
            
            cache_item = self.cache[key]
            item_ttl = cache_item.get("ttl", self.ttl)
            cache_age = (datetime.now() - cache_item["timestamp"]).total_seconds()
            
            return cache_age <= item_ttl
    
    def get_age(self, key: str) -> Optional[float]:
        """
        获取缓存年龄
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[float]: 缓存年龄(秒)，不存在返回None
        """
        with self._lock:
            if key not in self.cache:
                return None
            
            cache_item = self.cache[key]
            return (datetime.now() - cache_item["timestamp"]).total_seconds()
    
    def get_remaining_ttl(self, key: str) -> Optional[float]:
        """
        获取缓存剩余TTL
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[float]: 剩余TTL(秒)，不存在返回None
        """
        with self._lock:
            if key not in self.cache:
                return None
            
            cache_item = self.cache[key]
            item_ttl = cache_item.get("ttl", self.ttl)
            cache_age = (datetime.now() - cache_item["timestamp"]).total_seconds()
            remaining = item_ttl - cache_age
            
            return max(0, remaining)
    
    def cleanup_expired(self) -> int:
        """
        清理所有过期的缓存条目
        
        Returns:
            int: 清理的条目数量
        """
        with self._lock:
            expired_keys = []
            current_time = datetime.now()
            
            for key, cache_item in self.cache.items():
                item_ttl = cache_item.get("ttl", self.ttl)
                cache_age = (current_time - cache_item["timestamp"]).total_seconds()
                
                if cache_age > item_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                self._evictions += 1
            
            if expired_keys:
                logger.info(f"✅ 清理了 {len(expired_keys)} 个过期缓存条目")
            
            return len(expired_keys)
    
    def get_keys(self) -> List[str]:
        """
        获取所有缓存键
        
        Returns:
            List[str]: 缓存键列表
        """
        with self._lock:
            return list(self.cache.keys())
    
    def get_expired_keys(self) -> List[str]:
        """
        获取所有已过期的缓存键
        
        Returns:
            List[str]: 已过期的缓存键列表
        """
        with self._lock:
            expired_keys = []
            current_time = datetime.now()
            
            for key, cache_item in self.cache.items():
                item_ttl = cache_item.get("ttl", self.ttl)
                cache_age = (current_time - cache_item["timestamp"]).total_seconds()
                
                if cache_age > item_ttl:
                    expired_keys.append(key)
            
            return expired_keys
    
    def reset_stats(self):
        """
        重置统计信息
        """
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            logger.info("✅ 缓存统计信息已重置")
    
    def invalidate(self, pattern: str = None) -> int:
        """
        使缓存失效
        
        Args:
            pattern: 可选的键模式匹配(前缀匹配)
            
        Returns:
            int: 删除的条目数量
        """
        with self._lock:
            if pattern is None:
                count = len(self.cache)
                self.cache.clear()
                logger.info(f"✅ 使所有缓存失效, 共 {count} 个条目")
                return count
            
            keys_to_delete = [k for k in self.cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self.cache[key]
            
            if keys_to_delete:
                logger.info(f"✅ 使 {len(keys_to_delete)} 个缓存条目失效 (模式: {pattern})")
            
            return len(keys_to_delete)
    
    def __len__(self) -> int:
        return len(self.cache)
    
    def __contains__(self, key: str) -> bool:
        return self.exists(key)

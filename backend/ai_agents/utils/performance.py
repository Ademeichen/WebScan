"""
性能优化工具模块

提供缓存机制、超时控制、资源管理等性能优化功能。
"""
import time
import functools
import threading
from typing import Any, Callable, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def record(self, name: str, duration: float, success: bool = True):
        """记录性能指标"""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = {
                    "count": 0,
                    "total_time": 0.0,
                    "success_count": 0,
                    "failure_count": 0,
                    "min_time": float('inf'),
                    "max_time": 0.0,
                    "avg_time": 0.0
                }

            metric = self.metrics[name]
            metric["count"] += 1
            metric["total_time"] += duration
            metric["min_time"] = min(metric["min_time"], duration)
            metric["max_time"] = max(metric["max_time"], duration)
            metric["avg_time"] = metric["total_time"] / metric["count"]

            if success:
                metric["success_count"] += 1
            else:
                metric["failure_count"] += 1

    def get_metrics(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定指标"""
        with self._lock:
            return self.metrics.get(name)

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有指标"""
        with self._lock:
            return self.metrics.copy()

    def reset(self):
        """重置所有指标"""
        with self._lock:
            self.metrics.clear()


class CacheManager:
    """缓存管理器"""

    def __init__(self, default_ttl: int = 3600):
        """
        初始化缓存管理器

        Args:
            default_ttl: 默认缓存时间(秒)
        """
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.default_ttl = default_ttl
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key not in self.cache:
                self.misses += 1
                return None

            value, expiry = self.cache[key]

            if datetime.now() > expiry:
                del self.cache[key]
                self.misses += 1
                return None

            self.hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        if ttl is None:
            ttl = self.default_ttl

        expiry = datetime.now() + timedelta(seconds=ttl)

        with self._lock:
            self.cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def cleanup_expired(self) -> int:
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = []

        with self._lock:
            for key, (_, expiry) in self.cache.items():
                if now > expiry:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "size": len(self.cache),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.2f}%"
            }


class TimeoutController:
    """超时控制器"""

    def __init__(self, default_timeout: int = 60):
        """
        初始化超时控制器

        Args:
            default_timeout: 默认超时时间(秒)
        """
        self.default_timeout = default_timeout
        self.timeouts: Dict[str, int] = {
            "tool_execution": 120,
            "code_generation": 180,
            "code_execution": 60,
            "capability_enhancement": 300,
            "poc_verification": 60,
            "vulnerability_analysis": 30,
            "report_generation": 30
        }

    def get_timeout(self, operation: str) -> int:
        """获取操作超时时间"""
        return self.timeouts.get(operation, self.default_timeout)

    def set_timeout(self, operation: str, timeout: int) -> None:
        """设置操作超时时间"""
        self.timeouts[operation] = timeout

    def with_timeout(self, operation: str, timeout: Optional[int] = None):
        """超时装饰器"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                import asyncio
                actual_timeout = timeout or self.get_timeout(operation)
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=actual_timeout
                    )
                except asyncio.TimeoutError:
                    logger.error(f"操作超时: {operation} (超时时间: {actual_timeout}秒)")
                    raise TimeoutError(f"操作超时: {operation}")

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError(f"操作超时: {operation}")

                actual_timeout = timeout or self.get_timeout(operation)

                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(actual_timeout)

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator


class ResourceManager:
    """资源管理器"""

    def __init__(self):
        """初始化资源管理器"""
        self.resources: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def register(self, name: str, resource: Any, cleanup_func: Optional[Callable] = None) -> None:
        """注册资源"""
        with self._lock:
            self.resources[name] = {
                "resource": resource,
                "cleanup_func": cleanup_func,
                "created_at": datetime.now()
            }
            logger.info(f"注册资源: {name}")

    def get(self, name: str) -> Optional[Any]:
        """获取资源"""
        with self._lock:
            if name in self.resources:
                return self.resources[name]["resource"]
            return None

    def cleanup(self, name: str) -> bool:
        """清理指定资源"""
        with self._lock:
            if name not in self.resources:
                return False

            resource_info = self.resources[name]
            cleanup_func = resource_info.get("cleanup_func")

            if cleanup_func:
                try:
                    cleanup_func(resource_info["resource"])
                    logger.info(f"清理资源: {name}")
                except Exception as e:
                    logger.error(f"清理资源失败 {name}: {str(e)}")

            del self.resources[name]
            return True

    def cleanup_all(self) -> int:
        """清理所有资源"""
        with self._lock:
            names = list(self.resources.keys())
            count = 0

            for name in names:
                if self.cleanup(name):
                    count += 1

            return count

    def get_stats(self) -> Dict[str, Any]:
        """获取资源统计信息"""
        with self._lock:
            return {
                "total_resources": len(self.resources),
                "resources": list(self.resources.keys())
            }


def measure_performance(metrics: PerformanceMetrics, name: str):
    """性能测量装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = False

            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            finally:
                duration = time.time() - start_time
                metrics.record(name, duration, success)
                logger.debug(f"{name} 耗时: {duration:.2f}秒")

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = False

            try:
                result = func(*args, **kwargs)
                success = True
                return result
            finally:
                duration = time.time() - start_time
                metrics.record(name, duration, success)
                logger.debug(f"{name} 耗时: {duration:.2f}秒")

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def cached(cache_manager: CacheManager, ttl: Optional[int] = None):
    """缓存装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"

            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value

            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"缓存设置: {cache_key}")
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"

            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value

            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"缓存设置: {cache_key}")
            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"第 {attempt + 1} 次尝试失败: {str(e)}")

                    if attempt < max_attempts - 1:
                        logger.info(f"等待 {current_delay:.2f} 秒后重试...")
                        import asyncio
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

            logger.error(f"所有尝试失败,共 {max_attempts} 次")
            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time as time_module
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"第 {attempt + 1} 次尝试失败: {str(e)}")

                    if attempt < max_attempts - 1:
                        logger.info(f"等待 {current_delay:.2f} 秒后重试...")
                        time_module.sleep(current_delay)
                        current_delay *= backoff

            logger.error(f"所有尝试失败,共 {max_attempts} 次")
            raise last_exception

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        """初始化性能监控器"""
        self.metrics = PerformanceMetrics()
        self.cache = CacheManager()
        self.timeout = TimeoutController()
        self.resource = ResourceManager()

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            "metrics": self.metrics.get_all_metrics(),
            "cache_stats": self.cache.get_stats(),
            "resource_stats": self.resource.get_stats(),
            "timeouts": self.timeout.timeouts
        }

    def reset(self) -> None:
        """重置监控器"""
        self.metrics.reset()
        self.cache.clear()
        self.resource.cleanup_all()


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()

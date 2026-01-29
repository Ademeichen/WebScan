"""
性能优化模块

提供系统性能优化功能，包括：
- API响应缓存
- 异步并发控制
- 数据库查询优化
- 内存管理优化
"""
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """
    性能指标数据类
    """
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    peak_memory_usage: float = 0.0

    @property
    def success_rate(self) -> float:
        """
        成功率
        """
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def average_response_time(self) -> float:
        """
        平均响应时间
        """
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests

    @property
    def cache_hit_rate(self) -> float:
        """
        缓存命中率
        """
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return (self.cache_hits / total_cache_requests) * 100


class APICache:
    """
    API响应缓存管理器

    提供高效的API响应缓存机制，减少重复请求
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        初始化API缓存

        Args:
            default_ttl: 默认缓存时间（秒）
            max_size: 最大缓存条目数
        """
        self.cache: Dict[str, tuple] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.access_times: Dict[str, datetime] = {}
        self.metrics = PerformanceMetrics()

    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据

        Args:
            key: 缓存键

        Returns:
            Optional[Any]: 缓存的数据，如果不存在或已过期返回None
        """
        if key not in self.cache:
            self.metrics.cache_misses += 1
            return None

        data, timestamp, ttl = self.cache[key]

        if datetime.now() - timestamp > timedelta(seconds=ttl):
            del self.cache[key]
            self.metrics.cache_misses += 1
            return None

        self.metrics.cache_hits += 1
        self.access_times[key] = datetime.now()
        return data

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存数据

        Args:
            key: 缓存键
            data: 要缓存的数据
            ttl: 缓存时间（秒），默认使用default_ttl
        """
        ttl = ttl or self.default_ttl

        if len(self.cache) >= self.max_size:
            self._evict_lru()

        self.cache[key] = (data, datetime.now(), ttl)
        self.access_times[key] = datetime.now()

    def delete(self, key: str) -> bool:
        """
        删除缓存数据

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功删除
        """
        if key in self.cache:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return True
        return False

    def clear(self) -> None:
        """
        清除所有缓存
        """
        self.cache.clear()
        self.access_times.clear()
        logger.info("✅ API缓存已清除")

    def _evict_lru(self) -> None:
        """
        淘汰最近最少使用的缓存条目
        """
        if not self.access_times:
            return

        lru_key = min(self.access_times, key=self.access_times.get)
        del self.cache[lru_key]
        del self.access_times[lru_key]
        logger.debug(f"🔄 淘汰LRU缓存条目: {lru_key}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        获取缓存指标

        Returns:
            Dict: 缓存指标
        """
        return {
            "cache_entries": len(self.cache),
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "cache_hit_rate": f"{self.metrics.cache_hit_rate:.2f}%",
            "max_size": self.max_size,
            "default_ttl": self.default_ttl
        }


class AsyncConcurrencyController:
    """
    异步并发控制器

    控制异步任务的并发数量，防止资源耗尽
    """

    def __init__(self, max_concurrent: int = 10):
        """
        初始化并发控制器

        Args:
            max_concurrent: 最大并发数
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks = 0
        self.total_tasks = 0
        self.metrics = PerformanceMetrics()

    async def run(self, coro: Awaitable[Any]) -> Any:
        """
        运行异步任务（带并发控制）

        Args:
            coro: 协程对象

        Returns:
            Any: 协程的返回值
        """
        async with self.semaphore:
            self.active_tasks += 1
            self.total_tasks += 1

            start_time = time.time()

            try:
                result = await coro
                self.metrics.successful_requests += 1
                self.metrics.total_requests += 1

                elapsed_time = time.time() - start_time
                self.metrics.total_response_time += elapsed_time

                return result

            except Exception as e:
                self.metrics.failed_requests += 1
                self.metrics.total_requests += 1
                logger.error(f"❌ 异步任务执行失败: {e}")
                raise

            finally:
                self.active_tasks -= 1

    async def run_batch(
        self,
        coros: list[Awaitable[Any]]
    ) -> list[Any]:
        """
        批量运行异步任务

        Args:
            coros: 协程对象列表

        Returns:
            list: 返回值列表
        """
        tasks = [self.run(coro) for coro in coros]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_metrics(self) -> Dict[str, Any]:
        """
        获取并发控制指标

        Returns:
            Dict: 并发控制指标
        """
        return {
            "max_concurrent": self.max_concurrent,
            "active_tasks": self.active_tasks,
            "total_tasks": self.total_tasks,
            "success_rate": f"{self.metrics.success_rate:.2f}%",
            "average_response_time": f"{self.metrics.average_response_time:.2f}s"
        }


class DatabaseQueryOptimizer:
    """
    数据库查询优化器

    提供数据库查询优化建议和索引管理
    """

    def __init__(self):
        """
        初始化查询优化器
        """
        self.query_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "slow_queries": 0
        })

    def record_query(
        self,
        query_name: str,
        execution_time: float,
        threshold: float = 1.0
    ) -> None:
        """
        记录查询执行情况

        Args:
            query_name: 查询名称
            execution_time: 执行时间（秒）
            threshold: 慢查询阈值（秒）
        """
        stats = self.query_stats[query_name]
        stats["count"] += 1
        stats["total_time"] += execution_time

        if execution_time > threshold:
            stats["slow_queries"] += 1
            logger.warning(
                f"⚠️ 慢查询检测: {query_name} "
                f"耗时 {execution_time:.2f}s (阈值: {threshold}s)"
            )

    def get_query_stats(self) -> Dict[str, Any]:
        """
        获取查询统计信息

        Returns:
            Dict: 查询统计
        """
        stats = {}
        for query_name, data in self.query_stats.items():
            avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0
            stats[query_name] = {
                "count": data["count"],
                "total_time": data["total_time"],
                "average_time": avg_time,
                "slow_queries": data["slow_queries"]
            }
        return stats

    def get_optimization_suggestions(self) -> list[str]:
        """
        获取优化建议

        Returns:
            list: 优化建议列表
        """
        suggestions = []

        for query_name, data in self.query_stats.items():
            avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0

            if avg_time > 1.0:
                suggestions.append(
                    f"⚠️ 查询 '{query_name}' 平均耗时 {avg_time:.2f}s，"
                    f"建议添加索引或优化查询逻辑"
                )

            if data["slow_queries"] / data["count"] > 0.1 if data["count"] > 0 else False:
                suggestions.append(
                    f"⚠️ 查询 '{query_name}' 慢查询率过高 "
                    f"({data['slow_queries']}/{data['count']})，"
                    f"建议检查查询计划"
                )

        return suggestions


class MemoryOptimizer:
    """
    内存优化器

    监控和优化内存使用
    """

    def __init__(self):
        """
        初始化内存优化器
        """
        self.memory_usage_history: list[float] = []
        self.peak_memory = 0.0
        self.memory_threshold = 1024 * 1024 * 1024

    def record_memory_usage(self, usage: float) -> None:
        """
        记录内存使用情况

        Args:
            usage: 内存使用量（字节）
        """
        self.memory_usage_history.append(usage)
        self.peak_memory = max(self.peak_memory, usage)

        if len(self.memory_usage_history) > 1000:
            self.memory_usage_history = self.memory_usage_history[-1000:]

        if usage > self.memory_threshold:
            logger.warning(
                f"⚠️ 内存使用超过阈值: {usage / (1024 * 1024):.2f}MB"
            )

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取内存统计信息

        Returns:
            Dict: 内存统计
        """
        avg_memory = (
            sum(self.memory_usage_history) / len(self.memory_usage_history)
            if self.memory_usage_history else 0
        )

        return {
            "current_memory": self.memory_usage_history[-1] if self.memory_usage_history else 0,
            "peak_memory": self.peak_memory,
            "average_memory": avg_memory,
            "memory_threshold": self.memory_threshold,
            "history_length": len(self.memory_usage_history)
        }


def cache_api_response(
    cache: APICache,
    ttl: int = 300
):
    """
    API响应缓存装饰器

    Args:
        cache: 缓存实例
        ttl: 缓存时间（秒）
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"

            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"✅ 使用缓存: {func.__name__}")
                return cached_data

            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


def measure_performance(
    metrics: PerformanceMetrics
):
    """
    性能测量装饰器

    Args:
        metrics: 性能指标实例
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                metrics.successful_requests += 1
                return result

            except Exception as e:
                metrics.failed_requests += 1
                raise

            finally:
                metrics.total_requests += 1
                elapsed_time = time.time() - start_time
                metrics.total_response_time += elapsed_time

                if elapsed_time > 5.0:
                    logger.warning(
                        f"⚠️ 函数 {func.__name__} 执行时间过长: "
                        f"{elapsed_time:.2f}s"
                    )

        return wrapper
    return decorator


class PerformanceOptimizer:
    """
    性能优化器（统一入口）

    整合所有性能优化功能
    """

    def __init__(
        self,
        enable_cache: bool = True,
        max_concurrent: int = 10,
        cache_ttl: int = 300
    ):
        """
        初始化性能优化器

        Args:
            enable_cache: 是否启用缓存
            max_concurrent: 最大并发数
            cache_ttl: 缓存时间（秒）
        """
        self.api_cache = APICache(default_ttl=cache_ttl) if enable_cache else None
        self.concurrency_controller = AsyncConcurrencyController(max_concurrent)
        self.query_optimizer = DatabaseQueryOptimizer()
        self.memory_optimizer = MemoryOptimizer()
        self.global_metrics = PerformanceMetrics()

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        获取所有性能指标

        Returns:
            Dict: 性能指标
        """
        return {
            "cache_metrics": self.api_cache.get_metrics() if self.api_cache else None,
            "concurrency_metrics": self.concurrency_controller.get_metrics(),
            "query_metrics": self.query_optimizer.get_query_stats(),
            "memory_metrics": self.memory_optimizer.get_memory_stats(),
            "global_metrics": {
                "total_requests": self.global_metrics.total_requests,
                "success_rate": f"{self.global_metrics.success_rate:.2f}%",
                "average_response_time": f"{self.global_metrics.average_response_time:.2f}s"
            }
        }

    def get_optimization_report(self) -> str:
        """
        获取优化报告

        Returns:
            str: 优化报告
        """
        report = ["📊 性能优化报告", "=" * 50]

        if self.api_cache:
            cache_metrics = self.api_cache.get_metrics()
            report.append(
                f"\n📦 缓存统计:\n"
                f"  - 缓存条目数: {cache_metrics['cache_entries']}\n"
                f"  - 缓存命中率: {cache_metrics['cache_hit_rate']}\n"
                f"  - 缓存命中: {cache_metrics['cache_hits']}\n"
                f"  - 缓存未命中: {cache_metrics['cache_misses']}"
            )

        concurrency_metrics = self.concurrency_controller.get_metrics()
        report.append(
            f"\n🔄 并发控制统计:\n"
            f"  - 最大并发数: {concurrency_metrics['max_concurrent']}\n"
            f"  - 活跃任务: {concurrency_metrics['active_tasks']}\n"
            f"  - 总任务数: {concurrency_metrics['total_tasks']}\n"
            f"  - 成功率: {concurrency_metrics['success_rate']}\n"
            f"  - 平均响应时间: {concurrency_metrics['average_response_time']}"
        )

        suggestions = self.query_optimizer.get_optimization_suggestions()
        if suggestions:
            report.append("\n⚠️ 优化建议:")
            for suggestion in suggestions:
                report.append(f"  - {suggestion}")

        return "\n".join(report)


global_performance_optimizer = PerformanceOptimizer(
    enable_cache=True,
    max_concurrent=10,
    cache_ttl=300
)

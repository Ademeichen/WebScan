"""
资源限制器

提供CPU、内存、网络和并发任务数限制功能。
"""
import asyncio
import time
import gc
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil未安装，资源监控功能将受限")


class LimitType(Enum):
    """限制类型枚举"""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    CONCURRENT = "concurrent"


@dataclass
class ResourceLimits:
    """资源限制配置"""
    max_cpu_percent: float = 80.0
    max_memory_mb: float = 512.0
    max_requests_per_second: int = 100
    max_concurrent_tasks: int = 10
    max_connections: int = 50
    check_interval: float = 1.0
    enable_gc_on_high_memory: bool = True


@dataclass
class ResourceUsage:
    """资源使用情况"""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    active_tasks: int = 0
    active_connections: int = 0
    requests_per_second: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "active_tasks": self.active_tasks,
            "active_connections": self.active_connections,
            "requests_per_second": self.requests_per_second,
            "timestamp": self.timestamp
        }


@dataclass
class TokenBucket:
    """令牌桶算法实现"""
    capacity: int
    tokens: float = 0.0
    refill_rate: float = 1.0
    last_refill: float = field(default_factory=time.time)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self):
        self.tokens = float(self.capacity)

    async def consume(self, tokens: int = 1) -> bool:
        """尝试消费令牌"""
        async with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_for_token(self, tokens: int = 1, timeout: float = 30.0) -> bool:
        """等待获取令牌"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if await self.consume(tokens):
                return True
            await asyncio.sleep(0.1)
        return False

    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now


class ResourceLimiter:
    """
    资源限制器
    
    提供CPU、内存、网络和并发任务数限制功能。
    """
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        """
        初始化资源限制器
        
        Args:
            limits: 资源限制配置
        """
        self.limits = limits or ResourceLimits()
        self._semaphore = asyncio.Semaphore(self.limits.max_concurrent_tasks)
        self._connection_semaphore = asyncio.Semaphore(self.limits.max_connections)
        self._token_bucket = TokenBucket(
            capacity=self.limits.max_requests_per_second,
            refill_rate=self.limits.max_requests_per_second
        )
        self._active_tasks = 0
        self._active_connections = 0
        self._request_times: List[float] = []
        self._lock = asyncio.Lock()
        self._paused = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._monitor_task: Optional[asyncio.Task] = None
        self._usage_history: List[ResourceUsage] = []
        self._max_history_size = 100
        
        logger.info(f"🔧 资源限制器初始化完成: CPU={self.limits.max_cpu_percent}%, "
                   f"内存={self.limits.max_memory_mb}MB, "
                   f"并发={self.limits.max_concurrent_tasks}, "
                   f"连接={self.limits.max_connections}")
    
    async def start_monitor(self):
        """启动资源监控"""
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info("📊 资源监控已启动")
    
    async def stop_monitor(self):
        """停止资源监控"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
            logger.info("📊 资源监控已停止")
    
    async def _monitor_loop(self):
        """资源监控循环"""
        while True:
            try:
                usage = await self.get_current_usage()
                self._usage_history.append(usage)
                if len(self._usage_history) > self._max_history_size:
                    self._usage_history.pop(0)
                
                if usage.cpu_percent > self.limits.max_cpu_percent:
                    logger.warning(f"⚠️ CPU使用率过高: {usage.cpu_percent:.1f}% > {self.limits.max_cpu_percent}%")
                    await self._handle_cpu_overload(usage)
                
                if usage.memory_mb > self.limits.max_memory_mb:
                    logger.warning(f"⚠️ 内存使用过高: {usage.memory_mb:.1f}MB > {self.limits.max_memory_mb}MB")
                    await self._handle_memory_overload(usage)
                
                await asyncio.sleep(self.limits.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"资源监控异常: {e}")
                await asyncio.sleep(5)
    
    async def _handle_cpu_overload(self, usage: ResourceUsage):
        """处理CPU过载"""
        self._paused = True
        self._pause_event.clear()
        logger.warning("⏸️ 因CPU过载暂停新任务")
        await asyncio.sleep(2)
        self._paused = False
        self._pause_event.set()
        logger.info("▶️ 恢复任务执行")
    
    async def _handle_memory_overload(self, usage: ResourceUsage):
        """处理内存过载"""
        if self.limits.enable_gc_on_high_memory:
            collected = gc.collect()
            logger.info(f"🗑️ 执行垃圾回收，回收对象数: {collected}")
    
    async def get_current_usage(self) -> ResourceUsage:
        """获取当前资源使用情况"""
        usage = ResourceUsage()
        
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            usage.cpu_percent = process.cpu_percent()
            usage.memory_mb = process.memory_info().rss / (1024 * 1024)
        
        async with self._lock:
            usage.active_tasks = self._active_tasks
            usage.active_connections = self._active_connections
            
            now = time.time()
            self._request_times = [t for t in self._request_times if now - t < 1.0]
            usage.requests_per_second = len(self._request_times)
        
        return usage
    
    async def acquire_task(self, timeout: float = 30.0) -> bool:
        """
        获取任务执行许可
        
        Args:
            timeout: 超时时间
            
        Returns:
            bool: 是否成功获取
        """
        await self._pause_event.wait()
        
        if self._paused:
            return False
        
        try:
            async with asyncio.timeout(timeout):
                await self._semaphore.acquire()
                async with self._lock:
                    self._active_tasks += 1
                return True
        except asyncio.TimeoutError:
            logger.warning("⏱️ 获取任务许可超时")
            return False
    
    def release_task(self):
        """释放任务执行许可"""
        self._semaphore.release()
        self._active_tasks = max(0, self._active_tasks - 1)
    
    async def acquire_connection(self, timeout: float = 10.0) -> bool:
        """
        获取连接许可
        
        Args:
            timeout: 超时时间
            
        Returns:
            bool: 是否成功获取
        """
        try:
            async with asyncio.timeout(timeout):
                await self._connection_semaphore.acquire()
                async with self._lock:
                    self._active_connections += 1
                return True
        except asyncio.TimeoutError:
            logger.warning("⏱️ 获取连接许可超时")
            return False
    
    def release_connection(self):
        """释放连接许可"""
        self._connection_semaphore.release()
        self._active_connections = max(0, self._active_connections - 1)
    
    async def acquire_request(self, timeout: float = 5.0) -> bool:
        """
        获取请求许可（限流）
        
        Args:
            timeout: 超时时间
            
        Returns:
            bool: 是否成功获取
        """
        result = await self._token_bucket.wait_for_token(1, timeout)
        if result:
            async with self._lock:
                self._request_times.append(time.time())
        return result
    
    def get_usage_history(self, limit: int = 10) -> List[ResourceUsage]:
        """获取资源使用历史"""
        return self._usage_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取资源统计信息"""
        if not self._usage_history:
            return {}
        
        recent = self._usage_history[-10:]
        return {
            "avg_cpu_percent": sum(u.cpu_percent for u in recent) / len(recent),
            "avg_memory_mb": sum(u.memory_mb for u in recent) / len(recent),
            "max_cpu_percent": max(u.cpu_percent for u in recent),
            "max_memory_mb": max(u.memory_mb for u in recent),
            "current_active_tasks": self._active_tasks,
            "current_active_connections": self._active_connections,
            "limits": {
                "max_cpu_percent": self.limits.max_cpu_percent,
                "max_memory_mb": self.limits.max_memory_mb,
                "max_concurrent_tasks": self.limits.max_concurrent_tasks,
                "max_connections": self.limits.max_connections
            }
        }
    
    async def __aenter__(self):
        await self.start_monitor()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop_monitor()


class TaskLimiter:
    """
    任务限制器
    
    用于限制并发任务执行的上下文管理器。
    """
    
    def __init__(self, limiter: ResourceLimiter, timeout: float = 30.0):
        self.limiter = limiter
        self.timeout = timeout
        self.acquired = False
    
    async def __aenter__(self):
        self.acquired = await self.limiter.acquire_task(self.timeout)
        return self.acquired
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            self.limiter.release_task()


def create_resource_limiter(
    max_cpu_percent: float = 80.0,
    max_memory_mb: float = 512.0,
    max_concurrent_tasks: int = 10,
    max_connections: int = 50,
    max_requests_per_second: int = 100
) -> ResourceLimiter:
    """
    创建资源限制器的工厂函数
    
    Args:
        max_cpu_percent: CPU使用率上限
        max_memory_mb: 内存使用上限(MB)
        max_concurrent_tasks: 最大并发任务数
        max_connections: 最大连接数
        max_requests_per_second: 每秒最大请求数
        
    Returns:
        ResourceLimiter: 资源限制器实例
    """
    limits = ResourceLimits(
        max_cpu_percent=max_cpu_percent,
        max_memory_mb=max_memory_mb,
        max_concurrent_tasks=max_concurrent_tasks,
        max_connections=max_connections,
        max_requests_per_second=max_requests_per_second
    )
    return ResourceLimiter(limits)


default_limiter: Optional[ResourceLimiter] = None


def get_default_limiter() -> ResourceLimiter:
    """获取默认资源限制器"""
    global default_limiter
    if default_limiter is None:
        default_limiter = create_resource_limiter()
    return default_limiter

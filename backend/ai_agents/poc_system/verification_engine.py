"""
POC 验证执行引擎.

负责 POC 验证的核心执行逻辑,包括多线程并发执行、资源限制管理、超时控制、错误重试机制等。
"""

import asyncio
import hashlib
import heapq
import logging
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union

import psutil

from backend.Pocsuite3Agent.agent import POCResult, Pocsuite3Agent
from backend.ai_agents.poc_system.poc_manager import poc_manager
from backend.config import settings
from backend.models import POCExecutionLog, POCVerificationResult, POCVerificationTask

logger = logging.getLogger(__name__)


class ExecutionPriority(Enum):
    """执行优先级枚举."""

    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class ExecutionStatus(Enum):
    """执行状态枚举."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ResourceThrottleAction(Enum):
    """资源节流动作枚举."""

    NONE = "none"
    WARNING = "warning"
    THROTTLE = "throttle"
    PAUSE = "pause"


@dataclass
class ExecutionConfig:
    """执行配置类.

    用于配置单个 POC 执行的参数和限制。

    Attributes:
        poc_id: POC 唯一标识.
        target: 目标地址.
        poc_code: POC 代码.
        timeout: 超时时间.
        max_retries: 最大重试次数.
        retry_delay_base: 重试延迟基数.
        retry_delay_max: 最大重试延迟.
        enable_sandbox: 是否启用沙箱.
        max_memory_mb: 最大内存(MB).
        max_cpu_percent: 最大 CPU 百分比.
        priority: 执行优先级.
        enable_cache: 是否启用缓存.
        cache_ttl: 缓存 TTL.
    """

    poc_id: str
    target: str
    poc_code: str
    timeout: int = 60
    max_retries: int = 3
    retry_delay_base: float = 2.0
    retry_delay_max: float = 60.0
    enable_sandbox: bool = True
    max_memory_mb: int = 512
    max_cpu_percent: float = 80.0
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    enable_cache: bool = True
    cache_ttl: int = 3600


@dataclass
class ExecutionStats:
    """执行统计类.

    用于跟踪 POC 验证执行的统计信息。

    Attributes:
        total_pocs: 总 POC 数.
        executed_count: 已执行数量.
        vulnerable_count: 漏洞数量.
        failed_count: 失败数量.
        cancelled_count: 取消数量.
        timeout_count: 超时数量.
        total_execution_time: 总执行时间.
        average_execution_time: 平均执行时间.
        success_rate: 成功率.
        cache_hit_count: 缓存命中数.
        retry_count: 重试次数.
    """

    total_pocs: int = 0
    executed_count: int = 0
    vulnerable_count: int = 0
    failed_count: int = 0
    cancelled_count: int = 0
    timeout_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    success_rate: float = 0.0
    cache_hit_count: int = 0
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式.

        Returns:
            Dict[str, Any]: 统计信息字典.
        """
        return {
            "total_pocs": self.total_pocs,
            "executed_count": self.executed_count,
            "vulnerable_count": self.vulnerable_count,
            "failed_count": self.failed_count,
            "cancelled_count": self.cancelled_count,
            "timeout_count": self.timeout_count,
            "total_execution_time": self.total_execution_time,
            "average_execution_time": self.average_execution_time,
            "success_rate": self.success_rate,
            "cache_hit_count": self.cache_hit_count,
            "retry_count": self.retry_count,
        }


@dataclass
class ResourceLimits:
    """资源限制配置.

    Attributes:
        max_memory_mb: 最大内存(MB).
        max_cpu_percent: 最大 CPU 百分比.
        max_concurrent_executions: 最大并发执行数.
        throttle_threshold_memory: 内存节流阈值.
        throttle_threshold_cpu: CPU 节流阈值.
        pause_threshold_memory: 内存暂停阈值.
        pause_threshold_cpu: CPU 暂停阈值.
    """

    max_memory_mb: int = 1024
    max_cpu_percent: float = 80.0
    max_concurrent_executions: int = 10
    throttle_threshold_memory: float = 0.8
    throttle_threshold_cpu: float = 0.8
    pause_threshold_memory: float = 0.95
    pause_threshold_cpu: float = 0.95

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式.

        Returns:
            Dict[str, Any]: 资源限制字典.
        """
        return {
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_percent": self.max_cpu_percent,
            "max_concurrent_executions": self.max_concurrent_executions,
            "throttle_threshold_memory": self.throttle_threshold_memory,
            "throttle_threshold_cpu": self.throttle_threshold_cpu,
            "pause_threshold_memory": self.pause_threshold_memory,
            "pause_threshold_cpu": self.pause_threshold_cpu,
        }


@dataclass
class ResourceUsage:
    """资源使用情况.

    Attributes:
        memory_mb: 内存使用(MB).
        memory_percent: 内存使用百分比.
        cpu_percent: CPU 使用百分比.
        timestamp: 时间戳.
    """

    memory_mb: float = 0.0
    memory_percent: float = 0.0
    cpu_percent: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式.

        Returns:
            Dict[str, Any]: 资源使用字典.
        """
        return {
            "memory_mb": self.memory_mb,
            "memory_percent": self.memory_percent,
            "cpu_percent": self.cpu_percent,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass(order=True)
class PrioritizedTask:
    """优先级任务包装器.

    Attributes:
        priority: 优先级.
        sequence: 序列号.
        task_data: 任务数据.
        config: 执行配置.
        callback: 回调函数.
        created_at: 创建时间.
    """

    priority: int
    sequence: int
    task_data: Any = field(compare=False)
    config: ExecutionConfig = field(compare=False)
    callback: Optional[Callable] = field(compare=False, default=None)
    created_at: datetime = field(compare=False, default_factory=datetime.now)


@dataclass
class ExecutionHistoryEntry:
    """执行历史条目.

    Attributes:
        task_id: 任务 ID.
        poc_id: POC ID.
        poc_name: POC 名称.
        target: 目标地址.
        status: 执行状态.
        start_time: 开始时间.
        end_time: 结束时间.
        execution_time: 执行时间.
        vulnerable: 是否存在漏洞.
        error: 错误信息.
        retry_count: 重试次数.
        cache_hit: 是否缓存命中.
    """

    task_id: str
    poc_id: str
    poc_name: str
    target: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time: float = 0.0
    vulnerable: bool = False
    error: Optional[str] = None
    retry_count: int = 0
    cache_hit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式.

        Returns:
            Dict[str, Any]: 历史条目字典.
        """
        return {
            "task_id": self.task_id,
            "poc_id": self.poc_id,
            "poc_name": self.poc_name,
            "target": self.target,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "vulnerable": self.vulnerable,
            "error": self.error,
            "retry_count": self.retry_count,
            "cache_hit": self.cache_hit,
        }


@dataclass
class ExecutionProgress:
    """执行进度信息.

    Attributes:
        task_id: 任务 ID.
        poc_name: POC 名称.
        status: 执行状态.
        progress: 进度百分比.
        message: 消息.
        current_step: 当前步骤.
        total_steps: 总步骤数.
        completed_steps: 已完成步骤数.
        elapsed_time: 已用时间.
        estimated_remaining: 预计剩余时间.
        resource_usage: 资源使用情况.
    """

    task_id: str
    poc_name: str
    status: ExecutionStatus
    progress: int
    message: str
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    elapsed_time: float = 0.0
    estimated_remaining: float = 0.0
    resource_usage: Optional[ResourceUsage] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式.

        Returns:
            Dict[str, Any]: 进度信息字典.
        """
        return {
            "task_id": self.task_id,
            "poc_name": self.poc_name,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "elapsed_time": self.elapsed_time,
            "estimated_remaining": self.estimated_remaining,
            "resource_usage": self.resource_usage.to_dict() if self.resource_usage else None,
        }


class ProgressCallback(ABC):
    """进度回调抽象基类."""

    @abstractmethod
    async def on_progress(self, progress: ExecutionProgress) -> None:
        """进度更新回调.

        Args:
            progress: 执行进度信息.
        """
        pass

    @abstractmethod
    async def on_complete(self, result: POCVerificationResult) -> None:
        """完成回调.

        Args:
            result: 验证结果.
        """
        pass

    @abstractmethod
    async def on_error(self, error: Exception, task_id: str) -> None:
        """错误回调.

        Args:
            error: 异常对象.
            task_id: 任务 ID.
        """
        pass


class WebSocketProgressCallback(ProgressCallback):
    """WebSocket 进度回调实现.

    Attributes:
        websocket_manager: WebSocket 管理器.
        channel: 频道名称.
    """

    def __init__(self, websocket_manager: Any = None, channel: str = "poc_progress") -> None:
        self.websocket_manager = websocket_manager
        self.channel = channel

    async def on_progress(self, progress: ExecutionProgress) -> None:
        """进度更新回调.

        Args:
            progress: 执行进度信息.
        """
        if self.websocket_manager:
            await self.websocket_manager.broadcast(
                self.channel,
                {
                    "type": "progress",
                    "data": progress.to_dict(),
                },
            )

    async def on_complete(self, result: POCVerificationResult) -> None:
        """完成回调.

        Args:
            result: 验证结果.
        """
        if self.websocket_manager:
            await self.websocket_manager.broadcast(
                self.channel,
                {
                    "type": "complete",
                    "data": result.to_dict() if hasattr(result, "to_dict") else str(result),
                },
            )

    async def on_error(self, error: Exception, task_id: str) -> None:
        """错误回调.

        Args:
            error: 异常对象.
            task_id: 任务 ID.
        """
        if self.websocket_manager:
            await self.websocket_manager.broadcast(
                self.channel,
                {
                    "type": "error",
                    "data": {
                        "task_id": task_id,
                        "error": str(error),
                        "error_type": type(error).__name__,
                    },
                },
            )


class ExecutionResultCache:
    """执行结果缓存.

    Attributes:
        _cache: 缓存字典.
        _max_size: 最大大小.
        _default_ttl: 默认 TTL.
        _lock: 异步锁.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600) -> None:
        self._cache: Dict[str, Tuple[Any, float, float]] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()

    def _generate_key(self, poc_id: str, target: str, poc_code: str) -> str:
        """生成缓存键.

        Args:
            poc_id: POC ID.
            target: 目标地址.
            poc_code: POC 代码.

        Returns:
            str: 缓存键.
        """
        content = f"{poc_id}:{target}:{poc_code}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def get(self, poc_id: str, target: str, poc_code: str) -> Optional[POCResult]:
        """获取缓存结果.

        Args:
            poc_id: POC ID.
            target: 目标地址.
            poc_code: POC 代码.

        Returns:
            Optional[POCResult]: 缓存结果.
        """
        key = self._generate_key(poc_id, target, poc_code)
        async with self._lock:
            if key in self._cache:
                result, created_at, ttl = self._cache[key]
                if time.time() - created_at < ttl:
                    return result
                else:
                    del self._cache[key]
        return None

    async def set(
        self,
        poc_id: str,
        target: str,
        poc_code: str,
        result: POCResult,
        ttl: Optional[int] = None,
    ) -> None:
        """设置缓存结果.

        Args:
            poc_id: POC ID.
            target: 目标地址.
            poc_code: POC 代码.
            result: 执行结果.
            ttl: TTL.
        """
        key = self._generate_key(poc_id, target, poc_code)
        async with self._lock:
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]

            self._cache[key] = (result, time.time(), ttl or self._default_ttl)

    async def clear(self) -> None:
        """清除缓存."""
        async with self._lock:
            self._cache.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计.

        Returns:
            Dict[str, Any]: 缓存统计信息.
        """
        async with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "default_ttl": self._default_ttl,
            }


class ResourceMonitor:
    """资源监控器.

    Attributes:
        limits: 资源限制.
        _monitoring: 是否正在监控.
        _monitor_task: 监控任务.
        _usage_history: 使用历史.
        _callbacks: 回调列表.
    """

    def __init__(self, limits: ResourceLimits) -> None:
        self.limits = limits
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._usage_history: deque = deque(maxlen=100)
        self._callbacks: List[Callable[[ResourceUsage, ResourceThrottleAction], Awaitable[None]]] = []

    def add_callback(
        self, callback: Callable[[ResourceUsage, ResourceThrottleAction], Awaitable[None]]
    ) -> None:
        """添加回调.

        Args:
            callback: 回调函数.
        """
        self._callbacks.append(callback)

    def remove_callback(
        self, callback: Callable[[ResourceUsage, ResourceThrottleAction], Awaitable[None]]
    ) -> None:
        """移除回调.

        Args:
            callback: 回调函数.
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_current_usage(self) -> ResourceUsage:
        """获取当前资源使用情况.

        Returns:
            ResourceUsage: 资源使用情况.
        """
        process = psutil.Process()
        memory_info = process.memory_info()

        usage = ResourceUsage(
            memory_mb=memory_info.rss / (1024 * 1024),
            memory_percent=process.memory_percent(),
            cpu_percent=process.cpu_percent(interval=0.1),
            timestamp=datetime.now(),
        )

        self._usage_history.append(usage)
        return usage

    def get_average_usage(self, seconds: int = 60) -> ResourceUsage:
        """获取平均资源使用情况.

        Args:
            seconds: 时间范围(秒).

        Returns:
            ResourceUsage: 平均资源使用情况.
        """
        cutoff = datetime.now() - timedelta(seconds=seconds)
        recent = [u for u in self._usage_history if u.timestamp >= cutoff]

        if not recent:
            return self.get_current_usage()

        return ResourceUsage(
            memory_mb=sum(u.memory_mb for u in recent) / len(recent),
            memory_percent=sum(u.memory_percent for u in recent) / len(recent),
            cpu_percent=sum(u.cpu_percent for u in recent) / len(recent),
            timestamp=datetime.now(),
        )

    def check_throttle_action(self, usage: ResourceUsage) -> ResourceThrottleAction:
        """检查节流动作.

        Args:
            usage: 资源使用情况.

        Returns:
            ResourceThrottleAction: 节流动作.
        """
        memory_ratio = usage.memory_mb / self.limits.max_memory_mb
        cpu_ratio = usage.cpu_percent / 100.0

        if memory_ratio >= self.limits.pause_threshold_memory or cpu_ratio >= self.limits.pause_threshold_cpu:
            return ResourceThrottleAction.PAUSE
        elif (
            memory_ratio >= self.limits.throttle_threshold_memory
            or cpu_ratio >= self.limits.throttle_threshold_cpu
        ):
            return ResourceThrottleAction.THROTTLE
        elif (
            memory_ratio >= self.limits.throttle_threshold_memory * 0.9
            or cpu_ratio >= self.limits.throttle_threshold_cpu * 0.9
        ):
            return ResourceThrottleAction.WARNING

        return ResourceThrottleAction.NONE

    async def start_monitoring(self, interval: float = 1.0) -> None:
        """开始监控.

        Args:
            interval: 监控间隔(秒).
        """
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))

    async def stop_monitoring(self) -> None:
        """停止监控."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def _monitor_loop(self, interval: float) -> None:
        """监控循环.

        Args:
            interval: 监控间隔(秒).
        """
        while self._monitoring:
            try:
                usage = self.get_current_usage()
                action = self.check_throttle_action(usage)

                if action != ResourceThrottleAction.NONE:
                    for callback in self._callbacks:
                        try:
                            await callback(usage, action)
                        except Exception as e:
                            logger.error(f"资源监控回调执行失败: {str(e)}")

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"资源监控循环异常: {str(e)}")
                await asyncio.sleep(interval)


class ExecutionQueue:
    """执行队列管理器.

    Attributes:
        _queue: 任务队列.
        _sequence: 序列号.
        _max_concurrent: 最大并发数.
        _running_count: 运行中数量.
        _lock: 异步锁.
        _not_empty: 非空事件.
        _paused: 是否暂停.
    """

    def __init__(self, max_concurrent: int = 10) -> None:
        self._queue: List[PrioritizedTask] = []
        self._sequence = 0
        self._max_concurrent = max_concurrent
        self._running_count = 0
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Event()
        self._paused = False

    async def enqueue(
        self,
        task_data: Any,
        config: ExecutionConfig,
        callback: Optional[Callable] = None,
    ) -> str:
        """入队.

        Args:
            task_data: 任务数据.
            config: 执行配置.
            callback: 回调函数.

        Returns:
            str: 任务 ID.
        """
        async with self._lock:
            self._sequence += 1
            prioritized = PrioritizedTask(
                priority=-config.priority.value,
                sequence=self._sequence,
                task_data=task_data,
                config=config,
                callback=callback,
            )
            heapq.heappush(self._queue, prioritized)
            self._not_empty.set()

            task_id = f"{config.poc_id}_{self._sequence}"
            logger.debug(f"任务已入队: {task_id}, 优先级: {config.priority.name}")
            return task_id

    async def dequeue(self) -> Optional[PrioritizedTask]:
        """出队.

        Returns:
            Optional[PrioritizedTask]: 任务.
        """
        while True:
            async with self._lock:
                if self._paused:
                    pass
                elif self._running_count >= self._max_concurrent:
                    pass
                elif self._queue:
                    task = heapq.heappop(self._queue)
                    self._running_count += 1
                    if not self._queue:
                        self._not_empty.clear()
                    return task

            await asyncio.sleep(0.1)

    async def task_completed(self) -> None:
        """任务完成."""
        async with self._lock:
            self._running_count = max(0, self._running_count - 1)

    async def pause(self) -> None:
        """暂停队列."""
        async with self._lock:
            self._paused = True
        logger.info("执行队列已暂停")

    async def resume(self) -> None:
        """恢复队列."""
        async with self._lock:
            self._paused = False
        logger.info("执行队列已恢复")

    async def clear(self) -> int:
        """清空队列.

        Returns:
            int: 清空的任务数.
        """
        async with self._lock:
            count = len(self._queue)
            self._queue.clear()
            self._not_empty.clear()
            return count

    async def get_queue_size(self) -> int:
        """获取队列大小.

        Returns:
            int: 队列大小.
        """
        async with self._lock:
            return len(self._queue)

    async def get_running_count(self) -> int:
        """获取运行中数量.

        Returns:
            int: 运行中数量.
        """
        async with self._lock:
            return self._running_count

    async def set_max_concurrent(self, max_concurrent: int) -> None:
        """设置最大并发数.

        Args:
            max_concurrent: 最大并发数.
        """
        async with self._lock:
            self._max_concurrent = max_concurrent

    def get_status(self) -> Dict[str, Any]:
        """获取队列状态.

        Returns:
            Dict[str, Any]: 队列状态.
        """
        return {
            "queue_size": len(self._queue),
            "running_count": self._running_count,
            "max_concurrent": self._max_concurrent,
            "paused": self._paused,
        }


class VerificationEngine:
    """POC 验证执行引擎类.

    负责管理 POC 验证任务的执行,包括:
    - 多线程并发执行
    - 资源限制管理
    - 超时控制
    - 错误重试机制
    - 执行进度监控
    - 实时日志捕获
    - 优先级队列调度
    - 结果缓存

    Attributes:
        pocsuite3_agent: Pocsuite3 代理.
        active_executions: 活跃执行字典.
        execution_semaphore: 执行信号量.
    """

    def __init__(
        self,
        max_concurrent: Optional[int] = None,
        resource_limits: Optional[ResourceLimits] = None,
    ) -> None:
        self.pocsuite3_agent = Pocsuite3Agent()

        self._max_concurrent = max_concurrent or settings.POC_MAX_CONCURRENT_EXECUTIONS
        self._resource_limits = resource_limits or ResourceLimits(
            max_concurrent_executions=self._max_concurrent
        )

        self.active_executions: Dict[str, asyncio.Task] = {}
        self.execution_semaphore = asyncio.Semaphore(self._max_concurrent)

        self._execution_queue = ExecutionQueue(self._max_concurrent)
        self._resource_monitor = ResourceMonitor(self._resource_limits)
        self._result_cache = ExecutionResultCache()

        self._execution_history: deque = deque(maxlen=1000)
        self._progress_callbacks: List[ProgressCallback] = []
        self._stats = ExecutionStats()
        self._task_progress: Dict[str, ExecutionProgress] = {}

        self._shutdown = False
        self._queue_processor_task: Optional[asyncio.Task] = None

        self._resource_monitor.add_callback(self._handle_resource_throttle)

        logger.info("✅ POC 验证执行引擎初始化完成")

    async def start(self) -> None:
        """启动引擎."""
        await self._resource_monitor.start_monitoring()
        self._queue_processor_task = asyncio.create_task(self._process_queue())
        logger.info("🚀 POC 验证执行引擎已启动")

    async def shutdown(self) -> None:
        """关闭引擎."""
        self._shutdown = True

        if self._queue_processor_task:
            self._queue_processor_task.cancel()
            try:
                await self._queue_processor_task
            except asyncio.CancelledError:
                pass

        await self._resource_monitor.stop_monitoring()
        await self.cancel_all_executions()

        logger.info("🛑 POC 验证执行引擎已关闭")

    def add_progress_callback(self, callback: ProgressCallback) -> None:
        """添加进度回调.

        Args:
            callback: 进度回调.
        """
        self._progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: ProgressCallback) -> None:
        """移除进度回调.

        Args:
            callback: 进度回调.
        """
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)

    async def _notify_progress(self, progress: ExecutionProgress) -> None:
        """通知进度.

        Args:
            progress: 执行进度.
        """
        self._task_progress[progress.task_id] = progress
        for callback in self._progress_callbacks:
            try:
                await callback.on_progress(progress)
            except Exception as e:
                logger.error(f"进度回调执行失败: {str(e)}")

    async def _notify_complete(self, result: POCVerificationResult) -> None:
        """通知完成.

        Args:
            result: 验证结果.
        """
        for callback in self._progress_callbacks:
            try:
                await callback.on_complete(result)
            except Exception as e:
                logger.error(f"完成回调执行失败: {str(e)}")

    async def _notify_error(self, error: Exception, task_id: str) -> None:
        """通知错误.

        Args:
            error: 异常对象.
            task_id: 任务 ID.
        """
        for callback in self._progress_callbacks:
            try:
                await callback.on_error(error, task_id)
            except Exception as e:
                logger.error(f"错误回调执行失败: {str(e)}")

    async def _handle_resource_throttle(
        self, usage: ResourceUsage, action: ResourceThrottleAction
    ) -> None:
        """处理资源节流.

        Args:
            usage: 资源使用情况.
            action: 节流动作.
        """
        if action == ResourceThrottleAction.WARNING:
            logger.warning(
                f"⚠️ 资源使用接近限制: 内存 {usage.memory_mb:.1f}MB, "
                f"CPU {usage.cpu_percent:.1f}%"
            )
        elif action == ResourceThrottleAction.THROTTLE:
            logger.warning(
                f"⏳ 资源使用达到限制,开始节流: 内存 {usage.memory_mb:.1f}MB, "
                f"CPU {usage.cpu_percent:.1f}%"
            )
            await self._execution_queue.pause()
        elif action == ResourceThrottleAction.PAUSE:
            logger.error(
                f"🛑 资源使用超过限制,暂停执行: 内存 {usage.memory_mb:.1f}MB, "
                f"CPU {usage.cpu_percent:.1f}%"
            )
            await self._execution_queue.pause()

    async def _process_queue(self) -> None:
        """队列处理循环."""
        while not self._shutdown:
            try:
                task = await self._execution_queue.dequeue()
                if task is None:
                    continue

                asyncio.create_task(self._execute_queued_task(task))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"队列处理异常: {str(e)}")
                await asyncio.sleep(0.1)

    async def _execute_queued_task(self, prioritized_task: PrioritizedTask) -> None:
        """执行队列中的任务.

        Args:
            prioritized_task: 优先级任务.
        """
        try:
            result = await self.execute_verification_task(
                prioritized_task.task_data,
                progress_callback=prioritized_task.callback,
            )

            if prioritized_task.callback:
                try:
                    if asyncio.iscoroutinefunction(prioritized_task.callback):
                        await prioritized_task.callback(result)
                    else:
                        prioritized_task.callback(result)
                except Exception as e:
                    logger.error(f"任务回调执行失败: {str(e)}")

        except Exception as e:
            logger.error(f"队列任务执行失败: {str(e)}")
        finally:
            await self._execution_queue.task_completed()

    def set_max_concurrent_executions(self, max_concurrent: int) -> None:
        """设置最大并发执行数.

        Args:
            max_concurrent: 最大并发数.
        """
        self._max_concurrent = max_concurrent
        self._resource_limits.max_concurrent_executions = max_concurrent

        self.execution_semaphore = asyncio.Semaphore(max_concurrent)
        asyncio.create_task(self._execution_queue.set_max_concurrent(max_concurrent))

        logger.info(f"最大并发执行数已设置为: {max_concurrent}")

    def set_resource_limits(self, limits: ResourceLimits) -> None:
        """设置资源限制.

        Args:
            limits: 资源限制.
        """
        self._resource_limits = limits
        self._resource_monitor.limits = limits
        logger.info(f"资源限制已更新: {limits.to_dict()}")

    def get_resource_limits(self) -> ResourceLimits:
        """获取资源限制.

        Returns:
            ResourceLimits: 资源限制.
        """
        return self._resource_limits

    async def get_current_resource_usage(self) -> ResourceUsage:
        """获取当前资源使用情况.

        Returns:
            ResourceUsage: 资源使用情况.
        """
        return self._resource_monitor.get_current_usage()

    async def enqueue_verification_task(
        self,
        verification_task: POCVerificationTask,
        priority: ExecutionPriority = ExecutionPriority.NORMAL,
        callback: Optional[Callable] = None,
    ) -> str:
        """将验证任务加入队列.

        Args:
            verification_task: 验证任务.
            priority: 优先级.
            callback: 回调函数.

        Returns:
            str: 任务 ID.

        Raises:
            ValueError: POC 代码不存在.
        """
        poc_code = await poc_manager.get_poc_code(verification_task.poc_id)
        if not poc_code:
            raise ValueError(f"POC 代码不存在: {verification_task.poc_id}")

        config = ExecutionConfig(
            poc_id=verification_task.poc_id,
            target=verification_task.target,
            poc_code=poc_code,
            timeout=settings.POC_EXECUTION_TIMEOUT,
            max_retries=settings.POC_RETRY_MAX_COUNT,
            priority=priority,
        )

        task_id = await self._execution_queue.enqueue(
            verification_task,
            config,
            callback,
        )

        verification_task.status = "queued"
        await verification_task.save()

        return task_id

    async def execute_verification_task(
        self,
        verification_task: POCVerificationTask,
        progress_callback: Optional[Callable[[ExecutionProgress], Awaitable[None]]] = None,
    ) -> POCVerificationResult:
        """执行单个 POC 验证任务.

        Args:
            verification_task: POC 验证任务对象.
            progress_callback: 进度回调函数.

        Returns:
            POCVerificationResult: 验证结果.
        """
        task_id = str(verification_task.id)
        start_time = datetime.now()

        logger.info(f"[{task_id}] 🚀 开始执行 POC 验证: {verification_task.poc_name}")

        await self._notify_progress(
            ExecutionProgress(
                task_id=task_id,
                poc_name=verification_task.poc_name,
                status=ExecutionStatus.RUNNING,
                progress=0,
                message="开始执行",
                current_step="初始化",
                total_steps=5,
                completed_steps=0,
            )
        )

        try:
            verification_task.status = "running"
            verification_task.progress = 10
            await verification_task.save()

            poc_code = await poc_manager.get_poc_code(verification_task.poc_id)
            if not poc_code:
                raise ValueError(f"POC 代码不存在: {verification_task.poc_id}")

            await self._notify_progress(
                ExecutionProgress(
                    task_id=task_id,
                    poc_name=verification_task.poc_name,
                    status=ExecutionStatus.RUNNING,
                    progress=20,
                    message="获取POC代码完成",
                    current_step="执行POC",
                    total_steps=5,
                    completed_steps=1,
                )
            )

            config = ExecutionConfig(
                poc_id=verification_task.poc_id,
                target=verification_task.target,
                poc_code=poc_code,
                timeout=settings.POC_EXECUTION_TIMEOUT,
                max_retries=settings.POC_RETRY_MAX_COUNT,
                enable_sandbox=True,
            )

            poc_result, cache_hit = await self._execute_poc_with_retry_and_cache(
                config, task_id, verification_task.poc_name, progress_callback
            )

            await self._notify_progress(
                ExecutionProgress(
                    task_id=task_id,
                    poc_name=verification_task.poc_name,
                    status=ExecutionStatus.RUNNING,
                    progress=80,
                    message="POC执行完成",
                    current_step="生成报告",
                    total_steps=5,
                    completed_steps=4,
                )
            )

            result = await POCVerificationResult.create(
                verification_task=verification_task,
                poc_name=verification_task.poc_name,
                poc_id=verification_task.poc_id,
                target=verification_task.target,
                vulnerable=poc_result.vulnerable,
                message=poc_result.message,
                output=poc_result.output,
                error=poc_result.error,
                execution_time=poc_result.execution_time,
                confidence=self._calculate_confidence(poc_result),
                severity=self._calculate_severity(poc_result),
                cvss_score=self._calculate_cvss_score(poc_result),
            )

            verification_task.status = "completed"
            verification_task.progress = 100
            await verification_task.save()

            await self._log_execution_details(result, poc_result)

            execution_time = (datetime.now() - start_time).total_seconds()

            self._add_history_entry(
                ExecutionHistoryEntry(
                    task_id=task_id,
                    poc_id=verification_task.poc_id,
                    poc_name=verification_task.poc_name,
                    target=verification_task.target,
                    status=ExecutionStatus.COMPLETED,
                    start_time=start_time,
                    end_time=datetime.now(),
                    execution_time=execution_time,
                    vulnerable=poc_result.vulnerable,
                    cache_hit=cache_hit,
                )
            )

            self._update_stats(poc_result.vulnerable, False, False, execution_time, cache_hit)

            await self._notify_progress(
                ExecutionProgress(
                    task_id=task_id,
                    poc_name=verification_task.poc_name,
                    status=ExecutionStatus.COMPLETED,
                    progress=100,
                    message="验证完成",
                    current_step="完成",
                    total_steps=5,
                    completed_steps=5,
                    elapsed_time=execution_time,
                    resource_usage=await self.get_current_resource_usage(),
                )
            )

            await self._notify_complete(result)

            logger.info(
                f"[{task_id}] ✅ POC 验证完成: {verification_task.poc_name}, 耗时: {execution_time:.2f}秒"
            )

            return result

        except asyncio.CancelledError:
            logger.warning(f"[{task_id}] ⚠️ POC 验证被取消")

            verification_task.status = "cancelled"
            await verification_task.save()

            self._add_history_entry(
                ExecutionHistoryEntry(
                    task_id=task_id,
                    poc_id=verification_task.poc_id,
                    poc_name=verification_task.poc_name,
                    target=verification_task.target,
                    status=ExecutionStatus.CANCELLED,
                    start_time=start_time,
                    end_time=datetime.now(),
                )
            )

            self._update_stats(False, True, False, 0, False)

            result = await POCVerificationResult.create(
                verification_task=verification_task,
                poc_name=verification_task.poc_name,
                poc_id=verification_task.poc_id,
                target=verification_task.target,
                vulnerable=False,
                message="执行被取消",
                output="",
                error="Execution cancelled",
                execution_time=0.0,
                confidence=0.0,
                severity="info",
                cvss_score=0.0,
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"[{task_id}] ⏰ POC 验证超时")

            verification_task.status = "timeout"
            await verification_task.save()

            self._add_history_entry(
                ExecutionHistoryEntry(
                    task_id=task_id,
                    poc_id=verification_task.poc_id,
                    poc_name=verification_task.poc_name,
                    target=verification_task.target,
                    status=ExecutionStatus.TIMEOUT,
                    start_time=start_time,
                    end_time=datetime.now(),
                    error="Execution timeout",
                )
            )

            self._update_stats(False, False, True, 0, False)

            result = await POCVerificationResult.create(
                verification_task=verification_task,
                poc_name=verification_task.poc_name,
                poc_id=verification_task.poc_id,
                target=verification_task.target,
                vulnerable=False,
                message="执行超时",
                output="",
                error="Execution timeout",
                execution_time=float(settings.POC_EXECUTION_TIMEOUT),
                confidence=0.0,
                severity="info",
                cvss_score=0.0,
            )

            await self._notify_error(TimeoutError("Execution timeout"), task_id)

            return result

        except Exception as e:
            logger.error(f"[{task_id}] ❌ POC 验证失败: {str(e)}")

            verification_task.status = "failed"
            await verification_task.save()

            self._add_history_entry(
                ExecutionHistoryEntry(
                    task_id=task_id,
                    poc_id=verification_task.poc_id,
                    poc_name=verification_task.poc_name,
                    target=verification_task.target,
                    status=ExecutionStatus.FAILED,
                    start_time=start_time,
                    end_time=datetime.now(),
                    error=str(e),
                )
            )

            self._update_stats(False, False, False, 0, False)

            result = await POCVerificationResult.create(
                verification_task=verification_task,
                poc_name=verification_task.poc_name,
                poc_id=verification_task.poc_id,
                target=verification_task.target,
                vulnerable=False,
                message=f"执行失败: {str(e)}",
                output="",
                error=str(e),
                execution_time=0.0,
                confidence=0.0,
                severity="info",
                cvss_score=0.0,
            )

            await self._log_execution_details(result, None, e)
            await self._notify_error(e, task_id)

            return result

    async def execute_batch_verification(
        self,
        verification_tasks: List[POCVerificationTask],
        max_concurrent: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, str], Awaitable[None]]] = None,
    ) -> List[POCVerificationResult]:
        """批量执行 POC 验证任务.

        Args:
            verification_tasks: POC 验证任务列表.
            max_concurrent: 最大并发数,None 则使用配置值.
            progress_callback: 进度回调函数 (completed, total, message).

        Returns:
            List[POCVerificationResult]: 验证结果列表.
        """
        logger.info(f"🚀 开始批量 POC 验证,任务数: {len(verification_tasks)}")

        concurrent_limit = max_concurrent or self._max_concurrent
        semaphore = asyncio.Semaphore(concurrent_limit)

        results: List[POCVerificationResult] = []
        completed = 0
        total = len(verification_tasks)

        async def execute_single_task(task: POCVerificationTask) -> POCVerificationResult:
            nonlocal completed

            async with semaphore:
                result = await self.execute_verification_task(task)
                completed += 1

                if progress_callback:
                    try:
                        if asyncio.iscoroutinefunction(progress_callback):
                            await progress_callback(completed, total, f"完成 {task.poc_name}")
                        else:
                            progress_callback(completed, total, f"完成 {task.poc_name}")
                    except Exception as e:
                        logger.error(f"批量进度回调执行失败: {str(e)}")

                return result

        tasks = [execute_single_task(task) for task in verification_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 任务 {verification_tasks[i].poc_name} 执行异常: {str(result)}")
            else:
                final_results.append(result)

        logger.info(f"✅ 批量 POC 验证完成,成功: {len(final_results)}/{total}")

        return final_results

    async def _execute_poc_with_retry_and_cache(
        self,
        config: ExecutionConfig,
        task_id: str,
        poc_name: str,
        progress_callback: Optional[Callable] = None,
    ) -> Tuple[POCResult, bool]:
        """带重试机制和缓存的 POC 执行.

        Args:
            config: 执行配置.
            task_id: 任务 ID.
            poc_name: POC 名称.
            progress_callback: 进度回调.

        Returns:
            Tuple[POCResult, bool]: (执行结果, 是否缓存命中).
        """
        if config.enable_cache:
            cached_result = await self._result_cache.get(config.poc_id, config.target, config.poc_code)
            if cached_result:
                logger.info(f"[{config.poc_id}] 📦 使用缓存结果")
                self._stats.cache_hit_count += 1
                return cached_result, True

        result = await self._execute_poc_with_retry(config, task_id, poc_name, progress_callback)

        if config.enable_cache and result.vulnerable:
            await self._result_cache.set(
                config.poc_id, config.target, config.poc_code, result, config.cache_ttl
            )

        return result, False

    async def _execute_poc_with_retry(
        self,
        config: ExecutionConfig,
        task_id: str = "",
        poc_name: str = "",
        progress_callback: Optional[Callable] = None,
    ) -> POCResult:
        """带重试机制的 POC 执行.

        Args:
            config: 执行配置.
            task_id: 任务 ID.
            poc_name: POC 名称.
            progress_callback: 进度回调.

        Returns:
            POCResult: POC 执行结果.
        """
        last_error: Optional[Exception] = None
        retry_count = 0

        for attempt in range(config.max_retries):
            retry_count = attempt
            logger.info(f"[{config.poc_id}] 🔄 尝试执行 POC (第 {attempt + 1} 次)")

            await self._notify_progress(
                ExecutionProgress(
                    task_id=task_id,
                    poc_name=poc_name,
                    status=ExecutionStatus.RUNNING,
                    progress=30 + attempt * 10,
                    message=f"执行尝试 {attempt + 1}/{config.max_retries}",
                    current_step=f"执行POC (尝试 {attempt + 1})",
                    total_steps=5,
                    completed_steps=2,
                )
            )

            try:
                try:
                    result = await asyncio.wait_for(
                        self.pocsuite3_agent.execute_custom_poc(
                            poc_code=config.poc_code, target=config.target
                        ),
                        timeout=config.timeout,
                    )
                except asyncio.TimeoutError:
                    raise TimeoutError(f"POC 执行超时 ({config.timeout}秒)")

                if result.vulnerable:
                    logger.info(f"[{config.poc_id}] ✅ POC 验证成功: {result.message}")
                    self._stats.retry_count += retry_count
                    return result
                else:
                    logger.warning(f"[{config.poc_id}] ⚠️ POC 验证未发现漏洞: {result.message}")

                    if attempt < config.max_retries - 1:
                        delay = min(config.retry_delay_base**attempt, config.retry_delay_max)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        self._stats.retry_count += retry_count
                        return result

            except asyncio.CancelledError:
                raise

            except Exception as e:
                last_error = e
                logger.error(f"[{config.poc_id}] ❌ POC 执行异常 (第 {attempt + 1} 次): {str(e)}")

                if attempt < config.max_retries - 1:
                    delay = min(config.retry_delay_base**attempt, config.retry_delay_max)
                    await asyncio.sleep(delay)
                    continue
                else:
                    self._stats.retry_count += retry_count
                    return POCResult(
                        poc_name=config.poc_id,
                        target=config.target,
                        vulnerable=False,
                        message=f"执行失败: {str(e)}",
                        output="",
                        error=str(e),
                        execution_time=0.0,
                    )

        self._stats.retry_count += retry_count
        return POCResult(
            poc_name=config.poc_id,
            target=config.target,
            vulnerable=False,
            message="超过最大重试次数",
            output="",
            error=last_error.__class__.__name__ if last_error else "Max retries exceeded",
            execution_time=0.0,
        )

    async def cancel_execution(self, task_id: str) -> bool:
        """取消正在执行的验证任务.

        Args:
            task_id: 任务 ID.

        Returns:
            bool: 是否取消成功.
        """
        try:
            if task_id in self.active_executions:
                execution_task = self.active_executions[task_id]
                execution_task.cancel()

                try:
                    await execution_task
                except asyncio.CancelledError:
                    pass

                del self.active_executions[task_id]
                logger.info(f"✅ 执行已取消: {task_id}")
                return True

            task = await POCVerificationTask.get_or_none(id=task_id)
            if task and task.status in ["running", "queued", "pending"]:
                task.status = "cancelled"
                await task.save()
                logger.info(f"✅ 任务已标记为取消: {task_id}")
                return True

            logger.warning(f"⚠️ 未找到正在执行的任务: {task_id}")
            return False

        except Exception as e:
            logger.error(f"❌ 取消执行失败: {str(e)}")
            return False

    async def cancel_all_executions(self) -> int:
        """取消所有正在执行的验证任务.

        Returns:
            int: 取消的任务数量.
        """
        cancelled_count = 0
        task_ids = list(self.active_executions.keys())

        for task_id in task_ids:
            if await self.cancel_execution(task_id):
                cancelled_count += 1

        await self._execution_queue.clear()

        running_tasks = await POCVerificationTask.filter(status="running")
        for task in running_tasks:
            task.status = "cancelled"
            await task.save()
            cancelled_count += 1

        logger.info(f"✅ 已取消 {cancelled_count} 个执行任务")
        return cancelled_count

    async def pause_verification_task(self, task_id: str) -> bool:
        """暂停 POC 验证任务.

        Args:
            task_id: 任务 ID.

        Returns:
            bool: 是否暂停成功.
        """
        try:
            task = await POCVerificationTask.get_or_none(id=task_id)
            if not task:
                logger.warning(f"⚠️ 任务不存在: {task_id}")
                return False

            if task.status != "running":
                logger.warning(f"⚠️ 任务状态不允许暂停: {task.status}")
                return False

            task.status = "paused"
            await task.save()

            if task.id in self.active_executions:
                execution_task = self.active_executions[task.id]
                execution_task.cancel()
                del self.active_executions[task.id]

            logger.info(f"✅ 任务已暂停: {task_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 暂停任务失败: {str(e)}")
            return False

    async def resume_verification_task(self, task_id: str) -> bool:
        """继续 POC 验证任务.

        Args:
            task_id: 任务 ID.

        Returns:
            bool: 是否继续成功.
        """
        try:
            task = await POCVerificationTask.get_or_none(id=task_id)
            if not task:
                logger.warning(f"⚠️ 任务不存在: {task_id}")
                return False

            if task.status != "paused":
                logger.warning(f"⚠️ 任务状态不允许继续: {task.status}")
                return False

            task.status = "running"
            await task.save()

            logger.info(f"✅ 任务已继续: {task_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 继续任务失败: {str(e)}")
            return False

    async def cancel_verification_task(self, task_id: str) -> bool:
        """取消 POC 验证任务.

        Args:
            task_id: 任务 ID.

        Returns:
            bool: 是否取消成功.
        """
        return await self.cancel_execution(task_id)

    def get_execution_status(self, task_id: str) -> Optional[ExecutionProgress]:
        """获取执行状态.

        Args:
            task_id: 任务 ID.

        Returns:
            Optional[ExecutionProgress]: 执行进度信息.
        """
        return self._task_progress.get(task_id)

    async def get_execution_progress(self, task_id: str) -> Dict[str, Any]:
        """获取执行进度.

        Args:
            task_id: 任务 ID.

        Returns:
            Dict[str, Any]: 包含进度信息的字典.
        """
        try:
            task = await POCVerificationTask.get_or_none(id=task_id)
            if not task:
                return {"error": "Task not found"}

            results = await POCVerificationResult.filter(verification_task=task_id).order_by(
                "-created_at"
            )

            cached_progress = self._task_progress.get(task_id)

            return {
                "task_id": task_id,
                "poc_name": task.poc_name,
                "status": task.status,
                "progress": task.progress,
                "total_results": len(results),
                "vulnerable_count": sum(1 for r in results if r.vulnerable),
                "failed_count": sum(1 for r in results if not r.vulnerable and r.error),
                "latest_result": results[0].to_dict() if results else None,
                "current_progress": cached_progress.to_dict() if cached_progress else None,
            }

        except Exception as e:
            logger.error(f"❌ 获取执行进度失败: {str(e)}")
            return {"error": str(e)}

    def get_execution_statistics(self) -> ExecutionStats:
        """获取执行统计.

        Returns:
            ExecutionStats: 执行统计信息.
        """
        if self._stats.executed_count > 0:
            self._stats.average_execution_time = (
                self._stats.total_execution_time / self._stats.executed_count
            )
            self._stats.success_rate = (
                (self._stats.executed_count - self._stats.failed_count - self._stats.cancelled_count)
                / self._stats.executed_count
                * 100
            )

        return self._stats

    def get_execution_history(
        self,
        limit: int = 100,
        status: Optional[ExecutionStatus] = None,
        poc_id: Optional[str] = None,
    ) -> List[ExecutionHistoryEntry]:
        """获取执行历史.

        Args:
            limit: 返回条数限制.
            status: 按状态过滤.
            poc_id: 按 POC ID 过滤.

        Returns:
            List[ExecutionHistoryEntry]: 执行历史列表.
        """
        history = list(self._execution_history)

        if status:
            history = [h for h in history if h.status == status]

        if poc_id:
            history = [h for h in history if h.poc_id == poc_id]

        return history[:limit]

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态.

        Returns:
            Dict[str, Any]: 队列状态信息.
        """
        return self._execution_queue.get_status()

    async def clear_cache(self) -> None:
        """清除结果缓存."""
        await self._result_cache.clear()
        logger.info("✅ 结果缓存已清除")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计.

        Returns:
            Dict[str, Any]: 缓存统计信息.
        """
        return await self._result_cache.get_stats()

    def _add_history_entry(self, entry: ExecutionHistoryEntry) -> None:
        """添加历史条目.

        Args:
            entry: 历史条目.
        """
        self._execution_history.append(entry)

    def _update_stats(
        self,
        vulnerable: bool,
        cancelled: bool,
        timeout: bool,
        execution_time: float,
        cache_hit: bool,
    ) -> None:
        """更新统计信息.

        Args:
            vulnerable: 是否存在漏洞.
            cancelled: 是否取消.
            timeout: 是否超时.
            execution_time: 执行时间.
            cache_hit: 是否缓存命中.
        """
        self._stats.executed_count += 1
        self._stats.total_execution_time += execution_time

        if vulnerable:
            self._stats.vulnerable_count += 1
        elif cancelled:
            self._stats.cancelled_count += 1
        elif timeout:
            self._stats.timeout_count += 1
        else:
            self._stats.failed_count += 1

        if cache_hit:
            self._stats.cache_hit_count += 1

    def _calculate_confidence(self, poc_result: POCResult) -> float:
        """计算结果置信度.

        Args:
            poc_result: POC 执行结果.

        Returns:
            float: 置信度(0-1).
        """
        confidence = 0.5

        if poc_result.vulnerable:
            confidence = 0.9
        elif poc_result.error:
            confidence = 0.1
        else:
            confidence = 0.5

        if poc_result.output and len(poc_result.output) > 100:
            confidence += 0.1

        return min(confidence, 1.0)

    def _calculate_severity(self, poc_result: POCResult) -> str:
        """计算漏洞严重度.

        Args:
            poc_result: POC 执行结果.

        Returns:
            str: 严重度(critical, high, medium, low, info).
        """
        if poc_result.vulnerable:
            return "high"
        elif poc_result.error:
            return "info"
        else:
            return "low"

    def _calculate_cvss_score(self, poc_result: POCResult) -> float:
        """计算 CVSS 评分.

        Args:
            poc_result: POC 执行结果.

        Returns:
            float: CVSS 评分(0-10).
        """
        if poc_result.vulnerable:
            return 7.5
        elif poc_result.error:
            return 0.0
        else:
            return 3.5

    async def _log_execution_details(
        self,
        result: POCVerificationResult,
        poc_result: Optional[POCResult] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """记录执行详情日志.

        Args:
            result: 验证结果对象.
            poc_result: POC 执行结果.
            error: 异常对象.
        """
        try:
            await POCExecutionLog.create(
                verification_result=result,
                log_level="info",
                message=f"开始执行 POC: {result.poc_name}",
                details={
                    "poc_id": result.poc_id,
                    "target": result.target,
                    "config": {
                        "timeout": settings.POC_EXECUTION_TIMEOUT,
                        "max_retries": settings.POC_RETRY_MAX_COUNT,
                    },
                },
            )

            if poc_result:
                await POCExecutionLog.create(
                    verification_result=result,
                    log_level="info",
                    message=f"POC 执行完成: {poc_result.message}",
                    details={
                        "vulnerable": poc_result.vulnerable,
                        "execution_time": poc_result.execution_time,
                        "output_length": len(poc_result.output) if poc_result.output else 0,
                    },
                )

            if error:
                await POCExecutionLog.create(
                    verification_result=result,
                    log_level="error",
                    message=f"POC 执行异常: {str(error)}",
                    details={
                        "exception_type": type(error).__name__,
                        "exception_message": str(error),
                    },
                )

        except Exception as e:
            logger.error(f"❌ 记录执行日志失败: {str(e)}")

    async def get_engine_statistics(self) -> Dict[str, Any]:
        """获取引擎统计信息.

        Returns:
            Dict[str, Any]: 包含引擎统计信息的字典.
        """
        try:
            total_tasks = await POCVerificationTask.all().count()
            running_tasks = await POCVerificationTask.filter(status="running").count()
            completed_tasks = await POCVerificationTask.filter(status="completed").count()
            failed_tasks = await POCVerificationTask.filter(status="failed").count()

            total_results = await POCVerificationResult.all().count()
            vulnerable_results = await POCVerificationResult.filter(vulnerable=True).count()

            resource_usage = await self.get_current_resource_usage()
            cache_stats = await self.get_cache_stats()
            queue_status = self.get_queue_status()
            execution_stats = self.get_execution_statistics()

            return {
                "tasks": {
                    "total": total_tasks,
                    "running": running_tasks,
                    "completed": completed_tasks,
                    "failed": failed_tasks,
                },
                "results": {
                    "total": total_results,
                    "vulnerable": vulnerable_results,
                    "success_rate": (vulnerable_results / total_results * 100) if total_results > 0 else 0,
                },
                "execution": execution_stats.to_dict(),
                "queue": queue_status,
                "cache": cache_stats,
                "resources": resource_usage.to_dict(),
                "resource_limits": self._resource_limits.to_dict(),
                "active_executions": len(self.active_executions),
                "registered_pocs": len(poc_manager.get_all_pocs()),
                "cached_pocs": len(poc_manager.poc_cache),
            }

        except Exception as e:
            logger.error(f"❌ 获取引擎统计失败: {str(e)}")
            return {"error": str(e)}


verification_engine = VerificationEngine()

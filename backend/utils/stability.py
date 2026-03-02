"""
稳定性机制模块

提供重试、超时控制、熔断器等稳定性机制，确保后端服务的可靠性。
"""
import asyncio
import logging
import time
from typing import Callable, Any, Optional, TypeVar, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitStats:
    """熔断器统计信息"""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state: CircuitState = CircuitState.OPEN
    last_state_change: Optional[datetime] = None


class CircuitBreaker:
    """
    熔断器
    
    实现熔断模式，防止级联故障。
    当失败率达到阈值时，熔断器会"断开"，阻止后续请求。
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_requests: int = 3,
        name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests
        self.name = name
        self.stats = CircuitStats()
        self._half_open_success_count = 0
        logger.info(f"熔断器 '{name}' 初始化: 失败阈值={failure_threshold}, 恢复超时={recovery_timeout}s")
    
    def can_execute(self) -> bool:
        """检查是否可以执行"""
        if self.stats.state == CircuitState.OPEN:
            return True
        
        if self.stats.state == CircuitState.HALF_OPEN:
            return True
        
        if self.stats.state == CircuitState.CLOSED:
            if self.stats.last_failure_time:
                elapsed = (datetime.now() - self.stats.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return True
            return False
        
        return False
    
    def record_success(self):
        """记录成功"""
        self.stats.success_count += 1
        self.stats.last_success_time = datetime.now()
        
        if self.stats.state == CircuitState.HALF_OPEN:
            self._half_open_success_count += 1
            if self._half_open_success_count >= self.half_open_requests:
                self._transition_to(CircuitState.OPEN)
                self._half_open_success_count = 0
        elif self.stats.state == CircuitState.OPEN:
            self.stats.failure_count = max(0, self.stats.failure_count - 1)
    
    def record_failure(self):
        """记录失败"""
        self.stats.failure_count += 1
        self.stats.last_failure_time = datetime.now()
        
        if self.stats.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.CLOSED)
        elif self.stats.state == CircuitState.OPEN:
            if self.stats.failure_count >= self.failure_threshold:
                self._transition_to(CircuitState.CLOSED)
    
    def _transition_to(self, new_state: CircuitState):
        """状态转换"""
        old_state = self.stats.state
        self.stats.state = new_state
        self.stats.last_state_change = datetime.now()
        logger.warning(f"熔断器 '{self.name}' 状态变更: {old_state.value} -> {new_state.value}")
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
        }


class RetryPolicy:
    """
    重试策略
    
    支持指数退避、固定间隔、随机间隔等重试策略。
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            delay = delay * (0 + random.random() * 0.1)
        
        return delay
    
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """判断是否应该重试"""
        if attempt >= self.max_retries:
            return False
        
        retryable_exceptions = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )
        
        return isinstance(exception, retryable_exceptions)


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError, asyncio.TimeoutError)
):
    """
    重试装饰器
    
    为函数添加自动重试功能。
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            policy = RetryPolicy(max_retries=max_retries, base_delay=base_delay)
            last_exception = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = policy.get_delay(attempt)
                        logger.warning(f"函数 {func.__name__} 执行失败 (尝试 {attempt}/{max_retries}), {delay:.2f}秒后重试: {str(e)}")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"函数 {func.__name__} 执行失败,已达到最大重试次数: {str(e)}")
                        raise
                except Exception as e:
                    logger.error(f"函数 {func.__name__} 执行失败,不可重试的异常: {str(e)}")
                    raise
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            policy = RetryPolicy(max_retries=max_retries, base_delay=base_delay)
            last_exception = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = policy.get_delay(attempt)
                        logger.warning(f"函数 {func.__name__} 执行失败 (尝试 {attempt}/{max_retries}), {delay:.2f}秒后重试: {str(e)}")
                        time.sleep(delay)
                    else:
                        logger.error(f"函数 {func.__name__} 执行失败,已达到最大重试次数: {str(e)}")
                        raise
                except Exception as e:
                    logger.error(f"函数 {func.__name__} 执行失败,不可重试的异常: {str(e)}")
                    raise
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def with_timeout(
    timeout: float = 30.0,
    timeout_message: str = "操作超时"
):
    """
    超时装饰器
    
    为异步函数添加超时控制。
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"函数 {func.__name__} 执行超时 ({timeout}秒)")
                raise TimeoutError(timeout_message)
        
        return wrapper
    
    return decorator


def with_circuit_breaker(
    breaker: CircuitBreaker,
    fallback: Optional[Callable] = None
):
    """
    熔断器装饰器
    
    为函数添加熔断保护。
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            if not breaker.can_execute():
                if fallback:
                    logger.warning(f"熔断器 '{breaker.name}' 处于断开状态,使用降级函数")
                    return await fallback(*args, **kwargs)
                raise Exception(f"熔断器 '{breaker.name}' 处于断开状态,拒绝执行")
            
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            if not breaker.can_execute():
                if fallback:
                    logger.warning(f"熔断器 '{breaker.name}' 处于断开状态,使用降级函数")
                    return fallback(*args, **kwargs)
                raise Exception(f"熔断器 '{breaker.name}' 处于断开状态,拒绝执行")
            
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class StabilityManager:
    """
    稳定性管理器
    
    统一管理重试、超时、熔断等稳定性机制。
    """
    
    _instance = None
    _breakers: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._breakers = {}
            self._initialized = True
            logger.info("稳定性管理器初始化完成")
    
    def get_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ) -> CircuitBreaker:
        """获取或创建熔断器"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout
            )
        return self._breakers[name]
    
    def get_all_stats(self) -> dict:
        """获取所有熔断器统计信息"""
        return {
            name: breaker.get_stats()
            for name, breaker in self._breakers.items()
        }
    
    def reset_all(self):
        """重置所有熔断器"""
        for breaker in self._breakers.values():
            breaker._transition_to(CircuitState.OPEN)
            breaker.stats.failure_count = 0
            breaker.stats.success_count = 0
        logger.info("所有熔断器已重置")


stability_manager = StabilityManager()

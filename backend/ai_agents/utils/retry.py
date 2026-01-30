"""
重试策略

实现多种重试策略,包括指数退避、固定间隔等。
"""
import asyncio
import logging

from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class RetryStrategy:
    """
    重试策略基类
    
    定义重试策略的接口。
    """
    
    async def execute(
        self,
        func: Callable,
        max_retries: int = 3,
        *args,
        **kwargs
    ) -> Any:
        """
        执行函数并应用重试策略
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数执行结果
            
        Raises:
            Exception: 所有重试失败后抛出最后一个异常
        """
        raise NotImplementedError("子类必须实现execute方法")


class ExponentialBackoffRetry(RetryStrategy):
    """
    指数退避重试策略
    
    每次重试的等待时间按指数增长,避免频繁重试。
    """
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        初始化指数退避重试策略
        
        Args:
            base_delay: 基础延迟时间(秒)
            max_delay: 最大延迟时间(秒)
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        logger.debug(f"指数退避重试策略初始化: base={base_delay}s, max={max_delay}s")
    
    async def execute(
        self,
        func: Callable,
        max_retries: int = 3,
        *args,
        **kwargs
    ) -> Any:
        """
        执行函数并应用指数退避重试
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数执行结果
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    delay = min(
                        self.base_delay * (2 ** attempt),
                        self.max_delay
                    )
                    logger.warning(
                        f"重试 {attempt + 1}/{max_retries}, "
                        f"等待 {delay:.1f}s 后重试... 错误: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"达到最大重试次数 {max_retries}, "
                        f"最后错误: {str(e)}"
                    )
        
        raise last_exception


class FixedIntervalRetry(RetryStrategy):
    """
    固定间隔重试策略
    
    每次重试的等待时间固定。
    """
    
    def __init__(self, delay: float = 2.0):
        """
        初始化固定间隔重试策略
        
        Args:
            delay: 固定延迟时间(秒)
        """
        self.delay = delay
        logger.debug(f"固定间隔重试策略初始化: delay={delay}s")
    
    async def execute(
        self,
        func: Callable,
        max_retries: int = 3,
        *args,
        **kwargs
    ) -> Any:
        """
        执行函数并应用固定间隔重试
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数执行结果
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(
                        f"重试 {attempt + 1}/{max_retries}, "
                        f"等待 {self.delay}s 后重试... 错误: {str(e)}"
                    )
                    await asyncio.sleep(self.delay)
                else:
                    logger.error(
                        f"达到最大重试次数 {max_retries}, "
                        f"最后错误: {str(e)}"
                    )
        
        raise last_exception


def retry_on_failure(
    max_retries: int = 3,
    strategy: Optional[RetryStrategy] = None,
    exceptions: tuple = (Exception,)
):
    """
    重试装饰器
    
    用于简化函数的重试逻辑。
    
    Args:
        max_retries: 最大重试次数
        strategy: 重试策略,默认为指数退避
        exceptions: 要捕获的异常类型
        
    Examples:
        >>> @retry_on_failure(max_retries=3)
        ... async def my_function():
        ...     return await some_operation()
    """
    if strategy is None:
        strategy = ExponentialBackoffRetry()
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await strategy.execute(
                func, max_retries, *args, **kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            async def sync_to_async():
                return func(*args, **kwargs)
            
            try:
                loop = asyncio.get_running_loop()
                return strategy.execute(sync_to_async, max_retries)
            except RuntimeError:
                return asyncio.run(strategy.execute(
                    sync_to_async, max_retries
                ))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

"""
工具异步封装

将同步工具函数封装为异步调用,支持超时控制和错误处理。
"""
import asyncio
import logging
from typing import Callable, Any


logger = logging.getLogger(__name__)


class AsyncToolWrapper:
    """
    异步工具包装器
    
    将同步函数封装为异步调用,并提供超时控制。
    
    Attributes:
        func: 原始函数
        timeout: 超时时间(秒)
    """
    
    def __init__(self, func: Callable, timeout: int = 60):
        """
        初始化工具包装器
        
        Args:
            func: 要封装的函数
            timeout: 超时时间(秒)
        """
        self.func = func
        self.timeout = timeout
        self.is_async = asyncio.iscoroutinefunction(func)
        func_name = getattr(func, '__name__', str(func))
        logger.debug(f"创建工具包装器: {func_name}, 异步: {self.is_async}, 超时: {timeout}s")
    
    async def execute(self, target: str, **kwargs) -> Any:
        """
        执行工具
        
        Args:
            target: 扫描目标
            **kwargs: 工具参数
            
        Returns:
            Any: 工具执行结果
            
        Raises:
            asyncio.TimeoutError: 执行超时
            Exception: 执行失败
        """
        func_name = getattr(self.func, '__name__', str(self.func))
        try:
            if self.is_async:
                result = await asyncio.wait_for(
                    self.func(target, **kwargs),
                    timeout=self.timeout
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self.func, target, **kwargs),
                    timeout=self.timeout
                )
            return result
        except asyncio.TimeoutError:
            logger.error(f"工具 {func_name} 执行超时({self.timeout}秒)")
            raise
        except Exception as e:
            logger.error(f"工具 {func_name} 执行失败: {str(e)}")
            raise
    
    def get_timeout(self) -> int:
        """
        获取超时时间
        
        Returns:
            int: 超时时间(秒)
        """
        return self.timeout
    
    def get_func_name(self) -> str:
        """
        获取函数名称
        
        Returns:
            str: 函数名称
        """
        return self.func.__name__


def wrap_async(
    func: Callable,
    timeout: int = 60
) -> AsyncToolWrapper:
    """
    工具异步封装函数
    
    便捷函数,用于快速创建工具包装器。
    
    Args:
        func: 要封装的函数
        timeout: 超时时间(秒)
        
    Returns:
        AsyncToolWrapper: 工具包装器实例
        
    Examples:
        >>> from plugins.baseinfo.baseinfo import getbaseinfo
        >>> wrapper = wrap_async(getbaseinfo, timeout=10)
        >>> result = await wrapper.execute("https://www.baidu.com")
    """
    return AsyncToolWrapper(func, timeout=timeout)

"""
错误隔离执行器

提供工具执行沙箱、异常捕获和恢复、错误影响范围控制功能。
"""
import asyncio
import logging
import traceback
import time
from typing import Dict, Any, Optional, Callable, TypeVar, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorType(Enum):
    """错误类型枚举"""
    TEMPORARY = "temporary"
    PERMANENT = "permanent"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    NETWORK = "network"
    PERMISSION = "permission"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """恢复策略枚举"""
    RETRY = "retry"
    SKIP = "skip"
    FALLBACK = "fallback"
    ABORT = "abort"


@dataclass
class IsolatedResult:
    """隔离执行结果"""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    error_type: Optional[ErrorType] = None
    error_context: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    retry_count: int = 0
    tool_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": str(self.error) if self.error else None,
            "error_type": self.error_type.value if self.error_type else None,
            "error_context": self.error_context,
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "tool_name": self.tool_name,
            "timestamp": self.timestamp
        }


@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str
    error_type: ErrorType
    error_message: str
    tool_name: str
    context: Dict[str, Any]
    timestamp: str
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False


class ErrorClassifier:
    """错误分类器"""
    
    TEMPORARY_ERRORS = (
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError,
    )
    
    NETWORK_ERROR_PATTERNS = [
        "connection refused",
        "connection reset",
        "network unreachable",
        "timeout",
        "socket error",
    ]
    
    @classmethod
    def classify(cls, error: Exception) -> ErrorType:
        """
        分类错误类型
        
        Args:
            error: 异常对象
            
        Returns:
            ErrorType: 错误类型
        """
        error_str = str(error).lower()
        
        if isinstance(error, asyncio.TimeoutError) or isinstance(error, TimeoutError):
            return ErrorType.TIMEOUT
        
        if isinstance(error, (ConnectionError, ConnectionRefusedError, ConnectionResetError)):
            return ErrorType.NETWORK
        
        if isinstance(error, PermissionError):
            return ErrorType.PERMISSION
        
        if isinstance(error, ValueError):
            return ErrorType.VALIDATION
        
        for pattern in cls.NETWORK_ERROR_PATTERNS:
            if pattern in error_str:
                return ErrorType.NETWORK
        
        if isinstance(error, cls.TEMPORARY_ERRORS):
            return ErrorType.TEMPORARY
        
        if "memory" in error_str or "resource" in error_str:
            return ErrorType.RESOURCE
        
        return ErrorType.UNKNOWN
    
    @classmethod
    def is_recoverable(cls, error_type: ErrorType) -> bool:
        """判断错误是否可恢复"""
        return error_type in (
            ErrorType.TEMPORARY,
            ErrorType.NETWORK,
            ErrorType.TIMEOUT,
            ErrorType.RESOURCE,
        )


class ErrorIsolationExecutor:
    """
    错误隔离执行器
    
    提供工具执行沙箱、异常捕获和恢复、错误影响范围控制功能。
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        default_timeout: float = 60.0
    ):
        """
        初始化错误隔离执行器
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 初始重试延迟(秒)
            backoff_factor: 退避因子
            default_timeout: 默认超时时间(秒)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.default_timeout = default_timeout
        self._error_records: List[ErrorRecord] = []
        self._error_handlers: Dict[ErrorType, Callable] = {}
        self._fallback_handlers: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()
        
        self._register_default_handlers()
        logger.info(f"🔧 错误隔离执行器初始化完成: 最大重试={max_retries}, 超时={default_timeout}s")
    
    def _register_default_handlers(self):
        """注册默认错误处理器"""
        self._error_handlers[ErrorType.TIMEOUT] = self._handle_timeout
        self._error_handlers[ErrorType.NETWORK] = self._handle_network_error
        self._error_handlers[ErrorType.RESOURCE] = self._handle_resource_error
    
    async def _handle_timeout(self, error: Exception, context: Dict[str, Any]) -> RecoveryStrategy:
        """处理超时错误"""
        logger.warning(f"⏱️ 超时错误: {error}")
        return RecoveryStrategy.RETRY
    
    async def _handle_network_error(self, error: Exception, context: Dict[str, Any]) -> RecoveryStrategy:
        """处理网络错误"""
        logger.warning(f"🌐 网络错误: {error}")
        return RecoveryStrategy.RETRY
    
    async def _handle_resource_error(self, error: Exception, context: Dict[str, Any]) -> RecoveryStrategy:
        """处理资源错误"""
        logger.warning(f"📦 资源错误: {error}")
        await asyncio.sleep(2)
        return RecoveryStrategy.RETRY
    
    def register_error_handler(self, error_type: ErrorType, handler: Callable):
        """注册错误处理器"""
        self._error_handlers[error_type] = handler
    
    def register_fallback_handler(self, tool_name: str, handler: Callable):
        """注册降级处理器"""
        self._fallback_handlers[tool_name] = handler
    
    async def execute(
        self,
        func: Callable[..., T],
        *args,
        tool_name: str = "",
        timeout: Optional[float] = None,
        retry_on_error: bool = True,
        fallback: Optional[Callable] = None,
        **kwargs
    ) -> IsolatedResult:
        """
        在隔离环境中执行函数
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            tool_name: 工具名称
            timeout: 超时时间
            retry_on_error: 是否在错误时重试
            fallback: 降级函数
            **kwargs: 关键字参数
            
        Returns:
            IsolatedResult: 隔离执行结果
        """
        start_time = time.time()
        timeout = timeout or self.default_timeout
        retry_count = 0
        last_error = None
        last_error_type = None
        
        while retry_count <= self.max_retries:
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                else:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(func, *args, **kwargs),
                        timeout=timeout
                    )
                
                execution_time = time.time() - start_time
                logger.info(f"✅ 工具 {tool_name} 执行成功, 耗时: {execution_time:.2f}s")
                
                return IsolatedResult(
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    retry_count=retry_count,
                    tool_name=tool_name
                )
                
            except asyncio.TimeoutError as e:
                last_error = e
                last_error_type = ErrorType.TIMEOUT
                logger.warning(f"⏱️ 工具 {tool_name} 执行超时 ({timeout}s)")
                
            except Exception as e:
                last_error = e
                last_error_type = ErrorClassifier.classify(e)
                logger.error(f"❌ 工具 {tool_name} 执行失败: {e}")
            
            if not retry_on_error or not ErrorClassifier.is_recoverable(last_error_type):
                break
            
            retry_count += 1
            if retry_count <= self.max_retries:
                delay = self.retry_delay * (self.backoff_factor ** (retry_count - 1))
                logger.info(f"🔄 工具 {tool_name} 将在 {delay:.1f}s 后重试 ({retry_count}/{self.max_retries})")
                await asyncio.sleep(delay)
        
        execution_time = time.time() - start_time
        
        error_context = {
            "tool_name": tool_name,
            "args": str(args)[:200] if args else None,
            "kwargs": str(kwargs)[:200] if kwargs else None,
            "retry_count": retry_count,
            "timeout": timeout
        }
        
        await self._record_error(
            error=last_error,
            error_type=last_error_type,
            tool_name=tool_name,
            context=error_context
        )
        
        if fallback or tool_name in self._fallback_handlers:
            fallback_func = fallback or self._fallback_handlers.get(tool_name)
            if fallback_func:
                logger.info(f"🔄 执行降级函数: {tool_name}")
                try:
                    fallback_result = await self.execute(
                        fallback_func, *args,
                        tool_name=f"{tool_name}_fallback",
                        timeout=timeout,
                        retry_on_error=False,
                        **kwargs
                    )
                    fallback_result.retry_count = retry_count
                    return fallback_result
                except Exception as e:
                    logger.error(f"❌ 降级函数执行失败: {e}")
        
        return IsolatedResult(
            success=False,
            error=last_error,
            error_type=last_error_type,
            error_context=error_context,
            execution_time=execution_time,
            retry_count=retry_count,
            tool_name=tool_name
        )
    
    async def _record_error(
        self,
        error: Exception,
        error_type: ErrorType,
        tool_name: str,
        context: Dict[str, Any]
    ):
        """记录错误"""
        error_id = f"{tool_name}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        record = ErrorRecord(
            error_id=error_id,
            error_type=error_type,
            error_message=str(error),
            tool_name=tool_name,
            context=context,
            timestamp=datetime.now().isoformat(),
            stack_trace=traceback.format_exc()
        )
        
        async with self._lock:
            self._error_records.append(record)
            if len(self._error_records) > 1000:
                self._error_records = self._error_records[-500:]
    
    def get_error_records(self, tool_name: Optional[str] = None, limit: int = 100) -> List[ErrorRecord]:
        """获取错误记录"""
        records = self._error_records
        if tool_name:
            records = [r for r in records if r.tool_name == tool_name]
        return records[-limit:]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        if not self._error_records:
            return {"total_errors": 0}
        
        type_counts = {}
        tool_counts = {}
        
        for record in self._error_records:
            type_counts[record.error_type.value] = type_counts.get(record.error_type.value, 0) + 1
            tool_counts[record.tool_name] = tool_counts.get(record.tool_name, 0) + 1
        
        return {
            "total_errors": len(self._error_records),
            "by_type": type_counts,
            "by_tool": tool_counts,
            "recent_errors": len([r for r in self._error_records[-100:]])
        }
    
    def clear_error_records(self):
        """清除错误记录"""
        self._error_records.clear()


def isolated_execution(
    tool_name: str = "",
    timeout: float = 60.0,
    max_retries: int = 3,
    fallback: Optional[Callable] = None
):
    """
    隔离执行装饰器
    
    Args:
        tool_name: 工具名称
        timeout: 超时时间
        max_retries: 最大重试次数
        fallback: 降级函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        executor = ErrorIsolationExecutor(max_retries=max_retries, default_timeout=timeout)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await executor.execute(
                func, *args,
                tool_name=tool_name or func.__name__,
                timeout=timeout,
                fallback=fallback,
                **kwargs
            )
            if result.success:
                return result.result
            raise result.error or Exception(f"Execution failed: {result.error_type}")
        
        return wrapper
    return decorator


def create_error_isolation_executor(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    default_timeout: float = 60.0
) -> ErrorIsolationExecutor:
    """
    创建错误隔离执行器的工厂函数
    
    Args:
        max_retries: 最大重试次数
        retry_delay: 重试延迟
        default_timeout: 默认超时时间
        
    Returns:
        ErrorIsolationExecutor: 错误隔离执行器实例
    """
    return ErrorIsolationExecutor(
        max_retries=max_retries,
        retry_delay=retry_delay,
        default_timeout=default_timeout
    )


default_executor: Optional[ErrorIsolationExecutor] = None


def get_default_executor() -> ErrorIsolationExecutor:
    """获取默认错误隔离执行器"""
    global default_executor
    if default_executor is None:
        default_executor = create_error_isolation_executor()
    return default_executor

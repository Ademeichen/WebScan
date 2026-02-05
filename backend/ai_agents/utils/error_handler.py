"""
异常处理工具模块

提供统一的异常处理、超时控制、重试机制等功能。
"""
import logging
import functools
import asyncio
from typing import Any, Callable, Dict, Optional, Type
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Agent基础异常类"""

    def __init__(self, message: str, error_code: str = "UNKNOWN", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class TimeoutError(AgentError):
    """超时异常"""

    def __init__(self, message: str, timeout: float = 0.0, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "TIMEOUT", details)
        self.timeout = timeout


class ValidationError(AgentError):
    """验证异常"""

    def __init__(self, message: str, validation_errors: Optional[list] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.validation_errors = validation_errors or []


class ExecutionError(AgentError):
    """执行异常"""

    def __init__(self, message: str, exit_code: int = -1, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EXECUTION_ERROR", details)
        self.exit_code = exit_code


class DependencyError(AgentError):
    """依赖异常"""

    def __init__(self, message: str, missing_dependencies: Optional[list] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DEPENDENCY_ERROR", details)
        self.missing_dependencies = missing_dependencies or []


class NetworkError(AgentError):
    """网络异常"""

    def __init__(self, message: str, url: str = "", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "NETWORK_ERROR", details)
        self.url = url


class ErrorHandler:
    """异常处理器"""

    def __init__(self, enable_logging: bool = True, enable_metrics: bool = True):
        """
        初始化异常处理器

        Args:
            enable_logging: 是否启用日志记录
            enable_metrics: 是否启用指标收集
        """
        self.enable_logging = enable_logging
        self.enable_metrics = enable_metrics
        self.error_counts: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        reraise: bool = False
    ) -> Dict[str, Any]:
        """
        处理异常

        Args:
            error: 异常对象
            context: 错误上下文
            reraise: 是否重新抛出异常

        Returns:
            Dict: 错误信息
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }

        if isinstance(error, AgentError):
            error_info["error_code"] = error.error_code
            error_info["details"] = error.details

        if self.enable_logging:
            self._log_error(error, context)

        if self.enable_metrics:
            await self._record_error(error)

        if reraise:
            raise error

        return error_info

    def _log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """记录错误日志"""
        error_type = type(error).__name__
        error_msg = str(error)

        if isinstance(error, AgentError):
            logger.error(
                f"[{error.error_code}] {error_msg}",
                extra={
                    "error_code": error.error_code,
                    "context": context,
                    "details": error.details
                }
            )
        else:
            logger.error(
                f"[{error_type}] {error_msg}",
                extra={"context": context}
            )

    async def _record_error(self, error: Exception):
        """记录错误统计"""
        error_type = type(error).__name__

        async with self._lock:
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

    def get_error_stats(self) -> Dict[str, int]:
        """获取错误统计"""
        return self.error_counts.copy()

    def reset_error_stats(self):
        """重置错误统计"""
        self.error_counts.clear()


def handle_errors(
    error_handler: Optional[ErrorHandler] = None,
    reraise: bool = False,
    default_return: Any = None
):
    """异常处理装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            handler = error_handler or ErrorHandler()

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200],
                    "kwargs": str(kwargs)[:200]
                }

                error_info = await handler.handle_error(e, context, reraise)

                if not reraise:
                    return default_return

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            handler = error_handler or ErrorHandler()

            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200],
                    "kwargs": str(kwargs)[:200]
                }

                error_info = asyncio.run(handler.handle_error(e, context, reraise))

                if not reraise:
                    return default_return

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def with_timeout(
    timeout: float,
    timeout_error_message: str = "操作超时"
):
    """超时控制装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(
                    timeout_error_message,
                    timeout=timeout,
                    details={"function": func.__name__}
                )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(
                    timeout_error_message,
                    timeout=timeout,
                    details={"function": func.__name__}
                )

            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))

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


def validate_input(
    validators: Optional[Dict[str, Callable]] = None,
    raise_on_error: bool = True
):
    """输入验证装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if validators:
                for param_name, validator in validators.items():
                    if param_name in kwargs:
                        try:
                            validator(kwargs[param_name])
                        except Exception as e:
                            error_msg = f"参数验证失败: {param_name} - {str(e)}"
                            if raise_on_error:
                                raise ValidationError(error_msg, validation_errors=[{
                                    "param": param_name,
                                    "error": str(e)
                                }])
                            else:
                                logger.warning(error_msg)

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if validators:
                for param_name, validator in validators.items():
                    if param_name in kwargs:
                        try:
                            validator(kwargs[param_name])
                        except Exception as e:
                            error_msg = f"参数验证失败: {param_name} - {str(e)}"
                            if raise_on_error:
                                raise ValidationError(error_msg, validation_errors=[{
                                    "param": param_name,
                                    "error": str(e)
                                }])
                            else:
                                logger.warning(error_msg)

            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def safe_execute(
    default_return: Any = None,
    log_errors: bool = True
):
    """安全执行装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(
                        f"安全执行失败: {func.__name__} - {str(e)}",
                        extra={"function": func.__name__}
                    )
                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(
                        f"安全执行失败: {func.__name__} - {str(e)}",
                        extra={"function": func.__name__}
                    )
                return default_return

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class CircuitBreaker:
    """熔断器"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        初始化熔断器

        Args:
            failure_threshold: 失败阈值
            recovery_timeout: 恢复超时时间(秒)
            expected_exception: 预期的异常类型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"

        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs):
        """调用函数"""
        async with self._lock:
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half_open"
                else:
                    raise AgentError(
                        "熔断器已打开，拒绝调用",
                        error_code="CIRCUIT_BREAKER_OPEN"
                    )

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            async with self._lock:
                if self.state == "half_open":
                    self.state = "closed"
                    self.failure_count = 0

            return result

        except self.expected_exception as e:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = datetime.now()

                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                    logger.warning(
                        f"熔断器已打开: 失败次数 {self.failure_count} >= {self.failure_threshold}"
                    )

            raise e

    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置"""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def get_state(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


# 全局异常处理器实例
global_error_handler = ErrorHandler()

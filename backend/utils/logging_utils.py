"""
结构化日志工具模块

提供JSON格式的结构化日志功能，包括：
- JSON格式日志输出
- 请求ID追踪
- 错误堆栈追踪
- 日志上下文管理
"""
import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from pathlib import Path

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    request_id_var.set(request_id)


class JsonFormatter(logging.Formatter):
    """
    JSON格式日志格式化器
    
    将日志记录格式化为JSON格式，包含以下字段：
    - timestamp: 时间戳
    - level: 日志级别
    - logger: 日志器名称
    - message: 日志消息
    - request_id: 请求ID（可选）
    - module: 模块名称
    - function: 函数名称
    - line: 行号
    - exception: 异常信息（可选）
    - extra: 额外字段
    """
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id
        
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_data["exception"] = {
                "type": exc_type.__name__ if exc_type else "Unknown",
                "message": str(exc_value) if exc_value else "",
                "traceback": self._format_traceback(exc_tb) if exc_tb else ""
            }
        
        if self.include_extra:
            extra_fields = {}
            standard_attrs = {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                'message', 'asctime'
            }
            for key, value in record.__dict__.items():
                if key not in standard_attrs and not key.startswith('_'):
                    try:
                        json.dumps(value)
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)
            
            if extra_fields:
                log_data["extra"] = extra_fields
        
        return json.dumps(log_data, ensure_ascii=False, default=str)
    
    def _format_traceback(self, tb) -> str:
        """格式化堆栈追踪"""
        if tb is None:
            return ""
        tb_list = traceback.format_tb(tb)
        return "".join(tb_list)


class StructuredLogger:
    """
    结构化日志器
    
    提供便捷的结构化日志记录方法，支持：
    - 自动添加上下文信息
    - 错误堆栈追踪
    - 性能指标记录
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self._context: Dict[str, Any] = {}
    
    def with_context(self, **kwargs) -> "StructuredLogger":
        """添加上下文信息"""
        new_logger = StructuredLogger(self.logger.name, self.logger.level)
        new_logger._context = {**self._context, **kwargs}
        return new_logger
    
    def _log(self, level: int, message: str, exc_info: bool = False, **kwargs):
        """内部日志方法"""
        extra = {**self._context, **kwargs}
        self.logger.log(level, message, exc_info=exc_info, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc: Exception = None, **kwargs):
        exc_info = exc is not None
        if exc:
            kwargs["error_type"] = type(exc).__name__
            kwargs["error_message"] = str(exc)
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc: Exception = None, **kwargs):
        exc_info = exc is not None
        if exc:
            kwargs["error_type"] = type(exc).__name__
            kwargs["error_message"] = str(exc)
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """记录异常日志（自动包含堆栈追踪）"""
        self._log(logging.ERROR, message, exc_info=True, **kwargs)


class TaskStateLogger:
    """
    任务状态日志记录器
    
    专门用于记录任务状态变更的日志，提供：
    - 任务状态变更追踪
    - 任务执行时间统计
    - 任务错误详情记录
    """
    
    def __init__(self):
        self.logger = StructuredLogger("task_state")
    
    def log_task_created(self, task_id: int, task_type: str, target: str, **kwargs):
        """记录任务创建"""
        self.logger.info(
            "Task created",
            task_id=task_id,
            task_type=task_type,
            target=target,
            event="task_created",
            **kwargs
        )
    
    def log_task_started(self, task_id: int, task_type: str, target: str, **kwargs):
        """记录任务开始"""
        self.logger.info(
            "Task started",
            task_id=task_id,
            task_type=task_type,
            target=target,
            event="task_started",
            **kwargs
        )
    
    def log_task_progress(self, task_id: int, progress: int, **kwargs):
        """记录任务进度"""
        self.logger.debug(
            "Task progress updated",
            task_id=task_id,
            progress=progress,
            event="task_progress",
            **kwargs
        )
    
    def log_task_completed(self, task_id: int, duration: float = None, **kwargs):
        """记录任务完成"""
        extra = {"task_id": task_id, "event": "task_completed"}
        if duration is not None:
            extra["duration_seconds"] = round(duration, 2)
        extra.update(kwargs)
        self.logger.info("Task completed", **extra)
    
    def log_task_failed(self, task_id: int, error: str, exc: Exception = None, **kwargs):
        """记录任务失败"""
        self.logger.error(
            "Task failed",
            task_id=task_id,
            error=error,
            event="task_failed",
            exc=exc,
            **kwargs
        )
    
    def log_task_timeout(self, task_id: int, timeout_seconds: int, **kwargs):
        """记录任务超时"""
        self.logger.warning(
            "Task timeout",
            task_id=task_id,
            timeout_seconds=timeout_seconds,
            event="task_timeout",
            **kwargs
        )
    
    def log_task_cancelled(self, task_id: int, reason: str = None, **kwargs):
        """记录任务取消"""
        extra = {"task_id": task_id, "event": "task_cancelled"}
        if reason:
            extra["reason"] = reason
        extra.update(kwargs)
        self.logger.info("Task cancelled", **extra)
    
    def log_task_recovery(self, task_id: int, task_type: str, status: str, **kwargs):
        """记录任务恢复"""
        self.logger.info(
            "Task recovered on startup",
            task_id=task_id,
            task_type=task_type,
            previous_status=status,
            event="task_recovery",
            **kwargs
        )
    
    def log_heartbeat(self, task_id: int, **kwargs):
        """记录任务心跳"""
        self.logger.debug(
            "Task heartbeat",
            task_id=task_id,
            event="task_heartbeat",
            **kwargs
        )


def setup_structured_logging(
    log_level: str = "INFO",
    log_file: str = None,
    json_format: bool = True,
    console_output: bool = True
) -> None:
    """
    配置结构化日志系统
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        json_format: 是否使用JSON格式
        console_output: 是否输出到控制台
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
            defaults={'request_id': ''}
        )
    
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


task_state_logger = TaskStateLogger()


class RequestContext:
    """
    请求上下文管理器
    
    用于在请求处理过程中管理请求ID和上下文信息
    """
    
    def __init__(self, request_id: str = None, **context):
        self.request_id = request_id or ""
        self.context = context
        self._old_request_id = None
    
    def __enter__(self):
        self._old_request_id = get_request_id()
        set_request_id(self.request_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        set_request_id(self._old_request_id or "")
        return False


def log_exception_with_context(
    logger: logging.Logger,
    message: str,
    exc: Exception,
    **context
) -> None:
    """
    记录带有上下文的异常日志
    
    Args:
        logger: 日志器
        message: 日志消息
        exc: 异常对象
        **context: 额外的上下文信息
    """
    exc_info = {
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc()
    }
    
    log_data = {
        "message": message,
        "exception": exc_info,
        "context": context,
        "request_id": get_request_id()
    }
    
    logger.error(json.dumps(log_data, ensure_ascii=False, default=str))

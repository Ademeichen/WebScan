"""
日志和监控工具模块

提供统一的日志记录、监控指标、性能追踪等功能。
"""
import logging
import time
import functools
import threading
from typing import Any, Dict, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: str
    level: str
    module: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "module": self.module,
            "message": self.message,
            "context": self.context
        }


class LogBuffer:
    """日志缓冲区"""

    def __init__(self, max_size: int = 1000):
        """
        初始化日志缓冲区

        Args:
            max_size: 最大日志条数
        """
        self.max_size = max_size
        self.logs: List[LogEntry] = []
        self._lock = threading.Lock()

    def add(self, level: str, module: str, message: str, context: Optional[Dict[str, Any]] = None):
        """添加日志"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            module=module,
            message=message,
            context=context or {}
        )

        with self._lock:
            self.logs.append(entry)

            if len(self.logs) > self.max_size:
                self.logs = self.logs[-self.max_size:]

    def get_logs(
        self,
        level: Optional[str] = None,
        module: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[LogEntry]:
        """获取日志"""
        with self._lock:
            filtered_logs = self.logs

            if level:
                filtered_logs = [log for log in filtered_logs if log.level == level]

            if module:
                filtered_logs = [log for log in filtered_logs if log.module == module]

            if limit:
                filtered_logs = filtered_logs[-limit:]

            return filtered_logs.copy()

    def clear(self):
        """清空日志"""
        with self._lock:
            self.logs.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            level_counts = defaultdict(int)
            module_counts = defaultdict(int)

            for log in self.logs:
                level_counts[log.level] += 1
                module_counts[log.module] += 1

            return {
                "total_logs": len(self.logs),
                "level_counts": dict(level_counts),
                "module_counts": dict(module_counts),
                "max_size": self.max_size,
                "usage_percent": len(self.logs) / self.max_size * 100
            }


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        """初始化指标收集器"""
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def increment(self, name: str, value: int = 1):
        """增加计数器"""
        with self._lock:
            self.counters[name] += value

    def decrement(self, name: str, value: int = 1):
        """减少计数器"""
        with self._lock:
            self.counters[name] -= value

    def set_gauge(self, name: str, value: float):
        """设置仪表盘值"""
        with self._lock:
            self.gauges[name] = value

    def record_histogram(self, name: str, value: float):
        """记录直方图值"""
        with self._lock:
            self.histograms[name].append(value)

            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]

    def get_counter(self, name: str) -> int:
        """获取计数器值"""
        with self._lock:
            return self.counters.get(name, 0)

    def get_gauge(self, name: str) -> Optional[float]:
        """获取仪表盘值"""
        with self._lock:
            return self.gauges.get(name)

    def get_histogram(self, name: str) -> Dict[str, float]:
        """获取直方图统计"""
        with self._lock:
            values = self.histograms.get(name, [])

            if not values:
                return {
                    "count": 0,
                    "min": 0.0,
                    "max": 0.0,
                    "avg": 0.0,
                    "p50": 0.0,
                    "p95": 0.0,
                    "p99": 0.0
                }

            sorted_values = sorted(values)
            count = len(sorted_values)

            return {
                "count": count,
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "avg": sum(sorted_values) / count,
                "p50": sorted_values[int(count * 0.5)],
                "p95": sorted_values[int(count * 0.95)],
                "p99": sorted_values[int(count * 0.99)]
            }

    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        with self._lock:
            return {
                "counters": dict(self.counters),
                "gauges": self.gauges.copy(),
                "histograms": {
                    name: self.get_histogram(name)
                    for name in self.histograms.keys()
                }
            }

    def reset(self):
        """重置所有指标"""
        with self._lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()


class Tracer:
    """追踪器"""

    def __init__(self):
        """初始化追踪器"""
        self.spans: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._current_span: Optional[Dict[str, Any]] = None

    def start_span(
        self,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """开始一个span"""
        span_id = f"{operation}_{time.time()}"

        span = {
            "span_id": span_id,
            "operation": operation,
            "start_time": time.time(),
            "end_time": None,
            "duration": None,
            "context": context or {},
            "parent_span_id": self._current_span["span_id"] if self._current_span else None,
            "status": "running"
        }

        with self._lock:
            self.spans.append(span)
            self._current_span = span

        return span_id

    def end_span(
        self,
        span_id: str,
        status: str = "completed",
        error: Optional[str] = None
    ):
        """结束一个span"""
        with self._lock:
            for span in self.spans:
                if span["span_id"] == span_id:
                    span["end_time"] = time.time()
                    span["duration"] = span["end_time"] - span["start_time"]
                    span["status"] = status

                    if error:
                        span["error"] = error

                    if self._current_span and self._current_span["span_id"] == span_id:
                        self._current_span = None

                    break

    def get_spans(
        self,
        operation: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取spans"""
        with self._lock:
            filtered_spans = self.spans

            if operation:
                filtered_spans = [span for span in filtered_spans if span["operation"] == operation]

            if status:
                filtered_spans = [span for span in filtered_spans if span["status"] == status]

            if limit:
                filtered_spans = filtered_spans[-limit:]

            return filtered_spans.copy()

    def clear(self):
        """清空所有spans"""
        with self._lock:
            self.spans.clear()
            self._current_span = None


class MonitoringSystem:
    """监控系统"""

    def __init__(self, enable_logging: bool = True, enable_metrics: bool = True):
        """
        初始化监控系统

        Args:
            enable_logging: 是否启用日志记录
            enable_metrics: 是否启用指标收集
        """
        self.enable_logging = enable_logging
        self.enable_metrics = enable_metrics

        self.log_buffer = LogBuffer(max_size=1000)
        self.metrics = MetricsCollector()
        self.tracer = Tracer()

        if enable_logging:
            self._setup_logging()

    def _setup_logging(self):
        """设置日志"""
        handler = LogHandler(self.log_buffer)
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

    def log(
        self,
        level: str,
        module: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """记录日志"""
        if self.enable_logging:
            self.log_buffer.add(level, module, message, context)

    def get_logs(self, **kwargs) -> List[LogEntry]:
        """获取日志"""
        return self.log_buffer.get_logs(**kwargs)

    def increment_counter(self, name: str, value: int = 1):
        """增加计数器"""
        if self.enable_metrics:
            self.metrics.increment(name, value)

    def set_gauge(self, name: str, value: float):
        """设置仪表盘值"""
        if self.enable_metrics:
            self.metrics.set_gauge(name, value)

    def record_histogram(self, name: str, value: float):
        """记录直方图值"""
        if self.enable_metrics:
            self.metrics.record_histogram(name, value)

    def start_trace(self, operation: str, context: Optional[Dict[str, Any]] = None) -> str:
        """开始追踪"""
        return self.tracer.start_span(operation, context)

    def end_trace(self, span_id: str, status: str = "completed", error: Optional[str] = None):
        """结束追踪"""
        self.tracer.end_span(span_id, status, error)

    def get_monitoring_report(self) -> Dict[str, Any]:
        """获取监控报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "logs": self.log_buffer.get_stats(),
            "metrics": self.metrics.get_all_metrics(),
            "traces": {
                "total_spans": len(self.tracer.spans),
                "active_spans": 1 if self.tracer._current_span else 0
            }
        }

    def reset(self):
        """重置监控系统"""
        self.log_buffer.clear()
        self.metrics.reset()
        self.tracer.clear()


class LogHandler(logging.Handler):
    """日志处理器"""

    def __init__(self, log_buffer: LogBuffer):
        """
        初始化日志处理器

        Args:
            log_buffer: 日志缓冲区
        """
        super().__init__()
        self.log_buffer = log_buffer

    def emit(self, record: logging.LogRecord):
        """发送日志"""
        try:
            self.log_buffer.add(
                level=record.levelname,
                module=record.name,
                message=record.getMessage(),
                context={
                    "function": record.funcName,
                    "line": record.lineno,
                    "path": record.pathname
                }
            )
        except Exception:
            self.handleError(record)


def log_execution_time(metrics: MetricsCollector, operation_name: str):
    """执行时间日志装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                metrics.increment(f"{operation_name}_success")
                return result
            except Exception as e:
                metrics.increment(f"{operation_name}_error")
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_histogram(f"{operation_name}_duration", duration)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                metrics.increment(f"{operation_name}_success")
                return result
            except Exception as e:
                metrics.increment(f"{operation_name}_error")
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_histogram(f"{operation_name}_duration", duration)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 全局监控系统实例
global_monitor = MonitoringSystem()

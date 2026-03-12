"""
流程执行优化模块

提供响应时间监控、重试机制、节点跳过等功能。
"""
import time
import logging
import asyncio
from typing import Any, Callable, Optional, Dict, Tuple
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime

from ..agent_config import agent_config

logger = logging.getLogger(__name__)


@dataclass
class NodeExecutionMetrics:
    """节点执行指标"""
    node_name: str
    task_id: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = False
    retries: int = 0
    skipped: bool = False
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ExecutionMetricsCollector:
    """执行指标收集器"""
    
    def __init__(self):
        self.metrics: Dict[str, NodeExecutionMetrics] = {}
        self._lock = asyncio.Lock()
    
    async def start_execution(self, node_name: str, task_id: str) -> str:
        """开始执行记录"""
        metrics_id = f"{task_id}_{node_name}_{int(time.time())}"
        metrics = NodeExecutionMetrics(
            node_name=node_name,
            task_id=task_id,
            start_time=time.time()
        )
        
        async with self._lock:
            self.metrics[metrics_id] = metrics
        
        logger.debug(f"[Metrics] 开始执行: {node_name}, 任务ID: {task_id}")
        return metrics_id
    
    async def end_execution(self, metrics_id: str, success: bool, error: Optional[str] = None):
        """结束执行记录"""
        async with self._lock:
            if metrics_id in self.metrics:
                metrics = self.metrics[metrics_id]
                metrics.end_time = time.time()
                metrics.duration = metrics.end_time - metrics.start_time
                metrics.success = success
                metrics.error = error
                
                logger.debug(
                    f"[Metrics] 执行完成: {metrics.node_name}, "
                    f"任务ID: {metrics.task_id}, "
                    f"耗时: {metrics.duration:.2f}s, "
                    f"成功: {success}"
                )
    
    async def record_retry(self, metrics_id: str):
        """记录重试"""
        async with self._lock:
            if metrics_id in self.metrics:
                self.metrics[metrics_id].retries += 1
                logger.debug(
                    f"[Metrics] 重试: {self.metrics[metrics_id].node_name}, "
                    f"重试次数: {self.metrics[metrics_id].retries}"
                )
    
    async def mark_skipped(self, metrics_id: str, reason: str):
        """标记为跳过"""
        async with self._lock:
            if metrics_id in self.metrics:
                self.metrics[metrics_id].skipped = True
                self.metrics[metrics_id].error = reason
                logger.warning(
                    f"[Metrics] 节点跳过: {self.metrics[metrics_id].node_name}, "
                    f"原因: {reason}"
                )
    
    def get_metrics(self, task_id: Optional[str] = None) -> list:
        """获取指标"""
        if task_id:
            return [m for m in self.metrics.values() if m.task_id == task_id]
        return list(self.metrics.values())
    
    def get_summary(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """获取摘要"""
        metrics_list = self.get_metrics(task_id)
        if not metrics_list:
            return {}
        
        total = len(metrics_list)
        successful = sum(1 for m in metrics_list if m.success and not m.skipped)
        skipped = sum(1 for m in metrics_list if m.skipped)
        failed = total - successful - skipped
        
        durations = [m.duration for m in metrics_list if m.duration is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        total_duration = sum(durations) if durations else 0
        
        return {
            "total_nodes": total,
            "successful": successful,
            "skipped": skipped,
            "failed": failed,
            "avg_duration": avg_duration,
            "max_duration": max_duration,
            "total_duration": total_duration
        }


class NodeExecutionOptimizer:
    """节点执行优化器"""
    
    def __init__(self):
        self.metrics_collector = ExecutionMetricsCollector()
    
    async def execute_with_optimization(
        self,
        node_func: Callable,
        node_name: str,
        task_id: str,
        *args,
        **kwargs
    ) -> Tuple[Any, bool]:
        """
        带优化机制的节点执行
        
        Args:
            node_func: 节点函数
            node_name: 节点名称
            task_id: 任务ID
            *args, **kwargs: 节点函数参数
            
        Returns:
            (结果, 是否成功)
        """
        if not agent_config.ENABLE_RESPONSE_TIME_MONITORING:
            try:
                result = await node_func(*args, **kwargs)
                return result, True
            except Exception as e:
                logger.error(f"节点执行失败: {node_name}, 错误: {str(e)}")
                return None, False
        
        metrics_id = await self.metrics_collector.start_execution(node_name, task_id)
        
        max_retries = agent_config.NODE_MAX_RETRIES
        threshold = agent_config.NODE_RESPONSE_TIME_THRESHOLD
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(node_func):
                    result = await asyncio.wait_for(
                        node_func(*args, **kwargs),
                        timeout=threshold
                    )
                else:
                    result = node_func(*args, **kwargs)
                
                duration = time.time() - start_time
                
                await self.metrics_collector.end_execution(metrics_id, success=True)
                
                logger.info(
                    f"✅ 节点执行成功: {node_name}, "
                    f"任务ID: {task_id}, "
                    f"耗时: {duration:.2f}s"
                )
                
                return result, True
                
            except asyncio.TimeoutError:
                last_error = f"执行超时 (>{threshold}s)"
                logger.warning(
                    f"⏱️ 节点执行超时: {node_name}, "
                    f"任务ID: {task_id}, "
                    f"尝试: {attempt + 1}/{max_retries + 1}"
                )
                
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"⚠️ 节点执行异常: {node_name}, "
                    f"任务ID: {task_id}, "
                    f"尝试: {attempt + 1}/{max_retries + 1}, "
                    f"错误: {last_error}"
                )
            
            if attempt < max_retries:
                await self.metrics_collector.record_retry(metrics_id)
                wait_time = min(2 ** attempt, 10)
                logger.info(f"🔄 {wait_time}秒后重试...")
                await asyncio.sleep(wait_time)
        
        await self.metrics_collector.end_execution(
            metrics_id,
            success=False,
            error=last_error
        )
        
        if agent_config.ENABLE_NODE_SKIPPING:
            await self.metrics_collector.mark_skipped(metrics_id, last_error)
            logger.warning(
                f"⏭️ 节点已跳过: {node_name}, "
                f"任务ID: {task_id}, "
                f"原因: {last_error}"
            )
            return None, True
        
        logger.error(
            f"❌ 节点执行最终失败: {node_name}, "
            f"任务ID: {task_id}, "
            f"错误: {last_error}"
        )
        return None, False
    
    def get_execution_summary(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """获取执行摘要"""
        return self.metrics_collector.get_summary(task_id)
    
    def get_execution_metrics(self, task_id: Optional[str] = None) -> list:
        """获取执行指标"""
        return self.metrics_collector.get_metrics(task_id)


def optimized_node(node_name: str):
    """
    优化节点装饰器
    
    Args:
        node_name: 节点名称
    """
    def decorator(func):
        optimizer = NodeExecutionOptimizer()
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            task_id = None
            for arg in args:
                if hasattr(arg, 'task_id'):
                    task_id = arg.task_id
                    break
            
            if task_id is None:
                task_id = kwargs.get('task_id', f'unknown-{int(time.time())}')
            
            result, success = await optimizer.execute_with_optimization(
                func,
                node_name,
                task_id,
                *args,
                **kwargs
            )
            
            return result
        
        return wrapper
    return decorator


_execution_optimizer = NodeExecutionOptimizer()


def get_execution_optimizer() -> NodeExecutionOptimizer:
    """获取全局执行优化器实例"""
    return _execution_optimizer

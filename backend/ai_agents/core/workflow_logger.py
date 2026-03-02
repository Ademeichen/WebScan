"""
AIAgent工作流日志追踪系统

实现功能：
- 在关键节点插入详细日志记录
- 日志同时输出到控制台和指定日志文件
- 日志包含时间戳、节点标识、数据内容和执行状态
- 完整追踪AIAgent经过的所有工作节点路径
"""
import logging
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler
import threading


class WorkflowLogger:
    """
    工作流日志记录器
    
    实现同时输出到控制台和文件的日志记录
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        log_dir: str = None,
        log_level: int = logging.DEBUG,
        max_file_size: int = 10 * 1024 * 1024,
        backup_count: int = 5
    ):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self.log_dir = log_dir or os.path.join(os.path.dirname(__file__), "logs")
        self.log_level = log_level
        
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("AIAgentWorkflow")
        self.logger.setLevel(log_level)
        self.logger.handlers = []
        
        self._setup_console_handler()
        self._setup_file_handler(max_file_size, backup_count)
        
        self.traces: Dict[str, Dict[str, Any]] = {}
        self.current_trace_id: Optional[str] = None
    
    def _setup_console_handler(self):
        """设置控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self, max_file_size: int, backup_count: int):
        """设置文件处理器"""
        log_file = os.path.join(self.log_dir, f"workflow_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        self.trace_file = os.path.join(self.log_dir, f"trace_{datetime.now().strftime('%Y%m%d')}.jsonl")
    
    def start_workflow_trace(self, task_id: str, target: str) -> str:
        """
        开始工作流追踪
        
        Args:
            task_id: 任务ID
            target: 扫描目标
            
        Returns:
            str: 追踪ID
        """
        trace_id = f"{task_id}_{int(time.time() * 1000)}"
        self.current_trace_id = trace_id
        
        self.traces[trace_id] = {
            "trace_id": trace_id,
            "task_id": task_id,
            "target": target,
            "start_time": datetime.now().isoformat(),
            "nodes_visited": [],
            "data_transfers": [],
            "state_changes": [],
            "decisions": [],
            "errors": [],
            "performance_metrics": {}
        }
        
        self.logger.info(f"[TRACE_START] 追踪ID: {trace_id}, 目标: {target}")
        self._append_trace_to_file(self.traces[trace_id], "start")
        
        return trace_id
    
    def log_node_entry(
        self,
        node_name: str,
        task_id: str,
        input_state: Dict[str, Any] = None,
        details: Dict[str, Any] = None
    ):
        """
        记录节点进入日志
        
        Args:
            node_name: 节点名称
            task_id: 任务ID
            input_state: 输入状态
            details: 详细信息
        """
        timestamp = datetime.now().isoformat()
        
        log_data = {
            "timestamp": timestamp,
            "event": "NODE_ENTRY",
            "node_name": node_name,
            "task_id": task_id,
            "input_state_keys": list(input_state.keys()) if input_state else [],
            "details": details or {}
        }
        
        self.logger.info(f"[NODE_ENTRY] 节点: {node_name}, 任务ID: {task_id}")
        self._add_to_trace("nodes_visited", log_data)
        self._append_trace_to_file(log_data, "node_entry")
    
    def log_node_exit(
        self,
        node_name: str,
        task_id: str,
        status: str,
        output_state: Dict[str, Any] = None,
        execution_time: float = None,
        details: Dict[str, Any] = None
    ):
        """
        记录节点退出日志
        
        Args:
            node_name: 节点名称
            task_id: 任务ID
            status: 退出状态(success/failed/skipped)
            output_state: 输出状态
            execution_time: 执行时间
            details: 详细信息
        """
        timestamp = datetime.now().isoformat()
        
        log_data = {
            "timestamp": timestamp,
            "event": "NODE_EXIT",
            "node_name": node_name,
            "task_id": task_id,
            "status": status,
            "output_state_keys": list(output_state.keys()) if output_state else [],
            "execution_time": execution_time,
            "details": details or {}
        }
        
        status_icon = "✅" if status == "success" else "❌" if status == "failed" else "⏭️"
        self.logger.info(f"[NODE_EXIT] {status_icon} 节点: {node_name}, 状态: {status}, 耗时: {execution_time:.3f}s" if execution_time else f"[NODE_EXIT] {status_icon} 节点: {node_name}, 状态: {status}")
        self._add_to_trace("nodes_visited", log_data)
        self._append_trace_to_file(log_data, "node_exit")
    
    def log_state_change(
        self,
        task_id: str,
        key: str,
        old_value: Any,
        new_value: Any,
        node_name: str = None
    ):
        """
        记录状态变更日志
        
        Args:
            task_id: 任务ID
            key: 状态键名
            old_value: 旧值
            new_value: 新值
            node_name: 触发变更的节点名称
        """
        timestamp = datetime.now().isoformat()
        
        old_str = str(old_value)[:200] if old_value is not None else "None"
        new_str = str(new_value)[:200] if new_value is not None else "None"
        
        log_data = {
            "timestamp": timestamp,
            "event": "STATE_CHANGE",
            "task_id": task_id,
            "node_name": node_name,
            "key": key,
            "old_value": old_str,
            "new_value": new_str
        }
        
        self.logger.debug(f"[STATE_CHANGE] 任务ID: {task_id}, 键: {key}, 旧值: {old_str[:50]}, 新值: {new_str[:50]}")
        self._add_to_trace("state_changes", log_data)
        self._append_trace_to_file(log_data, "state_change")
    
    def log_decision(
        self,
        task_id: str,
        decision_type: str,
        decision: str,
        reason: str = "",
        node_name: str = None
    ):
        """
        记录决策日志
        
        Args:
            task_id: 任务ID
            decision_type: 决策类型
            decision: 决策结果
            reason: 决策原因
            node_name: 触发决策的节点名称
        """
        timestamp = datetime.now().isoformat()
        
        log_data = {
            "timestamp": timestamp,
            "event": "DECISION",
            "task_id": task_id,
            "node_name": node_name,
            "decision_type": decision_type,
            "decision": decision,
            "reason": reason
        }
        
        self.logger.info(f"[DECISION] 任务ID: {task_id}, 类型: {decision_type}, 决策: {decision}, 原因: {reason}")
        self._add_to_trace("decisions", log_data)
        self._append_trace_to_file(log_data, "decision")
    
    def log_data_transfer(
        self,
        from_node: str,
        to_node: str,
        data_keys: List[str],
        data_sample: Dict[str, Any] = None
    ):
        """
        记录数据传递日志
        
        Args:
            from_node: 源节点
            to_node: 目标节点
            data_keys: 传递的数据键列表
            data_sample: 数据样本
        """
        timestamp = datetime.now().isoformat()
        
        log_data = {
            "timestamp": timestamp,
            "event": "DATA_TRANSFER",
            "from_node": from_node,
            "to_node": to_node,
            "data_keys": data_keys,
            "data_sample": str(data_sample)[:500] if data_sample else None
        }
        
        self.logger.debug(f"[DATA_TRANSFER] {from_node} -> {to_node}, 数据键: {data_keys}")
        self._add_to_trace("data_transfers", log_data)
        self._append_trace_to_file(log_data, "data_transfer")
    
    def log_error(
        self,
        task_id: str,
        node_name: str,
        error: Exception,
        context: Dict[str, Any] = None
    ):
        """
        记录错误日志
        
        Args:
            task_id: 任务ID
            node_name: 节点名称
            error: 异常对象
            context: 错误上下文
        """
        timestamp = datetime.now().isoformat()
        
        log_data = {
            "timestamp": timestamp,
            "event": "ERROR",
            "task_id": task_id,
            "node_name": node_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        self.logger.error(f"[ERROR] 任务ID: {task_id}, 节点: {node_name}, 错误: {type(error).__name__}: {str(error)}")
        self._add_to_trace("errors", log_data)
        self._append_trace_to_file(log_data, "error")
    
    def log_performance(
        self,
        task_id: str,
        metrics: Dict[str, Any]
    ):
        """
        记录性能指标
        
        Args:
            task_id: 任务ID
            metrics: 性能指标字典
        """
        timestamp = datetime.now().isoformat()
        
        log_data = {
            "timestamp": timestamp,
            "event": "PERFORMANCE",
            "task_id": task_id,
            "metrics": metrics
        }
        
        self.logger.info(f"[PERFORMANCE] 任务ID: {task_id}, 指标: {metrics}")
        if self.current_trace_id and self.current_trace_id in self.traces:
            self.traces[self.current_trace_id]["performance_metrics"].update(metrics)
        self._append_trace_to_file(log_data, "performance")
    
    def end_workflow_trace(self, task_id: str, final_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        结束工作流追踪
        
        Args:
            task_id: 任务ID
            final_state: 最终状态
            
        Returns:
            Dict: 追踪报告
        """
        if self.current_trace_id and self.current_trace_id in self.traces:
            trace = self.traces[self.current_trace_id]
            trace["end_time"] = datetime.now().isoformat()
            trace["final_state"] = {
                "is_complete": final_state.get("is_complete") if final_state else None,
                "total_vulnerabilities": len(final_state.get("vulnerabilities", [])) if final_state else 0,
                "total_errors": len(final_state.get("errors", [])) if final_state else 0,
                "completed_tasks": final_state.get("completed_tasks", []) if final_state else []
            }
            
            trace["summary"] = {
                "total_nodes_visited": len(trace["nodes_visited"]),
                "total_data_transfers": len(trace["data_transfers"]),
                "total_state_changes": len(trace["state_changes"]),
                "total_decisions": len(trace["decisions"]),
                "total_errors": len(trace["errors"])
            }
            
            self.logger.info(f"[TRACE_END] 追踪ID: {self.current_trace_id}, 总结: {trace['summary']}")
            self._append_trace_to_file(trace, "end")
            
            result = trace.copy()
            self.current_trace_id = None
            return result
        
        return {}
    
    def _add_to_trace(self, key: str, data: Dict[str, Any]):
        """添加数据到当前追踪"""
        if self.current_trace_id and self.current_trace_id in self.traces:
            self.traces[self.current_trace_id][key].append(data)
    
    def _append_trace_to_file(self, data: Dict[str, Any], event_type: str):
        """追加追踪数据到文件"""
        try:
            with open(self.trace_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False, default=str) + '\n')
        except Exception as e:
            self.logger.error(f"写入追踪文件失败: {e}")
    
    def get_trace_report(self, trace_id: str = None) -> Dict[str, Any]:
        """
        获取追踪报告
        
        Args:
            trace_id: 追踪ID，如果为None则返回所有追踪
            
        Returns:
            Dict: 追踪报告
        """
        if trace_id:
            return self.traces.get(trace_id, {})
        return {
            "total_traces": len(self.traces),
            "traces": list(self.traces.values())
        }
    
    def get_node_path(self, trace_id: str) -> List[str]:
        """
        获取节点路径
        
        Args:
            trace_id: 追踪ID
            
        Returns:
            List[str]: 节点路径列表
        """
        if trace_id not in self.traces:
            return []
        
        trace = self.traces[trace_id]
        path = []
        for node_visit in trace.get("nodes_visited", []):
            if node_visit.get("event") == "NODE_ENTRY":
                path.append(node_visit.get("node_name"))
        return path


workflow_logger = WorkflowLogger()


def get_workflow_logger() -> WorkflowLogger:
    """获取工作流日志记录器实例"""
    return workflow_logger

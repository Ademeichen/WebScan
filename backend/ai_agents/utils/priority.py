"""
任务优先级管理

实现任务优先级排序和动态调整功能。
"""
import logging
from typing import List, Dict, Any
from ..agent_config import agent_config

logger = logging.getLogger(__name__)


class TaskPriorityManager:
    """
    任务优先级管理器
    
    负责根据任务类型、漏洞严重度、目标特征等因素
    动态调整任务优先级。
    """
    
    def __init__(self):
        self.priority_weights = agent_config.PRIORITY_WEIGHTS.copy()
        logger.info("🎯 任务优先级管理器初始化完成")
    
    def calculate_priority(
        self,
        task_name: str,
        context: Dict[str, Any] = None
    ) -> float:
        """
        计算任务优先级
        
        Args:
            task_name: 任务名称
            context: 目标上下文
            
        Returns:
            float: 优先级分数(越高优先级越高)
        """
        base_priority = self._get_base_priority(task_name)
        
        if context:
            # 根据上下文调整优先级
            adjusted_priority = self._adjust_by_context(
                task_name, base_priority, context
            )
            return adjusted_priority
        
        return base_priority
    
    def sort_tasks(
        self,
        tasks: List[str],
        context: Dict[str, Any] = None
    ) -> List[str]:
        """
        对任务列表进行优先级排序
        
        Args:
            tasks: 任务列表
            context: 目标上下文
            
        Returns:
            List[str]: 排序后的任务列表
        """
        task_priorities = []
        for task in tasks:
            priority = self.calculate_priority(task, context)
            task_priorities.append((task, priority))
        
        # 按优先级降序排序
        sorted_tasks = sorted(
            task_priorities,
            key=lambda x: x[1],
            reverse=True
        )
        
        logger.info(f"🎯 任务优先级排序: {[t[0] for t in sorted_tasks]}")
        return [t[0] for t in sorted_tasks]
    
    def _get_base_priority(self, task_name: str) -> float:
        """
        获取任务基础优先级
        
        Args:
            task_name: 任务名称
            
        Returns:
            float: 基础优先级
        """
        task_lower = task_name.lower()
        
        if task_lower == "portscan":
            return self.priority_weights.get("portscan", 0.5)
        elif task_lower == "baseinfo":
            return self.priority_weights.get("baseinfo", 0.3)
        elif task_lower in ["waf_detect", "cdn_detect", "cms_identify"]:
            return 0.4
        elif task_lower in ["infoleak_scan", "subdomain_scan"]:
            return 0.35
        
        return 0.5
    
    def _adjust_by_context(
        self,
        task_name: str,
        base_priority: float,
        context: Dict[str, Any]
    ) -> float:
        """
        根据上下文调整优先级
        
        Args:
            task_name: 任务名称
            base_priority: 基础优先级
            context: 目标上下文
            
        Returns:
            float: 调整后的优先级
        """
        adjusted_priority = base_priority
        
        if context.get("cdn") and task_name == "portscan":
            adjusted_priority *= 0.7

        return min(adjusted_priority, 1.0)
    
    def get_critical_tasks(self, tasks: List[str]) -> List[str]:
        """
        获取关键任务列表
        
        Args:
            tasks: 任务列表
            
        Returns:
            List[str]: 关键任务列表
        """
        critical_tasks = []
        for task in tasks:
            priority = self.calculate_priority(task)
            if priority >= 0.8:
                critical_tasks.append(task)
        
        return critical_tasks

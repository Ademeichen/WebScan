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
        
        # POC验证任务优先级最高
        if task_lower.startswith("poc_"):
            return self.priority_weights.get("poc_verification", 0.9)
        
        # 基础信息收集任务
        if task_lower == "portscan":
            return self.priority_weights.get("portscan", 0.5)
        elif task_lower == "baseinfo":
            return self.priority_weights.get("baseinfo", 0.3)
        elif task_lower in ["waf_detect", "cdn_detect", "cms_identify"]:
            return 0.4
        elif task_lower in ["infoleak_scan", "subdomain_scan"]:
            return 0.35
        
        # 默认优先级
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
        
        # 如果检测到WAF,降低POC优先级(避免被封禁)
        if context.get("waf") and task_name.startswith("poc_"):
            adjusted_priority *= 0.5
            logger.debug(f"检测到WAF,降低POC优先级: {task_name}")
        
        # 如果检测到CDN,降低端口扫描优先级
        if context.get("cdn") and task_name == "portscan":
            adjusted_priority *= 0.7

        
        # 如果CMS已知,提高相关POC优先级
        cms = context.get("cms", "").lower()
        if cms and task_name.startswith("poc_"):
            poc_lower = task_name.lower()
            if cms in poc_lower:
                adjusted_priority *= 1.5
                logger.debug(f"提高相关POC优先级: {task_name}")
        
        # 如果开放特定端口,提高相关POC优先级
        open_ports = context.get("open_ports", [])
        if task_name.startswith("poc_"):
            for port in open_ports:
                port_pocs = self._get_pocs_by_port(port)
                if task_name in port_pocs:
                    adjusted_priority *= 1.3
                    logger.debug(f"提高端口{port}相关POC优先级: {task_name}")
                    break
        
        return min(adjusted_priority, 1.0)
    
    def _get_pocs_by_port(self, port: int) -> List[str]:
        """
        根据端口获取相关POC
        
        Args:
            port: 端口号
            
        Returns:
            List[str]: POC名称列表
        """
        from ..tools.adapters import POCAdapter
        return POCAdapter.get_poc_by_port(port)
    
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

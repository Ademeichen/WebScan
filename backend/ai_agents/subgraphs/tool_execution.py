"""
工具执行子图

负责固定工具执行、结果验证和循环控制。
执行时间目标: < 2分钟
"""
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionState:
    """
    工具执行状态
    
    ToolExecutionGraph专用的轻量级状态类。
    """
    target: str
    task_id: str
    planned_tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    tool_results: Dict[str, Any] = field(default_factory=dict)
    target_context: Dict[str, Any] = field(default_factory=dict)
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    new_poc_tasks: List[Dict[str, Any]] = field(default_factory=list)
    awvs_required: bool = False
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    execution_time: float = 0.0
    _round: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "task_id": self.task_id,
            "planned_tasks": self.planned_tasks,
            "completed_tasks": self.completed_tasks,
            "current_task": self.current_task,
            "tool_results": self.tool_results,
            "target_context": self.target_context,
            "vulnerabilities": self.vulnerabilities,
            "new_poc_tasks": self.new_poc_tasks,
            "awvs_required": self.awvs_required,
            "errors": self.errors,
            "retry_count": self.retry_count,
            "execution_time": self.execution_time
        }


class ToolExecutionNode:
    """
    工具执行节点
    
    执行当前规划的任务，调用相应的工具并更新状态。
    """
    
    def __init__(self, max_concurrent: int = 3):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        logger.info(f"🔧 工具执行节点初始化, 最大并发: {max_concurrent}")
    
    async def __call__(self, state: ToolExecutionState) -> ToolExecutionState:
        if not state.current_task:
            logger.info(f"[{state.task_id}] ⏹️ 没有待执行任务")
            return state
        
        tool_name = state.current_task
        logger.info(f"[{state.task_id}] 🔧 执行工具: {tool_name}")
        
        try:
            async with self.semaphore:
                from ..tools.registry import registry
                
                logger.info(f"[{state.task_id}] 🚀 开始执行插件: {tool_name}")
                result = await registry.call_tool(tool_name, state.target)
                
                if result.get("status") == "success":
                    state.tool_results[tool_name] = result
                    self._update_context(state, tool_name, result)
                    
                    if tool_name.startswith("poc_") and result.get("data", {}).get("vulnerable"):
                        self._process_poc_result(state, tool_name, result)
                    
                    state.completed_tasks.append(tool_name)
                    if tool_name in state.planned_tasks:
                        state.planned_tasks.remove(tool_name)
                    
                    logger.info(f"[{state.task_id}] ✅ 工具 {tool_name} 执行完成")
                else:
                    error_msg = result.get("error", "未知错误")
                    logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 执行失败: {error_msg}")
                    state.errors.append(f"工具执行失败 {tool_name}: {error_msg}")
                    state.retry_count += 1
                    
                    if state.retry_count >= state.max_retries:
                        state.completed_tasks.append(tool_name)
                        if tool_name in state.planned_tasks:
                            state.planned_tasks.remove(tool_name)
                        state.retry_count = 0
                        
        except ValueError as e:
            logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 不存在: {str(e)}")
            state.errors.append(f"工具不存在: {tool_name}")
            state.completed_tasks.append(tool_name)
            if tool_name in state.planned_tasks:
                state.planned_tasks.remove(tool_name)
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 执行异常: {str(e)}")
            state.errors.append(f"工具执行异常 {tool_name}: {str(e)}")
            state.retry_count += 1
        
        state.current_task = state.planned_tasks[0] if state.planned_tasks else None
        return state
    
    def _update_context(self, state: ToolExecutionState, tool_name: str, result: Dict[str, Any]):
        if result.get("status") != "success":
            return
        
        data = result.get("data", {})
        if not isinstance(data, dict):
            return
        
        context_mapping = {
            "baseinfo": {"server": data.get("server"), "os": data.get("os"), "ip": data.get("ip")},
            "cms_identify": {"cms": data.get("cms", "unknown")},
            "portscan": {"open_ports": data.get("open_ports", [])},
            "waf_detect": {"waf": data.get("waf")},
            "cdn_detect": {"cdn": data.get("has_cdn")}
        }
        
        if tool_name in context_mapping:
            for key, value in context_mapping[tool_name].items():
                if value is not None:
                    state.target_context[key] = value
    
    def _process_poc_result(self, state: ToolExecutionState, tool_name: str, result: Dict[str, Any]):
        data = result.get("data", {})
        if data.get("vulnerable"):
            vuln_info = {
                "cve": tool_name.replace("poc_", ""),
                "target": state.target,
                "severity": "high",
                "details": data.get("message", ""),
                "poc_name": tool_name
            }
            state.vulnerabilities.append(vuln_info)
            logger.warning(f"[{state.task_id}] 🚨 发现漏洞: {vuln_info}")


class ResultVerificationNode:
    """
    结果验证节点
    
    验证工具执行结果，决定是否继续执行。
    """
    
    def __init__(self, max_rounds: int = 50):
        self.max_rounds = max_rounds
    
    def __call__(self, state: ToolExecutionState) -> str:
        state._round += 1
        
        if state._round >= self.max_rounds:
            logger.warning(f"[{state.task_id}] ⚠️ 达到最大执行轮次: {self.max_rounds}")
            return "analyze"
        
        if state.planned_tasks:
            logger.info(f"[{state.task_id}] 🔄 继续执行, 剩余任务: {len(state.planned_tasks)}")
            return "continue"
        
        if state.new_poc_tasks:
            logger.info(f"[{state.task_id}] 📋 发现新POC任务: {len(state.new_poc_tasks)}")
            return "poc_verify"
        
        if state.target_context.get("use_awvs") and not state.awvs_required:
            state.awvs_required = True
            logger.info(f"[{state.task_id}] 🔍 需要AWVS扫描")
            return "awvs_scan"
        
        logger.info(f"[{state.task_id}] ✅ 所有任务完成")
        return "analyze"


class ToolExecutionGraph:
    """
    工具执行图
    
    执行固定工具扫描任务。
    """
    
    def __init__(self, max_execution_time: float = 120.0, max_rounds: int = 50):
        self.max_execution_time = max_execution_time
        self.max_rounds = max_rounds
        self.execution_node = ToolExecutionNode()
        self.verification_node = ResultVerificationNode(max_rounds)
        logger.info(f"📊 ToolExecutionGraph 初始化, 最大执行时间: {max_execution_time}s, 最大轮次: {max_rounds}")
    
    async def execute(self, state: ToolExecutionState) -> ToolExecutionState:
        """
        执行工具扫描
        
        Args:
            state: 工具执行状态
            
        Returns:
            ToolExecutionState: 更新后的状态
        """
        start_time = time.time()
        logger.info(f"[{state.task_id}] 🚀 开始工具执行图")
        
        try:
            while state.planned_tasks:
                if time.time() - start_time > self.max_execution_time:
                    logger.warning(f"[{state.task_id}] ⚠️ 工具执行超时")
                    break
                
                state = await self.execution_node(state)
                
                decision = self.verification_node(state)
                
                if decision == "analyze":
                    break
                elif decision == "poc_verify":
                    break
                elif decision == "awvs_scan":
                    break
            
            total_time = time.time() - start_time
            state.execution_time = total_time
            
            if total_time > self.max_execution_time:
                logger.warning(f"[{state.task_id}] ⚠️ ToolExecutionGraph 执行超时: {total_time:.2f}s")
            else:
                logger.info(f"[{state.task_id}] ✅ ToolExecutionGraph 执行完成, 耗时: {total_time:.2f}s")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ ToolExecutionGraph 执行失败: {str(e)}")
            state.errors.append(f"工具执行图失败: {str(e)}")
        
        return state
    
    def get_result_dto(self, state: ToolExecutionState) -> 'ToolExecutionResultDTO':
        """
        将状态转换为ToolExecutionResultDTO
        
        Args:
            state: 工具执行状态
            
        Returns:
            ToolExecutionResultDTO: 工具执行结果DTO
        """
        from .dto import ToolExecutionResultDTO, TaskStatus
        
        status = TaskStatus.COMPLETED if not state.errors else TaskStatus.FAILED
        
        return ToolExecutionResultDTO(
            task_id=state.task_id,
            target=state.target,
            status=status,
            tool_results=state.tool_results,
            findings=state.vulnerabilities,
            new_poc_tasks=state.new_poc_tasks,
            awvs_required=state.awvs_required,
            target_context=state.target_context,
            total_execution_time=state.execution_time
        )

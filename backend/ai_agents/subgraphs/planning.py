"""
规划子图

负责环境感知、任务规划和扫描策略决策。
执行时间目标: < 10秒
"""
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PlanningState:
    """
    规划状态
    
    PlanningGraph专用的轻量级状态类。
    """
    target: str
    task_id: str
    target_context: Dict[str, Any] = field(default_factory=dict)
    env_info: Dict[str, Any] = field(default_factory=dict)
    planned_tasks: List[str] = field(default_factory=list)
    decision: str = "fixed_tool"
    need_custom_scan: bool = False
    custom_scan_type: Optional[str] = None
    custom_scan_requirements: Optional[str] = None
    need_capability_enhancement: bool = False
    capability_requirement: Optional[str] = None
    need_seebug: bool = False
    use_awvs: bool = False
    poc_tasks: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "task_id": self.task_id,
            "target_context": self.target_context,
            "env_info": self.env_info,
            "planned_tasks": self.planned_tasks,
            "decision": self.decision,
            "need_custom_scan": self.need_custom_scan,
            "custom_scan_type": self.custom_scan_type,
            "custom_scan_requirements": self.custom_scan_requirements,
            "need_capability_enhancement": self.need_capability_enhancement,
            "capability_requirement": self.capability_requirement,
            "need_seebug": self.need_seebug,
            "use_awvs": self.use_awvs,
            "poc_tasks": self.poc_tasks,
            "errors": self.errors,
            "execution_time": self.execution_time
        }


class EnvironmentAwarenessNode:
    """
    环境感知节点
    
    获取运行环境信息，包括操作系统、Python版本、可用工具等。
    """
    
    def __init__(self):
        self.timeout = 5.0
    
    async def __call__(self, state: PlanningState) -> PlanningState:
        start_time = time.time()
        logger.info(f"[{state.task_id}] 🔍 开始环境感知: {state.target}")
        
        try:
            from ..code_execution.environment import EnvironmentAwareness
            
            env_awareness = EnvironmentAwareness()
            env_info = env_awareness.get_environment_report()
            
            state.env_info = env_info
            state.target_context["env_info"] = env_info
            
            logger.info(f"[{state.task_id}] ✅ 环境感知完成")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 环境感知失败: {str(e)}")
            state.errors.append(f"环境感知失败: {str(e)}")
            state.env_info = {"error": str(e)}
        
        state.execution_time += time.time() - start_time
        return state


class TaskPlanningNode:
    """
    任务规划节点
    
    根据目标特征和用户需求生成扫描任务计划。
    """
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self.timeout = 10.0
    
    async def __call__(self, state: PlanningState) -> PlanningState:
        start_time = time.time()
        logger.info(f"[{state.task_id}] 📋 开始任务规划")
        
        try:
            from ..agent_config import agent_config
            
            if state.target_context.get("custom_tasks"):
                state.planned_tasks = state.target_context["custom_tasks"]
                logger.info(f"[{state.task_id}] 使用自定义任务列表: {state.planned_tasks}")
            else:
                state.planned_tasks = agent_config.DEFAULT_SCAN_TASKS.copy()
                logger.info(f"[{state.task_id}] 使用默认任务列表: {state.planned_tasks}")
            
            logger.info(f"[{state.task_id}] ✅ 任务规划完成: {state.planned_tasks}")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 任务规划失败: {str(e)}")
            state.errors.append(f"任务规划失败: {str(e)}")
            state.planned_tasks = ["baseinfo", "portscan"]
        
        state.execution_time += time.time() - start_time
        return state


class IntelligentDecisionNode:
    """
    智能决策节点
    
    根据规划结果决定扫描策略。
    """
    
    def __init__(self):
        self.timeout = 5.0
    
    async def __call__(self, state: PlanningState) -> PlanningState:
        start_time = time.time()
        logger.info(f"[{state.task_id}] 🧠 开始智能决策")
        
        try:
            if state.poc_tasks and len(state.poc_tasks) > 0:
                state.decision = "poc_verification"
                logger.info(f"[{state.task_id}] 决策: POC验证")
            elif state.need_capability_enhancement:
                state.decision = "enhance_first"
                logger.info(f"[{state.task_id}] 决策: 功能增强优先")
            elif state.need_custom_scan:
                state.decision = "custom_code"
                logger.info(f"[{state.task_id}] 决策: 自定义代码扫描")
            elif state.need_seebug:
                state.decision = "seebug_agent"
                logger.info(f"[{state.task_id}] 决策: Seebug Agent")
            elif state.use_awvs or "awvs" in state.planned_tasks:
                non_awvs_tasks = [t for t in state.planned_tasks if t != 'awvs']
                if non_awvs_tasks:
                    state.decision = "fixed_tool"
                else:
                    state.decision = "awvs_scan"
                logger.info(f"[{state.task_id}] 决策: {'AWVS扫描' if state.decision == 'awvs_scan' else '固定工具扫描'}")
            else:
                state.decision = "fixed_tool"
                logger.info(f"[{state.task_id}] 决策: 固定工具扫描")
            
            logger.info(f"[{state.task_id}] ✅ 智能决策完成: {state.decision}")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 智能决策失败: {str(e)}")
            state.errors.append(f"智能决策失败: {str(e)}")
            state.decision = "fixed_tool"
        
        state.execution_time += time.time() - start_time
        return state


class PlanningGraph:
    """
    规划图
    
    负责环境感知、任务规划和扫描策略决策。
    执行时间目标: < 10秒
    
    节点流程:
    environment_awareness → task_planning → intelligent_decision
    """
    
    def __init__(self, use_llm_planning: bool = False):
        self.env_node = EnvironmentAwarenessNode()
        self.planning_node = TaskPlanningNode(use_llm=use_llm_planning)
        self.decision_node = IntelligentDecisionNode()
        
        self.max_execution_time = 10.0
        
        logger.info("🏗️ PlanningGraph 初始化完成")
    
    async def run(self, target: str, task_id: str, target_context: Dict[str, Any] = None) -> PlanningState:
        """
        执行规划图
        
        Args:
            target: 扫描目标
            task_id: 任务ID
            target_context: 目标上下文
            
        Returns:
            PlanningState: 规划结果状态
        """
        start_time = time.time()
        
        state = PlanningState(
            target=target,
            task_id=task_id,
            target_context=target_context or {}
        )
        
        logger.info(f"[{task_id}] 🚀 PlanningGraph 开始执行, 目标: {target}")
        
        try:
            state = await self.env_node(state)
            
            if state.need_capability_enhancement is None:
                state.need_capability_enhancement = target_context.get("need_capability_enhancement", False) if target_context else False
            if state.need_custom_scan is None:
                state.need_custom_scan = target_context.get("need_custom_scan", False) if target_context else False
            if state.need_seebug is None:
                state.need_seebug = target_context.get("need_seebug_agent", False) if target_context else False
            if state.use_awvs is None:
                state.use_awvs = target_context.get("use_awvs", False) if target_context else False
            
            state.poc_tasks = target_context.get("poc_verification_tasks", []) if target_context else []
            
            state = await self.planning_node(state)
            
            state = await self.decision_node(state)
            
            total_time = time.time() - start_time
            state.execution_time = total_time
            
            if total_time > self.max_execution_time:
                logger.warning(f"[{task_id}] ⚠️ PlanningGraph 执行超时: {total_time:.2f}s > {self.max_execution_time}s")
            else:
                logger.info(f"[{task_id}] ✅ PlanningGraph 执行完成, 耗时: {total_time:.2f}s")
            
        except Exception as e:
            logger.error(f"[{task_id}] ❌ PlanningGraph 执行失败: {str(e)}")
            state.errors.append(f"规划图执行失败: {str(e)}")
            state.decision = "fixed_tool"
        
        return state
    
    def get_scan_plan_dto(self, state: PlanningState) -> 'ScanPlanDTO':
        """
        将规划状态转换为ScanPlanDTO
        
        Args:
            state: 规划状态
            
        Returns:
            ScanPlanDTO: 扫描计划DTO
        """
        from .dto import ScanPlanDTO, ScanDecisionType
        
        decision_map = {
            "fixed_tool": ScanDecisionType.FIXED_TOOL,
            "custom_code": ScanDecisionType.CUSTOM_CODE,
            "enhance_first": ScanDecisionType.ENHANCE_FIRST,
            "poc_verification": ScanDecisionType.POC_VERIFICATION,
            "seebug_agent": ScanDecisionType.SEEBUG_AGENT,
            "awvs_scan": ScanDecisionType.AWVS_SCAN
        }
        
        return ScanPlanDTO(
            target=state.target,
            task_id=state.task_id,
            decision=decision_map.get(state.decision, ScanDecisionType.FIXED_TOOL),
            tool_tasks=state.planned_tasks,
            poc_tasks=state.poc_tasks,
            need_custom_scan=state.need_custom_scan,
            custom_scan_type=state.custom_scan_type,
            custom_scan_requirements=state.custom_scan_requirements,
            need_capability_enhancement=state.need_capability_enhancement,
            capability_requirement=state.capability_requirement,
            need_seebug=state.need_seebug,
            use_awvs=state.use_awvs,
            target_context=state.target_context
        )

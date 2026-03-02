"""
任务路由器模块

负责评估任务复杂度并决定使用子图还是大图执行。
通过智能分析任务特征，优化执行效率和资源利用。
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Literal

from .state import AgentState

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """
    任务复杂度枚举
    
    定义任务的复杂程度级别。
    """
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class ExecutionMode(Enum):
    """
    执行模式枚举
    
    定义任务执行的模式。
    """
    SUBGRAPH = "subgraph"
    FULLGRAPH = "fullgraph"
    HYBRID = "hybrid"


class TaskType(Enum):
    """
    任务类型枚举
    
    定义不同类型的任务。
    """
    INFO_GATHERING = "info_gathering"
    VULNERABILITY_SCAN = "vulnerability_scan"
    POC_VERIFICATION = "poc_verification"
    CODE_GENERATION = "code_generation"
    CAPABILITY_ENHANCEMENT = "capability_enhancement"
    REPORT_GENERATION = "report_generation"
    AWVS_SCAN = "awvs_scan"
    SEEBUG_AGENT = "seebug_agent"


@dataclass
class ComplexityFactors:
    """
    复杂度因素数据类
    
    存储影响任务复杂度的各种因素。
    
    Attributes:
        task_type_count: 任务类型数量
        requires_ai_decision: 是否需要AI决策
        requires_code_generation: 是否需要代码生成
        requires_code_execution: 是否需要代码执行
        requires_capability_enhancement: 是否需要功能增强
        requires_external_api: 是否需要外部API调用
        estimated_execution_time: 预估执行时间（秒）
        dependency_count: 依赖数量
        risk_level: 风险级别（1-10）
    """
    task_type_count: int = 0
    requires_ai_decision: bool = False
    requires_code_generation: bool = False
    requires_code_execution: bool = False
    requires_capability_enhancement: bool = False
    requires_external_api: bool = False
    estimated_execution_time: float = 0.0
    dependency_count: int = 0
    risk_level: int = 1


@dataclass
class RoutingDecision:
    """
    路由决策数据类
    
    存储路由决策的结果和原因。
    
    Attributes:
        task_id: 任务ID
        execution_mode: 执行模式
        complexity: 任务复杂度
        factors: 复杂度因素
        reasoning: 决策原因
        timestamp: 决策时间戳
        confidence: 决策置信度（0-1）
        fallback_mode: 降级模式
    """
    task_id: str
    execution_mode: ExecutionMode
    complexity: TaskComplexity
    factors: ComplexityFactors
    reasoning: str
    timestamp: float = field(default_factory=time.time)
    confidence: float = 1.0
    fallback_mode: Optional[ExecutionMode] = None


@dataclass
class RoutingLog:
    """
    路由日志数据类
    
    记录路由决策的详细日志信息。
    
    Attributes:
        task_id: 任务ID
        decision: 路由决策
        log_level: 日志级别
        message: 日志消息
        details: 详细信息
        timestamp: 时间戳
    """
    task_id: str
    decision: RoutingDecision
    log_level: str = "INFO"
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class TaskRouter:
    """
    任务路由器类
    
    负责评估任务复杂度并决定使用子图还是大图执行。
    通过智能分析任务特征，优化执行效率和资源利用。
    
    核心功能:
    - 任务复杂度评估：根据多种因素评估任务复杂度
    - 路由决策：基于复杂度选择最优执行模式
    - 降级机制：提供执行失败时的降级策略
    - 日志记录：记录所有路由决策及其原因
    
    Attributes:
        routing_history: 路由历史记录
        decision_logs: 决策日志列表
        complexity_thresholds: 复杂度阈值配置
    """
    
    def __init__(
        self,
        simple_threshold: float = 0.3,
        complex_threshold: float = 0.7,
        enable_fallback: bool = True
    ):
        """
        初始化任务路由器
        
        Args:
            simple_threshold: 简单任务阈值（0-1）
            complex_threshold: 复杂任务阈值（0-1）
            enable_fallback: 是否启用降级机制
        """
        self.simple_threshold = simple_threshold
        self.complex_threshold = complex_threshold
        self.enable_fallback = enable_fallback
        
        self.routing_history: Dict[str, RoutingDecision] = {}
        self.decision_logs: List[RoutingLog] = []
        
        self.complexity_weights = {
            "task_type_count": 0.15,
            "ai_decision": 0.20,
            "code_generation": 0.15,
            "code_execution": 0.10,
            "capability_enhancement": 0.15,
            "external_api": 0.10,
            "execution_time": 0.10,
            "dependency_count": 0.05
        }
        
        self.task_type_mapping = {
            "baseinfo": TaskType.INFO_GATHERING,
            "portscan": TaskType.INFO_GATHERING,
            "waf_detect": TaskType.INFO_GATHERING,
            "cdn_detect": TaskType.INFO_GATHERING,
            "cms_identify": TaskType.INFO_GATHERING,
            "infoleak_scan": TaskType.INFO_GATHERING,
            "subdomain_scan": TaskType.INFO_GATHERING,
            "webside_scan": TaskType.INFO_GATHERING,
            "webweight_scan": TaskType.INFO_GATHERING,
            "awvs": TaskType.AWVS_SCAN,
            "seebug_agent": TaskType.SEEBUG_AGENT,
        }
        
        logger.info("🔀 任务路由器初始化完成")
        logger.debug(f"   - 简单任务阈值: {simple_threshold}")
        logger.debug(f"   - 复杂任务阈值: {complex_threshold}")
        logger.debug(f"   - 降级机制: {'启用' if enable_fallback else '禁用'}")
    
    async def analyze_task(self, state: AgentState) -> ComplexityFactors:
        """
        分析任务复杂度因素
        
        根据任务状态分析各种影响复杂度的因素。
        
        Args:
            state: Agent当前状态
            
        Returns:
            ComplexityFactors: 复杂度因素分析结果
        """
        logger.info(f"[{state.task_id}] 🔍 开始分析任务复杂度")
        
        factors = ComplexityFactors()
        
        task_types = set()
        for task in state.planned_tasks:
            task_type = self.task_type_mapping.get(task)
            if task_type:
                task_types.add(task_type)
            elif task.startswith("poc_"):
                task_types.add(TaskType.POC_VERIFICATION)
            else:
                task_types.add(TaskType.VULNERABILITY_SCAN)
        
        factors.task_type_count = len(task_types)
        logger.debug(f"[{state.task_id}]   - 任务类型数量: {factors.task_type_count}")
        
        target_context = state.target_context
        
        factors.requires_ai_decision = bool(
            target_context.get("need_custom_scan") or
            target_context.get("need_seebug_agent") or
            len(state.poc_verification_tasks) > 0
        )
        logger.debug(f"[{state.task_id}]   - 需要AI决策: {factors.requires_ai_decision}")
        
        factors.requires_code_generation = bool(
            target_context.get("need_custom_scan") or
            target_context.get("need_code_generation")
        )
        logger.debug(f"[{state.task_id}]   - 需要代码生成: {factors.requires_code_generation}")
        
        factors.requires_code_execution = bool(
            target_context.get("generated_code") or
            factors.requires_code_generation
        )
        logger.debug(f"[{state.task_id}]   - 需要代码执行: {factors.requires_code_execution}")
        
        factors.requires_capability_enhancement = bool(
            target_context.get("need_capability_enhancement")
        )
        logger.debug(f"[{state.task_id}]   - 需要功能增强: {factors.requires_capability_enhancement}")
        
        factors.requires_external_api = bool(
            TaskType.AWVS_SCAN in task_types or
            TaskType.SEEBUG_AGENT in task_types or
            target_context.get("use_awvs")
        )
        logger.debug(f"[{state.task_id}]   - 需要外部API: {factors.requires_external_api}")
        
        factors.estimated_execution_time = self._estimate_execution_time(
            state.planned_tasks,
            task_types,
            factors
        )
        logger.debug(f"[{state.task_id}]   - 预估执行时间: {factors.estimated_execution_time:.1f}秒")
        
        factors.dependency_count = self._count_dependencies(state)
        logger.debug(f"[{state.task_id}]   - 依赖数量: {factors.dependency_count}")
        
        factors.risk_level = self._assess_risk_level(state, factors)
        logger.debug(f"[{state.task_id}]   - 风险级别: {factors.risk_level}/10")
        
        logger.info(f"[{state.task_id}] ✅ 任务复杂度分析完成")
        
        return factors
    
    def _estimate_execution_time(
        self,
        planned_tasks: List[str],
        task_types: set,
        factors: ComplexityFactors
    ) -> float:
        """
        预估任务执行时间
        
        Args:
            planned_tasks: 计划任务列表
            task_types: 任务类型集合
            factors: 复杂度因素
            
        Returns:
            float: 预估执行时间（秒）
        """
        base_time = 0.0
        
        task_time_mapping = {
            TaskType.INFO_GATHERING: 30.0,
            TaskType.VULNERABILITY_SCAN: 60.0,
            TaskType.POC_VERIFICATION: 45.0,
            TaskType.CODE_GENERATION: 30.0,
            TaskType.CODE_EXECUTION: 20.0,
            TaskType.CAPABILITY_ENHANCEMENT: 60.0,
            TaskType.REPORT_GENERATION: 10.0,
            TaskType.AWVS_SCAN: 300.0,
            TaskType.SEEBUG_AGENT: 60.0,
        }
        
        for task_type in task_types:
            base_time += task_time_mapping.get(task_type, 30.0)
        
        if factors.requires_ai_decision:
            base_time += 20.0
        
        if factors.requires_code_generation:
            base_time += 30.0
        
        if factors.requires_capability_enhancement:
            base_time += 60.0
        
        task_count = len(planned_tasks)
        if task_count > 5:
            base_time *= (1 + (task_count - 5) * 0.1)
        
        return base_time
    
    def _count_dependencies(self, state: AgentState) -> int:
        """
        计算任务依赖数量
        
        Args:
            state: Agent当前状态
            
        Returns:
            int: 依赖数量
        """
        count = 0
        
        target_context = state.target_context
        
        if target_context.get("cms"):
            count += 1
        if target_context.get("open_ports"):
            count += len(target_context.get("open_ports", []))
        if target_context.get("waf"):
            count += 1
        if target_context.get("cdn"):
            count += 1
        
        count += len(state.poc_verification_tasks)
        
        return count
    
    def _assess_risk_level(
        self,
        state: AgentState,
        factors: ComplexityFactors
    ) -> int:
        """
        评估任务风险级别
        
        Args:
            state: Agent当前状态
            factors: 复杂度因素
            
        Returns:
            int: 风险级别（1-10）
        """
        risk = 1
        
        if factors.requires_code_execution:
            risk += 2
        
        if factors.requires_capability_enhancement:
            risk += 2
        
        if factors.requires_external_api:
            risk += 1
        
        if len(state.errors) > 0:
            risk += 1
        
        if state.retry_count > 0:
            risk += 1
        
        if factors.estimated_execution_time > 300:
            risk += 1
        
        return min(risk, 10)
    
    def calculate_complexity_score(self, factors: ComplexityFactors) -> float:
        """
        计算复杂度分数
        
        基于各种因素计算任务的复杂度分数（0-1）。
        
        Args:
            factors: 复杂度因素
            
        Returns:
            float: 复杂度分数（0-1）
        """
        score = 0.0
        
        task_type_score = min(factors.task_type_count / 5.0, 1.0)
        score += task_type_score * self.complexity_weights["task_type_count"]
        
        if factors.requires_ai_decision:
            score += 1.0 * self.complexity_weights["ai_decision"]
        
        if factors.requires_code_generation:
            score += 1.0 * self.complexity_weights["code_generation"]
        
        if factors.requires_code_execution:
            score += 1.0 * self.complexity_weights["code_execution"]
        
        if factors.requires_capability_enhancement:
            score += 1.0 * self.complexity_weights["capability_enhancement"]
        
        if factors.requires_external_api:
            score += 1.0 * self.complexity_weights["external_api"]
        
        time_score = min(factors.estimated_execution_time / 600.0, 1.0)
        score += time_score * self.complexity_weights["execution_time"]
        
        dep_score = min(factors.dependency_count / 10.0, 1.0)
        score += dep_score * self.complexity_weights["dependency_count"]
        
        return min(score, 1.0)
    
    def determine_complexity(self, score: float) -> TaskComplexity:
        """
        根据分数确定任务复杂度级别
        
        Args:
            score: 复杂度分数（0-1）
            
        Returns:
            TaskComplexity: 任务复杂度级别
        """
        if score < self.simple_threshold:
            return TaskComplexity.SIMPLE
        elif score >= self.complex_threshold:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.MEDIUM
    
    def determine_execution_mode(
        self,
        complexity: TaskComplexity,
        factors: ComplexityFactors
    ) -> ExecutionMode:
        """
        确定执行模式
        
        根据任务复杂度和因素确定最优执行模式。
        
        Args:
            complexity: 任务复杂度
            factors: 复杂度因素
            
        Returns:
            ExecutionMode: 执行模式
        """
        if complexity == TaskComplexity.SIMPLE:
            if factors.task_type_count == 1 and not factors.requires_ai_decision:
                return ExecutionMode.SUBGRAPH
            else:
                return ExecutionMode.HYBRID
        
        elif complexity == TaskComplexity.COMPLEX:
            return ExecutionMode.FULLGRAPH
        
        else:
            if factors.requires_ai_decision or factors.requires_code_generation:
                return ExecutionMode.FULLGRAPH
            elif factors.task_type_count <= 2:
                return ExecutionMode.SUBGRAPH
            else:
                return ExecutionMode.HYBRID
    
    def get_fallback_mode(
        self,
        current_mode: ExecutionMode,
        failure_reason: str
    ) -> Optional[ExecutionMode]:
        """
        获取降级执行模式
        
        当执行失败时，提供降级策略。
        
        Args:
            current_mode: 当前执行模式
            failure_reason: 失败原因
            
        Returns:
            Optional[ExecutionMode]: 降级模式，如果无法降级则返回None
        """
        if not self.enable_fallback:
            return None
        
        fallback_mapping = {
            ExecutionMode.SUBGRAPH: None,
            ExecutionMode.HYBRID: ExecutionMode.SUBGRAPH,
            ExecutionMode.FULLGRAPH: ExecutionMode.HYBRID,
        }
        
        fallback = fallback_mapping.get(current_mode)
        
        if fallback:
            logger.warning(f"⚠️ 执行失败，降级模式: {current_mode.value} -> {fallback.value}")
            logger.warning(f"   失败原因: {failure_reason}")
        
        return fallback
    
    async def route(self, state: AgentState) -> RoutingDecision:
        """
        执行路由决策
        
        分析任务并决定最优执行模式。
        
        Args:
            state: Agent当前状态
            
        Returns:
            RoutingDecision: 路由决策结果
        """
        logger.info(f"[{state.task_id}] 🔀 开始路由决策")
        
        factors = await self.analyze_task(state)
        
        score = self.calculate_complexity_score(factors)
        logger.info(f"[{state.task_id}] 📊 复杂度分数: {score:.2f}")
        
        complexity = self.determine_complexity(score)
        logger.info(f"[{state.task_id}] 📊 复杂度级别: {complexity.value}")
        
        execution_mode = self.determine_execution_mode(complexity, factors)
        logger.info(f"[{state.task_id}] 📊 执行模式: {execution_mode.value}")
        
        reasoning = self._generate_reasoning(factors, complexity, execution_mode)
        
        fallback_mode = None
        if self.enable_fallback and execution_mode != ExecutionMode.SUBGRAPH:
            fallback_mode = self.get_fallback_mode(execution_mode, "preparation")
        
        decision = RoutingDecision(
            task_id=state.task_id,
            execution_mode=execution_mode,
            complexity=complexity,
            factors=factors,
            reasoning=reasoning,
            confidence=self._calculate_confidence(factors),
            fallback_mode=fallback_mode
        )
        
        self.routing_history[state.task_id] = decision
        
        self._log_decision(decision)
        
        logger.info(f"[{state.task_id}] ✅ 路由决策完成: {execution_mode.value}")
        logger.info(f"[{state.task_id}]    原因: {reasoning}")
        
        return decision
    
    def _generate_reasoning(
        self,
        factors: ComplexityFactors,
        complexity: TaskComplexity,
        execution_mode: ExecutionMode
    ) -> str:
        """
        生成决策原因说明
        
        Args:
            factors: 复杂度因素
            complexity: 任务复杂度
            execution_mode: 执行模式
            
        Returns:
            str: 决策原因说明
        """
        reasons = []
        
        if factors.task_type_count == 1:
            reasons.append("单一任务类型")
        elif factors.task_type_count <= 3:
            reasons.append(f"少量任务类型({factors.task_type_count}个)")
        else:
            reasons.append(f"多种任务类型({factors.task_type_count}个)")
        
        if factors.requires_ai_decision:
            reasons.append("需要AI决策")
        
        if factors.requires_code_generation:
            reasons.append("需要代码生成")
        
        if factors.requires_code_execution:
            reasons.append("需要代码执行")
        
        if factors.requires_capability_enhancement:
            reasons.append("需要功能增强")
        
        if factors.requires_external_api:
            reasons.append("需要外部API调用")
        
        if factors.estimated_execution_time > 300:
            reasons.append(f"预估执行时间较长({factors.estimated_execution_time:.0f}秒)")
        
        mode_reasons = {
            ExecutionMode.SUBGRAPH: "使用子图执行以提高效率",
            ExecutionMode.HYBRID: "使用混合模式平衡效率和功能",
            ExecutionMode.FULLGRAPH: "使用完整图以确保功能完整性"
        }
        
        reasons.append(mode_reasons[execution_mode])
        
        return "；".join(reasons)
    
    def _calculate_confidence(self, factors: ComplexityFactors) -> float:
        """
        计算决策置信度
        
        Args:
            factors: 复杂度因素
            
        Returns:
            float: 置信度（0-1）
        """
        confidence = 1.0
        
        if factors.task_type_count > 5:
            confidence -= 0.1
        
        if factors.risk_level > 7:
            confidence -= 0.1
        
        if factors.estimated_execution_time > 600:
            confidence -= 0.1
        
        return max(confidence, 0.5)
    
    def _log_decision(self, decision: RoutingDecision) -> None:
        """
        记录路由决策日志
        
        Args:
            decision: 路由决策
        """
        log = RoutingLog(
            task_id=decision.task_id,
            decision=decision,
            log_level="INFO",
            message=f"路由决策: {decision.execution_mode.value}",
            details={
                "complexity": decision.complexity.value,
                "complexity_score": self.calculate_complexity_score(decision.factors),
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "factors": {
                    "task_type_count": decision.factors.task_type_count,
                    "requires_ai_decision": decision.factors.requires_ai_decision,
                    "requires_code_generation": decision.factors.requires_code_generation,
                    "requires_code_execution": decision.factors.requires_code_execution,
                    "requires_capability_enhancement": decision.factors.requires_capability_enhancement,
                    "requires_external_api": decision.factors.requires_external_api,
                    "estimated_execution_time": decision.factors.estimated_execution_time,
                    "dependency_count": decision.factors.dependency_count,
                    "risk_level": decision.factors.risk_level
                }
            }
        )
        
        self.decision_logs.append(log)
        
        timestamp = datetime.fromtimestamp(decision.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{decision.task_id}] 📝 路由决策日志")
        logger.info(f"   - 时间: {timestamp}")
        logger.info(f"   - 模式: {decision.execution_mode.value}")
        logger.info(f"   - 复杂度: {decision.complexity.value}")
        logger.info(f"   - 置信度: {decision.confidence:.2f}")
        logger.info(f"   - 原因: {decision.reasoning}")
    
    def get_routing_history(self, task_id: str) -> Optional[RoutingDecision]:
        """
        获取指定任务的路由历史
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[RoutingDecision]: 路由决策，如果不存在则返回None
        """
        return self.routing_history.get(task_id)
    
    def get_all_routing_history(self) -> Dict[str, RoutingDecision]:
        """
        获取所有路由历史
        
        Returns:
            Dict[str, RoutingDecision]: 所有路由决策
        """
        return self.routing_history.copy()
    
    def get_decision_logs(
        self,
        task_id: Optional[str] = None,
        limit: int = 100
    ) -> List[RoutingLog]:
        """
        获取决策日志
        
        Args:
            task_id: 任务ID，如果为None则返回所有日志
            limit: 返回日志数量限制
            
        Returns:
            List[RoutingLog]: 决策日志列表
        """
        if task_id:
            logs = [log for log in self.decision_logs if log.task_id == task_id]
        else:
            logs = self.decision_logs
        
        return logs[-limit:]
    
    def clear_history(self, task_id: Optional[str] = None) -> None:
        """
        清除路由历史
        
        Args:
            task_id: 任务ID，如果为None则清除所有历史
        """
        if task_id:
            self.routing_history.pop(task_id, None)
            self.decision_logs = [
                log for log in self.decision_logs if log.task_id != task_id
            ]
            logger.info(f"🗑️ 已清除任务 {task_id} 的路由历史")
        else:
            self.routing_history.clear()
            self.decision_logs.clear()
            logger.info("🗑️ 已清除所有路由历史")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取路由统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_decisions = len(self.routing_history)
        
        if total_decisions == 0:
            return {
                "total_decisions": 0,
                "message": "暂无路由决策记录"
            }
        
        mode_counts = {}
        complexity_counts = {}
        total_confidence = 0.0
        total_execution_time = 0.0
        
        for decision in self.routing_history.values():
            mode = decision.execution_mode.value
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
            
            complexity = decision.complexity.value
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
            
            total_confidence += decision.confidence
            total_execution_time += decision.factors.estimated_execution_time
        
        return {
            "total_decisions": total_decisions,
            "execution_mode_distribution": mode_counts,
            "complexity_distribution": complexity_counts,
            "average_confidence": total_confidence / total_decisions,
            "average_estimated_time": total_execution_time / total_decisions,
            "total_logs": len(self.decision_logs)
        }


async def create_task_router(
    simple_threshold: float = 0.3,
    complex_threshold: float = 0.7,
    enable_fallback: bool = True
) -> TaskRouter:
    """
    创建任务路由器实例
    
    Args:
        simple_threshold: 简单任务阈值（0-1）
        complex_threshold: 复杂任务阈值（0-1）
        enable_fallback: 是否启用降级机制
        
    Returns:
        TaskRouter: 任务路由器实例
    """
    return TaskRouter(
        simple_threshold=simple_threshold,
        complex_threshold=complex_threshold,
        enable_fallback=enable_fallback
    )

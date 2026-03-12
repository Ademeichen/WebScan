"""
LangGraph 图构建

构建支持自主规划、代码生成、环境感知的完整Agent工作流。

日志记录:
- 时间戳:所有日志包含时间戳
- 操作类型:节点进入/退出、状态变更、决策结果、错误信息
- 对象标识:任务ID、节点名称、状态键名
- 详细描述:操作的具体内容和结果
"""
import json
import logging
import time
from typing import Dict, Any, Literal, Optional, Union
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    TaskPlanningNode,
    ToolExecutionNode,
    ResultVerificationNode,
    VulnerabilityAnalysisNode,
    ReportGenerationNode,
    EnvironmentAwarenessNode,
    # CodeGenerationNode,
    # CapabilityEnhancementNode,
    # CodeExecutionNode,
    # IntelligentDecisionNode
)

from ..agent_config import agent_config

logger = logging.getLogger(__name__)


def _log_node_entry(node_name: str, task_id: str, details: Dict[str, Any] = None):
    """
    记录节点进入日志
    
    Args:
        node_name: 节点名称
        task_id: 任务ID
        details: 详细信息
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_msg = f"[{timestamp}] [NODE_ENTRY] 节点: {node_name}, 任务ID: {task_id}"
    if details:
        log_msg += f", 详情: {details}"
    logger.info(log_msg)
    logger.debug(f"[{timestamp}] [NODE_ENTRY_DEBUG] 节点: {node_name}, 完整详情: {json.dumps(details, ensure_ascii=False, default=str) if details else 'None'}")


def _log_node_exit(node_name: str, task_id: str, status: str, details: Dict[str, Any] = None):
    """
    记录节点退出日志
    
    Args:
        node_name: 节点名称
        task_id: 任务ID
        status: 退出状态(success/failed/skipped)
        details: 详细信息
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_msg = f"[{timestamp}] [NODE_EXIT] 节点: {node_name}, 任务ID: {task_id}, 状态: {status}"
    if details:
        log_msg += f", 详情: {details}"
    logger.info(log_msg)
    logger.debug(f"[{timestamp}] [NODE_EXIT_DEBUG] 节点: {node_name}, 完整详情: {json.dumps(details, ensure_ascii=False, default=str) if details else 'None'}")


def _log_state_change(task_id: str, key: str, old_value: Any, new_value: Any):
    """
    记录状态变更日志
    
    Args:
        task_id: 任务ID
        key: 状态键名
        old_value: 旧值
        new_value: 新值
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logger.info(f"[{timestamp}] [STATE_CHANGE] 任务ID: {task_id}, 键: {key}, 旧值: {old_value}, 新值: {new_value}")
    logger.debug(f"[{timestamp}] [STATE_CHANGE_DEBUG] 任务ID: {task_id}, 键: {key}, 旧值类型: {type(old_value).__name__}, 新值类型: {type(new_value).__name__}")


def _log_decision(task_id: str, decision_type: str, decision: str, reason: str = ""):
    """
    记录决策日志
    
    Args:
        task_id: 任务ID
        decision_type: 决策类型
        decision: 决策结果
        reason: 决策原因
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_msg = f"[{timestamp}] [DECISION] 任务ID: {task_id}, 类型: {decision_type}, 决策: {decision}"
    if reason:
        log_msg += f", 原因: {reason}"
    logger.info(log_msg)


def _log_edge_traversal(task_id: str, from_node: str, to_node: str, condition: str = "", state_snapshot: Dict[str, Any] = None):
    """
    记录边遍历日志
    
    Args:
        task_id: 任务ID
        from_node: 起始节点
        to_node: 目标节点
        condition: 条件说明
        state_snapshot: 状态快照
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_msg = f"[{timestamp}] [EDGE_TRAVERSAL] 任务ID: {task_id}, 边: {from_node} → {to_node}"
    if condition:
        log_msg += f", 条件: {condition}"
    logger.info(log_msg)
    if state_snapshot:
        logger.debug(f"[{timestamp}] [EDGE_STATE_SNAPSHOT] 任务ID: {task_id}, 状态快照: {json.dumps(state_snapshot, ensure_ascii=False, default=str)[:500]}")


def _log_data_flow(task_id: str, flow_type: str, source: str, data: Any, description: str = ""):
    """
    记录数据流转日志
    
    Args:
        task_id: 任务ID
        flow_type: 流转类型(input/output/transform)
        source: 数据来源
        data: 数据内容
        description: 描述
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    data_str = str(data)[:200] if data else "None"
    log_msg = f"[{timestamp}] [DATA_FLOW] 任务ID: {task_id}, 类型: {flow_type}, 来源: {source}, 数据: {data_str}"
    if description:
        log_msg += f", 描述: {description}"
    logger.debug(log_msg)


def _log_error(task_id: str, node_name: str, error: Exception, context: Dict[str, Any] = None):
    """
    记录错误日志
    
    Args:
        task_id: 任务ID
        node_name: 节点名称
        error: 异常对象
        context: 错误上下文
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_msg = f"[{timestamp}] [ERROR] 任务ID: {task_id}, 节点: {node_name}, 错误: {str(error)}"
    if context:
        log_msg += f", 上下文: {context}"
    logger.error(log_msg)
    logger.debug(f"[{timestamp}] [ERROR_DEBUG] 任务ID: {task_id}, 异常类型: {type(error).__name__}, 堆栈: {error.__traceback__}")


def _log_variable_value(task_id: str, node_name: str, var_name: str, var_value: Any, var_type: str = None):
    """
    记录变量值日志
    
    Args:
        task_id: 任务ID
        node_name: 节点名称
        var_name: 变量名
        var_value: 变量值
        var_type: 变量类型
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    value_str = str(var_value)[:100] if var_value is not None else "None"
    type_str = var_type or type(var_value).__name__ if var_value is not None else "NoneType"
    logger.debug(f"[{timestamp}] [VARIABLE] 任务ID: {task_id}, 节点: {node_name}, 变量: {var_name}, 值: {value_str}, 类型: {type_str}")


class ScanAgentGraph:
    """
    扫描Agent图类
    
    负责构建和编译LangGraph工作流。
    """
    
    def __init__(self):
        """
        初始化扫描Agent图
        """
        logger.info("🔧 初始化扫描Agent图")
        
        # 创建核心节点实例
        self.env_awareness_node = EnvironmentAwarenessNode()
        self.planning_node = TaskPlanningNode()
        # self.intelligent_decision_node = IntelligentDecisionNode()
        self.execution_node = ToolExecutionNode()
        # self.code_generation_node = CodeGenerationNode()
        # self.code_execution_node = CodeExecutionNode()
        # self.capability_enhancement_node = CapabilityEnhancementNode()
        self.verification_node = ResultVerificationNode()
        self.analysis_node = VulnerabilityAnalysisNode()
        self.report_node = ReportGenerationNode()
        
        # 构建图
        self.graph = self._build_graph()
        
        logger.info("✅ 扫描Agent图构建完成")
    
    def _build_graph(self) -> StateGraph:
        """
        构建LangGraph图 (简化版)

        实现简化的工作流:
        - 环境感知 → 任务规划 → 工具执行
        - 工具执行 → 结果验证 → 循环/漏洞分析
        - 漏洞分析 → 报告生成 → 结束

        Returns:
            StateGraph: 编译后的图
        """
        _log_node_entry("_build_graph", "GRAPH_BUILD", {"total_nodes": 6})

        # 创建状态图
        workflow = StateGraph(AgentState)

        # 添加核心节点
        workflow.add_node("environment_awareness", self.env_awareness_node)
        workflow.add_node("task_planning", self.planning_node)
        workflow.add_node("tool_execution", self.execution_node)
        workflow.add_node("result_verification", self.verification_node)
        workflow.add_node("vulnerability_analysis", self.analysis_node)
        workflow.add_node("report_generation", self.report_node)

        # 设置入口点:从环境感知开始
        workflow.set_entry_point("environment_awareness")

        # 基础流程:环境感知 → 任务规划 → 工具执行
        workflow.add_edge("environment_awareness", "task_planning")
        workflow.add_edge("task_planning", "tool_execution")

        # 工具流程:执行→验证→循环/分析
        workflow.add_edge("tool_execution", "result_verification")
        workflow.add_conditional_edges(
            "result_verification",
            self._should_continue_or_verify,
            {
                "continue": "tool_execution",
                "analyze": "vulnerability_analysis"
            }
        )

        # 后续流程:分析→报告→结束
        workflow.add_edge("vulnerability_analysis", "report_generation")
        workflow.add_edge("report_generation", END)

        logger.info("📊 LangGraph图边定义完成")
        _log_node_exit("_build_graph", "GRAPH_BUILD", "success", {"nodes_count": 6, "edges_count": 6})
        return workflow
    
    def _should_continue_or_verify(self, state: AgentState) -> Literal["continue", "analyze"]:
        """
        判断是否继续执行工具

        Args:
            state: Agent当前状态

        Returns:
            Literal["continue", "analyze"]: 下一步节点名称
        """
        max_tool_rounds = 50
        tool_round_key = "_tool_execution_rounds"
        current_round = state.target_context.get(tool_round_key, 0)

        _log_variable_value(state.task_id, "_should_continue_or_verify", "current_round", current_round)
        _log_variable_value(state.task_id, "_should_continue_or_verify", "planned_tasks", state.planned_tasks)

        if current_round >= max_tool_rounds:
            logger.warning(f"[{state.task_id}] ⚠️ 已达到工具执行最大轮次({max_tool_rounds}),强制进入分析阶段")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="result_verification",
                to_node="vulnerability_analysis",
                condition=f"max_rounds_reached={max_tool_rounds}"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="SHOULD_CONTINUE",
                decision="analyze",
                reason=f"达到工具执行最大轮次({max_tool_rounds})"
            )
            return "analyze"

        state.target_context[tool_round_key] = current_round + 1
        _log_state_change(state.task_id, tool_round_key, current_round, current_round + 1)

        if state.planned_tasks:
            logger.info(f"[{state.task_id}] 🔄 继续执行工具: {state.planned_tasks[0]}")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="result_verification",
                to_node="tool_execution",
                condition=f"next_task={state.planned_tasks[0]}"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="SHOULD_CONTINUE",
                decision="continue",
                reason=f"继续执行工具: {state.planned_tasks[0]}"
            )
            return "continue"

        logger.info(f"[{state.task_id}] 📋 所有任务已完成,进入分析阶段")
        _log_edge_traversal(
            task_id=state.task_id,
            from_node="result_verification",
            to_node="vulnerability_analysis",
            condition="all_tasks_completed"
        )
        _log_decision(
            task_id=state.task_id,
            decision_type="SHOULD_CONTINUE",
            decision="analyze",
            reason="所有任务已完成"
        )
        return "analyze"
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "analyze"]:
        """
        判断是否继续执行工具
        
        Args:
            state: Agent当前状态
            
        Returns:
            Literal["continue", "analyze"]: 下一步节点名称
        """
        if state.is_complete or not state.planned_tasks:
            logger.info(f"[{state.task_id}] 📋 所有任务已完成,进入分析阶段")
            return "analyze"
        else:
            logger.info(f"[{state.task_id}] 🔄 继续执行工具: {state.current_task}")
            return "continue"
    
    def _decide_scan_type(self, state: AgentState) -> Literal["fixed_tool", "custom_code", "enhance_first"]:
        """
        智能决策:选择扫描类型(核心分支逻辑)

        根据环境信息和目标特征,智能决定使用固定工具扫描、
        生成自定义代码扫描,还是先增强功能再扫描。

        Args:
            state: Agent当前状态

        Returns:
            Literal["fixed_tool", "custom_code", "enhance_first"]: 扫描类型
        """
        target_context = state.target_context

        _log_variable_value(state.task_id, "_decide_scan_type", "target_context_keys", list(target_context.keys()))
        _log_variable_value(state.task_id, "_decide_scan_type", "planned_tasks", state.planned_tasks)

        # 1. 需要功能增强(比如依赖缺失)→先增强
        if target_context.get("need_capability_enhancement"):
            logger.info(f"[{state.task_id}] 🚀 需要功能增强,优先执行增强节点")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="intelligent_decision",
                to_node="capability_enhancement",
                condition="need_capability_enhancement=True"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="SCAN_TYPE",
                decision="enhance_first",
                reason="需要功能增强"
            )
            return "enhance_first"

        # 2. 需要自定义扫描→生成代码
        elif target_context.get("need_custom_scan"):
            logger.info(f"[{state.task_id}] 🔧 需要自定义扫描,执行代码生成")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="intelligent_decision",
                to_node="code_generation",
                condition="need_custom_scan=True"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="SCAN_TYPE",
                decision="custom_code",
                reason="需要自定义扫描"
            )
            return "custom_code"

        # 3. 默认使用现有工具
        else:
            logger.info(f"[{state.task_id}] 🛠️ 使用现有工具执行扫描")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="intelligent_decision",
                to_node="tool_execution",
                condition="default"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="SCAN_TYPE",
                decision="fixed_tool",
                reason="使用现有工具"
            )
            return "fixed_tool"
    
    def _code_execution_result(self, state: AgentState) -> Literal["success", "need_enhance"]:
        """
        判断代码执行结果:成功→继续流程,失败→触发功能补充
        
        根据代码执行结果决定是继续验证结果还是触发功能补充。
        
        Args:
            state: Agent当前状态
            
        Returns:
            Literal["success", "need_enhance"]: 下一步操作
        """
        execution_result = state.tool_results.get("code_execution", {})
        
        _log_variable_value(state.task_id, "_code_execution_result", "execution_status", execution_result.get("status"))
        _log_variable_value(state.task_id, "_code_execution_result", "enhancement_retry_count", state.enhancement_retry_count)
        _log_data_flow(
            task_id=state.task_id,
            flow_type="input",
            source="code_execution",
            data=execution_result,
            description="代码执行结果"
        )
        
        if execution_result.get("status") == "success":
            logger.info(f"[{state.task_id}] ✅ 代码执行成功,继续验证结果")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="code_execution",
                to_node="result_verification",
                condition="execution_success"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="CODE_EXECUTION",
                decision="success",
                reason="代码执行成功"
            )
            # 重置增强重试计数
            old_count = state.enhancement_retry_count
            state.reset_enhancement_retry()
            _log_state_change(state.task_id, "enhancement_retry_count", old_count, 0)
            return "success"
        else:
            # 检查重试次数,防止无限循环
            if state.enhancement_retry_count >= 3:
                logger.error(f"[{state.task_id}] ❌ 代码执行失败且达到最大增强重试次数,停止增强")
                _log_edge_traversal(
                    task_id=state.task_id,
                    from_node="code_execution",
                    to_node="result_verification",
                    condition="max_retries_reached"
                )
                _log_decision(
                    task_id=state.task_id,
                    decision_type="CODE_EXECUTION",
                    decision="max_retries",
                    reason=f"达到最大增强重试次数(3), 错误: {execution_result.get('error', 'unknown')}"
                )
                return "success"  # 视为"完成"当前阶段，进入结果验证
            
            # 执行失败时,标记需要功能增强
            logger.warning(f"[{state.task_id}] ⚠️ 代码执行失败,需要功能增强 (重试 {state.enhancement_retry_count + 1}/3)")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="code_execution",
                to_node="capability_enhancement",
                condition=f"execution_failed, retry={state.enhancement_retry_count + 1}/3"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="CODE_EXECUTION",
                decision="need_enhance",
                reason=f"代码执行失败: {execution_result.get('error', 'unknown')}"
            )
            state.target_context["need_capability_enhancement"] = True
            state.target_context["capability_requirement"] = "自动安装代码执行所需依赖"
            state.increment_enhancement_retry()
            _log_state_change(state.task_id, "enhancement_retry_count", state.enhancement_retry_count - 1, state.enhancement_retry_count)
            return "need_enhance"
    
    def _capability_enhancement_result(self, state: AgentState) -> Literal["success", "failed"]:
        """
        判断功能补充结果:成功→重试代码执行,失败→继续验证结果
        
        Args:
            state: Agent当前状态
            
        Returns:
            Literal["success", "failed"]: 下一步操作
        """
        enhancement_result = state.tool_results.get("capability_enhancement", {})
        
        _log_variable_value(state.task_id, "_capability_enhancement_result", "enhancement_status", enhancement_result.get("status"))
        _log_variable_value(state.task_id, "_capability_enhancement_result", "installed_packages", enhancement_result.get("installed_packages", []))
        _log_data_flow(
            task_id=state.task_id,
            flow_type="input",
            source="capability_enhancement",
            data=enhancement_result,
            description="功能增强结果"
        )
        
        if enhancement_result.get("status") == "success":
            logger.info(f"[{state.task_id}] ✅ 功能补充成功,重试代码执行")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="capability_enhancement",
                to_node="code_execution",
                condition="enhancement_success"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="CAPABILITY_ENHANCEMENT",
                decision="success",
                reason="功能补充成功"
            )
            return "success"
        else:
            logger.warning(f"[{state.task_id}] ⚠️ 功能补充失败,继续验证结果")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="capability_enhancement",
                to_node="result_verification",
                condition="enhancement_failed"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="CAPABILITY_ENHANCEMENT",
                decision="failed",
                reason=f"功能补充失败: {enhancement_result.get('error', 'unknown')}"
            )
            return "failed"
    
    def _build_info_collection_graph(self) -> StateGraph:
        """
        构建信息收集子图
        
        负责环境感知和任务规划阶段。
        
        Returns:
            StateGraph: 信息收集子图
        """
        _log_node_entry("_build_info_collection_graph", "SUBGRAPH_BUILD", {"total_nodes": 2})

        workflow = StateGraph(AgentState)

        workflow.add_node("environment_awareness", self.env_awareness_node)
        workflow.add_node("task_planning", self.planning_node)

        workflow.set_entry_point("environment_awareness")
        workflow.add_edge("environment_awareness", "task_planning")
        workflow.add_edge("task_planning", END)

        logger.info("📊 信息收集子图构建完成")
        _log_node_exit("_build_info_collection_graph", "SUBGRAPH_BUILD", "success", {"nodes_count": 2, "edges_count": 2})
        return workflow

    def _build_vulnerability_scan_graph(self) -> StateGraph:
        """
        构建漏洞扫描子图
        
        负责工具执行和结果验证阶段，支持循环执行多个工具。
        
        Returns:
            StateGraph: 漏洞扫描子图
        """
        _log_node_entry("_build_vulnerability_scan_graph", "SUBGRAPH_BUILD", {"total_nodes": 2})

        workflow = StateGraph(AgentState)

        workflow.add_node("tool_execution", self.execution_node)
        workflow.add_node("result_verification", self.verification_node)

        workflow.set_entry_point("tool_execution")
        workflow.add_edge("tool_execution", "result_verification")
        workflow.add_conditional_edges(
            "result_verification",
            self._should_continue_or_verify,
            {
                "continue": "tool_execution",
                "analyze": END
            }
        )

        logger.info("📊 漏洞扫描子图构建完成")
        _log_node_exit("_build_vulnerability_scan_graph", "SUBGRAPH_BUILD", "success", {"nodes_count": 2, "edges_count": 3})
        return workflow

    def _build_result_analysis_graph(self) -> StateGraph:
        """
        构建结果分析子图
        
        负责漏洞分析和报告生成阶段。
        
        Returns:
            StateGraph: 结果分析子图
        """
        _log_node_entry("_build_result_analysis_graph", "SUBGRAPH_BUILD", {"total_nodes": 2})

        workflow = StateGraph(AgentState)

        workflow.add_node("vulnerability_analysis", self.analysis_node)
        workflow.add_node("report_generation", self.report_node)

        workflow.set_entry_point("vulnerability_analysis")
        workflow.add_edge("vulnerability_analysis", "report_generation")
        workflow.add_edge("report_generation", END)

        logger.info("📊 结果分析子图构建完成")
        _log_node_exit("_build_result_analysis_graph", "SUBGRAPH_BUILD", "success", {"nodes_count": 2, "edges_count": 2})
        return workflow

    def get_info_collection_graph(self):
        """
        获取信息收集子图（可编译和独立执行）
        
        Returns:
            StateGraph: 信息收集子图
        """
        return self._build_info_collection_graph()

    def get_vulnerability_scan_graph(self):
        """
        获取漏洞扫描子图（可编译和独立执行）
        
        Returns:
            StateGraph: 漏洞扫描子图
        """
        return self._build_vulnerability_scan_graph()

    def get_result_analysis_graph(self):
        """
        获取结果分析子图（可编译和独立执行）
        
        Returns:
            StateGraph: 结果分析子图
        """
        return self._build_result_analysis_graph()

    def compile_info_collection(self):
        """
        编译信息收集子图
        
        Returns:
            编译后的信息收集子图
        """
        return self.get_info_collection_graph().compile()

    def compile_vulnerability_scan(self):
        """
        编译漏洞扫描子图
        
        Returns:
            编译后的漏洞扫描子图
        """
        return self.get_vulnerability_scan_graph().compile()

    def compile_result_analysis(self):
        """
        编译结果分析子图
        
        Returns:
            编译后的结果分析子图
        """
        return self.get_result_analysis_graph().compile()

    async def invoke_info_collection(self, initial_state: AgentState) -> AgentState:
        """
        执行信息收集子图
        
        Args:
            initial_state: 初始状态
            
        Returns:
            AgentState: 执行后的状态
        """
        logger.info(f"🚀 开始执行信息收集子图: {initial_state.task_id}")
        _log_node_entry("invoke_info_collection", initial_state.task_id, {"target": initial_state.target})
        
        try:
            compiled_graph = self.compile_info_collection()
            config = {"recursion_limit": 100}
            final_state = await compiled_graph.ainvoke(initial_state, config=config)
            
            logger.info(f"✅ 信息收集子图执行完成: {getattr(final_state, 'task_id', initial_state.task_id)}")
            _log_node_exit("invoke_info_collection", initial_state.task_id, "success", {
                "planned_tasks": getattr(final_state, 'planned_tasks', [])
            })
            
            return final_state
        except Exception as e:
            logger.error(f"❌ 信息收集子图执行失败: {initial_state.task_id}, 错误: {str(e)}")
            _log_error(initial_state.task_id, "invoke_info_collection", e, {"target": initial_state.target})
            raise

    async def invoke_vulnerability_scan(self, initial_state: AgentState) -> AgentState:
        """
        执行漏洞扫描子图
        
        Args:
            initial_state: 初始状态（通常是信息收集子图的输出）
            
        Returns:
            AgentState: 执行后的状态
        """
        logger.info(f"🚀 开始执行漏洞扫描子图: {initial_state.task_id}")
        _log_node_entry("invoke_vulnerability_scan", initial_state.task_id, {"target": initial_state.target})
        
        try:
            compiled_graph = self.compile_vulnerability_scan()
            config = {"recursion_limit": 200}
            final_state = await compiled_graph.ainvoke(initial_state, config=config)
            
            logger.info(f"✅ 漏洞扫描子图执行完成: {getattr(final_state, 'task_id', initial_state.task_id)}")
            _log_node_exit("invoke_vulnerability_scan", initial_state.task_id, "success", {
                "completed_tasks": len(getattr(final_state, 'completed_tasks', [])),
                "vulnerabilities_found": len(getattr(final_state, 'vulnerabilities', []))
            })
            
            return final_state
        except Exception as e:
            logger.error(f"❌ 漏洞扫描子图执行失败: {initial_state.task_id}, 错误: {str(e)}")
            _log_error(initial_state.task_id, "invoke_vulnerability_scan", e, {"target": initial_state.target})
            raise

    async def invoke_result_analysis(self, initial_state: AgentState) -> AgentState:
        """
        执行结果分析子图
        
        Args:
            initial_state: 初始状态（通常是漏洞扫描子图的输出）
            
        Returns:
            AgentState: 执行后的状态
        """
        logger.info(f"🚀 开始执行结果分析子图: {initial_state.task_id}")
        _log_node_entry("invoke_result_analysis", initial_state.task_id, {"target": initial_state.target})
        
        try:
            compiled_graph = self.compile_result_analysis()
            config = {"recursion_limit": 100}
            final_state = await compiled_graph.ainvoke(initial_state, config=config)
            
            logger.info(f"✅ 结果分析子图执行完成: {getattr(final_state, 'task_id', initial_state.task_id)}")
            _log_node_exit("invoke_result_analysis", initial_state.task_id, "success", {
                "vulnerabilities": len(getattr(final_state, 'vulnerabilities', []))
            })
            
            return final_state
        except Exception as e:
            logger.error(f"❌ 结果分析子图执行失败: {initial_state.task_id}, 错误: {str(e)}")
            _log_error(initial_state.task_id, "invoke_result_analysis", e, {"target": initial_state.target})
            raise

    async def invoke_subgraphs_sequential(self, initial_state: AgentState) -> AgentState:
        """
        依次执行所有子图（验证子图之间的数据传递）
        
        Args:
            initial_state: 初始状态
            
        Returns:
            AgentState: 最终状态
        """
        logger.info(f"🚀 开始依次执行所有子图: {initial_state.task_id}")
        _log_node_entry("invoke_subgraphs_sequential", initial_state.task_id, {"target": initial_state.target})
        
        try:
            state1 = await self.invoke_info_collection(initial_state)
            
            state2 = await self.invoke_vulnerability_scan(state1)
            
            final_state = await self.invoke_result_analysis(state2)
            
            logger.info(f"✅ 所有子图依次执行完成: {getattr(final_state, 'task_id', initial_state.task_id)}")
            _log_node_exit("invoke_subgraphs_sequential", initial_state.task_id, "success", {
                "completed_tasks": len(getattr(final_state, 'completed_tasks', [])),
                "vulnerabilities_found": len(getattr(final_state, 'vulnerabilities', []))
            })
            
            return final_state
        except Exception as e:
            logger.error(f"❌ 子图依次执行失败: {initial_state.task_id}, 错误: {str(e)}")
            _log_error(initial_state.task_id, "invoke_subgraphs_sequential", e, {"target": initial_state.target})
            raise

    def compile(self):
        """
        编译完整图
        
        Returns:
            编译后的可执行图
        """
        return self.graph.compile()
    
    async def invoke(self, initial_state: AgentState) -> AgentState:
        """
        执行Agent工作流(增强版)
        
        Args:
            initial_state: 初始状态
            
        Returns:
            AgentState: 最终状态
        """
        logger.info(f"🚀 开始执行增强版Agent工作流: {initial_state.task_id}")
        _log_node_entry("invoke", initial_state.task_id, {"target": initial_state.target})
        
        try:
            compiled_graph = self.compile()
            # 设置递归限制以避免无限循环
            config = {"recursion_limit": 100}
            final_state = await compiled_graph.ainvoke(initial_state, config=config)
            
            # 处理返回的状态对象，可能是字典形式
            task_id = getattr(final_state, 'task_id', initial_state.task_id)
            completed_tasks = getattr(final_state, 'completed_tasks', [])
            vulnerabilities = getattr(final_state, 'vulnerabilities', [])
            errors = getattr(final_state, 'errors', [])
            
            logger.info(f"✅ 增强版Agent工作流执行完成: {task_id}")
            _log_node_exit("invoke", initial_state.task_id, "success", {
                "completed_tasks": len(completed_tasks),
                "vulnerabilities_found": len(vulnerabilities),
                "errors_count": len(errors)
            })
            
            return final_state
        except Exception as e:
            logger.error(f"❌ 增强版Agent工作流执行失败: {initial_state.task_id}, 错误: {str(e)}")
            _log_error(initial_state.task_id, "invoke", e, {"target": initial_state.target})
            raise
    

def create_agent_graph() -> ScanAgentGraph:
    """
    创建Agent图实例
    
    Returns:
        ScanAgentGraph: Agent图实例
    """
    return ScanAgentGraph()


def initialize_tools():
    """
    初始化所有工具
    
    注册所有插件和POC到工具注册表。
    """
    from ..tools.registry import registry
    from ..tools.adapters import PluginAdapter, POCAdapter
    
    logger.info("🔧 开始初始化工具...")
    
    # 注册插件 - 注意：传递函数引用而不是调用结果
    registry.register(
        name="baseinfo",
        func=PluginAdapter.adapt_baseinfo,
        description="基础信息收集(域名、IP、服务器、OS等)",
        category="plugin",
        timeout=10,
        priority=3
    )
    
    registry.register(
        name="portscan",
        func=PluginAdapter.adapt_portscan,
        description="TCP端口扫描,识别开放端口和服务",
        category="plugin",
        timeout=120,
        priority=5
    )
    
    registry.register(
        name="waf_detect",
        func=PluginAdapter.adapt_waf_detect,
        description="WAF(Web应用防火墙)检测",
        category="plugin",
        timeout=10,
        priority=4
    )
    
    registry.register(
        name="cdn_detect",
        func=PluginAdapter.adapt_cdn_detect,
        description="CDN(内容分发网络)检测",
        category="plugin",
        timeout=10,
        priority=4
    )
    
    registry.register(
        name="cms_identify",
        func=PluginAdapter.adapt_cms_identify,
        description="CMS(内容管理系统)识别",
        category="plugin",
        timeout=15,
        priority=4
    )
    
    registry.register(
        name="infoleak_scan",
        func=PluginAdapter.adapt_infoleak_scan,
        description="信息泄露扫描",
        category="plugin",
        timeout=30,
        priority=3
    )
    
    registry.register(
        name="subdomain_scan",
        func=PluginAdapter.adapt_subdomain_scan,
        description="子域名枚举",
        category="plugin",
        timeout=60,
        priority=3
    )
    
    registry.register(
        name="webside_scan",
        func=PluginAdapter.adapt_webside_scan,
        description="站点信息收集",
        category="plugin",
        timeout=30,
        priority=3
    )
    
    registry.register(
        name="webweight_scan",
        func=PluginAdapter.adapt_webweight_scan,
        description="网站权重查询",
        category="plugin",
        timeout=30,
        priority=2
    )
    
    registry.register(
        name="iplocating",
        func=PluginAdapter.adapt_iplocating,
        description="IP地址定位",
        category="plugin",
        timeout=30,
        priority=3
    )
    
    registry.register(
        name="loginfo",
        func=PluginAdapter.adapt_loginfo,
        description="日志信息分析",
        category="plugin",
        timeout=30,
        priority=2
    )
    
    registry.register(
        name="randheader",
        func=PluginAdapter.adapt_randheader,
        description="随机HTTP请求头生成",
        category="plugin",
        timeout=30,
        priority=2
    )
    
    logger.info(f"✅ 工具初始化完成,共注册 {len(registry.tools)} 个工具")
    
    logger.info("🔧 开始注册POC工具...")
    pocs = POCAdapter.get_all_pocs()
    for poc_name, poc_module in pocs.items():
        def create_poc_func(poc_name=poc_name, poc_module=poc_module):
            async def poc_func(target: str, timeout: Optional[float] = None, progress_callback=None, **kwargs):
                return await POCAdapter.adapt_poc(
                    target=target,
                    poc_name=poc_name,
                    poc_module=poc_module,
                    timeout=timeout,
                    progress_callback=progress_callback
                )
            return poc_func
        
        registry.register(
            name=poc_name,
            func=create_poc_func(),
            description=f"POC漏洞检测: {poc_name}",
            category="poc",
            timeout=POCAdapter.DEFAULT_POC_TIMEOUT,
            priority=6,
            tags=["poc", "vulnerability", "exploit"],
            enabled=True
        )
    
    logger.info(f"✅ POC工具初始化完成,共注册 {len(pocs)} 个POC工具")

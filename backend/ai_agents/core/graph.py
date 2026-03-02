"""
LangGraph 图构建(增强版)

构建支持自主规划、代码生成、环境感知的完整Agent工作流。

重构说明:
- 新增SubgraphRouter类：子图路由器，优先使用子图执行
- 保留ScanAgentGraph类：大图组件，作为备选方案
- 统一调用接口：execute_scan()方法

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
from .task_router import TaskRouter, ExecutionMode, TaskComplexity, RoutingDecision
from ..subgraphs.orchestrator import ScanOrchestrator
from ..subgraphs.dto import OrchestratorResultDTO, TaskStatus
from .nodes import (
    TaskPlanningNode,
    ToolExecutionNode,
    ResultVerificationNode,
    VulnerabilityAnalysisNode,
    ReportGenerationNode,
    EnvironmentAwarenessNode,
    CodeGenerationNode,
    CapabilityEnhancementNode,
    CodeExecutionNode,
    IntelligentDecisionNode,
    SeebugAgentNode,
    POCVerificationNode,
    AWVSScanningNode
)

from ..agent_config import agent_config

logger = logging.getLogger(__name__)

seebug_agent_node = SeebugAgentNode()
poc_verification_node = POCVerificationNode()
awvs_scanning_node = AWVSScanningNode()


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
        
        # 创建节点实例(原有+新增)
        self.env_awareness_node = EnvironmentAwarenessNode()  # 环境感知
        self.planning_node = TaskPlanningNode()  # 任务规划
        self.intelligent_decision_node = IntelligentDecisionNode()  # 智能决策
        self.execution_node = ToolExecutionNode()  # 固定工具执行
        self.code_generation_node = CodeGenerationNode()  # 代码生成
        self.code_execution_node = CodeExecutionNode()  # 代码执行
        self.capability_enhancement_node = CapabilityEnhancementNode()  # 功能补充
        self.verification_node = ResultVerificationNode()  # 结果验证
        self.poc_verification_node = poc_verification_node  # POC 验证(新增)
        self.seebug_agent_node = seebug_agent_node  # Seebug Agent(新增)
        self.awvs_scanning_node = awvs_scanning_node # AWVS 扫描(新增)
        self.analysis_node = VulnerabilityAnalysisNode()  # 漏洞分析
        self.report_node = ReportGenerationNode()  # 报告生成
        
        # 构建图
        self.graph = self._build_graph()
        
        logger.info("✅ 扫描Agent图构建完成")
    
    def _build_graph(self) -> StateGraph:
        """
        构建LangGraph图(增强版,包含所有11个节点)
        
        实现完整的工作流:
        - 环境感知 → 任务规划 → 智能决策
        - 智能决策 → 固定工具 / 代码生成 / 功能补充 / POC 验证
        - 代码生成 → 代码执行 → 结果验证 / 功能补充
        - 固定工具 → 结果验证 → 循环 / 漏洞分析 / POC 验证
        - POC 验证 → 漏洞分析
        - 漏洞分析 → 报告生成 → 结束
        
        Returns:
            StateGraph: 编译后的图
        """
        _log_node_entry("_build_graph", "GRAPH_BUILD", {"total_nodes": 11})
        
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 添加所有节点(原有5个 + 新增7个 = 12个)
        workflow.add_node("environment_awareness", self.env_awareness_node)  # 新增:环境感知
        workflow.add_node("task_planning", self.planning_node)
        workflow.add_node("intelligent_decision", self.intelligent_decision_node)  # 新增:智能决策
        workflow.add_node("tool_execution", self.execution_node)
        workflow.add_node("code_generation", self.code_generation_node)  # 新增:代码生成
        workflow.add_node("code_execution", self.code_execution_node)  # 新增:代码执行
        workflow.add_node("capability_enhancement", self.capability_enhancement_node)  # 新增:功能补充
        workflow.add_node("result_verification", self.verification_node)
        workflow.add_node("poc_verification", self.poc_verification_node)  # 新增:POC 验证
        workflow.add_node("seebug_agent", self.seebug_agent_node)  # 新增:Seebug Agent
        workflow.add_node("awvs_scanning", self.awvs_scanning_node) # 新增:AWVS 扫描
        workflow.add_node("vulnerability_analysis", self.analysis_node)
        workflow.add_node("report_generation", self.report_node)
        
        # 设置入口点:从环境感知开始(先看环境,再做规划)
        workflow.set_entry_point("environment_awareness")
        
        # 基础流程:环境感知 → 任务规划 → 智能决策
        workflow.add_edge("environment_awareness", "task_planning")
        workflow.add_edge("task_planning", "intelligent_decision")
        
        # 核心条件分支1:智能决策后选择"固定工具"或"代码生成"或"功能增强"或"POC 验证"或"Seebug Agent"
        workflow.add_conditional_edges(
            "intelligent_decision",  # 起始节点:智能决策
            self._decide_scan_type,  # 分支判断函数
            {
                "fixed_tool": "tool_execution",  # 用现有工具扫描
                "custom_code": "code_generation",  # 生成代码扫描
                "enhance_first": "capability_enhancement",  # 先增强功能再扫描
                "poc_verification": "poc_verification",  # POC 验证
                "seebug_agent": "seebug_agent",  # Seebug Agent(新增)
                "awvs_scan": "awvs_scanning" # AWVS 扫描
            }
        )
        
        # 代码生成→执行→补充闭环
        workflow.add_edge("code_generation", "code_execution")
        # 代码执行失败时,触发功能补充(比如自动安装依赖)
        workflow.add_conditional_edges(
            "code_execution",
            self._code_execution_result,
            {
                "success": "result_verification",  # 执行成功→验证结果
                "need_enhance": "capability_enhancement"  # 执行失败→功能补充
            }
        )
        # 功能补充后回到代码执行(重试)
        workflow.add_conditional_edges(
            "capability_enhancement",
            self._capability_enhancement_result,
            {
                "success": "code_execution",  # 补充成功→重试代码执行
                "failed": "result_verification"  # 补充失败→继续验证结果
            }
        )
        
        # 固定工具流程:执行→验证→循环/分析/POC 验证
        workflow.add_edge("tool_execution", "result_verification")
        # 结果验证后的分支:有任务继续执行,无任务进入分析或 POC 验证
        workflow.add_conditional_edges(
            "result_verification",
            self._should_continue_or_verify,
            {
                "continue": "tool_execution",  # 继续执行工具
                "analyze": "vulnerability_analysis",  # 进入漏洞分析
                "poc_verify": "poc_verification",  # 进入 POC 验证(新增)
                "awvs_scan": "awvs_scanning"  # 进入 AWVS 扫描
            }
        )
        
        # POC 验证流程:POC 验证 → 漏洞分析
        workflow.add_edge("poc_verification", "vulnerability_analysis")
        
        # Seebug Agent流程:Seebug Agent → POC 验证
        workflow.add_edge("seebug_agent", "poc_verification")
        
        # AWVS 扫描流程: AWVS 扫描 → 漏洞分析
        workflow.add_edge("awvs_scanning", "vulnerability_analysis")
        
        # 后续流程:分析→POC验证(如果有任务)或报告
        workflow.add_conditional_edges(
            "vulnerability_analysis",
            self._post_analysis_routing,
            {
                "poc_verification": "poc_verification",
                "report_generation": "report_generation"
            }
        )
        workflow.add_edge("report_generation", END)
        
        logger.info("📊 增强版LangGraph图边定义完成")
        _log_node_exit("_build_graph", "GRAPH_BUILD", "success", {"nodes_count": 11, "edges_count": 16})
        return workflow
    
    def _post_analysis_routing(self, state: AgentState) -> Literal["poc_verification", "report_generation"]:
        """
        漏洞分析后的路由判断
        
        Args:
            state: Agent当前状态
            
        Returns:
            Literal["poc_verification", "report_generation"]: 下一步节点
        """
        max_poc_rounds = 3
        poc_round_key = "_poc_verification_rounds"
        
        current_round = state.target_context.get(poc_round_key, 0)
        _log_variable_value(state.task_id, "_post_analysis_routing", "current_round", current_round)
        
        pending_pocs = [t for t in state.poc_verification_tasks if t.get("status") == "pending"]
        _log_variable_value(state.task_id, "_post_analysis_routing", "pending_pocs_count", len(pending_pocs))
        
        if pending_pocs and current_round < max_poc_rounds:
            state.target_context[poc_round_key] = current_round + 1
            logger.info(f"[{state.task_id}] 🔄 发现 {len(pending_pocs)} 个待验证POC任务,进入POC验证阶段 (轮次 {current_round + 1}/{max_poc_rounds})")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="vulnerability_analysis",
                to_node="poc_verification",
                condition=f"pending_pocs={len(pending_pocs)}, round={current_round + 1}/{max_poc_rounds}",
                state_snapshot={"poc_round": current_round + 1}
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="POST_ANALYSIS_ROUTING",
                decision="poc_verification",
                reason=f"发现 {len(pending_pocs)} 个待验证POC任务"
            )
            return "poc_verification"
            
        if current_round >= max_poc_rounds:
            logger.warning(f"[{state.task_id}] ⚠️ 已达到POC验证最大轮次({max_poc_rounds}),直接生成报告")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="vulnerability_analysis",
                to_node="report_generation",
                condition=f"max_rounds_reached={max_poc_rounds}"
            )
        else:
            logger.info(f"[{state.task_id}] ✅ 漏洞分析完成且无待验证POC,生成报告")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="vulnerability_analysis",
                to_node="report_generation",
                condition="no_pending_pocs"
            )
        return "report_generation"

    def _should_continue_or_verify(self, state: AgentState) -> Literal["continue", "analyze", "poc_verify", "awvs_scan"]:
        """
        判断是否继续执行工具或进入 POC 验证
        
        Args:
            state: Agent当前状态
            
        Returns:
            Literal["continue", "analyze", "poc_verify", "awvs_scan"]: 下一步节点名称
        """
        max_tool_rounds = 50
        tool_round_key = "_tool_execution_rounds"
        current_round = state.target_context.get(tool_round_key, 0)
        
        _log_variable_value(state.task_id, "_should_continue_or_verify", "current_round", current_round)
        _log_variable_value(state.task_id, "_should_continue_or_verify", "planned_tasks", state.planned_tasks)
        _log_variable_value(state.task_id, "_should_continue_or_verify", "poc_tasks_count", len(state.poc_verification_tasks) if state.poc_verification_tasks else 0)
        
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
        
        if state.poc_verification_tasks and len(state.poc_verification_tasks) > 0:
            logger.info(f"[{state.task_id}] 📋 发现待验证的 POC 任务,进入 POC 验证节点")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="result_verification",
                to_node="poc_verification",
                condition=f"poc_tasks={len(state.poc_verification_tasks)}"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="SHOULD_CONTINUE",
                decision="poc_verify",
                reason=f"发现 {len(state.poc_verification_tasks)} 个待验证POC任务"
            )
            return "poc_verify"
        
        non_awvs_tasks = [t for t in state.planned_tasks if t != 'awvs']
        if non_awvs_tasks:
            logger.info(f"[{state.task_id}] 🔄 继续执行工具: {non_awvs_tasks[0]}")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="result_verification",
                to_node="tool_execution",
                condition=f"next_task={non_awvs_tasks[0]}"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="SHOULD_CONTINUE",
                decision="continue",
                reason=f"继续执行工具: {non_awvs_tasks[0]}"
            )
            return "continue"

        awvs_status = state.stage_status.get("awvs", {}).get("status")
        _log_variable_value(state.task_id, "_should_continue_or_verify", "awvs_status", awvs_status)
        
        if (state.target_context.get("use_awvs") or "awvs" in state.planned_tasks) and awvs_status != "completed":
             logger.info(f"[{state.task_id}] 🔍 启用 AWVS 扫描")
             _log_edge_traversal(
                 task_id=state.task_id,
                 from_node="result_verification",
                 to_node="awvs_scanning",
                 condition="awvs_enabled_and_not_completed"
             )
             _log_decision(
                 task_id=state.task_id,
                 decision_type="SHOULD_CONTINUE",
                 decision="awvs_scan",
                 reason="AWVS扫描已启用且未完成"
             )
             return "awvs_scan"
        
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
    
    def _decide_scan_type(self, state: AgentState) -> Literal["fixed_tool", "custom_code", "enhance_first", "poc_verification", "seebug_agent", "awvs_scan"]:
        """
        智能决策:选择扫描类型(核心分支逻辑)
        
        根据环境信息和目标特征,智能决定使用固定工具扫描、
        生成自定义代码扫描,还是先增强功能再扫描,或者进行 POC 验证,或者使用 Seebug Agent,或者使用AWVS。
        
        Args:
            state: Agent当前状态
            
        Returns:
            Literal["fixed_tool", "custom_code", "enhance_first", "poc_verification", "seebug_agent", "awvs_scan"]: 扫描类型
        """
        target_context = state.target_context
        
        _log_variable_value(state.task_id, "_decide_scan_type", "target_context_keys", list(target_context.keys()))
        _log_variable_value(state.task_id, "_decide_scan_type", "planned_tasks", state.planned_tasks)
        _log_variable_value(state.task_id, "_decide_scan_type", "poc_tasks_count", len(state.poc_verification_tasks) if state.poc_verification_tasks else 0)
        
        # 1. 检查是否有待验证的 POC 任务
        if state.poc_verification_tasks and len(state.poc_verification_tasks) > 0:
            logger.info(f"[{state.task_id}] 🔍 发现 POC 验证任务,进入 POC 验证流程")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="intelligent_decision",
                to_node="poc_verification",
                condition=f"poc_tasks={len(state.poc_verification_tasks)}"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="SCAN_TYPE",
                decision="poc_verification",
                reason="存在待验证的 POC 任务"
            )
            return "poc_verification"
        
        # 2. 需要功能增强(比如依赖缺失)→先增强
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
        
        # 3. 需要自定义扫描→生成代码
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
        
        # 4. 需要使用Seebug Agent→搜索和生成POC
        elif target_context.get("need_seebug_agent"):
            logger.info(f"[{state.task_id}] 🔍 使用Seebug Agent搜索和生成POC")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="intelligent_decision",
                to_node="seebug_agent",
                condition="need_seebug_agent=True"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="SCAN_TYPE",
                decision="seebug_agent",
                reason="使用Seebug Agent"
            )
            return "seebug_agent"
            
        # 5. 检查是否有普通工具任务 (优先于AWVS, 确保混合任务时先执行工具)
        non_awvs_tasks = [t for t in state.planned_tasks if t != 'awvs']
        if non_awvs_tasks:
            logger.info(f"[{state.task_id}] 🛠️ 使用现有工具执行扫描")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="intelligent_decision",
                to_node="tool_execution",
                condition=f"non_awvs_tasks={non_awvs_tasks}"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="SCAN_TYPE",
                decision="fixed_tool",
                reason="使用现有工具"
            )
            return "fixed_tool"

        # 6. 检查是否需要AWVS扫描 (如果没其他任务了)
        if target_context.get("use_awvs") or "awvs" in state.planned_tasks:
            logger.info(f"[{state.task_id}] 🔍 启用 AWVS 扫描")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="intelligent_decision",
                to_node="awvs_scanning",
                condition="use_awvs=True or awvs in planned_tasks"
            )
            _log_decision(
                task_id=state.task_id,
                decision_type="SCAN_TYPE",
                decision="awvs_scan",
                reason="用户指定或计划任务包含AWVS"
            )
            return "awvs_scan"
        
        # 7. 默认使用现有工具 (虽然可能没有任务了,但作为Fallback)
        else:
            logger.info(f"[{state.task_id}] 🛠️ 使用现有工具执行扫描 (Fallback)")
            _log_edge_traversal(
                task_id=state.task_id,
                from_node="intelligent_decision",
                to_node="tool_execution",
                condition="fallback"
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
    
    def compile(self):
        """
        编译图
        
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
    
    def get_graph_info(self) -> Dict[str, Any]:
        """
        获取图信息(包含所有13个节点)
        
        Returns:
            Dict: 图结构信息
        """
        return {
            "nodes": [
                "environment_awareness",
                "task_planning",
                "intelligent_decision",
                "tool_execution",
                "code_generation",
                "code_execution",
                "capability_enhancement",
                "result_verification",
                "poc_verification",
                "seebug_agent",
                "awvs_scanning",
                "vulnerability_analysis",
                "report_generation"
            ],
            "edges": [
                ("environment_awareness", "task_planning"),
                ("task_planning", "intelligent_decision"),
                ("intelligent_decision", "tool_execution"),
                ("intelligent_decision", "code_generation"),
                ("intelligent_decision", "capability_enhancement"),
                ("intelligent_decision", "poc_verification"),
                ("intelligent_decision", "seebug_agent"),
                ("intelligent_decision", "awvs_scanning"),
                ("code_generation", "code_execution"),
                ("code_execution", "result_verification"),
                ("code_execution", "capability_enhancement"),
                ("capability_enhancement", "code_execution"),
                ("tool_execution", "result_verification"),
                ("result_verification", "tool_execution"),
                ("result_verification", "vulnerability_analysis"),
                ("result_verification", "poc_verification"),
                ("result_verification", "awvs_scanning"),
                ("poc_verification", "vulnerability_analysis"),
                ("seebug_agent", "poc_verification"),
                ("awvs_scanning", "vulnerability_analysis"),
                ("vulnerability_analysis", "report_generation"),
                ("vulnerability_analysis", "poc_verification"),
                ("report_generation", "END")
            ],
            "entry_point": "environment_awareness",
            "exit_points": ["report_generation"],
            "total_nodes": 13,
            "original_nodes": 5,
            "new_nodes": 8
        }
    
    def visualize(self) -> str:
        """
        生成图的可视化文本(增强版,包含所有12个节点)
        
        Returns:
            str: Mermaid格式的图描述
        """
        return """
graph TD
    A[环境感知] --> B[任务规划]
    B --> C[智能决策]
    C -->|固定工具| D[工具执行]
    C -->|自定义代码| E[代码生成]
    C -->|需要增强| F[功能补充]
    C -->|POC验证| K[POC验证]
    C -->|Seebug Agent| L[Seebug Agent]
    E --> G[代码执行]
    G -->|成功| H[结果验证]
    G -->|失败| F
    F --> G
    D --> H
    H -->|有任务| D
    H -->|无任务| I[漏洞分析]
    H -->|POC验证| K
    K --> I
    L --> K
    I --> J[报告生成]
    J --> M[结束]
    
    style A fill:#e1f5ff
    style B fill:#fff3cd
    style C fill:#e8f5e9
    style D fill:#fff3cd
    style E fill:#f8d7da
    style F fill:#fce4ec
    style G fill:#f8d7da
    style H fill:#d4edda
    style K fill:#ff6b6b
    style L fill:#9b59b6
    style I fill:#f8d7da
    style J fill:#fce4ec
    style M fill:#c3e6cb
        """


class SubgraphRouter:
    """
    子图路由器
    
    优先使用子图组件执行任务，当子图无法处理时降级到大图。
    
    核心功能:
    - 智能路由决策：通过TaskRouter分析任务复杂度
    - 子图优先执行：优先调用ScanOrchestrator执行子图
    - 大图降级机制：子图执行失败时自动降级到ScanAgentGraph
    - 统一调用接口：提供execute_scan()方法统一入口
    
    执行策略:
    - SUBGRAPH模式：仅使用子图执行，适用于简单任务
    - HYBRID模式：子图+大图混合执行，适用于中等复杂任务
    - FULLGRAPH模式：使用完整大图执行，适用于复杂任务
    
    Attributes:
        task_router: 任务路由器，负责路由决策
        subgraph_orchestrator: 子图编排器，协调子图执行
        fullgraph: 大图组件，作为备选方案
        enable_fallback: 是否启用降级机制
    """
    
    def __init__(
        self,
        enable_fallback: bool = True,
        simple_threshold: float = 0.3,
        complex_threshold: float = 0.7,
        planning_timeout: float = 10.0,
        tool_execution_timeout: float = 120.0,
        code_scan_timeout: float = 60.0,
        poc_verification_timeout: float = 60.0,
        report_timeout: float = 30.0
    ):
        """
        初始化子图路由器
        
        Args:
            enable_fallback: 是否启用降级机制
            simple_threshold: 简单任务阈值（0-1）
            complex_threshold: 复杂任务阈值（0-1）
            planning_timeout: 规划子图超时时间（秒）
            tool_execution_timeout: 工具执行子图超时时间（秒）
            code_scan_timeout: 代码扫描子图超时时间（秒）
            poc_verification_timeout: POC验证子图超时时间（秒）
            report_timeout: 报告生成子图超时时间（秒）
        """
        logger.info("🔀 初始化子图路由器")
        
        self.task_router = TaskRouter(
            simple_threshold=simple_threshold,
            complex_threshold=complex_threshold,
            enable_fallback=enable_fallback
        )
        
        self.subgraph_orchestrator = ScanOrchestrator(
            planning_timeout=planning_timeout,
            tool_execution_timeout=tool_execution_timeout,
            code_scan_timeout=code_scan_timeout,
            poc_verification_timeout=poc_verification_timeout,
            report_timeout=report_timeout
        )
        
        self._fullgraph: Optional[ScanAgentGraph] = None
        self.enable_fallback = enable_fallback
        
        self._execution_stats = {
            "subgraph_success": 0,
            "subgraph_failed": 0,
            "fullgraph_success": 0,
            "fullgraph_failed": 0,
            "fallback_triggered": 0
        }
        
        logger.info("✅ 子图路由器初始化完成")
        logger.info(f"   - 降级机制: {'启用' if enable_fallback else '禁用'}")
        logger.info(f"   - 简单任务阈值: {simple_threshold}")
        logger.info(f"   - 复杂任务阈值: {complex_threshold}")
    
    @property
    def fullgraph(self) -> ScanAgentGraph:
        """
        懒加载大图组件
        
        只有在需要时才创建大图实例，节省资源。
        
        Returns:
            ScanAgentGraph: 大图组件实例
        """
        if self._fullgraph is None:
            logger.info("📦 懒加载大图组件")
            self._fullgraph = ScanAgentGraph()
        return self._fullgraph
    
    async def execute_scan(self, state: AgentState) -> AgentState:
        """
        执行扫描任务（统一入口）
        
        根据路由决策选择最优执行方式：
        1. 通过TaskRouter进行路由决策
        2. 根据决策结果选择执行模式
        3. 执行失败时自动降级
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 最终状态
            
        Raises:
            Exception: 执行失败且无法降级时抛出异常
        """
        task_id = state.task_id
        logger.info(f"[{task_id}] 🚀 子图路由器开始执行扫描")
        _log_node_entry("SubgraphRouter.execute_scan", task_id, {
            "target": state.target,
            "planned_tasks": state.planned_tasks
        })
        
        try:
            decision = await self.task_router.route(state)
            
            _log_decision(
                task_id=task_id,
                decision_type="ROUTER_DECISION",
                decision=decision.execution_mode.value,
                reason=decision.reasoning
            )
            
            if decision.execution_mode == ExecutionMode.SUBGRAPH:
                result = await self._execute_subgraph(state, decision)
            elif decision.execution_mode == ExecutionMode.FULLGRAPH:
                result = await self._execute_fullgraph(state, decision)
            else:
                result = await self._execute_hybrid(state, decision)
            
            _log_node_exit("SubgraphRouter.execute_scan", task_id, "success", {
                "execution_mode": decision.execution_mode.value,
                "completed_tasks": len(getattr(result, 'completed_tasks', []))
            })
            
            return result
            
        except Exception as e:
            logger.error(f"[{task_id}] ❌ 子图路由器执行失败: {str(e)}")
            _log_error(task_id, "SubgraphRouter.execute_scan", e, {
                "target": state.target
            })
            raise
    
    async def _execute_subgraph(
        self,
        state: AgentState,
        decision: RoutingDecision
    ) -> AgentState:
        """
        使用子图执行任务
        
        适用于简单任务，执行效率高。
        
        Args:
            state: Agent当前状态
            decision: 路由决策
            
        Returns:
            AgentState: 最终状态
        """
        task_id = state.task_id
        logger.info(f"[{task_id}] 🔧 使用子图执行任务")
        _log_edge_traversal(
            task_id=task_id,
            from_node="SubgraphRouter",
            to_node="ScanOrchestrator",
            condition=f"mode={ExecutionMode.SUBGRAPH.value}"
        )
        
        try:
            result = await self.subgraph_orchestrator.execute_scan(
                target=state.target,
                task_id=task_id,
                target_context=state.target_context,
                custom_tasks=state.planned_tasks if state.planned_tasks else None
            )
            
            if result.status == TaskStatus.COMPLETED:
                self._execution_stats["subgraph_success"] += 1
                logger.info(f"[{task_id}] ✅ 子图执行成功")
                return self._convert_orchestrator_result_to_state(result, state)
            else:
                raise Exception(f"子图执行失败: {result.status}")
                
        except Exception as e:
            self._execution_stats["subgraph_failed"] += 1
            logger.warning(f"[{task_id}] ⚠️ 子图执行失败: {str(e)}")
            
            if self.enable_fallback and decision.fallback_mode:
                logger.info(f"[{task_id}] 🔄 触发降级机制: {decision.fallback_mode.value}")
                self._execution_stats["fallback_triggered"] += 1
                return await self._execute_fullgraph(state, decision)
            
            raise
    
    async def _execute_fullgraph(
        self,
        state: AgentState,
        decision: RoutingDecision
    ) -> AgentState:
        """
        使用大图执行任务
        
        适用于复杂任务，功能完整。
        
        Args:
            state: Agent当前状态
            decision: 路由决策
            
        Returns:
            AgentState: 最终状态
        """
        task_id = state.task_id
        logger.info(f"[{task_id}] 🏗️ 使用大图执行任务")
        _log_edge_traversal(
            task_id=task_id,
            from_node="SubgraphRouter",
            to_node="ScanAgentGraph",
            condition=f"mode={ExecutionMode.FULLGRAPH.value}"
        )
        
        try:
            result = await self.fullgraph.invoke(state)
            self._execution_stats["fullgraph_success"] += 1
            logger.info(f"[{task_id}] ✅ 大图执行成功")
            return result
            
        except Exception as e:
            self._execution_stats["fullgraph_failed"] += 1
            logger.error(f"[{task_id}] ❌ 大图执行失败: {str(e)}")
            _log_error(task_id, "_execute_fullgraph", e, {"target": state.target})
            raise
    
    async def _execute_hybrid(
        self,
        state: AgentState,
        decision: RoutingDecision
    ) -> AgentState:
        """
        使用混合模式执行任务
        
        先尝试子图执行，失败时降级到大图。
        
        Args:
            state: Agent当前状态
            decision: 路由决策
            
        Returns:
            AgentState: 最终状态
        """
        task_id = state.task_id
        logger.info(f"[{task_id}] 🔀 使用混合模式执行任务")
        _log_edge_traversal(
            task_id=task_id,
            from_node="SubgraphRouter",
            to_node="HybridExecution",
            condition=f"mode={ExecutionMode.HYBRID.value}"
        )
        
        try:
            logger.info(f"[{task_id}] 📋 混合模式：首先尝试子图执行")
            result = await self.subgraph_orchestrator.execute_scan(
                target=state.target,
                task_id=task_id,
                target_context=state.target_context,
                custom_tasks=state.planned_tasks if state.planned_tasks else None
            )
            
            if result.status == TaskStatus.COMPLETED:
                self._execution_stats["subgraph_success"] += 1
                logger.info(f"[{task_id}] ✅ 混合模式：子图执行成功")
                return self._convert_orchestrator_result_to_state(result, state)
            else:
                raise Exception(f"子图执行未完成: {result.status}")
                
        except Exception as e:
            logger.warning(f"[{task_id}] ⚠️ 混合模式：子图执行失败: {str(e)}")
            self._execution_stats["subgraph_failed"] += 1
            
            if self.enable_fallback:
                logger.info(f"[{task_id}] 🔄 混合模式：降级到大图执行")
                self._execution_stats["fallback_triggered"] += 1
                return await self._execute_fullgraph(state, decision)
            
            raise
    
    def _convert_orchestrator_result_to_state(
        self,
        result: OrchestratorResultDTO,
        original_state: AgentState
    ) -> AgentState:
        """
        将编排器结果转换为AgentState
        
        Args:
            result: 编排器执行结果
            original_state: 原始Agent状态
            
        Returns:
            AgentState: 转换后的Agent状态
        """
        original_state.is_complete = True
        
        if result.tool_result and result.tool_result.tool_results:
            if isinstance(result.tool_result.tool_results, dict):
                original_state.tool_results.update(result.tool_result.tool_results)
        
        if result.code_scan_result and result.code_scan_result.findings:
            for finding in result.code_scan_result.findings:
                if finding not in original_state.vulnerabilities:
                    original_state.vulnerabilities.append(finding)
        
        for poc_result in result.poc_results:
            if poc_result.vulnerabilities:
                for vuln in poc_result.vulnerabilities:
                    if vuln not in original_state.vulnerabilities:
                        original_state.vulnerabilities.append(vuln)
        
        if result.report:
            original_state.final_report = result.report.to_dict() if hasattr(result.report, 'to_dict') else result.report
        
        original_state.target_context["orchestrator_result"] = result.to_dict() if hasattr(result, 'to_dict') else {}
        
        return original_state
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        获取执行统计信息
        
        Returns:
            Dict[str, Any]: 执行统计信息
        """
        total = (
            self._execution_stats["subgraph_success"] +
            self._execution_stats["subgraph_failed"] +
            self._execution_stats["fullgraph_success"] +
            self._execution_stats["fullgraph_failed"]
        )
        
        return {
            **self._execution_stats,
            "total_executions": total,
            "subgraph_success_rate": (
                self._execution_stats["subgraph_success"] / 
                max(self._execution_stats["subgraph_success"] + self._execution_stats["subgraph_failed"], 1)
            ),
            "fullgraph_success_rate": (
                self._execution_stats["fullgraph_success"] / 
                max(self._execution_stats["fullgraph_success"] + self._execution_stats["fullgraph_failed"], 1)
            ),
            "fallback_rate": (
                self._execution_stats["fallback_triggered"] / max(total, 1)
            )
        }
    
    def get_routing_history(self, task_id: str = None) -> Union[Dict[str, RoutingDecision], Optional[RoutingDecision]]:
        """
        获取路由历史
        
        Args:
            task_id: 任务ID，如果为None则返回所有历史
            
        Returns:
            路由决策历史
        """
        if task_id:
            return self.task_router.get_routing_history(task_id)
        return self.task_router.get_all_routing_history()
    
    def clear_routing_history(self, task_id: str = None) -> None:
        """
        清除路由历史
        
        Args:
            task_id: 任务ID，如果为None则清除所有历史
        """
        self.task_router.clear_history(task_id)


def create_agent_graph() -> ScanAgentGraph:
    """
    创建Agent图实例（向后兼容）
    
    注意：推荐使用create_subgraph_router()获取更优的执行效率。
    
    Returns:
        ScanAgentGraph: Agent图实例
    """
    return ScanAgentGraph()


def create_subgraph_router(
    enable_fallback: bool = True,
    simple_threshold: float = 0.3,
    complex_threshold: float = 0.7,
    **kwargs
) -> SubgraphRouter:
    """
    创建子图路由器实例（推荐）
    
    子图路由器优先使用子图执行，效率更高。
    当子图无法处理时自动降级到大图。
    
    Args:
        enable_fallback: 是否启用降级机制
        simple_threshold: 简单任务阈值（0-1）
        complex_threshold: 复杂任务阈值（0-1）
        **kwargs: 其他超时配置参数
        
    Returns:
        SubgraphRouter: 子图路由器实例
    """
    return SubgraphRouter(
        enable_fallback=enable_fallback,
        simple_threshold=simple_threshold,
        complex_threshold=complex_threshold,
        **kwargs
    )


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

    # 注册AWVS扫描工具
    registry.register(
        name="awvs",
        func=PluginAdapter.adapt_awvs,
        description="AWVS全自动漏洞扫描(包含SQL注入/XSS等深度扫描)",
        category="scanner",
        timeout=3600,  # AWVS扫描时间较长
        priority=6     # 最高优先级
    )
    
    # 注册POC - 使用lambda创建闭包来传递POC模块
    pocs = POCAdapter.get_all_pocs()
    for poc_name, poc_module in pocs.items():
        # 创建一个闭包来捕获poc_name和poc_module
        def make_poc_wrapper(name, module):
            async def poc_wrapper(target: str, **kwargs):
                return await POCAdapter.adapt_poc(target, name, module, **kwargs)
            return poc_wrapper
        
        registry.register(
            name=poc_name,
            func=make_poc_wrapper(poc_name, poc_module),
            description=f"POC验证: {poc_name}",
            category="poc",
            timeout=30,
            priority=8
        )
    
    # 注册依赖管理工具
    from ..tools.adapters import DependencyAdapter
    
    registry.register(
        name="install_dependencies",
        func=DependencyAdapter.adapt_install_dependencies,
        description="安装Python包依赖",
        category="dependency",
        timeout=300,
        priority=9
    )
    
    registry.register(
        name="check_package",
        func=DependencyAdapter.adapt_check_package,
        description="检查Python包是否已安装",
        category="dependency",
        timeout=10,
        priority=9
    )
    
    registry.register(
        name="list_packages",
        func=DependencyAdapter.adapt_get_packages,
        description="列出已安装的Python包",
        category="dependency",
        timeout=10,
        priority=9
    )
    
    logger.info(f"✅ 工具初始化完成,共注册 {len(registry.tools)} 个工具")

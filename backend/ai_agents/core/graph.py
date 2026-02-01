"""
LangGraph 图构建(增强版)

构建支持自主规划、代码生成、环境感知的完整Agent工作流。

日志记录:
- 时间戳:所有日志包含时间戳
- 操作类型:节点进入/退出、状态变更、决策结果、错误信息
- 对象标识:任务ID、节点名称、状态键名
- 详细描述:操作的具体内容和结果
"""
import logging
import time
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from .state import AgentState
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
    POCVerificationNode
)

# 创建节点实例
seebug_agent_node = SeebugAgentNode()
poc_verification_node = POCVerificationNode()
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
                "seebug_agent": "seebug_agent"  # Seebug Agent(新增)
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
                "poc_verify": "poc_verification"  # 进入 POC 验证(新增)
            }
        )
        
        # POC 验证流程:POC 验证 → 漏洞分析
        workflow.add_edge("poc_verification", "vulnerability_analysis")
        
        # Seebug Agent流程:Seebug Agent → POC 验证
        workflow.add_edge("seebug_agent", "poc_verification")
        
        # 后续流程:分析→报告→结束
        workflow.add_edge("vulnerability_analysis", "report_generation")
        workflow.add_edge("report_generation", END)
        
        logger.info("📊 增强版LangGraph图边定义完成")
        _log_node_exit("_build_graph", "GRAPH_BUILD", "success", {"nodes_count": 11, "edges_count": 16})
        return workflow
    
    def _should_continue_or_verify(self, state: AgentState) -> Literal["continue", "analyze", "poc_verify"]:
        """
        判断是否继续执行工具或进入 POC 验证
        
        Args:
            state: Agent当前状态
            
        Returns:
            Literal["continue", "analyze", "poc_verify"]: 下一步节点名称
        """
        # 检查是否有待验证的 POC 任务
        if state.poc_verification_tasks and len(state.poc_verification_tasks) > 0:
            logger.info(f"[{state.task_id}] 📋 发现待验证的 POC 任务,进入 POC 验证节点")
            return "poc_verify"
        
        # 原有逻辑:所有任务已完成,进入分析阶段
        if state.is_complete or not state.planned_tasks:
            logger.info(f"[{state.task_id}] 📋 所有任务已完成,进入分析阶段")
            return "analyze"
        else:
            logger.info(f"[{state.task_id}] 🔄 继续执行工具: {state.current_task}")
            return "continue"
    
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
    
    def _decide_scan_type(self, state: AgentState) -> Literal["fixed_tool", "custom_code", "enhance_first", "poc_verification", "seebug_agent"]:
        """
        智能决策:选择扫描类型(核心分支逻辑)
        
        根据环境信息和目标特征,智能决定使用固定工具扫描、
        生成自定义代码扫描,还是先增强功能再扫描,或者进行 POC 验证,或者使用 Seebug Agent。
        
        Args:
            state: Agent当前状态
            
        Returns:
            Literal["fixed_tool", "custom_code", "enhance_first", "poc_verification", "seebug_agent"]: 扫描类型
        """
        target_context = state.target_context
        
        # 1. 检查是否有待验证的 POC 任务
        if state.poc_verification_tasks and len(state.poc_verification_tasks) > 0:
            logger.info(f"[{state.task_id}] 🔍 发现 POC 验证任务,进入 POC 验证流程")
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
            _log_decision(
                task_id=state.task_id,
                decision_type="SCAN_TYPE",
                decision="seebug_agent",
                reason="使用Seebug Agent"
            )
            return "seebug_agent"
        
        # 5. 其他情况→使用现有工具
        else:
            logger.info(f"[{state.task_id}] 🛠️ 使用现有工具执行扫描")
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
        
        if execution_result.get("status") == "success":
            logger.info(f"[{state.task_id}] ✅ 代码执行成功,继续验证结果")
            _log_decision(
                task_id=state.task_id,
                decision_type="CODE_EXECUTION",
                decision="success",
                reason="代码执行成功"
            )
            return "success"
        else:
            # 执行失败时,标记需要功能增强
            logger.warning(f"[{state.task_id}] ⚠️ 代码执行失败,需要功能增强")
            _log_decision(
                task_id=state.task_id,
                decision_type="CODE_EXECUTION",
                decision="need_enhance",
                reason=f"代码执行失败: {execution_result.get('error', 'unknown')}"
            )
            state.target_context["need_capability_enhancement"] = True
            state.target_context["capability_requirement"] = "自动安装代码执行所需依赖"
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
        
        if enhancement_result.get("status") == "success":
            logger.info(f"[{state.task_id}] ✅ 功能补充成功,重试代码执行")
            _log_decision(
                task_id=state.task_id,
                decision_type="CAPABILITY_ENHANCEMENT",
                decision="success",
                reason="功能补充成功"
            )
            return "success"
        else:
            logger.warning(f"[{state.task_id}] ⚠️ 功能补充失败,继续验证结果")
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
        获取图信息(包含所有12个节点)
        
        Returns:
            Dict: 图结构信息
        """
        return {
            "nodes": [
                "environment_awareness",  # 新增
                "task_planning",
                "intelligent_decision",  # 新增
                "tool_execution",
                "code_generation",  # 新增
                "code_execution",  # 新增
                "capability_enhancement",  # 新增
                "result_verification",
                "poc_verification",  # 新增
                "seebug_agent",  # 新增
                "vulnerability_analysis",
                "report_generation"
            ],
            "edges": [
                ("environment_awareness", "task_planning"),  # 新增
                ("task_planning", "intelligent_decision"),  # 新增
                ("intelligent_decision", "tool_execution"),
                ("intelligent_decision", "code_generation"),  # 新增
                ("intelligent_decision", "capability_enhancement"),  # 新增
                ("intelligent_decision", "poc_verification"),  # 新增
                ("intelligent_decision", "seebug_agent"),  # 新增
                ("code_generation", "code_execution"),  # 新增
                ("code_execution", "result_verification"),
                ("code_execution", "capability_enhancement"),  # 新增
                ("capability_enhancement", "code_execution"),  # 新增
                ("tool_execution", "result_verification"),
                ("result_verification", "tool_execution"),
                ("result_verification", "vulnerability_analysis"),
                ("result_verification", "poc_verification"),  # 新增
                ("poc_verification", "vulnerability_analysis"),  # 新增
                ("seebug_agent", "poc_verification"),  # 新增
                ("vulnerability_analysis", "report_generation"),
                ("report_generation", "END")
            ],
            "entry_point": "environment_awareness",  # 更新为环境感知
            "exit_points": ["report_generation"],
            "total_nodes": 12,  # 更新为12个节点
            "original_nodes": 5,  # 原有节点数
            "new_nodes": 7  # 新增节点数
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
    
    # 注册插件
    registry.register(
        name="baseinfo",
        func=PluginAdapter.adapt_baseinfo(),
        description="基础信息收集(域名、IP、服务器、OS等)",
        category="plugin",
        timeout=10,
        priority=3
    )
    
    registry.register(
        name="portscan",
        func=PluginAdapter.adapt_portscan(),
        description="TCP端口扫描,识别开放端口和服务",
        category="plugin",
        timeout=120,
        priority=5
    )
    
    registry.register(
        name="waf_detect",
        func=PluginAdapter.adapt_waf_detect(),
        description="WAF(Web应用防火墙)检测",
        category="plugin",
        timeout=10,
        priority=4
    )
    
    registry.register(
        name="cdn_detect",
        func=PluginAdapter.adapt_cdn_detect(),
        description="CDN(内容分发网络)检测",
        category="plugin",
        timeout=10,
        priority=4
    )
    
    registry.register(
        name="cms_identify",
        func=PluginAdapter.adapt_cms_identify(),
        description="CMS(内容管理系统)识别",
        category="plugin",
        timeout=15,
        priority=4
    )
    
    registry.register(
        name="infoleak_scan",
        func=PluginAdapter.adapt_infoleak_scan(),
        description="信息泄露扫描",
        category="plugin",
        timeout=30,
        priority=3
    )
    
    registry.register(
        name="subdomain_scan",
        func=PluginAdapter.adapt_subdomain_scan(),
        description="子域名枚举",
        category="plugin",
        timeout=60,
        priority=3
    )
    
    registry.register(
        name="webside_scan",
        func=PluginAdapter.adapt_webside_scan(),
        description="站点信息收集",
        category="plugin",
        timeout=30,
        priority=3
    )
    
    registry.register(
        name="webweight_scan",
        func=PluginAdapter.adapt_webweight_scan(),
        description="网站权重查询",
        category="plugin",
        timeout=30,
        priority=2
    )
    
    # 注册POC
    pocs = POCAdapter.get_all_pocs()
    for poc_name, poc_module in pocs.items():
        poc_wrapper = POCAdapter.adapt_poc(poc_name, poc_module)
        registry.register(
            name=poc_name,
            func=poc_wrapper,
            description=f"POC验证: {poc_name}",
            category="poc",
            timeout=30,
            priority=8
        )
    
    # 注册依赖管理工具
    from ..tools.adapters import DependencyAdapter
    
    registry.register(
        name="install_dependencies",
        func=DependencyAdapter.adapt_install_dependencies(),
        description="安装Python包依赖",
        category="dependency",
        timeout=300,
        priority=9
    )
    
    registry.register(
        name="check_package",
        func=DependencyAdapter.adapt_check_package(),
        description="检查Python包是否已安装",
        category="dependency",
        timeout=10,
        priority=9
    )
    
    registry.register(
        name="list_packages",
        func=DependencyAdapter.adapt_get_packages(),
        description="列出已安装的Python包",
        category="dependency",
        timeout=10,
        priority=9
    )
    
    logger.info(f"✅ 工具初始化完成,共注册 {len(registry.tools)} 个工具")

"""
LangGraph 图构建

构建Agent工作流的有向图，定义节点和边的连接关系。
"""
import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    TaskPlanningNode,
    ToolExecutionNode,
    ResultVerificationNode,
    VulnerabilityAnalysisNode,
    ReportGenerationNode
)
from .new_nodes import (
    EnvironmentAwarenessNode,
    CodeGenerationNode,
    CapabilityEnhancementNode,
    CodeExecutionNode,
    IntelligentDecisionNode
)
from ..config import agent_config

logger = logging.getLogger(__name__)


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
        
        # 创建节点实例
        self.env_awareness_node = EnvironmentAwarenessNode()
        self.planning_node = TaskPlanningNode()
        self.intelligent_decision_node = IntelligentDecisionNode()
        self.execution_node = ToolExecutionNode()
        self.code_generation_node = CodeGenerationNode()
        self.code_execution_node = CodeExecutionNode()
        self.capability_enhancement_node = CapabilityEnhancementNode()
        self.verification_node = ResultVerificationNode()
        self.analysis_node = VulnerabilityAnalysisNode()
        self.report_node = ReportGenerationNode()
        
        # 构建图
        self.graph = self._build_graph()
        
        logger.info("✅ 扫描Agent图构建完成")
    
    def _build_graph(self) -> StateGraph:
        """
        构建LangGraph图
        
        Returns:
            StateGraph: 编译后的图
        """
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("task_planning", self.planning_node)
        workflow.add_node("tool_execution", self.execution_node)
        workflow.add_node("result_verification", self.verification_node)
        workflow.add_node("vulnerability_analysis", self.analysis_node)
        workflow.add_node("report_generation", self.report_node)
        
        # 设置入口点
        workflow.set_entry_point("task_planning")
        
        # 定义边（核心流程）
        workflow.add_edge("task_planning", "tool_execution")
        workflow.add_edge("tool_execution", "result_verification")
        
        # 条件边：验证后判断是否继续执行工具
        workflow.add_conditional_edges(
            "result_verification",
            self._should_continue,
            {
                "continue": "tool_execution",
                "analyze": "vulnerability_analysis"
            }
        )
        
        # 后续流程
        workflow.add_edge("vulnerability_analysis", "report_generation")
        workflow.add_edge("report_generation", END)
        
        logger.info("📊 LangGraph图边定义完成")
        return workflow
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "analyze"]:
        """
        判断是否继续执行工具
        
        Args:
            state: Agent当前状态
            
        Returns:
            Literal["continue", "analyze"]: 下一步节点名称
        """
        if state.is_complete or not state.planned_tasks:
            logger.info(f"[{state.task_id}] 📋 所有任务已完成，进入分析阶段")
            return "analyze"
        else:
            logger.info(f"[{state.task_id}] 🔄 继续执行工具: {state.current_task}")
            return "continue"
    
    def compile(self):
        """
        编译图
        
        Returns:
            编译后的可执行图
        """
        return self.graph.compile()
    
    async def invoke(self, initial_state: AgentState) -> AgentState:
        """
        执行Agent工作流
        
        Args:
            initial_state: 初始状态
            
        Returns:
            AgentState: 最终状态
        """
        logger.info(f"🚀 开始执行Agent工作流: {initial_state.task_id}")
        
        compiled_graph = self.compile()
        final_state = await compiled_graph.ainvoke(initial_state)
        
        logger.info(f"✅ Agent工作流执行完成: {final_state.task_id}")
        return final_state
    
    def get_graph_info(self) -> Dict[str, Any]:
        """
        获取图信息
        
        Returns:
            Dict: 图结构信息
        """
        return {
            "nodes": [
                "task_planning",
                "tool_execution",
                "result_verification",
                "vulnerability_analysis",
                "report_generation"
            ],
            "edges": [
                ("task_planning", "tool_execution"),
                ("tool_execution", "result_verification"),
                ("result_verification", "tool_execution"),
                ("result_verification", "vulnerability_analysis"),
                ("vulnerability_analysis", "report_generation"),
                ("report_generation", "END")
            ],
            "entry_point": "task_planning",
            "exit_points": ["report_generation"]
        }
    
    def visualize(self) -> str:
        """
        生成图的可视化文本
        
        Returns:
            str: Mermaid格式的图描述
        """
        return """
graph TD
    A[环境感知] --> B[任务规划]
    B --> C[智能决策]
    C --> D[工具执行]
    D --> E[结果验证]
    E -->|继续执行| D
    E -->|需要代码生成| F[代码生成]
    E -->|完成所有任务| G[漏洞分析]
    F --> H[代码执行]
    H --> I[功能补充]
    I --> E
    G --> J[报告生成]
    J --> K[结束]
    
    style A fill:#e1f5ff
    style B fill:#fff3cd
    style C fill:#e8f5e9
    style D fill:#fff3cd
    style E fill:#d4edda
    style F fill:#f8d7da
    style H fill:#f8d7da
    style I fill:#fce4ec
    style G fill:#f8d7da
    style J fill:#fce4ec
    style K fill:#c3e6cb
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
    from .tools.registry import registry
    from .tools.adapters import PluginAdapter, POCAdapter
    
    logger.info("🔧 开始初始化工具...")
    
    # 注册插件
    registry.register(
        name="baseinfo",
        func=PluginAdapter.adapt_baseinfo(),
        description="基础信息收集（域名、IP、服务器、OS等）",
        category="plugin",
        timeout=10,
        priority=3
    )
    
    registry.register(
        name="portscan",
        func=PluginAdapter.adapt_portscan(),
        description="TCP端口扫描，识别开放端口和服务",
        category="plugin",
        timeout=120,
        priority=5
    )
    
    registry.register(
        name="waf_detect",
        func=PluginAdapter.adapt_waf_detect(),
        description="WAF（Web应用防火墙）检测",
        category="plugin",
        timeout=10,
        priority=4
    )
    
    registry.register(
        name="cdn_detect",
        func=PluginAdapter.adapt_cdn_detect(),
        description="CDN（内容分发网络）检测",
        category="plugin",
        timeout=10,
        priority=4
    )
    
    registry.register(
        name="cms_identify",
        func=PluginAdapter.adapt_cms_identify(),
        description="CMS（内容管理系统）识别",
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
    
    logger.info(f"✅ 工具初始化完成，共注册 {len(registry.tools)} 个工具")


# 初始化工具（模块加载时自动执行）
initialize_tools()

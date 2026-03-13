"""
AI Agents 核心模块

包含Agent状态管理、LangGraph图构建和节点定义。
"""

__all__ = [
    "AgentState",
    "ScanAgentGraph",
    "TaskPlanningNode",
    "ToolExecutionNode",
    "ResultVerificationNode",
    "VulnerabilityAnalysisNode",
    "ReportGenerationNode"
]


def __getattr__(name):
    """延迟导入以避免依赖问题"""
    if name == "AgentState":
        from .state import AgentState
        return AgentState
    elif name == "ScanAgentGraph":
        from .graph import ScanAgentGraph
        return ScanAgentGraph
    elif name in [
        "TaskPlanningNode",
        "ToolExecutionNode",
        "ResultVerificationNode",
        "VulnerabilityAnalysisNode",
        "ReportGenerationNode"
    ]:
        from .nodes import (
            TaskPlanningNode,
            ToolExecutionNode,
            ResultVerificationNode,
            VulnerabilityAnalysisNode,
            ReportGenerationNode
        )
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

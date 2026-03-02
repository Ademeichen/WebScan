"""
AI Agents 工具模块

包含工具注册表、工具封装和工具适配器。
"""

from .registry import ToolRegistry, register_tool
from .wrappers import AsyncToolWrapper
from .adapters import PluginAdapter, POCAdapter
from .tool_recommender import (
    ToolRecommender,
    TargetProfile,
    ToolRecommendation,
    RecommendationSource,
    create_target_profile,
    get_recommended_tools
)

__all__ = [
    "ToolRegistry",
    "register_tool",
    "AsyncToolWrapper",
    "PluginAdapter",
    "POCAdapter",
    "ToolRecommender",
    "TargetProfile",
    "ToolRecommendation",
    "RecommendationSource",
    "create_target_profile",
    "get_recommended_tools"
]

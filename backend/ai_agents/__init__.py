"""
AI Agents 模块

基于LangGraph的Web安全漏洞扫描Agent智能体编排系统。
提供自主任务规划、工具调用、结果迭代验证、漏洞分析与报告生成功能。

主要模块：
- core: 核心框架（状态管理、图构建、节点定义）
- tools: 工具集成（注册表、封装、适配器）
- planners: 任务规划（规则化、LLM增强）
- analyzers: 结果分析（漏洞分析、报告生成）
- memory: 记忆机制（上下文、历史）
- api: API路由（Agent扫描接口）
- utils: 工具函数（优先级、重试策略）
"""

from .core import ScanAgentGraph
from .tools import ToolRegistry
from .memory import AgentMemory

__version__ = "1.0.0"
__all__ = ["ScanAgentGraph", "ToolRegistry", "AgentMemory"]

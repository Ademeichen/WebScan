# sandbox/__init__.py
"""
Sandbox模块 - 核心业务执行层
提供代码执行和命令执行功能
"""

from .core_executor import CodeExecutor

__version__ = "1.0.0"
__author__ = "Sandbox Team"
__all__ = ['CodeExecutor']
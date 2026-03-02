"""
POC 系统模块.

提供 POC 管理、目标管理、验证执行、结果分析和报告生成功能。
"""

from .poc_manager import POCMetadata, poc_manager
from .report_generator import ReportGenerator, report_generator
from .result_analyzer import AnalysisResult, BatchAnalysisSummary, result_analyzer
from .target_manager import TargetInfo, target_manager
from .verification_engine import ExecutionConfig, ExecutionStats, verification_engine

__all__ = [
    "poc_manager",
    "POCMetadata",
    "target_manager",
    "TargetInfo",
    "verification_engine",
    "ExecutionConfig",
    "ExecutionStats",
    "result_analyzer",
    "AnalysisResult",
    "BatchAnalysisSummary",
    "report_generator",
    "ReportGenerator",
]

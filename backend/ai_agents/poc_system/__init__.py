"""
POC 系统模块

提供 POC 管理、目标管理、验证执行、结果分析和报告生成功能。
"""
from .poc_manager import poc_manager, POCMetadata
from .target_manager import target_manager, TargetInfo
from .verification_engine import verification_engine, ExecutionConfig, ExecutionStats
from .result_analyzer import result_analyzer, AnalysisResult, BatchAnalysisSummary
from .report_generator import report_generator, ReportGenerator

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
    "ReportGenerator"
]

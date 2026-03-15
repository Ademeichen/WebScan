"""
AI Agents 分析器模块

包含漏洞分析器、报告生成器和智能结果分析器。
"""

__all__ = []

def __getattr__(name):
    if name == "VulnerabilityAnalyzer":
        from .vuln_analyzer import VulnerabilityAnalyzer
        return VulnerabilityAnalyzer
    elif name in ["ReportGenerator", "EnhancedReportGenerator", "EnhancedReportData", "ReportFormat"]:
        from .enhanced_report_gen import (
            ReportGenerator, EnhancedReportGenerator, EnhancedReportData, ReportFormat
        )
        if name == "ReportGenerator":
            return ReportGenerator
        elif name == "EnhancedReportGenerator":
            return EnhancedReportGenerator
        elif name == "EnhancedReportData":
            return EnhancedReportData
        elif name == "ReportFormat":
            return ReportFormat
    elif name in ["AIAnalyzer", "AIAnalysisResult"]:
        from .ai_analyzer import AIAnalyzer, AIAnalysisResult
        if name == "AIAnalyzer":
            return AIAnalyzer
        elif name == "AIAnalysisResult":
            return AIAnalysisResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

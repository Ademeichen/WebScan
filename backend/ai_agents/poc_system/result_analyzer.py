"""
结果分析器

负责分析 POC 验证结果,包括漏洞验证状态判定、漏洞等级评估、误报检测、结果置信度计算等。
"""
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


from backend.models import POCVerificationResult, POCExecutionLog
from backend.config import settings
from backend.ai_agents.poc_system.utils import (
    calculate_severity_distribution,
    calculate_statistics,
    get_high_risk_targets
)
from backend.utils.poc_utils import (
    get_false_positive_keywords,
    get_success_keywords
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """
    分析结果类
    
    用于存储单个 POC 验证结果的分析数据。
    """
    
    result_id: int
    poc_name: str
    poc_id: str
    target: str
    is_vulnerable: bool
    severity: str
    confidence: float
    cvss_score: float
    is_false_positive: bool
    risk_level: str
    recommendations: List[str]
    analysis_details: Dict[str, Any]


@dataclass
class BatchAnalysisSummary:
    """
    批量分析摘要类
    
    用于存储批量 POC 验证结果的分析摘要。
    """
    
    total_results: int
    vulnerable_count: int
    not_vulnerable_count: int
    false_positive_count: int
    true_positive_count: int
    severity_distribution: Dict[str, int]
    average_confidence: float
    average_cvss_score: float
    high_risk_targets: List[str]
    recommendations: List[str]


class ResultAnalyzer:
    """
    结果分析器类
    
    负责分析 POC 验证结果,包括:
    - 漏洞验证状态判定
    - 漏洞等级评估
    - 误报检测
    - 结果置信度计算
    - 风险评估
    - 修复建议生成
    """
    
    def __init__(self):
        """
        初始化结果分析器
        """
        self.false_positive_keywords = get_false_positive_keywords()
        self.success_keywords = get_success_keywords()
        
        logger.info("✅ 结果分析器初始化完成")
    
    async def analyze_single_result(
        self,
        result: POCVerificationResult
    ) -> AnalysisResult:
        """
        分析单个 POC 验证结果
        
        Args:
            result: POC 验证结果对象
            
        Returns:
            AnalysisResult: 分析结果
        """
        logger.info(f"🔍 开始分析结果: {result.poc_name}")
        
        # 获取执行日志
        logs = await POCExecutionLog.filter(
            verification_result=result.id
        ).order_by("timestamp")
        
        # 判断是否为误报
        is_false_positive = self._detect_false_positive(result, logs)
        
        # 计算风险等级
        risk_level = self._calculate_risk_level(result, is_false_positive)
        
        # 生成修复建议
        recommendations = self._generate_recommendations(result, is_false_positive)
        
        # 分析详情
        analysis_details = {
            "false_positive_indicators": self._get_false_positive_indicators(result),
            "success_indicators": self._get_success_indicators(result),
            "confidence_factors": self._get_confidence_factors(result),
            "execution_logs_count": len(logs),
            "has_errors": any(log.log_level == "error" for log in logs)
        }
        
        analysis_result = AnalysisResult(
            result_id=result.id,
            poc_name=result.poc_name,
            poc_id=result.poc_id,
            target=result.target,
            is_vulnerable=result.vulnerable,
            severity=result.severity or "info",
            confidence=result.confidence,
            cvss_score=result.cvss_score or 0.0,
            is_false_positive=is_false_positive,
            risk_level=risk_level,
            recommendations=recommendations,
            analysis_details=analysis_details
        )
        
        logger.info(f"✅ 结果分析完成: {result.poc_name}, 风险等级: {risk_level}")
        return analysis_result
    
    async def analyze_batch_results(
        self,
        results: List[POCVerificationResult]
    ) -> BatchAnalysisSummary:
        """
        批量分析 POC 验证结果
        
        Args:
            results: POC 验证结果列表
            
        Returns:
            BatchAnalysisSummary: 批量分析摘要
        """
        logger.info(f"🔍 开始批量分析,结果数: {len(results)}")
        
        analysis_results = []
        for result in results:
            analysis = await self.analyze_single_result(result)
            analysis_results.append(analysis)
        
        # 统计数据
        total_results = len(results)
        vulnerable_count = sum(1 for a in analysis_results if a.is_vulnerable)
        not_vulnerable_count = total_results - vulnerable_count
        false_positive_count = sum(1 for a in analysis_results if a.is_false_positive)
        true_positive_count = vulnerable_count - false_positive_count
        
        # 严重度分布
        severity_distribution = {}
        for analysis in analysis_results:
            severity = analysis.severity
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # 平均置信度和 CVSS 评分
        average_confidence = sum(a.confidence for a in analysis_results) / total_results if total_results > 0 else 0.0
        average_cvss_score = sum(a.cvss_score for a in analysis_results) / total_results if total_results > 0 else 0.0
        
        # 高风险目标
        high_risk_targets = get_high_risk_targets(results)
        
        # 生成批量建议
        recommendations = self._generate_batch_recommendations(analysis_results)
        
        summary = BatchAnalysisSummary(
            total_results=total_results,
            vulnerable_count=vulnerable_count,
            not_vulnerable_count=not_vulnerable_count,
            false_positive_count=false_positive_count,
            true_positive_count=true_positive_count,
            severity_distribution=severity_distribution,
            average_confidence=average_confidence,
            average_cvss_score=average_cvss_score,
            high_risk_targets=high_risk_targets,
            recommendations=recommendations
        )
        
        logger.info(f"✅ 批量分析完成,漏洞: {vulnerable_count}, 误报: {false_positive_count}")
        return summary
    
    def _detect_false_positive(
        self,
        result: POCVerificationResult,
        logs: List[POCExecutionLog]
    ) -> bool:
        """
        检测误报
        
        Args:
            result: POC 验证结果
            logs: 执行日志
            
        Returns:
            bool: 是否为误报
        """
        # 如果结果明确显示存在漏洞,不太可能是误报
        if result.vulnerable and result.confidence > settings.POC_RESULT_ACCURACY_THRESHOLD:
            return False
        
        # 检查输出中的误报关键词
        if result.output:
            output_lower = result.output.lower()
            for keyword in self.false_positive_keywords:
                if keyword in output_lower:
                    return True
        
        # 检查错误信息
        if result.error:
            error_lower = result.error.lower()
            for keyword in self.false_positive_keywords:
                if keyword in error_lower:
                    return True
        
        # 检查执行日志中的错误
        for log in logs:
            if log.log_level == "error":
                log_lower = log.message.lower()
                for keyword in self.false_positive_keywords:
                    if keyword in log_lower:
                        return True
        
        # 检查置信度是否过低
        if result.confidence < 0.3:
            return True
        
        return False
    
    def _calculate_risk_level(
        self,
        result: POCVerificationResult,
        is_false_positive: bool
    ) -> str:
        """
        计算风险等级
        
        Args:
            result: POC 验证结果
            is_false_positive: 是否为误报
            
        Returns:
            str: 风险等级(critical, high, medium, low, info)
        """
        # 如果是误报,风险等级为 info
        if is_false_positive:
            return "info"
        
        # 如果不存在漏洞,风险等级为 low
        if not result.vulnerable:
            return "low"
        
        # 根据严重度和 CVSS 评分确定风险等级
        severity = result.severity or "info"
        cvss_score = result.cvss_score or 0.0
        
        if cvss_score >= 9.0:
            return "critical"
        elif cvss_score >= 7.0:
            return "high"
        elif cvss_score >= 4.0:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(
        self,
        result: POCVerificationResult,
        is_false_positive: bool
    ) -> List[str]:
        """
        生成修复建议
        
        Args:
            result: POC 验证结果
            is_false_positive: 是否为误报
            
        Returns:
            List[str]: 修复建议列表
        """
        recommendations = []
        
        if is_false_positive:
            recommendations.append("此结果可能是误报,建议进行人工验证")
            recommendations.append("检查网络连接是否正常")
            recommendations.append("确认目标服务是否正常运行")
        elif result.vulnerable:
            recommendations.append(f"确认漏洞存在: {result.poc_name}")
            recommendations.append("评估漏洞对业务的影响范围")
            recommendations.append("制定修复计划并优先处理高风险漏洞")
            
            # 根据严重度生成具体建议
            if result.severity in ["critical", "high"]:
                recommendations.append("立即修复此漏洞")
                recommendations.append("考虑临时缓解措施")
            elif result.severity == "medium":
                recommendations.append("在下一个维护窗口修复")
            else:
                recommendations.append("按计划修复")
        else:
            recommendations.append("未发现漏洞")
            recommendations.append("继续监控目标系统")
        
        return recommendations
    
    def _generate_batch_recommendations(
        self,
        analysis_results: List[AnalysisResult]
    ) -> List[str]:
        """
        生成批量修复建议
        
        Args:
            analysis_results: 分析结果列表
            
        Returns:
            List[str]: 修复建议列表
        """
        recommendations = []
        
        # 统计高风险目标
        high_risk_targets = set(
            a.target for a in analysis_results
            if a.risk_level in ["critical", "high"]
        )
        
        if high_risk_targets:
            recommendations.append(f"发现 {len(high_risk_targets)} 个高风险目标,需要立即处理")
            recommendations.append("优先处理 critical 和 high 级别的漏洞")
        
        # 统计误报
        false_positive_count = sum(1 for a in analysis_results if a.is_false_positive)
        if false_positive_count > 0:
            recommendations.append(f"发现 {false_positive_count} 个可能的误报,建议人工验证")
        
        # 统计漏洞类型
        severity_distribution = {}
        for analysis in analysis_results:
            severity = analysis.severity
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        if severity_distribution.get("critical", 0) > 0:
            recommendations.append(f"存在 {severity_distribution['critical']} 个严重漏洞,需要紧急修复")
        
        if severity_distribution.get("high", 0) > 0:
            recommendations.append(f"存在 {severity_distribution['high']} 个高危漏洞,建议尽快修复")
        
        return recommendations
    
    def _get_false_positive_indicators(
        self,
        result: POCVerificationResult
    ) -> List[str]:
        """
        获取误报指示器
        
        Args:
            result: POC 验证结果
            
        Returns:
            List[str]: 误报指示器列表
        """
        indicators = []
        
        if result.error:
            indicators.append(f"存在错误: {result.error}")
        
        if result.confidence < 0.5:
            indicators.append(f"置信度较低: {result.confidence:.2f}")
        
        if result.output:
            output_lower = result.output.lower()
            for keyword in self.false_positive_keywords:
                if keyword in output_lower:
                    indicators.append(f"输出包含误报关键词: {keyword}")
        
        return indicators
    
    def _get_success_indicators(
        self,
        result: POCVerificationResult
    ) -> List[str]:
        """
        获取成功指示器
        
        Args:
            result: POC 验证结果
            
        Returns:
            List[str]: 成功指示器列表
        """
        indicators = []
        
        if result.vulnerable:
            indicators.append("POC 验证成功")
        
        if result.confidence > 0.8:
            indicators.append(f"置信度较高: {result.confidence:.2f}")
        
        if result.output:
            output_lower = result.output.lower()
            for keyword in self.success_keywords:
                if keyword in output_lower:
                    indicators.append(f"输出包含成功关键词: {keyword}")
        
        return indicators
    
    def _get_confidence_factors(
        self,
        result: POCVerificationResult
    ) -> Dict[str, Any]:
        """
        获取置信度因素
        
        Args:
            result: POC 验证结果
            
        Returns:
            Dict: 置信度因素字典
        """
        factors = {
            "base_confidence": result.confidence,
            "vulnerable_status": result.vulnerable,
            "has_output": bool(result.output),
            "has_error": bool(result.error),
            "output_length": len(result.output) if result.output else 0,
            "execution_time": result.execution_time
        }
        
        # 计算调整后的置信度
        adjusted_confidence = result.confidence
        
        if result.vulnerable:
            adjusted_confidence += 0.1
        elif result.error:
            adjusted_confidence -= 0.2
        
        if result.output and len(result.output) > 100:
            adjusted_confidence += 0.05
        
        factors["adjusted_confidence"] = min(adjusted_confidence, 1.0)
        
        return factors
    
    async def get_result_statistics(
        self,
        results: List[POCVerificationResult]
    ) -> Dict[str, Any]:
        """
        获取结果统计信息
        
        Args:
            results: POC 验证结果列表
            
        Returns:
            Dict: 统计信息字典
        """
        return calculate_statistics(results)


# 全局结果分析器实例
result_analyzer = ResultAnalyzer()

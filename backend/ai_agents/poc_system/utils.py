"""
POC 系统工具函数.

提供统计计算、数据处理等公共工具函数。
"""
from typing import Any, Dict, List, Set

from backend.models import POCVerificationResult


def calculate_severity_distribution(results: List[POCVerificationResult]) -> Dict[str, int]:
    """
    计算严重度分布.

    Args:
        results: POC验证结果列表.

    Returns:
        Dict[str, int]: 严重度分布字典.
    """
    distribution: Dict[str, int] = {}
    for result in results:
        severity = result.severity or "info"
        distribution[severity] = distribution.get(severity, 0) + 1
    return distribution


def calculate_statistics(results: List[POCVerificationResult]) -> Dict[str, Any]:
    """
    计算统计信息.

    Args:
        results: POC验证结果列表.

    Returns:
        Dict[str, Any]: 统计信息字典.
    """
    if not results:
        return {
            "total": 0,
            "vulnerable": 0,
            "not_vulnerable": 0,
            "vulnerability_rate": 0,
            "average_confidence": 0.0,
            "average_cvss_score": 0.0,
            "severity_distribution": {}
        }

    total = len(results)
    vulnerable_count = sum(1 for r in results if r.vulnerable)
    not_vulnerable_count = total - vulnerable_count

    severity_distribution = calculate_severity_distribution(results)

    average_confidence = sum(r.confidence for r in results) / total
    average_cvss_score = sum(r.cvss_score or 0 for r in results) / total

    return {
        "total": total,
        "vulnerable": vulnerable_count,
        "not_vulnerable": not_vulnerable_count,
        "vulnerability_rate": (vulnerable_count / total * 100) if total > 0 else 0,
        "average_confidence": average_confidence,
        "average_cvss_score": average_cvss_score,
        "severity_distribution": severity_distribution
    }


def calculate_average_execution_time(results: List[POCVerificationResult]) -> float:
    """
    计算平均执行时间.

    Args:
        results: POC验证结果列表.

    Returns:
        float: 平均执行时间.
    """
    if not results:
        return 0.0

    total_execution_time = sum(r.execution_time for r in results)
    return total_execution_time / len(results)


def get_high_risk_targets(results: List[Any]) -> List[str]:
    """
    获取高风险目标列表.

    Args:
        results: POC验证结果列表或分析结果列表.

    Returns:
        List[str]: 高风险目标列表.
    """
    high_risk_targets: Set[str] = set()

    for result in results:
        if hasattr(result, 'vulnerable') and hasattr(result, 'severity'):
            if result.vulnerable and result.severity in ["critical", "high"]:
                high_risk_targets.add(result.target)
        elif hasattr(result, 'risk_level'):
            if result.risk_level in ["critical", "high"]:
                high_risk_targets.add(result.target)

    return list(high_risk_targets)

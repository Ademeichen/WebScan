"""
智能结果分析器

实现漏洞结果去重、聚合、误报识别、补充扫描建议生成和风险评分功能。
"""
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from ..agent_config import agent_config

logger = logging.getLogger(__name__)


class VulnerabilitySource(Enum):
    """漏洞来源枚举"""
    POC_VERIFICATION = "poc_verification"
    AWVS_SCAN = "awvs_scan"
    CODE_SCAN = "code_scan"
    PORT_SCAN = "port_scan"
    MANUAL = "manual"
    OTHER = "other"


class RiskLevel(Enum):
    """风险等级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class VulnerabilityRecord:
    """漏洞记录数据结构"""
    vuln_id: str
    cve: Optional[str] = None
    name: str = ""
    vuln_type: str = ""
    target: str = ""
    url: str = ""
    severity: str = "info"
    confidence: float = 0.0
    cvss_score: float = 0.0
    source: str = ""
    description: str = ""
    solution: str = ""
    references: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_dedup_key(self) -> str:
        """
        获取去重键
        
        根据CVE、位置、类型生成唯一标识
        """
        key_parts = [
            self.cve or "",
            self.target or self.url,
            self.vuln_type,
            self.name
        ]
        key_str = "_".join(str(p) for p in key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()


@dataclass
class FalsePositiveRule:
    """误报规则数据结构"""
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    weight: float = 1.0
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FollowUpSuggestion:
    """补充扫描建议数据结构"""
    suggestion_id: str
    title: str
    description: str
    priority: str
    scan_type: str
    target: str
    reason: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyzedResult:
    """分析结果数据结构"""
    vulnerabilities: List[Dict[str, Any]]
    false_positives: List[Dict[str, Any]]
    risk_score: float
    follow_up_suggestions: List[str]
    confidence: float
    summary: str
    statistics: Dict[str, Any] = field(default_factory=dict)
    deduplication_stats: Dict[str, Any] = field(default_factory=dict)


class ResultAnalyzer:
    """
    智能结果分析器
    
    提供漏洞结果去重、聚合、误报识别、补充扫描建议生成和风险评分功能。
    
    Attributes:
        severity_order: 严重度排序权重
        false_positive_rules: 误报规则列表
        user_feedback: 用户反馈记录
    """
    
    def __init__(self):
        """初始化结果分析器"""
        self.severity_order = agent_config.SEVERITY_ORDER.copy()
        self.false_positive_rules: List[FalsePositiveRule] = []
        self.user_feedback: Dict[str, bool] = {}
        self._false_positive_patterns = self._init_false_positive_patterns()
        self._attack_surface_coverage: Dict[str, Set[str]] = {}
        
        self._init_default_false_positive_rules()
        
        logger.info("智能结果分析器初始化完成")
    
    def _init_false_positive_patterns(self) -> Dict[str, List[str]]:
        """初始化误报模式"""
        return {
            "error_patterns": [
                "timeout",
                "connection refused",
                "connection reset",
                "network unreachable",
                "dns resolution failed",
                "ssl error",
                "certificate error",
                "handshake failed",
                "socket error",
            ],
            "http_error_patterns": [
                "404 not found",
                "403 forbidden",
                "401 unauthorized",
                "500 internal server error",
                "502 bad gateway",
                "503 service unavailable",
                "504 gateway timeout",
            ],
            "false_positive_keywords": [
                "test",
                "example",
                "sample",
                "dummy",
                "placeholder",
                "localhost",
                "127.0.0.1",
            ],
            "success_patterns": [
                "vulnerability confirmed",
                "exploit successful",
                "poc verified",
                "vulnerable to",
            ]
        }
    
    def _init_default_false_positive_rules(self) -> None:
        """初始化默认误报规则"""
        default_rules = [
            {
                "rule_id": "fp_timeout",
                "name": "超时误报规则",
                "description": "因超时导致的误报",
                "conditions": {"has_timeout": True, "confidence_below": 0.3},
                "weight": 0.8
            },
            {
                "rule_id": "fp_connection_error",
                "name": "连接错误误报规则",
                "description": "因连接错误导致的误报",
                "conditions": {"has_connection_error": True, "no_output": True},
                "weight": 0.7
            },
            {
                "rule_id": "fp_low_confidence",
                "name": "低置信度规则",
                "description": "置信度过低的结果",
                "conditions": {"confidence_below": 0.2},
                "weight": 0.6
            },
            {
                "rule_id": "fp_test_target",
                "name": "测试目标规则",
                "description": "测试环境或示例目标",
                "conditions": {"is_test_target": True},
                "weight": 0.9
            },
            {
                "rule_id": "fp_http_error",
                "name": "HTTP错误规则",
                "description": "HTTP错误响应导致的误报",
                "conditions": {"has_http_error": True, "no_vuln_evidence": True},
                "weight": 0.7
            }
        ]
        
        for rule_data in default_rules:
            rule = FalsePositiveRule(
                rule_id=rule_data["rule_id"],
                name=rule_data["name"],
                description=rule_data["description"],
                conditions=rule_data["conditions"],
                weight=rule_data["weight"]
            )
            self.false_positive_rules.append(rule)
    
    def deduplicate_vulnerabilities(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        漏洞结果去重
        
        根据CVE、位置、类型进行去重，保留置信度最高的记录。
        
        Args:
            vulnerabilities: 漏洞列表
            
        Returns:
            Tuple[List[Dict], Dict]: (去重后的漏洞列表, 去重统计信息)
        """
        if not vulnerabilities:
            return [], {"original_count": 0, "deduplicated_count": 0, "duplicates_removed": 0}
        
        vuln_records: Dict[str, VulnerabilityRecord] = {}
        duplicates: List[Dict[str, Any]] = []
        
        for vuln in vulnerabilities:
            record = self._dict_to_record(vuln)
            dedup_key = record.get_dedup_key()
            
            if dedup_key not in vuln_records:
                vuln_records[dedup_key] = record
            else:
                existing = vuln_records[dedup_key]
                if record.confidence > existing.confidence:
                    duplicates.append(self._record_to_dict(existing))
                    vuln_records[dedup_key] = record
                else:
                    duplicates.append(self._record_to_dict(record))
        
        deduplicated = [self._record_to_dict(r) for r in vuln_records.values()]
        
        stats = {
            "original_count": len(vulnerabilities),
            "deduplicated_count": len(deduplicated),
            "duplicates_removed": len(duplicates),
            "deduplication_rate": len(duplicates) / len(vulnerabilities) * 100 if vulnerabilities else 0
        }
        
        logger.info(
            f"漏洞去重完成: {stats['original_count']} -> {stats['deduplicated_count']} "
            f"(移除 {stats['duplicates_removed']} 个重复项)"
        )
        
        return deduplicated, stats
    
    def _dict_to_record(self, vuln: Dict[str, Any]) -> VulnerabilityRecord:
        """将字典转换为漏洞记录"""
        return VulnerabilityRecord(
            vuln_id=vuln.get("id", vuln.get("vuln_id", "")),
            cve=vuln.get("cve", vuln.get("cve_id")),
            name=vuln.get("name", vuln.get("vuln_name", "")),
            vuln_type=vuln.get("type", vuln.get("vuln_type", "")),
            target=vuln.get("target", vuln.get("host", "")),
            url=vuln.get("url", ""),
            severity=str(vuln.get("severity", "info")).lower(),
            confidence=float(vuln.get("confidence", 0.0)),
            cvss_score=float(vuln.get("cvss_score", vuln.get("cvss", 0.0))),
            source=vuln.get("source", ""),
            description=vuln.get("description", ""),
            solution=vuln.get("solution", vuln.get("fix", "")),
            references=vuln.get("references", []),
            raw_data=vuln
        )
    
    def _record_to_dict(self, record: VulnerabilityRecord) -> Dict[str, Any]:
        """将漏洞记录转换为字典"""
        result = record.raw_data.copy()
        result.update({
            "vuln_id": record.vuln_id,
            "cve": record.cve,
            "name": record.name,
            "type": record.vuln_type,
            "target": record.target,
            "url": record.url,
            "severity": record.severity,
            "confidence": record.confidence,
            "cvss_score": record.cvss_score,
            "source": record.source,
            "description": record.description,
            "solution": record.solution,
            "references": record.references,
            "dedup_key": record.get_dedup_key()
        })
        return result
    
    def aggregate_results(
        self,
        results_by_source: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        合并多个来源的扫描结果
        
        将不同扫描工具的结果进行统一格式化并合并。
        
        Args:
            results_by_source: 按来源分组的扫描结果
            
        Returns:
            Tuple[List[Dict], Dict]: (合并后的结果列表, 聚合统计信息)
        """
        all_vulnerabilities: List[Dict[str, Any]] = []
        source_stats: Dict[str, Dict[str, Any]] = {}
        
        for source, results in results_by_source.items():
            normalized = self._normalize_results(results, source)
            all_vulnerabilities.extend(normalized)
            
            source_stats[source] = {
                "count": len(results),
                "normalized_count": len(normalized),
                "vulnerable_count": sum(
                    1 for r in normalized if r.get("severity") not in ["info", "low"]
                )
            }
        
        deduplicated, dedup_stats = self.deduplicate_vulnerabilities(all_vulnerabilities)
        
        sorted_results = self._sort_by_severity(deduplicated)
        
        aggregate_stats = {
            "total_sources": len(results_by_source),
            "total_raw_results": sum(len(r) for r in results_by_source.values()),
            "total_normalized": len(all_vulnerabilities),
            "total_after_dedup": len(sorted_results),
            "source_stats": source_stats,
            "deduplication_stats": dedup_stats
        }
        
        logger.info(
            f"结果聚合完成: {aggregate_stats['total_raw_results']} 条原始数据 "
            f"-> {aggregate_stats['total_after_dedup']} 条最终结果"
        )
        
        return sorted_results, aggregate_stats
    
    def _normalize_results(
        self,
        results: List[Dict[str, Any]],
        source: str
    ) -> List[Dict[str, Any]]:
        """标准化不同来源的结果格式"""
        normalized = []
        
        for result in results:
            normalized_item = {
                "source": source,
                "id": result.get("id", ""),
                "cve": result.get("cve", result.get("cve_id", "")),
                "name": result.get("name", result.get("title", result.get("vuln_name", ""))),
                "type": result.get("type", result.get("vuln_type", "")),
                "target": result.get("target", result.get("host", result.get("url", ""))),
                "url": result.get("url", result.get("affected_url", "")),
                "severity": self._normalize_severity(result.get("severity", result.get("level", "info"))),
                "confidence": float(result.get("confidence", result.get("certainty", 0.5))),
                "cvss_score": float(result.get("cvss_score", result.get("cvss", 0.0))),
                "description": result.get("description", result.get("desc", "")),
                "solution": result.get("solution", result.get("fix", result.get("remediation", ""))),
                "references": result.get("references", result.get("refs", [])),
                "raw_data": result
            }
            normalized.append(normalized_item)
        
        return normalized
    
    def _normalize_severity(self, severity: Any) -> str:
        """标准化严重度级别"""
        severity_str = str(severity).lower()
        
        severity_map = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "moderate": "medium",
            "low": "low",
            "info": "info",
            "information": "info",
            "notice": "info",
            "warning": "medium",
            "error": "high",
        }
        
        return severity_map.get(severity_str, "info")
    
    def _sort_by_severity(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按严重度排序"""
        return sorted(
            vulnerabilities,
            key=lambda x: (
                self.severity_order.get(str(x.get("severity", "info")).lower(), 0),
                x.get("confidence", 0)
            ),
            reverse=True
        )
    
    async def identify_false_positives(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        基于规则识别误报
        
        分析漏洞结果，识别可能的误报。
        
        Args:
            vulnerabilities: 漏洞列表
            
        Returns:
            Tuple[List[Dict], List[Dict], Dict]: (真实漏洞列表, 误报列表, 识别统计信息)
        """
        true_vulnerabilities: List[Dict[str, Any]] = []
        false_positives: List[Dict[str, Any]] = []
        
        for vuln in vulnerabilities:
            fp_score, fp_reasons = self._calculate_false_positive_score(vuln)
            
            vuln_with_fp = vuln.copy()
            vuln_with_fp["false_positive_score"] = fp_score
            vuln_with_fp["false_positive_reasons"] = fp_reasons
            
            vuln_key = self._get_vuln_key(vuln)
            if vuln_key in self.user_feedback:
                is_fp = self.user_feedback[vuln_key]
                vuln_with_fp["user_marked"] = True
            else:
                is_fp = fp_score > 0.5
            
            if is_fp:
                false_positives.append(vuln_with_fp)
            else:
                true_vulnerabilities.append(vuln_with_fp)
        
        stats = {
            "total_analyzed": len(vulnerabilities),
            "true_vulnerabilities": len(true_vulnerabilities),
            "false_positives": len(false_positives),
            "false_positive_rate": len(false_positives) / len(vulnerabilities) * 100 if vulnerabilities else 0,
            "rules_applied": len(self.false_positive_rules)
        }
        
        logger.info(
            f"误报识别完成: {stats['true_vulnerabilities']} 个真实漏洞, "
            f"{stats['false_positives']} 个误报"
        )
        
        return true_vulnerabilities, false_positives, stats
    
    def _calculate_false_positive_score(
        self,
        vuln: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """计算误报分数"""
        score = 0.0
        reasons: List[str] = []
        
        confidence = vuln.get("confidence", 0.5)
        if confidence < 0.2:
            score += 0.3
            reasons.append(f"置信度过低 ({confidence:.2f})")
        elif confidence < 0.4:
            score += 0.15
            reasons.append(f"置信度较低 ({confidence:.2f})")
        
        raw_data = vuln.get("raw_data", {})
        output = str(raw_data.get("output", "")).lower()
        error = str(raw_data.get("error", "")).lower()
        
        error_patterns = self._false_positive_patterns["error_patterns"]
        for pattern in error_patterns:
            if pattern in error or pattern in output:
                score += 0.1
                reasons.append(f"检测到错误模式: {pattern}")
        
        http_errors = self._false_positive_patterns["http_error_patterns"]
        for pattern in http_errors:
            if pattern in output:
                score += 0.1
                reasons.append(f"检测到HTTP错误: {pattern}")
        
        success_patterns = self._false_positive_patterns["success_patterns"]
        has_success = any(pattern in output for pattern in success_patterns)
        if has_success:
            score -= 0.2
            reasons.append("检测到成功验证模式")
        
        target = vuln.get("target", "").lower()
        url = vuln.get("url", "").lower()
        test_keywords = self._false_positive_patterns["false_positive_keywords"]
        for keyword in test_keywords:
            if keyword in target or keyword in url:
                score += 0.3
                reasons.append(f"目标疑似测试环境: {keyword}")
                break
        
        for rule in self.false_positive_rules:
            if not rule.enabled:
                continue
            
            rule_match = self._check_rule_conditions(vuln, rule.conditions)
            if rule_match:
                score += 0.1 * rule.weight
                reasons.append(f"匹配规则: {rule.name}")
        
        final_score = min(max(score, 0.0), 1.0)
        return final_score, reasons
    
    def _check_rule_conditions(
        self,
        vuln: Dict[str, Any],
        conditions: Dict[str, Any]
    ) -> bool:
        """检查规则条件"""
        raw_data = vuln.get("raw_data", {})
        
        if conditions.get("has_timeout"):
            error = str(raw_data.get("error", "")).lower()
            if "timeout" not in error:
                return False
        
        if conditions.get("has_connection_error"):
            error = str(raw_data.get("error", "")).lower()
            if not any(kw in error for kw in ["connection", "refused", "reset"]):
                return False
        
        if conditions.get("confidence_below"):
            if vuln.get("confidence", 1.0) >= conditions["confidence_below"]:
                return False
        
        if conditions.get("no_output"):
            if raw_data.get("output"):
                return False
        
        if conditions.get("is_test_target"):
            target = vuln.get("target", "").lower()
            test_keywords = self._false_positive_patterns["false_positive_keywords"]
            if not any(kw in target for kw in test_keywords):
                return False
        
        if conditions.get("has_http_error"):
            output = str(raw_data.get("output", "")).lower()
            if not any(str(code) in output for code in [404, 403, 401, 500, 502, 503, 504]):
                return False
        
        if conditions.get("no_vuln_evidence"):
            output = str(raw_data.get("output", "")).lower()
            success_patterns = self._false_positive_patterns["success_patterns"]
            if any(pattern in output for pattern in success_patterns):
                return False
        
        return True
    
    def _get_vuln_key(self, vuln: Dict[str, Any]) -> str:
        """获取漏洞唯一键"""
        return f"{vuln.get('cve', '')}_{vuln.get('target', '')}_{vuln.get('type', '')}"
    
    def filter_low_confidence(
        self,
        vulnerabilities: List[Dict[str, Any]],
        threshold: float = 0.3
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        过滤低置信度结果
        
        Args:
            vulnerabilities: 漏洞列表
            threshold: 置信度阈值
            
        Returns:
            Tuple[List[Dict], List[Dict], Dict]: (高置信度结果, 低置信度结果, 统计信息)
        """
        high_confidence: List[Dict[str, Any]] = []
        low_confidence: List[Dict[str, Any]] = []
        
        for vuln in vulnerabilities:
            confidence = vuln.get("confidence", 0.5)
            if confidence >= threshold:
                high_confidence.append(vuln)
            else:
                low_confidence.append(vuln)
        
        stats = {
            "total": len(vulnerabilities),
            "high_confidence_count": len(high_confidence),
            "low_confidence_count": len(low_confidence),
            "threshold": threshold,
            "average_confidence": sum(v.get("confidence", 0) for v in vulnerabilities) / len(vulnerabilities) if vulnerabilities else 0
        }
        
        logger.info(
            f"置信度过滤完成: {stats['high_confidence_count']} 条高置信度, "
            f"{stats['low_confidence_count']} 条低置信度 (阈值: {threshold})"
        )
        
        return high_confidence, low_confidence, stats
    
    def add_user_feedback(
        self,
        vuln_key: str,
        is_false_positive: bool
    ) -> None:
        """
        添加用户反馈
        
        支持用户反馈学习，记录用户对误报的判断。
        
        Args:
            vuln_key: 漏洞唯一键
            is_false_positive: 是否为误报
        """
        self.user_feedback[vuln_key] = is_false_positive
        logger.info(f"用户反馈已记录: {vuln_key} -> {'误报' if is_false_positive else '真实漏洞'}")
    
    def add_false_positive_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        conditions: Dict[str, Any],
        weight: float = 1.0
    ) -> None:
        """
        添加自定义误报规则
        
        Args:
            rule_id: 规则ID
            name: 规则名称
            description: 规则描述
            conditions: 规则条件
            weight: 规则权重
        """
        rule = FalsePositiveRule(
            rule_id=rule_id,
            name=name,
            description=description,
            conditions=conditions,
            weight=weight
        )
        self.false_positive_rules.append(rule)
        logger.info(f"添加误报规则: {name}")
    
    def generate_follow_up_suggestions(
        self,
        vulnerabilities: List[Dict[str, Any]],
        scan_history: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[FollowUpSuggestion], Dict[str, Any]]:
        """
        根据结果生成补充扫描建议
        
        分析当前漏洞结果，识别未覆盖的攻击面，生成补充扫描建议。
        
        Args:
            vulnerabilities: 漏洞列表
            scan_history: 扫描历史记录
            
        Returns:
            Tuple[List[FollowUpSuggestion], Dict]: (建议列表, 统计信息)
        """
        suggestions: List[FollowUpSuggestion] = []
        
        vuln_types = set()
        targets = set()
        ports_found = set()
        urls_found = set()
        
        for vuln in vulnerabilities:
            if vuln.get("type"):
                vuln_types.add(vuln.get("type"))
            if vuln.get("target"):
                targets.add(vuln.get("target"))
            if vuln.get("url"):
                urls_found.add(vuln.get("url"))
        
        suggestion_id = 0
        
        for target in targets:
            if not self._has_port_scan(target, scan_history):
                suggestion_id += 1
                suggestions.append(FollowUpSuggestion(
                    suggestion_id=f"follow_up_{suggestion_id}",
                    title=f"端口扫描: {target}",
                    description=f"对目标 {target} 进行全面端口扫描，发现潜在攻击面",
                    priority="medium",
                    scan_type="portscan",
                    target=target,
                    reason="未发现该目标的端口扫描记录",
                    parameters={"target": target, "scan_type": "full"}
                ))
        
        for target in targets:
            if not self._has_vuln_scan(target, scan_history):
                suggestion_id += 1
                suggestions.append(FollowUpSuggestion(
                    suggestion_id=f"follow_up_{suggestion_id}",
                    title=f"漏洞扫描: {target}",
                    description=f"对目标 {target} 进行深度漏洞扫描",
                    priority="high",
                    scan_type="vuln_scan",
                    target=target,
                    reason="未发现该目标的漏洞扫描记录",
                    parameters={"target": target}
                ))
        
        for vuln_type in vuln_types:
            related_scans = self._get_related_scan_types(vuln_type)
            for scan_type in related_scans:
                suggestion_id += 1
                suggestions.append(FollowUpSuggestion(
                    suggestion_id=f"follow_up_{suggestion_id}",
                    title=f"补充扫描: {scan_type}",
                    description=f"针对 {vuln_type} 类型漏洞的补充 {scan_type} 扫描",
                    priority="medium",
                    scan_type=scan_type,
                    target=",".join(targets),
                    reason=f"发现 {vuln_type} 类型漏洞，建议进行补充扫描",
                    parameters={"vuln_type": vuln_type}
                ))
        
        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "critical"]
        for vuln in critical_vulns:
            suggestion_id += 1
            suggestions.append(FollowUpSuggestion(
                suggestion_id=f"follow_up_{suggestion_id}",
                title=f"深度验证: {vuln.get('name', '未知漏洞')}",
                description=f"对严重漏洞进行深度验证和影响评估",
                priority="critical",
                scan_type="poc_verification",
                target=vuln.get("target", ""),
                reason="发现严重漏洞，需要深度验证",
                parameters={"vuln_id": vuln.get("id"), "cve": vuln.get("cve")}
            ))
        
        if len(targets) > 0 and not self._has_subdomain_scan(list(targets), scan_history):
            suggestion_id += 1
            suggestions.append(FollowUpSuggestion(
                suggestion_id=f"follow_up_{suggestion_id}",
                title="子域名扫描",
                description="对目标域名进行子域名枚举，扩大攻击面",
                priority="low",
                scan_type="subdomain",
                target=",".join(targets),
                reason="未发现子域名扫描记录",
                parameters={}
            ))
        
        sorted_suggestions = sorted(
            suggestions,
            key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.priority, 4)
        )
        
        stats = {
            "total_suggestions": len(suggestions),
            "by_priority": {
                "critical": sum(1 for s in suggestions if s.priority == "critical"),
                "high": sum(1 for s in suggestions if s.priority == "high"),
                "medium": sum(1 for s in suggestions if s.priority == "medium"),
                "low": sum(1 for s in suggestions if s.priority == "low")
            },
            "unique_targets": len(targets),
            "vuln_types_found": list(vuln_types)
        }
        
        logger.info(f"生成 {len(suggestions)} 条补充扫描建议")
        
        return sorted_suggestions, stats
    
    def _has_port_scan(self, target: str, scan_history: Optional[Dict[str, Any]]) -> bool:
        """检查是否有端口扫描记录"""
        if not scan_history:
            return False
        port_scans = scan_history.get("port_scans", [])
        return any(scan.get("target") == target for scan in port_scans)
    
    def _has_vuln_scan(self, target: str, scan_history: Optional[Dict[str, Any]]) -> bool:
        """检查是否有漏洞扫描记录"""
        if not scan_history:
            return False
        vuln_scans = scan_history.get("vuln_scans", [])
        return any(scan.get("target") == target for scan in vuln_scans)
    
    def _has_subdomain_scan(self, targets: List[str], scan_history: Optional[Dict[str, Any]]) -> bool:
        """检查是否有子域名扫描记录"""
        if not scan_history:
            return False
        subdomain_scans = scan_history.get("subdomain_scans", [])
        return len(subdomain_scans) > 0
    
    def _get_related_scan_types(self, vuln_type: str) -> List[str]:
        """获取与漏洞类型相关的扫描类型"""
        type_scan_map = {
            "sql_injection": ["database_scan", "auth_bypass_scan"],
            "xss": ["dom_analysis", "input_validation_scan"],
            "rce": ["command_injection_scan", "file_upload_scan"],
            "lfi": ["directory_traversal_scan", "file_inclusion_scan"],
            "ssrf": ["internal_network_scan", "cloud_metadata_scan"],
            "auth_bypass": ["auth_testing", "session_analysis"],
            "info_disclosure": ["sensitive_data_scan", "backup_file_scan"],
        }
        
        vuln_type_lower = vuln_type.lower().replace("-", "_").replace(" ", "_")
        return type_scan_map.get(vuln_type_lower, [])
    
    def calculate_risk_score(
        self,
        vulnerabilities: List[Dict[str, Any]],
        false_positives: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算综合风险评分
        
        考虑漏洞严重性、可信度、影响范围计算综合风险评分。
        
        Args:
            vulnerabilities: 漏洞列表
            false_positives: 误报列表
            
        Returns:
            Tuple[float, Dict]: (风险评分, 评分详情)
        """
        if not vulnerabilities:
            return 0.0, {"score": 0.0, "factors": {}, "summary": "无漏洞"}
        
        severity_weights = {
            "critical": 10.0,
            "high": 7.5,
            "medium": 5.0,
            "low": 2.5,
            "info": 1.0
        }
        
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        severity_scores = {"critical": 0.0, "high": 0.0, "medium": 0.0, "low": 0.0, "info": 0.0}
        
        total_confidence = 0.0
        total_cvss = 0.0
        unique_targets: Set[str] = set()
        
        for vuln in vulnerabilities:
            severity = str(vuln.get("severity", "info")).lower()
            confidence = vuln.get("confidence", 0.5)
            cvss_score = vuln.get("cvss_score", 0.0)
            target = vuln.get("target", "")
            
            if severity in severity_counts:
                severity_counts[severity] += 1
                severity_scores[severity] += severity_weights[severity] * confidence
            
            total_confidence += confidence
            total_cvss += cvss_score
            if target:
                unique_targets.add(target)
        
        fp_penalty = 0.0
        if false_positives:
            fp_penalty = len(false_positives) * 0.5
        
        raw_score = sum(severity_scores.values())
        
        confidence_factor = total_confidence / len(vulnerabilities)
        adjusted_score = raw_score * confidence_factor
        
        target_factor = min(len(unique_targets) * 0.1, 1.0)
        adjusted_score *= (1 + target_factor)
        
        adjusted_score -= fp_penalty
        
        max_possible_score = len(vulnerabilities) * 10.0
        normalized_score = min((adjusted_score / max_possible_score) * 100, 100) if max_possible_score > 0 else 0
        normalized_score = max(normalized_score, 0)
        
        risk_level = self._get_risk_level(normalized_score)
        
        factors = {
            "severity_distribution": severity_counts,
            "severity_scores": severity_scores,
            "average_confidence": confidence_factor,
            "average_cvss": total_cvss / len(vulnerabilities),
            "unique_targets": len(unique_targets),
            "false_positive_penalty": fp_penalty,
            "raw_score": raw_score,
            "adjusted_score": adjusted_score
        }
        
        summary = self._generate_risk_summary(normalized_score, risk_level, severity_counts)
        
        details = {
            "score": round(normalized_score, 2),
            "risk_level": risk_level,
            "factors": factors,
            "summary": summary
        }
        
        logger.info(f"风险评分计算完成: {normalized_score:.2f} ({risk_level})")
        
        return round(normalized_score, 2), details
    
    def _get_risk_level(self, score: float) -> str:
        """根据分数获取风险等级"""
        if score >= 80:
            return RiskLevel.CRITICAL.value
        elif score >= 60:
            return RiskLevel.HIGH.value
        elif score >= 40:
            return RiskLevel.MEDIUM.value
        elif score >= 20:
            return RiskLevel.LOW.value
        else:
            return RiskLevel.INFO.value
    
    def _generate_risk_summary(
        self,
        score: float,
        risk_level: str,
        severity_counts: Dict[str, int]
    ) -> str:
        """生成风险摘要"""
        level_names = {
            "critical": "严重",
            "high": "高危",
            "medium": "中危",
            "low": "低危",
            "info": "信息"
        }
        
        parts = []
        for level in ["critical", "high", "medium", "low", "info"]:
            count = severity_counts.get(level, 0)
            if count > 0:
                parts.append(f"{level_names[level]}: {count}")
        
        severity_summary = ", ".join(parts) if parts else "无漏洞"
        
        return f"风险评分: {score:.1f}分, 风险等级: {risk_level}, 漏洞分布: {severity_summary}"
    
    async def analyze(
        self,
        vulnerabilities: List[Dict[str, Any]],
        results_by_source: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        scan_history: Optional[Dict[str, Any]] = None
    ) -> AnalyzedResult:
        """
        执行完整的结果分析
        
        整合所有分析功能，生成完整的分析报告。
        
        Args:
            vulnerabilities: 漏洞列表
            results_by_source: 按来源分组的结果
            scan_history: 扫描历史
            
        Returns:
            AnalyzedResult: 完整的分析结果
        """
        logger.info(f"开始智能结果分析, 共 {len(vulnerabilities)} 条记录")
        
        if results_by_source:
            aggregated, aggregate_stats = self.aggregate_results(results_by_source)
            vulnerabilities = aggregated
        else:
            vulnerabilities, aggregate_stats = self.deduplicate_vulnerabilities(vulnerabilities)
        
        true_vulns, false_positives, fp_stats = await self.identify_false_positives(vulnerabilities)
        
        high_conf, low_conf, conf_stats = self.filter_low_confidence(true_vulns)
        
        risk_score, risk_details = self.calculate_risk_score(high_conf, false_positives)
        
        suggestions, suggestion_stats = self.generate_follow_up_suggestions(high_conf, scan_history)
        
        avg_confidence = sum(v.get("confidence", 0) for v in high_conf) / len(high_conf) if high_conf else 0
        
        summary = self._generate_analysis_summary(
            high_conf, false_positives, risk_score, avg_confidence
        )
        
        statistics = {
            "total_input": len(vulnerabilities),
            "after_dedup": aggregate_stats.get("deduplicated_count", len(vulnerabilities)),
            "true_vulnerabilities": len(true_vulns),
            "false_positives": len(false_positives),
            "high_confidence": len(high_conf),
            "low_confidence": len(low_conf),
            "risk_score": risk_score,
            "average_confidence": avg_confidence,
            "aggregate_stats": aggregate_stats,
            "false_positive_stats": fp_stats,
            "confidence_stats": conf_stats,
            "suggestion_stats": suggestion_stats
        }
        
        result = AnalyzedResult(
            vulnerabilities=high_conf,
            false_positives=false_positives,
            risk_score=risk_score,
            follow_up_suggestions=[s.title for s in suggestions],
            confidence=avg_confidence,
            summary=summary,
            statistics=statistics,
            deduplication_stats=aggregate_stats
        )
        
        logger.info(f"智能结果分析完成: 风险评分 {risk_score}, {len(high_conf)} 个真实漏洞")
        
        return result
    
    def _generate_analysis_summary(
        self,
        vulnerabilities: List[Dict[str, Any]],
        false_positives: List[Dict[str, Any]],
        risk_score: float,
        confidence: float
    ) -> str:
        """生成分析摘要"""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for vuln in vulnerabilities:
            severity = str(vuln.get("severity", "info")).lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        parts = []
        level_names = {"critical": "严重", "high": "高危", "medium": "中危", "low": "低危", "info": "信息"}
        for level in ["critical", "high", "medium", "low"]:
            count = severity_counts.get(level, 0)
            if count > 0:
                parts.append(f"{level_names[level]} {count} 个")
        
        severity_str = ", ".join(parts) if parts else "无高危漏洞"
        
        summary = (
            f"共发现 {len(vulnerabilities)} 个真实漏洞({severity_str}), "
            f"识别出 {len(false_positives)} 个误报, "
            f"综合风险评分 {risk_score:.1f} 分, "
            f"平均置信度 {confidence:.2%}。"
        )
        
        return summary
    
    def get_analyzer_stats(self) -> Dict[str, Any]:
        """获取分析器统计信息"""
        return {
            "false_positive_rules": len(self.false_positive_rules),
            "enabled_rules": sum(1 for r in self.false_positive_rules if r.enabled),
            "user_feedback_count": len(self.user_feedback),
            "severity_order": self.severity_order
        }

"""
插件结果聚合器

聚合多个插件的执行结果,处理冲突并生成综合报告。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(Enum):
    """
    冲突解决策略枚举
    
    定义不同的冲突解决策略:
    - PRIORITY: 基于插件优先级
    - CONFIDENCE: 基于结果置信度
    - TIMESTAMP: 基于时间戳(最新优先)
    - MERGE: 合并所有结果
    """
    PRIORITY = "priority"
    CONFIDENCE = "confidence"
    TIMESTAMP = "timestamp"
    MERGE = "merge"


class MergeStrategy(Enum):
    """
    结果合并策略枚举
    
    定义不同类型结果的合并方式:
    - REPLACE: 替换旧值
    - APPEND: 追加到列表
    - UNION: 取并集
    - INTERSECTION: 取交集
    - MAX: 取最大值
    - MIN: 取最小值
    """
    REPLACE = "replace"
    APPEND = "append"
    UNION = "union"
    INTERSECTION = "intersection"
    MAX = "max"
    MIN = "min"


@dataclass
class ConflictRecord:
    """
    冲突记录数据类
    
    记录结果冲突的详细信息。
    
    Attributes:
        field_name: 冲突字段名称
        plugin_name: 相关插件名称
        values: 冲突的值列表
        resolution: 解决策略
        resolved_value: 解决后的值
        reason: 解决原因
        timestamp: 记录时间
    """
    field_name: str
    plugin_name: str
    values: List[Any]
    resolution: str
    resolved_value: Any
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AggregatedResult:
    """
    聚合结果数据类
    
    存储聚合后的完整结果。
    
    Attributes:
        plugin_results: 原始插件结果字典
        merged_findings: 合并后的发现列表
        conflicts_resolved: 已解决的冲突列表
        summary: 摘要信息
        statistics: 统计信息
        generated_at: 生成时间
    """
    plugin_results: Dict[str, Any]
    merged_findings: List[Dict[str, Any]]
    conflicts_resolved: List[Dict[str, Any]]
    summary: Dict[str, Any]
    statistics: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationResult:
    """
    验证结果数据类
    
    存储结果验证的详细信息。
    
    Attributes:
        is_valid: 是否有效
        plugin_name: 插件名称
        errors: 错误列表
        warnings: 警告列表
        missing_fields: 缺失字段列表
        invalid_fields: 无效字段列表
    """
    is_valid: bool
    plugin_name: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    invalid_fields: List[str] = field(default_factory=list)


class PluginResultAggregator:
    """
    插件结果聚合器
    
    负责聚合多个插件的执行结果,处理冲突并生成综合报告。
    
    支持的功能:
    - 多插件结果合并
    - 冲突检测与解决
    - 综合报告生成
    - 结果验证
    
    Attributes:
        plugin_priorities: 插件优先级配置
        merge_strategies: 字段合并策略配置
        required_fields: 必要字段配置
        conflict_log: 冲突日志记录
    """
    
    DEFAULT_REQUIRED_FIELDS = ["status", "target"]
    DEFAULT_MERGE_STRATEGIES = {
        "open_ports": MergeStrategy.UNION,
        "vulnerabilities": MergeStrategy.APPEND,
        "findings": MergeStrategy.APPEND,
        "confidence": MergeStrategy.MAX,
        "risk_level": MergeStrategy.MAX,
    }
    
    def __init__(
        self,
        plugin_priorities: Optional[Dict[str, int]] = None,
        merge_strategies: Optional[Dict[str, MergeStrategy]] = None,
        required_fields: Optional[List[str]] = None
    ):
        """
        初始化插件结果聚合器
        
        Args:
            plugin_priorities: 插件优先级配置,键为插件名,值为优先级(1-10)
            merge_strategies: 字段合并策略配置
            required_fields: 必要字段列表
        """
        self.plugin_priorities = plugin_priorities or {}
        self.merge_strategies = merge_strategies or self.DEFAULT_MERGE_STRATEGIES
        self.required_fields = required_fields or self.DEFAULT_REQUIRED_FIELDS
        self.conflict_log: List[ConflictRecord] = []
        logger.info("插件结果聚合器初始化完成")
    
    async def merge_results(
        self,
        results: Dict[str, Dict[str, Any]],
        target: str
    ) -> Dict[str, Any]:
        """
        合并多个插件的执行结果
        
        根据配置的合并策略,将多个插件的结果合并为统一格式。
        保留原始数据引用以便追溯。
        
        Args:
            results: 插件结果字典,键为插件名,值为结果字典
            target: 扫描目标
            
        Returns:
            Dict: 合并后的结果字典
            
        Example:
            >>> results = {
            ...     "portscan": {"open_ports": [80, 443]},
            ...     "waf": {"waf_detected": True}
            ... }
            >>> merged = await aggregator.merge_results(results, "example.com")
        """
        if not results:
            logger.warning("没有插件结果需要合并")
            return {"status": "empty", "target": target}
        
        logger.info(f"开始合并 {len(results)} 个插件的结果")
        
        merged: Dict[str, Any] = {
            "target": target,
            "plugins_executed": list(results.keys()),
            "merge_timestamp": datetime.now().isoformat()
        }
        
        field_values: Dict[str, List[Dict[str, Any]]] = {}
        
        for plugin_name, result in results.items():
            if not isinstance(result, dict):
                logger.warning(f"插件 {plugin_name} 结果格式无效,跳过")
                continue
            
            for field_name, value in result.items():
                if field_name not in field_values:
                    field_values[field_name] = []
                field_values[field_name].append({
                    "value": value,
                    "plugin": plugin_name,
                    "priority": self.plugin_priorities.get(plugin_name, 5),
                    "timestamp": result.get("timestamp", datetime.now())
                })
        
        for field_name, values_list in field_values.items():
            if len(values_list) == 1:
                merged[field_name] = values_list[0]["value"]
            else:
                merged[field_name] = await self._merge_field(
                    field_name, values_list
                )
        
        merged["_raw_results"] = results
        
        logger.info(f"结果合并完成,共处理 {len(field_values)} 个字段")
        return merged
    
    async def _merge_field(
        self,
        field_name: str,
        values_list: List[Dict[str, Any]]
    ) -> Any:
        """
        合并单个字段的多个值
        
        根据字段类型和配置的策略选择合适的合并方式。
        
        Args:
            field_name: 字段名称
            values_list: 值列表,每个值包含value、plugin、priority等信息
            
        Returns:
            Any: 合并后的值
        """
        strategy = self.merge_strategies.get(field_name, MergeStrategy.REPLACE)
        
        if strategy == MergeStrategy.REPLACE:
            sorted_values = sorted(
                values_list, 
                key=lambda x: x["priority"], 
                reverse=True
            )
            return sorted_values[0]["value"]
        
        elif strategy == MergeStrategy.APPEND:
            result = []
            for item in values_list:
                value = item["value"]
                if isinstance(value, list):
                    result.extend(value)
                else:
                    result.append(value)
            return result
        
        elif strategy == MergeStrategy.UNION:
            result_set: Set = set()
            for item in values_list:
                value = item["value"]
                if isinstance(value, list):
                    result_set.update(value)
                elif isinstance(value, (str, int)):
                    result_set.add(value)
            return list(result_set)
        
        elif strategy == MergeStrategy.INTERSECTION:
            if not values_list:
                return []
            
            first_value = values_list[0]["value"]
            if isinstance(first_value, list):
                result_set = set(first_value)
                for item in values_list[1:]:
                    value = item["value"]
                    if isinstance(value, list):
                        result_set &= set(value)
                return list(result_set)
            return first_value
        
        elif strategy == MergeStrategy.MAX:
            numeric_values = []
            for item in values_list:
                value = item["value"]
                if isinstance(value, (int, float)):
                    numeric_values.append(value)
            return max(numeric_values) if numeric_values else 0
        
        elif strategy == MergeStrategy.MIN:
            numeric_values = []
            for item in values_list:
                value = item["value"]
                if isinstance(value, (int, float)):
                    numeric_values.append(value)
            return min(numeric_values) if numeric_values else 0
        
        return values_list[0]["value"]
    
    async def resolve_conflicts(
        self,
        results: Dict[str, Dict[str, Any]],
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.PRIORITY
    ) -> Dict[str, Any]:
        """
        处理结果冲突
        
        检测并解决多个插件结果之间的冲突。
        支持多种解决策略,并记录冲突解决日志。
        
        Args:
            results: 插件结果字典
            strategy: 冲突解决策略
            
        Returns:
            Dict: 解决冲突后的结果,包含:
                - resolved_results: 解决后的结果
                - conflicts: 冲突记录列表
                - resolution_summary: 解决摘要
        """
        logger.info(f"开始处理冲突,策略: {strategy.value}")
        
        conflicts: List[ConflictRecord] = []
        resolved: Dict[str, Any] = {}
        
        field_occurrences: Dict[str, List[Dict[str, Any]]] = {}
        
        for plugin_name, result in results.items():
            if not isinstance(result, dict):
                continue
            
            for field_name, value in result.items():
                if field_name.startswith("_"):
                    continue
                    
                if field_name not in field_occurrences:
                    field_occurrences[field_name] = []
                
                field_occurrences[field_name].append({
                    "plugin": plugin_name,
                    "value": value,
                    "priority": self.plugin_priorities.get(plugin_name, 5),
                    "confidence": result.get("confidence", 0.5),
                    "timestamp": result.get("timestamp", datetime.now())
                })
        
        for field_name, occurrences in field_occurrences.items():
            if len(occurrences) <= 1:
                if occurrences:
                    resolved[field_name] = occurrences[0]["value"]
                continue
            
            unique_values = set()
            for occ in occurrences:
                value = occ["value"]
                if isinstance(value, (list, dict)):
                    unique_values.add(str(sorted(value) if isinstance(value, list) else value))
                else:
                    unique_values.add(value)
            
            if len(unique_values) > 1:
                conflict = await self._detect_conflict(field_name, occurrences)
                if conflict:
                    conflicts.append(conflict)
                    resolved[field_name] = conflict.resolved_value
                else:
                    resolved[field_name] = occurrences[0]["value"]
            else:
                resolved[field_name] = occurrences[0]["value"]
        
        self.conflict_log.extend(conflicts)
        
        conflict_dicts = [
            {
                "field_name": c.field_name,
                "plugin_name": c.plugin_name,
                "values": c.values,
                "resolution": c.resolution,
                "resolved_value": c.resolved_value,
                "reason": c.reason,
                "timestamp": c.timestamp.isoformat()
            }
            for c in conflicts
        ]
        
        logger.info(f"冲突处理完成,发现并解决 {len(conflicts)} 个冲突")
        
        return {
            "resolved_results": resolved,
            "conflicts": conflict_dicts,
            "resolution_summary": {
                "total_conflicts": len(conflicts),
                "strategy_used": strategy.value,
                "fields_affected": list(set(c.field_name for c in conflicts))
            }
        }
    
    async def _detect_conflict(
        self,
        field_name: str,
        occurrences: List[Dict[str, Any]]
    ) -> Optional[ConflictRecord]:
        """
        检测并解决单个字段的冲突
        
        Args:
            field_name: 字段名称
            occurrences: 该字段在多个插件中的出现记录
            
        Returns:
            Optional[ConflictRecord]: 冲突记录,无冲突返回None
        """
        values = [occ["value"] for occ in occurrences]
        plugins = [occ["plugin"] for occ in occurrences]
        
        if len(set(str(v) for v in values)) <= 1:
            return None
        
        sorted_occurrences = sorted(
            occurrences,
            key=lambda x: x["priority"],
            reverse=True
        )
        
        resolved_value = sorted_occurrences[0]["value"]
        winning_plugin = sorted_occurrences[0]["plugin"]
        
        return ConflictRecord(
            field_name=field_name,
            plugin_name=winning_plugin,
            values=values,
            resolution=ConflictResolutionStrategy.PRIORITY.value,
            resolved_value=resolved_value,
            reason=f"插件 {winning_plugin} 具有最高优先级"
        )
    
    async def generate_report(
        self,
        results: Dict[str, Dict[str, Any]],
        target: str
    ) -> AggregatedResult:
        """
        生成综合扫描报告
        
        整合所有插件结果,生成包含摘要和统计信息的综合报告。
        
        Args:
            results: 插件结果字典
            target: 扫描目标
            
        Returns:
            AggregatedResult: 聚合结果对象,包含:
                - plugin_results: 原始插件结果
                - merged_findings: 合并后的发现
                - conflicts_resolved: 已解决的冲突
                - summary: 摘要信息
                - statistics: 统计信息
        """
        logger.info(f"开始生成综合报告,目标: {target}")
        
        merged = await self.merge_results(results, target)
        
        conflict_result = await self.resolve_conflicts(results)
        
        merged_findings = await self._extract_findings(merged, results)
        
        summary = await self._generate_summary(merged, results)
        
        statistics = await self._generate_statistics(results)
        
        aggregated = AggregatedResult(
            plugin_results=results,
            merged_findings=merged_findings,
            conflicts_resolved=conflict_result["conflicts"],
            summary=summary,
            statistics=statistics
        )
        
        logger.info("综合报告生成完成")
        return aggregated
    
    async def _extract_findings(
        self,
        merged: Dict[str, Any],
        results: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        从合并结果中提取发现
        
        Args:
            merged: 合并后的结果
            results: 原始插件结果
            
        Returns:
            List[Dict]: 发现列表
        """
        findings: List[Dict[str, Any]] = []
        
        for plugin_name, result in results.items():
            if not isinstance(result, dict):
                continue
            
            if result.get("status") == "failed":
                findings.append({
                    "type": "error",
                    "plugin": plugin_name,
                    "message": result.get("error", "未知错误"),
                    "severity": "high"
                })
            
            if "vulnerabilities" in result:
                vulns = result["vulnerabilities"]
                if isinstance(vulns, list):
                    for vuln in vulns:
                        findings.append({
                            "type": "vulnerability",
                            "plugin": plugin_name,
                            "details": vuln,
                            "severity": vuln.get("severity", "medium")
                        })
            
            if "open_ports" in result:
                ports = result["open_ports"]
                if isinstance(ports, list) and ports:
                    findings.append({
                        "type": "open_ports",
                        "plugin": plugin_name,
                        "ports": ports,
                        "severity": "info"
                    })
            
            if "findings" in result:
                plugin_findings = result["findings"]
                if isinstance(plugin_findings, list):
                    for finding in plugin_findings:
                        findings.append({
                            "type": "finding",
                            "plugin": plugin_name,
                            "details": finding,
                            "severity": finding.get("severity", "info")
                        })
        
        findings.sort(key=lambda x: self._severity_order(x.get("severity", "info")))
        
        return findings
    
    def _severity_order(self, severity: str) -> int:
        """
        获取严重性排序值
        
        Args:
            severity: 严重性级别
            
        Returns:
            int: 排序值,值越小越严重
        """
        severity_map = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "info": 4
        }
        return severity_map.get(severity.lower(), 5)
    
    async def _generate_summary(
        self,
        merged: Dict[str, Any],
        results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成摘要信息
        
        Args:
            merged: 合并后的结果
            results: 原始插件结果
            
        Returns:
            Dict: 摘要信息
        """
        total_plugins = len(results)
        successful_plugins = sum(
            1 for r in results.values() 
            if isinstance(r, dict) and r.get("status") == "success"
        )
        failed_plugins = total_plugins - successful_plugins
        
        vulnerability_count = 0
        high_risk_count = 0
        
        for result in results.values():
            if not isinstance(result, dict):
                continue
            
            if "vulnerabilities" in result:
                vulns = result["vulnerabilities"]
                if isinstance(vulns, list):
                    vulnerability_count += len(vulns)
                    high_risk_count += sum(
                        1 for v in vulns 
                        if v.get("severity") in ["critical", "high"]
                    )
        
        open_ports = merged.get("open_ports", [])
        if not isinstance(open_ports, list):
            open_ports = []
        
        summary = {
            "target": merged.get("target", "unknown"),
            "scan_status": "completed" if failed_plugins == 0 else "partial",
            "plugins_summary": {
                "total": total_plugins,
                "successful": successful_plugins,
                "failed": failed_plugins
            },
            "security_summary": {
                "vulnerabilities_found": vulnerability_count,
                "high_risk_vulnerabilities": high_risk_count,
                "open_ports_count": len(open_ports)
            },
            "risk_assessment": self._assess_risk(
                vulnerability_count, 
                high_risk_count, 
                len(open_ports)
            ),
            "generated_at": datetime.now().isoformat()
        }
        
        return summary
    
    def _assess_risk(
        self,
        vuln_count: int,
        high_risk_count: int,
        open_ports_count: int
    ) -> Dict[str, Any]:
        """
        评估风险等级
        
        Args:
            vuln_count: 漏洞总数
            high_risk_count: 高危漏洞数
            open_ports_count: 开放端口数
            
        Returns:
            Dict: 风险评估结果
        """
        if high_risk_count > 0:
            level = "high"
            score = min(100, 60 + high_risk_count * 10)
        elif vuln_count > 0:
            level = "medium"
            score = min(59, 30 + vuln_count * 5)
        elif open_ports_count > 10:
            level = "low"
            score = 25
        else:
            level = "info"
            score = 10
        
        return {
            "level": level,
            "score": score,
            "factors": {
                "vulnerabilities": vuln_count,
                "high_risk": high_risk_count,
                "exposed_services": open_ports_count
            }
        }
    
    async def _generate_statistics(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成统计信息
        
        Args:
            results: 插件结果字典
            
        Returns:
            Dict: 统计信息
        """
        stats: Dict[str, Any] = {
            "by_plugin": {},
            "by_category": {},
            "execution_times": {},
            "data_counts": {}
        }
        
        for plugin_name, result in results.items():
            if not isinstance(result, dict):
                continue
            
            stats["by_plugin"][plugin_name] = {
                "status": result.get("status", "unknown"),
                "has_error": "error" in result,
                "data_size": len(str(result))
            }
            
            for key, value in result.items():
                if key.startswith("_"):
                    continue
                
                if key not in stats["data_counts"]:
                    stats["data_counts"][key] = 0
                
                if value is not None:
                    stats["data_counts"][key] += 1
        
        total_data_fields = sum(stats["data_counts"].values())
        stats["total_data_points"] = total_data_fields
        
        return stats
    
    async def validate_results(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, ValidationResult]:
        """
        验证结果完整性
        
        检查每个插件结果的必要字段和格式正确性。
        
        Args:
            results: 插件结果字典
            
        Returns:
            Dict[str, ValidationResult]: 验证结果字典,键为插件名
        """
        logger.info(f"开始验证 {len(results)} 个插件结果")
        
        validation_results: Dict[str, ValidationResult] = {}
        
        for plugin_name, result in results.items():
            validation = await self._validate_single_result(plugin_name, result)
            validation_results[plugin_name] = validation
        
        valid_count = sum(1 for v in validation_results.values() if v.is_valid)
        logger.info(f"验证完成: {valid_count}/{len(results)} 个结果有效")
        
        return validation_results
    
    async def _validate_single_result(
        self,
        plugin_name: str,
        result: Dict[str, Any]
    ) -> ValidationResult:
        """
        验证单个插件结果
        
        Args:
            plugin_name: 插件名称
            result: 插件结果
            
        Returns:
            ValidationResult: 验证结果
        """
        errors: List[str] = []
        warnings: List[str] = []
        missing_fields: List[str] = []
        invalid_fields: List[str] = []
        
        if not isinstance(result, dict):
            return ValidationResult(
                is_valid=False,
                plugin_name=plugin_name,
                errors=[f"结果类型无效: 期望dict, 实际{type(result).__name__}"],
                warnings=[],
                missing_fields=self.required_fields,
                invalid_fields=[]
            )
        
        for field in self.required_fields:
            if field not in result:
                missing_fields.append(field)
                errors.append(f"缺少必要字段: {field}")
        
        if "status" in result:
            status = result["status"]
            valid_statuses = ["success", "failed", "timeout", "error", "partial"]
            if status not in valid_statuses:
                invalid_fields.append("status")
                warnings.append(f"状态值异常: {status}")
        
        if "open_ports" in result:
            ports = result["open_ports"]
            if not isinstance(ports, list):
                invalid_fields.append("open_ports")
                warnings.append("open_ports 应为列表类型")
            else:
                for port in ports:
                    if not isinstance(port, int) or port < 1 or port > 65535:
                        invalid_fields.append("open_ports")
                        warnings.append(f"无效端口号: {port}")
                        break
        
        if "vulnerabilities" in result:
            vulns = result["vulnerabilities"]
            if not isinstance(vulns, list):
                invalid_fields.append("vulnerabilities")
                warnings.append("vulnerabilities 应为列表类型")
        
        if "confidence" in result:
            confidence = result["confidence"]
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                invalid_fields.append("confidence")
                warnings.append("confidence 应为0-1之间的数值")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            plugin_name=plugin_name,
            errors=errors,
            warnings=warnings,
            missing_fields=missing_fields,
            invalid_fields=invalid_fields
        )
    
    def get_conflict_log(self) -> List[Dict[str, Any]]:
        """
        获取冲突日志
        
        Returns:
            List[Dict]: 冲突日志列表
        """
        return [
            {
                "field_name": c.field_name,
                "plugin_name": c.plugin_name,
                "values": c.values,
                "resolution": c.resolution,
                "resolved_value": c.resolved_value,
                "reason": c.reason,
                "timestamp": c.timestamp.isoformat()
            }
            for c in self.conflict_log
        ]
    
    def clear_conflict_log(self) -> None:
        """
        清空冲突日志
        """
        self.conflict_log.clear()
        logger.info("冲突日志已清空")
    
    def set_plugin_priority(self, plugin_name: str, priority: int) -> None:
        """
        设置插件优先级
        
        Args:
            plugin_name: 插件名称
            priority: 优先级(1-10)
        """
        if not 1 <= priority <= 10:
            raise ValueError("优先级必须在1-10之间")
        self.plugin_priorities[plugin_name] = priority
        logger.info(f"设置插件 {plugin_name} 优先级为 {priority}")
    
    def set_merge_strategy(self, field_name: str, strategy: MergeStrategy) -> None:
        """
        设置字段合并策略
        
        Args:
            field_name: 字段名称
            strategy: 合并策略
        """
        self.merge_strategies[field_name] = strategy
        logger.info(f"设置字段 {field_name} 合并策略为 {strategy.value}")

"""
报告生成子图

负责漏洞分析和报告生成。
执行时间目标: < 30秒

优化功能：
- 报告生成缓存
- 增量报告更新
- 风险评分可视化
- 多格式支持（HTML、PDF、JSON、Markdown）
- AWVS报告集成
"""
import logging
import time
import json
import hashlib
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from enum import Enum

logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    """报告格式枚举"""
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"


class SeverityLevel(str, Enum):
    """漏洞严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


SEVERITY_SCORES = {
    SeverityLevel.CRITICAL: 10.0,
    SeverityLevel.HIGH: 8.0,
    SeverityLevel.MEDIUM: 5.0,
    SeverityLevel.LOW: 3.0,
    SeverityLevel.INFO: 1.0
}

SEVERITY_COLORS = {
    SeverityLevel.CRITICAL: "#c0392b",
    SeverityLevel.HIGH: "#e74c3c",
    SeverityLevel.MEDIUM: "#f39c12",
    SeverityLevel.LOW: "#3498db",
    SeverityLevel.INFO: "#95a5a6"
}

SEVERITY_LABELS = {
    SeverityLevel.CRITICAL: "严重",
    SeverityLevel.HIGH: "高危",
    SeverityLevel.MEDIUM: "中危",
    SeverityLevel.LOW: "低危",
    SeverityLevel.INFO: "信息"
}


@dataclass
class ReportState:
    """
    报告状态
    
    ReportGraph专用的轻量级状态类。
    """
    target: str
    task_id: str
    tool_results: Dict[str, Any] = field(default_factory=dict)
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    target_context: Dict[str, Any] = field(default_factory=dict)
    scan_summary: Dict[str, Any] = field(default_factory=dict)
    report_content: Optional[str] = None
    report_format: str = "json"
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    awvs_data: Dict[str, Any] = field(default_factory=dict)
    incremental_update: bool = False
    previous_report: Optional[Dict[str, Any]] = None
    risk_score: float = 0.0
    risk_level: str = "low"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "task_id": self.task_id,
            "tool_results": self.tool_results,
            "vulnerabilities": self.vulnerabilities,
            "target_context": self.target_context,
            "scan_summary": self.scan_summary,
            "report_content": self.report_content,
            "report_format": self.report_format,
            "errors": self.errors,
            "execution_time": self.execution_time,
            "awvs_data": self.awvs_data,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level
        }


class ReportCache:
    """
    报告缓存管理器
    
    使用内存缓存提升报告生成效率，支持基于内容哈希的缓存键。
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        初始化缓存管理器
        
        Args:
            max_size: 最大缓存数量
            ttl: 缓存过期时间（秒）
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._max_size = max_size
        self._ttl = ttl
        self._lock = asyncio.Lock()
        logger.info(f"📦 报告缓存初始化 | 最大缓存: {max_size} | TTL: {ttl}s")
    
    def _generate_cache_key(self, task_id: str, content_hash: str, format: str) -> str:
        """生成缓存键"""
        return f"{task_id}:{content_hash}:{format}"
    
    def _hash_content(self, content: Dict[str, Any]) -> str:
        """计算内容哈希"""
        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    async def get(self, task_id: str, content: Dict[str, Any], format: str) -> Optional[str]:
        """
        从缓存获取报告
        
        Args:
            task_id: 任务ID
            content: 报告内容数据
            format: 报告格式
            
        Returns:
            缓存的报告内容，如果不存在或已过期则返回None
        """
        async with self._lock:
            content_hash = self._hash_content(content)
            cache_key = self._generate_cache_key(task_id, content_hash, format)
            
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self._ttl:
                    logger.debug(f"[{task_id}] 🎯 缓存命中 | 格式: {format}")
                    return cached_data
                else:
                    del self._cache[cache_key]
                    logger.debug(f"[{task_id}] ⏰ 缓存过期 | 格式: {format}")
            
            return None
    
    async def set(self, task_id: str, content: Dict[str, Any], format: str, report: str) -> None:
        """
        设置缓存
        
        Args:
            task_id: 任务ID
            content: 报告内容数据
            format: 报告格式
            report: 生成的报告内容
        """
        async with self._lock:
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
                logger.debug(f"🗑️ 清理最旧缓存")
            
            content_hash = self._hash_content(content)
            cache_key = self._generate_cache_key(task_id, content_hash, format)
            self._cache[cache_key] = (report, time.time())
            logger.debug(f"[{task_id}] 💾 缓存已存储 | 格式: {format}")
    
    async def invalidate(self, task_id: str) -> None:
        """
        使指定任务的所有缓存失效
        
        Args:
            task_id: 任务ID
        """
        async with self._lock:
            keys_to_delete = [k for k in self._cache if k.startswith(f"{task_id}:")]
            for key in keys_to_delete:
                del self._cache[key]
            logger.debug(f"[{task_id}] 🗑️ 缓存已失效 | 清理数量: {len(keys_to_delete)}")


report_cache = ReportCache()


class RiskScoreCalculator:
    """
    风险评分计算器
    
    基于漏洞数量、严重程度和可利用性计算综合风险评分。
    """
    
    @staticmethod
    def calculate(vulnerabilities: List[Dict[str, Any]], target_context: Dict[str, Any] = None) -> Tuple[float, str]:
        """
        计算风险评分
        
        Args:
            vulnerabilities: 漏洞列表
            target_context: 目标上下文信息
            
        Returns:
            (风险评分, 风险等级)
        """
        if not vulnerabilities:
            return 0.0, "low"
        
        base_score = 0.0
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            vuln_score = SEVERITY_SCORES.get(SeverityLevel(severity), 1.0)
            
            exploitability = vuln.get("exploitability", 1.0)
            impact = vuln.get("impact", 1.0)
            
            base_score += vuln_score * exploitability * impact
        
        if target_context:
            if target_context.get("waf"):
                base_score *= 0.8
            if target_context.get("cdn"):
                base_score *= 0.95
            if target_context.get("cms"):
                base_score *= 1.1
        
        max_possible_score = len(vulnerabilities) * 10.0
        normalized_score = min(100.0, (base_score / max_possible_score) * 100) if max_possible_score > 0 else 0.0
        
        if normalized_score >= 80:
            risk_level = "critical"
        elif normalized_score >= 60:
            risk_level = "high"
        elif normalized_score >= 40:
            risk_level = "medium"
        elif normalized_score >= 20:
            risk_level = "low"
        else:
            risk_level = "info"
        
        return round(normalized_score, 2), risk_level
    
    @staticmethod
    def get_risk_color(risk_level: str) -> str:
        """获取风险等级对应的颜色"""
        colors = {
            "critical": "#c0392b",
            "high": "#e74c3c",
            "medium": "#f39c12",
            "low": "#3498db",
            "info": "#95a5a6"
        }
        return colors.get(risk_level, "#95a5a6")


class VulnerabilityAnalysisNode:
    """
    漏洞分析节点
    
    分析扫描结果，识别和评估漏洞。
    支持AWVS数据集成和增量更新。
    """
    
    def __init__(self):
        self.timeout = 10.0
    
    async def __call__(self, state: ReportState) -> ReportState:
        logger.info(f"[{state.task_id}] 🔍 开始漏洞分析")
        
        try:
            analyzed_vulns = []
            
            for vuln in state.vulnerabilities:
                analyzed_vuln = self._analyze_vulnerability(vuln, state.target_context)
                analyzed_vulns.append(analyzed_vuln)
            
            for tool_name, result in state.tool_results.items():
                if result.get("status") == "success":
                    tool_vulns = self._extract_vulnerabilities_from_result(tool_name, result)
                    analyzed_vulns.extend(tool_vulns)
            
            if state.awvs_data:
                awvs_vulns = self._extract_awvs_vulnerabilities(state.awvs_data)
                analyzed_vulns.extend(awvs_vulns)
                logger.info(f"[{state.task_id}] 📊 AWVS漏洞集成完成 | 数量: {len(awvs_vulns)}")
            
            if state.incremental_update and state.previous_report:
                analyzed_vulns = self._merge_vulnerabilities(
                    analyzed_vulns,
                    state.previous_report.get("vulnerabilities", [])
                )
                logger.info(f"[{state.task_id}] 🔄 增量更新完成")
            
            state.vulnerabilities = self._deduplicate_vulnerabilities(analyzed_vulns)
            
            state.scan_summary = {
                "total_vulnerabilities": len(state.vulnerabilities),
                "critical": len([v for v in state.vulnerabilities if v.get("severity") == "critical"]),
                "high": len([v for v in state.vulnerabilities if v.get("severity") == "high"]),
                "medium": len([v for v in state.vulnerabilities if v.get("severity") == "medium"]),
                "low": len([v for v in state.vulnerabilities if v.get("severity") == "low"]),
                "info": len([v for v in state.vulnerabilities if v.get("severity") == "info"])
            }
            
            state.risk_score, state.risk_level = RiskScoreCalculator.calculate(
                state.vulnerabilities, state.target_context
            )
            
            logger.info(f"[{state.task_id}] ✅ 漏洞分析完成 | 发现 {len(state.vulnerabilities)} 个漏洞 | 风险评分: {state.risk_score}")
            
        except Exception as e:
            error_msg = f"漏洞分析失败: {str(e)}"
            state.errors.append(error_msg)
            logger.error(f"[{state.task_id}] ❌ {error_msg}")
        
        return state
    
    def _analyze_vulnerability(self, vuln: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        analyzed = vuln.copy()
        
        if "severity" not in analyzed:
            analyzed["severity"] = self._determine_severity(vuln)
        
        analyzed["analyzed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        analyzed["exploitability"] = self._calculate_exploitability(vuln)
        analyzed["impact"] = self._calculate_impact(vuln, context)
        
        return analyzed
    
    def _determine_severity(self, vuln: Dict[str, Any]) -> str:
        cve = vuln.get("cve", "").lower()
        vuln_type = vuln.get("vuln_type", "").lower()
        
        critical_keywords = ["rce", "remote", "code_exec", "deserialization", "ssrf"]
        high_keywords = ["sqli", "injection", "xss", "auth_bypass", "lfi", "rfi"]
        medium_keywords = ["csrf", "redirect", "leak", "idor"]
        
        combined = f"{cve} {vuln_type}"
        
        if any(x in combined for x in critical_keywords):
            return "critical"
        elif any(x in combined for x in high_keywords):
            return "high"
        elif any(x in combined for x in medium_keywords):
            return "medium"
        else:
            return "low"
    
    def _calculate_exploitability(self, vuln: Dict[str, Any]) -> float:
        """计算漏洞可利用性评分"""
        exploitability = 1.0
        
        if vuln.get("poc_available"):
            exploitability *= 1.3
        if vuln.get("public_exploit"):
            exploitability *= 1.2
        if vuln.get("cve"):
            exploitability *= 1.1
        
        return min(2.0, exploitability)
    
    def _calculate_impact(self, vuln: Dict[str, Any], context: Dict[str, Any]) -> float:
        """计算漏洞影响评分"""
        impact = 1.0
        
        vuln_type = vuln.get("vuln_type", "").lower()
        
        if any(x in vuln_type for x in ["rce", "sqli", "deserialization"]):
            impact *= 1.5
        elif any(x in vuln_type for x in ["xss", "csrf", "lfi"]):
            impact *= 1.2
        
        if context:
            if context.get("sensitive_data"):
                impact *= 1.3
            if context.get("public_facing"):
                impact *= 1.1
        
        return min(2.0, impact)
    
    def _extract_vulnerabilities_from_result(self, tool_name: str, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        vulns = []
        
        if tool_name == "portscan":
            open_ports = result.get("data", {}).get("open_ports", [])
            for port in open_ports:
                if port in [22, 23, 3389]:
                    vulns.append({
                        "type": "sensitive_port",
                        "port": port,
                        "severity": "info",
                        "details": f"敏感端口 {port} 开放"
                    })
        
        return vulns
    
    def _extract_awvs_vulnerabilities(self, awvs_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从AWVS数据中提取漏洞信息"""
        vulns = []
        
        vulnerabilities = awvs_data.get("vulnerabilities", [])
        for v in vulnerabilities:
            severity = v.get("severity", "info")
            if isinstance(severity, int):
                severity_map = {3: "high", 2: "medium", 1: "low", 0: "info"}
                severity = severity_map.get(severity, "info")
            
            vulns.append({
                "vuln_id": v.get("vuln_id"),
                "cve": v.get("cve_id", v.get("vt_name", "")),
                "vuln_type": v.get("vt_name", "Unknown"),
                "severity": severity.lower(),
                "title": v.get("vt_name", "Unknown Vulnerability"),
                "description": v.get("description", ""),
                "url": v.get("affects_url", ""),
                "remediation": v.get("recommendation", ""),
                "source": "awvs",
                "poc_available": v.get("poc_available", False),
                "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return vulns
    
    def _merge_vulnerabilities(self, new_vulns: List[Dict[str, Any]], 
                                old_vulns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并新旧漏洞列表（增量更新）"""
        merged = {v.get("vuln_id", v.get("cve", "")): v for v in old_vulns}
        
        for vuln in new_vulns:
            key = vuln.get("vuln_id", vuln.get("cve", ""))
            if key in merged:
                merged[key].update(vuln)
                merged[key]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                vuln["first_seen"] = time.strftime("%Y-%m-%d %H:%M:%S")
                merged[key] = vuln
        
        return list(merged.values())
    
    def _deduplicate_vulnerabilities(self, vulns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique_vulns = []
        
        for vuln in vulns:
            key = (vuln.get("cve", ""), vuln.get("type", ""), vuln.get("target", ""), vuln.get("url", ""))
            if key not in seen:
                seen.add(key)
                unique_vulns.append(vuln)
        
        return unique_vulns


class ReportGenerationNode:
    """
    报告生成节点
    
    根据分析结果生成扫描报告。
    支持多格式输出：JSON、HTML、PDF、Markdown。
    """
    
    def __init__(self):
        self.timeout = 15.0
    
    async def __call__(self, state: ReportState) -> ReportState:
        logger.info(f"[{state.task_id}] 📝 开始生成报告 | 格式: {state.report_format}")
        
        try:
            report_content = await self._generate_report(state)
            state.report_content = report_content
            
            logger.info(f"[{state.task_id}] ✅ 报告生成完成 | 格式: {state.report_format}")
            
        except Exception as e:
            error_msg = f"报告生成失败: {str(e)}"
            state.errors.append(error_msg)
            logger.error(f"[{state.task_id}] ❌ {error_msg}")
        
        return state
    
    async def _generate_report(self, state: ReportState) -> str:
        """生成报告（带缓存）"""
        report_data = self._prepare_report_data(state)
        
        cached = await report_cache.get(state.task_id, report_data, state.report_format)
        if cached:
            return cached
        
        format_generators = {
            "json": self._generate_json_report,
            "html": self._generate_html_report,
            "markdown": self._generate_markdown_report,
            "pdf": self._generate_pdf_report
        }
        
        generator = format_generators.get(state.report_format, self._generate_json_report)
        report_content = generator(state, report_data)
        
        await report_cache.set(state.task_id, report_data, state.report_format, report_content)
        
        return report_content
    
    def _prepare_report_data(self, state: ReportState) -> Dict[str, Any]:
        """准备报告数据"""
        return {
            "task_id": state.task_id,
            "target": state.target,
            "scan_summary": state.scan_summary,
            "vulnerabilities": state.vulnerabilities,
            "target_info": {
                "server": state.target_context.get("server"),
                "cms": state.target_context.get("cms"),
                "waf": state.target_context.get("waf"),
                "cdn": state.target_context.get("cdn"),
                "open_ports": state.target_context.get("open_ports", [])
            },
            "risk_assessment": {
                "score": state.risk_score,
                "level": state.risk_level,
                "color": RiskScoreCalculator.get_risk_color(state.risk_level)
            },
            "awvs_data": state.awvs_data,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _generate_json_report(self, state: ReportState, data: Dict[str, Any] = None) -> str:
        """生成JSON格式报告"""
        if data is None:
            data = self._prepare_report_data(state)
        
        report = {
            "meta": {
                "version": "2.0",
                "generator": "AI_WebSecurity Report Engine",
                "generated_at": data["generated_at"]
            },
            "task_info": {
                "task_id": data["task_id"],
                "target": data["target"]
            },
            "executive_summary": self._generate_executive_summary(data),
            "scan_summary": data["scan_summary"],
            "risk_assessment": data["risk_assessment"],
            "vulnerabilities": {
                "total": len(data["vulnerabilities"]),
                "items": data["vulnerabilities"]
            },
            "target_info": data["target_info"],
            "recommendations": self._generate_recommendations(data["vulnerabilities"]),
            "appendix": {
                "awvs_integration": bool(data.get("awvs_data")),
                "scan_tools": list(state.tool_results.keys()) if state.tool_results else []
            }
        }
        
        return json.dumps(report, ensure_ascii=False, indent=2)
    
    def _generate_html_report(self, state: ReportState, data: Dict[str, Any] = None) -> str:
        """生成HTML格式报告"""
        if data is None:
            data = self._prepare_report_data(state)
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>安全扫描报告 - {data['target']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .meta {{ font-size: 14px; opacity: 0.9; }}
        
        .risk-gauge {{ background: white; border-radius: 10px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .risk-gauge h2 {{ color: #333; margin-bottom: 20px; }}
        .gauge-container {{ display: flex; align-items: center; gap: 30px; }}
        .gauge {{ width: 200px; height: 200px; position: relative; }}
        .gauge-value {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 48px; font-weight: bold; color: {data['risk_assessment']['color']}; }}
        .gauge-label {{ font-size: 14px; color: #666; margin-top: 10px; text-align: center; }}
        .risk-details {{ flex: 1; }}
        .risk-level {{ font-size: 24px; font-weight: bold; color: {data['risk_assessment']['color']}; margin-bottom: 10px; }}
        
        .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card.critical {{ border-top: 4px solid #c0392b; }}
        .card.high {{ border-top: 4px solid #e74c3c; }}
        .card.medium {{ border-top: 4px solid #f39c12; }}
        .card.low {{ border-top: 4px solid #3498db; }}
        .card.info {{ border-top: 4px solid #95a5a6; }}
        .card .count {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
        .card.critical .count {{ color: #c0392b; }}
        .card.high .count {{ color: #e74c3c; }}
        .card.medium .count {{ color: #f39c12; }}
        .card.low .count {{ color: #3498db; }}
        .card.info .count {{ color: #95a5a6; }}
        .card .label {{ font-size: 14px; color: #666; }}
        
        .section {{ background: white; border-radius: 10px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
        
        .vuln-item {{ border: 1px solid #eee; border-radius: 8px; padding: 20px; margin-bottom: 15px; transition: box-shadow 0.3s; }}
        .vuln-item:hover {{ box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .vuln-item.critical {{ border-left: 5px solid #c0392b; }}
        .vuln-item.high {{ border-left: 5px solid #e74c3c; }}
        .vuln-item.medium {{ border-left: 5px solid #f39c12; }}
        .vuln-item.low {{ border-left: 5px solid #3498db; }}
        .vuln-item.info {{ border-left: 5px solid #95a5a6; }}
        .vuln-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .vuln-title {{ font-size: 18px; font-weight: bold; color: #333; }}
        .vuln-severity {{ padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; }}
        .vuln-severity.critical {{ background: #c0392b; }}
        .vuln-severity.high {{ background: #e74c3c; }}
        .vuln-severity.medium {{ background: #f39c12; }}
        .vuln-severity.low {{ background: #3498db; }}
        .vuln-severity.info {{ background: #95a5a6; }}
        .vuln-meta {{ font-size: 13px; color: #666; margin-bottom: 10px; }}
        .vuln-description {{ color: #555; margin-bottom: 10px; }}
        .vuln-remediation {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; }}
        .vuln-remediation h4 {{ color: #28a745; margin-bottom: 8px; }}
        
        .recommendations {{ background: #e8f5e9; border-radius: 8px; padding: 20px; }}
        .recommendations h3 {{ color: #2e7d32; margin-bottom: 15px; }}
        .recommendations ul {{ list-style: none; }}
        .recommendations li {{ padding: 10px 0; border-bottom: 1px solid #c8e6c9; }}
        .recommendations li:last-child {{ border-bottom: none; }}
        .recommendations li:before {{ content: "✓"; color: #2e7d32; margin-right: 10px; }}
        
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        
        @media print {{
            body {{ background: white; }}
            .section, .card, .vuln-item {{ box-shadow: none; border: 1px solid #ddd; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 安全扫描报告</h1>
            <div class="meta">
                <p>目标: {data['target']}</p>
                <p>任务ID: {data['task_id']}</p>
                <p>生成时间: {data['generated_at']}</p>
            </div>
        </div>
        
        <div class="risk-gauge">
            <h2>📊 风险评估</h2>
            <div class="gauge-container">
                <div class="gauge">
                    <svg viewBox="0 0 200 200">
                        <circle cx="100" cy="100" r="80" fill="none" stroke="#eee" stroke-width="20"/>
                        <circle cx="100" cy="100" r="80" fill="none" stroke="{data['risk_assessment']['color']}" stroke-width="20"
                            stroke-dasharray="{data['risk_assessment']['score'] * 5.03} 503"
                            stroke-linecap="round" transform="rotate(-90 100 100)"/>
                    </svg>
                    <div class="gauge-value">{data['risk_assessment']['score']}</div>
                </div>
                <div class="risk-details">
                    <div class="risk-level">风险等级: {self._get_risk_level_text(data['risk_assessment']['level'])}</div>
                    <p>综合风险评分基于漏洞数量、严重程度、可利用性和影响程度计算得出。</p>
                    <p>建议优先处理高危和严重级别的漏洞。</p>
                </div>
            </div>
        </div>
        
        <div class="summary-cards">
            <div class="card critical">
                <div class="label">严重</div>
                <div class="count">{data['scan_summary'].get('critical', 0)}</div>
            </div>
            <div class="card high">
                <div class="label">高危</div>
                <div class="count">{data['scan_summary'].get('high', 0)}</div>
            </div>
            <div class="card medium">
                <div class="label">中危</div>
                <div class="count">{data['scan_summary'].get('medium', 0)}</div>
            </div>
            <div class="card low">
                <div class="label">低危</div>
                <div class="count">{data['scan_summary'].get('low', 0)}</div>
            </div>
            <div class="card info">
                <div class="label">信息</div>
                <div class="count">{data['scan_summary'].get('info', 0)}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 执行摘要</h2>
            <p>{self._generate_executive_summary(data)}</p>
        </div>
        
        <div class="section">
            <h2>🔍 漏洞详情</h2>
            {self._generate_vuln_html(data['vulnerabilities'])}
        </div>
        
        <div class="section">
            <h2>💡 修复建议</h2>
            <div class="recommendations">
                {self._generate_recommendations_html(data['vulnerabilities'])}
            </div>
        </div>
        
        <div class="footer">
            <p>报告由 AI_WebSecurity 自动生成 | 生成时间: {data['generated_at']}</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_markdown_report(self, state: ReportState, data: Dict[str, Any] = None) -> str:
        """生成Markdown格式报告"""
        if data is None:
            data = self._prepare_report_data(state)
        
        md = f"""# 安全扫描报告

## 基本信息

- **目标**: {data['target']}
- **任务ID**: {data['task_id']}
- **生成时间**: {data['generated_at']}

## 风险评估

- **风险评分**: {data['risk_assessment']['score']}
- **风险等级**: {self._get_risk_level_text(data['risk_assessment']['level'])}

## 漏洞统计

| 严重程度 | 数量 |
|---------|------|
| 严重 | {data['scan_summary'].get('critical', 0)} |
| 高危 | {data['scan_summary'].get('high', 0)} |
| 中危 | {data['scan_summary'].get('medium', 0)} |
| 低危 | {data['scan_summary'].get('low', 0)} |
| 信息 | {data['scan_summary'].get('info', 0)} |

## 执行摘要

{self._generate_executive_summary(data)}

## 漏洞详情

{self._generate_vuln_markdown(data['vulnerabilities'])}

## 修复建议

{self._generate_recommendations_markdown(data['vulnerabilities'])}

---
*报告由 AI_WebSecurity 自动生成*
"""
        return md
    
    def _generate_pdf_report(self, state: ReportState, data: Dict[str, Any] = None) -> str:
        """生成PDF格式报告（返回HTML，由API层转换为PDF）"""
        return self._generate_html_report(state, data)
    
    def _generate_executive_summary(self, data: Dict[str, Any]) -> str:
        """生成执行摘要"""
        total = data['scan_summary'].get('total_vulnerabilities', 0)
        critical = data['scan_summary'].get('critical', 0)
        high = data['scan_summary'].get('high', 0)
        medium = data['scan_summary'].get('medium', 0)
        
        if total == 0:
            return "本次扫描未发现安全漏洞，目标系统安全性良好。建议定期进行安全扫描以保持系统安全。"
        
        summary_parts = [f"本次扫描共发现 {total} 个安全问题"]
        
        severity_parts = []
        if critical > 0:
            severity_parts.append(f"{critical} 个严重漏洞")
        if high > 0:
            severity_parts.append(f"{high} 个高危漏洞")
        if medium > 0:
            severity_parts.append(f"{medium} 个中危漏洞")
        
        if severity_parts:
            summary_parts.append("，其中包括 " + "、".join(severity_parts))
        
        summary_parts.append(f"。风险评分为 {data['risk_assessment']['score']} 分，风险等级为{self._get_risk_level_text(data['risk_assessment']['level'])}。")
        
        if critical > 0 or high > 0:
            summary_parts.append("建议立即处理严重和高危漏洞，以降低安全风险。")
        
        return "".join(summary_parts)
    
    def _generate_recommendations(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """生成修复建议列表"""
        recommendations = []
        
        severity_order = ["critical", "high", "medium", "low"]
        sorted_vulns = sorted(vulnerabilities, key=lambda v: severity_order.index(v.get("severity", "low")) if v.get("severity") in severity_order else 4)
        
        for vuln in sorted_vulns[:10]:
            if vuln.get("remediation"):
                recommendations.append({
                    "vulnerability": vuln.get("title", vuln.get("cve", "未知漏洞")),
                    "severity": vuln.get("severity", "info"),
                    "recommendation": vuln.get("remediation")
                })
        
        return recommendations
    
    def _generate_recommendations_html(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """生成修复建议HTML"""
        recommendations = self._generate_recommendations(vulnerabilities)
        
        if not recommendations:
            return "<p>暂无具体修复建议。</p>"
        
        items = []
        for rec in recommendations:
            items.append(f"<li><strong>{rec['vulnerability']}</strong> ({rec['severity']}): {rec['recommendation']}</li>")
        
        return "<ul>" + "".join(items) + "</ul>"
    
    def _generate_recommendations_markdown(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """生成修复建议Markdown"""
        recommendations = self._generate_recommendations(vulnerabilities)
        
        if not recommendations:
            return "暂无具体修复建议。"
        
        items = []
        for rec in recommendations:
            items.append(f"- **{rec['vulnerability']}** ({rec['severity']}): {rec['recommendation']}")
        
        return "\n".join(items)
    
    def _generate_vuln_html(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """生成漏洞详情HTML"""
        if not vulnerabilities:
            return "<p>未发现漏洞</p>"
        
        severity_order = ["critical", "high", "medium", "low", "info"]
        sorted_vulns = sorted(vulnerabilities, key=lambda v: severity_order.index(v.get("severity", "info")) if v.get("severity") in severity_order else 4)
        
        html = ""
        for vuln in sorted_vulns:
            severity = vuln.get("severity", "info")
            html += f"""
            <div class="vuln-item {severity}">
                <div class="vuln-header">
                    <span class="vuln-title">{vuln.get('title', vuln.get('cve', vuln.get('vuln_type', '未知漏洞')))}</span>
                    <span class="vuln-severity {severity}">{self._get_severity_text(severity)}</span>
                </div>
                <div class="vuln-meta">
                    <span>类型: {vuln.get('vuln_type', 'N/A')}</span> | 
                    <span>URL: {vuln.get('url', 'N/A')}</span>
                </div>
                <div class="vuln-description">{vuln.get('description', vuln.get('details', '无详细描述'))}</div>
                {f'<div class="vuln-remediation"><h4>修复建议</h4><p>{vuln.get("remediation", "暂无修复建议")}</p></div>' if vuln.get('remediation') else ''}
            </div>
            """
        return html
    
    def _generate_vuln_markdown(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """生成漏洞详情Markdown"""
        if not vulnerabilities:
            return "未发现漏洞"
        
        severity_order = ["critical", "high", "medium", "low", "info"]
        sorted_vulns = sorted(vulnerabilities, key=lambda v: severity_order.index(v.get("severity", "info")) if v.get("severity") in severity_order else 4)
        
        md = ""
        for vuln in sorted_vulns:
            severity = vuln.get("severity", "info")
            md += f"""### {vuln.get('title', vuln.get('cve', '未知漏洞'))}

- **严重程度**: {self._get_severity_text(severity)}
- **类型**: {vuln.get('vuln_type', 'N/A')}
- **URL**: {vuln.get('url', 'N/A')}
- **描述**: {vuln.get('description', vuln.get('details', '无详细描述'))}
- **修复建议**: {vuln.get('remediation', '暂无修复建议')}

---
"""
        return md
    
    def _get_severity_text(self, severity: str) -> str:
        """获取严重程度文本"""
        labels = {
            "critical": "严重",
            "high": "高危",
            "medium": "中危",
            "low": "低危",
            "info": "信息"
        }
        return labels.get(severity.lower(), severity)
    
    def _get_risk_level_text(self, level: str) -> str:
        """获取风险等级文本"""
        labels = {
            "critical": "极高风险",
            "high": "高风险",
            "medium": "中等风险",
            "low": "低风险",
            "info": "信息"
        }
        return labels.get(level.lower(), level)


class ReportGraph:
    """
    报告生成图
    
    分析漏洞并生成扫描报告。
    支持多格式输出、缓存和增量更新。
    """
    
    def __init__(self, max_execution_time: float = 30.0):
        self.max_execution_time = max_execution_time
        self.analysis_node = VulnerabilityAnalysisNode()
        self.generation_node = ReportGenerationNode()
        logger.info(f"📊 ReportGraph 初始化 | 最大执行时间: {max_execution_time}s")
    
    async def execute(self, state: ReportState) -> ReportState:
        """
        执行报告生成
        
        Args:
            state: 报告状态
            
        Returns:
            ReportState: 更新后的状态
        """
        start_time = time.time()
        logger.info(f"[{state.task_id}] 🚀 开始报告生成图")
        
        try:
            state = await self.analysis_node(state)
            
            state = await self.generation_node(state)
            
            total_time = time.time() - start_time
            state.execution_time = total_time
            
            if total_time > self.max_execution_time:
                logger.warning(f"[{state.task_id}] ⚠️ ReportGraph 执行超时: {total_time:.2f}s")
            else:
                logger.info(f"[{state.task_id}] ✅ ReportGraph 执行完成 | 耗时: {total_time:.2f}s")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ ReportGraph 执行失败: {str(e)}")
            state.errors.append(f"报告生成图失败: {str(e)}")
        
        return state
    
    def get_result_dto(self, state: ReportState) -> 'ReportDTO':
        """
        将状态转换为ReportDTO
        
        Args:
            state: 报告状态
            
        Returns:
            ReportDTO: 报告结果DTO
        """
        from .dto import ReportDTO, TaskStatus, VulnerabilityDTO, SeverityLevel
        
        status = TaskStatus.COMPLETED if not state.errors else TaskStatus.FAILED
        
        vulnerabilities = []
        for v in state.vulnerabilities:
            if isinstance(v, VulnerabilityDTO):
                vulnerabilities.append(v)
            elif isinstance(v, dict):
                severity = v.get("severity", "medium")
                try:
                    severity = SeverityLevel(severity)
                except ValueError:
                    severity = SeverityLevel.MEDIUM
                vulnerabilities.append(VulnerabilityDTO(
                    vuln_id=v.get("vuln_id", v.get("id", "unknown")),
                    vuln_type=v.get("vuln_type", v.get("type", "unknown")),
                    severity=severity,
                    title=v.get("title", v.get("name", "Unknown Vulnerability")),
                    description=v.get("description", v.get("details")),
                    url=v.get("url"),
                    payload=v.get("payload"),
                    evidence=v.get("evidence"),
                    remediation=v.get("remediation"),
                    cve_id=v.get("cve_id", v.get("cve")),
                    poc_name=v.get("poc_name")
                ))
        
        return ReportDTO(
            task_id=state.task_id,
            target=state.target,
            status=status,
            vulnerabilities=vulnerabilities,
            summary=state.scan_summary,
            tool_findings=state.tool_results,
            report_content=state.report_content,
            report_format=state.report_format,
            total_execution_time=state.execution_time
        )
    
    async def invalidate_cache(self, task_id: str) -> None:
        """
        使指定任务的缓存失效
        
        Args:
            task_id: 任务ID
        """
        await report_cache.invalidate(task_id)

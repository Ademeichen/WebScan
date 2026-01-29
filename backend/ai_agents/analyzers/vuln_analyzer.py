"""
漏洞分析器

实现漏洞去重、排序和严重度评估功能。
"""
import logging
from typing import List, Dict, Any
from ..agent_config import agent_config

logger = logging.getLogger(__name__)


class VulnerabilityAnalyzer:
    """
    漏洞分析器
    
    负责对发现的漏洞进行去重、排序和严重度评估。
    """
    
    def __init__(self):
        self.severity_order = agent_config.SEVERITY_ORDER.copy()
        logger.info("🔍 漏洞分析器初始化完成")
    
    def deduplicate(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        漏洞去重
        
        根据CVE和目标组合去重。
        
        Args:
            vulnerabilities: 漏洞列表
            
        Returns:
            List[Dict]: 去重后的漏洞列表
        """
        unique_vulns = {}
        
        for vuln in vulnerabilities:
            key = self._get_vuln_key(vuln)
            if key not in unique_vulns:
                unique_vulns[key] = vuln
            else:
                logger.debug(f"去重漏洞: {key}")
        
        deduplicated = list(unique_vulns.values())
        logger.info(f"漏洞去重: {len(vulnerabilities)} -> {len(deduplicated)}")
        return deduplicated
    
    def sort_by_severity(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按严重度排序漏洞
        
        Args:
            vulnerabilities: 漏洞列表
            
        Returns:
            List[Dict]: 排序后的漏洞列表
        """
        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda x: self.severity_order.get(
                x.get("severity", "info").lower(),
                0
            ),
            reverse=True
        )
        
        logger.info("漏洞按严重度排序完成")
        return sorted_vulns
    
    def analyze(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析漏洞列表
        
        生成漏洞统计信息。
        
        Args:
            vulnerabilities: 漏洞列表
            
        Returns:
            Dict: 分析结果，包含统计信息
        """
        if not vulnerabilities:
            return {
                "total": 0,
                "by_severity": {},
                "summary": "未发现漏洞"
            }
        
        # 按严重度统计
        severity_stats = {}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info").lower()
            severity_stats[severity] = severity_stats.get(severity, 0) + 1
        
        # 生成摘要
        summary_parts = []
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = severity_stats.get(severity, 0)
            if count > 0:
                summary_parts.append(f"{severity.capitalize()}: {count}")
        
        summary = f"共发现 {len(vulnerabilities)} 个漏洞: " + ", ".join(summary_parts)
        
        return {
            "total": len(vulnerabilities),
            "by_severity": severity_stats,
            "summary": summary
        }
    
    async def enrich_with_kb(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用知识库丰富漏洞信息
        
        Args:
            vulnerabilities: 漏洞列表
            
        Returns:
            List[Dict]: 丰富后的漏洞列表
        """
        if not agent_config.ENABLE_KB_INTEGRATION:
            return vulnerabilities
        
        enriched = []
        
        for vuln in vulnerabilities:
            cve = vuln.get("cve", "")
            if cve:
                kb_info = await self._get_kb_info(cve)
                if kb_info:
                    vuln["kb_info"] = kb_info
                    if kb_info.get("solution"):
                        vuln["fix_suggestion"] = kb_info["solution"]
            enriched.append(vuln)
        
        return enriched
    
    def _get_vuln_key(self, vuln: Dict[str, Any]) -> str:
        """
        获取漏洞唯一键
        
        Args:
            vuln: 漏洞信息
            
        Returns:
            str: 唯一键
        """
        target = vuln.get("target", "")
        cve = vuln.get("cve", "")
        return f"{cve}_{target}"
    
    async def _get_kb_info(self, cve: str) -> Dict[str, Any]:
        """
        从知识库获取漏洞信息
        
        Args:
            cve: CVE编号
            
        Returns:
            Dict: 知识库信息
        """
        try:
            from models import VulnerabilityKB
            kb_entry = await VulnerabilityKB.get_or_none(cve_id=cve)
            if kb_entry:
                return {
                    "name": kb_entry.name,
                    "description": kb_entry.description,
                    "solution": kb_entry.solution,
                    "cvss_score": kb_entry.cvss_score,
                    "references": kb_entry.references
                }
        except Exception as e:
            logger.error(f"查询知识库失败: {str(e)}")
        
        return {}

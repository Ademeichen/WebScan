"""
报告生成器

生成标准化的扫描报告。

优化功能：
- 模板渲染性能优化
- 完善报告结构（摘要、详情、建议、附录）
- 风险评分可视化
- 多格式导出（HTML、PDF、JSON、Markdown）
- AWVS报告集成
"""
import logging
import json
import time
import asyncio
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache
from string import Template
from enum import Enum

logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    """报告格式枚举"""
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"


SEVERITY_CONFIG = {
    "critical": {"score": 10.0, "color": "#c0392b", "label": "严重", "order": 0},
    "high": {"score": 8.0, "color": "#e74c3c", "label": "高危", "order": 1},
    "medium": {"score": 5.0, "color": "#f39c12", "label": "中危", "order": 2},
    "low": {"score": 3.0, "color": "#3498db", "label": "低危", "order": 3},
    "info": {"score": 1.0, "color": "#95a5a6", "label": "信息", "order": 4}
}


class TemplateCache:
    """
    模板缓存管理器
    
    缓存已编译的模板以提升渲染性能。
    """
    
    def __init__(self, max_size: int = 50):
        self._cache: Dict[str, Template] = {}
        self._max_size = max_size
    
    def get_template(self, template_str: str) -> Template:
        """获取或创建模板实例"""
        cache_key = hashlib.md5(template_str.encode()).hexdigest()
        
        if cache_key not in self._cache:
            if len(self._cache) >= self._max_size:
                self._cache.pop(next(iter(self._cache)))
            
            self._cache[cache_key] = Template(template_str)
        
        return self._cache[cache_key]


template_cache = TemplateCache()


class RiskAssessment:
    """
    风险评估计算器
    
    计算综合风险评分和风险等级。
    """
    
    @staticmethod
    def calculate(vulnerabilities: List[Dict[str, Any]], target_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        计算风险评分
        
        Args:
            vulnerabilities: 漏洞列表
            target_context: 目标上下文信息
            
        Returns:
            风险评估结果字典
        """
        if not vulnerabilities:
            return {
                "score": 0.0,
                "level": "info",
                "label": "无风险",
                "color": "#95a5a6",
                "factors": []
            }
        
        base_score = 0.0
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        factors = []
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["info"])
            vuln_score = config["score"]
            
            exploitability = 1.0
            if vuln.get("poc_available"):
                exploitability *= 1.3
            if vuln.get("cve"):
                exploitability *= 1.1
            
            impact = 1.0
            vuln_type = str(vuln.get("vuln_type", "")).lower()
            if any(x in vuln_type for x in ["rce", "sqli", "deserialization"]):
                impact *= 1.5
            
            final_score = vuln_score * exploitability * impact
            base_score += final_score
            
            if final_score >= 8.0:
                factors.append({
                    "type": "high_risk_vuln",
                    "description": f"{vuln.get('title', '未知漏洞')} - {config['label']}",
                    "score": final_score
                })
        
        context_multiplier = 1.0
        if target_context:
            if target_context.get("waf"):
                context_multiplier *= 0.8
                factors.append({"type": "mitigation", "description": "存在WAF防护", "multiplier": 0.8})
            if target_context.get("cdn"):
                context_multiplier *= 0.95
            if target_context.get("cms"):
                context_multiplier *= 1.1
        
        base_score *= context_multiplier
        
        max_possible = len(vulnerabilities) * 15.0
        normalized_score = min(100.0, (base_score / max_possible) * 100) if max_possible > 0 else 0.0
        
        if normalized_score >= 80:
            level, label, color = "critical", "极高风险", "#c0392b"
        elif normalized_score >= 60:
            level, label, color = "high", "高风险", "#e74c3c"
        elif normalized_score >= 40:
            level, label, color = "medium", "中等风险", "#f39c12"
        elif normalized_score >= 20:
            level, label, color = "low", "低风险", "#3498db"
        else:
            level, label, color = "info", "信息", "#95a5a6"
        
        return {
            "score": round(normalized_score, 2),
            "level": level,
            "label": label,
            "color": color,
            "factors": factors[:5],
            "severity_counts": severity_counts
        }


class ReportGenerator:
    """
    报告生成器
    
    负责生成标准化的扫描报告，支持多种格式输出。
    """
    
    def __init__(self):
        self._init_templates()
        logger.info("📄 报告生成器初始化完成")
    
    def _init_templates(self):
        """初始化报告模板"""
        self.html_template = self._get_html_template()
        self.md_template = self._get_markdown_template()
    
    def _get_html_template(self) -> str:
        """获取HTML模板"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${report_title}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; margin-bottom: 30px; }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header .meta { font-size: 14px; opacity: 0.9; }
        
        .risk-gauge { background: white; border-radius: 10px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .risk-gauge h2 { color: #333; margin-bottom: 20px; }
        .gauge-container { display: flex; align-items: center; gap: 30px; flex-wrap: wrap; }
        .gauge { width: 200px; height: 200px; position: relative; }
        .gauge-value { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 48px; font-weight: bold; }
        .risk-details { flex: 1; min-width: 300px; }
        .risk-level { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
        .risk-factors { margin-top: 15px; }
        .risk-factor { padding: 8px 12px; margin: 5px 0; background: #f8f9fa; border-radius: 5px; font-size: 13px; }
        
        .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card .count { font-size: 36px; font-weight: bold; margin: 10px 0; }
        .card .label { font-size: 14px; color: #666; }
        
        .section { background: white; border-radius: 10px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .section h2 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }
        .section h3 { color: #555; margin: 20px 0 10px 0; }
        
        .vuln-item { border: 1px solid #eee; border-radius: 8px; padding: 20px; margin-bottom: 15px; transition: box-shadow 0.3s; }
        .vuln-item:hover { box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .vuln-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 10px; }
        .vuln-title { font-size: 18px; font-weight: bold; color: #333; }
        .vuln-severity { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; }
        .vuln-meta { font-size: 13px; color: #666; margin-bottom: 10px; }
        .vuln-description { color: #555; margin-bottom: 10px; }
        .vuln-remediation { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; }
        .vuln-remediation h4 { color: #28a745; margin-bottom: 8px; }
        
        .recommendations { background: #e8f5e9; border-radius: 8px; padding: 20px; }
        .recommendations h3 { color: #2e7d32; margin-bottom: 15px; }
        .recommendations ul { list-style: none; }
        .recommendations li { padding: 10px 0; border-bottom: 1px solid #c8e6c9; }
        .recommendations li:last-child { border-bottom: none; }
        .recommendations li:before { content: "✓"; color: #2e7d32; margin-right: 10px; }
        
        .awvs-section { background: #fff3e0; border-radius: 8px; padding: 20px; margin-top: 20px; }
        .awvs-section h3 { color: #e65100; margin-bottom: 15px; }
        
        .target-info table { width: 100%; border-collapse: collapse; }
        .target-info th, .target-info td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        .target-info th { background: #f8f9fa; font-weight: bold; color: #555; }
        
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        
        @media print {
            body { background: white; }
            .section, .card, .vuln-item { box-shadow: none; border: 1px solid #ddd; }
        }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header { padding: 20px; }
            .section { padding: 15px; }
        }
    </style>
</head>
<body>
    <div class="container">
        ${header_section}
        ${risk_section}
        ${summary_section}
        ${executive_summary_section}
        ${target_info_section}
        ${vulnerabilities_section}
        ${recommendations_section}
        ${awvs_section}
        ${footer_section}
    </div>
</body>
</html>
"""
    
    def _get_markdown_template(self) -> str:
        """获取Markdown模板"""
        return """# ${report_title}

## 基本信息

${basic_info}

## 风险评估

${risk_assessment}

## 漏洞统计

${vuln_statistics}

## 执行摘要

${executive_summary}

## 目标信息

${target_info}

## 漏洞详情

${vulnerabilities}

## 修复建议

${recommendations}

${awvs_section}

---
*报告由 AI_WebSecurity 自动生成 | 生成时间: ${generated_at}*
"""
    
    def generate_report(self, state: Any) -> Dict[str, Any]:
        """
        生成扫描报告
        
        Args:
            state: Agent状态
            
        Returns:
            Dict: 扫描报告
        """
        risk_assessment = RiskAssessment.calculate(
            state.vulnerabilities,
            getattr(state, 'target_context', None)
        )
        
        report = {
            "meta": {
                "version": "2.0",
                "generator": "AI_WebSecurity Report Engine",
                "generated_at": datetime.now().isoformat()
            },
            "task_id": state.task_id,
            "target": state.target,
            "scan_time": datetime.now().isoformat(),
            "duration": self._calculate_duration(state),
            "status": "completed" if state.is_complete else "failed",
            "progress": state.get_progress(),
            
            "tasks": {
                "planned": state.planned_tasks,
                "completed": state.completed_tasks,
                "total": len(state.planned_tasks) + len(state.completed_tasks)
            },
            
            "target_context": state.target_context,
            
            "vulnerabilities": {
                "list": state.vulnerabilities,
                "total": len(state.vulnerabilities),
                "summary": self._generate_vuln_summary(state.vulnerabilities),
                "by_severity": risk_assessment.get("severity_counts", {}),
                "deduplication_policy": "Disabled (All findings reported)"
            },
            
            "risk_assessment": risk_assessment,
            
            "tool_results": self._summarize_tool_results(state.tool_results),
            
            "errors": state.errors,
            
            "execution_history": state.execution_history,
            
            "recommendations": self._generate_recommendations(state.vulnerabilities)
        }
        
        logger.info(f"📄 扫描报告生成完成: {report['task_id']}")
        return report
    
    def generate_html_report(self, state: Any) -> str:
        """
        生成HTML格式报告
        
        Args:
            state: Agent状态
            
        Returns:
            str: HTML报告
        """
        report_data = self.generate_report(state)
        risk = report_data["risk_assessment"]
        
        header = self._render_html_header(state, report_data)
        risk_section = self._render_html_risk_section(risk)
        summary = self._render_html_summary(report_data)
        exec_summary = self._render_html_executive_summary(report_data)
        target_info = self._render_html_target_info(state)
        vulns = self._render_html_vulnerabilities(state.vulnerabilities)
        recommendations = self._render_html_recommendations(report_data["recommendations"])
        awvs = self._render_html_awvs_section(state)
        footer = self._render_html_footer(report_data)
        
        template = template_cache.get_template(self.html_template)
        
        html = template.safe_substitute(
            report_title=f"安全扫描报告 - {state.target}",
            header_section=header,
            risk_section=risk_section,
            summary_section=summary,
            executive_summary_section=exec_summary,
            target_info_section=target_info,
            vulnerabilities_section=vulns,
            recommendations_section=recommendations,
            awvs_section=awvs,
            footer_section=footer
        )
        
        return html
    
    def _render_html_header(self, state: Any, report_data: Dict) -> str:
        """渲染HTML头部"""
        return f"""
        <div class="header">
            <h1>🔒 安全扫描报告</h1>
            <div class="meta">
                <p>目标: {state.target}</p>
                <p>任务ID: {state.task_id}</p>
                <p>扫描时间: {report_data['scan_time']}</p>
                <p>状态: {report_data['status']}</p>
            </div>
        </div>
        """
    
    def _render_html_risk_section(self, risk: Dict) -> str:
        """渲染风险评估部分"""
        score = risk["score"]
        color = risk["color"]
        label = risk["label"]
        factors = risk.get("factors", [])
        
        stroke_dash = score * 5.03
        
        factors_html = ""
        for f in factors:
            factors_html += f'<div class="risk-factor">• {f["description"]}</div>'
        
        return f"""
        <div class="risk-gauge">
            <h2>📊 风险评估</h2>
            <div class="gauge-container">
                <div class="gauge">
                    <svg viewBox="0 0 200 200">
                        <circle cx="100" cy="100" r="80" fill="none" stroke="#eee" stroke-width="20"/>
                        <circle cx="100" cy="100" r="80" fill="none" stroke="{color}" stroke-width="20"
                            stroke-dasharray="{stroke_dash} 503"
                            stroke-linecap="round" transform="rotate(-90 100 100)"/>
                    </svg>
                    <div class="gauge-value" style="color: {color};">{score}</div>
                </div>
                <div class="risk-details">
                    <div class="risk-level" style="color: {color};">风险等级: {label}</div>
                    <p>综合风险评分基于漏洞数量、严重程度、可利用性和影响程度计算得出。</p>
                    <p>建议优先处理高危和严重级别的漏洞。</p>
                    {f'<div class="risk-factors">{factors_html}</div>' if factors_html else ''}
                </div>
            </div>
        </div>
        """
    
    def _render_html_summary(self, report_data: Dict) -> str:
        """渲染漏洞统计卡片"""
        summary = report_data["vulnerabilities"]["by_severity"]
        
        cards = ""
        for severity, config in [("critical", SEVERITY_CONFIG["critical"]), 
                                  ("high", SEVERITY_CONFIG["high"]),
                                  ("medium", SEVERITY_CONFIG["medium"]),
                                  ("low", SEVERITY_CONFIG["low"]),
                                  ("info", SEVERITY_CONFIG["info"])]:
            count = summary.get(severity, 0)
            cards += f"""
            <div class="card" style="border-top: 4px solid {config['color']};">
                <div class="label">{config['label']}</div>
                <div class="count" style="color: {config['color']};">{count}</div>
            </div>
            """
        
        return f'<div class="summary-cards">{cards}</div>'
    
    def _render_html_executive_summary(self, report_data: Dict) -> str:
        """渲染执行摘要"""
        summary = report_data["vulnerabilities"]["summary"]
        risk = report_data["risk_assessment"]
        
        return f"""
        <div class="section">
            <h2>📋 执行摘要</h2>
            <p>{summary}</p>
            <p>风险评分: {risk['score']} 分，风险等级: {risk['label']}。</p>
        </div>
        """
    
    def _render_html_target_info(self, state: Any) -> str:
        """渲染目标信息"""
        context = state.target_context or {}
        
        rows = ""
        for key, value in context.items():
            if value:
                display_value = ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)
                rows += f"<tr><th>{key}</th><td>{display_value}</td></tr>"
        
        if not rows:
            rows = "<tr><th>目标</th><td>{state.target}</td></tr>"
        
        return f"""
        <div class="section target-info">
            <h2>🖥️ 目标信息</h2>
            <table>
                {rows}
            </table>
        </div>
        """
    
    def _render_html_vulnerabilities(self, vulnerabilities: List[Dict]) -> str:
        """渲染漏洞详情"""
        if not vulnerabilities:
            return '<div class="section"><h2>🔍 漏洞详情</h2><p>未发现漏洞</p></div>'
        
        severity_order = {s: c["order"] for s, c in SEVERITY_CONFIG.items()}
        sorted_vulns = sorted(vulnerabilities, key=lambda v: severity_order.get(v.get("severity", "info"), 4))
        
        vuln_items = ""
        for vuln in sorted_vulns:
            severity = vuln.get("severity", "info")
            config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["info"])
            
            vuln_items += f"""
            <div class="vuln-item" style="border-left: 5px solid {config['color']};">
                <div class="vuln-header">
                    <span class="vuln-title">{vuln.get('title', vuln.get('cve', '未知漏洞'))}</span>
                    <span class="vuln-severity" style="background: {config['color']};">{config['label']}</span>
                </div>
                <div class="vuln-meta">
                    <span>类型: {vuln.get('vuln_type', 'N/A')}</span> | 
                    <span>URL: {vuln.get('url', 'N/A')}</span>
                </div>
                <div class="vuln-description">{vuln.get('description', vuln.get('details', '无详细描述'))}</div>
                {f'<div class="vuln-remediation"><h4>修复建议</h4><p>{vuln.get("remediation", "暂无修复建议")}</p></div>' if vuln.get('remediation') else ''}
            </div>
            """
        
        return f'<div class="section"><h2>🔍 漏洞详情</h2>{vuln_items}</div>'
    
    def _render_html_recommendations(self, recommendations: List[Dict]) -> str:
        """渲染修复建议"""
        if not recommendations:
            return '<div class="section"><h2>💡 修复建议</h2><p>暂无具体修复建议。</p></div>'
        
        items = ""
        for rec in recommendations:
            items += f"<li><strong>{rec['vulnerability']}</strong> ({rec['severity']}): {rec['recommendation']}</li>"
        
        return f"""
        <div class="section">
            <h2>💡 修复建议</h2>
            <div class="recommendations">
                <ul>{items}</ul>
            </div>
        </div>
        """
    
    def _render_html_awvs_section(self, state: Any) -> str:
        """渲染AWVS集成部分"""
        awvs_data = getattr(state, 'awvs_data', None)
        if not awvs_data:
            return ""
        
        vulns = awvs_data.get('vulnerabilities', [])
        if not vulns:
            return ""
        
        items = ""
        for v in vulns[:5]:
            items += f"<li>{v.get('vt_name', 'Unknown')} - {v.get('affects_url', 'N/A')}</li>"
        
        return f"""
        <div class="awvs-section">
            <h3>🔧 AWVS扫描集成</h3>
            <p>共发现 {len(vulns)} 个AWVS漏洞</p>
            <ul>{items}</ul>
        </div>
        """
    
    def _render_html_footer(self, report_data: Dict) -> str:
        """渲染页脚"""
        return f"""
        <div class="footer">
            <p>报告由 AI_WebSecurity 自动生成 | 生成时间: {report_data['scan_time']}</p>
        </div>
        """
    
    def generate_markdown_report(self, state: Any) -> str:
        """
        生成Markdown格式报告
        
        Args:
            state: Agent状态
            
        Returns:
            str: Markdown报告
        """
        report_data = self.generate_report(state)
        risk = report_data["risk_assessment"]
        
        basic_info = f"""
- **目标**: {state.target}
- **任务ID**: {state.task_id}
- **扫描时间**: {report_data['scan_time']}
- **状态**: {report_data['status']}
"""
        
        risk_assessment = f"""
- **风险评分**: {risk['score']}
- **风险等级**: {risk['label']}
"""
        
        severity_counts = report_data["vulnerabilities"]["by_severity"]
        vuln_stats = """
| 严重程度 | 数量 |
|---------|------|
"""
        for severity, config in [("critical", SEVERITY_CONFIG["critical"]), 
                                  ("high", SEVERITY_CONFIG["high"]),
                                  ("medium", SEVERITY_CONFIG["medium"]),
                                  ("low", SEVERITY_CONFIG["low"]),
                                  ("info", SEVERITY_CONFIG["info"])]:
            vuln_stats += f"| {config['label']} | {severity_counts.get(severity, 0)} |\n"
        
        exec_summary = report_data["vulnerabilities"]["summary"]
        
        target_info = ""
        for key, value in (state.target_context or {}).items():
            if value:
                target_info += f"- **{key}**: {value}\n"
        
        vulns_md = ""
        severity_order = {s: c["order"] for s, c in SEVERITY_CONFIG.items()}
        sorted_vulns = sorted(state.vulnerabilities, key=lambda v: severity_order.get(v.get("severity", "info"), 4))
        
        for vuln in sorted_vulns:
            severity = vuln.get("severity", "info")
            config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["info"])
            vulns_md += f"""
### {vuln.get('title', vuln.get('cve', '未知漏洞'))}

- **严重程度**: {config['label']}
- **类型**: {vuln.get('vuln_type', 'N/A')}
- **URL**: {vuln.get('url', 'N/A')}
- **描述**: {vuln.get('description', vuln.get('details', '无详细描述'))}
- **修复建议**: {vuln.get('remediation', '暂无修复建议')}

---
"""
        
        recommendations = ""
        for rec in report_data["recommendations"]:
            recommendations += f"- **{rec['vulnerability']}** ({rec['severity']}): {rec['recommendation']}\n"
        
        awvs_section = ""
        awvs_data = getattr(state, 'awvs_data', None)
        if awvs_data:
            awvs_section = f"\n## AWVS扫描结果\n\n共发现 {len(awvs_data.get('vulnerabilities', []))} 个漏洞。\n"
        
        template = template_cache.get_template(self.md_template)
        
        md = template.safe_substitute(
            report_title=f"安全扫描报告 - {state.target}",
            basic_info=basic_info,
            risk_assessment=risk_assessment,
            vuln_statistics=vuln_stats,
            executive_summary=exec_summary,
            target_info=target_info,
            vulnerabilities=vulns_md,
            recommendations=recommendations,
            awvs_section=awvs_section,
            generated_at=report_data['scan_time']
        )
        
        return md
    
    def generate_json_report(self, state: Any) -> str:
        """
        生成JSON格式报告
        
        Args:
            state: Agent状态
            
        Returns:
            str: JSON报告
        """
        report_data = self.generate_report(state)
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def generate_report_by_format(self, state: Any, format: str = "json") -> str:
        """
        根据格式生成报告
        
        Args:
            state: Agent状态
            format: 报告格式 (json, html, markdown, pdf)
            
        Returns:
            str: 报告内容
        """
        format = format.lower()
        
        generators = {
            "json": self.generate_json_report,
            "html": self.generate_html_report,
            "markdown": self.generate_markdown_report,
            "pdf": self.generate_html_report
        }
        
        generator = generators.get(format, self.generate_json_report)
        return generator(state)
    
    def _calculate_duration(self, state: Any) -> float:
        """
        计算扫描持续时间
        
        Args:
            state: Agent状态
            
        Returns:
            float: 持续时间(秒)
        """
        if not state.execution_history:
            return 0.0
        
        start_time = state.execution_history[0].get("timestamp", 0)
        end_time = state.execution_history[-1].get("timestamp", 0)
        
        if start_time is None or end_time is None:
            return 0.0
        
        try:
            return float(end_time) - float(start_time)
        except (TypeError, ValueError):
            return 0.0
    
    def _generate_vuln_summary(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """
        生成漏洞摘要
        
        Args:
            vulnerabilities: 漏洞列表
            
        Returns:
            str: 摘要文本
        """
        if not vulnerabilities:
            return "未发现漏洞"
        
        severity_count = {}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info")
            severity_count[severity] = severity_count.get(severity, 0) + 1
        
        parts = []
        for severity in ["critical", "high", "medium", "low"]:
            count = severity_count.get(severity, 0)
            if count > 0:
                config = SEVERITY_CONFIG.get(severity, {})
                parts.append(f"{config.get('label', severity)}: {count}")
        
        return "共发现 {} 个漏洞: {}".format(
            len(vulnerabilities),
            ", ".join(parts)
        )
    
    def _generate_recommendations(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """生成修复建议列表"""
        recommendations = []
        
        severity_order = {s: c["order"] for s, c in SEVERITY_CONFIG.items()}
        sorted_vulns = sorted(vulnerabilities, key=lambda v: severity_order.get(v.get("severity", "info"), 4))
        
        for vuln in sorted_vulns[:10]:
            if vuln.get("remediation"):
                recommendations.append({
                    "vulnerability": vuln.get("title", vuln.get("cve", "未知漏洞")),
                    "severity": vuln.get("severity", "info"),
                    "recommendation": vuln.get("remediation")
                })
        
        return recommendations
    
    def _summarize_tool_results(self, tool_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        汇总工具结果
        
        Args:
            tool_results: 工具结果字典
            
        Returns:
            Dict: 汇总结果
        """
        summary = {
            "total": len(tool_results),
            "success": 0,
            "failed": 0,
            "timeout": 0,
            "details": {}
        }
        
        for tool_name, result in tool_results.items():
            status = result.get("status", "unknown")
            if status == "success":
                summary["success"] += 1
            elif status == "failed":
                summary["failed"] += 1
            elif status == "timeout":
                summary["timeout"] += 1
            
            summary["details"][tool_name] = {
                "status": status,
                "has_data": "data" in result,
                "summary": self._get_tool_summary(tool_name, result)
            }
        
        return summary
    
    def _get_tool_summary(self, tool_name: str, result: Dict[str, Any]) -> str:
        """获取工具执行结果摘要"""
        if not result:
            return "无结果"
            
        status = result.get("status")
        if status != "success":
            return result.get("error", "执行失败")
        
        data = result.get("data", {})
        if not data:
            return "无数据"

        if tool_name == "baseinfo":
            details = []
            if isinstance(data, dict):
                if data.get("domain"): details.append(f"域名: {data['domain']}")
                if data.get("ip"): details.append(f"IP: {data['ip']}")
                if data.get("server"): details.append(f"Server: {data['server']}")
                if data.get("os"): details.append(f"OS: {data['os']}")
            return ", ".join(details) if details else "获取基础信息成功"
        
        elif tool_name == "portscan":
            ports = data.get("open_ports", [])
            if not ports:
                return "未发现开放端口"
            return f"开放端口: {', '.join(str(p) for p in ports)}"
            
        elif tool_name == "waf_detect":
            has_waf = data.get("has_waf")
            if has_waf == "yes":
                return f"发现WAF: {data.get('waf_name', 'Unknown')}"
            return "未发现WAF"
            
        elif tool_name == "cdn_detect":
            has_cdn = data.get("has_cdn")
            if has_cdn:
                return f"发现CDN: {data.get('cdn_info', 'Unknown')}"
            return "未发现CDN"
            
        elif tool_name == "cms_identify":
            inner_data = data.get("data", {}) if isinstance(data, dict) else {}
            if not inner_data:
                return data.get("message", "未识别到CMS")
            
            apps = inner_data.get("apps", [])
            if apps:
                 app_names = [app.get("name") for app in apps if app.get("name")]
                 return f"识别组件: {', '.join(app_names)}"
            return "未识别到CMS"

        return "执行完成"
    
    def generate_execution_trace_report(self, state: Any) -> Dict[str, Any]:
        """
        生成详细的执行轨迹报告
        
        Args:
            state: Agent状态
            
        Returns:
            Dict: 执行轨迹报告
        """
        try:
            trace_report = {
                "task_id": state.task_id,
                "target": state.target,
                "scan_time": datetime.now().isoformat(),
                "total_steps": len(state.execution_history),
                "total_duration": self._calculate_duration(state),
                "execution_trace": self._generate_detailed_trace(state.execution_history) if state.execution_history else [],
                "trace_summary": self._generate_trace_summary(state.execution_history) if state.execution_history else self._empty_trace_summary(),
                "state_changes": self._generate_state_changes(state.execution_history) if state.execution_history else [],
                "performance_metrics": self._generate_performance_metrics(state.execution_history) if state.execution_history else self._empty_performance_metrics()
            }
            
            logger.info(f"📄 执行轨迹报告生成完成: {trace_report['task_id']}")
            return trace_report
        except Exception as e:
            logger.error(f"生成执行轨迹报告失败: {str(e)}")
            return self._empty_trace_report(state)
    
    def _empty_trace_summary(self) -> Dict:
        """返回空的轨迹摘要"""
        return {
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "running_steps": 0,
            "pending_steps": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0
        }
    
    def _empty_performance_metrics(self) -> Dict:
        """返回空的性能指标"""
        return {
            "throughput": 0.0,
            "success_rate": 0.0,
            "failure_rate": 0.0,
            "steps_per_second": 0.0,
            "average_step_duration": 0.0
        }
    
    def _empty_trace_report(self, state: Any) -> Dict:
        """返回空的轨迹报告"""
        return {
            "task_id": getattr(state, 'task_id', 'unknown'),
            "target": getattr(state, 'target', 'unknown'),
            "scan_time": datetime.now().isoformat(),
            "total_steps": 0,
            "total_duration": 0.0,
            "execution_trace": [],
            "trace_summary": self._empty_trace_summary(),
            "state_changes": [],
            "performance_metrics": self._empty_performance_metrics()
        }
    
    def _generate_detailed_trace(self, execution_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成详细的执行轨迹"""
        detailed_trace = []
        
        for step in execution_history:
            trace_entry = {
                "step_number": step.get("step_number", 0),
                "timestamp": step.get("timestamp_iso", ""),
                "task": step.get("task", ""),
                "step_type": step.get("step_type", "unknown"),
                "status": step.get("status", "unknown"),
                "execution_time": step.get("execution_time", 0),
                "input_parameters": step.get("input_params", {}),
                "processing_logic": step.get("processing_logic", ""),
                "intermediate_results": step.get("intermediate_results", []),
                "output_data": step.get("output_data", {}),
                "final_result": step.get("result", {}),
                "data_changes": step.get("data_changes", {}),
                "state_transitions": step.get("state_transitions", []),
                "state_snapshot": step.get("state_snapshot", {})
            }
            
            detailed_trace.append(trace_entry)
        
        return detailed_trace
    
    def _generate_trace_summary(self, execution_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成轨迹摘要"""
        summary = {
            "total_steps": len(execution_history),
            "successful_steps": 0,
            "failed_steps": 0,
            "running_steps": 0,
            "pending_steps": 0,
            "step_types": {},
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "min_execution_time": float('inf'),
            "max_execution_time": 0.0
        }
        
        execution_times = []
        
        for step in execution_history:
            status = step.get("status", "unknown")
            
            if status == "success":
                summary["successful_steps"] += 1
            elif status == "failed":
                summary["failed_steps"] += 1
            elif status == "running":
                summary["running_steps"] += 1
            elif status == "pending":
                summary["pending_steps"] += 1
            
            step_type = step.get("step_type", "unknown")
            summary["step_types"][step_type] = summary["step_types"].get(step_type, 0) + 1
            
            execution_time = step.get("execution_time")
            if execution_time is not None and execution_time > 0:
                execution_times.append(execution_time)
                summary["total_execution_time"] += execution_time
                summary["min_execution_time"] = min(summary["min_execution_time"], execution_time)
                summary["max_execution_time"] = max(summary["max_execution_time"], execution_time)
        
        if execution_times:
            summary["average_execution_time"] = summary["total_execution_time"] / len(execution_times)
        else:
            summary["min_execution_time"] = 0.0
        
        return summary
    
    def _generate_state_changes(self, execution_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成状态变化记录"""
        state_changes = []
        
        for step in execution_history:
            step_number = step.get("step_number", 0)
            task = step.get("task", "")
            timestamp = step.get("timestamp_iso", "")
            data_changes = step.get("data_changes", {})
            state_transitions = step.get("state_transitions", [])
            state_snapshot = step.get("state_snapshot", {})
            
            if data_changes or state_transitions:
                change_entry = {
                    "step_number": step_number,
                    "task": task,
                    "timestamp": timestamp,
                    "data_changes": data_changes,
                    "state_transitions": state_transitions,
                    "state_snapshot": state_snapshot
                }
                state_changes.append(change_entry)
        
        return state_changes
    
    def _generate_performance_metrics(self, execution_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成性能指标"""
        metrics = {
            "throughput": 0.0,
            "success_rate": 0.0,
            "failure_rate": 0.0,
            "steps_per_second": 0.0,
            "average_step_duration": 0.0
        }
        
        if not execution_history:
            return metrics
        
        total_steps = len(execution_history)
        successful_steps = sum(1 for step in execution_history if step.get("status") == "success")
        
        metrics["success_rate"] = (successful_steps / total_steps * 100) if total_steps > 0 else 0.0
        metrics["failure_rate"] = 100.0 - metrics["success_rate"]
        
        total_time = self._calculate_total_time(execution_history)
        
        if total_time > 0:
            metrics["steps_per_second"] = total_steps / total_time
            metrics["throughput"] = successful_steps / total_time
        
        execution_times = [step.get("execution_time", 0) for step in execution_history if step.get("execution_time") is not None and step.get("execution_time", 0) > 0]
        if execution_times:
            metrics["average_step_duration"] = sum(execution_times) / len(execution_times)
        
        return metrics
    
    def _calculate_total_time(self, execution_history: List[Dict[str, Any]]) -> float:
        """计算总执行时间"""
        if not execution_history:
            return 0.0
        
        start_time = execution_history[0].get("timestamp", 0)
        end_time = execution_history[-1].get("timestamp", 0)
        
        if start_time is None or end_time is None:
            return 0.0
        
        try:
            return float(end_time) - float(start_time)
        except (TypeError, ValueError):
            return 0.0
    
    def generate_html_execution_trace(self, state: Any) -> str:
        """
        生成HTML格式的执行轨迹报告
        
        Args:
            state: Agent状态
            
        Returns:
            str: HTML执行轨迹报告
        """
        try:
            trace_report = self.generate_execution_trace_report(state)
        except Exception as e:
            logger.error(f"生成执行轨迹报告失败: {str(e)}")
            trace_report = self._empty_trace_report(state)
        
        total_duration = trace_report.get('total_duration', 0.0) or 0.0
        total_steps = trace_report.get('total_steps', 0) or 0
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent执行轨迹报告 - {state.target}</title>
    <style>
        body {{ font-family: 'Courier New', monospace; line-height: 1.6; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0 0 10px 0; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{ color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
        .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
        .card h3 {{ margin: 0 0 10px 0; color: #667eea; font-size: 14px; }}
        .card .value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .trace-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 12px; }}
        .trace-table th {{ background: #667eea; color: white; padding: 12px; text-align: left; font-weight: bold; }}
        .trace-table td {{ padding: 10px; border-bottom: 1px solid #ddd; vertical-align: top; }}
        .trace-table tr:hover {{ background: #f5f5f5; }}
        .status-success {{ color: #28a745; font-weight: bold; }}
        .status-failed {{ color: #dc3545; font-weight: bold; }}
        .status-running {{ color: #ffc107; font-weight: bold; }}
        .step-type {{ padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        .type-tool {{ background: #e3f2fd; color: #1976d2; }}
        .type-code {{ background: #fce4ec; color: #c2185b; }}
        .type-execution {{ background: #fff3e0; color: #f57c00; }}
        .type-enhancement {{ background: #e8f5e9; color: #388e3c; }}
        .type-verification {{ background: #f3e5f5; color: #7b1fa2; }}
        .type-analysis {{ background: #ffebee; color: #d32f2f; }}
        .json-display {{ background: #f5f5f5; padding: 10px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 11px; max-height: 200px; overflow-y: auto; }}
        .timestamp {{ color: #666; font-size: 11px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Agent执行轨迹报告</h1>
            <p><strong>目标:</strong> {state.target}</p>
            <p><strong>任务ID:</strong> {state.task_id}</p>
            <p><strong>扫描时间:</strong> {trace_report['scan_time']}</p>
            <p><strong>总步骤:</strong> {total_steps}</p>
            <p><strong>总耗时:</strong> {total_duration:.2f}秒</p>
        </div>
        
        <div class="section">
            <h2>📊 执行摘要</h2>
            <div class="summary-cards">
                <div class="card">
                    <h3>总步骤</h3>
                    <div class="value">{trace_report['trace_summary']['total_steps']}</div>
                </div>
                <div class="card">
                    <h3>成功步骤</h3>
                    <div class="value status-success">{trace_report['trace_summary']['successful_steps']}</div>
                </div>
                <div class="card">
                    <h3>失败步骤</h3>
                    <div class="value status-failed">{trace_report['trace_summary']['failed_steps']}</div>
                </div>
                <div class="card">
                    <h3>总耗时</h3>
                    <div class="value">{trace_report['trace_summary']['total_execution_time'] or 0:.2f}s</div>
                </div>
                <div class="card">
                    <h3>平均耗时</h3>
                    <div class="value">{trace_report['trace_summary']['average_execution_time'] or 0:.2f}s</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 性能指标</h2>
            <table class="trace-table">
                <tr><th>指标</th><th>值</th></tr>
                <tr><td>成功率</td><td>{trace_report['performance_metrics']['success_rate'] or 0:.2f}%</td></tr>
                <tr><td>失败率</td><td>{trace_report['performance_metrics']['failure_rate'] or 0:.2f}%</td></tr>
                <tr><td>吞吐量（成功步骤/秒）</td><td>{trace_report['performance_metrics']['throughput'] or 0:.4f}</td></tr>
                <tr><td>步骤/秒</td><td>{trace_report['performance_metrics']['steps_per_second'] or 0:.4f}</td></tr>
                <tr><td>平均步骤持续时间</td><td>{trace_report['performance_metrics']['average_step_duration'] or 0:.2f}s</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>📋 详细执行轨迹</h2>
            {self._generate_trace_table(trace_report['execution_trace'])}
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def _generate_trace_table(self, execution_trace: List[Dict[str, Any]]) -> str:
        """生成轨迹表格"""
        if not execution_trace:
            return "<p>无执行轨迹记录</p>"
        
        rows = ""
        for step in execution_trace:
            step_number = step.get("step_number", 0)
            timestamp = step.get("timestamp", "")
            task = step.get("task", "")
            step_type = step.get("step_type", "unknown")
            status = step.get("status", "unknown")
            execution_time = step.get("execution_time") or 0
            
            status_class = {
                "success": "status-success",
                "failed": "status-failed",
                "running": "status-running"
            }.get(status, "")
            
            type_class = {
                "tool_execution": "type-tool",
                "code_generation": "type-code",
                "code_execution": "type-execution",
                "capability_enhancement": "type-enhancement",
                "verification": "type-verification",
                "analysis": "type-analysis"
            }.get(step_type, "")
            
            rows += f"""
                <tr>
                    <td>{step_number}</td>
                    <td class="timestamp">{timestamp}</td>
                    <td>{task}</td>
                    <td><span class="step-type {type_class}">{step_type}</span></td>
                    <td class="{status_class}">{status.upper()}</td>
                    <td>{execution_time:.2f}s</td>
                </tr>
            """
        
        return f"""
        <table class="trace-table">
            <thead>
                <tr>
                    <th>步骤</th>
                    <th>时间戳</th>
                    <th>任务</th>
                    <th>类型</th>
                    <th>状态</th>
                    <th>耗时</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

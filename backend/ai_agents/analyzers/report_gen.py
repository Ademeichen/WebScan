"""
报告生成器

生成标准化的扫描报告。
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from ..config import agent_config

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    报告生成器
    
    负责生成标准化的扫描报告。
    """
    
    def __init__(self):
        logger.info("📄 报告生成器初始化完成")
    
    def generate_report(self, state: Any) -> Dict[str, Any]:
        """
        生成扫描报告
        
        Args:
            state: Agent状态
            
        Returns:
            Dict: 扫描报告
        """
        report = {
            "task_id": state.task_id,
            "target": state.target,
            "scan_time": datetime.now().isoformat(),
            "duration": self._calculate_duration(state),
            "status": "completed" if state.is_complete else "failed",
            "progress": state.get_progress(),
            
            # 任务信息
            "tasks": {
                "planned": state.planned_tasks,
                "completed": state.completed_tasks,
                "total": len(state.planned_tasks) + len(state.completed_tasks)
            },
            
            # 目标上下文
            "target_context": state.target_context,
            
            # 漏洞信息
            "vulnerabilities": {
                "list": state.vulnerabilities,
                "total": len(state.vulnerabilities),
                "summary": self._generate_vuln_summary(state.vulnerabilities)
            },
            
            # 工具结果
            "tool_results": self._summarize_tool_results(state.tool_results),
            
            # 错误信息
            "errors": state.errors,
            
            # 执行历史
            "execution_history": state.execution_history
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
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web安全扫描报告 - {state.target}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .vulnerability {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .vulnerability.critical {{ border-left: 5px solid #dc3545; }}
        .vulnerability.high {{ border-left: 5px solid #fd7e14; }}
        .vulnerability.medium {{ border-left: 5px solid #ffc107; }}
        .vulnerability.low {{ border-left: 5px solid #28a745; }}
        .severity {{ font-weight: bold; text-transform: uppercase; }}
        .summary {{ background: #e9ecef; padding: 15px; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        table th, table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        table th {{ background: #007bff; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Web安全扫描报告</h1>
        <p><strong>目标:</strong> {state.target}</p>
        <p><strong>扫描时间:</strong> {report_data['scan_time']}</p>
        <p><strong>任务ID:</strong> {state.task_id}</p>
        <p><strong>状态:</strong> {report_data['status']}</p>
    </div>
    
    <div class="section">
        <h2>扫描摘要</h2>
        <div class="summary">
            <p>{report_data['vulnerabilities']['summary']}</p>
            <p><strong>任务进度:</strong> {report_data['progress']:.1f}%</p>
            <p><strong>已完成任务:</strong> {len(report_data['tasks']['completed'])}/{report_data['tasks']['total']}</p>
        </div>
    </div>
    
    <div class="section">
        <h2>目标信息</h2>
        <table>
            <tr><th>项目</th><th>信息</th></tr>
            {self._generate_context_rows(state.target_context)}
        </table>
    </div>
    
    <div class="section">
        <h2>漏洞详情</h2>
        {self._generate_vuln_rows(state.vulnerabilities)}
    </div>
    
    <div class="section">
        <h2>工具执行结果</h2>
        {self._generate_tool_rows(state.tool_results)}
    </div>
    
    {self._generate_error_section(state.errors)}
</body>
</html>
        """
        
        return html
    
    def _calculate_duration(self, state: Any) -> float:
        """
        计算扫描持续时间
        
        Args:
            state: Agent状态
            
        Returns:
            float: 持续时间（秒）
        """
        if not state.execution_history:
            return 0.0
        
        start_time = state.execution_history[0].get("timestamp", 0)
        end_time = state.execution_history[-1].get("timestamp", 0)
        return end_time - start_time
    
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
                parts.append(f"{severity.capitalize()}: {count}")
        
        return "共发现 {} 个漏洞: {}".format(
            len(vulnerabilities),
            ", ".join(parts)
        )
    
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
                "has_data": "data" in result
            }
        
        return summary
    
    def _generate_context_rows(self, context: Dict[str, Any]) -> str:
        """
        生成上下文表格行
        
        Args:
            context: 上下文字典
            
        Returns:
            str: HTML表格行
        """
        rows = []
        for key, value in context.items():
            if value:
                display_value = str(value)
                if isinstance(value, list):
                    display_value = ", ".join(str(v) for v in value)
                rows.append(f"<tr><td>{key}</td><td>{display_value}</td></tr>")
        
        return "\n".join(rows)
    
    def _generate_vuln_rows(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """
        生成漏洞HTML行
        
        Args:
            vulnerabilities: 漏洞列表
            
        Returns:
            str: HTML漏洞行
        """
        if not vulnerabilities:
            return "<p>未发现漏洞</p>"
        
        rows = []
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info")
            rows.append(f"""
    <div class="vulnerability {severity}">
        <p><strong>CVE:</strong> {vuln.get('cve', 'N/A')}</p>
        <p><strong>严重度:</strong> <span class="severity">{severity}</span></p>
        <p><strong>详情:</strong> {vuln.get('details', 'N/A')}</p>
        {f"<p><strong>修复建议:</strong> {vuln.get('fix_suggestion', 'N/A')}</p>" if vuln.get('fix_suggestion') else ''}
    </div>
            """)
        
        return "\n".join(rows)
    
    def _generate_tool_rows(self, tool_results: Dict[str, Any]) -> str:
        """
        生成工具结果HTML行
        
        Args:
            tool_results: 工具结果字典
            
        Returns:
            str: HTML工具行
        """
        rows = []
        for tool_name, result in tool_results.items():
            status = result.get("status", "unknown")
            status_color = {
                "success": "#28a745",
                "failed": "#dc3545",
                "timeout": "#ffc107"
            }.get(status, "#6c757d")
            
            rows.append(f"""
    <tr>
        <td>{tool_name}</td>
        <td style="color: {status_color}; font-weight: bold;">{status.upper()}</td>
        <td>{'是' if result.get('data') else '否'}</td>
    </tr>
            """)
        
        return "\n".join(rows)
    
    def _generate_error_section(self, errors: List[str]) -> str:
        """
        生成错误部分
        
        Args:
            errors: 错误列表
            
        Returns:
            str: HTML错误部分
        """
        if not errors:
            return ""
        
        error_rows = "\n".join([f"<li>{error}</li>" for error in errors])
        return f"""
    <div class="section">
        <h2>执行错误</h2>
        <ul style="color: #dc3545;">
            {error_rows}
        </ul>
    </div>
        """

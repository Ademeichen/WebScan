"""
测试报告生成器

生成详细的测试报告，包含覆盖率、性能指标和AI优化建议。
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from jinja2 import Template
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

logger = logging.getLogger(__name__)


@dataclass
class TestMetric:
    name: str
    value: Any
    unit: str = ""
    status: str = "normal"


@dataclass
class TestCoverage:
    module: str
    total: int
    covered: int
    percentage: float


@dataclass 
class SecurityFinding:
    severity: str
    title: str
    description: str
    recommendation: str


@dataclass
class PerformanceMetric:
    endpoint: str
    avg_response_time: float
    max_response_time: float
    min_response_time: float
    success_rate: float


@dataclass
class ComprehensiveTestReport:
    title: str
    timestamp: str
    summary: Dict[str, Any]
    coverage: List[TestCoverage]
    security_findings: List[SecurityFinding]
    performance_metrics: List[PerformanceMetric]
    ai_recommendations: List[str]
    detailed_results: List[Dict[str, Any]]


class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, output_dir: str = "tests/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_from_pytest_results(
        self,
        pytest_output: str,
        test_results: List[Dict[str, Any]]
    ) -> ComprehensiveTestReport:
        """从pytest结果生成报告"""
        
        total = len(test_results)
        passed = sum(1 for r in test_results if r.get("status") == "passed")
        failed = sum(1 for r in test_results if r.get("status") == "failed")
        skipped = sum(1 for r in test_results if r.get("status") == "skipped")
        
        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "execution_time": sum(r.get("duration", 0) for r in test_results)
        }
        
        coverage = self._calculate_coverage(test_results)
        security = self._extract_security_findings(test_results)
        performance = self._calculate_performance_metrics(test_results)
        recommendations = self._generate_ai_recommendations(summary, security, performance)
        
        return ComprehensiveTestReport(
            title="AI WebSecurity 测试报告",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary=summary,
            coverage=coverage,
            security_findings=security,
            performance_metrics=performance,
            ai_recommendations=recommendations,
            detailed_results=test_results
        )
    
    def _calculate_coverage(self, results: List[Dict]) -> List[TestCoverage]:
        """计算测试覆盖率"""
        module_counts: Dict[str, Dict[str, int]] = {}
        
        for result in results:
            module = result.get("module", "unknown")
            if module not in module_counts:
                module_counts[module] = {"total": 0, "covered": 0}
            
            module_counts[module]["total"] += 1
            if result.get("status") == "passed":
                module_counts[module]["covered"] += 1
        
        coverage = []
        for module, counts in module_counts.items():
            percentage = (counts["covered"] / counts["total"] * 100) if counts["total"] > 0 else 0
            coverage.append(TestCoverage(
                module=module,
                total=counts["total"],
                covered=counts["covered"],
                percentage=round(percentage, 2)
            ))
        
        return coverage
    
    def _extract_security_findings(self, results: List[Dict]) -> List[SecurityFinding]:
        """提取安全发现"""
        findings = []
        
        for result in results:
            if result.get("security_findings"):
                for finding in result["security_findings"]:
                    findings.append(SecurityFinding(
                        severity=finding.get("severity", "info"),
                        title=finding.get("title", ""),
                        description=finding.get("description", ""),
                        recommendation=finding.get("recommendation", "")
                    ))
        
        return findings
    
    def _calculate_performance_metrics(self, results: List[Dict]) -> List[PerformanceMetric]:
        """计算性能指标"""
        endpoint_times: Dict[str, List[float]] = {}
        endpoint_status: Dict[str, Dict[str, int]] = {}
        
        for result in results:
            endpoint = result.get("endpoint", result.get("name", "unknown"))
            duration = result.get("duration", 0)
            
            if endpoint not in endpoint_times:
                endpoint_times[endpoint] = []
                endpoint_status[endpoint] = {"success": 0, "total": 0}
            
            endpoint_times[endpoint].append(duration)
            endpoint_status[endpoint]["total"] += 1
            if result.get("status") == "passed":
                endpoint_status[endpoint]["success"] += 1
        
        metrics = []
        for endpoint, times in endpoint_times.items():
            if times:
                metrics.append(PerformanceMetric(
                    endpoint=endpoint,
                    avg_response_time=round(sum(times) / len(times), 3),
                    max_response_time=round(max(times), 3),
                    min_response_time=round(min(times), 3),
                    success_rate=round(
                        endpoint_status[endpoint]["success"] / endpoint_status[endpoint]["total"] * 100, 2
                    )
                ))
        
        return metrics
    
    def _generate_ai_recommendations(
        self,
        summary: Dict,
        security: List,
        performance: List
    ) -> List[str]:
        """生成AI优化建议"""
        recommendations = []
        
        pass_rate = summary.get("pass_rate", 0)
        if pass_rate < 80:
            recommendations.append(f"⚠️ 测试通过率({pass_rate:.1f}%)较低，建议检查失败用例并修复相关问题")
        elif pass_rate < 95:
            recommendations.append(f"✅ 测试通过率({pass_rate:.1f}%)良好，建议继续优化剩余失败用例")
        else:
            recommendations.append(f"🎉 测试通过率({pass_rate:.1f}%)优秀，系统运行稳定")
        
        failed = summary.get("failed", 0)
        if failed > 0:
            recommendations.append(f"🔍 发现{failed}个失败用例，建议优先处理高优先级功能的测试失败")
        
        skipped = summary.get("skipped", 0)
        if skipped > summary.get("total", 0) * 0.1:
            recommendations.append(f"⏭ 跳过测试较多({skipped}个)，建议检查超时配置或网络连接")
        
        if security:
            critical = sum(1 for s in security if s.severity == "critical")
            high = sum(1 for s in security if s.severity == "high")
            if critical > 0:
                recommendations.append(f"🚨 发现{critical}个严重安全漏洞，建议立即修复")
            if high > 0:
                recommendations.append(f"⚠️ 发现{high}个高危安全漏洞，建议尽快处理")
        
        slow_endpoints = [p for p in performance if p.avg_response_time > 5]
        if slow_endpoints:
            recommendations.append(f"🐌 {len(slow_endpoints)}个接口响应时间超过5秒，建议优化性能")
        
        if not recommendations:
            recommendations.append("✨ 系统运行良好，所有指标正常，建议保持当前配置")
        
        return recommendations
    
    def generate_html_report(self, report: ComprehensiveTestReport) -> str:
        """生成HTML报告"""
        template = Template(HTML_TEMPLATE)
        
        html_content = template.render(
            title=report.title,
            timestamp=report.timestamp,
            summary=report.summary,
            coverage=report.coverage,
            security_findings=report.security_findings,
            performance_metrics=report.performance_metrics,
            ai_recommendations=report.ai_recommendations,
            detailed_results=report.detailed_results
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"test_report_{timestamp}.html"
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"HTML报告已生成: {report_file}")
        return str(report_file)
    
    def generate_json_report(self, report: ComprehensiveTestReport) -> str:
        """生成JSON报告"""
        report_dict = {
            "title": report.title,
            "timestamp": report.timestamp,
            "summary": report.summary,
            "coverage": [asdict(c) for c in report.coverage],
            "security_findings": [asdict(s) for s in report.security_findings],
            "performance_metrics": [asdict(p) for p in report.performance_metrics],
            "ai_recommendations": report.ai_recommendations,
            "detailed_results": report.detailed_results
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"test_report_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON报告已生成: {report_file}")
        return str(report_file)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            padding: 20px 0;
            color: white;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }
        .stat-card {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
            border-radius: 12px;
        }
        .stat-card h3 { font-size: 2.5em; color: #333; }
        .stat-card p { color: #666; margin-top: 5px; }
        .stat-card.passed h3 { color: #10b981; }
        .stat-card.failed h3 { color: #ef4444; }
        .stat-card.skipped h3 { color: #f59e0b; }
        .progress-bar {
            height: 20px;
            background: #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 20px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981, #34d399);
            transition: width 0.5s ease;
        }
        h2 { 
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        th { background: #f5f7fa; font-weight: 600; }
        tr:hover { background: #f9fafb; }
        .badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }
        .badge-success { background: #d1fae5; color: #065f46; }
        .badge-danger { background: #fee2e2; color: #991b1b; }
        .badge-warning { background: #fef3c7; color: #92400e; }
        .recommendation {
            padding: 12px 16px;
            margin: 8px 0;
            background: #f0f9ff;
            border-left: 4px solid #3b82f6;
            border-radius: 0 8px 8px 0;
        }
        .severity-critical { color: #dc2626; font-weight: bold; }
        .severity-high { color: #ea580c; }
        .severity-medium { color: #d97706; }
        .severity-low { color: #65a30d; }
        @media (max-width: 768px) {
            .summary-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <p>生成时间: {{ timestamp }}</p>
        </div>
        
        <div class="card">
            <h2>📊 测试概览</h2>
            <div class="summary-grid">
                <div class="stat-card">
                    <h3>{{ summary.total }}</h3>
                    <p>总测试数</p>
                </div>
                <div class="stat-card passed">
                    <h3>{{ summary.passed }}</h3>
                    <p>通过</p>
                </div>
                <div class="stat-card failed">
                    <h3>{{ summary.failed }}</h3>
                    <p>失败</p>
                </div>
                <div class="stat-card skipped">
                    <h3>{{ summary.skipped }}</h3>
                    <p>跳过</p>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ summary.pass_rate }}%;"></div>
            </div>
            <p style="text-align: center; margin-top: 10px; color: #666;">
                通过率: {{ "%.1f"|format(summary.pass_rate) }}%
            </p>
        </div>
        
        {% if coverage %}
        <div class="card">
            <h2>📈 测试覆盖率</h2>
            <table>
                <thead>
                    <tr>
                        <th>模块</th>
                        <th>总数</th>
                        <th>覆盖</th>
                        <th>覆盖率</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in coverage %}
                    <tr>
                        <td>{{ item.module }}</td>
                        <td>{{ item.total }}</td>
                        <td>{{ item.covered }}</td>
                        <td>
                            <span class="badge {% if item.percentage >= 80 %}badge-success{% elif item.percentage >= 60 %}badge-warning{% else %}badge-danger{% endif %}">
                                {{ "%.1f"|format(item.percentage) }}%
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        {% if performance_metrics %}
        <div class="card">
            <h2>⚡ 性能指标</h2>
            <table>
                <thead>
                    <tr>
                        <th>接口</th>
                        <th>平均响应(s)</th>
                        <th>最大响应(s)</th>
                        <th>最小响应(s)</th>
                        <th>成功率</th>
                    </tr>
                </thead>
                <tbody>
                    {% for metric in performance_metrics %}
                    <tr>
                        <td>{{ metric.endpoint }}</td>
                        <td>{{ "%.3f"|format(metric.avg_response_time) }}</td>
                        <td>{{ "%.3f"|format(metric.max_response_time) }}</td>
                        <td>{{ "%.3f"|format(metric.min_response_time) }}</td>
                        <td>
                            <span class="badge {% if metric.success_rate >= 95 %}badge-success{% elif metric.success_rate >= 80 %}badge-warning{% else %}badge-danger{% endif %}">
                                {{ "%.1f"|format(metric.success_rate) }}%
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        {% if security_findings %}
        <div class="card">
            <h2>🔒 安全发现</h2>
            <table>
                <thead>
                    <tr>
                        <th>严重程度</th>
                        <th>标题</th>
                        <th>描述</th>
                        <th>建议</th>
                    </tr>
                </thead>
                <tbody>
                    {% for finding in security_findings %}
                    <tr>
                        <td class="severity-{{ finding.severity }}">{{ finding.severity|upper }}</td>
                        <td>{{ finding.title }}</td>
                        <td>{{ finding.description }}</td>
                        <td>{{ finding.recommendation }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        {% if ai_recommendations %}
        <div class="card">
            <h2>🤖 AI优化建议</h2>
            {% for rec in ai_recommendations %}
            <div class="recommendation">{{ rec }}</div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""


if __name__ == "__main__":
    generator = TestReportGenerator()
    
    sample_results = [
        {"name": "test_api_health", "status": "passed", "duration": 0.5, "module": "API"},
        {"name": "test_database", "status": "passed", "duration": 1.2, "module": "Database"},
        {"name": "test_security_scan", "status": "failed", "duration": 5.0, "module": "Security"},
    ]
    
    report = generator.generate_from_pytest_results("", sample_results)
    html_file = generator.generate_html_report(report)
    json_file = generator.generate_json_report(report)
    
    print(f"HTML报告: {html_file}")
    print(f"JSON报告: {json_file}")

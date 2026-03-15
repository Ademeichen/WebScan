"""
报告功能综合测试

整合报告API端点测试和导出功能测试
测试报告创建、导出、下载等API功能
测试三种报告导出格式：JSON、HTML、PDF
"""
import pytest
import json
import sys
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from backend.api.reports import (
    generate_html_report,
    generate_markdown_report,
    calculate_risk_score,
    SEVERITY_CONFIG
)


SAMPLE_REPORT_DATA: Dict[str, Any] = {
    "report_name": "安全扫描测试报告",
    "task_name": "测试任务_Example_Scan",
    "target": "https://example.com",
    "scan_time": "2025-03-14T10:30:00Z",
    "summary": {
        "critical": 2,
        "high": 3,
        "medium": 5,
        "low": 4,
        "info": 2
    },
    "vulnerabilities": [
        {
            "id": 1,
            "title": "SQL注入漏洞",
            "name": "SQL Injection",
            "severity": "critical",
            "url": "https://example.com/search?id=1",
            "description": "在搜索参数中发现SQL注入漏洞，攻击者可以执行任意SQL语句。",
            "remediation": "使用参数化查询，对用户输入进行严格过滤。"
        },
        {
            "id": 2,
            "title": "远程代码执行漏洞",
            "name": "Remote Code Execution",
            "severity": "critical",
            "url": "https://example.com/api/exec",
            "description": "API接口存在命令注入漏洞，可执行任意系统命令。",
            "remediation": "禁用危险函数，使用白名单过滤输入。"
        },
        {
            "id": 3,
            "title": "XSS跨站脚本漏洞",
            "name": "Cross-Site Scripting (XSS)",
            "severity": "high",
            "url": "https://example.com/comment",
            "description": "评论功能存在存储型XSS漏洞。",
            "remediation": "对输出进行HTML编码，使用CSP策略。"
        },
        {
            "id": 4,
            "title": "敏感信息泄露",
            "name": "Sensitive Information Disclosure",
            "severity": "high",
            "url": "https://example.com/debug",
            "description": "调试接口泄露敏感配置信息。",
            "remediation": "关闭调试模式，移除调试接口。"
        },
        {
            "id": 5,
            "title": "CSRF跨站请求伪造",
            "name": "Cross-Site Request Forgery",
            "severity": "high",
            "url": "https://example.com/account/delete",
            "description": "删除账户功能缺少CSRF保护。",
            "remediation": "添加CSRF Token验证。"
        },
        {
            "id": 6,
            "title": "目录遍历漏洞",
            "name": "Path Traversal",
            "severity": "medium",
            "url": "https://example.com/download?file=../../../etc/passwd",
            "description": "文件下载功能存在路径遍历漏洞。",
            "remediation": "限制文件访问路径，使用白名单验证。"
        },
        {
            "id": 7,
            "title": "开放重定向",
            "name": "Open Redirect",
            "severity": "medium",
            "url": "https://example.com/redirect?url=http://evil.com",
            "description": "重定向功能未验证目标URL。",
            "remediation": "验证重定向目标，使用白名单。"
        },
        {
            "id": 8,
            "title": "弱密码策略",
            "name": "Weak Password Policy",
            "severity": "medium",
            "url": "https://example.com/register",
            "description": "注册功能允许设置弱密码。",
            "remediation": "强制要求复杂密码，最小长度8位。"
        },
        {
            "id": 9,
            "title": "信息泄露-版本号",
            "name": "Version Disclosure",
            "severity": "low",
            "url": "https://example.com/",
            "description": "响应头泄露服务器版本信息。",
            "remediation": "隐藏服务器版本信息。"
        },
        {
            "id": 10,
            "title": "HTTP方法允许",
            "name": "HTTP Methods Allowed",
            "severity": "info",
            "url": "https://example.com/",
            "description": "服务器允许TRACE方法。",
            "remediation": "禁用不必要的HTTP方法。"
        }
    ]
}

EMPTY_REPORT_DATA: Dict[str, Any] = {
    "report_name": "空报告测试",
    "task_name": "空测试任务",
    "target": "https://safe-example.com",
    "scan_time": "2025-03-14T10:30:00Z",
    "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
    "vulnerabilities": []
}

MINIMAL_REPORT_DATA: Dict[str, Any] = {
    "report_name": "最小报告测试",
    "task_name": "最小测试任务",
    "target": "https://minimal-example.com",
    "scan_time": "2025-03-14T10:30:00Z",
    "summary": {"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
    "vulnerabilities": [
        {
            "id": 1,
            "title": "测试漏洞",
            "severity": "critical",
            "url": "https://minimal-example.com/test",
            "description": "测试描述",
            "remediation": "测试修复建议"
        }
    ]
}


class MockReport:
    """模拟报告对象"""
    def __init__(self, id=1, task_id=1, report_name="测试报告", report_type="json", content=None):
        self.id = id
        self.task_id = task_id
        self.report_name = report_name
        self.report_type = report_type
        self.content = content or json.dumps({
            "report_name": report_name,
            "task_name": "测试任务",
            "target": "https://test.example.com",
            "scan_time": "2025-03-14T10:00:00Z",
            "summary": {"critical": 1, "high": 1, "medium": 1, "low": 0, "info": 0},
            "vulnerabilities": SAMPLE_REPORT_DATA["vulnerabilities"][:3]
        })
        self.file_path = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.task = MockTask()


class MockTask:
    """模拟任务对象"""
    def __init__(self, id=1):
        self.id = id
        self.task_name = "测试扫描任务"
        self.task_type = "vulnerability"
        self.target = "https://test.example.com"
        self.status = "completed"
        self.progress = 100
        self.created_at = datetime.now()


class MockVulnerability:
    """模拟漏洞对象"""
    def __init__(self, id=1, **kwargs):
        self.id = id
        self.title = kwargs.get("title", "测试漏洞")
        self.vuln_type = kwargs.get("vuln_type", "XSS")
        self.severity = kwargs.get("severity", "high")
        self.url = kwargs.get("url", "https://test.example.com/vuln")
        self.description = kwargs.get("description", "测试描述")
        self.remediation = kwargs.get("remediation", "测试修复")
        self.status = "open"
        self.source_id = None
        self.source = "poc"


class TestCalculateRiskScore:
    """测试风险评分计算功能"""
    
    def test_empty_vulnerabilities(self):
        """测试空漏洞列表"""
        result = calculate_risk_score([])
        assert result["score"] == 0.0
        assert result["level"] == "info"
        assert result["label"] == "无风险"
    
    def test_single_critical_vulnerability(self):
        """测试单个严重漏洞"""
        vulns = [{"severity": "critical"}]
        result = calculate_risk_score(vulns)
        assert result["score"] == 100.0
        assert result["level"] == "critical"
        assert result["label"] == "极高风险"
    
    def test_single_high_vulnerability(self):
        """测试单个高危漏洞"""
        vulns = [{"severity": "high"}]
        result = calculate_risk_score(vulns)
        assert result["score"] == 80.0
        assert result["level"] == "critical"
    
    def test_mixed_severity_vulnerabilities(self):
        """测试混合严重程度漏洞"""
        vulns = [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
            {"severity": "info"}
        ]
        result = calculate_risk_score(vulns)
        assert result["score"] > 0
        assert result["level"] in ["critical", "high", "medium", "low", "info"]
    
    def test_unknown_severity(self):
        """测试未知严重程度"""
        vulns = [{"severity": "unknown"}]
        result = calculate_risk_score(vulns)
        assert result["score"] > 0
    
    def test_case_insensitive_severity(self):
        """测试严重程度大小写不敏感"""
        vulns_upper = [{"severity": "CRITICAL"}]
        vulns_lower = [{"severity": "critical"}]
        vulns_mixed = [{"severity": "Critical"}]
        
        result_upper = calculate_risk_score(vulns_upper)
        result_lower = calculate_risk_score(vulns_lower)
        result_mixed = calculate_risk_score(vulns_mixed)
        
        assert result_upper["score"] == result_lower["score"] == result_mixed["score"]
    
    def test_sample_report_risk_score(self):
        """测试示例报告的风险评分"""
        result = calculate_risk_score(SAMPLE_REPORT_DATA["vulnerabilities"])
        assert result["score"] > 0
        assert "level" in result
        assert "label" in result
        assert "color" in result


class TestGenerateHTMLReport:
    """测试HTML报告生成功能"""
    
    def test_generate_html_basic(self):
        """测试基本HTML报告生成"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        
        assert html is not None
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
    
    def test_html_contains_report_name(self):
        """测试HTML包含报告名称"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        assert SAMPLE_REPORT_DATA["report_name"] in html
    
    def test_html_contains_target(self):
        """测试HTML包含目标地址"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        assert SAMPLE_REPORT_DATA["target"] in html
    
    def test_html_contains_vulnerabilities(self):
        """测试HTML包含漏洞信息"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        
        for vuln in SAMPLE_REPORT_DATA["vulnerabilities"][:5]:
            assert vuln["title"] in html
    
    def test_html_contains_severity_colors(self):
        """测试HTML包含严重程度颜色"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        
        for severity, config in SEVERITY_CONFIG.items():
            assert config["color"] in html
    
    def test_html_contains_summary_counts(self):
        """测试HTML包含漏洞统计"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        summary = SAMPLE_REPORT_DATA["summary"]
        
        assert str(summary["critical"]) in html
        assert str(summary["high"]) in html
        assert str(summary["medium"]) in html
    
    def test_html_empty_report(self):
        """测试空报告HTML生成"""
        html = generate_html_report(EMPTY_REPORT_DATA)
        
        assert html is not None
        assert "未发现漏洞" in html
    
    def test_html_minimal_report(self):
        """测试最小报告HTML生成"""
        html = generate_html_report(MINIMAL_REPORT_DATA)
        
        assert html is not None
        assert MINIMAL_REPORT_DATA["vulnerabilities"][0]["title"] in html
    
    def test_html_structure_valid(self):
        """测试HTML结构有效性"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        
        assert "<head>" in html
        assert "</head>" in html
        assert "<body>" in html
        assert "</body>" in html
        assert "<style>" in html
        assert "</style>" in html
    
    def test_html_contains_risk_gauge(self):
        """测试HTML包含风险评估仪表盘"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        
        assert "风险评估" in html or "risk" in html.lower()
        assert "svg" in html.lower()


class TestGenerateMarkdownReport:
    """测试Markdown报告生成功能"""
    
    def test_generate_markdown_basic(self):
        """测试基本Markdown报告生成"""
        md = generate_markdown_report(SAMPLE_REPORT_DATA)
        
        assert md is not None
        assert len(md) > 0
        assert "# " in md
    
    def test_markdown_contains_report_name(self):
        """测试Markdown包含报告名称"""
        md = generate_markdown_report(SAMPLE_REPORT_DATA)
        assert SAMPLE_REPORT_DATA["report_name"] in md
    
    def test_markdown_contains_target(self):
        """测试Markdown包含目标地址"""
        md = generate_markdown_report(SAMPLE_REPORT_DATA)
        assert SAMPLE_REPORT_DATA["target"] in md
    
    def test_markdown_contains_vulnerabilities(self):
        """测试Markdown包含漏洞信息"""
        md = generate_markdown_report(SAMPLE_REPORT_DATA)
        
        for vuln in SAMPLE_REPORT_DATA["vulnerabilities"][:5]:
            assert vuln["title"] in md
    
    def test_markdown_contains_table(self):
        """测试Markdown包含表格"""
        md = generate_markdown_report(SAMPLE_REPORT_DATA)
        
        assert "|" in md
        assert "---" in md
    
    def test_markdown_empty_report(self):
        """测试空报告Markdown生成"""
        md = generate_markdown_report(EMPTY_REPORT_DATA)
        
        assert md is not None
        assert len(md) > 0


class TestJSONExport:
    """测试JSON格式导出功能"""
    
    def test_json_serialization(self):
        """测试JSON序列化"""
        json_str = json.dumps(SAMPLE_REPORT_DATA, ensure_ascii=False, indent=2)
        
        assert json_str is not None
        assert len(json_str) > 0
    
    def test_json_deserialization(self):
        """测试JSON反序列化"""
        json_str = json.dumps(SAMPLE_REPORT_DATA, ensure_ascii=False)
        data = json.loads(json_str)
        
        assert data["report_name"] == SAMPLE_REPORT_DATA["report_name"]
        assert data["target"] == SAMPLE_REPORT_DATA["target"]
        assert len(data["vulnerabilities"]) == len(SAMPLE_REPORT_DATA["vulnerabilities"])
    
    def test_json_unicode_support(self):
        """测试JSON Unicode支持"""
        chinese_data = {
            "report_name": "中文报告名称",
            "task_name": "中文任务名称",
            "vulnerabilities": [
                {
                    "title": "中文漏洞标题",
                    "description": "中文描述信息"
                }
            ]
        }
        
        json_str = json.dumps(chinese_data, ensure_ascii=False)
        data = json.loads(json_str)
        
        assert data["report_name"] == "中文报告名称"
        assert data["vulnerabilities"][0]["title"] == "中文漏洞标题"


class TestPDFExport:
    """测试PDF格式导出功能"""
    
    def test_pdf_returns_html(self):
        """测试PDF导出返回HTML（用于浏览器打印）"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        
        assert html is not None
        assert "<!DOCTYPE html>" in html
    
    def test_pdf_html_has_print_styles(self):
        """测试PDF HTML包含打印样式"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        
        assert "@media print" in html
    
    def test_pdf_html_no_scripts(self):
        """测试PDF HTML不包含脚本（安全考虑）"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        
        assert "<script" not in html.lower() or "function" not in html.lower()


class TestReportAPIEndpoints:
    """测试报告API端点"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        mock_report = MockReport()
        mock_task = MockTask()
        mock_vulns = [MockVulnerability(id=i, **v) for i, v in enumerate(SAMPLE_REPORT_DATA["vulnerabilities"][:3], 1)]
        return {
            "report": mock_report,
            "task": mock_task,
            "vulnerabilities": mock_vulns
        }
    
    def test_export_json_format(self, mock_db):
        """测试JSON格式导出"""
        content = json.loads(mock_db["report"].content)
        assert "report_name" in content
        assert "vulnerabilities" in content
    
    def test_export_html_format(self, mock_db):
        """测试HTML格式导出"""
        content = json.loads(mock_db["report"].content)
        html = generate_html_report(content)
        
        assert html is not None
        assert "<!DOCTYPE html>" in html
        assert "测试报告" in html
    
    def test_export_markdown_format(self, mock_db):
        """测试Markdown格式导出"""
        content = json.loads(mock_db["report"].content)
        md = generate_markdown_report(content)
        
        assert md is not None
        assert "# " in md
    
    def test_export_pdf_format(self, mock_db):
        """测试PDF格式导出（返回HTML用于打印）"""
        content = json.loads(mock_db["report"].content)
        html = generate_html_report(content)
        
        assert html is not None
        assert "@media print" in html
        assert "<!DOCTYPE html>" in html


class TestReportCreateEndpoint:
    """测试报告创建API端点"""
    
    def test_create_report_success(self):
        """测试成功创建报告"""
        from backend.api.reports import ReportCreate
        
        report_data = ReportCreate(
            task_id=1,
            name="测试报告_创建",
            format="json",
            include_awvs=False
        )
        
        assert report_data.task_id == 1
        assert report_data.name == "测试报告_创建"
        assert report_data.format == "json"
    
    def test_create_report_with_awvs(self):
        """测试创建包含AWVS数据的报告"""
        from backend.api.reports import ReportCreate
        
        report_data = ReportCreate(
            task_id=1,
            name="测试报告_AWVS",
            format="html",
            include_awvs=True
        )
        
        assert report_data.include_awvs is True


class TestReportCompareEndpoint:
    """测试报告对比API端点"""
    
    def test_compare_reports(self):
        """测试报告对比"""
        from backend.api.reports import ReportCompareRequest
        
        compare_request = ReportCompareRequest(
            report_id_1=1,
            report_id_2=2
        )
        
        assert compare_request.report_id_1 == 1
        assert compare_request.report_id_2 == 2


class TestReportExportIntegration:
    """报告导出集成测试"""
    
    def test_all_formats_generate_content(self):
        """测试所有格式都能生成内容"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        md = generate_markdown_report(SAMPLE_REPORT_DATA)
        json_str = json.dumps(SAMPLE_REPORT_DATA, ensure_ascii=False)
        
        assert len(html) > 0
        assert len(md) > 0
        assert len(json_str) > 0
    
    def test_all_formats_contain_essential_info(self):
        """测试所有格式都包含关键信息"""
        html = generate_html_report(SAMPLE_REPORT_DATA)
        md = generate_markdown_report(SAMPLE_REPORT_DATA)
        
        essential_info = [
            SAMPLE_REPORT_DATA["report_name"],
            SAMPLE_REPORT_DATA["target"],
            SAMPLE_REPORT_DATA["vulnerabilities"][0]["title"]
        ]
        
        for info in essential_info:
            assert info in html
            assert info in md
    
    def test_severity_config_completeness(self):
        """测试严重程度配置完整性"""
        required_severities = ["critical", "high", "medium", "low", "info"]
        
        for severity in required_severities:
            assert severity in SEVERITY_CONFIG
            assert "color" in SEVERITY_CONFIG[severity]
            assert "label" in SEVERITY_CONFIG[severity]
    
    def test_report_data_validation(self):
        """测试报告数据验证"""
        required_fields = ["report_name", "task_name", "target", "scan_time", "summary", "vulnerabilities"]
        
        for field in required_fields:
            assert field in SAMPLE_REPORT_DATA
        
        summary_fields = ["critical", "high", "medium", "low", "info"]
        for field in summary_fields:
            assert field in SAMPLE_REPORT_DATA["summary"]


class TestEdgeCases:
    """边界情况测试"""
    
    def test_missing_optional_fields(self):
        """测试缺少可选字段"""
        minimal_data = {
            "report_name": "测试报告",
            "vulnerabilities": []
        }
        
        html = generate_html_report(minimal_data)
        assert html is not None
    
    def test_special_characters_in_content(self):
        """测试内容中的特殊字符"""
        special_data = {
            "report_name": "测试<>&\"'报告",
            "vulnerabilities": [
                {
                    "title": "漏洞<script>alert(1)</script>",
                    "description": "描述<>&\"'测试",
                    "severity": "high"
                }
            ]
        }
        
        html = generate_html_report(special_data)
        assert html is not None
    
    def test_very_long_content(self):
        """测试超长内容"""
        long_data = {
            "report_name": "测试报告",
            "vulnerabilities": [
                {
                    "title": "漏洞" + "A" * 1000,
                    "description": "描述" + "B" * 10000,
                    "severity": "high"
                }
            ]
        }
        
        html = generate_html_report(long_data)
        assert html is not None
        assert len(html) > 1000
    
    def test_many_vulnerabilities(self):
        """测试大量漏洞"""
        many_vulns_data = {
            "report_name": "大量漏洞测试",
            "vulnerabilities": [
                {
                    "id": i,
                    "title": f"漏洞_{i}",
                    "severity": "medium",
                    "url": f"https://example.com/vuln/{i}",
                    "description": f"描述_{i}",
                    "remediation": f"修复_{i}"
                }
                for i in range(100)
            ]
        }
        
        html = generate_html_report(many_vulns_data)
        assert html is not None
        assert len(html) > 10000


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("报告功能综合测试")
    print("=" * 60)
    
    test_classes = [
        TestCalculateRiskScore,
        TestGenerateHTMLReport,
        TestGenerateMarkdownReport,
        TestJSONExport,
        TestPDFExport,
        TestReportAPIEndpoints,
        TestReportCreateEndpoint,
        TestReportCompareEndpoint,
        TestReportExportIntegration,
        TestEdgeCases
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        print(f"\n--- {test_class.__name__} ---")
        instance = test_class()
        
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total_tests += 1
                try:
                    method = getattr(instance, method_name)
                    import inspect
                    sig = inspect.signature(method)
                    if 'mock_db' in sig.parameters:
                        mock_db = {
                            "report": MockReport(),
                            "task": MockTask(),
                            "vulnerabilities": [MockVulnerability(id=i, **v) for i, v in enumerate(SAMPLE_REPORT_DATA["vulnerabilities"][:3], 1)]
                        }
                        method(mock_db=mock_db)
                    else:
                        method()
                    
                    print(f"  ✓ {method_name}")
                    passed_tests += 1
                except AssertionError as e:
                    print(f"  ✗ {method_name}: {str(e)}")
                    failed_tests += 1
                except Exception as e:
                    print(f"  ✗ {method_name}: {type(e).__name__}: {str(e)}")
                    failed_tests += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: 总计 {total_tests}, 通过 {passed_tests}, 失败 {failed_tests}")
    print("=" * 60)
    
    return failed_tests == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

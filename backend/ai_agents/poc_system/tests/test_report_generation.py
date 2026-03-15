"""
报告生成测试

测试报告生成器的各项功能，包括HTML、JSON报告生成和结果分析。
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.ai_agents.poc_system.tests.conftest import (
    MockVerificationResult,
    MockVerificationTask,
    load_test_data,
    TEST_DATA_DIR
)
from backend.ai_agents.poc_system.report_generator import (
    ReportGenerator,
    ReportSection,
    TemplateVariable,
    CustomTemplate,
    Language,
    I18N
)


class TestReportGenerator:
    """测试报告生成器"""
    
    @pytest.fixture
    def report_generator(self):
        """创建报告生成器fixture"""
        return ReportGenerator()
    
    @pytest.fixture
    def mock_results(self):
        """创建模拟结果列表"""
        return [
            MockVerificationResult(
                id="result_001",
                task_id="task_001",
                poc_name="ThinkPHP RCE",
                poc_id="poc-001",
                target="http://target1.example.com",
                vulnerable=True,
                message="Critical vulnerability detected",
                output="Remote code execution confirmed",
                execution_time=2.5,
                confidence=0.95,
                severity="critical",
                cvss_score=9.8
            ),
            MockVerificationResult(
                id="result_002",
                task_id="task_001",
                poc_name="Log4j RCE",
                poc_id="poc-002",
                target="http://target2.example.com",
                vulnerable=True,
                message="Log4Shell vulnerability detected",
                output="JNDI injection successful",
                execution_time=3.0,
                confidence=0.98,
                severity="critical",
                cvss_score=10.0
            ),
            MockVerificationResult(
                id="result_003",
                task_id="task_001",
                poc_name="SQL Injection",
                poc_id="poc-003",
                target="http://target3.example.com",
                vulnerable=False,
                message="No SQL injection found",
                output="Target is not vulnerable",
                execution_time=1.5,
                confidence=0.85,
                severity="info",
                cvss_score=0.0
            )
        ]
    
    @pytest.fixture
    def mock_task(self):
        """创建模拟任务"""
        return MockVerificationTask(
            id="task_001",
            poc_name="Security Scan",
            poc_id="scan-001",
            target="http://example.com",
            status="completed",
            progress=100
        )
    
    def test_initialization(self, report_generator):
        """测试报告生成器初始化"""
        assert report_generator is not None
        assert hasattr(report_generator, 'report_templates')
        assert hasattr(report_generator, 'custom_templates')
        assert hasattr(report_generator, 'enabled_sections')
        assert hasattr(report_generator, 'i18n')
    
    def test_report_templates_available(self, report_generator):
        """测试报告模板可用性"""
        templates = report_generator.report_templates
        
        assert 'html' in templates
        assert 'json' in templates
        assert 'pdf' in templates
    
    def test_enabled_sections(self, report_generator):
        """测试启用的章节"""
        sections = report_generator.enabled_sections
        
        assert 'executive_summary' in sections
        assert 'verification_details' in sections
        assert 'statistics' in sections
    
    def test_enable_disable_section(self, report_generator):
        """测试启用/禁用章节"""
        report_generator.disable_section('test_section')
        assert 'test_section' not in report_generator.enabled_sections
        
        report_generator.enable_section('test_section')
        assert 'test_section' in report_generator.enabled_sections
    
    def test_is_section_enabled(self, report_generator):
        """测试检查章节是否启用"""
        report_generator.enable_section('enabled_section')
        report_generator.disable_section('disabled_section')
        
        assert report_generator.is_section_enabled('enabled_section') is True
        assert report_generator.is_section_enabled('disabled_section') is False


class TestHTMLReportGeneration:
    """测试HTML报告生成"""
    
    @pytest.fixture
    def generator(self):
        return ReportGenerator()
    
    @pytest.fixture
    def results(self):
        return [
            MockVerificationResult(
                id="html_001",
                task_id="task_html",
                poc_name="HTML Test POC",
                poc_id="html-001",
                target="http://html.example.com",
                vulnerable=True,
                message="Vulnerability found",
                severity="high",
                cvss_score=7.5,
                confidence=0.9,
                execution_time=2.0
            )
        ]
    
    @pytest.fixture
    def task(self):
        return MockVerificationTask(
            id="task_html",
            poc_name="HTML Report Test",
            poc_id="html-test",
            target="http://html.example.com"
        )
    
    @pytest.mark.asyncio
    async def test_generate_html_report(self, generator, task, results):
        """测试生成HTML报告"""
        with patch('backend.ai_agents.poc_system.report_generator.POCVerificationResult') as mock_result:
            mock_result.filter = AsyncMock(return_value=results)
            
            html_content = await generator._generate_html_report(task, results)
            
            assert html_content is not None
            assert isinstance(html_content, str)
            assert len(html_content) > 0
    
    @pytest.mark.asyncio
    async def test_html_report_structure(self, generator, task, results):
        """测试HTML报告结构"""
        with patch('backend.ai_agents.poc_system.report_generator.POCVerificationResult') as mock_result:
            mock_result.filter = AsyncMock(return_value=results)
            
            html_content = await generator._generate_html_report(task, results)
            
            assert "<!DOCTYPE html>" in html_content
            assert "<html" in html_content
            assert "</html>" in html_content
            assert "<head>" in html_content
            assert "<body>" in html_content
    
    @pytest.mark.asyncio
    async def test_html_report_contains_required_sections(self, generator, task, results):
        """测试HTML报告包含必要章节"""
        with patch('backend.ai_agents.poc_system.report_generator.POCVerificationResult') as mock_result:
            mock_result.filter = AsyncMock(return_value=results)
            
            html_content = await generator._generate_html_report(task, results)
            
            assert "执行摘要" in html_content or "Executive Summary" in html_content or "executive" in html_content.lower()
            assert "验证结果详情" in html_content or "Verification Details" in html_content or "verification" in html_content.lower()
    
    @pytest.mark.asyncio
    async def test_html_report_contains_results(self, generator, task, results):
        """测试HTML报告包含结果"""
        with patch('backend.ai_agents.poc_system.report_generator.POCVerificationResult') as mock_result:
            mock_result.filter = AsyncMock(return_value=results)
            
            html_content = await generator._generate_html_report(task, results)
            
            for result in results:
                assert result.poc_name in html_content or result.target in html_content
    
    @pytest.mark.asyncio
    async def test_html_report_css_styles(self, generator, task, results):
        """测试HTML报告CSS样式"""
        with patch('backend.ai_agents.poc_system.report_generator.POCVerificationResult') as mock_result:
            mock_result.filter = AsyncMock(return_value=results)
            
            html_content = await generator._generate_html_report(task, results)
            
            assert "<style>" in html_content
            assert ".container" in html_content or ".header" in html_content
    
    @pytest.mark.asyncio
    async def test_html_report_responsive_design(self, generator, task, results):
        """测试HTML报告响应式设计"""
        with patch('backend.ai_agents.poc_system.report_generator.POCVerificationResult') as mock_result:
            mock_result.filter = AsyncMock(return_value=results)
            
            html_content = await generator._generate_html_report(task, results)
            
            assert "@media" in html_content


class TestJSONReportGeneration:
    """测试JSON报告生成"""
    
    @pytest.fixture
    def generator(self):
        return ReportGenerator()
    
    @pytest.fixture
    def results(self):
        return [
            MockVerificationResult(
                id="json_001",
                task_id="task_json",
                poc_name="JSON Test POC",
                poc_id="json-001",
                target="http://json.example.com",
                vulnerable=True,
                message="JSON vulnerability",
                severity="critical",
                cvss_score=9.5,
                confidence=0.95,
                execution_time=1.5
            )
        ]
    
    @pytest.fixture
    def task(self):
        return MockVerificationTask(
            id="task_json",
            poc_name="JSON Report Test",
            poc_id="json-test",
            target="http://json.example.com"
        )
    
    @pytest.mark.asyncio
    async def test_generate_json_report(self, generator, task, results):
        """测试生成JSON报告"""
        json_content = await generator._generate_json_report(task, results)
        
        assert json_content is not None
        assert isinstance(json_content, str)
    
    @pytest.mark.asyncio
    async def test_json_report_valid_structure(self, generator, task, results):
        """测试JSON报告有效结构"""
        json_content = await generator._generate_json_report(task, results)
        
        report_data = json.loads(json_content)
        
        assert "report_type" in report_data
        assert "generated_at" in report_data
        assert "summary" in report_data
        assert "results" in report_data
    
    @pytest.mark.asyncio
    async def test_json_report_summary_fields(self, generator, task, results):
        """测试JSON报告摘要字段"""
        json_content = await generator._generate_json_report(task, results)
        
        report_data = json.loads(json_content)
        summary = report_data.get("summary", {})
        
        assert "total_results" in summary
        assert "vulnerable_count" in summary
        assert "vulnerability_rate" in summary
        assert "severity_distribution" in summary
    
    @pytest.mark.asyncio
    async def test_json_report_results_array(self, generator, task, results):
        """测试JSON报告结果数组"""
        json_content = await generator._generate_json_report(task, results)
        
        report_data = json.loads(json_content)
        results_array = report_data.get("results", [])
        
        assert isinstance(results_array, list)
        assert len(results_array) == len(results)
    
    @pytest.mark.asyncio
    async def test_json_report_result_fields(self, generator, task, results):
        """测试JSON报告结果字段"""
        json_content = await generator._generate_json_report(task, results)
        
        report_data = json.loads(json_content)
        results_array = report_data.get("results", [])
        
        if results_array:
            result = results_array[0]
            required_fields = [
                "id", "poc_name", "target", "vulnerable",
                "message", "severity", "cvss_score"
            ]
            
            for field in required_fields:
                assert field in result, f"缺少字段: {field}"


class TestReportStatistics:
    """测试报告统计功能"""
    
    @pytest.fixture
    def generator(self):
        return ReportGenerator()
    
    @pytest.fixture
    def mixed_results(self):
        return [
            MockVerificationResult(
                id="stat_001",
                task_id="task_stat",
                poc_name="Critical Vuln",
                poc_id="stat-001",
                target="http://critical.example.com",
                vulnerable=True,
                message="Critical",
                severity="critical",
                cvss_score=9.8,
                confidence=0.95,
                execution_time=2.0
            ),
            MockVerificationResult(
                id="stat_002",
                task_id="task_stat",
                poc_name="High Vuln",
                poc_id="stat-002",
                target="http://high.example.com",
                vulnerable=True,
                message="High",
                severity="high",
                cvss_score=7.5,
                confidence=0.85,
                execution_time=1.5
            ),
            MockVerificationResult(
                id="stat_003",
                task_id="task_stat",
                poc_name="Medium Vuln",
                poc_id="stat-003",
                target="http://medium.example.com",
                vulnerable=True,
                message="Medium",
                severity="medium",
                cvss_score=5.5,
                confidence=0.75,
                execution_time=1.0
            ),
            MockVerificationResult(
                id="stat_004",
                task_id="task_stat",
                poc_name="No Vuln",
                poc_id="stat-004",
                target="http://safe.example.com",
                vulnerable=False,
                message="Safe",
                severity="info",
                cvss_score=0.0,
                confidence=0.9,
                execution_time=0.5
            )
        ]
    
    @pytest.mark.asyncio
    async def test_generate_statistics(self, generator, mixed_results):
        """测试生成统计信息"""
        stats = await generator.generate_statistics(mixed_results)
        
        assert stats is not None
        assert stats["total"] == 4
        assert stats["vulnerable"] == 3
        assert stats["not_vulnerable"] == 1
    
    @pytest.mark.asyncio
    async def test_vulnerability_rate_calculation(self, generator, mixed_results):
        """测试漏洞率计算"""
        stats = await generator.generate_statistics(mixed_results)
        
        expected_rate = (3 / 4) * 100
        assert abs(stats["vulnerability_rate"] - expected_rate) < 0.01
    
    @pytest.mark.asyncio
    async def test_severity_distribution(self, generator, mixed_results):
        """测试严重级别分布"""
        stats = await generator.generate_statistics(mixed_results)
        
        severity_dist = stats.get("severity_distribution", {})
        
        assert severity_dist.get("critical", 0) == 1
        assert severity_dist.get("high", 0) == 1
        assert severity_dist.get("medium", 0) == 1
        assert severity_dist.get("info", 0) == 1
    
    @pytest.mark.asyncio
    async def test_average_confidence(self, generator, mixed_results):
        """测试平均置信度"""
        stats = await generator.generate_statistics(mixed_results)
        
        assert "average_confidence" in stats
        assert 0 <= stats["average_confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_average_cvss_score(self, generator, mixed_results):
        """测试平均CVSS评分"""
        stats = await generator.generate_statistics(mixed_results)
        
        assert "average_cvss_score" in stats
        assert 0 <= stats["average_cvss_score"] <= 10
    
    @pytest.mark.asyncio
    async def test_empty_results_statistics(self, generator):
        """测试空结果统计"""
        stats = await generator.generate_statistics([])
        
        assert stats["total"] == 0
        assert stats["vulnerable"] == 0
        assert stats["vulnerability_rate"] == 0


class TestResultAnalysis:
    """测试结果分析功能"""
    
    @pytest.fixture
    def generator(self):
        return ReportGenerator()
    
    @pytest.fixture
    def task(self):
        return MockVerificationTask(
            id="task_analysis",
            poc_name="Analysis Test",
            poc_id="analysis-001",
            target="http://analysis.example.com",
            status="completed",
            progress=100
        )
    
    @pytest.fixture
    def results(self):
        return [
            MockVerificationResult(
                id="analysis_001",
                task_id="task_analysis",
                poc_name="RCE Vulnerability",
                poc_id="analysis-001",
                target="http://target1.example.com",
                vulnerable=True,
                message="Remote code execution",
                output="RCE confirmed",
                severity="critical",
                cvss_score=9.8,
                confidence=0.98,
                execution_time=3.0
            )
        ]
    
    @pytest.mark.asyncio
    async def test_generate_execution_summary(self, generator, task, results):
        """测试生成执行摘要"""
        class MockQuerySet:
            async def order_by(self, *args, **kwargs):
                return results
        
        def mock_filter(*args, **kwargs):
            return MockQuerySet()
        
        with patch('backend.ai_agents.poc_system.report_generator.POCVerificationResult') as mock_result:
            mock_result.filter = mock_filter
            
            summary = await generator.generate_execution_summary(task)
            
            assert summary is not None
            assert "task_id" in summary
            assert "poc_name" in summary
            assert "summary" in summary
    
    @pytest.mark.asyncio
    async def test_generate_vulnerability_details(self, generator, results):
        """测试生成漏洞详情"""
        details = await generator.generate_vulnerability_details(results)
        
        assert isinstance(details, list)
        
        vulnerable_results = [r for r in results if r.vulnerable]
        assert len(details) == len(vulnerable_results)
    
    @pytest.mark.asyncio
    async def test_vulnerability_details_content(self, generator, results):
        """测试漏洞详情内容"""
        details = await generator.generate_vulnerability_details(results)
        
        if details:
            detail = details[0]
            assert "poc_name" in detail
            assert "target" in detail
            assert "severity" in detail
            assert "message" in detail


class TestCustomTemplate:
    """测试自定义模板"""
    
    @pytest.fixture
    def generator(self):
        return ReportGenerator()
    
    def test_register_custom_template(self, generator):
        """测试注册自定义模板"""
        template = CustomTemplate(
            name="test_template",
            html_template="<html>{{content}}</html>",
            variables={
                "title": TemplateVariable(name="title", value="Test Report")
            }
        )
        
        generator.register_custom_template(template)
        
        assert "test_template" in generator.custom_templates
    
    def test_unregister_custom_template(self, generator):
        """测试注销自定义模板"""
        template = CustomTemplate(name="unregister_test")
        generator.register_custom_template(template)
        
        result = generator.unregister_custom_template("unregister_test")
        
        assert result is True
        assert "unregister_test" not in generator.custom_templates
    
    def test_get_template_variables(self, generator):
        """测试获取模板变量"""
        template = CustomTemplate(
            name="var_test",
            variables={
                "var1": TemplateVariable(name="var1", value="value1"),
                "var2": TemplateVariable(name="var2", value="value2")
            }
        )
        generator.register_custom_template(template)
        
        variables = generator.get_template_variables("var_test")
        
        assert variables["var1"] == "value1"
        assert variables["var2"] == "value2"
    
    def test_set_template_variable(self, generator):
        """测试设置模板变量"""
        template = CustomTemplate(name="set_var_test")
        generator.register_custom_template(template)
        
        result = generator.set_template_variable("set_var_test", "new_var", "new_value")
        
        assert result is True
        variables = generator.get_template_variables("set_var_test")
        assert variables["new_var"] == "new_value"


class TestI18N:
    """测试多语言支持"""
    
    def test_default_language(self):
        """测试默认语言"""
        i18n = I18N()
        
        assert i18n.language == Language.ZH_CN
    
    def test_set_language(self):
        """测试设置语言"""
        i18n = I18N()
        i18n.set_language(Language.EN_US)
        
        assert i18n.language == Language.EN_US
    
    def test_get_translation_zh_cn(self):
        """测试中文翻译"""
        i18n = I18N(Language.ZH_CN)
        
        assert i18n.get("report_title") == "POC 验证报告"
        assert i18n.get("executive_summary") == "执行摘要"
    
    def test_get_translation_en_us(self):
        """测试英文翻译"""
        i18n = I18N(Language.EN_US)
        
        assert i18n.get("report_title") == "POC Verification Report"
        assert i18n.get("executive_summary") == "Executive Summary"
    
    def test_format_translation(self):
        """测试格式化翻译"""
        i18n = I18N(Language.ZH_CN)
        
        text = i18n.get(
            "executive_summary_text",
            total=10,
            vuln=5,
            rate="50.0",
            critical=2,
            high=2,
            medium=1,
            low=0
        )
        
        assert "10" in text
        assert "5" in text


class TestReportDataValidation:
    """测试报告数据验证"""
    
    @pytest.fixture
    def report_template_data(self):
        """加载报告模板数据"""
        return load_test_data("reports/report_template.json")
    
    @pytest.fixture
    def mock_tasks_data(self):
        """加载模拟任务数据"""
        return load_test_data("reports/mock_tasks.json")
    
    def test_report_template_structure(self, report_template_data):
        """测试报告模板结构"""
        assert "report_template" in report_template_data
        
        template = report_template_data["report_template"]
        assert "name" in template
        assert "version" in template
        assert "sections" in template
    
    def test_report_template_sections(self, report_template_data):
        """测试报告模板章节"""
        template = report_template_data["report_template"]
        sections = template.get("sections", [])
        
        assert len(sections) > 0
        
        for section in sections:
            assert "id" in section
            assert "title" in section
            assert "enabled" in section
            assert "order" in section
    
    def test_expected_output_structure(self, report_template_data):
        """测试预期输出结构"""
        expected = report_template_data.get("expected_output", {})
        
        assert "html" in expected
        assert "json" in expected
        
        html_expected = expected["html"]
        assert "contains" in html_expected
        assert "not_contains" in html_expected
        
        json_expected = expected["json"]
        assert "required_fields" in json_expected
    
    def test_mock_tasks_data(self, mock_tasks_data):
        """测试模拟任务数据"""
        assert "mock_tasks" in mock_tasks_data
        
        tasks = mock_tasks_data["mock_tasks"]
        assert isinstance(tasks, list)
        
        for task in tasks:
            assert "id" in task
            assert "poc_name" in task
            assert "target" in task
            assert "status" in task


@pytest.mark.report
class TestReportEdgeCases:
    """测试报告边界情况"""
    
    @pytest.fixture
    def generator(self):
        return ReportGenerator()
    
    @pytest.mark.asyncio
    async def test_empty_results_report(self, generator):
        """测试空结果报告"""
        task = MockVerificationTask(
            id="empty_task",
            poc_name="Empty Test",
            poc_id="empty-001",
            target="http://empty.example.com"
        )
        
        html_content = await generator._generate_html_report(task, [])
        json_content = await generator._generate_json_report(task, [])
        
        assert html_content is not None
        assert json_content is not None
        
        report_data = json.loads(json_content)
        assert report_data["summary"]["total_results"] == 0
    
    @pytest.mark.asyncio
    async def test_large_results_report(self, generator):
        """测试大量结果报告"""
        large_results = [
            MockVerificationResult(
                id=f"large_{i:03d}",
                task_id="large_task",
                poc_name=f"POC {i}",
                poc_id=f"large-{i:03d}",
                target=f"http://target{i}.example.com",
                vulnerable=i % 2 == 0,
                message=f"Result {i}",
                severity="high" if i % 3 == 0 else "medium",
                cvss_score=7.5 if i % 3 == 0 else 5.5,
                confidence=0.85,
                execution_time=1.0
            )
            for i in range(100)
        ]
        
        task = MockVerificationTask(
            id="large_task",
            poc_name="Large Test",
            poc_id="large-001",
            target="http://large.example.com"
        )
        
        json_content = await generator._generate_json_report(task, large_results)
        report_data = json.loads(json_content)
        
        assert report_data["summary"]["total_results"] == 100
    
    @pytest.mark.asyncio
    async def test_special_characters_in_report(self, generator):
        """测试报告中的特殊字符"""
        results = [
            MockVerificationResult(
                id="special_001",
                task_id="special_task",
                poc_name="Special <>&\"' Characters",
                poc_id="special-001",
                target="http://special.example.com?param=<script>",
                vulnerable=True,
                message="Found <script>alert('XSS')</script>",
                output="HTML entities test",
                severity="high",
                cvss_score=7.5,
                confidence=0.9,
                execution_time=1.0
            )
        ]
        
        task = MockVerificationTask(
            id="special_task",
            poc_name="Special Test",
            poc_id="special-001",
            target="http://special.example.com"
        )
        
        html_content = await generator._generate_html_report(task, results)
        
        assert html_content is not None
    
    @pytest.mark.asyncio
    async def test_merge_reports(self, generator):
        """测试合并报告"""
        reports = [
            {
                "summary": {
                    "total_results": 10,
                    "vulnerable_count": 5,
                    "severity_distribution": {"critical": 2, "high": 3}
                },
                "results": [{"id": "1"}, {"id": "2"}]
            },
            {
                "summary": {
                    "total_results": 8,
                    "vulnerable_count": 3,
                    "severity_distribution": {"critical": 1, "high": 2}
                },
                "results": [{"id": "3"}, {"id": "4"}]
            }
        ]
        
        merged = await generator.merge_reports(reports, format="json")
        
        merged_data = json.loads(merged)
        
        assert merged_data["source_reports"] == 2
        assert len(merged_data["results"]) == 4


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'report'])

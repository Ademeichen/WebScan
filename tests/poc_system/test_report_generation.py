"""
报告生成测试

测试HTML报告生成、JSON报告生成、结果分析功能。
"""
import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.ai_agents.poc_system.report_generator import (
    ReportGenerator,
    ReportSection,
    TemplateVariable,
    CustomTemplate,
    Language,
    I18N
)


class TestI18N:
    """测试多语言支持"""
    
    def test_default_language(self):
        """测试默认语言"""
        i18n = I18N()
        
        assert i18n.language == Language.ZH_CN
    
    def test_get_text_zh_cn(self):
        """测试获取中文文本"""
        i18n = I18N(Language.ZH_CN)
        
        text = i18n.get("report_title")
        assert text == "POC 验证报告"
        
        text = i18n.get("vulnerabilities_found")
        assert text == "发现漏洞"
    
    def test_get_text_en_us(self):
        """测试获取英文文本"""
        i18n = I18N(Language.EN_US)
        
        text = i18n.get("report_title")
        assert text == "POC Verification Report"
        
        text = i18n.get("vulnerabilities_found")
        assert text == "Vulnerabilities Found"
    
    def test_get_text_with_format(self):
        """测试带格式化的文本"""
        i18n = I18N(Language.ZH_CN)
        
        text = i18n.get(
            "executive_summary_text",
            total=10,
            vuln=3,
            rate="30.0",
            critical=1,
            high=1,
            medium=1,
            low=0
        )
        
        assert "10" in text
        assert "3" in text
    
    def test_set_language(self):
        """测试设置语言"""
        i18n = I18N()
        
        i18n.set_language(Language.EN_US)
        assert i18n.language == Language.EN_US
        
        i18n.set_language(Language.JA_JP)
        assert i18n.language == Language.JA_JP


class TestReportSection:
    """测试报告章节"""
    
    def test_section_creation(self):
        """测试创建报告章节"""
        section = ReportSection(
            section_id="summary",
            title="执行摘要",
            content="这是摘要内容",
            enabled=True,
            order=1
        )
        
        assert section.section_id == "summary"
        assert section.title == "执行摘要"
        assert section.content == "这是摘要内容"
        assert section.enabled is True
        assert section.order == 1
    
    def test_section_defaults(self):
        """测试章节默认值"""
        section = ReportSection(
            section_id="test",
            title="Test"
        )
        
        assert section.content == ""
        assert section.enabled is True
        assert section.order == 0


class TestTemplateVariable:
    """测试模板变量"""
    
    def test_variable_creation(self):
        """测试创建模板变量"""
        var = TemplateVariable(
            name="title",
            value="测试报告",
            description="报告标题"
        )
        
        assert var.name == "title"
        assert var.value == "测试报告"
        assert var.description == "报告标题"
    
    def test_variable_defaults(self):
        """测试变量默认值"""
        var = TemplateVariable(name="test", value="value")
        
        assert var.description == ""


class TestCustomTemplate:
    """测试自定义模板"""
    
    def test_template_creation(self):
        """测试创建自定义模板"""
        template = CustomTemplate(
            name="custom_report",
            html_template="<html>{{title}}</html>",
            variables={
                "title": TemplateVariable(name="title", value="Test")
            }
        )
        
        assert template.name == "custom_report"
        assert template.html_template == "<html>{{title}}</html>"
        assert "title" in template.variables
    
    def test_template_with_base(self):
        """测试带基础模板的模板"""
        base_template = CustomTemplate(
            name="base",
            html_template="<html><body>{content}</body></html>",
            variables={
                "title": TemplateVariable(name="title", value="Base Title")
            }
        )
        
        template = CustomTemplate(
            name="derived",
            base_template="base",
            variables={
                "title": TemplateVariable(name="title", value="Derived Title")
            }
        )
        
        assert template.name == "derived"


class TestReportGenerator:
    """测试报告生成器"""
    
    @pytest.fixture
    def generator(self):
        return ReportGenerator()
    
    def test_generator_initialization(self, generator):
        """测试生成器初始化"""
        assert generator is not None
        assert hasattr(generator, 'report_templates')
        assert hasattr(generator, 'custom_templates')
        assert hasattr(generator, 'enabled_sections')
        assert hasattr(generator, 'i18n')
    
    def test_register_custom_template(self, generator):
        """测试注册自定义模板"""
        template = CustomTemplate(
            name="test_template",
            html_template="<html>test</html>"
        )
        
        generator.register_custom_template(template)
        
        assert "test_template" in generator.custom_templates
    
    def test_unregister_custom_template(self, generator):
        """测试注销自定义模板"""
        template = CustomTemplate(
            name="to_remove",
            html_template="<html>test</html>"
        )
        
        generator.register_custom_template(template)
        assert "to_remove" in generator.custom_templates
        
        result = generator.unregister_custom_template("to_remove")
        assert result is True
        assert "to_remove" not in generator.custom_templates
    
    def test_unregister_nonexistent_template(self, generator):
        """测试注销不存在的模板"""
        result = generator.unregister_custom_template("nonexistent")
        assert result is False
    
    def test_enable_section(self, generator):
        """测试启用章节"""
        generator.disable_section("test_section")
        assert not generator.is_section_enabled("test_section")
        
        generator.enable_section("test_section")
        assert generator.is_section_enabled("test_section")
    
    def test_disable_section(self, generator):
        """测试禁用章节"""
        generator.enable_section("test_section")
        assert generator.is_section_enabled("test_section")
        
        generator.disable_section("test_section")
        assert not generator.is_section_enabled("test_section")
    
    def test_set_language(self, generator):
        """测试设置语言"""
        generator.set_language(Language.EN_US)
        assert generator.i18n.language == Language.EN_US
    
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
        template = CustomTemplate(
            name="set_var_test",
            variables={
                "var1": TemplateVariable(name="var1", value="old")
            }
        )
        
        generator.register_custom_template(template)
        result = generator.set_template_variable("set_var_test", "var1", "new")
        
        assert result is True
        assert generator.custom_templates["set_var_test"].variables["var1"].value == "new"
    
    def test_set_template_variable_new(self, generator):
        """测试设置新模板变量"""
        template = CustomTemplate(
            name="new_var_test",
            variables={}
        )
        
        generator.register_custom_template(template)
        result = generator.set_template_variable("new_var_test", "new_var", "value")
        
        assert result is True
        assert "new_var" in generator.custom_templates["new_var_test"].variables
    
    def test_set_template_variable_nonexistent_template(self, generator):
        """测试设置不存在模板的变量"""
        result = generator.set_template_variable("nonexistent", "var", "value")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_json_report(self, generator):
        """测试生成JSON报告"""
        mock_task = Mock()
        mock_task.id = "test_task_id"
        mock_task.poc_name = "test_poc"
        mock_task.poc_id = "poc_001"
        mock_task.target = "https://example.com"
        mock_task.status = "completed"
        mock_task.progress = 100
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()
        
        mock_result = Mock()
        mock_result.id = "result_001"
        mock_result.poc_name = "test_poc"
        mock_result.poc_id = "poc_001"
        mock_result.target = "https://example.com"
        mock_result.vulnerable = True
        mock_result.message = "Vulnerability found"
        mock_result.output = "Test output"
        mock_result.error = None
        mock_result.execution_time = 1.5
        mock_result.confidence = 0.9
        mock_result.severity = "high"
        mock_result.cvss_score = 7.5
        mock_result.created_at = datetime.now()
        
        with patch('backend.ai_agents.poc_system.report_generator.POCVerificationResult') as mock_result_model:
            mock_result_model.filter = AsyncMock()
            mock_result_model.filter.return_value.order_by = AsyncMock()
            mock_result_model.filter.return_value.order_by.return_value = [mock_result]
            
            report = await generator._generate_json_report(
                mock_task,
                [mock_result],
                is_batch=False
            )
            
            data = json.loads(report)
            
            assert "report_type" in data
            assert "generated_at" in data
            assert "summary" in data
            assert "results" in data
    
    def test_get_modern_css(self, generator):
        """测试获取CSS样式"""
        css = generator._get_modern_css()
        
        assert "<style>" in css
        assert "</style>" in css
        assert "primary-color" in css
    
    def test_get_javascript(self, generator):
        """测试获取JavaScript代码"""
        js = generator._get_javascript()
        
        assert "<script>" in js
        assert "</script>" in js
        assert "toggleTheme" in js
    
    @pytest.mark.asyncio
    async def test_generate_statistics(self, generator):
        """测试生成统计信息"""
        mock_result1 = Mock()
        mock_result1.vulnerable = True
        mock_result1.confidence = 0.9
        mock_result1.cvss_score = 7.5
        mock_result1.severity = "high"
        
        mock_result2 = Mock()
        mock_result2.vulnerable = False
        mock_result2.confidence = 0.5
        mock_result2.cvss_score = 0.0
        mock_result2.severity = "info"
        
        stats = await generator.generate_statistics([mock_result1, mock_result2])
        
        assert stats["total"] == 2
        assert stats["vulnerable"] == 1
        assert stats["vulnerability_rate"] == 50.0
    
    @pytest.mark.asyncio
    async def test_generate_statistics_empty(self, generator):
        """测试生成空统计信息"""
        stats = await generator.generate_statistics([])
        
        assert stats["total"] == 0
        assert stats["vulnerable"] == 0
        assert stats["vulnerability_rate"] == 0


class TestReportGenerationIntegration:
    """报告生成集成测试"""
    
    @pytest.fixture
    def generator(self):
        return ReportGenerator()
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.mark.asyncio
    async def test_save_report_to_file(self, generator, temp_dir):
        """测试保存报告到文件"""
        mock_task = Mock()
        mock_task.id = "test_task"
        mock_task.poc_name = "test_poc"
        mock_task.poc_id = "poc_001"
        mock_task.target = "https://example.com"
        mock_task.status = "completed"
        mock_task.progress = 100
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()
        
        mock_result = Mock()
        mock_result.id = "result_001"
        mock_result.poc_name = "test_poc"
        mock_result.poc_id = "poc_001"
        mock_result.target = "https://example.com"
        mock_result.vulnerable = False
        mock_result.message = "No vulnerability"
        mock_result.output = ""
        mock_result.error = None
        mock_result.execution_time = 0.5
        mock_result.confidence = 0.5
        mock_result.severity = "info"
        mock_result.cvss_score = 0.0
        mock_result.created_at = datetime.now()
        
        output_path = os.path.join(temp_dir, "test_report.json")
        
        with patch('backend.ai_agents.poc_system.report_generator.POCVerificationResult') as mock_result_model:
            mock_result_model.filter = AsyncMock()
            mock_result_model.filter.return_value.order_by = AsyncMock()
            mock_result_model.filter.return_value.order_by.return_value = [mock_result]
            
            result = await generator.generate_report(
                verification_task=mock_task,
                format="json",
                output_path=output_path
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            assert "report_type" in content


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

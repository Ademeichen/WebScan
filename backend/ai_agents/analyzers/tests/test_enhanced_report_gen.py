"""
测试增强版报告生成器

包含完整的单元测试，验证报告生成功能和AI分析结果集成。
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from ai_agents.analyzers.enhanced_report_gen import (
    EnhancedReportGenerator,
    EnhancedReportData,
    ReportFormat,
    EnvironmentInfo,
    TargetInfo,
    ExecutionTiming,
    NodeExecutionInfo,
    SubgraphExecutionInfo,
    VulnerabilityItem,
    AIResultAnalysis
)
from ai_agents.analyzers.ai_analyzer import (
    AIAnalyzer,
    AIAnalysisResult,
    VulnerabilityCause,
    ExploitationRisk,
    RemediationPriority,
    BusinessImpact
)
from ai_agents.core.state import AgentState


def create_mock_agent_state() -> AgentState:
    """创建模拟的Agent状态用于测试"""
    state = AgentState(
        target="https://test.example.com",
        task_id="test_task_001"
    )
    
    state.tool_results = {
        "crawler": {
            "status": "success",
            "data": {"links": ["https://test.example.com/page1", "https://test.example.com/page2"]}
        },
        "dirscan": {
            "status": "success",
            "data": {"directories": ["/admin", "/config"]}
        }
    }
    
    state.vulnerabilities = [
        {
            "title": "SQL注入漏洞",
            "vuln_type": "sqli",
            "severity": "critical",
            "cve": "CVE-2024-1001",
            "url": "https://test.example.com/login",
            "description": "登录页面存在SQL注入",
            "remediation": "使用参数化查询"
        },
        {
            "title": "XSS漏洞",
            "vuln_type": "xss",
            "severity": "high",
            "url": "https://test.example.com/comment",
            "description": "评论功能存在XSS",
            "remediation": "HTML编码输出"
        }
    ]
    
    state.target_context = {
        "domain": "test.example.com",
        "ip": "192.168.1.100",
        "open_ports": [80, 443],
        "waf": "Cloudflare",
        "cdn": True
    }
    
    state.execution_history = [
        {
            "step_number": 1,
            "task": "baseinfo",
            "status": "success",
            "timestamp": 1710000000.0,
            "timestamp_iso": "2024-03-14T10:00:00",
            "execution_time": 1.5,
            "input_params": {"target": "https://test.example.com"},
            "output_data": {"domain": "test.example.com"},
            "result": {"status": "success"}
        },
        {
            "step_number": 2,
            "task": "crawler",
            "status": "success",
            "timestamp": 1710000002.0,
            "timestamp_iso": "2024-03-14T10:00:02",
            "execution_time": 3.0,
            "input_params": {"depth": 2},
            "output_data": {"links_count": 2},
            "result": {"status": "success"}
        }
    ]
    
    return state


def create_mock_ai_analysis_data() -> Dict[str, Any]:
    """创建模拟的AI分析数据"""
    return {
        "causes": [
            {
                "description": "可能存在输入验证不足，导致SQL注入漏洞",
                "confidence": 0.8,
                "evidence": ["发现critical级SQL注入漏洞"]
            }
        ],
        "risks": [
            {
                "risk_level": "critical",
                "description": "存在严重漏洞，可能导致系统被控制",
                "likelihood": 0.9,
                "impact": "critical"
            }
        ],
        "priorities": [
            {
                "vulnerability_id": "0",
                "vulnerability": "SQL注入漏洞",
                "priority": 1,
                "reason": "critical级漏洞",
                "estimated_effort": "高"
            }
        ],
        "business_impact": {
            "affected_systems": ["test.example.com"],
            "data_risk": "高",
            "downtime_risk": "高",
            "compliance_risk": "高",
            "financial_impact": "高"
        },
        "evidence": ["基于规则的分析"]
    }


class TestEnhancedReportData:
    """测试增强版报告数据类"""
    
    def test_environment_info_creation(self):
        """测试环境信息创建"""
        env_info = EnvironmentInfo(
            os="Windows 11",
            python_version="3.12.0",
            dependencies={"requests": "2.31.0"}
        )
        assert env_info.os == "Windows 11"
        assert env_info.python_version == "3.12.0"
        assert "requests" in env_info.dependencies
    
    def test_target_info_creation(self):
        """测试目标信息创建"""
        target_info = TargetInfo(
            url="https://example.com",
            ip="192.168.1.1",
            domain="example.com",
            ports=[80, 443]
        )
        assert target_info.url == "https://example.com"
        assert 80 in target_info.ports
    
    def test_vulnerability_item_creation(self):
        """测试漏洞项创建"""
        vuln = VulnerabilityItem(
            vuln_name="SQL注入",
            cve_id="CVE-2024-0001",
            severity="critical",
            remediation="使用参数化查询"
        )
        assert vuln.vuln_name == "SQL注入"
        assert vuln.severity == "critical"
    
    def test_ai_result_analysis_creation(self):
        """测试AI结果分析创建"""
        ai_analysis = AIResultAnalysis(
            vulnerability_causes=["输入验证不足"],
            exploitation_risks=["数据泄露"],
            remediation_priorities=[{"vulnerability": "SQL注入", "priority": 1}],
            business_impact="严重影响业务"
        )
        assert len(ai_analysis.vulnerability_causes) == 1
        assert ai_analysis.business_impact == "严重影响业务"


class TestEnhancedReportGenerator:
    """测试增强版报告生成器"""
    
    @pytest.fixture
    def generator(self, tmp_path):
        """创建报告生成器实例"""
        return EnhancedReportGenerator(output_dir=str(tmp_path))
    
    @pytest.fixture
    def mock_state(self):
        """创建模拟的Agent状态"""
        return create_mock_agent_state()
    
    @pytest.fixture
    def mock_ai_data(self):
        """创建模拟的AI分析数据"""
        return create_mock_ai_analysis_data()
    
    def test_generator_initialization(self, generator, tmp_path):
        """测试生成器初始化"""
        assert generator.output_dir == Path(tmp_path)
        assert Path(tmp_path).exists()
    
    def test_collect_environment_info(self, generator):
        """测试环境信息收集"""
        env_info = generator.collect_environment_info()
        assert isinstance(env_info, EnvironmentInfo)
        assert env_info.os != ""
        assert env_info.python_version != ""
    
    @pytest.mark.asyncio
    async def test_generate_from_state(self, generator, mock_state, mock_ai_data):
        """测试从状态生成报告数据"""
        report_data = await generator.generate_from_state(
            mock_state,
            task_name="测试扫描任务",
            ai_analysis_data=mock_ai_data
        )
        
        assert isinstance(report_data, EnhancedReportData)
        assert report_data.task_name == "测试扫描任务"
        assert report_data.task_id == "test_task_001"
        assert len(report_data.vulnerabilities) == 2
        assert len(report_data.ai_analysis.vulnerability_causes) > 0
    
    def test_extract_target_info(self, generator, mock_state):
        """测试目标信息提取"""
        target_info = generator._extract_target_info(mock_state)
        assert isinstance(target_info, TargetInfo)
        assert target_info.url == "https://test.example.com"
        assert target_info.domain == "test.example.com"
        assert 80 in target_info.ports
    
    def test_extract_vulnerabilities(self, generator, mock_state):
        """测试漏洞信息提取"""
        vulnerabilities = generator._extract_vulnerabilities(mock_state)
        assert len(vulnerabilities) == 2
        assert vulnerabilities[0].severity == "critical"
        assert vulnerabilities[1].severity == "high"
    
    @pytest.mark.asyncio
    async def test_generate_json_report(self, generator, mock_state, mock_ai_data):
        """测试JSON报告生成"""
        report_data = await generator.generate_from_state(
            mock_state,
            ai_analysis_data=mock_ai_data
        )
        json_content = generator.generate_json_report(report_data)
        
        assert isinstance(json_content, str)
        parsed = json.loads(json_content)
        assert "ai_analysis" in parsed
        assert "vulnerability_causes" in parsed["ai_analysis"]
    
    @pytest.mark.asyncio
    async def test_generate_html_report(self, generator, mock_state, mock_ai_data):
        """测试HTML报告生成"""
        report_data = await generator.generate_from_state(
            mock_state,
            ai_analysis_data=mock_ai_data
        )
        html_content = generator.generate_html_report(report_data)
        
        assert isinstance(html_content, str)
        assert "<!DOCTYPE html>" in html_content
        assert "AI结果分析" in html_content
    
    @pytest.mark.asyncio
    async def test_save_report_json(self, generator, mock_state, mock_ai_data, tmp_path):
        """测试保存JSON报告"""
        report_data = await generator.generate_from_state(
            mock_state,
            ai_analysis_data=mock_ai_data
        )
        filepath = generator.save_report(report_data, format=ReportFormat.JSON)
        
        assert Path(filepath).exists()
        assert filepath.endswith(".json")
    
    @pytest.mark.asyncio
    async def test_save_report_html(self, generator, mock_state, mock_ai_data, tmp_path):
        """测试保存HTML报告"""
        report_data = await generator.generate_from_state(
            mock_state,
            ai_analysis_data=mock_ai_data
        )
        filepath = generator.save_report(report_data, format=ReportFormat.HTML)
        
        assert Path(filepath).exists()
        assert filepath.endswith(".html")
    
    def test_parse_ai_analysis(self, generator, mock_ai_data):
        """测试AI分析数据解析"""
        ai_analysis = generator._parse_ai_analysis(mock_ai_data)
        assert isinstance(ai_analysis, AIResultAnalysis)
        assert len(ai_analysis.vulnerability_causes) > 0
        assert len(ai_analysis.exploitation_risks) > 0
        assert len(ai_analysis.remediation_priorities) > 0
    
    @pytest.mark.asyncio
    async def test_auto_ai_analysis_integration(self, generator, mock_state):
        """测试自动AI分析集成"""
        report_data = await generator.generate_from_state(
            mock_state,
            task_name="测试自动AI分析"
        )
        
        assert isinstance(report_data, EnhancedReportData)
        assert len(report_data.ai_analysis.vulnerability_causes) > 0
        assert len(report_data.ai_analysis.exploitation_risks) > 0
    
    def test_sync_version(self, generator, mock_state, mock_ai_data):
        """测试同步版本"""
        report_data = generator.generate_from_state_sync(
            mock_state,
            task_name="同步版本测试",
            ai_analysis_data=mock_ai_data
        )
        
        assert isinstance(report_data, EnhancedReportData)
        assert report_data.task_name == "同步版本测试"


class TestAIAnalyzer:
    """测试AI分析器"""
    
    @pytest.fixture
    def ai_analyzer(self):
        """创建AI分析器实例"""
        return AIAnalyzer()
    
    @pytest.fixture
    def mock_vulnerabilities(self):
        """创建模拟漏洞数据"""
        return [
            {
                "title": "SQL注入漏洞",
                "vuln_type": "sqli",
                "severity": "critical"
            },
            {
                "title": "XSS漏洞",
                "vuln_type": "xss",
                "severity": "high"
            }
        ]
    
    @pytest.fixture
    def mock_tool_results(self):
        """创建模拟工具结果"""
        return {
            "crawler": {"status": "success", "data": {"links_count": 10}}
        }
    
    @pytest.fixture
    def mock_target_context(self):
        """创建模拟目标上下文"""
        return {
            "domain": "test.example.com",
            "ip": "192.168.1.1"
        }
    
    def test_analyzer_initialization(self, ai_analyzer):
        """测试分析器初始化"""
        assert isinstance(ai_analyzer, AIAnalyzer)
    
    def test_analyze_with_rules(
        self,
        ai_analyzer,
        mock_vulnerabilities,
        mock_tool_results,
        mock_target_context
    ):
        """测试规则分析"""
        result = ai_analyzer._analyze_with_rules(
            mock_vulnerabilities,
            mock_tool_results,
            mock_target_context
        )
        
        assert isinstance(result, AIAnalysisResult)
        assert len(result.vulnerability_causes) > 0
        assert len(result.exploitation_risks) > 0
        assert len(result.remediation_priorities) > 0
        assert isinstance(result.business_impact, BusinessImpact)
    
    def test_extract_causes_by_rules(self, ai_analyzer, mock_vulnerabilities):
        """测试提取漏洞成因"""
        causes = ai_analyzer._extract_causes_by_rules(mock_vulnerabilities)
        assert len(causes) > 0
        assert all(isinstance(c, VulnerabilityCause) for c in causes)
    
    def test_extract_risks_by_rules(self, ai_analyzer, mock_vulnerabilities):
        """测试提取利用风险"""
        risks = ai_analyzer._extract_risks_by_rules(mock_vulnerabilities)
        assert len(risks) > 0
        assert all(isinstance(r, ExploitationRisk) for r in risks)
    
    def test_extract_priorities_by_rules(self, ai_analyzer, mock_vulnerabilities):
        """测试提取修复优先级"""
        priorities = ai_analyzer._extract_priorities_by_rules(mock_vulnerabilities)
        assert len(priorities) > 0
        assert all(isinstance(p, RemediationPriority) for p in priorities)
        assert priorities[0].priority == 1
    
    def test_extract_business_impact_by_rules(
        self,
        ai_analyzer,
        mock_vulnerabilities,
        mock_target_context
    ):
        """测试提取业务影响"""
        impact = ai_analyzer._extract_business_impact_by_rules(
            mock_vulnerabilities,
            mock_target_context
        )
        assert isinstance(impact, BusinessImpact)
        assert len(impact.affected_systems) > 0
    
    def test_ai_analysis_result_to_dict(self, ai_analyzer):
        """测试AI分析结果转换为字典"""
        result = AIAnalysisResult(
            vulnerability_causes=[
                VulnerabilityCause(description="测试原因", confidence=0.8)
            ],
            exploitation_risks=[
                ExploitationRisk(risk_level="high", description="测试风险")
            ],
            remediation_priorities=[
                RemediationPriority(vulnerability_name="测试漏洞", priority=1)
            ],
            business_impact=BusinessImpact(data_risk="高"),
            analysis_evidence=["测试证据"]
        )
        
        result_dict = result.to_dict()
        assert "causes" in result_dict
        assert "risks" in result_dict
        assert "priorities" in result_dict
        assert "business_impact" in result_dict
        assert "evidence" in result_dict


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path):
        """测试完整工作流：AI分析 -> 报告生成"""
        from ai_agents.analyzers.enhanced_report_gen import EnhancedReportGenerator, ReportFormat
        from ai_agents.analyzers.ai_analyzer import AIAnalyzer
        
        state = create_mock_agent_state()
        generator = EnhancedReportGenerator(output_dir=str(tmp_path))
        ai_analyzer = AIAnalyzer()
        
        ai_result = ai_analyzer._analyze_with_rules(
            state.vulnerabilities,
            state.tool_results,
            state.target_context
        )
        
        report_data = await generator.generate_from_state(
            state,
            task_name="集成测试任务",
            ai_analysis_data=ai_result.to_dict()
        )
        
        json_path = generator.save_report(report_data, format=ReportFormat.JSON)
        html_path = generator.save_report(report_data, format=ReportFormat.HTML)
        
        assert Path(json_path).exists()
        assert Path(html_path).exists()
        
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        assert "ai_analysis" in json_data
        assert "vulnerability_causes" in json_data["ai_analysis"]
        assert "exploitation_risks" in json_data["ai_analysis"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

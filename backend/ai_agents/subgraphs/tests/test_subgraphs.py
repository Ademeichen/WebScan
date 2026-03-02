"""
子图单元测试

测试各子图的核心功能。
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.ai_agents.subgraphs.dto import (
    ScanPlanDTO, ToolExecutionResultDTO, CodeScanResultDTO,
    POCVerificationResultDTO, ReportDTO, TaskStatus, ScanDecisionType
)
from backend.ai_agents.subgraphs.planning import PlanningGraph, PlanningState
from backend.ai_agents.subgraphs.tool_execution import ToolExecutionGraph, ToolExecutionState
from backend.ai_agents.subgraphs.code_scan import CodeScanGraph, CodeScanState
from backend.ai_agents.subgraphs.poc_verification import POCVerificationGraph, POCVerificationState
from backend.ai_agents.subgraphs.report import ReportGraph, ReportState


class TestPlanningGraph:
    """规划图测试"""
    
    @pytest.fixture
    def planning_graph(self):
        return PlanningGraph()
    
    @pytest.fixture
    def planning_state(self):
        return PlanningState(
            target="http://example.com",
            task_id="test-001"
        )
    
    @pytest.mark.asyncio
    async def test_planning_state_creation(self, planning_state):
        """测试规划状态创建"""
        assert planning_state.target == "http://example.com"
        assert planning_state.task_id == "test-001"
        assert planning_state.decision == "fixed_tool"
        assert planning_state.planned_tasks == []
    
    @pytest.mark.asyncio
    async def test_planning_graph_initialization(self, planning_graph):
        """测试规划图初始化"""
        assert planning_graph.max_execution_time == 10.0
        assert planning_graph.env_node is not None
        assert planning_graph.planning_node is not None
        assert planning_graph.decision_node is not None
    
    @pytest.mark.asyncio
    async def test_get_scan_plan_dto(self, planning_graph, planning_state):
        """测试获取扫描计划DTO"""
        planning_state.decision = "fixed_tool"
        planning_state.planned_tasks = ["portscan", "baseinfo"]
        
        dto = planning_graph.get_scan_plan_dto(planning_state)
        
        assert isinstance(dto, ScanPlanDTO)
        assert dto.target == "http://example.com"
        assert dto.decision == ScanDecisionType.FIXED_TOOL
        assert dto.tool_tasks == ["portscan", "baseinfo"]


class TestToolExecutionGraph:
    """工具执行图测试"""
    
    @pytest.fixture
    def tool_graph(self):
        return ToolExecutionGraph(max_execution_time=120.0, max_rounds=50)
    
    @pytest.fixture
    def tool_state(self):
        return ToolExecutionState(
            target="http://example.com",
            task_id="test-002",
            planned_tasks=["portscan"],
            current_task="portscan"
        )
    
    @pytest.mark.asyncio
    async def test_tool_state_creation(self, tool_state):
        """测试工具执行状态创建"""
        assert tool_state.target == "http://example.com"
        assert tool_state.planned_tasks == ["portscan"]
        assert tool_state.current_task == "portscan"
        assert tool_state.retry_count == 0
    
    @pytest.mark.asyncio
    async def test_tool_graph_initialization(self, tool_graph):
        """测试工具执行图初始化"""
        assert tool_graph.max_execution_time == 120.0
        assert tool_graph.max_rounds == 50
        assert tool_graph.execution_node is not None
        assert tool_graph.verification_node is not None
    
    @pytest.mark.asyncio
    async def test_get_result_dto(self, tool_graph, tool_state):
        """测试获取结果DTO"""
        tool_state.completed_tasks = ["portscan"]
        tool_state.tool_results = {"portscan": {"status": "success"}}
        
        dto = tool_graph.get_result_dto(tool_state)
        
        assert isinstance(dto, ToolExecutionResultDTO)
        assert dto.target == "http://example.com"


class TestCodeScanGraph:
    """代码扫描图测试"""
    
    @pytest.fixture
    def code_graph(self):
        return CodeScanGraph(max_execution_time=60.0, max_retries=3)
    
    @pytest.fixture
    def code_state(self):
        return CodeScanState(
            target="http://example.com",
            task_id="test-003",
            need_custom_scan=True,
            custom_scan_type="port_scan"
        )
    
    @pytest.mark.asyncio
    async def test_code_state_creation(self, code_state):
        """测试代码扫描状态创建"""
        assert code_state.target == "http://example.com"
        assert code_state.need_custom_scan == True
        assert code_state.custom_scan_type == "port_scan"
        assert code_state.retry_count == 0
    
    @pytest.mark.asyncio
    async def test_code_graph_initialization(self, code_graph):
        """测试代码扫描图初始化"""
        assert code_graph.max_execution_time == 60.0
        assert code_graph.max_retries == 3
        assert code_graph.code_generation_node is not None
        assert code_graph.code_execution_node is not None
        assert code_graph.capability_enhancement_node is not None


class TestPOCVerificationGraph:
    """POC验证图测试"""
    
    @pytest.fixture
    def poc_graph(self):
        return POCVerificationGraph(max_execution_time=60.0, max_rounds=3)
    
    @pytest.fixture
    def poc_state(self):
        return POCVerificationState(
            target="http://vulnerable.com",
            task_id="test-004",
            poc_tasks=[
                {"poc_name": "poc_test", "target": "http://vulnerable.com", "status": "pending"}
            ]
        )
    
    @pytest.mark.asyncio
    async def test_poc_state_creation(self, poc_state):
        """测试POC验证状态创建"""
        assert poc_state.target == "http://vulnerable.com"
        assert len(poc_state.poc_tasks) == 1
        assert poc_state.round == 0
    
    @pytest.mark.asyncio
    async def test_poc_graph_initialization(self, poc_graph):
        """测试POC验证图初始化"""
        assert poc_graph.max_execution_time == 60.0
        assert poc_graph.max_rounds == 3
        assert poc_graph.execution_node is not None


class TestReportGraph:
    """报告图测试"""
    
    @pytest.fixture
    def report_graph(self):
        return ReportGraph(max_execution_time=30.0)
    
    @pytest.fixture
    def report_state(self):
        return ReportState(
            target="http://example.com",
            task_id="test-005",
            tool_results={"portscan": {"status": "success"}},
            vulnerabilities=[{"cve": "CVE-2021-44228", "severity": "critical"}]
        )
    
    @pytest.mark.asyncio
    async def test_report_state_creation(self, report_state):
        """测试报告状态创建"""
        assert report_state.target == "http://example.com"
        assert len(report_state.vulnerabilities) == 1
        assert report_state.report_format == "json"
    
    @pytest.mark.asyncio
    async def test_report_graph_initialization(self, report_graph):
        """测试报告图初始化"""
        assert report_graph.max_execution_time == 30.0
        assert report_graph.analysis_node is not None
        assert report_graph.generation_node is not None


class TestDTOModels:
    """DTO模型测试"""
    
    def test_scan_plan_dto_creation(self):
        """测试扫描计划DTO创建"""
        dto = ScanPlanDTO(
            target="http://example.com",
            task_id="test-001",
            decision=ScanDecisionType.FIXED_TOOL,
            tool_tasks=["portscan"]
        )
        
        assert dto.target == "http://example.com"
        assert dto.decision == ScanDecisionType.FIXED_TOOL
        assert dto.tool_tasks == ["portscan"]
    
    def test_tool_execution_result_dto_creation(self):
        """测试工具执行结果DTO创建"""
        dto = ToolExecutionResultDTO(
            task_id="test-002",
            target="http://example.com",
            status=TaskStatus.COMPLETED,
            tool_results={"portscan": {"status": "success"}},
            findings=[],
            new_poc_tasks=[],
            awvs_required=False,
            target_context={},
            total_execution_time=5.0
        )
        
        assert dto.status == TaskStatus.COMPLETED
        assert dto.tool_results.get("portscan", {}).get("status") == "success"
    
    def test_report_dto_creation(self):
        """测试报告DTO创建"""
        dto = ReportDTO(
            task_id="test-005",
            target="http://example.com",
            status=TaskStatus.COMPLETED,
            vulnerabilities=[{"cve": "CVE-2021-44228"}],
            summary={"total": 1},
            tool_findings={},
            report_content="{}",
            report_format="json",
            total_execution_time=1.0
        )
        
        assert dto.status == TaskStatus.COMPLETED
        assert len(dto.vulnerabilities) == 1
    
    def test_dto_to_dict(self):
        """测试DTO转换为字典"""
        dto = ScanPlanDTO(
            target="http://example.com",
            task_id="test-001",
            decision=ScanDecisionType.FIXED_TOOL
        )
        
        result = dto.to_dict()
        
        assert isinstance(result, dict)
        assert result["target"] == "http://example.com"
        assert result["decision"] == "fixed_tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

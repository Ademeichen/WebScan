"""
ScanOrchestrator 单元测试

测试扫描编排器的核心功能，包括初始化、各种决策分支、错误处理和超时处理。
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import time

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

from backend.ai_agents.subgraphs.dto import (
    ScanPlanDTO, ToolExecutionResultDTO, CodeScanResultDTO,
    POCVerificationResultDTO, ReportDTO, OrchestratorResultDTO,
    TaskStatus, ScanDecisionType, ToolResultDTO, SeverityLevel
)
from backend.ai_agents.subgraphs.orchestrator import ScanOrchestrator
from backend.ai_agents.subgraphs.planning import PlanningState, PlanningGraph
from backend.ai_agents.subgraphs.tool_execution import ToolExecutionState, ToolExecutionGraph
from backend.ai_agents.subgraphs.code_scan import CodeScanState, CodeScanGraph
from backend.ai_agents.subgraphs.poc_verification import POCVerificationState, POCVerificationGraph
from backend.ai_agents.subgraphs.report import ReportState, ReportGraph


def create_mock_environment_report():
    return {
        "os": "Linux",
        "python_version": "3.10",
        "available_tools": ["portscan", "baseinfo"]
    }


def create_mock_tool_result(tool_name: str, status: str = "success", data: dict = None):
    return {
        "status": status,
        "data": data or {"open_ports": [80, 443]},
        "execution_time": 1.0
    }


@pytest.fixture
def mock_all_services():
    """Mock所有外部服务"""
    with patch('backend.ai_agents.code_execution.environment.EnvironmentAwareness') as mock_env, \
         patch('backend.ai_agents.tools.registry.registry') as mock_registry, \
         patch('backend.ai_agents.code_execution.code_generator.CodeGenerator') as mock_codegen, \
         patch('backend.ai_agents.code_execution.executor.UnifiedExecutor') as mock_executor, \
         patch('backend.ai_agents.code_execution.capability_enhancer.CapabilityEnhancer') as mock_enhancer, \
         patch('backend.ai_agents.agent_config.agent_config') as mock_config:
        
        mock_env.return_value.get_environment_report.return_value = create_mock_environment_report()
        
        async def mock_call_tool(tool_name, target):
            return create_mock_tool_result(tool_name)
        mock_registry.call_tool = AsyncMock(side_effect=mock_call_tool)
        
        mock_codegen.return_value.generate_code = AsyncMock(return_value=Mock(code="print('test')"))
        mock_executor.return_value.execute = AsyncMock(return_value={"status": "success", "output": "ok"})
        mock_enhancer.return_value.enhance_capability = AsyncMock(return_value={"status": "success"})
        
        mock_config.DEFAULT_SCAN_TASKS = ["baseinfo", "portscan"]
        
        yield {
            "env": mock_env,
            "registry": mock_registry,
            "codegen": mock_codegen,
            "executor": mock_executor,
            "enhancer": mock_enhancer,
            "config": mock_config
        }


@pytest.fixture
def orchestrator():
    """创建ScanOrchestrator实例"""
    return ScanOrchestrator(
        planning_timeout=5.0,
        tool_execution_timeout=30.0,
        code_scan_timeout=20.0,
        poc_verification_timeout=20.0,
        report_timeout=10.0
    )


class TestScanOrchestratorInitialization:
    """测试ScanOrchestrator初始化"""
    
    def test_initialization_with_default_timeouts(self):
        """测试使用默认超时设置初始化"""
        orch = ScanOrchestrator()
        
        assert orch.planning_graph.max_execution_time == 10.0
        assert orch.tool_execution_graph.max_execution_time == 120.0
        assert orch.code_scan_graph.max_execution_time == 60.0
        assert orch.poc_verification_graph.max_execution_time == 60.0
        assert orch.report_graph.max_execution_time == 30.0
    
    def test_initialization_with_custom_timeouts(self):
        """测试使用自定义超时设置初始化"""
        orch = ScanOrchestrator(
            planning_timeout=5.0,
            tool_execution_timeout=60.0,
            code_scan_timeout=30.0,
            poc_verification_timeout=30.0,
            report_timeout=15.0
        )
        
        assert orch.planning_graph.max_execution_time == 5.0
        assert orch.tool_execution_graph.max_execution_time == 60.0
        assert orch.code_scan_graph.max_execution_time == 30.0
        assert orch.poc_verification_graph.max_execution_time == 30.0
        assert orch.report_graph.max_execution_time == 15.0
    
    def test_initialization_creates_all_graphs(self, orchestrator):
        """测试初始化创建所有子图"""
        assert isinstance(orchestrator.planning_graph, PlanningGraph)
        assert isinstance(orchestrator.tool_execution_graph, ToolExecutionGraph)
        assert isinstance(orchestrator.code_scan_graph, CodeScanGraph)
        assert isinstance(orchestrator.poc_verification_graph, POCVerificationGraph)
        assert isinstance(orchestrator.report_graph, ReportGraph)


class TestExecuteScanWithFixedTool:
    """测试fixed_tool决策分支"""
    
    @pytest.mark.asyncio
    async def test_execute_scan_fixed_tool_success(self, mock_all_services, orchestrator):
        """测试fixed_tool决策成功执行"""
        result = await orchestrator.execute_scan(
            target="http://example.com",
            task_id="test-001",
            custom_tasks=["portscan"]
        )
        
        assert isinstance(result, OrchestratorResultDTO)
        assert result.task_id == "test-001"
        assert result.target == "http://example.com"
        assert result.status == TaskStatus.COMPLETED
        assert result.scan_plan is not None
        assert result.scan_plan.decision == ScanDecisionType.FIXED_TOOL
    
    @pytest.mark.asyncio
    async def test_execute_scan_fixed_tool_with_custom_tasks(self, mock_all_services):
        """测试使用自定义任务列表"""
        orch = ScanOrchestrator(planning_timeout=5.0, report_timeout=10.0)
        
        result = await orch.execute_scan(
            target="http://custom-tasks.com",
            task_id="test-002",
            custom_tasks=["baseinfo", "portscan"]
        )
        
        assert result.status == TaskStatus.COMPLETED
        assert result.scan_plan is not None


class TestExecuteScanWithPOCVerification:
    """测试poc_verification决策分支"""
    
    @pytest.mark.asyncio
    async def test_execute_scan_poc_verification_success(self, mock_all_services):
        """测试POC验证决策成功执行"""
        mock_all_services["registry"].call_tool = AsyncMock(side_effect=lambda tool, target: {
            "status": "success",
            "data": {"vulnerable": True, "message": "Vulnerability found"} if tool.startswith("poc_") else {"open_ports": [80]}
        })
        
        orch = ScanOrchestrator(
            planning_timeout=5.0,
            poc_verification_timeout=20.0,
            report_timeout=10.0
        )
        
        result = await orch.execute_scan(
            target="http://poc-target.com",
            task_id="poc-test-001",
            target_context={
                "poc_verification_tasks": [
                    {"poc_name": "poc_cve_2021_44228", "target": "http://poc-target.com", "status": "pending"}
                ]
            }
        )
        
        assert result.status == TaskStatus.COMPLETED
        assert result.scan_plan is not None


class TestExecutePlanningOnly:
    """测试execute_planning_only方法"""
    
    @pytest.mark.asyncio
    async def test_execute_planning_only_returns_scan_plan(self, mock_all_services, orchestrator):
        """测试仅执行规划返回扫描计划"""
        result = await orchestrator.execute_planning_only(
            target="http://planning-only.com",
            task_id="planning-001"
        )
        
        assert isinstance(result, ScanPlanDTO)
        assert result.target == "http://planning-only.com"
        assert result.task_id == "planning-001"
        assert isinstance(result.decision, ScanDecisionType)
    
    @pytest.mark.asyncio
    async def test_execute_planning_only_with_context(self, mock_all_services, orchestrator):
        """测试带上下文的规划"""
        result = await orchestrator.execute_planning_only(
            target="http://context-test.com",
            task_id="planning-002",
            target_context={"server": "nginx", "cms": "wordpress"}
        )
        
        assert isinstance(result, ScanPlanDTO)
        assert result.target_context is not None


class TestExecuteToolScanOnly:
    """测试execute_tool_scan_only方法"""
    
    @pytest.mark.asyncio
    async def test_execute_tool_scan_only_success(self, mock_all_services, orchestrator):
        """测试仅执行工具扫描"""
        result = await orchestrator.execute_tool_scan_only(
            target="http://tool-scan.com",
            task_id="tool-001",
            planned_tasks=["portscan"]
        )
        
        assert isinstance(result, ToolExecutionResultDTO)
        assert result.target == "http://tool-scan.com"
        assert result.task_id == "tool-001"
    
    @pytest.mark.asyncio
    async def test_execute_tool_scan_only_empty_tasks(self, mock_all_services, orchestrator):
        """测试空任务列表"""
        result = await orchestrator.execute_tool_scan_only(
            target="http://empty-tasks.com",
            task_id="tool-002",
            planned_tasks=[]
        )
        
        assert isinstance(result, ToolExecutionResultDTO)
        assert result.status == TaskStatus.COMPLETED


class TestErrorHandling:
    """测试错误处理"""
    
    @pytest.mark.asyncio
    async def test_tool_execution_error_propagation(self):
        """测试工具执行错误传播"""
        with patch('backend.ai_agents.tools.registry.registry') as mock_registry:
            mock_registry.call_tool = AsyncMock(side_effect=Exception("Tool error"))
            
            orch = ScanOrchestrator(planning_timeout=5.0, report_timeout=10.0)
            result = await orch.execute_scan(
                target="http://error-test.com",
                task_id="error-001",
                custom_tasks=["portscan"]
            )
            
            assert result.status == TaskStatus.COMPLETED


class TestOrchestratorResultDTO:
    """测试OrchestratorResultDTO"""
    
    def test_result_dto_creation(self):
        """测试结果DTO创建"""
        dto = OrchestratorResultDTO(
            task_id="test-001",
            target="http://test.com",
            status=TaskStatus.COMPLETED,
            total_execution_time=10.0
        )
        
        assert dto.task_id == "test-001"
        assert dto.target == "http://test.com"
        assert dto.status == TaskStatus.COMPLETED
        assert dto.total_execution_time == 10.0
    
    def test_result_dto_to_dict(self):
        """测试结果DTO转换为字典"""
        scan_plan = ScanPlanDTO(
            target="http://test.com",
            task_id="test-001",
            decision=ScanDecisionType.FIXED_TOOL
        )
        
        dto = OrchestratorResultDTO(
            task_id="test-001",
            target="http://test.com",
            status=TaskStatus.COMPLETED,
            scan_plan=scan_plan,
            total_execution_time=10.0
        )
        
        result = dto.to_dict()
        
        assert isinstance(result, dict)
        assert result["task_id"] == "test-001"
        assert result["status"] == "completed"
        assert result["scan_plan"]["decision"] == "fixed_tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

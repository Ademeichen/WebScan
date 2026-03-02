"""
子图集成测试

测试各子图之间的端到端集成，包括数据流、DTO传递和执行时间约束。
仅mock外部服务，不mock内部子图。
"""
import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

from backend.ai_agents.subgraphs.dto import (
    ScanPlanDTO, ToolExecutionResultDTO, CodeScanResultDTO,
    POCVerificationResultDTO, ReportDTO, OrchestratorResultDTO,
    TaskStatus, ScanDecisionType, SeverityLevel, VulnerabilityDTO,
    ToolResultDTO
)
from backend.ai_agents.subgraphs.planning import PlanningGraph, PlanningState
from backend.ai_agents.subgraphs.tool_execution import ToolExecutionGraph, ToolExecutionState
from backend.ai_agents.subgraphs.code_scan import CodeScanGraph, CodeScanState
from backend.ai_agents.subgraphs.poc_verification import POCVerificationGraph, POCVerificationState
from backend.ai_agents.subgraphs.report import ReportGraph, ReportState
from backend.ai_agents.subgraphs.orchestrator import ScanOrchestrator


def create_mock_environment_report():
    return {
        "os": "Linux",
        "python_version": "3.10.0",
        "available_tools": ["nmap", "masscan"],
        "cpu_cores": 8,
        "memory_gb": 16
    }


def create_mock_tool_result(tool_name: str, status: str = "success", data: Dict = None, error: str = None):
    return {
        "status": status,
        "data": data or {"open_ports": [80, 443]},
        "error": error,
        "execution_time": 1.5
    }


@pytest.fixture
def mock_external_services():
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
        mock_registry.get_available_tools = Mock(return_value=["portscan", "baseinfo"])
        
        mock_codegen.return_value.generate_code = AsyncMock(return_value=Mock(code="print('test')"))
        mock_executor.return_value.execute = AsyncMock(return_value={"status": "success", "output": "ok"})
        mock_enhancer.return_value.enhance_capability = AsyncMock(return_value={"status": "success"})
        
        mock_config.DEFAULT_SCAN_TASKS = ["baseinfo", "portscan"]
        mock_config.MAX_EXECUTION_TIME = 300
        mock_config.MAX_RETRIES = 3
        
        yield {
            "env": mock_env,
            "registry": mock_registry,
            "codegen": mock_codegen,
            "executor": mock_executor,
            "enhancer": mock_enhancer,
            "config": mock_config
        }


class TestFullScanWorkflow:
    """测试完整扫描工作流"""
    
    @pytest.mark.asyncio
    async def test_full_scan_workflow_fixed_tool(self, mock_external_services):
        """测试完整扫描工作流 - 固定工具模式"""
        orchestrator = ScanOrchestrator(
            planning_timeout=10.0,
            tool_execution_timeout=120.0,
            report_timeout=30.0
        )
        
        result = await orchestrator.execute_scan(
            target="http://example.com",
            task_id="test-full-001",
            custom_tasks=["portscan", "baseinfo"]
        )
        
        assert isinstance(result, OrchestratorResultDTO)
        assert result.task_id == "test-full-001"
        assert result.target == "http://example.com"
        assert result.status == TaskStatus.COMPLETED
        assert result.scan_plan is not None
        assert result.scan_plan.decision == ScanDecisionType.FIXED_TOOL
        assert result.report is not None
        assert result.total_execution_time >= 0


class TestSubgraphCommunicationViaDTOs:
    """测试子图间通过DTO通信"""
    
    @pytest.fixture
    def mock_tool_registry(self):
        """Mock工具注册表"""
        with patch('backend.ai_agents.tools.registry.registry') as mock_registry:
            mock_registry.call_tool = AsyncMock(return_value=create_mock_tool_result(
                "portscan",
                data={"open_ports": [80, 443, 22], "server": "Apache"}
            ))
            yield mock_registry
    
    @pytest.mark.asyncio
    async def test_planning_to_tool_execution_dto_flow(self, mock_tool_registry):
        """测试PlanningGraph到ToolExecutionGraph的DTO传递"""
        planning_graph = PlanningGraph()
        planning_state = await planning_graph.run(
            target="http://dto-test.com",
            task_id="dto-test-001"
        )
        
        scan_plan_dto = planning_graph.get_scan_plan_dto(planning_state)
        
        assert isinstance(scan_plan_dto, ScanPlanDTO)
        assert scan_plan_dto.target == "http://dto-test.com"
        assert scan_plan_dto.decision == ScanDecisionType.FIXED_TOOL
        assert isinstance(scan_plan_dto.tool_tasks, list)
    
    @pytest.mark.asyncio
    async def test_dto_serialization_deserialization(self):
        """测试DTO序列化和反序列化"""
        scan_plan = ScanPlanDTO(
            target="http://serialize-test.com",
            task_id="serialize-001",
            decision=ScanDecisionType.FIXED_TOOL,
            tool_tasks=["portscan", "baseinfo"],
            target_context={"server": "nginx"}
        )
        
        scan_plan_dict = scan_plan.to_dict()
        assert isinstance(scan_plan_dict, dict)
        assert scan_plan_dict["decision"] == "fixed_tool"
        
        restored_plan = ScanPlanDTO.from_dict(scan_plan_dict)
        assert restored_plan.target == scan_plan.target
        assert restored_plan.decision == ScanDecisionType.FIXED_TOOL
        assert restored_plan.tool_tasks == scan_plan.tool_tasks


class TestErrorPropagationAcrossSubgraphs:
    """测试子图间的错误传播"""
    
    @pytest.mark.asyncio
    async def test_planning_error_propagation(self):
        """测试规划阶段错误传播"""
        with patch('backend.ai_agents.code_execution.environment.EnvironmentAwareness') as mock_env:
            mock_env.return_value.get_environment_report.side_effect = Exception("Environment error")
            
            planning_graph = PlanningGraph()
            planning_state = await planning_graph.run(
                target="http://error-test.com",
                task_id="error-001"
            )
            
            assert len(planning_state.errors) > 0
            assert planning_state.decision == "fixed_tool"
    
    @pytest.mark.asyncio
    async def test_tool_execution_error_propagation(self):
        """测试工具执行阶段错误传播"""
        with patch('backend.ai_agents.tools.registry.registry') as mock_registry:
            mock_registry.call_tool = AsyncMock(side_effect=Exception("Tool execution failed"))
            
            tool_graph = ToolExecutionGraph(max_execution_time=10.0)
            tool_state = ToolExecutionState(
                target="http://tool-error.com",
                task_id="tool-error-001",
                planned_tasks=["portscan"],
                current_task="portscan"
            )
            
            tool_state = await tool_graph.execute(tool_state)
            result = tool_graph.get_result_dto(tool_state)
            
            assert len(tool_state.errors) > 0
            assert result.status == TaskStatus.FAILED


class TestExecutionTimeConstraints:
    """测试执行时间约束"""
    
    @pytest.fixture
    def mock_fast_services(self):
        """Mock快速响应的外部服务"""
        with patch('backend.ai_agents.code_execution.environment.EnvironmentAwareness') as mock_env, \
             patch('backend.ai_agents.tools.registry.registry') as mock_registry, \
             patch('backend.ai_agents.agent_config.agent_config') as mock_config:
            
            mock_env.return_value.get_environment_report.return_value = create_mock_environment_report()
            mock_registry.call_tool = AsyncMock(return_value=create_mock_tool_result("portscan"))
            mock_config.DEFAULT_SCAN_TASKS = ["portscan"]
            
            yield {"registry": mock_registry}
    
    @pytest.mark.asyncio
    async def test_planning_time_constraint(self, mock_fast_services):
        """测试规划时间约束 < 10秒"""
        planning_graph = PlanningGraph()
        
        start_time = time.time()
        await planning_graph.run(
            target="http://timing-test.com",
            task_id="timing-001"
        )
        execution_time = time.time() - start_time
        
        assert execution_time < 10.0
    
    @pytest.mark.asyncio
    async def test_report_time_constraint(self):
        """测试报告生成时间约束 < 30秒"""
        report_graph = ReportGraph(max_execution_time=30.0)
        report_state = ReportState(
            target="http://timing-test.com",
            task_id="timing-002",
            tool_results={"portscan": {"status": "success"}},
            vulnerabilities=[]
        )
        
        start_time = time.time()
        await report_graph.execute(report_state)
        execution_time = time.time() - start_time
        
        assert execution_time < 30.0


class TestDTOValidation:
    """测试DTO验证"""
    
    def test_scan_plan_dto_creation(self):
        """测试扫描计划DTO创建"""
        dto = ScanPlanDTO(
            target="http://test.com",
            task_id="test-001",
            decision=ScanDecisionType.FIXED_TOOL,
            tool_tasks=["portscan"]
        )
        
        assert dto.target == "http://test.com"
        assert dto.decision == ScanDecisionType.FIXED_TOOL
        assert dto.tool_tasks == ["portscan"]
    
    def test_tool_result_dto_creation(self):
        """测试工具结果DTO创建"""
        dto = ToolResultDTO(
            tool_name="portscan",
            status=TaskStatus.COMPLETED,
            data={"open_ports": [80, 443]},
            execution_time=2.5
        )
        
        assert dto.tool_name == "portscan"
        assert dto.status == TaskStatus.COMPLETED
        assert dto.data["open_ports"] == [80, 443]
    
    def test_report_dto_creation(self):
        """测试报告DTO创建"""
        dto = ReportDTO(
            task_id="test-001",
            target="http://test.com",
            status=TaskStatus.COMPLETED,
            vulnerabilities=[],
            summary={"total": 0},
            tool_findings={},
            total_execution_time=5.0
        )
        
        assert dto.status == TaskStatus.COMPLETED
        assert dto.summary == {"total": 0}
    
    def test_poc_verification_result_dto_creation(self):
        """测试POC验证结果DTO创建"""
        dto = POCVerificationResultDTO(
            task_id="poc-001",
            target="http://poc-test.com",
            poc_name="poc_cve_2021_44228",
            status=TaskStatus.COMPLETED,
            vulnerable=True,
            severity=SeverityLevel.CRITICAL,
            cve_id="CVE-2021-44228"
        )
        
        assert dto.task_id == "poc-001"
        assert dto.vulnerable == True
        assert dto.severity == SeverityLevel.CRITICAL


class TestConcurrentExecution:
    """测试并发执行"""
    
    @pytest.fixture
    def mock_concurrent_services(self):
        """Mock并发服务"""
        with patch('backend.ai_agents.code_execution.environment.EnvironmentAwareness') as mock_env, \
             patch('backend.ai_agents.tools.registry.registry') as mock_registry, \
             patch('backend.ai_agents.agent_config.agent_config') as mock_config:
            
            mock_env.return_value.get_environment_report.return_value = create_mock_environment_report()
            mock_registry.call_tool = AsyncMock(return_value=create_mock_tool_result("portscan"))
            mock_config.DEFAULT_SCAN_TASKS = ["portscan"]
            
            yield {"registry": mock_registry}
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self, mock_concurrent_services):
        """测试并发工具执行"""
        tool_graph = ToolExecutionGraph(max_execution_time=60.0, max_rounds=10)
        
        tasks = []
        for i in range(3):
            state = ToolExecutionState(
                target=f"http://concurrent{i}.com",
                task_id=f"concurrent-{i}",
                planned_tasks=["portscan"],
                current_task="portscan"
            )
            tasks.append(tool_graph.execute(state))
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert result.task_id.startswith("concurrent-")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

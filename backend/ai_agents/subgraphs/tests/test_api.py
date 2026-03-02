"""
子图API接口测试

测试各子图的REST API端点。
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

from backend.ai_agents.subgraphs.api import router
from backend.ai_agents.subgraphs.dto import (
    ScanPlanDTO, ToolExecutionResultDTO, CodeScanResultDTO,
    POCVerificationResultDTO, ReportDTO, OrchestratorResultDTO,
    TaskStatus, ScanDecisionType, ToolResultDTO, VulnerabilityDTO, SeverityLevel
)


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_orchestrator():
    with patch('backend.ai_agents.subgraphs.api.orchestrator') as mock:
        yield mock


class TestPlanningEndpoint:
    """测试规划端点"""
    
    def test_planning_success(self, client, mock_orchestrator):
        """测试规划成功"""
        mock_orchestrator.execute_planning_only = AsyncMock(return_value=ScanPlanDTO(
            task_id="test-001",
            target="http://example.com",
            decision=ScanDecisionType.FIXED_TOOL,
            tool_tasks=["portscan", "baseinfo"]
        ))
        
        response = client.post("/subgraphs/planning", json={
            "target": "http://example.com",
            "task_id": "test-001"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["code"] == 200
        assert data["data"]["task_id"] == "test-001"
        assert data["data"]["decision"] == "fixed_tool"
    
    def test_planning_with_context(self, client, mock_orchestrator):
        """测试带上下文的规划"""
        mock_orchestrator.execute_planning_only = AsyncMock(return_value=ScanPlanDTO(
            task_id="test-002",
            target="http://example.com",
            decision=ScanDecisionType.FIXED_TOOL,
            tool_tasks=["portscan"],
            target_context={"server": "nginx"}
        ))
        
        response = client.post("/subgraphs/planning", json={
            "target": "http://example.com",
            "task_id": "test-002",
            "target_context": {"server": "nginx"}
        })
        
        assert response.status_code == 200
        assert response.json()["success"] == True


class TestToolScanEndpoint:
    """测试工具扫描端点"""
    
    def test_tool_scan_success(self, client, mock_orchestrator):
        """测试工具扫描成功"""
        from backend.ai_agents.subgraphs.dto import ToolResultDTO
        
        mock_orchestrator.execute_tool_scan_only = AsyncMock(return_value=ToolExecutionResultDTO(
            task_id="test-003",
            target="http://example.com",
            status=TaskStatus.COMPLETED,
            tool_results=[
                ToolResultDTO(
                    tool_name="portscan",
                    status=TaskStatus.COMPLETED,
                    data={"open_ports": [80, 443]}
                )
            ],
            findings=[],
            total_execution_time=1.5
        ))
        
        response = client.post("/subgraphs/tool-scan", json={
            "target": "http://example.com",
            "task_id": "test-003",
            "planned_tasks": ["portscan"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["task_id"] == "test-003"
        assert data["data"]["status"] == "completed"


class TestFullScanEndpoint:
    """测试完整扫描端点"""
    
    def test_full_scan_success(self, client, mock_orchestrator):
        """测试完整扫描成功"""
        mock_result = OrchestratorResultDTO(
            task_id="test-004",
            target="http://example.com",
            status=TaskStatus.COMPLETED,
            scan_plan=ScanPlanDTO(
                task_id="test-004",
                target="http://example.com",
                decision=ScanDecisionType.FIXED_TOOL
            ),
            report=ReportDTO(
                task_id="test-004",
                target="http://example.com",
                status=TaskStatus.COMPLETED,
                vulnerabilities=[],
                summary={"total": 0},
                tool_findings={}
            ),
            total_execution_time=5.0
        )
        mock_orchestrator.execute_scan = AsyncMock(return_value=mock_result)
        
        response = client.post("/subgraphs/full-scan", json={
            "target": "http://example.com",
            "task_id": "test-004"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["task_id"] == "test-004"
        assert data["data"]["status"] == "completed"
    
    def test_full_scan_with_custom_tasks(self, client, mock_orchestrator):
        """测试带自定义任务的完整扫描"""
        mock_result = OrchestratorResultDTO(
            task_id="test-005",
            target="http://example.com",
            status=TaskStatus.COMPLETED,
            scan_plan=ScanPlanDTO(
                task_id="test-005",
                target="http://example.com",
                decision=ScanDecisionType.FIXED_TOOL,
                tool_tasks=["portscan", "baseinfo"]
            ),
            total_execution_time=3.0
        )
        mock_orchestrator.execute_scan = AsyncMock(return_value=mock_result)
        
        response = client.post("/subgraphs/full-scan", json={
            "target": "http://example.com",
            "task_id": "test-005",
            "custom_tasks": ["portscan", "baseinfo"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["task_id"] == "test-005"


class TestHealthEndpoint:
    """测试健康检查端点"""
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/subgraphs/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "graphs" in data


class TestErrorHandling:
    """测试错误处理"""
    
    def test_planning_error_500(self, client, mock_orchestrator):
        """测试规划错误"""
        mock_orchestrator.execute_planning_only = AsyncMock(side_effect=Exception("Planning error"))
        
        response = client.post("/subgraphs/planning", json={
            "target": "http://example.com",
            "task_id": "test-error"
        })
        
        data = response.json()
        assert data["success"] == False
        assert data["code"] == 500
    
    def test_full_scan_error_500(self, client, mock_orchestrator):
        """测试完整扫描错误"""
        mock_orchestrator.execute_scan = AsyncMock(side_effect=Exception("Scan error"))
        
        response = client.post("/subgraphs/full-scan", json={
            "target": "http://example.com",
            "task_id": "test-error"
        })
        
        data = response.json()
        assert data["success"] == False
        assert data["code"] == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

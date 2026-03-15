"""
完整测试机制框架 - 单元测试、集成测试、端到端测试
"""
import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from backend.ai_agents.core.state import AgentState
from backend.ai_agents.core.graph import ScanAgentGraph, create_agent_graph, initialize_tools
from backend.ai_agents.agent_config import agent_config


class TestUnitTests:
    """单元测试 - 测试各个独立函数和类"""
    
    def test_agent_state_creation(self):
        """测试AgentState创建"""
        state = AgentState(
            task_id="test-001",
            target="http://example.com"
        )
        assert state.task_id == "test-001"
        assert state.target == "http://example.com"
        assert state.planned_tasks == []
        assert state.completed_tasks == []
        assert state.vulnerabilities == []
    
    def test_agent_state_update(self):
        """测试AgentState状态更新"""
        state = AgentState(
            task_id="test-002",
            target="http://example.com"
        )
        state.planned_tasks.append("baseinfo")
        state.completed_tasks.append("baseinfo")
        state.vulnerabilities.append({"type": "test", "severity": "medium"})
        
        assert len(state.planned_tasks) == 1
        assert len(state.completed_tasks) == 1
        assert len(state.vulnerabilities) == 1
    
    def test_agent_state_context(self):
        """测试AgentState上下文管理"""
        state = AgentState(
            task_id="test-003",
            target="http://example.com"
        )
        state.target_context["key1"] = "value1"
        state.target_context["key2"] = {"nested": "value2"}
        
        assert state.target_context["key1"] == "value1"
        assert state.target_context["key2"]["nested"] == "value2"


class TestNodeUnitTests:
    """节点单元测试"""
    
    @pytest.mark.asyncio
    async def test_graph_creation(self):
        """测试图创建"""
        graph = ScanAgentGraph()
        assert graph is not None
        assert graph.graph is not None
    
    def test_subgraph_creation(self):
        """测试子图创建"""
        graph = ScanAgentGraph()
        
        info_graph = graph.get_info_collection_graph()
        assert info_graph is not None
        
        scan_graph = graph.get_vulnerability_scan_graph()
        assert scan_graph is not None
        
        analysis_graph = graph.get_result_analysis_graph()
        assert analysis_graph is not None


class TestIntegrationTests:
    """集成测试 - 测试模块间交互"""
    
    @pytest.fixture
    def sample_state(self):
        """创建样本状态fixture"""
        return AgentState(
            task_id=f"integration-test-{int(time.time())}",
            target="http://example.com"
        )
    
    @pytest.mark.asyncio
    async def test_state_flow_between_nodes(self, sample_state):
        """测试状态在节点间的流转"""
        state = sample_state
        state.planned_tasks = ["baseinfo"]
        
        initial_tasks = len(state.planned_tasks)
        state.completed_tasks.append(state.planned_tasks.pop(0))
        
        assert len(state.planned_tasks) == initial_tasks - 1
        assert len(state.completed_tasks) == 1
    
    @pytest.mark.asyncio
    async def test_tool_results_storage(self, sample_state):
        """测试工具结果存储"""
        state = sample_state
        
        tool_result = {
            "status": "success",
            "data": {"key": "value"},
            "duration": 1.5
        }
        
        state.tool_results["baseinfo"] = tool_result
        
        assert "baseinfo" in state.tool_results
        assert state.tool_results["baseinfo"]["status"] == "success"
        assert state.tool_results["baseinfo"]["duration"] == 1.5


class TestEndToEndTests:
    """端到端测试 - 测试完整工作流"""
    
    @pytest.fixture
    def e2e_state(self):
        """创建端到端测试状态"""
        return AgentState(
            task_id=f"e2e-test-{int(time.time())}",
            target="http://example.com"
        )
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_complete_workflow_simulation(self, e2e_state):
        """模拟完整工作流执行"""
        state = e2e_state
        
        state.planned_tasks = ["baseinfo", "waf_detect", "cms_identify"]
        
        for task in list(state.planned_tasks):
            await asyncio.sleep(0.1)
            state.tool_results[task] = {
                "status": "success",
                "data": {"task": task},
                "timestamp": datetime.now().isoformat()
            }
            state.completed_tasks.append(state.planned_tasks.pop(0))
        
        assert len(state.planned_tasks) == 0
        assert len(state.completed_tasks) == 3
        assert len(state.tool_results) == 3


class TestErrorHandling:
    """异常场景测试"""
    
    @pytest.fixture
    def error_state(self):
        """创建错误测试状态"""
        return AgentState(
            task_id=f"error-test-{int(time.time())}",
            target="http://invalid-url-that-does-not-exist.com"
        )
    
    def test_error_handling_in_state(self, error_state):
        """测试状态中的错误处理"""
        state = error_state
        
        error_info = {
            "node": "tool_execution",
            "error": "Connection refused",
            "timestamp": datetime.now().isoformat()
        }
        
        state.errors.append(error_info)
        
        assert len(state.errors) == 1
        assert state.errors[0]["node"] == "tool_execution"
        assert state.errors[0]["error"] == "Connection refused"
    
    def test_multiple_errors_handling(self, error_state):
        """测试多个错误的处理"""
        state = error_state
        
        for i in range(3):
            state.errors.append({
                "node": f"node-{i}",
                "error": f"Error {i}",
                "timestamp": datetime.now().isoformat()
            })
        
        assert len(state.errors) == 3


class TestBoundaryConditions:
    """边界条件测试"""
    
    def test_empty_target(self):
        """测试空目标"""
        state = AgentState(
            task_id="boundary-test-001",
            target=""
        )
        assert state.target == ""
    
    def test_very_long_task_id(self):
        """测试超长任务ID"""
        long_id = "a" * 1000
        state = AgentState(
            task_id=long_id,
            target="http://example.com"
        )
        assert state.task_id == long_id
    
    def test_large_number_of_tasks(self):
        """测试大量任务"""
        state = AgentState(
            task_id="boundary-test-002",
            target="http://example.com"
        )
        
        state.planned_tasks = [f"task-{i}" for i in range(1000)]
        assert len(state.planned_tasks) == 1000


class TestToolInitialization:
    """工具初始化测试"""
    
    def test_agent_config_exists(self):
        """测试代理配置存在"""
        assert agent_config is not None
    
    def test_graph_creation_function(self):
        """测试图创建函数"""
        graph = create_agent_graph()
        assert graph is not None
        assert isinstance(graph, ScanAgentGraph)


class TestPerformanceBaseline:
    """性能基准测试"""
    
    @pytest.mark.slow
    def test_state_creation_performance(self):
        """测试状态创建性能"""
        start_time = time.time()
        
        for i in range(1000):
            AgentState(
                task_id=f"perf-test-{i}",
                target="http://example.com"
            )
        
        duration = time.time() - start_time
        assert duration < 5.0, f"状态创建过慢: {duration:.2f}秒"
    
    @pytest.mark.slow
    def test_graph_creation_performance(self):
        """测试图创建性能"""
        start_time = time.time()
        
        for i in range(100):
            ScanAgentGraph()
        
        duration = time.time() - start_time
        assert duration < 10.0, f"图创建过慢: {duration:.2f}秒"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

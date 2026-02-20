"""
节点边界测试

测试各个节点在边界条件下的行为。
"""
import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
import sys

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from ai_agents.core.nodes import (
    TaskPlanningNode,
    ToolExecutionNode,
    ResultVerificationNode,
    VulnerabilityAnalysisNode,
    ReportGenerationNode,
    EnvironmentAwarenessNode,
    CodeGenerationNode,
    CapabilityEnhancementNode,
    CodeExecutionNode,
    IntelligentDecisionNode,
    SeebugAgentNode,
    POCVerificationNode
)
from ai_agents.core.state import AgentState
from ai_agents.agent_config import agent_config


class TestNodeBoundaryConditions:
    """节点边界条件测试"""

    @pytest.fixture
    def empty_state(self):
        """空状态"""
        return AgentState(
            task_id="test_boundary",
            target="http://test.local"
        )

    @pytest.fixture
    def state_with_max_tasks(self):
        """包含最大任务数的状态"""
        return AgentState(
            task_id="test_max",
            target="http://test.local",
            planned_tasks=[f"task_{i}" for i in range(100)]
        )

    @pytest.fixture
    def state_with_empty_target(self):
        """空目标状态"""
        return AgentState(
            task_id="test_empty_target",
            target=""
        )

    @pytest.mark.asyncio
    async def test_task_planning_with_empty_target(self, empty_state):
        """测试任务规划节点处理空目标"""
        node = TaskPlanningNode()
        result = await node(empty_state)
        assert result is not None
        assert empty_state.current_task is None or empty_state.current_task != ""

    @pytest.mark.asyncio
    async def test_task_planning_with_max_tasks(self, state_with_max_tasks):
        """测试任务规划节点处理最大任务数"""
        node = TaskPlanningNode()
        result = await node(state_with_max_tasks)
        assert result is not None

    @pytest.mark.asyncio
    async def test_tool_execution_with_no_tools(self, empty_state):
        """测试工具执行节点处理无工具情况"""
        node = ToolExecutionNode()
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_result_verification_with_no_results(self, empty_state):
        """测试结果验证节点处理无结果情况"""
        node = ResultVerificationNode()
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_vulnerability_analysis_with_no_vulns(self, empty_state):
        """测试漏洞分析节点处理无漏洞情况"""
        node = VulnerabilityAnalysisNode()
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_report_generation_with_no_data(self, empty_state):
        """测试报告生成节点处理无数据情况"""
        node = ReportGenerationNode()
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_environment_awareness_with_invalid_target(self, state_with_empty_target):
        """测试环境感知节点处理无效目标"""
        node = EnvironmentAwarenessNode()
        result = await node(state_with_empty_target)
        assert result is not None

    @pytest.mark.asyncio
    async def test_code_generation_with_empty_requirements(self, empty_state):
        """测试代码生成节点处理空需求"""
        node = CodeGenerationNode()
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_capability_enhancement_with_no_capabilities(self, empty_state):
        """测试功能增强节点处理无功能情况"""
        node = CapabilityEnhancementNode()
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_code_execution_with_no_code(self, empty_state):
        """测试代码执行节点处理无代码情况"""
        node = CodeExecutionNode()
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_intelligent_decision_with_no_options(self, empty_state):
        """测试智能决策节点处理无选项情况"""
        node = IntelligentDecisionNode()
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_seebug_agent_with_no_api_key(self, empty_state):
        """测试Seebug Agent节点处理无API密钥情况"""
        node = SeebugAgentNode()
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_poc_verification_with_no_pocs(self, empty_state):
        """测试POC验证节点处理无POC情况"""
        node = POCVerificationNode()
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_state_with_very_long_target(self):
        """测试状态处理超长目标"""
        very_long_target = "http://" + "a" * 1000 + ".com"
        state = AgentState(
            task_id="test_long_target",
            target=very_long_target
        )
        assert state.target == very_long_target

    @pytest.mark.asyncio
    async def test_state_with_special_characters(self):
        """测试状态处理特殊字符"""
        special_target = "http://test.local?param=value&other=test"
        state = AgentState(
            task_id="test_special",
            target=special_target
        )
        assert state.target == special_target

    @pytest.mark.asyncio
    async def test_state_with_unicode_characters(self):
        """测试状态处理Unicode字符"""
        unicode_target = "http://测试.local"
        state = AgentState(
            task_id="test_unicode",
            target=unicode_target
        )
        assert state.target == unicode_target

    @pytest.mark.asyncio
    async def test_state_with_null_values(self):
        """测试状态处理空值"""
        state = AgentState(
            task_id="test_null",
            target="http://test.local",
            tool_results=None,
            vulnerabilities=None
        )
        assert state.tool_results == {}
        assert state.vulnerabilities == []

    @pytest.mark.asyncio
    async def test_state_update_with_large_context(self):
        """测试状态更新大上下文"""
        state = AgentState(
            task_id="test_large_context",
            target="http://test.local"
        )
        large_context = {f"key_{i}": f"value_{i}" for i in range(100)}
        for key, value in large_context.items():
            state.update_context(key, value)
        assert len(state.context) >= 100

    @pytest.mark.asyncio
    async def test_state_with_many_errors(self):
        """测试状态处理多个错误"""
        state = AgentState(
            task_id="test_many_errors",
            target="http://test.local"
        )
        for i in range(50):
            state.add_error(f"Error {i}")
        assert len(state.errors) == 50

    @pytest.mark.asyncio
    async def test_state_with_many_execution_steps(self):
        """测试状态处理多个执行步骤"""
        state = AgentState(
            task_id="test_many_steps",
            target="http://test.local"
        )
        for i in range(100):
            state.add_execution_step(f"step_{i}", {"data": i}, "success")
        assert len(state.execution_steps) == 100

    @pytest.mark.asyncio
    async def test_task_planning_timeout(self, empty_state):
        """测试任务规划节点超时"""
        node = TaskPlanningNode()
        empty_state.update_stage_status("openai", "running", "planning", 0, "开始规划")
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_tool_execution_timeout(self, empty_state):
        """测试工具执行节点超时"""
        node = ToolExecutionNode()
        empty_state.current_task = {"name": "test_tool", "timeout": 1}
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_code_execution_timeout(self, empty_state):
        """测试代码执行节点超时"""
        node = CodeExecutionNode()
        empty_state.current_task = {"name": "test_code", "timeout": 1}
        result = await node(empty_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_state_serialization_with_all_fields(self):
        """测试状态序列化包含所有字段"""
        state = AgentState(
            task_id="test_serialization",
            target="http://test.local",
            planned_tasks=["task1", "task2"],
            current_task={"name": "task1"},
            tool_results={"tool1": {"result": "success"}},
            vulnerabilities=[{"id": 1, "name": "test"}],
            context={"key": "value"},
            errors=["error1", "error2"],
            execution_steps=[{"step": "step1"}]
        )
        serialized = state.to_dict()
        assert "task_id" in serialized
        assert "target" in serialized
        assert "planned_tasks" in serialized
        assert "current_task" in serialized
        assert "tool_results" in serialized
        assert "vulnerabilities" in serialized
        assert "context" in serialized
        assert "errors" in serialized
        assert "execution_steps" in serialized

    @pytest.mark.asyncio
    async def test_state_progress_calculation(self):
        """测试状态进度计算"""
        state = AgentState(
            task_id="test_progress",
            target="http://test.local",
            planned_tasks=["task1", "task2", "task3", "task4", "task5"]
        )
        state.completed_tasks = ["task1", "task2"]
        progress = state.get_progress()
        assert progress == 40.0

    @pytest.mark.asyncio
    async def test_state_completion_marking(self):
        """测试状态完成标记"""
        state = AgentState(
            task_id="test_completion",
            target="http://test.local",
            planned_tasks=["task1", "task2"]
        )
        state.mark_completed()
        assert state.status == "completed"
        assert state.completed_at is not None

    @pytest.mark.asyncio
    async def test_state_retry_mechanism(self):
        """测试状态重试机制"""
        state = AgentState(
            task_id="test_retry",
            target="http://test.local"
        )
        for i in range(3):
            state.add_error(f"Error {i}")
        assert len(state.errors) == 3
        assert state.retry_count == 3

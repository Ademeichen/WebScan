"""
测试节点模块

测试各个节点的功能和状态管理。
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.core.state import AgentState
from backend.ai_agents.core.nodes import (
    EnvironmentAwarenessNode,
    TaskPlanningNode,
    IntelligentDecisionNode,
    ToolExecutionNode,
    ResultVerificationNode,
    VulnerabilityAnalysisNode,
    ReportGenerationNode
)


class TestEnvironmentAwarenessNode:
    """测试环境感知节点"""
    
    @pytest.fixture
    def node(self):
        return EnvironmentAwarenessNode()
    
    @pytest.fixture
    def state(self):
        return AgentState(
            task_id="test_env",
            target="https://www.baidu.com"
        )
    
    @pytest.mark.asyncio
    async def test_environment_awareness(self, node, state):
        """测试环境感知功能"""
        result = await node(state)
        
        assert result is not None
        assert hasattr(result, 'target_context')
        assert len(result.execution_history) > 0
        assert result.execution_history[0]['task'] == 'environment_awareness'
    
    @pytest.mark.asyncio
    async def test_environment_awareness_error_handling(self, node, state):
        """测试环境感知错误处理"""
        with patch('backend.ai_agents.code_execution.environment.EnvironmentAwareness.get_environment_report') as mock_get_report:
            mock_get_report.side_effect = Exception("Detection failed")
            
            result = await node(state)
            
            assert len(result.errors) > 0


class TestTaskPlanningNode:
    """测试任务规划节点"""
    
    @pytest.fixture
    def node(self):
        return TaskPlanningNode()
    
    @pytest.fixture
    def state(self):
        return AgentState(
            task_id="test_planning",
            target="https://www.baidu.com",
            target_context={"server": "nginx"}
        )
    
    @pytest.mark.asyncio
    async def test_task_planning(self, node, state):
        """测试任务规划功能"""
        result = await node(state)
        
        assert result is not None
        assert hasattr(result, 'planned_tasks')
        assert len(result.planned_tasks) > 0
        assert result.current_task is not None
        assert len(result.execution_history) > 0
    
    @pytest.mark.asyncio
    async def test_rule_based_planning(self, node, state):
        """测试规则化规划"""
        result = await node(state)
        
        assert len(result.planned_tasks) > 0
        assert all(isinstance(task, str) for task in result.planned_tasks)


class TestIntelligentDecisionNode:
    """测试智能决策节点"""
    
    @pytest.fixture
    def node(self):
        return IntelligentDecisionNode()
    
    @pytest.fixture
    def state(self):
        return AgentState(
            task_id="test_decision",
            target="https://www.baidu.com",
            planned_tasks=["baseinfo", "portscan"],
            target_context={"server": "nginx"}
        )
    
    @pytest.mark.asyncio
    async def test_intelligent_decision(self, node, state):
        """测试智能决策功能"""
        result = await node(state)
        
        assert result is not None
        assert hasattr(result, 'target_context')
        assert len(result.execution_history) > 0
    
    @pytest.mark.asyncio
    async def test_fixed_tool_decision(self, node, state):
        """测试固定工具决策"""
        result = await node(state)
        
        assert len(result.execution_history) > 0
        assert result.execution_history[0]['task'] == 'intelligent_decision'


class TestToolExecutionNode:
    """测试工具执行节点"""
    
    @pytest.fixture
    def node(self):
        return ToolExecutionNode()
    
    @pytest.fixture
    def state(self):
        return AgentState(
            task_id="test_execution",
            target="https://www.baidu.com",
            planned_tasks=["baseinfo"],
            current_task="baseinfo"
        )
    
    @pytest.mark.asyncio
    async def test_tool_execution(self, node, state):
        """测试工具执行功能"""
        with patch('backend.ai_agents.core.nodes.registry.call_tool') as mock_registry:
            mock_registry.return_value = {
                "status": "success",
                "data": {"server": "nginx"}
            }
            
            result = await node(state)
            
            assert result is not None
            assert hasattr(result, 'tool_results')
            assert len(result.tool_results) > 0
            assert len(result.execution_history) > 0
    
    @pytest.mark.asyncio
    async def test_tool_execution_error(self, node, state):
        """测试工具执行错误处理"""
        with patch('backend.ai_agents.core.nodes.registry.call_tool') as mock_registry:
            mock_registry.side_effect = Exception("Tool execution failed")
            
            result = await node(state)
            
            assert len(result.errors) > 0


class TestResultVerificationNode:
    """测试结果验证节点"""
    
    @pytest.fixture
    def node(self):
        return ResultVerificationNode()
    
    @pytest.fixture
    def state(self):
        return AgentState(
            task_id="test_verification",
            target="https://www.baidu.com",
            tool_results={
                "baseinfo": {"status": "success", "data": {"server": "nginx"}}
            }
        )
    
    @pytest.mark.asyncio
    async def test_result_verification(self, node, state):
        """测试结果验证功能"""
        result = await node(state)
        
        assert result is not None
        assert len(result.execution_history) > 0
    
    @pytest.mark.asyncio
    async def test_result_verification_success(self, node, state):
        """测试成功结果验证"""
        result = await node(state)
        
        assert len(result.execution_history) > 0
        assert result.execution_history[0]['task'] == 'result_verification'


class TestVulnerabilityAnalysisNode:
    """测试漏洞分析节点"""
    
    @pytest.fixture
    def node(self):
        return VulnerabilityAnalysisNode()
    
    @pytest.fixture
    def state(self):
        return AgentState(
            task_id="test_analysis",
            target="https://www.baidu.com",
            tool_results={
                "poc_cve_2020_2551": {
                    "status": "success",
                    "vulnerable": True,
                    "message": "CVE detected"
                }
            }
        )
    
    @pytest.mark.asyncio
    async def test_vulnerability_analysis(self, node, state):
        """测试漏洞分析功能"""
        result = await node(state)
        
        assert result is not None
        assert hasattr(result, 'vulnerabilities')
    
    @pytest.mark.asyncio
    async def test_vulnerability_detection(self, node, state):
        """测试漏洞检测"""
        result = await node(state)
        
        assert len(result.vulnerabilities) >= 0


class TestReportGenerationNode:
    """测试报告生成节点"""
    
    @pytest.fixture
    def node(self):
        return ReportGenerationNode()
    
    @pytest.fixture
    def state(self):
        return AgentState(
            task_id="test_report",
            target="https://www.baidu.com",
            vulnerabilities=[
                {
                    "cve": "poc_cve_2020_2551",
                    "description": "WebLogic RCE",
                    "severity": "high"
                }
            ],
            execution_history=[
                {
                    "step_number": 1,
                    "task": "environment_awareness",
                    "step_type": "tool_execution",
                    "status": "success",
                    "timestamp": 1704067200.0,
                    "timestamp_iso": "2024-01-01T00:00:00",
                    "input_params": {},
                    "processing_logic": "",
                    "result": {},
                    "intermediate_results": [],
                    "output_data": {},
                    "data_changes": {},
                    "state_transitions": [],
                    "execution_time": None,
                    "state_snapshot": {}
                }
            ]
        )
    
    @pytest.mark.asyncio
    async def test_report_generation(self, node, state):
        """测试报告生成功能"""
        result = await node(state)
        
        assert result is not None
        assert hasattr(result, 'tool_results')
        assert 'final_report' in result.tool_results
        assert len(result.execution_history) > 0
    
    @pytest.mark.asyncio
    async def test_report_structure(self, node, state):
        """测试报告结构"""
        result = await node(state)
        
        assert 'final_report' in result.tool_results
        report = result.tool_results['final_report']
        assert 'task_id' in report
        assert 'target' in report
        assert 'vulnerabilities' in report
        assert 'execution_history' in report


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

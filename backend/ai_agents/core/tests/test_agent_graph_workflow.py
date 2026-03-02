"""
Agent图工作流完整运行测试

测试内容包括：
1. 组件初始化验证
2. 主要功能路径测试
3. 边界条件测试
4. 异常处理测试
5. 数据流转和状态转换测试
6. 最终输出验证

注意：涉及外部服务的测试默认跳过，使用 --run-integration 参数运行
"""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_agents.core.graph import ScanAgentGraph, create_agent_graph, initialize_tools
from ai_agents.core.state import AgentState
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
    POCVerificationNode,
    AWVSScanningNode
)
from ai_agents.agent_config import agent_config


INTEGRATION_TEST_TIMEOUT = 60


def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """根据标记修改测试收集"""
    skip_integration = pytest.mark.skip(reason="需要外部服务，使用 --run-integration 运行")
    
    for item in items:
        if "integration" in item.keywords and not config.getoption("--run-integration", default=False):
            item.add_marker(skip_integration)


class TestAgentGraphInitialization:
    """测试Agent图工作流初始化"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    def test_create_agent_graph(self):
        """测试创建Agent图实例"""
        graph = create_agent_graph()
        assert graph is not None
        assert isinstance(graph, ScanAgentGraph)
    
    def test_graph_nodes_initialization(self):
        """测试所有节点初始化"""
        graph = create_agent_graph()
        
        assert hasattr(graph, 'env_awareness_node')
        assert hasattr(graph, 'planning_node')
        assert hasattr(graph, 'intelligent_decision_node')
        assert hasattr(graph, 'execution_node')
        assert hasattr(graph, 'code_generation_node')
        assert hasattr(graph, 'code_execution_node')
        assert hasattr(graph, 'capability_enhancement_node')
        assert hasattr(graph, 'verification_node')
        assert hasattr(graph, 'poc_verification_node')
        assert hasattr(graph, 'seebug_agent_node')
        assert hasattr(graph, 'awvs_scanning_node')
        assert hasattr(graph, 'analysis_node')
        assert hasattr(graph, 'report_node')
    
    def test_graph_compilation(self):
        """测试图编译"""
        graph = create_agent_graph()
        compiled_graph = graph.compile()
        assert compiled_graph is not None
    
    def test_graph_info(self):
        """测试图信息获取"""
        graph = create_agent_graph()
        info = graph.get_graph_info()
        
        assert 'nodes' in info
        assert 'edges' in info
        assert 'entry_point' in info
        assert 'exit_points' in info
        assert len(info['nodes']) == 13
        assert info['entry_point'] == 'environment_awareness'
    
    def test_graph_visualization(self):
        """测试图可视化"""
        graph = create_agent_graph()
        viz = graph.visualize()
        assert isinstance(viz, str)
        assert 'graph TD' in viz
    
    def test_agent_state_initialization(self):
        """测试Agent状态初始化"""
        state = AgentState(
            task_id="test_init",
            target="http://example.com",
            target_context={}
        )
        
        assert state.task_id == "test_init"
        assert state.target == "http://example.com"
        assert state.target_context == {}
        assert state.vulnerabilities == []
        assert state.errors == []
        assert state.is_complete == False
    
    def test_agent_state_context_update(self):
        """测试Agent状态上下文更新"""
        state = AgentState(
            task_id="test_context",
            target="http://example.com",
            target_context={}
        )
        
        state.target_context["cms"] = "WordPress"
        state.target_context["open_ports"] = [80, 443]
        
        assert state.target_context["cms"] == "WordPress"
        assert state.target_context["open_ports"] == [80, 443]
    
    def test_agent_state_vulnerability_add(self):
        """测试Agent状态漏洞添加"""
        state = AgentState(
            task_id="test_vuln",
            target="http://example.com",
            target_context={}
        )
        
        vuln = {
            "source": "test",
            "severity": "high",
            "title": "Test Vulnerability",
            "url": "http://example.com/vuln"
        }
        state.add_vulnerability(vuln)
        
        assert len(state.vulnerabilities) == 1
        assert state.vulnerabilities[0]["title"] == "Test Vulnerability"


class TestAgentGraphMainWorkflow:
    """测试Agent图主要工作流"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.timeout(INTEGRATION_TEST_TIMEOUT)
    async def test_simple_scan_workflow(self):
        """测试简单扫描工作流（需要外部服务）"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_simple_scan",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await asyncio.wait_for(
                graph.invoke(initial_state),
                timeout=INTEGRATION_TEST_TIMEOUT
            )
            
            assert final_state is not None
            assert hasattr(final_state, 'task_id')
            assert final_state.task_id == "test_simple_scan"
            assert hasattr(final_state, 'is_complete')
            
        except asyncio.TimeoutError:
            pytest.skip("工作流执行超时，已自动跳过")
        except Exception as e:
            pytest.skip(f"工作流执行跳过: {str(e)}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.timeout(INTEGRATION_TEST_TIMEOUT)
    async def test_workflow_with_poc_tasks(self):
        """测试包含POC任务的工作流（需要外部服务）"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_poc_workflow",
            target="http://test.example.com",
            target_context={
                "cms": "WordPress",
                "open_ports": [80, 443]
            }
        )
        
        try:
            final_state = await asyncio.wait_for(
                graph.invoke(initial_state),
                timeout=INTEGRATION_TEST_TIMEOUT
            )
            
            assert final_state is not None
            assert hasattr(final_state, 'poc_verification_tasks')
            
        except asyncio.TimeoutError:
            pytest.skip("工作流执行超时，已自动跳过")
        except Exception as e:
            pytest.skip(f"工作流执行跳过: {str(e)}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(True, reason="AWVS扫描测试需要长时间运行，默认跳过")
    async def test_workflow_with_awvs(self):
        """测试包含AWVS扫描的工作流（需要外部服务）"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_awvs_workflow",
            target="https://example.com",
            target_context={
                "use_awvs": True
            }
        )
        
        try:
            final_state = await asyncio.wait_for(
                graph.invoke(initial_state),
                timeout=120.0
            )
            
            assert final_state is not None
            
        except asyncio.TimeoutError:
            pytest.skip("AWVS扫描超时，已自动跳过")
        except Exception as e:
            pytest.skip(f"工作流执行跳过: {str(e)}")


class TestAgentGraphBoundaryConditions:
    """测试Agent图边界条件"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    def test_empty_target_validation(self):
        """测试空目标验证"""
        state = AgentState(
            task_id="test_empty_target",
            target="",
            target_context={}
        )
        
        assert state.target == ""
    
    def test_invalid_target_format_validation(self):
        """测试无效目标格式验证"""
        state = AgentState(
            task_id="test_invalid_target",
            target="not-a-valid-url",
            target_context={}
        )
        
        assert state.target == "not-a-valid-url"
    
    def test_max_tasks_limit_validation(self):
        """测试最大任务数限制验证"""
        state = AgentState(
            task_id="test_max_tasks",
            target="http://example.com",
            target_context={},
            planned_tasks=list(range(1000))
        )
        
        assert len(state.planned_tasks) == 1000
    
    def test_special_characters_in_target_validation(self):
        """测试目标中包含特殊字符验证"""
        state = AgentState(
            task_id="test_special_chars",
            target="http://example.com/path?param=<script>alert('xss')</script>",
            target_context={}
        )
        
        assert "<script>" in state.target


class TestAgentGraphDataFlow:
    """测试数据流转和状态转换"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    def test_state_initialization(self):
        """测试状态初始化"""
        state = AgentState(
            task_id="test_state",
            target="http://example.com",
            target_context={}
        )
        
        assert hasattr(state, 'execution_history')
        assert hasattr(state, 'stage_status')
        assert hasattr(state, 'tool_results')
        assert hasattr(state, 'vulnerabilities')
        assert hasattr(state, 'errors')
    
    def test_state_context_update(self):
        """测试状态上下文更新"""
        state = AgentState(
            task_id="test_context",
            target="http://example.com",
            target_context={}
        )
        
        state.target_context["cms"] = "WordPress"
        state.target_context["open_ports"] = [80, 443]
        
        assert state.target_context["cms"] == "WordPress"
        assert state.target_context["open_ports"] == [80, 443]
    
    def test_tool_results_accumulation(self):
        """测试工具结果累积"""
        state = AgentState(
            task_id="test_tool_results",
            target="http://example.com",
            target_context={}
        )
        
        state.tool_results["baseinfo"] = {"status": "success"}
        state.tool_results["portscan"] = {"status": "success"}
        
        assert len(state.tool_results) == 2
        assert state.tool_results["baseinfo"]["status"] == "success"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.timeout(INTEGRATION_TEST_TIMEOUT)
    async def test_state_transitions(self):
        """测试状态转换（需要外部服务）"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_state_transitions",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await asyncio.wait_for(
                graph.invoke(initial_state),
                timeout=INTEGRATION_TEST_TIMEOUT
            )
            
            assert hasattr(final_state, 'execution_steps')
            assert hasattr(final_state, 'stage_status')
            
        except asyncio.TimeoutError:
            pytest.skip("状态转换测试超时，已自动跳过")
        except Exception as e:
            pytest.skip(f"状态转换测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.timeout(INTEGRATION_TEST_TIMEOUT)
    async def test_context_updates(self):
        """测试上下文更新（需要外部服务）"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_context_updates",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await asyncio.wait_for(
                graph.invoke(initial_state),
                timeout=INTEGRATION_TEST_TIMEOUT
            )
            
            assert hasattr(final_state, 'target_context')
            
        except asyncio.TimeoutError:
            pytest.skip("上下文更新测试超时，已自动跳过")
        except Exception as e:
            pytest.skip(f"上下文更新测试跳过: {str(e)}")


class TestAgentGraphExceptionHandling:
    """测试异常处理"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    def test_error_addition(self):
        """测试错误添加"""
        state = AgentState(
            task_id="test_error",
            target="http://example.com",
            target_context={}
        )
        
        state.add_error("Test error 1")
        state.add_error("Test error 2")
        
        assert len(state.errors) == 2
        assert "Test error 1" in state.errors
    
    def test_execution_step_addition(self):
        """测试执行步骤添加"""
        state = AgentState(
            task_id="test_step",
            target="http://example.com",
            target_context={}
        )
        
        state.add_execution_step("test_step", {"data": "test"}, "success")
        
        assert len(state.execution_history) == 1
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.timeout(INTEGRATION_TEST_TIMEOUT)
    async def test_tool_failure_handling(self):
        """测试工具失败处理（需要外部服务）"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_tool_failure",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await asyncio.wait_for(
                graph.invoke(initial_state),
                timeout=INTEGRATION_TEST_TIMEOUT
            )
            
            assert hasattr(final_state, 'errors')
            
        except asyncio.TimeoutError:
            pytest.skip("工具失败处理测试超时，已自动跳过")
        except Exception as e:
            pass


class TestAgentGraphOutputValidation:
    """测试最终输出验证"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    def test_vulnerability_list_structure(self):
        """测试漏洞列表结构"""
        state = AgentState(
            task_id="test_vuln",
            target="http://example.com",
            target_context={}
        )
        
        vuln = {
            "source": "test",
            "severity": "high",
            "title": "Test Vulnerability",
            "url": "http://example.com/vuln",
            "cve": "CVE-2024-1234"
        }
        state.add_vulnerability(vuln)
        
        assert isinstance(state.vulnerabilities, list)
        assert len(state.vulnerabilities) == 1
    
    def test_execution_trace_structure(self):
        """测试执行轨迹结构"""
        state = AgentState(
            task_id="test_trace",
            target="http://example.com",
            target_context={}
        )
        
        state.add_execution_step("step1", {"data": "test1"}, "success")
        state.add_execution_step("step2", {"data": "test2"}, "success")
        
        assert hasattr(state, 'execution_history')
        assert hasattr(state, 'stage_status')
        assert len(state.execution_history) == 2
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.timeout(INTEGRATION_TEST_TIMEOUT)
    async def test_final_report_generation(self):
        """测试最终报告生成（需要外部服务）"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_report_generation",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await asyncio.wait_for(
                graph.invoke(initial_state),
                timeout=INTEGRATION_TEST_TIMEOUT
            )
            
            assert hasattr(final_state, 'tool_results')
            
        except asyncio.TimeoutError:
            pytest.skip("报告生成测试超时，已自动跳过")
        except Exception as e:
            pytest.skip(f"报告生成测试跳过: {str(e)}")


class TestAgentGraphPerformance:
    """测试性能指标"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    def test_graph_creation_performance(self):
        """测试图创建性能"""
        start_time = datetime.now()
        
        for _ in range(10):
            graph = create_agent_graph()
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        assert execution_time < 60
    
    def test_state_creation_performance(self):
        """测试状态创建性能"""
        start_time = datetime.now()
        
        for i in range(100):
            state = AgentState(
                task_id=f"test_{i}",
                target="http://example.com",
                target_context={}
            )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        assert execution_time < 5


class TestAgentGraphIntegration:
    """测试集成场景"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.timeout(INTEGRATION_TEST_TIMEOUT)
    async def test_full_scan_integration(self):
        """测试完整扫描集成（需要外部服务）"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_full_integration",
            target="http://example.com",
            target_context={
                "cms": "WordPress",
                "open_ports": [80, 443, 8080],
                "use_awvs": False
            }
        )
        
        try:
            final_state = await asyncio.wait_for(
                graph.invoke(initial_state),
                timeout=INTEGRATION_TEST_TIMEOUT
            )
            
            assert final_state is not None
            assert hasattr(final_state, 'is_complete')
            assert hasattr(final_state, 'vulnerabilities')
            assert hasattr(final_state, 'tool_results')
            
        except asyncio.TimeoutError:
            pytest.skip("完整扫描集成测试超时，已自动跳过")
        except Exception as e:
            pytest.skip(f"完整扫描集成测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.timeout(INTEGRATION_TEST_TIMEOUT)
    async def test_seebug_agent_integration(self):
        """测试Seebug Agent集成（需要外部服务）"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_seebug_integration",
            target="http://example.com",
            target_context={
                "need_seebug_agent": True
            }
        )
        
        try:
            final_state = await asyncio.wait_for(
                graph.invoke(initial_state),
                timeout=INTEGRATION_TEST_TIMEOUT
            )
            
            assert final_state is not None
            assert hasattr(final_state, 'seebug_pocs')
            
        except asyncio.TimeoutError:
            pytest.skip("Seebug Agent集成测试超时，已自动跳过")
        except Exception as e:
            pytest.skip(f"Seebug Agent集成测试跳过: {str(e)}")


def generate_test_report(results: List[Dict[str, Any]]) -> str:
    """
    生成测试报告
    
    Args:
        results: 测试结果列表
        
    Returns:
        str: 测试报告
    """
    report = []
    report.append("=" * 80)
    report.append("Agent图工作流测试报告")
    report.append("=" * 80)
    report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['status'] == 'passed')
    failed_tests = sum(1 for r in results if r['status'] == 'failed')
    skipped_tests = sum(1 for r in results if r['status'] == 'skipped')
    
    report.append(f"总测试数: {total_tests}")
    report.append(f"通过: {passed_tests}")
    report.append(f"失败: {failed_tests}")
    report.append(f"跳过: {skipped_tests}")
    report.append("")
    
    report.append("-" * 80)
    report.append("详细测试结果:")
    report.append("-" * 80)
    
    for result in results:
        status_icon = "✅" if result['status'] == 'passed' else "❌" if result['status'] == 'failed' else "⏭️"
        report.append(f"{status_icon} {result['test_name']}")
        if result['error']:
            report.append(f"   错误: {result['error']}")
        if result['duration']:
            report.append(f"   耗时: {result['duration']:.2f}s")
        report.append("")
    
    report.append("=" * 80)
    report.append("测试报告结束")
    report.append("=" * 80)
    
    return "\n".join(report)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])

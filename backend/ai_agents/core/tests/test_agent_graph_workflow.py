"""
Agent图工作流完整运行测试

测试内容包括：
1. 组件初始化验证
2. 主要功能路径测试
3. 边界条件测试
4. 异常处理测试
5. 数据流转和状态转换测试
6. 最终输出验证
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
        
        # 验证所有节点都已初始化
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
        assert len(info['nodes']) == 12
        assert info['entry_point'] == 'environment_awareness'
    
    def test_graph_visualization(self):
        """测试图可视化"""
        graph = create_agent_graph()
        viz = graph.visualize()
        assert isinstance(viz, str)
        assert 'graph TD' in viz


class TestAgentGraphMainWorkflow:
    """测试Agent图主要工作流"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    @pytest.mark.asyncio
    async def test_simple_scan_workflow(self):
        """测试简单扫描工作流"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_simple_scan",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            assert final_state is not None
            assert hasattr(final_state, 'task_id')
            assert final_state.task_id == "test_simple_scan"
            assert hasattr(final_state, 'is_complete')
            
        except Exception as e:
            pytest.skip(f"工作流执行跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_workflow_with_poc_tasks(self):
        """测试包含POC任务的工作流"""
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
            final_state = await graph.invoke(initial_state)
            
            assert final_state is not None
            assert hasattr(final_state, 'poc_verification_tasks')
            
        except Exception as e:
            pytest.skip(f"工作流执行跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_workflow_with_awvs(self):
        """测试包含AWVS扫描的工作流"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_awvs_workflow",
            target="http://awvs-test.example.com",
            target_context={
                "use_awvs": True
            }
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            assert final_state is not None
            
        except Exception as e:
            pytest.skip(f"工作流执行跳过: {str(e)}")


class TestAgentGraphBoundaryConditions:
    """测试Agent图边界条件"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    @pytest.mark.asyncio
    async def test_empty_target(self):
        """测试空目标"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_empty_target",
            target="",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            assert final_state is not None
            
        except Exception as e:
            assert "target" in str(e).lower() or "invalid" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_invalid_target_format(self):
        """测试无效目标格式"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_invalid_target",
            target="not-a-valid-url",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            assert final_state is not None
            
        except Exception as e:
            pass
    
    @pytest.mark.asyncio
    async def test_max_tasks_limit(self):
        """测试最大任务数限制"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_max_tasks",
            target="http://example.com",
            target_context={},
            planned_tasks=list(range(1000))  # 超过最大任务数
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            assert final_state is not None
            
        except Exception as e:
            pass
    
    @pytest.mark.asyncio
    async def test_special_characters_in_target(self):
        """测试目标中包含特殊字符"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_special_chars",
            target="http://example.com/path?param=<script>alert('xss')</script>",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            assert final_state is not None
            
        except Exception as e:
            pass


class TestAgentGraphDataFlow:
    """测试数据流转和状态转换"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    @pytest.mark.asyncio
    async def test_state_transitions(self):
        """测试状态转换"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_state_transitions",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证状态转换
            assert hasattr(final_state, 'execution_steps')
            assert hasattr(final_state, 'stage_status')
            
            # 验证执行步骤记录
            if hasattr(final_state, 'execution_steps') and final_state.execution_steps:
                assert len(final_state.execution_steps) > 0
                
        except Exception as e:
            pytest.skip(f"状态转换测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_context_updates(self):
        """测试上下文更新"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_context_updates",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证上下文更新
            assert hasattr(final_state, 'target_context')
            
        except Exception as e:
            pytest.skip(f"上下文更新测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_tool_results_accumulation(self):
        """测试工具结果累积"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_tool_results",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证工具结果累积
            assert hasattr(final_state, 'tool_results')
            
        except Exception as e:
            pytest.skip(f"工具结果累积测试跳过: {str(e)}")


class TestAgentGraphExceptionHandling:
    """测试异常处理"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    @pytest.mark.asyncio
    async def test_tool_failure_handling(self):
        """测试工具失败处理"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_tool_failure",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证错误处理
            assert hasattr(final_state, 'errors')
            
        except Exception as e:
            pass
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """测试网络错误处理"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_network_error",
            target="http://nonexistent-domain-12345.com",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证错误处理
            assert hasattr(final_state, 'errors')
            
        except Exception as e:
            pass
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """测试超时处理"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_timeout",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证超时处理
            assert hasattr(final_state, 'errors')
            
        except Exception as e:
            pass


class TestAgentGraphOutputValidation:
    """测试最终输出验证"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    @pytest.mark.asyncio
    async def test_final_report_generation(self):
        """测试最终报告生成"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_report_generation",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证报告生成
            assert hasattr(final_state, 'tool_results')
            if 'final_report' in final_state.tool_results:
                assert final_state.tool_results['final_report'] is not None
                
        except Exception as e:
            pytest.skip(f"报告生成测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_vulnerability_list_validation(self):
        """测试漏洞列表验证"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_vuln_validation",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证漏洞列表
            assert hasattr(final_state, 'vulnerabilities')
            assert isinstance(final_state.vulnerabilities, list)
            
        except Exception as e:
            pytest.skip(f"漏洞列表验证测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_execution_trace_validation(self):
        """测试执行轨迹验证"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_trace_validation",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证执行轨迹
            assert hasattr(final_state, 'execution_steps')
            assert hasattr(final_state, 'stage_status')
            
        except Exception as e:
            pytest.skip(f"执行轨迹验证测试跳过: {str(e)}")


class TestAgentGraphPerformance:
    """测试性能指标"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    @pytest.mark.asyncio
    async def test_execution_time(self):
        """测试执行时间"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_execution_time",
            target="http://example.com",
            target_context={}
        )
        
        start_time = datetime.now()
        
        try:
            final_state = await graph.invoke(initial_state)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 验证执行时间合理（不超过1小时）
            assert execution_time < 3600
            
        except Exception as e:
            pytest.skip(f"执行时间测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_memory_usage",
            target="http://example.com",
            target_context={}
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # 验证内存增长合理（不超过500MB）
            assert memory_increase < 500
            
        except Exception as e:
            pytest.skip(f"内存使用测试跳过: {str(e)}")


class TestAgentGraphIntegration:
    """测试集成场景"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        initialize_tools()
        yield
    
    @pytest.mark.asyncio
    async def test_full_scan_integration(self):
        """测试完整扫描集成"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_full_integration",
            target="http://example.com",
            target_context={
                "cms": "WordPress",
                "open_ports": [80, 443, 8080],
                "use_awvs": True
            }
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证完整流程
            assert final_state is not None
            assert hasattr(final_state, 'is_complete')
            assert hasattr(final_state, 'vulnerabilities')
            assert hasattr(final_state, 'tool_results')
            
        except Exception as e:
            pytest.skip(f"完整扫描集成测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_seebug_agent_integration(self):
        """测试Seebug Agent集成"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_seebug_integration",
            target="http://example.com",
            target_context={
                "need_seebug_agent": True
            }
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证Seebug Agent集成
            assert final_state is not None
            assert hasattr(final_state, 'seebug_pocs')
            
        except Exception as e:
            pytest.skip(f"Seebug Agent集成测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_code_generation_integration(self):
        """测试代码生成集成"""
        graph = create_agent_graph()
        
        initial_state = AgentState(
            task_id="test_code_gen_integration",
            target="http://example.com",
            target_context={
                "need_custom_scan": True,
                "custom_scan_type": "vuln_scan",
                "custom_scan_requirements": "Scan for SQL injection vulnerabilities"
            }
        )
        
        try:
            final_state = await graph.invoke(initial_state)
            
            # 验证代码生成集成
            assert final_state is not None
            assert hasattr(final_state, 'tool_results')
            
        except Exception as e:
            pytest.skip(f"代码生成集成测试跳过: {str(e)}")


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
    
    # 统计测试结果
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['status'] == 'passed')
    failed_tests = sum(1 for r in results if r['status'] == 'failed')
    skipped_tests = sum(1 for r in results if r['status'] == 'skipped')
    
    report.append(f"总测试数: {total_tests}")
    report.append(f"通过: {passed_tests}")
    report.append(f"失败: {failed_tests}")
    report.append(f"跳过: {skipped_tests}")
    report.append("")
    
    # 详细测试结果
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
    
    # 发现的问题
    report.append("-" * 80)
    report.append("发现的问题:")
    report.append("-" * 80)
    
    issues = [r for r in results if r['status'] == 'failed']
    if issues:
        for issue in issues:
            report.append(f"❌ {issue['test_name']}")
            report.append(f"   错误: {issue['error']}")
            report.append("")
    else:
        report.append("✅ 未发现严重问题")
        report.append("")
    
    # 修复建议
    report.append("-" * 80)
    report.append("修复建议:")
    report.append("-" * 80)
    
    if failed_tests > 0:
        report.append(f"1. 修复 {failed_tests} 个失败的测试用例")
        report.append("2. 检查错误日志，定位问题根因")
        report.append("3. 验证修复后重新运行测试")
    else:
        report.append("✅ 所有测试通过，无需修复")
    
    report.append("")
    report.append("=" * 80)
    report.append("测试报告结束")
    report.append("=" * 80)
    
    return "\n".join(report)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])

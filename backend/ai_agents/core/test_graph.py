"""
测试LangGraph图构建模块

测试 ScanAgentGraph 类的各项功能。
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_agents.core.graph import ScanAgentGraph, create_agent_graph


class TestScanAgentGraph:
    """
    测试扫描Agent图类
    """

    @pytest.fixture
    def agent_graph(self):
        """
        创建Agent图实例
        """
        return ScanAgentGraph()

    def test_initialization(self, agent_graph):
        """
        测试初始化
        """
        assert agent_graph is not None
        assert hasattr(agent_graph, 'graph')
        assert hasattr(agent_graph, 'planning_node')
        assert hasattr(agent_graph, 'execution_node')
        assert hasattr(agent_graph, 'verification_node')
        assert hasattr(agent_graph, 'analysis_node')
        assert hasattr(agent_graph, 'report_node')

    def test_build_graph(self, agent_graph):
        """
        测试构建图
        """
        graph = agent_graph.graph
        assert graph is not None

    def test_compile(self, agent_graph):
        """
        测试编译图
        """
        compiled_graph = agent_graph.compile()
        assert compiled_graph is not None

    def test_get_graph_info(self, agent_graph):
        """
        测试获取图信息
        """
        graph_info = agent_graph.get_graph_info()
        
        assert isinstance(graph_info, dict)
        assert 'nodes' in graph_info
        assert 'edges' in graph_info
        assert 'entry_point' in graph_info
        assert 'exit_points' in graph_info

    def test_graph_info_nodes(self, agent_graph):
        """
        测试图信息中的节点
        """
        graph_info = agent_graph.get_graph_info()
        
        expected_nodes = [
            'task_planning',
            'tool_execution',
            'result_verification',
            'vulnerability_analysis',
            'report_generation'
        ]
        
        for node in expected_nodes:
            assert node in graph_info['nodes']

    def test_graph_info_edges(self, agent_graph):
        """
        测试图信息中的边
        """
        graph_info = agent_graph.get_graph_info()
        
        assert len(graph_info['edges']) > 0
        assert all(isinstance(edge, tuple) and len(edge) == 2 for edge in graph_info['edges'])

    def test_graph_info_entry_point(self, agent_graph):
        """
        测试图信息中的入口点
        """
        graph_info = agent_graph.get_graph_info()
        
        assert graph_info['entry_point'] == 'task_planning'

    def test_graph_info_exit_points(self, agent_graph):
        """
        测试图信息中的出口点
        """
        graph_info = agent_graph.get_graph_info()
        
        assert isinstance(graph_info['exit_points'], list)
        assert len(graph_info['exit_points']) > 0

    def test_visualize(self, agent_graph):
        """
        测试生成图的可视化
        """
        visualization = agent_graph.visualize()
        
        assert isinstance(visualization, str)
        assert 'graph TD' in visualization
        assert '环境感知' in visualization
        assert '任务规划' in visualization
        assert '工具执行' in visualization
        assert '漏洞分析' in visualization
        assert '报告生成' in visualization

    def test_visualize_structure(self, agent_graph):
        """
        测试可视化结构
        """
        visualization = agent_graph.visualize()
        
        assert '-->' in visualization
        assert 'style' in visualization
        assert 'fill:' in visualization

    def test_should_continue_with_tasks(self, agent_graph):
        """
        测试判断是否继续执行（有任务）
        """
        from core.state import AgentState
        
        state = AgentState(
            target='http://example.com',
            task_id='test-001'
        )
        state.planned_tasks = ['task1', 'task2']
        state.current_task = 'task1'
        
        result = agent_graph._should_continue(state)
        
        assert result == 'continue'

    def test_should_continue_complete(self, agent_graph):
        """
        测试判断是否继续执行（已完成）
        """
        from core.state import AgentState
        
        state = AgentState(
            target='http://example.com',
            task_id='test-001'
        )
        state.is_complete = True
        
        result = agent_graph._should_continue(state)
        
        assert result == 'analyze'

    def test_should_continue_no_tasks(self, agent_graph):
        """
        测试判断是否继续执行（无任务）
        """
        from core.state import AgentState
        
        state = AgentState(
            target='http://example.com',
            task_id='test-001'
        )
        state.planned_tasks = []
        
        result = agent_graph._should_continue(state)
        
        assert result == 'analyze'


class TestCreateAgentGraph:
    """
    测试创建Agent图函数
    """

    def test_create_agent_graph(self):
        """
        测试创建Agent图
        """
        agent_graph = create_agent_graph()
        
        assert agent_graph is not None
        assert isinstance(agent_graph, ScanAgentGraph)
        assert hasattr(agent_graph, 'graph')

    def test_create_multiple_agent_graphs(self):
        """
        测试创建多个Agent图实例
        """
        graph1 = create_agent_graph()
        graph2 = create_agent_graph()
        
        assert graph1 is not None
        assert graph2 is not None
        assert graph1 is not graph2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

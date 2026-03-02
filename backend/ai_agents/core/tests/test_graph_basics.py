"""
图基础测试

测试图的基本构建和编译功能。
"""
import sys
import unittest
from pathlib import Path

# 统一导入路径配置
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.core.graph import create_agent_graph


class TestGraphBasics(unittest.TestCase):
    """图基础功能测试"""
    
    def test_graph_creation(self):
        """测试图创建"""
        graph = create_agent_graph()
        
        self.assertIsNotNone(graph)
        self.assertTrue(hasattr(graph, 'env_awareness_node'))
        self.assertTrue(hasattr(graph, 'planning_node'))
        self.assertTrue(hasattr(graph, 'intelligent_decision_node'))
        self.assertTrue(hasattr(graph, 'execution_node'))
        self.assertTrue(hasattr(graph, 'code_generation_node'))
        self.assertTrue(hasattr(graph, 'code_execution_node'))
        self.assertTrue(hasattr(graph, 'capability_enhancement_node'))
        self.assertTrue(hasattr(graph, 'verification_node'))
        self.assertTrue(hasattr(graph, 'analysis_node'))
        self.assertTrue(hasattr(graph, 'report_node'))
    
    def test_graph_info(self):
        """测试图信息获取"""
        graph = create_agent_graph()
        info = graph.get_graph_info()
        
        self.assertIsInstance(info, dict)
        self.assertIn("total_nodes", info)
        self.assertIn("original_nodes", info)
        self.assertIn("new_nodes", info)
        self.assertIn("entry_point", info)
        self.assertIn("nodes", info)
        self.assertIn("edges", info)
        
        self.assertEqual(info["total_nodes"], 13)  # 更新为13个节点
        self.assertEqual(info["entry_point"], "environment_awareness")
        self.assertEqual(len(info["nodes"]), 13)  # 更新为13个节点
    
    def test_graph_compilation(self):
        """测试图编译"""
        graph = create_agent_graph()
        compiled = graph.compile()
        
        self.assertIsNotNone(compiled)
    
    def test_graph_visualization(self):
        """测试图可视化"""
        graph = create_agent_graph()
        viz = graph.visualize()
        
        self.assertIsInstance(viz, str)
        self.assertIn("环境感知", viz)
        self.assertIn("任务规划", viz)
        self.assertIn("智能决策", viz)
        self.assertIn("工具执行", viz)
        self.assertIn("代码生成", viz)
        self.assertIn("代码执行", viz)
        self.assertIn("功能补充", viz)
        self.assertIn("结果验证", viz)
        self.assertIn("漏洞分析", viz)
        self.assertIn("报告生成", viz)


if __name__ == '__main__':
    unittest.main()

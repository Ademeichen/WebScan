"""
图集成测试

测试完整的工作流执行，包括所有10个节点的协同工作。
"""
import unittest
from unittest.mock import Mock, patch

import sys
from pathlib import Path

# 统一导入路径配置
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.core.state import AgentState
from backend.ai_agents.core.graph import create_agent_graph


class TestGraphBuilding(unittest.TestCase):
    """图构建测试"""
    
    def test_graph_initialization(self):
        """测试图初始化"""
        graph = create_agent_graph()
        
        self.assertIsNotNone(graph)
        self.assertIsNotNone(graph.env_awareness_node)
        self.assertIsNotNone(graph.planning_node)
        self.assertIsNotNone(graph.intelligent_decision_node)
        self.assertIsNotNone(graph.execution_node)
        self.assertIsNotNone(graph.code_generation_node)
        self.assertIsNotNone(graph.code_execution_node)
        self.assertIsNotNone(graph.capability_enhancement_node)
        self.assertIsNotNone(graph.verification_node)
        self.assertIsNotNone(graph.analysis_node)
        self.assertIsNotNone(graph.report_node)
    
    def test_graph_info(self):
        """测试图信息获取"""
        graph = create_agent_graph()
        info = graph.get_graph_info()
        
        self.assertEqual(info["total_nodes"], 10)
        self.assertEqual(info["original_nodes"], 5)
        self.assertEqual(info["new_nodes"], 5)
        self.assertEqual(info["entry_point"], "environment_awareness")
        self.assertEqual(len(info["nodes"]), 10)
        self.assertEqual(len(info["edges"]), 14)
    
    def test_graph_compilation(self):
        """测试图编译"""
        graph = create_agent_graph()
        compiled = graph.compile()
        
        self.assertIsNotNone(compiled)
    
    def test_visualization(self):
        """测试图可视化"""
        graph = create_agent_graph()
        viz = graph.visualize()
        
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


class TestFixedToolWorkflow(unittest.TestCase):
    """固定工具扫描流程测试"""
    
    def setUp(self):
        self.graph = create_agent_graph()
        self.initial_state = AgentState(
            task_id="test_fixed_tool",
            target="https://www.baidu.com",
            target_context={}
        )
    
    async def test_fixed_tool_workflow(self):
        """测试固定工具扫描完整流程"""
        # 模拟工具执行结果
        with patch('core.nodes.registry.call_tool') as mock_registry:
            mock_registry.return_value = {
                "status": "success",
                "data": {"server": "nginx"}
            }
            
            final_state = await self.graph.invoke(self.initial_state)
        
        # 验证流程
        self.assertIn("environment_awareness", final_state.execution_history[0]["task"])
        self.assertIn("task_planning", final_state.execution_history[1]["task"])
        self.assertIn("intelligent_decision", final_state.execution_history[2]["task"])
        self.assertIn("tool_execution", final_state.execution_history[3]["task"])
        self.assertIn("result_verification", final_state.execution_history[4]["task"])
        self.assertIn("vulnerability_analysis", final_state.execution_history[5]["task"])
        self.assertIn("report_generation", final_state.execution_history[6]["task"])
        
        # 验证最终状态
        self.assertTrue(final_state.is_complete)
        self.assertEqual(len(final_state.completed_tasks), 1)
    
    async def test_multiple_tools_workflow(self):
        """测试多个工具执行流程"""
        initial_state = AgentState(
            task_id="test_multiple_tools",
            target="https://www.baidu.com",
            target_context={}
        )
        
        with patch('core.nodes.registry.call_tool') as mock_registry:
            # 模拟多个工具执行
            mock_registry.side_effect = [
                {"status": "success", "data": {"server": "nginx"}},
                {"status": "success", "data": {"open_ports": [80, 443]}},
                {"status": "success", "data": {"cms": "WordPress"}}
            ]
            
            final_state = await self.graph.invoke(initial_state)
        
        # 验证多个工具都被执行
        self.assertEqual(len(final_state.completed_tasks), 3)


class TestCodeGenerationWorkflow(unittest.TestCase):
    """代码生成扫描流程测试"""
    
    def setUp(self):
        self.graph = create_agent_graph()
    
    async def test_code_generation_workflow(self):
        """测试代码生成完整流程"""
        initial_state = AgentState(
            task_id="test_code_generation",
            target="https://www.baidu.com",
            target_context={
                "need_custom_scan": True,
                "custom_scan_type": "vuln_scan",
                "custom_scan_requirements": "检测SQL注入漏洞",
                "custom_scan_language": "python"
            }
        )
        
        with patch('core.nodes.CodeGenerator') as mock_generator:
            # 模拟代码生成
            mock_response = Mock()
            mock_response.to_dict.return_value = {
                "code": "import requests\nrequests.get('https://www.baidu.com')",
                "language": "python",
                "explanation": "生成的SQL注入检测代码"
            }
            mock_generator.return_value = mock_response
            
            with patch('core.nodes.UnifiedExecutor') as mock_executor:
                # 模拟代码执行成功
                mock_result = Mock()
                mock_result.to_dict.return_value = {
                    "status": "success",
                    "output": "No SQL injection found"
                }
                mock_result.status = "success"
                mock_executor.return_value = mock_result
                
                final_state = await self.graph.invoke(initial_state)
        
        # 验证流程
        self.assertIn("code_generation", [h["task"] for h in final_state.execution_history])
        self.assertIn("code_execution", [h["task"] for h in final_state.execution_history])
        self.assertIn("result_verification", [h["task"] for h in final_state.execution_history])
        
        # 验证代码生成和执行结果
        self.assertIn("generated_code", final_state.tool_results)
        self.assertIn("code_execution", final_state.tool_results)
        self.assertEqual(final_state.tool_results["code_execution"]["status"], "success")
    
    async def test_code_execution_failure(self):
        """测试代码执行失败触发功能补充"""
        initial_state = AgentState(
            task_id="test_code_failure",
            target="https://www.baidu.com",
            target_context={
                "need_custom_scan": True,
                "custom_scan_type": "vuln_scan"
            }
        )
        
        with patch('core.nodes.CodeGenerator') as mock_generator:
            with patch('core.nodes.UnifiedExecutor') as mock_executor:
                with patch('core.nodes.CapabilityEnhancer') as mock_enhancer:
                    # 模拟代码生成
                    mock_response = Mock()
                    mock_response.to_dict.return_value = {
                        "code": "invalid_code",
                        "language": "python"
                    }
                    mock_generator.return_value = mock_response
                    
                    # 模拟代码执行失败
                    mock_result = Mock()
                    mock_result.to_dict.return_value = {
                        "status": "failed",
                        "error": "ModuleNotFoundError"
                    }
                    mock_result.status = "failed"
                    mock_executor.return_value = mock_result
                    
                    # 模拟功能补充
                    mock_enhance_result = {
                        "success": True,
                        "message": "requests库已安装"
                    }
                    mock_enhancer.return_value = mock_enhance_result
                    
                    final_state = await self.graph.invoke(initial_state)
        
        # 验证功能补充被触发
        self.assertIn("capability_enhancement", [h["task"] for h in final_state.execution_history])
        
        # 验证需要增强标志被设置
        self.assertTrue(final_state.target_context.get("need_capability_enhancement"))


class TestCapabilityEnhancementWorkflow(unittest.TestCase):
    """功能补充流程测试"""
    
    def setUp(self):
        self.graph = create_agent_graph()
    
    async def test_capability_enhancement_workflow(self):
        """测试功能补充完整流程"""
        initial_state = AgentState(
            task_id="test_enhancement",
            target="https://www.baidu.com",
            target_context={
                "need_capability_enhancement": True,
                "capability_requirement": "安装scapy库"
            }
        )
        
        with patch('core.nodes.CapabilityEnhancer') as mock_enhancer:
            # 模拟功能补充
            mock_result = {
                "success": True,
                "message": "scapy库已安装"
            }
            mock_enhancer.return_value = mock_result
            
            with patch('core.nodes.UnifiedExecutor') as mock_executor:
                # 模拟代码执行成功
                mock_result = Mock()
                mock_result.to_dict.return_value = {
                    "status": "success",
                    "output": "Test output"
                }
                mock_result.status = "success"
                mock_executor.return_value = mock_result
                
                final_state = await self.graph.invoke(initial_state)
        
        # 验证功能补充和代码执行都被执行
        self.assertIn("capability_enhancement", [h["task"] for h in final_state.execution_history])
        self.assertIn("code_execution", [h["task"] for h in final_state.execution_history])


class TestDecisionBranching(unittest.TestCase):
    """决策分支测试"""
    
    def setUp(self):
        self.graph = create_agent_graph()
    
    async def test_fixed_tool_branch(self):
        """测试固定工具分支"""
        initial_state = AgentState(
            task_id="test_decision_fixed",
            target="https://www.baidu.com",
            target_context={}
        )
        
        final_state = await self.graph.invoke(initial_state)
        
        # 验证选择了固定工具路径
        tool_execution_found = False
        for history in final_state.execution_history:
            if history["task"] == "tool_execution":
                tool_execution_found = True
                break
        
        self.assertTrue(tool_execution_found)
        self.assertNotIn("code_generation", [h["task"] for h in final_state.execution_history])
    
    async def test_custom_code_branch(self):
        """测试代码生成分支"""
        initial_state = AgentState(
            task_id="test_decision_custom",
            target="https://www.baidu.com",
            target_context={
                "need_custom_scan": True
            }
        )
        
        final_state = await self.graph.invoke(initial_state)
        
        # 验证选择了代码生成路径
        code_generation_found = False
        for history in final_state.execution_history:
            if history["task"] == "code_generation":
                code_generation_found = True
                break
        
        self.assertTrue(code_generation_found)
        self.assertNotIn("tool_execution", [h["task"] for h in final_state.execution_history])
    
    async def test_enhance_first_branch(self):
        """测试先增强分支"""
        initial_state = AgentState(
            task_id="test_decision_enhance",
            target="https://www.baidu.com",
            target_context={
                "need_capability_enhancement": True
            }
        )
        
        final_state = await self.graph.invoke(initial_state)
        
        # 验证选择了功能增强路径
        enhance_found = False
        for history in final_state.execution_history:
            if history["task"] == "capability_enhancement":
                enhance_found = True
                break
        
        self.assertTrue(enhance_found)


class TestErrorHandling(unittest.TestCase):
    """错误处理测试"""
    
    def setUp(self):
        self.graph = create_agent_graph()
    
    async def test_node_error_handling(self):
        """测试节点错误处理"""
        initial_state = AgentState(
            task_id="test_error",
            target="https://www.baidu.com"
        )
        
        with patch('core.nodes.registry.call_tool') as mock_registry:
            # 模拟工具执行失败
            mock_registry.side_effect = Exception("Tool execution failed")
            
            try:
                final_state = await self.graph.invoke(initial_state)
                # 应该捕获错误，但继续执行
                self.assertGreater(len(final_state.errors), 0)
            except Exception as e:
                # 应该抛出异常
                self.assertIn("Tool execution failed", str(e))
    
    async def test_environment_detection_error(self):
        """测试环境检测错误处理"""
        initial_state = AgentState(
            task_id="test_env_error",
            target="https://www.baidu.com"
        )
        
        with patch('core.nodes.EnvironmentAwareness') as mock_env:
            # 模拟环境检测失败
            mock_env.return_value = Mock()
            mock_env.get_environment_report.side_effect = Exception("Detection failed")
            
            try:
                final_state = await self.graph.invoke(initial_state)
                # 应该捕获错误
                self.assertGreater(len(final_state.errors), 0)
            except Exception as e:
                self.assertIn("Detection failed", str(e))


class TestStatePropagation(unittest.TestCase):
    """状态传递测试"""
    
    def setUp(self):
        self.graph = create_agent_graph()
    
    async def test_state_propagation_across_nodes(self):
        """测试状态在节点间正确传递"""
        initial_state = AgentState(
            task_id="test_state_prop",
            target="https://www.baidu.com",
            target_context={"initial_key": "initial_value"}
        )
        
        with patch('core.nodes.registry.call_tool') as mock_registry:
            # 模拟工具执行并更新上下文
            mock_registry.return_value = {
                "status": "success",
                "data": {"server": "updated_server"}
            }
            
            final_state = await self.graph.invoke(initial_state)
        
        # 验证上下文被更新
        self.assertIn("server", final_state.target_context)
        self.assertEqual(final_state.target_context["server"], "updated_server")
    
    async def test_vulnerability_propagation(self):
        """测试漏洞信息在节点间正确传递"""
        initial_state = AgentState(
            task_id="test_vuln_prop",
            target="https://www.baidu.com"
        )
        
        with patch('core.nodes.registry.call_tool') as mock_registry:
            # 模拟POC执行并添加漏洞
            mock_registry.return_value = {
                "status": "success",
                "data": {
                    "vulnerable": True,
                    "message": "CVE detected"
                }
            }
            
            final_state = await self.graph.invoke(initial_state)
        
        # 验证漏洞被添加
        self.assertEqual(len(final_state.vulnerabilities), 1)
        self.assertEqual(final_state.vulnerabilities[0]["cve"], "poc_cve_2020_2551")


class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def test_graph_compilation_performance(self):
        """测试图编译性能"""
        import time
        
        graph = create_agent_graph()
        
        start_time = time.time()
        compiled = graph.compile()
        end_time = time.time()
        
        compilation_time = end_time - start_time
        
        # 编译时间应该小于1秒
        self.assertLess(compilation_time, 1.0)
        print(f"图编译耗时: {compilation_time:.3f}秒")
    
    def test_graph_info_performance(self):
        """测试图信息获取性能"""
        import time
        
        graph = create_agent_graph()
        
        start_time = time.time()
        info = graph.get_graph_info()
        end_time = time.time()
        
        info_time = end_time - start_time
        
        # 获取信息时间应该小于0.1秒
        self.assertLess(info_time, 0.1)
        print(f"图信息获取耗时: {info_time:.3f}秒")


def run_tests():
    """运行所有集成测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestGraphBuilding))
    suite.addTests(loader.loadTestsFromTestCase(TestFixedToolWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeGenerationWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestCapabilityEnhancementWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionBranching))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestStatePropagation))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print("图集成测试结果:")
    print(f"  运行测试: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"{'='*60}\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

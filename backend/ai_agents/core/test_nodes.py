"""
节点单元测试

测试所有10个节点(原有5个 + 新增5个)的功能和异常处理。
"""
import unittest
import sys
from unittest.mock import patch, Mock

from pathlib import Path

# 统一导入路径配置
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.core.state import AgentState
from backend.ai_agents.core.nodes import (
    TaskPlanningNode,
    ToolExecutionNode,
    ResultVerificationNode,
    VulnerabilityAnalysisNode,
    ReportGenerationNode,
    EnvironmentAwarenessNode,
    CodeGenerationNode,
    CapabilityEnhancementNode,
    CodeExecutionNode,
    IntelligentDecisionNode
)


class TestTaskPlanningNode(unittest.TestCase):
    """任务规划节点测试"""
    
    def setUp(self):
        self.node = TaskPlanningNode()
        self.state = AgentState(
            task_id="test_001",
            target="http://example.com"
        )
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.node)
        self.assertIsNotNone(self.node.priority_manager)
    
    @patch('core.nodes.agent_config.ENABLE_LLM_PLANNING', False)
    async def test_rule_based_planning(self):
        """测试规则化规划"""
        state = await self.node(self.state)
        
        self.assertIsNotNone(state.planned_tasks)
        self.assertGreater(len(state.planned_tasks), 0)
        self.assertIn("baseinfo", state.planned_tasks)
        self.assertIn("portscan", state.planned_tasks)
    
    @patch('core.nodes.agent_config.ENABLE_LLM_PLANNING', True)
    @patch('core.nodes.ChatOpenAI')
    @patch('core.nodes.JsonOutputParser')
    async def test_llm_planning(self):
        """测试LLM规划"""
        state = await self.node(self.state)
        
        self.assertIsNotNone(state.planned_tasks)
        self.assertGreater(len(state.planned_tasks), 0)
    
    async def test_planning_with_context(self):
        """测试带上下文的规划"""
        self.state.target_context = {
            "cms": "WordPress",
            "open_ports": [80, 443]
        }
        
        state = await self.node(self.state)
        
        self.assertGreater(len(state.planned_tasks), 5)
    
    async def test_planning_error_handling(self):
        """测试规划异常处理"""
        with patch.object(self.node, '_llm_planning', side_effect=Exception("LLM error")):
            state = await self.node(self.state)
            
            self.assertIsNotNone(state.planned_tasks)
            self.assertGreater(len(state.errors), 0)


class TestToolExecutionNode(unittest.TestCase):
    """工具执行节点测试"""
    
    def setUp(self):
        self.node = ToolExecutionNode()
        self.state = AgentState(
            task_id="test_002",
            target="http://example.com",
            planned_tasks=["baseinfo"],
            current_task="baseinfo"
        )
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.node)
        self.assertIsNotNone(self.node.semaphore)
    
    @patch('core.nodes.registry.call_tool')
    async def test_tool_execution_success(self):
        """测试工具执行成功"""
        mock_result = {
            "status": "success",
            "data": {
                "server": "nginx",
                "os": "Linux"
            }
        }
        
        with patch('core.nodes.registry.call_tool', return_value=mock_result):
            state = await self.node(self.state)
            
            self.assertIn("baseinfo", state.completed_tasks)
            self.assertIn("baseinfo", state.tool_results)
            self.assertEqual(state.current_task, None)
    
    @patch('core.nodes.registry.call_tool')
    async def test_tool_execution_with_retry(self):
        """测试工具执行重试"""
        mock_result = {
            "status": "failed",
            "error": "Timeout"
        }
        
        with patch('core.nodes.registry.call_tool', return_value=mock_result):
            state = await self.node(self.state)
            
            self.assertEqual(state.retry_count, 1)
            self.assertIn("baseinfo", state.planned_tasks)
    
    @patch('core.nodes.registry.call_tool')
    async def test_context_update(self):
        """测试上下文更新"""
        mock_result = {
            "status": "success",
            "data": {
                "server": "Apache",
                "os": "Windows"
            }
        }
        
        with patch('core.nodes.registry.call_tool', return_value=mock_result):
            state = await self.node(self.state)
            
            self.assertEqual(state.target_context.get("server"), "Apache")
            self.assertEqual(state.target_context.get("os"), "Windows")
    
    @patch('core.nodes.registry.call_tool')
    async def test_poc_processing(self):
        """测试POC结果处理"""
        self.state.planned_tasks = ["poc_weblogic_2020_2551"]
        self.state.current_task = "poc_weblogic_2020_2551"
        
        mock_result = {
            "status": "success",
            "data": {
                "vulnerable": True,
                "message": "CVE-2020-2551 detected"
            }
        }
        
        with patch('core.nodes.registry.call_tool', return_value=mock_result):
            state = await self.node(self.state)
            
            self.assertEqual(len(state.vulnerabilities), 1)
            self.assertEqual(state.vulnerabilities[0]["cve"], "weblogic_2020_2551")
            self.assertEqual(state.vulnerabilities[0]["severity"], "critical")


class TestResultVerificationNode(unittest.TestCase):
    """结果验证节点测试"""
    
    def setUp(self):
        self.node = ResultVerificationNode()
        self.state = AgentState(
            task_id="test_003",
            target="http://example.com",
            planned_tasks=["baseinfo", "portscan"],
            completed_tasks=["baseinfo"]
        )
    
    async def test_supplement_poc_tasks(self):
        """测试POC任务补充"""
        self.state.target_context = {
            "cms": "WebLogic",
            "open_ports": [7001]
        }
        
        state = await self.node(self.state)
        
        self.assertGreater(len(state.planned_tasks), 2)
        poc_tasks = [t for t in state.planned_tasks if t.startswith("poc_")]
        self.assertGreater(len(poc_tasks), 0)
    
    async def test_continue_execution(self):
        """测试继续执行"""
        state = await self.node(self.state)
        
        self.assertTrue(state.should_continue)
        self.assertEqual(state.current_task, "portscan")
    
    async def test_all_tasks_complete(self):
        """测试所有任务完成"""
        self.state.planned_tasks = []
        self.state.completed_tasks = ["baseinfo", "portscan"]
        
        state = await self.node(self.state)
        
        self.assertFalse(state.should_continue)
        self.assertIsNone(state.current_task)


class TestVulnerabilityAnalysisNode(unittest.TestCase):
    """漏洞分析节点测试"""
    
    def setUp(self):
        self.node = VulnerabilityAnalysisNode()
        self.state = AgentState(
            task_id="test_004",
            target="http://example.com",
            vulnerabilities=[
                {"cve": "CVE-2020-2551", "severity": "critical"},
                {"cve": "CVE-2021-44228", "severity": "high"},
                {"cve": "CVE-2021-44228", "severity": "high"}
            ]
        )
    
    async def test_deduplication(self):
        """测试去重"""
        state = await self.node(self.state)
        
        self.assertEqual(len(state.vulnerabilities), 2)
        cves = [v["cve"] for v in state.vulnerabilities]
        self.assertEqual(len(cves), len(set(cves)))
    
    async def test_sorting(self):
        """测试排序"""
        state = await self.node(self.state)
        
        severities = [v["severity"] for v in state.vulnerabilities]
        self.assertEqual(severities, ["critical", "high"])
    
    async def test_empty_vulnerabilities(self):
        """测试空漏洞列表"""
        self.state.vulnerabilities = []
        
        state = await self.node(self.state)
        
        self.assertEqual(len(state.vulnerabilities), 0)


class TestReportGenerationNode(unittest.TestCase):
    """报告生成节点测试"""
    
    def setUp(self):
        self.node = ReportGenerationNode()
        self.state = AgentState(
            task_id="test_005",
            target="http://example.com",
            vulnerabilities=[
                {"cve": "CVE-2020-2551", "severity": "critical"}
            ]
        )
    
    @patch('core.nodes.ReportGenerator')
    async def test_report_generation(self):
        """测试报告生成"""
        mock_report = {
            "summary": "Scan completed",
            "vulnerabilities": 1
        }
        
        with patch.object(self.node.report_gen, 'generate_report', return_value=mock_report):
            state = await self.node(self.state)
            
            self.assertIn("final_report", state.tool_results)
            self.assertTrue(state.is_complete)
    
    @patch('core.nodes.ReportGenerator')
    async def test_report_generation_error(self):
        """测试报告生成错误处理"""
        with patch.object(self.node.report_gen, 'generate_report', side_effect=Exception("Report error")):
            state = await self.node(self.state)
            
            self.assertIn("final_report", state.tool_results)
            self.assertTrue(state.is_complete)
            self.assertGreater(len(state.errors), 0)


class TestEnvironmentAwarenessNode(unittest.TestCase):
    """环境感知节点测试(新增)"""
    
    def setUp(self):
        self.node = EnvironmentAwarenessNode()
        self.state = AgentState(
            task_id="test_006",
            target="http://example.com"
        )
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.node)
        self.assertIsNotNone(self.node.env_awareness)
    
    @patch('core.nodes.EnvironmentAwareness')
    async def test_environment_detection(self):
        """测试环境检测"""
        mock_report = {
            "os_info": {
                "system": "Windows",
                "release": "10",
                "version": "19044"
            },
            "python_info": {
                "version": "3.12.3",
                "executable": "python.exe"
            },
            "available_tools": {
                "nmap": {"available": True},
                "sqlmap": {"available": False}
            }
        }
        
        with patch.object(self.node.env_awareness, 'get_environment_report', return_value=mock_report):
            state = await self.node(self.state)
            
            self.assertEqual(state.target_context.get("os_system"), "Windows")
            self.assertEqual(state.target_context.get("python_version"), "3.12.3")
            self.assertIn("nmap", state.target_context.get("available_tools"))
    
    @patch('core.nodes.EnvironmentAwareness')
    async def test_environment_detection_error(self):
        """测试环境检测错误处理"""
        with patch.object(self.node.env_awareness, 'get_environment_report', side_effect=Exception("Detection error")):
            state = await self.node(self.state)
            
            self.assertGreater(len(state.errors), 0)
            self.assertIn("environment_info", state.target_context)


class TestCodeGenerationNode(unittest.TestCase):
    """代码生成节点测试(新增)"""
    
    def setUp(self):
        self.node = CodeGenerationNode()
        self.state = AgentState(
            task_id="test_007",
            target="http://example.com"
        )
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.node)
        self.assertIsNotNone(self.node.code_generator)
    
    @patch('core.nodes.CodeGenerator')
    async def test_code_generation(self):
        """测试代码生成"""
        self.state.target_context = {
            "need_custom_scan": True,
            "custom_scan_type": "vuln_scan",
            "custom_scan_requirements": "检测SQL注入漏洞",
            "custom_scan_language": "python"
        }
        
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "code": "import requests\nprint('test')",
            "language": "python",
            "explanation": "生成的代码"
        }
        
        with patch.object(self.node.code_generator, 'generate_code', return_value=mock_response):
            state = await self.node(self.state)
            
            self.assertIn("generated_code", state.tool_results)
            self.assertIn("generated_code", state.target_context)
    
    @patch('core.nodes.CodeGenerator')
    async def test_skip_code_generation(self):
        """测试跳过代码生成"""
        self.state.target_context = {
            "need_custom_scan": False
        }
        
        state = await self.node(self.state)
        
        self.assertNotIn("generated_code", state.tool_results)
    
    @patch('core.nodes.CodeGenerator')
    async def test_code_generation_error(self):
        """测试代码生成错误处理"""
        with patch.object(self.node.code_generator, 'generate_code', side_effect=Exception("Generation error")):
            state = await self.node(self.state)
            
            self.assertGreater(len(state.errors), 0)


class TestCapabilityEnhancementNode(unittest.TestCase):
    """功能补充节点测试(新增)"""
    
    def setUp(self):
        self.node = CapabilityEnhancementNode()
        self.state = AgentState(
            task_id="test_008",
            target="http://example.com"
        )
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.node)
        self.assertIsNotNone(self.node.capability_enhancer)
    
    @patch('core.nodes.CapabilityEnhancer')
    async def test_capability_enhancement(self):
        """测试功能补充"""
        self.state.target_context = {
            "need_capability_enhancement": True,
            "capability_requirement": "安装requests库"
        }
        
        mock_result = {
            "success": True,
            "message": "requests库已安装"
        }
        
        with patch.object(self.node.capability_enhancer, 'enhance_capability', return_value=mock_result):
            state = await self.node(self.state)
            
            self.assertIn("capability_enhancement", state.tool_results)
            self.assertIn("enhanced_capability", state.target_context)
    
    @patch('core.nodes.CapabilityEnhancer')
    async def test_skip_enhancement(self):
        """测试跳过功能补充"""
        self.state.target_context = {
            "need_capability_enhancement": False
        }
        
        state = await self.node(self.state)
        
        self.assertNotIn("capability_enhancement", state.tool_results)
    
    @patch('core.nodes.CapabilityEnhancer')
    async def test_enhancement_error(self):
        """测试功能补充错误处理"""
        with patch.object(self.node.capability_enhancer, 'enhance_capability', side_effect=Exception("Enhancement error")):
            state = await self.node(self.state)
            
            self.assertGreater(len(state.errors), 0)


class TestCodeExecutionNode(unittest.TestCase):
    """代码执行节点测试(新增)"""
    
    def setUp(self):
        self.node = CodeExecutionNode()
        self.state = AgentState(
            task_id="test_009",
            target="http://example.com"
        )
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.node)
        self.assertIsNotNone(self.node.executor)
    
    @patch('core.nodes.UnifiedExecutor')
    async def test_code_execution(self):
        """测试代码执行"""
        self.state.target_context = {
            "generated_code": {
                "code": "print('test')",
                "language": "python"
            }
        }
        
        mock_result = Mock()
        mock_result.to_dict.return_value = {
            "status": "success",
            "output": "test",
            "error": None
        }
        mock_result.status = "success"
        
        with patch.object(self.node.executor, 'execute_code', return_value=mock_result):
            state = await self.node(self.state)
            
            self.assertIn("code_execution", state.tool_results)
            self.assertIn("code_execution_result", state.target_context)
    
    @patch('core.nodes.UnifiedExecutor')
    async def test_code_execution_failure(self):
        """测试代码执行失败"""
        self.state.target_context = {
            "generated_code": {
                "code": "invalid_code",
                "language": "python"
            }
        }
        
        mock_result = Mock()
        mock_result.to_dict.return_value = {
            "status": "failed",
            "output": None,
            "error": "SyntaxError"
        }
        mock_result.status = "failed"
        
        with patch.object(self.node.executor, 'execute_code', return_value=mock_result):
            state = await self.node(self.state)
            
            self.assertIn("code_execution", state.tool_results)
            self.assertEqual(state.tool_results["code_execution"]["status"], "failed")
    
    @patch('core.nodes.UnifiedExecutor')
    async def test_skip_execution(self):
        """测试跳过代码执行"""
        self.state.target_context = {}
        
        state = await self.node(self.state)
        
        self.assertNotIn("code_execution", state.tool_results)


class TestIntelligentDecisionNode(unittest.TestCase):
    """智能决策节点测试(新增)"""
    
    def setUp(self):
        self.node = IntelligentDecisionNode()
        self.state = AgentState(
            task_id="test_010",
            target="http://example.com"
        )
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.node)
        self.assertIsNotNone(self.node.env_awareness)
    
    @patch('core.nodes.EnvironmentAwareness')
    async def test_decision_fixed_tool(self):
        """测试决策使用固定工具"""
        self.state.target_context = {}
        
        mock_env_info = {
            "os_info": {"system": "Linux"},
            "available_tools": {
                "nmap": {"available": True}
            },
            "network_info": {
                "proxy_detected": False,
                "firewall_detected": False
            }
        }
        
        with patch.object(self.node.env_awareness, 'get_environment_report', return_value=mock_env_info):
            state = await self.node(self.state)
            
            decisions = state.target_context["intelligent_decisions"]
            self.assertIn("使用Bash执行脚本", decisions)
            self.assertIn("使用nmap进行端口扫描", decisions)
    
    @patch('core.nodes.EnvironmentAwareness')
    async def test_decision_custom_code(self):
        """测试决策生成代码"""
        self.state.target_context = {
            "need_custom_scan": True
        }
        
        mock_env_info = {
            "os_info": {"system": "Windows"},
            "available_tools": {},
            "network_info": {}
        }
        
        with patch.object(self.node.env_awareness, 'get_environment_report', return_value=mock_env_info):
            state = await self.node(self.state)
            
            decisions = state.target_context["intelligent_decisions"]
            self.assertIn("使用PowerShell执行脚本", decisions)
    
    @patch('core.nodes.EnvironmentAwareness')
    async def test_decision_enhance_first(self):
        """测试决策先增强功能"""
        self.state.target_context = {
            "need_capability_enhancement": True
        }
        
        mock_env_info = {
            "os_info": {"system": "Linux"},
            "available_tools": {},
            "network_info": {}
        }
        
        with patch.object(self.node.env_awareness, 'get_environment_report', return_value=mock_env_info):
            state = await self.node(self.state)
            
            decisions = state.target_context["intelligent_decisions"]
            self.assertIn("使用Bash执行脚本", decisions)
    
    @patch('core.nodes.EnvironmentAwareness')
    async def test_decision_with_cms(self):
        """测试基于CMS的决策"""
        self.state.target_context = {
            "cms": "WebLogic"
        }
        
        mock_env_info = {
            "os_info": {"system": "Linux"},
            "available_tools": {},
            "network_info": {}
        }
        
        with patch.object(self.node.env_awareness, 'get_environment_report', return_value=mock_env_info):
            state = await self.node(self.state)
            
            decisions = state.target_context["intelligent_decisions"]
            self.assertIn("执行WebLogic相关POC", decisions)
    
    @patch('core.nodes.EnvironmentAwareness')
    async def test_decision_with_network(self):
        """测试基于网络状态的决策"""
        self.state.target_context = {}
        
        mock_env_info = {
            "os_info": {"system": "Windows"},
            "available_tools": {},
            "network_info": {
                "proxy_detected": True,
                "firewall_detected": True
            }
        }
        
        with patch.object(self.node.env_awareness, 'get_environment_report', return_value=mock_env_info):
            state = await self.node(self.state)
            
            decisions = state.target_context["intelligent_decisions"]
            self.assertIn("检测到代理,调整扫描策略", decisions)
            self.assertIn("检测到防火墙,降低扫描速度", decisions)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestTaskPlanningNode))
    suite.addTests(loader.loadTestsFromTestCase(TestToolExecutionNode))
    suite.addTests(loader.loadTestsFromTestCase(TestResultVerificationNode))
    suite.addTests(loader.loadTestsFromTestCase(TestVulnerabilityAnalysisNode))
    suite.addTests(loader.loadTestsFromTestCase(TestReportGenerationNode))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentAwarenessNode))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeGenerationNode))
    suite.addTests(loader.loadTestsFromTestCase(TestCapabilityEnhancementNode))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeExecutionNode))
    suite.addTests(loader.loadTestsFromTestCase(TestIntelligentDecisionNode))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n{'='*60}")

    print(f"  运行测试: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"{'='*60}\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

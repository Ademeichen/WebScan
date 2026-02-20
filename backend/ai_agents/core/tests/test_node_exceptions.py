"""
节点异常场景测试

测试各个节点在异常情况下的行为和错误处理。
"""
import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock

backend_dir = Path(__file__).parent.parent
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


class TestNodeExceptionScenarios:
    """节点异常场景测试"""

    @pytest.fixture
    def normal_state(self):
        """正常状态"""
        return AgentState(
            task_id="test_exception",
            target="http://test.local"
        )

    @pytest.mark.asyncio
    async def test_task_planning_with_network_error(self, normal_state):
        """测试任务规划节点处理网络错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            result = await node(normal_state)
            assert result is not None
            assert normal_state.errors

    @pytest.mark.asyncio
    async def test_tool_execution_with_tool_failure(self, normal_state):
        """测试工具执行节点处理工具失败"""
        node = ToolExecutionNode()
        normal_state.current_task = {"name": "test_tool"}
        with patch('ai_agents.core.nodes.registry.execute_tool') as mock_execute:
            mock_execute.side_effect = Exception("Tool execution failed")
            result = await node(normal_state)
            assert result is not None
            assert len(normal_state.errors) > 0

    @pytest.mark.asyncio
    async def test_result_verification_with_invalid_result(self, normal_state):
        """测试结果验证节点处理无效结果"""
        node = ResultVerificationNode()
        normal_state.tool_results = {"test_tool": {"status": "invalid"}}
        result = await node(normal_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_vulnerability_analysis_with_parse_error(self, normal_state):
        """测试漏洞分析节点处理解析错误"""
        node = VulnerabilityAnalysisNode()
        with patch('ai_agents.core.nodes.json.loads') as mock_loads:
            mock_loads.side_effect = Exception("Parse error")
            result = await node(normal_state)
            assert result is not None
            assert len(normal_state.errors) > 0

    @pytest.mark.asyncio
    async def test_report_generation_with_write_error(self, normal_state):
        """测试报告生成节点处理写入错误"""
        node = ReportGenerationNode()
        with patch('builtins.open', side_effect=IOError("Write error")):
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_environment_awareness_with_timeout(self, normal_state):
        """测试环境感知节点处理超时"""
        node = EnvironmentAwarenessNode()
        with patch('ai_agents.core.nodes.httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError("Timeout")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_code_generation_with_llm_error(self, normal_state):
        """测试代码生成节点处理LLM错误"""
        node = CodeGenerationNode()
        with patch('ai_agents.core.nodes.ChatOpenAI') as mock_llm:
            mock_llm.return_value.invoke.side_effect = Exception("LLM error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_capability_enhancement_with_dependency_error(self, normal_state):
        """测试功能增强节点处理依赖错误"""
        node = CapabilityEnhancementNode()
        with patch('ai_agents.core.nodes.DependencyInstaller') as mock_installer:
            mock_installer.install.side_effect = Exception("Dependency error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_code_execution_with_subprocess_error(self, normal_state):
        """测试代码执行节点处理子进程错误"""
        node = CodeExecutionNode()
        with patch('ai_agents.code_execution.executor.execute_process') as mock_execute:
            mock_execute.side_effect = Exception("Subprocess error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_intelligent_decision_with_invalid_decision(self, normal_state):
        """测试智能决策节点处理无效决策"""
        node = IntelligentDecisionNode()
        normal_state.context = {"decision": "invalid"}
        result = await node(normal_state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_seebug_agent_with_api_error(self, normal_state):
        """测试Seebug Agent节点处理API错误"""
        node = SeebugAgentNode()
        with patch('ai_agents.core.nodes.SeebugUtils') as mock_seebug:
            mock_seebug.return_value.search_poc.side_effect = Exception("API error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_poc_verification_with_verification_error(self, normal_state):
        """测试POC验证节点处理验证错误"""
        node = POCVerificationNode()
        with patch('ai_agents.core.nodes.POCVerificationEngine') as mock_engine:
            mock_engine.return_value.verify_poc.side_effect = Exception("Verification error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_memory_error(self, normal_state):
        """测试节点处理内存错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = MemoryError("Out of memory")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_keyboard_interrupt(self, normal_state):
        """测试节点处理键盘中断"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.asyncio.sleep') as mock_sleep:
            mock_sleep.side_effect = KeyboardInterrupt()
            with pytest.raises(KeyboardInterrupt):
                await node(normal_state)

    @pytest.mark.asyncio
    async def test_node_with_system_exit(self, normal_state):
        """测试节点处理系统退出"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.sys.exit') as mock_exit:
            mock_exit.side_effect = SystemExit()
            with pytest.raises(SystemExit):
                await node(normal_state)

    @pytest.mark.asyncio
    async def test_node_with_value_error(self, normal_state):
        """测试节点处理值错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = ValueError("Invalid value")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_type_error(self, normal_state):
        """测试节点处理类型错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = TypeError("Invalid type")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_attribute_error(self, normal_state):
        """测试节点处理属性错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = AttributeError("Missing attribute")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_key_error(self, normal_state):
        """测试节点处理键错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = KeyError("Missing key")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_import_error(self, normal_state):
        """测试节点处理导入错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.import_module') as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_runtime_error(self, normal_state):
        """测试节点处理运行时错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = RuntimeError("Runtime error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_connection_error(self, normal_state):
        """测试节点处理连接错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = ConnectionError("Connection failed")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_timeout_error(self, normal_state):
        """测试节点处理超时错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError("Request timeout")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_http_error(self, normal_state):
        """测试节点处理HTTP错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("HTTP 500")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_ssl_error(self, normal_state):
        """测试节点处理SSL错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("SSL error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_dns_error(self, normal_state):
        """测试节点处理DNS错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("DNS resolution failed")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_file_not_found_error(self, normal_state):
        """测试节点处理文件未找到错误"""
        node = TaskPlanningNode()
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_permission_error(self, normal_state):
        """测试节点处理权限错误"""
        node = TaskPlanningNode()
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_os_error(self, normal_state):
        """测试节点处理操作系统错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.os.path.exists') as mock_exists:
            mock_exists.side_effect = OSError("OS error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_json_decode_error(self, normal_state):
        """测试节点处理JSON解码错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.json.loads') as mock_loads:
            mock_loads.side_effect = Exception("JSON decode error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_json_encode_error(self, normal_state):
        """测试节点处理JSON编码错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.json.dumps') as mock_dumps:
            mock_dumps.side_effect = Exception("JSON encode error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_unicode_decode_error(self, normal_state):
        """测试节点处理Unicode解码错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.bytes.decode') as mock_decode:
            mock_decode.side_effect = UnicodeDecodeError("Unicode error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_unicode_encode_error(self, normal_state):
        """测试节点处理Unicode编码错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.str.encode') as mock_encode:
            mock_encode.side_effect = UnicodeEncodeError("Unicode error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_recursion_error(self, normal_state):
        """测试节点处理递归错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = RecursionError("Maximum recursion depth exceeded")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_overflow_error(self, normal_state):
        """测试节点处理溢出错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = OverflowError("Stack overflow")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_zero_division_error(self, normal_state):
        """测试节点处理除零错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = ZeroDivisionError("Division by zero")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_index_error(self, normal_state):
        """测试节点处理索引错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = IndexError("Index out of range")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_assertion_error(self, normal_state):
        """测试节点处理断言错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = AssertionError("Assertion failed")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_not_implemented_error(self, normal_state):
        """测试节点处理未实现错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = NotImplementedError("Feature not implemented")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_syntax_error(self, normal_state):
        """测试节点处理语法错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = SyntaxError("Syntax error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_indentation_error(self, normal_state):
        """测试节点处理缩进错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = IndentationError("Indentation error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_tab_error(self, normal_state):
        """测试节点处理制表符错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = TabError("Tab error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_eof_error(self, normal_state):
        """测试节点处理文件结束错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = EOFError("Unexpected EOF")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_blocking_io_error(self, normal_state):
        """测试节点处理阻塞IO错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = BlockingIOError("Blocking IO operation")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_child_process_error(self, normal_state):
        """测试节点处理子进程错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = ChildProcessError("Child process error")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_broken_pipe_error(self, normal_state):
        """测试节点处理管道错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = BrokenPipeError("Broken pipe")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_connection_aborted_error(self, normal_state):
        """测试节点处理连接中止错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = ConnectionAbortedError("Connection aborted")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_connection_refused_error(self, normal_state):
        """测试节点处理连接拒绝错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = ConnectionRefusedError("Connection refused")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_connection_reset_error(self, normal_state):
        """测试节点处理连接重置错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = ConnectionResetError("Connection reset")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_interrupted_error(self, normal_state):
        """测试节点处理中断错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = InterruptedError("Interrupted")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_not_a_directory_error(self, normal_state):
        """测试节点处理非目录错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = NotADirectoryError("Not a directory")
            result = await node(normal_state)
            assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_is_a_directory_error(self, normal_state):
        """测试节点处理是目录错误"""
        node = TaskPlanningNode()
        with patch('ai_agents.core.nodes.AgentState') as mock_state:
            mock_state.side_effect = IsADirectoryError("Is a directory")
            result = await node(normal_state)
            assert result is not None

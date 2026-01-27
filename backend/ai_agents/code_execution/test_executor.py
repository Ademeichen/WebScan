"""
测试统一执行器模块

测试 UnifiedExecutor 类的各项功能。
"""
import pytest
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.code_execution.executor import (
    UnifiedExecutor,
    ExecutionResult
)


class TestExecutionResult:
    """
    测试执行结果类
    """

    def test_creation(self):
        """
        测试创建执行结果
        """
        result = ExecutionResult(
            status='success',
            output='test output',
            error='',
            execution_time=1.5,
            exit_code=0
        )
        
        assert result.status == 'success'
        assert result.output == 'test output'
        assert result.error == ''
        assert result.execution_time == 1.5
        assert result.exit_code == 0

    def test_to_dict(self):
        """
        测试转换为字典
        """
        result = ExecutionResult(
            status='success',
            output='test output',
            error='test error',
            execution_time=1.5,
            exit_code=0
        )
        
        result_dict = result.to_dict()
        assert result_dict['status'] == 'success'
        assert result_dict['output'] == 'test output'
        assert result_dict['error'] == 'test error'
        assert result_dict['execution_time'] == 1.5
        assert result_dict['exit_code'] == 0


class TestUnifiedExecutor:
    """
    测试统一执行器类
    """

    @pytest.fixture
    def executor(self):
        """
        创建执行器实例
        """
        return UnifiedExecutor(
            timeout=30,
            max_memory=256,
            enable_sandbox=True
        )

    def test_initialization(self, executor):
        """
        测试初始化
        """
        assert executor is not None
        assert executor.timeout == 30
        assert executor.max_memory == 256
        assert executor.enable_sandbox is True
        assert hasattr(executor, 'env_awareness')
        assert hasattr(executor, 'code_generator')
        assert hasattr(executor, 'capability_enhancer')

    @pytest.mark.asyncio
    async def test_execute_code_python_simple(self, executor):
        """
        测试执行简单的Python代码
        """
        code = """
print("Hello, World!")
print("Test execution")
"""
        result = await executor.execute_code(code, language='python')
        
        assert isinstance(result, ExecutionResult)
        assert 'Hello, World!' in result.output
        assert 'Test execution' in result.output
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_execute_code_python_with_error(self, executor):
        """
        测试执行包含错误的Python代码
        """
        code = """
print("Before error")
raise ValueError("Test error")
"""
        result = await executor.execute_code(code, language='python')
        
        assert isinstance(result, ExecutionResult)
        assert result.status != 'success'
        assert 'ValueError' in result.error or 'Test error' in result.error

    @pytest.mark.asyncio
    async def test_execute_code_dangerous(self, executor):
        """
        测试执行危险代码（应该被拒绝）
        """
        code = """
import os
os.system("echo dangerous")
"""
        result = await executor.execute_code(code, language='python')
        
        assert isinstance(result, ExecutionResult)
        assert result.status == 'failed'
        assert '验证失败' in result.error or 'validation' in result.error.lower()

    @pytest.mark.asyncio
    async def test_generate_and_execute_port_scan(self, executor):
        """
        测试生成并执行端口扫描代码
        """
        result = await executor.generate_and_execute(
            scan_type='port_scan',
            target='127.0.0.1',
            requirements='',
            language='python'
        )
        
        assert isinstance(result, dict)
        assert 'code_generation' in result
        assert 'execution' in result
        assert 'scan_type' in result
        assert 'target' in result
        assert result['scan_type'] == 'port_scan'
        assert result['target'] == '127.0.0.1'

    @pytest.mark.asyncio
    async def test_generate_and_execute_dir_scan(self, executor):
        """
        测试生成并执行目录扫描代码
        """
        result = await executor.generate_and_execute(
            scan_type='dir_scan',
            target='https://www.baidu.com',
            requirements='',
            language='python'
        )
        
        assert isinstance(result, dict)
        assert 'code_generation' in result
        assert 'execution' in result
        assert result['scan_type'] == 'dir_scan'
        assert result['target'] == 'https://www.baidu.com'

    def test_get_environment_info(self, executor):
        """
        测试获取环境信息
        """
        env_info = executor.get_environment_info()
        
        assert isinstance(env_info, dict)
        assert 'os_info' in env_info
        assert 'python_info' in env_info
        assert 'available_tools' in env_info
        assert 'network_info' in env_info
        assert 'system_resources' in env_info

    def test_list_capabilities(self, executor):
        """
        测试列出所有能力
        """
        capabilities = executor.list_capabilities()
        
        assert isinstance(capabilities, list)
        assert all(isinstance(cap, dict) for cap in capabilities)

    def test_get_file_extension(self, executor):
        """
        测试获取文件扩展名
        """
        assert executor._get_file_extension('python') == 'py'
        assert executor._get_file_extension('bash') == 'sh'
        assert executor._get_file_extension('powershell') == 'ps1'
        assert executor._get_file_extension('shell') == 'sh'
        assert executor._get_file_extension('unknown') == 'py'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

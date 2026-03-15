"""
测试POC验证引擎

测试POC验证执行引擎的各项功能。
"""
import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock, MagicMock as MockMagic
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.Pocsuite3Agent.agent import Pocsuite3Agent, POCResult


class MockPOCVerificationResult:
    """模拟POC验证结果类"""
    def __init__(self, verification_task, poc_name, poc_id, target, vulnerable, message, output="", error="", execution_time=0.0, confidence=0.0, severity="info", cvss_score=0.0):
        self.verification_task = verification_task
        self.poc_name = poc_name
        self.poc_id = poc_id
        self.target = target
        self.vulnerable = vulnerable
        self.message = message
        self.output = output
        self.error = error
        self.execution_time = execution_time
        self.confidence = confidence
        self.severity = severity
        self.cvss_score = cvss_score
        
    @classmethod
    async def create(cls, verification_task, poc_name, poc_id, target, vulnerable, message, output="", error="", execution_time=0.0, confidence=0.0, severity="info", cvss_score=0.0):
        return cls(verification_task, poc_name, poc_id, target, vulnerable, message, output, error, execution_time, confidence, severity, cvss_score)


class POCVerificationTask:
    """测试用POC验证任务类"""
    def __init__(self, id, poc_name, target, poc_code, timeout=60, max_retries=3):
        self.id = id
        self.poc_id = poc_name
        self.poc_name = poc_name
        self.target = target
        self.poc_code = poc_code
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_count = 0
        self.status = "pending"
        self.result = None
        self.progress = 0
        self._saved_in_db = False
        
    async def save(self):
        """模拟保存方法"""
        self._saved_in_db = True


class TestExecutionConfig:
    """测试执行配置类"""
    
    def test_creation(self):
        """测试创建执行配置"""
        from ai_agents.poc_system.verification_engine import ExecutionConfig
        config = ExecutionConfig(
            poc_id="test_poc",
            target="https://www.baidu.com",
            poc_code="print('test')"
        )
        
        assert config.poc_id == "test_poc"
        assert config.target == "https://www.baidu.com"
        assert config.poc_code == "print('test')"
        assert config.timeout == 60
        assert config.max_retries == 3
        assert config.enable_sandbox is True
        assert config.max_memory_mb == 512
        assert config.max_cpu_percent == 80.0
    
    def test_custom_config(self):
        """测试自定义配置"""
        from ai_agents.poc_system.verification_engine import ExecutionConfig
        config = ExecutionConfig(
            poc_id="custom_poc",
            target="https://example.com",
            poc_code="import os",
            timeout=120,
            max_retries=5,
            enable_sandbox=False,
            max_memory_mb=1024,
            max_cpu_percent=90.0
        )
        
        assert config.timeout == 120
        assert config.max_retries == 5
        assert config.enable_sandbox is False
        assert config.max_memory_mb == 1024
        assert config.max_cpu_percent == 90.0


class TestExecutionStats:
    """测试执行统计类"""
    
    def test_initial_stats(self):
        """测试初始统计"""
        from ai_agents.poc_system.verification_engine import ExecutionStats
        stats = ExecutionStats()
        
        assert stats.total_pocs == 0
        assert stats.executed_count == 0
        assert stats.vulnerable_count == 0
        assert stats.failed_count == 0
        assert stats.total_execution_time == 0.0
        assert stats.average_execution_time == 0.0
        assert stats.success_rate == 0.0
    
    def test_update_stats(self):
        """测试更新统计"""
        from ai_agents.poc_system.verification_engine import ExecutionStats
        stats = ExecutionStats()
        stats.total_pocs = 10
        stats.executed_count = 8
        stats.vulnerable_count = 3
        stats.failed_count = 2
        stats.total_execution_time = 100.0
        
        stats.average_execution_time = stats.total_execution_time / stats.executed_count
        stats.success_rate = (stats.vulnerable_count / stats.executed_count) * 100
        
        assert stats.total_pocs == 10
        assert stats.executed_count == 8
        assert stats.vulnerable_count == 3
        assert stats.failed_count == 2
        assert stats.total_execution_time == 100.0
        assert stats.average_execution_time == 12.5
        assert stats.success_rate == 37.5


class TestVerificationEngine:
    """测试POC验证引擎"""
    
    @pytest.fixture
    def engine(self):
        from ai_agents.poc_system.verification_engine import VerificationEngine
        engine = VerificationEngine()
        return engine
    
    @pytest.fixture
    def verification_task(self):
        task = POCVerificationTask(
            id="test_task_1",
            poc_name="test_poc",
            target="https://www.baidu.com",
            poc_code="print('test')",
            timeout=60,
            max_retries=3
        )
        return task
    
    def test_initialization(self, engine):
        """测试引擎初始化"""
        assert engine is not None
        assert hasattr(engine, 'active_executions')
        assert hasattr(engine, 'execution_semaphore')
    
    @pytest.mark.asyncio
    async def test_execute_verification_task_success(self, engine, verification_task):
        """测试成功执行POC验证任务"""
        mock_result = MockPOCVerificationResult(
            verification_task=verification_task,
            poc_name=verification_task.poc_name,
            poc_id=verification_task.poc_id,
            target=verification_task.target,
            vulnerable=False,
            message="POC执行成功",
            output="test output",
            execution_time=1.5,
            confidence=0.9,
            severity="info",
            cvss_score=0.0
        )
        
        with patch('backend.models.POCVerificationResult.create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_result
            with patch('backend.ai_agents.poc_system.verification_engine.poc_manager') as mock_poc_manager:
                mock_poc_manager.get_poc_code = AsyncMock(return_value=verification_task.poc_code)
                result = await engine.execute_verification_task(verification_task)
                assert result is not None
    
    @pytest.mark.asyncio
    async def test_execute_verification_task_timeout(self, engine, verification_task):
        """测试POC验证任务超时"""
        verification_task.timeout = 1
        mock_result = MockPOCVerificationResult(
            verification_task=verification_task,
            poc_name=verification_task.poc_name,
            poc_id=verification_task.poc_id,
            target=verification_task.target,
            vulnerable=False,
            message="执行超时",
            output="",
            error="Execution timeout",
            execution_time=0.0,
            confidence=0.0,
            severity="info",
            cvss_score=0.0
        )
        
        with patch('backend.models.POCVerificationResult.create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_result
            with patch('backend.ai_agents.poc_system.verification_engine.poc_manager') as mock_poc_manager:
                mock_poc_manager.get_poc_code = AsyncMock(return_value=verification_task.poc_code)
                result = await engine.execute_verification_task(verification_task)
                assert result is not None
    
    @pytest.mark.asyncio
    async def test_execute_verification_task_exception(self, engine, verification_task):
        """测试POC验证任务异常"""
        verification_task.poc_code = "raise Exception('Test error')"
        mock_result = MockPOCVerificationResult(
            verification_task=verification_task,
            poc_name=verification_task.poc_name,
            poc_id=verification_task.poc_id,
            target=verification_task.target,
            vulnerable=False,
            message="执行错误",
            output="",
            error="Execution error",
            execution_time=0.0,
            confidence=0.0,
            severity="info",
            cvss_score=0.0
        )
        
        with patch('backend.models.POCVerificationResult.create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_result
            with patch('backend.ai_agents.poc_system.verification_engine.poc_manager') as mock_poc_manager:
                mock_poc_manager.get_poc_code = AsyncMock(return_value=verification_task.poc_code)
                result = await engine.execute_verification_task(verification_task)
                assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

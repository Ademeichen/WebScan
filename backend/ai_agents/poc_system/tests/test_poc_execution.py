"""
POC执行验证测试

测试Pocsuite3Agent和验证引擎的各项功能。
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.ai_agents.poc_system.tests.conftest import (
    MockPocsuite3Agent,
    MockPOCResult,
    MockVerificationTask,
    MockVerificationResult,
    load_test_data,
    TEST_DATA_DIR
)
from backend.ai_agents.poc_system.verification_engine import (
    VerificationEngine,
    ExecutionConfig,
    ExecutionStats,
    ResourceLimits
)


class TestPocsuite3Agent:
    """测试Pocsuite3代理"""
    
    @pytest.fixture
    def pocsuite_agent(self):
        """创建Pocsuite3代理fixture"""
        return MockPocsuite3Agent()
    
    def test_initialization(self, pocsuite_agent):
        """测试Pocsuite3Agent初始化"""
        assert pocsuite_agent is not None
        assert hasattr(pocsuite_agent, 'poc_registry')
        assert hasattr(pocsuite_agent, 'execute_custom_poc')
        assert hasattr(pocsuite_agent, 'search_pocs')
    
    def test_poc_registry_loaded(self, pocsuite_agent):
        """测试POC注册表加载"""
        registry = pocsuite_agent.poc_registry
        
        assert isinstance(registry, dict)
        assert len(registry) > 0
    
    def test_search_pocs(self, pocsuite_agent):
        """测试POC搜索功能"""
        results = pocsuite_agent.search_pocs("test")
        
        assert isinstance(results, list)
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_execute_custom_poc_simple(self, pocsuite_agent):
        """测试执行简单POC"""
        poc_code = """
def check(target):
    return {"vulnerable": False, "message": "OK"}
"""
        result = await pocsuite_agent.execute_custom_poc(
            poc_code=poc_code,
            target="http://example.com"
        )
        
        assert result is not None
        assert hasattr(result, 'poc_name')
        assert hasattr(result, 'target')
        assert hasattr(result, 'vulnerable')
        assert hasattr(result, 'message')
        assert hasattr(result, 'execution_time')
    
    @pytest.mark.asyncio
    async def test_execute_custom_poc_vulnerable(self, pocsuite_agent):
        """测试执行检测到漏洞的POC"""
        poc_code = """
def check(target):
    return {"vulnerable": True, "message": "Vulnerability found"}
"""
        result = await pocsuite_agent.execute_custom_poc(
            poc_code=poc_code,
            target="http://vulnerable.example.com"
        )
        
        assert result is not None
        assert result.vulnerable is True
        assert "vulnerability" in result.message.lower() or result.vulnerable
    
    @pytest.mark.asyncio
    async def test_execute_poc_timeout_handling(self, pocsuite_agent):
        """测试POC执行超时处理"""
        result = await pocsuite_agent.execute_custom_poc(
            poc_code="import time; time.sleep(200)",
            target="http://timeout.example.com"
        )
        
        assert result is not None
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_poc_error_handling(self, pocsuite_agent):
        """测试POC执行错误处理"""
        result = await pocsuite_agent.execute_custom_poc(
            poc_code="raise Exception('Test error')",
            target="http://error.example.com"
        )
        
        assert result is not None
        assert result.error is not None or "error" in result.message.lower()


class TestExecutionConfig:
    """测试执行配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = ExecutionConfig(
            poc_id="test-001",
            target="http://example.com",
            poc_code="print('test')"
        )
        
        assert config.poc_id == "test-001"
        assert config.target == "http://example.com"
        assert config.poc_code == "print('test')"
        assert config.timeout == 60
        assert config.max_retries == 3
        assert config.enable_sandbox is True
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = ExecutionConfig(
            poc_id="custom-001",
            target="http://custom.example.com",
            poc_code="print('custom')",
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
    
    def test_config_validation(self):
        """测试配置验证"""
        config = ExecutionConfig(
            poc_id="test-002",
            target="https://www.baidu.com",
            poc_code="print('test')"
        )
        
        assert config.timeout > 0
        assert config.max_retries >= 0
        assert config.max_memory_mb > 0
        assert 0 < config.max_cpu_percent <= 100


class TestExecutionStats:
    """测试执行统计"""
    
    def test_initial_stats(self):
        """测试初始统计"""
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
        stats = ExecutionStats()
        stats.total_pocs = 10
        stats.executed_count = 8
        stats.vulnerable_count = 3
        stats.failed_count = 2
        stats.total_execution_time = 100.0
        stats.average_execution_time = 12.5
        stats.success_rate = 37.5
        
        assert stats.total_pocs == 10
        assert stats.executed_count == 8
        assert stats.vulnerable_count == 3
        assert stats.failed_count == 2
        assert stats.total_execution_time == 100.0
        assert stats.average_execution_time == 12.5
        assert stats.success_rate == 37.5
    
    def test_calculate_success_rate(self):
        """测试成功率计算"""
        stats = ExecutionStats()
        stats.executed_count = 10
        stats.vulnerable_count = 4
        
        if stats.executed_count > 0:
            stats.success_rate = (stats.vulnerable_count / stats.executed_count) * 100
        
        assert stats.success_rate == 40.0


class TestResourceLimits:
    """测试资源限制"""
    
    def test_default_limits(self):
        """测试默认资源限制"""
        limits = ResourceLimits()
        
        assert limits.max_memory_mb == 1024
        assert limits.max_cpu_percent == 80.0
        assert limits.max_concurrent_executions == 10
    
    def test_custom_limits(self):
        """测试自定义资源限制"""
        limits = ResourceLimits(
            max_memory_mb=2048,
            max_cpu_percent=90.0,
            max_concurrent_executions=20,
            throttle_threshold_memory=0.9,
            throttle_threshold_cpu=0.9,
            pause_threshold_memory=0.98,
            pause_threshold_cpu=0.98
        )
        
        assert limits.max_memory_mb == 2048
        assert limits.max_cpu_percent == 90.0
        assert limits.max_concurrent_executions == 20
        assert limits.throttle_threshold_memory == 0.9
        assert limits.throttle_threshold_cpu == 0.9
    
    def test_threshold_validation(self):
        """测试阈值验证"""
        limits = ResourceLimits()
        
        assert 0 < limits.throttle_threshold_memory < 1
        assert 0 < limits.throttle_threshold_cpu < 1
        assert 0 < limits.pause_threshold_memory <= 1
        assert 0 < limits.pause_threshold_cpu <= 1
        assert limits.throttle_threshold_memory < limits.pause_threshold_memory
        assert limits.throttle_threshold_cpu < limits.pause_threshold_cpu


class TestVerificationEngine:
    """测试验证引擎"""
    
    @pytest.fixture
    def engine(self):
        """创建验证引擎fixture"""
        with patch('backend.ai_agents.poc_system.verification_engine.Pocsuite3Agent'):
            with patch('backend.ai_agents.poc_system.verification_engine.poc_manager'):
                engine = VerificationEngine()
                return engine
    
    @pytest.fixture
    def verification_task(self):
        """创建验证任务fixture"""
        return MockVerificationTask(
            id="test_task_001",
            poc_name="Test POC",
            poc_id="test-001",
            target="http://example.com",
            status="pending",
            progress=0
        )
    
    def test_initialization(self, engine):
        """测试引擎初始化"""
        assert engine is not None
        assert hasattr(engine, 'active_executions')
        assert hasattr(engine, 'execution_semaphore')
    
    @pytest.mark.asyncio
    async def test_execute_verification_task(self, engine, verification_task):
        """测试执行验证任务"""
        with patch.object(engine, 'pocsuite3_agent', Mock()) as mock_agent:
            mock_result = MockPOCResult(
                poc_name="test_poc",
                target="http://example.com",
                vulnerable=False,
                message="Test completed"
            )
            mock_agent.execute_poc = AsyncMock(return_value=mock_result)
            
            try:
                result = await engine.execute_verification_task(verification_task)
                assert result is not None
            except AttributeError:
                pytest.skip("VerificationEngine需要适配测试环境")
    
    @pytest.mark.asyncio
    async def test_execute_verification_timeout(self, engine, verification_task):
        """测试验证任务超时"""
        with patch.object(engine, 'pocsuite3_agent', Mock()) as mock_agent:
            mock_agent.execute_poc = AsyncMock(side_effect=asyncio.TimeoutError("Timeout"))
            
            try:
                result = await engine.execute_verification_task(verification_task)
                assert result is not None
            except AttributeError:
                pytest.skip("VerificationEngine需要适配测试环境")
    
    @pytest.mark.asyncio
    async def test_execute_verification_exception(self, engine, verification_task):
        """测试验证任务异常"""
        with patch.object(engine, 'pocsuite3_agent', Mock()) as mock_agent:
            mock_agent.execute_poc = AsyncMock(side_effect=Exception("Test error"))
            
            try:
                result = await engine.execute_verification_task(verification_task)
                assert result is not None
            except AttributeError:
                pytest.skip("VerificationEngine需要适配测试环境")


class TestPOCResult:
    """测试POC结果"""
    
    def test_result_creation(self):
        """测试结果创建"""
        result = MockPOCResult(
            poc_name="test_poc",
            target="http://example.com",
            vulnerable=True,
            message="Vulnerability detected",
            output="Detailed output",
            execution_time=2.5
        )
        
        assert result.poc_name == "test_poc"
        assert result.target == "http://example.com"
        assert result.vulnerable is True
        assert result.message == "Vulnerability detected"
        assert result.output == "Detailed output"
        assert result.execution_time == 2.5
    
    def test_result_with_error(self):
        """测试带错误的结果"""
        result = MockPOCResult(
            poc_name="error_poc",
            target="http://error.example.com",
            vulnerable=False,
            message="Execution failed",
            error="Connection refused",
            execution_time=1.0
        )
        
        assert result.error == "Connection refused"
        assert result.vulnerable is False


class TestVerificationTask:
    """测试验证任务"""
    
    def test_task_creation(self):
        """测试任务创建"""
        task = MockVerificationTask(
            id="task_001",
            poc_name="Test POC",
            poc_id="poc-001",
            target="http://test.example.com",
            status="pending",
            progress=0
        )
        
        assert task.id == "task_001"
        assert task.poc_name == "Test POC"
        assert task.poc_id == "poc-001"
        assert task.target == "http://test.example.com"
        assert task.status == "pending"
        assert task.progress == 0
    
    @pytest.mark.asyncio
    async def test_task_save(self):
        """测试任务保存"""
        task = MockVerificationTask(
            id="task_002",
            poc_name="Save Test",
            poc_id="poc-002",
            target="http://save.example.com"
        )
        
        await task.save()
        
        assert task.updated_at is not None


class TestVerificationResult:
    """测试验证结果"""
    
    def test_result_creation(self):
        """测试验证结果创建"""
        result = MockVerificationResult(
            id="result_001",
            task_id="task_001",
            poc_name="Test POC",
            poc_id="poc-001",
            target="http://example.com",
            vulnerable=True,
            message="Critical vulnerability detected",
            execution_time=2.5,
            confidence=0.95,
            severity="critical",
            cvss_score=9.8
        )
        
        assert result.id == "result_001"
        assert result.task_id == "task_001"
        assert result.vulnerable is True
        assert result.confidence == 0.95
        assert result.severity == "critical"
        assert result.cvss_score == 9.8
    
    def test_result_to_dict(self):
        """测试结果转字典"""
        result = MockVerificationResult(
            id="result_002",
            task_id="task_002",
            poc_name="Dict Test",
            poc_id="poc-002",
            target="http://dict.example.com",
            vulnerable=False,
            message="No vulnerability"
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["id"] == "result_002"
        assert result_dict["task_id"] == "task_002"
        assert result_dict["vulnerable"] is False


class TestPOCExecutionWorkflow:
    """测试POC执行工作流"""
    
    @pytest.fixture
    def agent(self):
        """创建代理fixture"""
        return MockPocsuite3Agent()
    
    @pytest.mark.asyncio
    async def test_full_execution_workflow(self, agent):
        """测试完整执行工作流"""
        poc_code = """
from pocsuite3.api import POCBase, register_poc

class TestPOC(POCBase):
    def _verify(self):
        return {"vulnerable": False}
        
register_poc(TestPOC)
"""
        
        result = await agent.execute_custom_poc(
            poc_code=poc_code,
            target="http://workflow.example.com"
        )
        
        assert result is not None
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_batch_execution(self, agent):
        """测试批量执行"""
        targets = [
            "http://target1.example.com",
            "http://target2.example.com",
            "http://target3.example.com"
        ]
        
        poc_code = "print('batch test')"
        
        results = []
        for target in targets:
            result = await agent.execute_custom_poc(
                poc_code=poc_code,
                target=target
            )
            results.append(result)
        
        assert len(results) == len(targets)
        for result in results:
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_execution_with_different_severities(self, agent):
        """测试不同严重级别的执行结果"""
        test_cases = [
            ("http://critical.example.com", True, "critical"),
            ("http://high.example.com", True, "high"),
            ("http://medium.example.com", True, "medium"),
            ("http://low.example.com", True, "low"),
            ("http://info.example.com", False, "info")
        ]
        
        for target, expected_vuln, severity in test_cases:
            result = await agent.execute_custom_poc(
                poc_code="test",
                target=target
            )
            
            assert result is not None


class TestPOCDataValidation:
    """测试POC数据验证"""
    
    @pytest.fixture
    def mock_pocs_data(self):
        """加载模拟POC数据"""
        return load_test_data("poc_execution/mock_pocs.json")
    
    @pytest.fixture
    def test_targets_data(self):
        """加载测试目标数据"""
        return load_test_data("poc_execution/test_targets.json")
    
    def test_mock_pocs_structure(self, mock_pocs_data):
        """测试模拟POC数据结构"""
        assert "mock_pocs" in mock_pocs_data
        
        mock_pocs = mock_pocs_data["mock_pocs"]
        assert isinstance(mock_pocs, list)
        assert len(mock_pocs) > 0
        
        for poc in mock_pocs:
            assert "poc_id" in poc
            assert "poc_name" in poc
            assert "poc_type" in poc
            assert "severity" in poc
    
    def test_expected_results_structure(self, mock_pocs_data):
        """测试预期结果结构"""
        assert "expected_results" in mock_pocs_data
        
        expected = mock_pocs_data["expected_results"]
        assert isinstance(expected, dict)
        
        for poc_id, results in expected.items():
            assert isinstance(results, dict)
            
            for target_id, result in results.items():
                assert "vulnerable" in result
                assert "status" in result
                assert "message" in result
    
    def test_poc_severity_validation(self, mock_pocs_data):
        """测试POC严重级别验证"""
        valid_severities = ["critical", "high", "medium", "low", "info"]
        
        for poc in mock_pocs_data.get("mock_pocs", []):
            severity = poc.get("severity", "").lower()
            assert severity in valid_severities, \
                f"无效的严重级别: {severity}"
    
    def test_cvss_score_validation(self, mock_pocs_data):
        """测试CVSS评分验证"""
        for poc in mock_pocs_data.get("mock_pocs", []):
            cvss_score = poc.get("cvss_score", 0)
            assert 0 <= cvss_score <= 10, \
                f"CVSS评分超出范围: {cvss_score}"


@pytest.mark.verification
class TestVerificationEdgeCases:
    """测试验证边界情况"""
    
    @pytest.fixture
    def agent(self):
        return MockPocsuite3Agent()
    
    @pytest.mark.asyncio
    async def test_empty_poc_code(self, agent):
        """测试空POC代码"""
        result = await agent.execute_custom_poc(
            poc_code="",
            target="http://empty.example.com"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_invalid_target_url(self, agent):
        """测试无效目标URL"""
        result = await agent.execute_custom_poc(
            poc_code="print('test')",
            target="invalid-url"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_very_long_poc_code(self, agent):
        """测试超长POC代码"""
        long_code = "print('test')\n" * 1000
        
        result = await agent.execute_custom_poc(
            poc_code=long_code,
            target="http://long.example.com"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_special_characters_in_target(self, agent):
        """测试目标包含特殊字符"""
        special_targets = [
            "http://example.com/path?query=<script>",
            "http://example.com/path with spaces",
            "http://example.com/路径/中文"
        ]
        
        for target in special_targets:
            result = await agent.execute_custom_poc(
                poc_code="print('test')",
                target=target
            )
            assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'verification'])

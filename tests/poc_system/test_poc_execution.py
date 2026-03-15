"""
POC执行验证测试

测试Pocsuite3Agent初始化、POC执行功能、验证引擎功能。
"""
import pytest
import sys
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.Pocsuite3Agent.agent import (
    Pocsuite3Agent,
    POCResult,
    ScanResult
)
from backend.ai_agents.poc_system.verification_engine import (
    VerificationEngine,
    ExecutionConfig,
    ExecutionStats,
    ResourceLimits,
    ResourceUsage,
    ExecutionQueue,
    ExecutionResultCache,
    ResourceMonitor,
    ExecutionPriority,
    ExecutionStatus,
    PrioritizedTask
)


class TestPOCResult:
    """测试POC执行结果"""
    
    def test_poc_result_creation(self):
        """测试创建POC结果"""
        result = POCResult(
            poc_name="test_poc",
            target="https://example.com",
            vulnerable=True,
            message="Vulnerability found",
            output="Test output",
            error=None,
            execution_time=1.5
        )
        
        assert result.poc_name == "test_poc"
        assert result.target == "https://example.com"
        assert result.vulnerable is True
        assert result.message == "Vulnerability found"
        assert result.output == "Test output"
        assert result.error is None
        assert result.execution_time == 1.5
    
    def test_poc_result_with_error(self):
        """测试带错误的POC结果"""
        result = POCResult(
            poc_name="error_poc",
            target="https://example.com",
            vulnerable=False,
            message="Execution failed",
            output="",
            error="Connection timeout",
            execution_time=30.0
        )
        
        assert result.vulnerable is False
        assert result.error == "Connection timeout"
        assert result.execution_time == 30.0


class TestScanResult:
    """测试扫描结果"""
    
    def test_scan_result_creation(self):
        """测试创建扫描结果"""
        results = [
            POCResult(
                poc_name="poc1",
                target="https://example.com",
                vulnerable=True,
                message="Found",
                output="output1",
                execution_time=1.0
            ),
            POCResult(
                poc_name="poc2",
                target="https://example.com",
                vulnerable=False,
                message="Not found",
                output="output2",
                execution_time=0.5
            )
        ]
        
        scan_result = ScanResult(
            target="https://example.com",
            total_pocs=2,
            vulnerable_count=1,
            results=results,
            execution_time=1.5
        )
        
        assert scan_result.target == "https://example.com"
        assert scan_result.total_pocs == 2
        assert scan_result.vulnerable_count == 1
        assert len(scan_result.results) == 2
        assert scan_result.execution_time == 1.5


class TestPocsuite3Agent:
    """测试Pocsuite3代理"""
    
    @pytest.fixture
    def agent(self):
        with patch('backend.Pocsuite3Agent.agent.pocsuite3') as mock_pocsuite:
            mock_pocsuite.__version__ = "3.0.0"
            agent = Pocsuite3Agent()
            return agent
    
    def test_agent_initialization(self, agent):
        """测试代理初始化"""
        assert agent is not None
        assert hasattr(agent, 'poc_registry')
        assert isinstance(agent.poc_registry, dict)
    
    def test_get_available_pocs(self, agent):
        """测试获取可用POC列表"""
        agent.poc_registry = {
            "poc1": "/path/to/poc1.py",
            "poc2": "/path/to/poc2.py"
        }
        
        pocs = agent.get_available_pocs()
        
        assert isinstance(pocs, list)
        assert len(pocs) == 2
        assert "poc1" in pocs
        assert "poc2" in pocs
    
    def test_search_pocs(self, agent):
        """测试搜索POC"""
        agent.poc_registry = {
            "weblogic_cve_2020_2551": "/path/to/weblogic.py",
            "struts2_009": "/path/to/struts2.py",
            "tomcat_cve_2017": "/path/to/tomcat.py"
        }
        
        results = agent.search_pocs("weblogic")
        
        assert len(results) == 1
        assert "weblogic" in results[0]
    
    def test_search_pocs_case_insensitive(self, agent):
        """测试搜索POC（不区分大小写）"""
        agent.poc_registry = {
            "WebLogic_CVE": "/path/to/weblogic.py",
            "STRUTS2_POC": "/path/to/struts2.py"
        }
        
        results = agent.search_pocs("weblogic")
        
        assert len(results) == 1
    
    def test_search_pocs_no_match(self, agent):
        """测试搜索POC无匹配"""
        agent.poc_registry = {
            "poc1": "/path/to/poc1.py",
            "poc2": "/path/to/poc2.py"
        }
        
        results = agent.search_pocs("nonexistent")
        
        assert len(results) == 0


class TestExecutionConfig:
    """测试执行配置"""
    
    def test_config_creation(self):
        """测试创建执行配置"""
        config = ExecutionConfig(
            poc_id="test_poc",
            target="https://example.com",
            poc_code="print('test')"
        )
        
        assert config.poc_id == "test_poc"
        assert config.target == "https://example.com"
        assert config.poc_code == "print('test')"
        assert config.timeout == 60
        assert config.max_retries == 3
        assert config.enable_sandbox is True
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = ExecutionConfig(
            poc_id="custom_poc",
            target="https://example.com",
            poc_code="print('custom')",
            timeout=120,
            max_retries=5,
            enable_sandbox=False,
            max_memory_mb=1024,
            max_cpu_percent=90.0,
            priority=ExecutionPriority.HIGH
        )
        
        assert config.timeout == 120
        assert config.max_retries == 5
        assert config.enable_sandbox is False
        assert config.max_memory_mb == 1024
        assert config.max_cpu_percent == 90.0
        assert config.priority == ExecutionPriority.HIGH


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
    
    def test_to_dict(self):
        """测试转换为字典"""
        stats = ExecutionStats(
            total_pocs=10,
            executed_count=8,
            vulnerable_count=3,
            failed_count=2,
            total_execution_time=100.0
        )
        
        result = stats.to_dict()
        
        assert isinstance(result, dict)
        assert result["total_pocs"] == 10
        assert result["executed_count"] == 8
        assert result["vulnerable_count"] == 3


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
            max_concurrent_executions=20
        )
        
        assert limits.max_memory_mb == 2048
        assert limits.max_cpu_percent == 90.0
        assert limits.max_concurrent_executions == 20
    
    def test_to_dict(self):
        """测试转换为字典"""
        limits = ResourceLimits()
        result = limits.to_dict()
        
        assert isinstance(result, dict)
        assert "max_memory_mb" in result
        assert "max_cpu_percent" in result


class TestResourceUsage:
    """测试资源使用"""
    
    def test_resource_usage_creation(self):
        """测试创建资源使用"""
        usage = ResourceUsage(
            memory_mb=512.5,
            memory_percent=25.0,
            cpu_percent=45.0
        )
        
        assert usage.memory_mb == 512.5
        assert usage.memory_percent == 25.0
        assert usage.cpu_percent == 45.0
        assert isinstance(usage.timestamp, datetime)
    
    def test_to_dict(self):
        """测试转换为字典"""
        usage = ResourceUsage(
            memory_mb=512.0,
            memory_percent=25.0,
            cpu_percent=45.0
        )
        
        result = usage.to_dict()
        
        assert "memory_mb" in result
        assert "memory_percent" in result
        assert "cpu_percent" in result
        assert "timestamp" in result


class TestExecutionQueue:
    """测试执行队列"""
    
    @pytest.fixture
    def queue(self):
        return ExecutionQueue(max_concurrent=5)
    
    @pytest.mark.asyncio
    async def test_enqueue(self, queue):
        """测试入队"""
        config = ExecutionConfig(
            poc_id="test_poc",
            target="https://example.com",
            poc_code="print('test')"
        )
        
        task_id = await queue.enqueue(
            task_data={"test": "data"},
            config=config
        )
        
        assert task_id is not None
        assert "test_poc" in task_id
    
    @pytest.mark.asyncio
    async def test_get_queue_size(self, queue):
        """测试获取队列大小"""
        config = ExecutionConfig(
            poc_id="test_poc",
            target="https://example.com",
            poc_code="print('test')"
        )
        
        await queue.enqueue(task_data={}, config=config)
        size = await queue.get_queue_size()
        
        assert size == 1
    
    @pytest.mark.asyncio
    async def test_pause_and_resume(self, queue):
        """测试暂停和恢复"""
        await queue.pause()
        status = queue.get_status()
        assert status["paused"] is True
        
        await queue.resume()
        status = queue.get_status()
        assert status["paused"] is False
    
    @pytest.mark.asyncio
    async def test_clear(self, queue):
        """测试清空队列"""
        config = ExecutionConfig(
            poc_id="test_poc",
            target="https://example.com",
            poc_code="print('test')"
        )
        
        await queue.enqueue(task_data={}, config=config)
        count = await queue.clear()
        
        assert count == 1
        size = await queue.get_queue_size()
        assert size == 0
    
    def test_get_status(self, queue):
        """测试获取队列状态"""
        status = queue.get_status()
        
        assert "queue_size" in status
        assert "running_count" in status
        assert "max_concurrent" in status
        assert "paused" in status


class TestExecutionResultCache:
    """测试执行结果缓存"""
    
    @pytest.fixture
    def cache(self):
        return ExecutionResultCache(max_size=100, default_ttl=3600)
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """测试设置和获取缓存"""
        result = POCResult(
            poc_name="test_poc",
            target="https://example.com",
            vulnerable=True,
            message="Found",
            output="output",
            execution_time=1.0
        )
        
        await cache.set("poc1", "https://example.com", "code", result)
        cached = await cache.get("poc1", "https://example.com", "code")
        
        assert cached is not None
        assert cached.poc_name == "test_poc"
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """测试缓存未命中"""
        cached = await cache.get("nonexistent", "https://example.com", "code")
        
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, cache):
        """测试清除缓存"""
        result = POCResult(
            poc_name="test_poc",
            target="https://example.com",
            vulnerable=True,
            message="Found",
            output="output",
            execution_time=1.0
        )
        
        await cache.set("poc1", "https://example.com", "code", result)
        await cache.clear()
        
        stats = await cache.get_stats()
        assert stats["size"] == 0
    
    @pytest.mark.asyncio
    async def test_get_stats(self, cache):
        """测试获取缓存统计"""
        stats = await cache.get_stats()
        
        assert "size" in stats
        assert "max_size" in stats
        assert "default_ttl" in stats


class TestResourceMonitor:
    """测试资源监控器"""
    
    @pytest.fixture
    def monitor(self):
        limits = ResourceLimits()
        return ResourceMonitor(limits)
    
    def test_get_current_usage(self, monitor):
        """测试获取当前资源使用"""
        usage = monitor.get_current_usage()
        
        assert isinstance(usage, ResourceUsage)
        assert usage.memory_mb >= 0
        assert usage.cpu_percent >= 0
    
    def test_check_throttle_action_none(self, monitor):
        """测试检查节流动作（正常）"""
        usage = ResourceUsage(
            memory_mb=512.0,
            memory_percent=25.0,
            cpu_percent=50.0
        )
        
        action = monitor.check_throttle_action(usage)
        
        from backend.ai_agents.poc_system.verification_engine import ResourceThrottleAction
        assert action == ResourceThrottleAction.NONE
    
    def test_add_callback(self, monitor):
        """测试添加回调"""
        async def callback(usage, action):
            pass
        
        monitor.add_callback(callback)
        
        assert callback in monitor._callbacks


class TestVerificationEngine:
    """测试POC验证引擎"""
    
    @pytest.fixture
    def engine(self):
        with patch('backend.ai_agents.poc_system.verification_engine.Pocsuite3Agent'):
            with patch('backend.ai_agents.poc_system.verification_engine.poc_manager'):
                engine = VerificationEngine(max_concurrent=5)
                return engine
    
    def test_engine_initialization(self, engine):
        """测试引擎初始化"""
        assert engine is not None
        assert hasattr(engine, 'active_executions')
        assert hasattr(engine, 'execution_semaphore')
        assert hasattr(engine, '_execution_queue')
        assert hasattr(engine, '_resource_monitor')
    
    def test_set_max_concurrent_executions(self, engine):
        """测试设置最大并发数"""
        engine.set_max_concurrent_executions(10)
        
        assert engine._max_concurrent == 10
    
    def test_get_resource_limits(self, engine):
        """测试获取资源限制"""
        limits = engine.get_resource_limits()
        
        assert isinstance(limits, ResourceLimits)
    
    def test_set_resource_limits(self, engine):
        """测试设置资源限制"""
        new_limits = ResourceLimits(
            max_memory_mb=2048,
            max_cpu_percent=90.0
        )
        
        engine.set_resource_limits(new_limits)
        limits = engine.get_resource_limits()
        
        assert limits.max_memory_mb == 2048
        assert limits.max_cpu_percent == 90.0
    
    def test_get_execution_statistics(self, engine):
        """测试获取执行统计"""
        stats = engine.get_execution_statistics()
        
        assert isinstance(stats, ExecutionStats)
    
    def test_get_queue_status(self, engine):
        """测试获取队列状态"""
        status = engine.get_queue_status()
        
        assert isinstance(status, dict)
        assert "queue_size" in status
        assert "running_count" in status
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, engine):
        """测试清除缓存"""
        await engine.clear_cache()
        
        stats = await engine.get_cache_stats()
        assert stats["size"] == 0
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, engine):
        """测试获取缓存统计"""
        stats = await engine.get_cache_stats()
        
        assert isinstance(stats, dict)
        assert "size" in stats


class TestExecutionPriority:
    """测试执行优先级"""
    
    def test_priority_values(self):
        """测试优先级值"""
        assert ExecutionPriority.LOW.value == 1
        assert ExecutionPriority.NORMAL.value == 5
        assert ExecutionPriority.HIGH.value == 10
        assert ExecutionPriority.CRITICAL.value == 20
    
    def test_priority_comparison(self):
        """测试优先级比较"""
        assert ExecutionPriority.CRITICAL.value > ExecutionPriority.HIGH.value
        assert ExecutionPriority.HIGH.value > ExecutionPriority.NORMAL.value
        assert ExecutionPriority.NORMAL.value > ExecutionPriority.LOW.value


class TestExecutionStatus:
    """测试执行状态"""
    
    def test_status_values(self):
        """测试状态值"""
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.QUEUED.value == "queued"
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.COMPLETED.value == "completed"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.CANCELLED.value == "cancelled"
        assert ExecutionStatus.TIMEOUT.value == "timeout"


class TestPrioritizedTask:
    """测试优先级任务"""
    
    def test_task_creation(self):
        """测试创建优先级任务"""
        config = ExecutionConfig(
            poc_id="test_poc",
            target="https://example.com",
            poc_code="print('test')"
        )
        
        task = PrioritizedTask(
            priority=1,
            sequence=1,
            task_data={"test": "data"},
            config=config
        )
        
        assert task.priority == 1
        assert task.sequence == 1
        assert task.task_data == {"test": "data"}
        assert task.config == config
    
    def test_task_ordering(self):
        """测试任务排序"""
        config = ExecutionConfig(
            poc_id="test",
            target="https://example.com",
            poc_code="print('test')"
        )
        
        task1 = PrioritizedTask(priority=1, sequence=1, task_data={}, config=config)
        task2 = PrioritizedTask(priority=2, sequence=2, task_data={}, config=config)
        
        assert task1 < task2


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

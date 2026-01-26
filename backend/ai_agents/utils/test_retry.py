"""
测试重试策略模块

测试 RetryStrategy、ExponentialBackoffRetry、FixedIntervalRetry 类和装饰器的功能。
"""
import pytest
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_agents.utils.retry import (
    RetryStrategy,
    ExponentialBackoffRetry,
    FixedIntervalRetry,
    retry_on_failure
)


class TestExponentialBackoffRetry:
    """
    测试指数退避重试策略类
    """

    @pytest.fixture
    def retry_strategy(self):
        """
        创建指数退避重试策略实例
        """
        return ExponentialBackoffRetry(base_delay=1.0, max_delay=60.0)

    def test_initialization(self, retry_strategy):
        """
        测试初始化
        """
        assert retry_strategy is not None
        assert retry_strategy.base_delay == 1.0
        assert retry_strategy.max_delay == 60.0

    @pytest.mark.asyncio
    async def test_execute_success_first_attempt(self, retry_strategy):
        """
        测试执行（第一次成功）
        """
        async def successful_func():
            return 'success'
        
        result = await retry_strategy.execute(successful_func, max_retries=3)
        
        assert result == 'success'

    @pytest.mark.asyncio
    async def test_execute_success_after_retry(self, retry_strategy):
        """
        测试执行（重试后成功）
        """
        attempt_count = [0]
        
        async def func_with_retry():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise ValueError('Temporary error')
            return 'success'
        
        result = await retry_strategy.execute(func_with_retry, max_retries=5)
        
        assert result == 'success'
        assert attempt_count[0] == 3

    @pytest.mark.asyncio
    async def test_execute_all_retries_failed(self, retry_strategy):
        """
        测试执行（所有重试失败）
        """
        async def failing_func():
            raise ValueError('Persistent error')
        
        with pytest.raises(ValueError, match='Persistent error'):
            await retry_strategy.execute(failing_func, max_retries=3)

    @pytest.mark.asyncio
    async def test_execute_delay_calculation(self, retry_strategy):
        """
        测试延迟计算
        """
        attempt_times = []
        
        async def func_with_delay():
            attempt_times.append(asyncio.get_event_loop().time())
            if len(attempt_times) < 3:
                raise ValueError('Temporary error')
            return 'success'
        
        await retry_strategy.execute(func_with_delay, max_retries=5)
        
        assert len(attempt_times) == 3
        if len(attempt_times) >= 2:
            delay1 = attempt_times[1] - attempt_times[0]
            delay2 = attempt_times[2] - attempt_times[1]
            assert delay2 > delay1

    @pytest.mark.asyncio
    async def test_execute_max_delay_limit(self, retry_strategy):
        """
        测试最大延迟限制
        """
        retry_strategy = ExponentialBackoffRetry(base_delay=0.1, max_delay=0.3)
        
        attempt_count = [0]
        
        async def func_with_many_retries():
            attempt_count[0] += 1
            if attempt_count[0] < 5:
                raise ValueError('Temporary error')
            return 'success'
        
        start_time = asyncio.get_event_loop().time()
        await retry_strategy.execute(func_with_many_retries, max_retries=10)
        end_time = asyncio.get_event_loop().time()
        
        total_time = end_time - start_time
        assert total_time < 2.0

    @pytest.mark.asyncio
    async def test_execute_sync_function(self, retry_strategy):
        """
        测试执行同步函数
        """
        def sync_func():
            return 'sync success'
        
        result = await retry_strategy.execute(sync_func, max_retries=3)
        
        assert result == 'sync success'


class TestFixedIntervalRetry:
    """
    测试固定间隔重试策略类
    """

    @pytest.fixture
    def retry_strategy(self):
        """
        创建固定间隔重试策略实例
        """
        return FixedIntervalRetry(delay=0.5)

    def test_initialization(self, retry_strategy):
        """
        测试初始化
        """
        assert retry_strategy is not None
        assert retry_strategy.delay == 0.5

    @pytest.mark.asyncio
    async def test_execute_success_first_attempt(self, retry_strategy):
        """
        测试执行（第一次成功）
        """
        async def successful_func():
            return 'success'
        
        result = await retry_strategy.execute(successful_func, max_retries=3)
        
        assert result == 'success'

    @pytest.mark.asyncio
    async def test_execute_success_after_retry(self, retry_strategy):
        """
        测试执行（重试后成功）
        """
        attempt_count = [0]
        
        async def func_with_retry():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError('Temporary error')
            return 'success'
        
        result = await retry_strategy.execute(func_with_retry, max_retries=5)
        
        assert result == 'success'
        assert attempt_count[0] == 2

    @pytest.mark.asyncio
    async def test_execute_all_retries_failed(self, retry_strategy):
        """
        测试执行（所有重试失败）
        """
        async def failing_func():
            raise ValueError('Persistent error')
        
        with pytest.raises(ValueError, match='Persistent error'):
            await retry_strategy.execute(failing_func, max_retries=3)

    @pytest.mark.asyncio
    async def test_execute_fixed_delay(self, retry_strategy):
        """
        测试固定延迟
        """
        attempt_times = []
        
        async def func_with_delay():
            attempt_times.append(asyncio.get_event_loop().time())
            if len(attempt_times) < 3:
                raise ValueError('Temporary error')
            return 'success'
        
        await retry_strategy.execute(func_with_delay, max_retries=5)
        
        assert len(attempt_times) == 3
        if len(attempt_times) >= 2:
            delay1 = attempt_times[1] - attempt_times[0]
            delay2 = attempt_times[2] - attempt_times[1]
            assert abs(delay1 - delay2) < 0.1


class TestRetryDecorator:
    """
    测试重试装饰器
    """

    @pytest.mark.asyncio
    async def test_retry_decorator_async_function(self):
        """
        测试重试装饰器（异步函数）
        """
        attempt_count = [0]
        
        @retry_on_failure(max_retries=3)
        async def async_func():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError('Temporary error')
            return 'success'
        
        result = await async_func()
        
        assert result == 'success'
        assert attempt_count[0] == 2

    @pytest.mark.asyncio
    async def test_retry_decorator_sync_function(self):
        """
        测试重试装饰器（同步函数）
        """
        attempt_count = [0]
        
        @retry_on_failure(max_retries=3)
        def sync_func():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError('Temporary error')
            return 'success'
        
        result = await sync_func()
        
        assert result == 'success'
        assert attempt_count[0] == 2

    @pytest.mark.asyncio
    async def test_retry_decorator_custom_strategy(self):
        """
        测试重试装饰器（自定义策略）
        """
        attempt_count = [0]
        strategy = FixedIntervalRetry(delay=0.1)
        
        @retry_on_failure(max_retries=3, strategy=strategy)
        async def async_func():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError('Temporary error')
            return 'success'
        
        result = await async_func()
        
        assert result == 'success'
        assert attempt_count[0] == 2

    @pytest.mark.asyncio
    async def test_retry_decorator_specific_exception(self):
        """
        测试重试装饰器（特定异常）
        """
        attempt_count = [0]
        
        @retry_on_failure(max_retries=3, exceptions=(ValueError,))
        async def async_func():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError('Temporary error')
            return 'success'
        
        result = await async_func()
        
        assert result == 'success'
        assert attempt_count[0] == 2

    @pytest.mark.asyncio
    async def test_retry_decorator_uncaught_exception(self):
        """
        测试重试装饰器（未捕获异常）
        """
        @retry_on_failure(max_retries=3, exceptions=(ValueError,))
        async def async_func():
            raise TypeError('Uncaught error')
        
        with pytest.raises(TypeError, match='Uncaught error'):
            await async_func()

    @pytest.mark.asyncio
    async def test_retry_decorator_no_retries(self):
        """
        测试重试装饰器（无重试）
        """
        @retry_on_failure(max_retries=0)
        async def async_func():
            raise ValueError('Error')
        
        with pytest.raises(ValueError, match='Error'):
            await async_func()

    @pytest.mark.asyncio
    async def test_retry_decorator_preserves_function_name(self):
        """
        测试重试装饰器（保留函数名）
        """
        @retry_on_failure(max_retries=3)
        async def my_function():
            return 'success'
        
        assert my_function.__name__ == 'my_function'


class TestRetryStrategyBase:
    """
    测试重试策略基类
    """

    def test_execute_not_implemented(self):
        """
        测试基类execute方法未实现
        """
        strategy = RetryStrategy()
        
        async def dummy_func():
            return 'test'
        
        with pytest.raises(NotImplementedError):
            await strategy.execute(dummy_func, max_retries=3)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
测试功能补充模块

测试 CapabilityEnhancer 类的各项功能。
"""
import pytest
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.code_execution.capability_enhancer import (
    CapabilityEnhancer,
    Capability
)


class TestCapability:
    """
    测试能力类
    """

    @pytest.fixture
    def capability(self):
        """
        创建能力实例
        """
        async def dummy_execute(target, **kwargs):
            return {'target': target, 'result': 'success'}
        
        return Capability(
            name='test_capability',
            description='Test capability for testing',
            version='1.0.0',
            dependencies=['requests'],
            execute_func=dummy_execute
        )

    def test_creation(self, capability):
        """
        测试创建能力
        """
        assert capability.name == 'test_capability'
        assert capability.description == 'Test capability for testing'
        assert capability.version == '1.0.0'
        assert capability.dependencies == ['requests']
        assert capability.execute_func is not None
        assert capability.execution_count == 0

    def test_to_dict(self, capability):
        """
        测试转换为字典
        """
        cap_dict = capability.to_dict()
        
        assert cap_dict['name'] == 'test_capability'
        assert cap_dict['description'] == 'Test capability for testing'
        assert cap_dict['version'] == '1.0.0'
        assert cap_dict['dependencies'] == ['requests']
        assert 'created_at' in cap_dict
        assert cap_dict['execution_count'] == 0

    @pytest.mark.asyncio
    async def test_execute(self, capability):
        """
        测试执行能力
        """
        result = await capability.execute('www.baidu.com')
        
        assert result['status'] == 'success'
        assert result['data']['target'] == 'www.baidu.com'
        assert result['data']['result'] == 'success'
        assert result['capability'] == 'test_capability'
        assert result['version'] == '1.0.0'
        assert capability.execution_count == 1

    @pytest.mark.asyncio
    async def test_execute_no_function(self):
        """
        测试执行没有执行函数的能力
        """
        capability = Capability(
            name='test_capability',
            description='Test capability',
            execute_func=None
        )
        
        result = await capability.execute('www.baidu.com')
        
        assert result['status'] == 'failed'
        assert '未定义执行函数' in result['error'] or 'execute function' in result['error'].lower()


class TestCapabilityEnhancer:
    """
    测试功能补充器类
    """

    @pytest.fixture
    def enhancer(self):
        """
        创建功能补充器实例
        """
        return CapabilityEnhancer()

    def test_initialization(self, enhancer):
        """
        测试初始化
        """
        assert enhancer is not None
        assert hasattr(enhancer, 'env_awareness')
        assert hasattr(enhancer, 'code_generator')
        assert hasattr(enhancer, 'capabilities')
        assert isinstance(enhancer.capabilities, dict)

    def test_register_capability(self, enhancer):
        """
        测试注册能力
        """
        async def dummy_execute(target, **kwargs):
            return {'target': target}
        
        enhancer.register_capability(
            name='test_capability',
            description='Test capability',
            execute_func=dummy_execute,
            version='1.0.0',
            dependencies=['requests']
        )
        
        assert 'test_capability' in enhancer.capabilities
        capability = enhancer.capabilities['test_capability']
        assert capability.name == 'test_capability'
        assert capability.description == 'Test capability'

    def test_get_capability(self, enhancer):
        """
        测试获取能力
        """
        async def dummy_execute(target, **kwargs):
            return {'target': target}
        
        enhancer.register_capability(
            name='test_capability',
            description='Test capability',
            execute_func=dummy_execute
        )
        
        capability = enhancer.get_capability('test_capability')
        assert capability is not None
        assert capability.name == 'test_capability'

    def test_get_capability_not_found(self, enhancer):
        """
        测试获取不存在的能力
        """
        capability = enhancer.get_capability('nonexistent_capability')
        assert capability is None

    def test_list_capabilities(self, enhancer):
        """
        测试列出所有能力
        """
        async def dummy_execute(target, **kwargs):
            return {'target': target}
        
        enhancer.register_capability(
            name='capability1',
            description='First capability',
            execute_func=dummy_execute
        )
        
        enhancer.register_capability(
            name='capability2',
            description='Second capability',
            execute_func=dummy_execute
        )
        
        capabilities = enhancer.list_capabilities()
        
        assert isinstance(capabilities, list)
        assert len(capabilities) >= 2
        assert all(isinstance(cap, dict) for cap in capabilities)

    @pytest.mark.asyncio
    async def test_execute_capability(self, enhancer):
        """
        测试执行能力
        """
        async def dummy_execute(target, **kwargs):
            return {'target': target, 'result': 'success'}
        
        enhancer.register_capability(
            name='test_capability',
            description='Test capability',
            execute_func=dummy_execute
        )
        
        result = await enhancer.execute_capability('test_capability', 'www.baidu.com')
        
        assert result['status'] == 'success'
        assert result['data']['target'] == 'www.baidu.com'
        assert result['data']['result'] == 'success'

    @pytest.mark.asyncio
    async def test_execute_capability_not_found(self, enhancer):
        """
        测试执行不存在的能力
        """
        result = await enhancer.execute_capability('nonexistent_capability', 'www.baidu.com')
        
        assert result['status'] == 'failed'
        assert '不存在' in result['error'] or 'not found' in result['error'].lower()

    def test_remove_capability(self, enhancer):
        """
        测试移除能力
        """
        async def dummy_execute(target, **kwargs):
            return {'target': target}
        
        enhancer.register_capability(
            name='test_capability',
            description='Test capability',
            execute_func=dummy_execute
        )
        
        assert 'test_capability' in enhancer.capabilities
        
        result = enhancer.remove_capability('test_capability')
        
        assert result is True
        assert 'test_capability' not in enhancer.capabilities

    def test_remove_capability_not_found(self, enhancer):
        """
        测试移除不存在的能力
        """
        result = enhancer.remove_capability('nonexistent_capability')
        assert result is False

    def test_get_capability_dependencies(self, enhancer):
        """
        测试获取能力的依赖
        """
        async def dummy_execute(target, **kwargs):
            return {'target': target}
        
        enhancer.register_capability(
            name='test_capability',
            description='Test capability',
            execute_func=dummy_execute,
            dependencies=['requests', 'beautifulsoup4']
        )
        
        dependencies = enhancer.get_capability_dependencies('test_capability')
        
        assert isinstance(dependencies, list)
        assert 'requests' in dependencies
        assert 'beautifulsoup4' in dependencies

    def test_check_capability_dependencies(self, enhancer):
        """
        测试检查能力依赖
        """
        async def dummy_execute(target, **kwargs):
            return {'target': target}
        
        enhancer.register_capability(
            name='test_capability',
            description='Test capability',
            execute_func=dummy_execute,
            dependencies=['requests']
        )
        
        result = enhancer.check_capability_dependencies('test_capability')
        
        assert isinstance(result, dict)
        assert 'capability' in result
        assert 'dependencies' in result
        assert 'satisfied' in result
        assert 'missing' in result
        assert 'all_satisfied' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

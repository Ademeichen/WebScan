"""
测试Seebug工具模块

测试Seebug_Agent的统一工具接口。
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.seebug_utils import SeebugUtils, SEBUG_AGENT_AVAILABLE


class TestSeebugUtils:
    """测试Seebug工具类"""
    
    @pytest.fixture
    def seebug_utils(self):
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', True):
            with patch('utils.seebug_utils.SeebugClient'):
                with patch('utils.seebug_utils.POCGenerator'):
                    with patch('utils.seebug_utils.SeebugAgent'):
                        with patch('utils.seebug_utils.SeebugConfig'):
                            return SeebugUtils()
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', True):
            with patch('utils.seebug_utils.SeebugClient'):
                with patch('utils.seebug_utils.POCGenerator'):
                    with patch('utils.seebug_utils.SeebugAgent'):
                        with patch('utils.seebug_utils.SeebugConfig'):
                            utils1 = SeebugUtils()
                            utils2 = SeebugUtils()
                            
                            assert utils1 is utils2
    
    def test_initialization(self, seebug_utils):
        """测试初始化"""
        assert seebug_utils is not None
        assert hasattr(seebug_utils, 'config')
        assert hasattr(seebug_utils, 'client')
        assert hasattr(seebug_utils, 'generator')
        assert hasattr(seebug_utils, 'agent')
    
    def test_is_available(self, seebug_utils):
        """测试检查可用性"""
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', True):
            result = seebug_utils.is_available()
            assert result is True
        
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', False):
            result = seebug_utils.is_available()
            assert result is False
    
    def test_get_client(self, seebug_utils):
        """测试获取客户端"""
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', True):
            client = seebug_utils.get_client()
            assert client is not None
    
    def test_get_client_unavailable(self, seebug_utils):
        """测试获取客户端(不可用)"""
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', False):
            client = seebug_utils.get_client()
            assert client is None
    
    def test_get_generator(self, seebug_utils):
        """测试获取生成器"""
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', True):
            generator = seebug_utils.get_generator()
            assert generator is not None
    
    def test_get_generator_unavailable(self, seebug_utils):
        """测试获取生成器(不可用)"""
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', False):
            generator = seebug_utils.get_generator()
            assert generator is None
    
    def test_get_agent(self, seebug_utils):
        """测试获取Agent"""
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', True):
            agent = seebug_utils.get_agent()
            assert agent is not None
    
    def test_get_agent_unavailable(self, seebug_utils):
        """测试获取Agent(不可用)"""
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', False):
            agent = seebug_utils.get_agent()
            assert agent is None


class TestSeebugUtilsIntegration:
    """测试Seebug工具集成"""
    
    @pytest.mark.asyncio
    async def test_get_pocs_integration(self):
        """测试获取POC集成"""
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', True):
            with patch('utils.seebug_utils.SeebugClient') as mock_client_class:
                mock_client = Mock()
                mock_client.get_pocs = AsyncMock(return_value=[
                    {
                        "poc_id": "seebug_001",
                        "poc_name": "test_poc",
                        "poc_type": "web",
                        "severity": "high"
                    }
                ])
                mock_client_class.return_value = mock_client
                
                with patch('utils.seebug_utils.SeebugConfig'):
                    utils = SeebugUtils()
                    client = utils.get_client()
                    
                    if client:
                        result = await client.get_pocs(limit=10)
                        
                        assert result is not None
                        assert len(result) > 0
                        assert result[0]['poc_id'] == "seebug_001"
    
    @pytest.mark.asyncio
    async def test_generate_poc_integration(self):
        """测试生成POC集成"""
        with patch('utils.seebug_utils.SEEBUG_AGENT_AVAILABLE', True):
            with patch('utils.seebug_utils.POCGenerator') as mock_generator_class:
                mock_generator = Mock()
                mock_generator.generate = AsyncMock(return_value={
                    "poc_code": "def poc_check(target): return True",
                    "poc_name": "generated_poc",
                    "description": "Auto-generated POC"
                })
                mock_generator_class.return_value = mock_generator
                
                with patch('utils.seebug_utils.SeebugConfig'):
                    utils = SeebugUtils()
                    generator = utils.get_generator()
                    
                    if generator:
                        result = await generator.generate(
                            vulnerability="SQL Injection",
                            target="https://example.com"
                        )
                        
                        assert result is not None
                        assert 'poc_code' in result
                        assert 'poc_name' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

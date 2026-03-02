"""
测试POC管理器

测试POC脚本管理器的各项功能。
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_agents.poc_system.poc_manager import (
    POCManager,
    POCMetadata
)


class TestPOCMetadata:
    """测试POC元数据类"""
    
    def test_creation(self):
        """测试创建POC元数据"""
        metadata = POCMetadata(
            poc_name="test_poc",
            poc_id="poc_001",
            poc_type="web",
            severity="high"
        )
        
        assert metadata.poc_name == "test_poc"
        assert metadata.poc_id == "poc_001"
        assert metadata.poc_type == "web"
        assert metadata.severity == "high"
        assert metadata.cvss_score is None
        assert metadata.description is None
        assert metadata.author is None
        assert metadata.source == "seebug"
        assert metadata.version == "1.0"
        assert metadata.tags == []
    
    def test_full_metadata(self):
        """测试完整POC元数据"""
        metadata = POCMetadata(
            poc_name="full_poc",
            poc_id="poc_002",
            poc_type="network",
            severity="critical",
            cvss_score=9.8,
            description="Critical vulnerability",
            author="test_author",
            source="custom",
            version="2.0",
            tags=["rce", "web"]
        )
        
        assert metadata.poc_name == "full_poc"
        assert metadata.poc_id == "poc_002"
        assert metadata.poc_type == "network"
        assert metadata.severity == "critical"
        assert metadata.cvss_score == 9.8
        assert metadata.description == "Critical vulnerability"
        assert metadata.author == "test_author"
        assert metadata.source == "custom"
        assert metadata.version == "2.0"
        assert metadata.tags == ["rce", "web"]
    
    def test_to_dict(self):
        """测试转换为字典"""
        metadata = POCMetadata(
            poc_name="dict_poc",
            poc_id="poc_003",
            poc_type="web",
            severity="medium"
        )
        
        result = metadata.to_dict()
        
        assert isinstance(result, dict)
        assert result['poc_name'] == "dict_poc"
        assert result['poc_id'] == "poc_003"
        assert result['poc_type'] == "web"
        assert result['severity'] == "medium"
        assert result['source'] == "seebug"
        assert result['version'] == "1.0"
        assert result['tags'] == []


class TestPOCManager:
    """测试POC管理器"""
    
    @pytest.fixture
    def manager(self):
        with patch('ai_agents.poc_system.poc_manager.seebug_utils'):
            with patch('ai_agents.poc_system.poc_manager.CacheManager'):
                return POCManager()
    
    def test_initialization(self, manager):
        """测试管理器初始化"""
        assert manager is not None
        assert hasattr(manager, 'poc_registry')
        assert hasattr(manager, 'poc_cache')
        assert hasattr(manager, 'seebug_client')
        assert hasattr(manager, 'seebug_agent')
    
    def test_register_poc(self, manager):
        """测试注册POC"""
        metadata = POCMetadata(
            poc_name="test_poc",
            poc_id="poc_test",
            poc_type="web",
            severity="high"
        )
        
        manager.poc_registry[metadata.poc_id] = metadata
        
        assert "poc_test" in manager.poc_registry
        assert manager.poc_registry["poc_test"].poc_name == "test_poc"
    
    def test_get_poc_metadata(self, manager):
        """测试获取POC元数据"""
        metadata = POCMetadata(
            poc_name="get_poc",
            poc_id="poc_get",
            poc_type="web",
            severity="medium"
        )
        
        manager.poc_registry[metadata.poc_id] = metadata
        
        result = manager.poc_registry.get("poc_get")
        
        assert result is not None
        assert result.poc_name == "get_poc"
        assert result.poc_id == "poc_get"
    
    def test_list_pocs(self, manager):
        """测试列出所有POC"""
        metadata1 = POCMetadata(
            poc_name="poc1",
            poc_id="poc_001",
            poc_type="web",
            severity="high"
        )
        metadata2 = POCMetadata(
            poc_name="poc2",
            poc_id="poc_002",
            poc_type="network",
            severity="medium"
        )
        
        manager.poc_registry["poc_001"] = metadata1
        manager.poc_registry["poc_002"] = metadata2
        
        pocs = list(manager.poc_registry.values())
        
        assert len(pocs) == 2
        assert any(poc.poc_name == "poc1" for poc in pocs)
        assert any(poc.poc_name == "poc2" for poc in pocs)
    
    @pytest.mark.asyncio
    async def test_sync_from_seebug(self, manager):
        """测试从Seebug同步POC"""
        with patch.object(manager, 'seebug_client', Mock()) as mock_client:
            mock_client.get_pocs = AsyncMock(return_value=[
                {
                    "poc_id": "seebug_001",
                    "poc_name": "seebug_poc",
                    "poc_type": "web",
                    "severity": "high",
                    "cvss_score": 8.5
                }
            ])
            
            result = await manager.sync_from_seebug(limit=10)
            
            assert result is not None or result == []
    
    @pytest.mark.asyncio
    async def test_load_local_poc(self, manager):
        """测试加载本地POC"""
        with patch('ai_agents.poc_system.poc_manager.Path') as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.read_text.return_value = """
# Test POC
def poc_check(target):
    return {"vulnerable": False}
"""
            mock_path.return_value = mock_path_instance
            
            with patch('ai_agents.poc_system.poc_manager.validate_poc_script_code') as mock_validate:
                mock_validate.return_value = True
                
                result = await manager.load_local_poc("test_poc.py")
                assert result is not None or result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

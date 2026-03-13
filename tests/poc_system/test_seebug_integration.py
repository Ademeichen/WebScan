"""
POC搜索下载测试

测试Seebug API搜索功能、POC下载功能、POC保存到本地功能。
"""
import pytest
import sys
import os
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.api.seebug_client import SeebugAPIClient, APIResponse


class TestSeebugAPIClient:
    """测试Seebug API客户端"""
    
    @pytest.fixture
    def client(self):
        with patch('backend.api.seebug_client.seebug_utils') as mock_utils:
            mock_utils.get_client.return_value = Mock()
            client = SeebugAPIClient(
                api_key="test_api_key",
                base_url="https://www.seebug.org/api",
                timeout=5.0,
                max_retries=3,
                enable_cache=True
            )
            return client
    
    def test_client_initialization(self, client):
        """测试客户端初始化"""
        assert client.api_key == "test_api_key"
        assert client.base_url == "https://www.seebug.org/api"
        assert client.timeout == 5.0
        assert client.max_retries == 3
        assert client.enable_cache is True
        assert isinstance(client.cache, dict)
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, client):
        """测试API Key验证成功"""
        client.seebug_client.validate_key = Mock(return_value={
            "status": "success",
            "msg": "API Key is valid"
        })
        
        response = await client.validate_api_key()
        
        assert response.success is True
        assert response.status_code == 200
        assert "valid" in response.message.lower() or response.message == "API Key is valid"
    
    @pytest.mark.asyncio
    async def test_validate_api_key_failure(self, client):
        """测试API Key验证失败"""
        client.seebug_client.validate_key = Mock(return_value={
            "status": "error",
            "msg": "Invalid API Key"
        })
        
        response = await client.validate_api_key()
        
        assert response.success is False
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_validate_api_key_exception(self, client):
        """测试API Key验证异常"""
        client.seebug_client.validate_key = Mock(side_effect=Exception("Network error"))
        
        response = await client.validate_api_key()
        
        assert response.success is False
        assert response.status_code == 500
        assert "Network error" in response.message
    
    @pytest.mark.asyncio
    async def test_search_poc_success(self, client):
        """测试POC搜索成功"""
        client.seebug_client.search_poc = Mock(return_value={
            "status": "success",
            "data": {
                "list": [
                    {"ssvid": 12345, "name": "Test POC 1"},
                    {"ssvid": 12346, "name": "Test POC 2"}
                ],
                "total": 2
            },
            "msg": ""
        })
        
        response = await client.search_poc(keyword="weblogic", page=1, page_size=10)
        
        assert response.success is True
        assert response.status_code == 200
        assert response.data is not None
        assert "list" in response.data
        assert len(response.data["list"]) == 2
        assert response.data["total"] == 2
    
    @pytest.mark.asyncio
    async def test_search_poc_empty_result(self, client):
        """测试POC搜索无结果"""
        client.seebug_client.search_poc = Mock(return_value={
            "status": "success",
            "data": {
                "list": [],
                "total": 0
            },
            "msg": ""
        })
        
        response = await client.search_poc(keyword="nonexistent", page=1, page_size=10)
        
        assert response.success is True
        assert response.data["total"] == 0
        assert len(response.data["list"]) == 0
    
    @pytest.mark.asyncio
    async def test_search_poc_with_cache(self, client):
        """测试POC搜索缓存"""
        client.seebug_client.search_poc = Mock(return_value={
            "status": "success",
            "data": {
                "list": [{"ssvid": 12345, "name": "Test POC"}],
                "total": 1
            },
            "msg": ""
        })
        
        response1 = await client.search_poc(keyword="test", page=1, page_size=10)
        response2 = await client.search_poc(keyword="test", page=1, page_size=10)
        
        assert response1.success is True
        assert response2.success is True
        client.seebug_client.search_poc.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_poc_success(self, client):
        """测试POC下载成功"""
        client.seebug_client.download_poc = Mock(return_value={
            "status": "success",
            "data": {
                "poc": "#!/usr/bin/env python\nprint('test poc')"
            },
            "msg": ""
        })
        
        response = await client.download_poc(ssvid=12345)
        
        assert response.success is True
        assert response.status_code == 200
        assert response.data is not None
        assert "code" in response.data
        assert "test poc" in response.data["code"]
    
    @pytest.mark.asyncio
    async def test_download_poc_not_found(self, client):
        """测试POC下载不存在"""
        client.seebug_client.download_poc = Mock(return_value={
            "status": "error",
            "data": {},
            "msg": "POC not found"
        })
        
        response = await client.download_poc(ssvid=99999)
        
        assert response.success is False
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_poc_detail_success(self, client):
        """测试获取POC详情成功"""
        client.seebug_client.get_poc_detail = Mock(return_value={
            "status": "success",
            "data": {
                "ssvid": 12345,
                "name": "WebLogic RCE",
                "severity": "高危",
                "cve": "CVE-2020-2551"
            },
            "msg": ""
        })
        
        response = await client.get_poc_detail(ssvid=12345)
        
        assert response.success is True
        assert response.data is not None
        assert response.data["ssvid"] == 12345
        assert "WebLogic" in response.data["name"]
    
    @pytest.mark.asyncio
    async def test_crawl_recent_vulnerabilities_success(self, client):
        """测试爬取最新漏洞成功"""
        client.seebug_client._search_poc_web = Mock(return_value={
            "status": "success",
            "data": {
                "list": [
                    {"ssvid": 12345, "name": "Vuln 1"},
                    {"ssvid": 12346, "name": "Vuln 2"}
                ]
            }
        })
        client.seebug_client._get_poc_detail_web = Mock(return_value={
            "status": "success",
            "data": {
                "description": "Test description",
                "severity": "high"
            }
        })
        
        response = await client.crawl_recent_vulnerabilities(limit=2)
        
        assert response.success is True
        assert isinstance(response.data, list)
    
    def test_clear_cache(self, client):
        """测试清除缓存"""
        client.cache["test_key"] = ("test_value", datetime.now())
        assert len(client.cache) > 0
        
        client.clear_cache()
        
        assert len(client.cache) == 0
    
    def test_get_cache_stats(self, client):
        """测试获取缓存统计"""
        client.cache["key1"] = ("value1", datetime.now())
        client.cache["key2"] = ("value2", datetime.now())
        
        stats = client.get_cache_stats()
        
        assert "cache_entries" in stats
        assert stats["cache_entries"] == 2
        assert "cache_enabled" in stats
        assert stats["cache_enabled"] is True
    
    def test_get_statistics(self, client):
        """测试获取统计信息"""
        stats = client.get_statistics()
        
        assert "api_key_configured" in stats
        assert "base_url" in stats
        assert "timeout" in stats
        assert "max_retries" in stats
        assert "cache_enabled" in stats
        assert "cache_stats" in stats


class TestPOCSaveToLocal:
    """测试POC保存到本地功能"""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_save_poc_to_file(self, temp_dir):
        """测试保存POC到文件"""
        poc_code = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test POC for WebLogic RCE
"""
def verify(target):
    return {"vulnerable": True, "message": "Test"}
'''
        poc_file_path = os.path.join(temp_dir, "test_poc.py")
        
        with open(poc_file_path, 'w', encoding='utf-8') as f:
            f.write(poc_code)
        
        assert os.path.exists(poc_file_path)
        
        with open(poc_file_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        
        assert saved_content == poc_code
        assert "verify" in saved_content
    
    def test_save_poc_with_metadata(self, temp_dir):
        """测试保存带元数据的POC"""
        poc_data = {
            "name": "WebLogic CVE-2020-2551",
            "code": "#!/usr/bin/env python\nprint('test')",
            "metadata": {
                "cve": "CVE-2020-2551",
                "severity": "high",
                "author": "test"
            }
        }
        
        poc_file_path = os.path.join(temp_dir, "weblogic_cve_2020_2551.py")
        metadata_file_path = os.path.join(temp_dir, "weblogic_cve_2020_2551.json")
        
        with open(poc_file_path, 'w', encoding='utf-8') as f:
            f.write(poc_data["code"])
        
        import json
        with open(metadata_file_path, 'w', encoding='utf-8') as f:
            json.dump(poc_data["metadata"], f, ensure_ascii=False, indent=2)
        
        assert os.path.exists(poc_file_path)
        assert os.path.exists(metadata_file_path)
        
        with open(metadata_file_path, 'r', encoding='utf-8') as f:
            saved_metadata = json.load(f)
        
        assert saved_metadata["cve"] == "CVE-2020-2551"
    
    def test_save_poc_to_nested_directory(self, temp_dir):
        """测试保存POC到嵌套目录"""
        nested_dir = os.path.join(temp_dir, "weblogic", "cve")
        os.makedirs(nested_dir, exist_ok=True)
        
        poc_file_path = os.path.join(nested_dir, "cve_2020_2551.py")
        poc_code = "# Test POC"
        
        with open(poc_file_path, 'w', encoding='utf-8') as f:
            f.write(poc_code)
        
        assert os.path.exists(poc_file_path)
    
    def test_overwrite_existing_poc(self, temp_dir):
        """测试覆盖已存在的POC"""
        poc_file_path = os.path.join(temp_dir, "existing_poc.py")
        
        with open(poc_file_path, 'w', encoding='utf-8') as f:
            f.write("old content")
        
        new_content = "new content"
        with open(poc_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        with open(poc_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == new_content


class TestAPIResponse:
    """测试API响应数据类"""
    
    def test_api_response_creation(self):
        """测试创建API响应"""
        response = APIResponse(
            success=True,
            data={"key": "value"},
            message="Success",
            status_code=200,
            execution_time=0.5
        )
        
        assert response.success is True
        assert response.data == {"key": "value"}
        assert response.message == "Success"
        assert response.status_code == 200
        assert response.execution_time == 0.5
    
    def test_api_response_defaults(self):
        """测试API响应默认值"""
        response = APIResponse(success=False)
        
        assert response.data is None
        assert response.message == ""
        assert response.status_code == 200
        assert response.execution_time == 0.0


class TestSeebugIntegration:
    """Seebug集成测试"""
    
    @pytest.fixture
    def mock_seebug_client(self):
        with patch('backend.api.seebug_client.seebug_utils') as mock_utils:
            mock_client = Mock()
            mock_client.validate_key = Mock(return_value={
                "status": "success",
                "msg": "API Key is valid"
            })
            mock_client.search_poc = Mock(return_value={
                "status": "success",
                "data": {
                    "list": [
                        {"ssvid": 12345, "name": "WebLogic RCE"}
                    ],
                    "total": 1
                },
                "msg": ""
            })
            mock_client.download_poc = Mock(return_value={
                "status": "success",
                "data": {
                    "poc": "#!/usr/bin/env python\nprint('test')"
                },
                "msg": ""
            })
            mock_utils.get_client.return_value = mock_client
            yield mock_client
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, mock_seebug_client):
        """测试完整工作流：验证 -> 搜索 -> 下载"""
        client = SeebugAPIClient(api_key="test_key")
        
        validate_response = await client.validate_api_key()
        assert validate_response.success is True
        
        search_response = await client.search_poc(keyword="weblogic")
        assert search_response.success is True
        assert len(search_response.data["list"]) > 0
        
        ssvid = search_response.data["list"][0]["ssvid"]
        download_response = await client.download_poc(ssvid=ssvid)
        assert download_response.success is True
        assert download_response.data["code"] is not None
    
    @pytest.mark.integration
    @pytest.mark.seebug
    @pytest.mark.asyncio
    async def test_real_api_connection(self):
        """测试真实API连接（需要配置API Key）"""
        from backend.config import settings
        
        if not settings.SEEBUG_API_KEY:
            pytest.skip("需要配置Seebug API Key")
        
        client = SeebugAPIClient()
        response = await client.validate_api_key()
        
        assert response is not None
        assert hasattr(response, 'success')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

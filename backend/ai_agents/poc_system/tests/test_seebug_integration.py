"""
Seebug集成测试

测试Seebug客户端和Agent的各项功能。
"""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.ai_agents.poc_system.tests.conftest import (
    MockSeebugClient,
    MockSeebugAgent,
    load_test_data,
    TEST_DATA_DIR
)


class TestSeebugClient:
    """测试Seebug客户端"""
    
    @pytest.fixture
    def seebug_client(self):
        """创建Seebug客户端fixture"""
        return MockSeebugClient()
    
    def test_initialization(self, seebug_client):
        """测试SeebugClient初始化"""
        assert seebug_client is not None
        assert hasattr(seebug_client, '_search_data')
        assert hasattr(seebug_client, '_detail_data')
        assert hasattr(seebug_client, '_validate_data')
    
    def test_search_poc_success(self, seebug_client):
        """测试POC搜索功能 - 成功"""
        result = seebug_client.search_poc(keyword="thinkphp", page=1, page_size=10)
        
        assert result is not None
        assert result.get("status") == "success"
        assert "data" in result
        
        data = result.get("data", {})
        assert "list" in data
        assert "total" in data
        assert data.get("total") == 10
        
        poc_list = data.get("list", [])
        assert len(poc_list) > 0
        
        first_poc = poc_list[0]
        assert "ssvid" in first_poc
        assert "name" in first_poc
        assert "severity" in first_poc
    
    def test_search_poc_with_pagination(self, seebug_client):
        """测试POC搜索功能 - 分页"""
        result_page1 = seebug_client.search_poc(keyword="rce", page=1, page_size=5)
        result_page2 = seebug_client.search_poc(keyword="rce", page=2, page_size=5)
        
        assert result_page1.get("status") == "success"
        assert result_page2.get("status") == "success"
        
        data1 = result_page1.get("data", {})
        data2 = result_page2.get("data", {})
        
        assert data1.get("page") == 1
        assert data1.get("page_size") == 10
    
    def test_download_poc_success(self, seebug_client):
        """测试POC下载功能 - 成功"""
        ssvid = 99617
        result = seebug_client.download_poc(ssvid)
        
        assert result is not None
        assert result.get("status") == "success"
        assert "data" in result
        
        data = result.get("data", {})
        assert data.get("ssvid") == ssvid
        assert "poc" in data
        
        poc_code = data.get("poc", "")
        assert len(poc_code) > 0
        assert "from pocsuite3" in poc_code.lower() or "class" in poc_code.lower()
    
    def test_download_poc_code_structure(self, seebug_client):
        """测试下载的POC代码结构"""
        ssvid = 99617
        result = seebug_client.download_poc(ssvid)
        
        data = result.get("data", {})
        poc_code = data.get("poc", "")
        
        assert "POCBase" in poc_code or "register_poc" in poc_code
        assert "_verify" in poc_code or "_attack" in poc_code
    
    def test_validate_key_success(self, seebug_client):
        """测试API Key验证功能 - 成功"""
        result = seebug_client.validate_key()
        
        assert result is not None
        assert result.get("status") == "success"
        assert "data" in result
        
        data = result.get("data", {})
        assert "user" in data
        
        user = data.get("user", {})
        assert "id" in user
        assert "username" in user
        assert "vip" in user
    
    def test_search_result_fields(self, seebug_client):
        """测试搜索结果字段完整性"""
        result = seebug_client.search_poc(keyword="log4j")
        
        data = result.get("data", {})
        poc_list = data.get("list", [])
        
        if poc_list:
            poc = poc_list[0]
            required_fields = ["ssvid", "name", "type", "severity", "cvss_score"]
            for field in required_fields:
                assert field in poc, f"缺少必要字段: {field}"
    
    def test_search_result_severity_levels(self, seebug_client):
        """测试搜索结果严重级别"""
        result = seebug_client.search_poc(keyword="rce")
        
        data = result.get("data", {})
        poc_list = data.get("list", [])
        
        valid_severities = ["critical", "high", "medium", "low", "info"]
        
        for poc in poc_list:
            severity = poc.get("severity", "").lower()
            assert severity in valid_severities, f"无效的严重级别: {severity}"


class TestSeebugAgent:
    """测试Seebug Agent"""
    
    @pytest.fixture
    def seebug_agent(self):
        """创建Seebug Agent fixture"""
        return MockSeebugAgent()
    
    def test_initialization(self, seebug_agent):
        """测试SeebugAgent初始化"""
        assert seebug_agent is not None
        assert hasattr(seebug_agent, '_client')
    
    def test_search_vulnerabilities(self, seebug_agent):
        """测试漏洞搜索功能"""
        result = seebug_agent.search_vulnerabilities(
            keyword="thinkphp",
            page=1,
            page_size=10
        )
        
        assert result is not None
        assert result.get("status") == "success"
        assert "data" in result
    
    def test_get_vulnerability_detail(self, seebug_agent):
        """测试获取漏洞详情"""
        ssvid = "99617"
        result = seebug_agent.get_vulnerability_detail(ssvid)
        
        assert result is not None
        assert result.get("status") == "success"
        
        data = result.get("data", {})
        assert data.get("ssvid") == int(ssvid)
        assert "name" in data
        assert "description" in data
        assert "poc" in data
    
    def test_vulnerability_detail_completeness(self, seebug_agent):
        """测试漏洞详情完整性"""
        ssvid = "99617"
        result = seebug_agent.get_vulnerability_detail(ssvid)
        
        data = result.get("data", {})
        
        expected_fields = [
            "ssvid", "name", "type", "severity", 
            "cvss_score", "description", "author", "tags"
        ]
        
        for field in expected_fields:
            assert field in data, f"缺少必要字段: {field}"


class TestSeebugIntegration:
    """测试Seebug集成功能"""
    
    @pytest.fixture
    def mock_seebug_client(self):
        """创建模拟Seebug客户端"""
        return MockSeebugClient()
    
    def test_poc_search_and_download_workflow(self, mock_seebug_client):
        """测试POC搜索和下载工作流"""
        search_result = mock_seebug_client.search_poc(keyword="thinkphp")
        
        assert search_result.get("status") == "success"
        
        data = search_result.get("data", {})
        poc_list = data.get("list", [])
        
        assert len(poc_list) > 0
        
        first_poc = poc_list[0]
        ssvid = first_poc.get("ssvid")
        
        assert ssvid is not None
        
        download_result = mock_seebug_client.download_poc(ssvid)
        
        assert download_result.get("status") == "success"
        
        poc_data = download_result.get("data", {})
        assert "poc" in poc_data
        assert len(poc_data.get("poc", "")) > 0
    
    def test_api_key_validation_workflow(self, mock_seebug_client):
        """测试API Key验证工作流"""
        validate_result = mock_seebug_client.validate_key()
        
        assert validate_result.get("status") == "success"
        
        user_data = validate_result.get("data", {}).get("user", {})
        
        assert user_data.get("vip") is True
        assert user_data.get("api_quota", 0) > 0
    
    def test_poc_save_to_local(self, mock_seebug_client, tmp_path):
        """测试POC保存到本地功能"""
        ssvid = 99617
        download_result = mock_seebug_client.download_poc(ssvid)
        
        assert download_result.get("status") == "success"
        
        poc_code = download_result.get("data", {}).get("poc", "")
        
        assert len(poc_code) > 0
        
        poc_file = tmp_path / f"poc_{ssvid}.py"
        poc_file.write_text(poc_code, encoding="utf-8")
        
        assert poc_file.exists()
        
        saved_content = poc_file.read_text(encoding="utf-8")
        assert saved_content == poc_code
    
    def test_batch_poc_download(self, mock_seebug_client, tmp_path):
        """测试批量POC下载"""
        search_result = mock_seebug_client.search_poc(keyword="rce", page_size=5)
        
        data = search_result.get("data", {})
        poc_list = data.get("list", [])
        
        downloaded_count = 0
        
        for poc in poc_list[:3]:
            ssvid = poc.get("ssvid")
            if ssvid:
                download_result = mock_seebug_client.download_poc(ssvid)
                if download_result.get("status") == "success":
                    poc_code = download_result.get("data", {}).get("poc", "")
                    if poc_code:
                        poc_file = tmp_path / f"poc_{ssvid}.py"
                        poc_file.write_text(poc_code, encoding="utf-8")
                        downloaded_count += 1
        
        assert downloaded_count > 0
    
    def test_search_with_different_keywords(self, mock_seebug_client):
        """测试不同关键词搜索"""
        keywords = ["thinkphp", "log4j", "weblogic", "spring"]
        
        for keyword in keywords:
            result = mock_seebug_client.search_poc(keyword=keyword)
            assert result.get("status") == "success", f"搜索关键词 '{keyword}' 失败"
    
    def test_poc_metadata_extraction(self, mock_seebug_client):
        """测试POC元数据提取"""
        search_result = mock_seebug_client.search_poc(keyword="thinkphp")
        
        data = search_result.get("data", {})
        poc_list = data.get("list", [])
        
        if poc_list:
            poc = poc_list[0]
            
            metadata = {
                "ssvid": poc.get("ssvid"),
                "name": poc.get("name"),
                "severity": poc.get("severity"),
                "cvss_score": poc.get("cvss_score"),
                "type": poc.get("type"),
                "tags": poc.get("tags", [])
            }
            
            assert metadata["ssvid"] is not None
            assert metadata["name"] is not None
            assert metadata["severity"] is not None


class TestSeebugDataValidation:
    """测试Seebug数据验证"""
    
    @pytest.fixture
    def test_data(self):
        """加载测试数据"""
        return {
            "search": load_test_data("seebug/search_response.json"),
            "download": load_test_data("seebug/download_response.json"),
            "validate": load_test_data("seebug/api_validate_response.json"),
            "detail": load_test_data("seebug/vuln_detail_response.json")
        }
    
    def test_search_response_structure(self, test_data):
        """测试搜索响应结构"""
        search_data = test_data["search"]
        
        assert "status" in search_data
        assert "msg" in search_data
        assert "data" in search_data
        
        data = search_data["data"]
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "list" in data
    
    def test_download_response_structure(self, test_data):
        """测试下载响应结构"""
        download_data = test_data["download"]
        
        assert "status" in download_data
        assert "data" in download_data
        
        data = download_data["data"]
        assert "ssvid" in data
        assert "poc" in data
    
    def test_validate_response_structure(self, test_data):
        """测试验证响应结构"""
        validate_data = test_data["validate"]
        
        assert "status" in validate_data
        assert "data" in validate_data
        
        user = validate_data["data"].get("user", {})
        assert "id" in user
        assert "username" in user
        assert "vip" in user
        assert "api_quota" in user
    
    def test_detail_response_structure(self, test_data):
        """测试详情响应结构"""
        detail_data = test_data["detail"]
        
        assert "status" in detail_data
        assert "data" in detail_data
        
        data = detail_data["data"]
        required_fields = [
            "ssvid", "name", "type", "severity",
            "cvss_score", "description", "author", "tags", "poc"
        ]
        
        for field in required_fields:
            assert field in data, f"详情数据缺少字段: {field}"
    
    def test_cvss_score_range(self, test_data):
        """测试CVSS评分范围"""
        search_data = test_data["search"]
        poc_list = search_data.get("data", {}).get("list", [])
        
        for poc in poc_list:
            cvss_score = poc.get("cvss_score", 0)
            assert 0 <= cvss_score <= 10, f"CVSS评分超出范围: {cvss_score}"
    
    def test_severity_consistency(self, test_data):
        """测试严重级别一致性"""
        search_data = test_data["search"]
        poc_list = search_data.get("data", {}).get("list", [])
        
        severity_cvss_map = {
            "critical": (9.0, 10.0),
            "high": (7.0, 8.9),
            "medium": (4.0, 6.9),
            "low": (0.1, 3.9),
            "info": (0.0, 0.0)
        }
        
        for poc in poc_list:
            severity = poc.get("severity", "").lower()
            cvss_score = poc.get("cvss_score", 0)
            
            if severity in severity_cvss_map:
                min_score, max_score = severity_cvss_map[severity]
                assert min_score <= cvss_score <= max_score, \
                    f"严重级别 {severity} 与 CVSS评分 {cvss_score} 不匹配"


@pytest.mark.seebug
class TestSeebugErrorHandling:
    """测试Seebug错误处理"""
    
    def test_invalid_ssvid_handling(self):
        """测试无效SSVID处理"""
        client = MockSeebugClient()
        
        result = client.download_poc(ssvid=99999999)
        
        assert result is not None
        assert "status" in result
    
    def test_empty_search_keyword(self):
        """测试空关键词搜索"""
        client = MockSeebugClient()
        
        result = client.search_poc(keyword="")
        
        assert result is not None
        assert result.get("status") == "success"
    
    def test_large_page_number(self):
        """测试大页码处理"""
        client = MockSeebugClient()
        
        result = client.search_poc(keyword="test", page=9999, page_size=10)
        
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'seebug'])

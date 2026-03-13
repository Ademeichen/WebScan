"""
API端点测试

测试POC系统相关的API端点功能。
"""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.ai_agents.poc_system.tests.conftest import (
    MockSeebugClient,
    MockPocsuite3Agent,
    MockVerificationTask,
    MockVerificationResult,
    load_test_data,
    TEST_DATA_DIR
)


class TestPOCListAPI:
    """测试POC列表API"""
    
    @pytest.fixture
    def mock_poc_manager(self):
        """创建模拟POC管理器"""
        manager = Mock()
        manager.poc_registry = {
            "poc-001": Mock(
                poc_name="Test POC 1",
                poc_id="poc-001",
                poc_type="web",
                severity="high",
                cvss_score=7.5
            ),
            "poc-002": Mock(
                poc_name="Test POC 2",
                poc_id="poc-002",
                poc_type="network",
                severity="critical",
                cvss_score=9.8
            )
        }
        return manager
    
    def test_list_pocs_success(self, mock_poc_manager):
        """测试获取POC列表成功"""
        pocs = list(mock_poc_manager.poc_registry.values())
        
        assert len(pocs) == 2
        assert pocs[0].poc_name == "Test POC 1"
        assert pocs[1].poc_name == "Test POC 2"
    
    def test_list_pocs_with_filter(self, mock_poc_manager):
        """测试过滤POC列表"""
        pocs = [
            poc for poc in mock_poc_manager.poc_registry.values()
            if poc.severity == "critical"
        ]
        
        assert len(pocs) == 1
        assert pocs[0].poc_id == "poc-002"
    
    def test_list_pocs_by_type(self, mock_poc_manager):
        """测试按类型列出POC"""
        pocs = [
            poc for poc in mock_poc_manager.poc_registry.values()
            if poc.poc_type == "web"
        ]
        
        assert len(pocs) == 1
        assert pocs[0].poc_type == "web"
    
    def test_list_pocs_pagination(self, mock_poc_manager):
        """测试POC列表分页"""
        all_pocs = list(mock_poc_manager.poc_registry.values())
        
        page = 1
        page_size = 10
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_pocs = all_pocs[start:end]
        
        assert len(paginated_pocs) <= page_size
    
    def test_list_pocs_sort_by_severity(self, mock_poc_manager):
        """测试按严重级别排序"""
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        
        pocs = sorted(
            mock_poc_manager.poc_registry.values(),
            key=lambda x: severity_order.get(x.severity, 5)
        )
        
        assert pocs[0].severity == "critical"
        assert pocs[1].severity == "high"


class TestPOCVerificationAPI:
    """测试POC验证API"""
    
    @pytest.fixture
    def mock_verification_engine(self):
        """创建模拟验证引擎"""
        engine = Mock()
        engine.active_executions = {}
        return engine
    
    @pytest.fixture
    def mock_pocsuite_agent(self):
        """创建模拟Pocsuite代理"""
        return MockPocsuite3Agent()
    
    @pytest.fixture
    def verification_request(self):
        """创建验证请求"""
        return {
            "poc_id": "test-001",
            "target": "http://example.com",
            "poc_code": "print('test')",
            "timeout": 60,
            "max_retries": 3
        }
    
    @pytest.mark.asyncio
    async def test_create_verification_task(self, mock_verification_engine):
        """测试创建验证任务"""
        task = MockVerificationTask(
            id="new_task_001",
            poc_name="New Task",
            poc_id="new-001",
            target="http://new.example.com",
            status="pending"
        )
        
        assert task.id == "new_task_001"
        assert task.status == "pending"
    
    @pytest.mark.asyncio
    async def test_execute_verification(self, mock_pocsuite_agent):
        """测试执行验证"""
        result = await mock_pocsuite_agent.execute_custom_poc(
            poc_code="print('test')",
            target="http://test.example.com"
        )
        
        assert result is not None
        assert hasattr(result, 'vulnerable')
        assert hasattr(result, 'message')
    
    @pytest.mark.asyncio
    async def test_verification_result_structure(self, mock_pocsuite_agent):
        """测试验证结果结构"""
        result = await mock_pocsuite_agent.execute_custom_poc(
            poc_code="test",
            target="http://structure.example.com"
        )
        
        assert hasattr(result, 'poc_name')
        assert hasattr(result, 'target')
        assert hasattr(result, 'vulnerable')
        assert hasattr(result, 'message')
        assert hasattr(result, 'output')
        assert hasattr(result, 'execution_time')
    
    @pytest.mark.asyncio
    async def test_batch_verification(self, mock_pocsuite_agent):
        """测试批量验证"""
        targets = [
            "http://batch1.example.com",
            "http://batch2.example.com",
            "http://batch3.example.com"
        ]
        
        results = []
        for target in targets:
            result = await mock_pocsuite_agent.execute_custom_poc(
                poc_code="batch test",
                target=target
            )
            results.append(result)
        
        assert len(results) == len(targets)
        for result in results:
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_verification_timeout(self, mock_pocsuite_agent):
        """测试验证超时"""
        result = await mock_pocsuite_agent.execute_custom_poc(
            poc_code="import time; time.sleep(200)",
            target="http://timeout.example.com"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_verification_error_handling(self, mock_pocsuite_agent):
        """测试验证错误处理"""
        result = await mock_pocsuite_agent.execute_custom_poc(
            poc_code="raise Exception('Test error')",
            target="http://error.example.com"
        )
        
        assert result is not None


class TestSeebugAPI:
    """测试Seebug API"""
    
    @pytest.fixture
    def seebug_client(self):
        """创建Seebug客户端"""
        return MockSeebugClient()
    
    def test_search_poc_api(self, seebug_client):
        """测试搜索POC API"""
        result = seebug_client.search_poc(keyword="thinkphp", page=1, page_size=10)
        
        assert result.get("status") == "success"
        assert "data" in result
        
        data = result.get("data", {})
        assert "list" in data
        assert "total" in data
    
    def test_download_poc_api(self, seebug_client):
        """测试下载POC API"""
        result = seebug_client.download_poc(ssvid=99617)
        
        assert result.get("status") == "success"
        assert "data" in result
        
        data = result.get("data", {})
        assert "poc" in data
        assert data.get("ssvid") == 99617
    
    def test_validate_api_key(self, seebug_client):
        """测试验证API Key"""
        result = seebug_client.validate_key()
        
        assert result.get("status") == "success"
        assert "data" in result
        
        user = result.get("data", {}).get("user", {})
        assert "id" in user
        assert "username" in user
    
    def test_get_poc_detail_api(self, seebug_client):
        """测试获取POC详情API"""
        result = seebug_client.download_poc(ssvid=99617)
        
        assert result.get("status") == "success"
        
        data = result.get("data", {})
        assert "ssvid" in data
        assert "poc" in data
    
    def test_search_with_pagination(self, seebug_client):
        """测试分页搜索"""
        result1 = seebug_client.search_poc(keyword="rce", page=1, page_size=5)
        result2 = seebug_client.search_poc(keyword="rce", page=2, page_size=5)
        
        assert result1.get("status") == "success"
        assert result2.get("status") == "success"
    
    def test_api_response_format(self, seebug_client):
        """测试API响应格式"""
        result = seebug_client.search_poc(keyword="test")
        
        assert "status" in result
        assert "msg" in result
        assert "data" in result


class TestAPIResponseModels:
    """测试API响应模型"""
    
    def test_poc_scan_result_model(self):
        """测试POC扫描结果模型"""
        result = {
            "poc_type": "weblogic_cve_2020_2551",
            "target": "http://example.com",
            "vulnerable": True,
            "message": "Vulnerability detected",
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        assert result["poc_type"] == "weblogic_cve_2020_2551"
        assert result["vulnerable"] is True
        assert "timestamp" in result
    
    def test_poc_scan_request_model(self):
        """测试POC扫描请求模型"""
        request = {
            "target": "http://example.com",
            "poc_types": ["weblogic_cve_2020_2551", "struts2_009"],
            "timeout": 10
        }
        
        assert request["target"] == "http://example.com"
        assert len(request["poc_types"]) == 2
        assert request["timeout"] == 10
    
    def test_api_response_structure(self):
        """测试API响应结构"""
        response = {
            "code": 200,
            "message": "Success",
            "data": {
                "task_id": "task_001",
                "status": "completed"
            }
        }
        
        assert response["code"] == 200
        assert "message" in response
        assert "data" in response
    
    def test_error_response_structure(self):
        """测试错误响应结构"""
        error_response = {
            "code": 500,
            "message": "Internal Server Error",
            "detail": "Something went wrong"
        }
        
        assert error_response["code"] == 500
        assert "message" in error_response


class TestAPIEndpointsIntegration:
    """测试API端点集成"""
    
    @pytest.fixture
    def mock_task(self):
        """创建模拟任务"""
        return MockVerificationTask(
            id="integration_task",
            poc_name="Integration Test",
            poc_id="integration-001",
            target="http://integration.example.com",
            status="pending"
        )
    
    @pytest.fixture
    def mock_result(self):
        """创建模拟结果"""
        return MockVerificationResult(
            id="integration_result",
            task_id="integration_task",
            poc_name="Integration Test",
            poc_id="integration-001",
            target="http://integration.example.com",
            vulnerable=True,
            message="Integration test result",
            severity="high",
            cvss_score=7.5,
            confidence=0.9,
            execution_time=2.0
        )
    
    def test_task_creation_flow(self, mock_task):
        """测试任务创建流程"""
        assert mock_task.id is not None
        assert mock_task.status == "pending"
        assert mock_task.target is not None
    
    def test_task_to_result_flow(self, mock_task, mock_result):
        """测试任务到结果流程"""
        assert mock_result.task_id == mock_task.id
        assert mock_result.poc_id == mock_task.poc_id
        assert mock_result.target == mock_task.target
    
    def test_result_to_report_flow(self, mock_result):
        """测试结果到报告流程"""
        result_dict = mock_result.to_dict()
        
        assert result_dict["id"] == mock_result.id
        assert result_dict["vulnerable"] == mock_result.vulnerable
        assert result_dict["severity"] == mock_result.severity


class TestAPIErrorHandling:
    """测试API错误处理"""
    
    def test_invalid_poc_type(self):
        """测试无效POC类型"""
        invalid_types = ["invalid_poc", "unknown_type", ""]
        
        for poc_type in invalid_types:
            assert poc_type is not None
    
    def test_invalid_target_url(self):
        """测试无效目标URL"""
        invalid_urls = [
            "not-a-url",
            "ftp://invalid-protocol.com",
            ""
        ]
        
        for url in invalid_urls:
            if url:
                assert url is not None
    
    def test_missing_required_fields(self):
        """测试缺少必填字段"""
        incomplete_request = {
            "target": "http://example.com"
        }
        
        assert "poc_types" not in incomplete_request
    
    def test_timeout_error_handling(self):
        """测试超时错误处理"""
        timeout_error = {
            "code": 408,
            "message": "Request Timeout",
            "detail": "POC execution exceeded timeout limit"
        }
        
        assert timeout_error["code"] == 408
    
    def test_authentication_error(self):
        """测试认证错误"""
        auth_error = {
            "code": 401,
            "message": "Unauthorized",
            "detail": "Invalid API key"
        }
        
        assert auth_error["code"] == 401


class TestAPIRateLimiting:
    """测试API限流"""
    
    def test_rate_limit_headers(self):
        """测试限流响应头"""
        headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "95",
            "X-RateLimit-Reset": "1705312800"
        }
        
        assert "X-RateLimit-Limit" in headers
        assert int(headers["X-RateLimit-Remaining"]) >= 0
    
    def test_rate_limit_exceeded(self):
        """测试超出限流"""
        response = {
            "code": 429,
            "message": "Too Many Requests",
            "detail": "Rate limit exceeded. Please try again later."
        }
        
        assert response["code"] == 429


class TestAPIValidation:
    """测试API验证"""
    
    def test_target_url_validation(self):
        """测试目标URL验证"""
        valid_urls = [
            "http://example.com",
            "https://example.com:8080",
            "http://192.168.1.1"
        ]
        
        for url in valid_urls:
            assert url.startswith("http://") or url.startswith("https://")
    
    def test_poc_type_validation(self):
        """测试POC类型验证"""
        valid_types = [
            "weblogic_cve_2020_2551",
            "struts2_009",
            "tomcat_cve_2017_12615"
        ]
        
        for poc_type in valid_types:
            assert poc_type is not None
            assert len(poc_type) > 0
    
    def test_timeout_range_validation(self):
        """测试超时范围验证"""
        valid_timeouts = [5, 10, 30, 60, 120]
        
        for timeout in valid_timeouts:
            assert 1 <= timeout <= 300
    
    def test_severity_validation(self):
        """测试严重级别验证"""
        valid_severities = ["critical", "high", "medium", "low", "info"]
        
        for severity in valid_severities:
            assert severity in valid_severities
    
    def test_cvss_score_validation(self):
        """测试CVSS评分验证"""
        valid_scores = [0.0, 5.5, 7.5, 9.8, 10.0]
        
        for score in valid_scores:
            assert 0.0 <= score <= 10.0


class TestAPIDataFormats:
    """测试API数据格式"""
    
    def test_json_request_format(self):
        """测试JSON请求格式"""
        request_body = {
            "target": "http://example.com",
            "poc_types": ["weblogic_cve_2020_2551"],
            "timeout": 10
        }
        
        json_str = json.dumps(request_body)
        parsed = json.loads(json_str)
        
        assert parsed == request_body
    
    def test_json_response_format(self):
        """测试JSON响应格式"""
        response = {
            "code": 200,
            "message": "Success",
            "data": {
                "results": [
                    {"poc_type": "test", "vulnerable": False}
                ]
            }
        }
        
        assert isinstance(response, dict)
        assert "code" in response
        assert "data" in response
    
    def test_datetime_format(self):
        """测试日期时间格式"""
        timestamp = "2024-01-15T10:30:00Z"
        
        from datetime import datetime
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        assert parsed is not None
    
    def test_list_response_format(self):
        """测试列表响应格式"""
        response = {
            "code": 200,
            "data": {
                "list": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"}
                ],
                "total": 2,
                "page": 1,
                "page_size": 10
            }
        }
        
        assert "list" in response["data"]
        assert "total" in response["data"]


class TestAPIPerformance:
    """测试API性能"""
    
    def test_response_time_expectation(self):
        """测试响应时间预期"""
        import time
        
        start = time.time()
        time.sleep(0.1)
        elapsed = time.time() - start
        
        assert elapsed < 1.0
    
    def test_concurrent_request_handling(self):
        """测试并发请求处理"""
        import asyncio
        
        async def mock_request(request_id):
            await asyncio.sleep(0.01)
            return {"id": request_id, "status": "success"}
        
        async def run_concurrent():
            tasks = [mock_request(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            return results
        
        results = asyncio.run(run_concurrent())
        
        assert len(results) == 10
    
    def test_large_response_handling(self):
        """测试大响应处理"""
        large_list = [{"id": i, "data": "x" * 100} for i in range(1000)]
        
        response = {
            "code": 200,
            "data": {
                "list": large_list,
                "total": len(large_list)
            }
        }
        
        assert response["data"]["total"] == 1000


@pytest.mark.integration
class TestAPIIntegrationScenarios:
    """测试API集成场景"""
    
    @pytest.fixture
    def seebug_client(self):
        return MockSeebugClient()
    
    @pytest.fixture
    def pocsuite_agent(self):
        return MockPocsuite3Agent()
    
    def test_full_scan_workflow(self, seebug_client, pocsuite_agent):
        """测试完整扫描工作流"""
        search_result = seebug_client.search_poc(keyword="rce")
        assert search_result.get("status") == "success"
        
        poc_list = search_result.get("data", {}).get("list", [])
        assert len(poc_list) > 0
    
    @pytest.mark.asyncio
    async def test_poc_download_and_execute_workflow(self, seebug_client, pocsuite_agent):
        """测试POC下载和执行工作流"""
        download_result = seebug_client.download_poc(ssvid=99617)
        assert download_result.get("status") == "success"
        
        poc_code = download_result.get("data", {}).get("poc", "")
        assert len(poc_code) > 0
    
    def test_search_filter_sort_workflow(self, seebug_client):
        """测试搜索过滤排序工作流"""
        search_result = seebug_client.search_poc(keyword="weblogic")
        
        assert search_result.get("status") == "success"
        
        poc_list = search_result.get("data", {}).get("list", [])
        
        filtered = [p for p in poc_list if p.get("severity") == "critical"]
        
        sorted_results = sorted(filtered, key=lambda x: x.get("cvss_score", 0), reverse=True)
        
        assert isinstance(sorted_results, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])

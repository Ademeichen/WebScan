"""
AWVS API测试

测试AWVS漏洞扫描相关的API端点。
"""
import pytest
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from backend.api.awvs import router, POC_Check


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router, prefix="/awvs")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_awvs_client():
    with patch('backend.api.awvs.get_awvs_client') as mock:
        mock.return_value = {
            'api_url': 'https://example.com',
            'api_key': 'test-api-key'
        }
        yield mock


@pytest.fixture
def mock_task_model():
    with patch('backend.api.awvs.Task') as mock:
        mock.create = AsyncMock(return_value=Mock(
            id=1,
            task_name="Test Task",
            target="http://example.com",
            status="pending",
            progress=0,
            config=json.dumps({'scan_type': 'full_scan'})
        ))
        mock.filter = Mock(return_value=Mock(
            order_by=Mock(return_value=Mock(
                all=AsyncMock(return_value=[])
            ))
        ))
        yield mock


class TestAWVSHealthEndpoint:
    """测试AWVS健康检查端点"""
    
    def test_health_check_success(self, client, mock_awvs_client):
        """测试健康检查成功"""
        with patch('backend.api.awvs.Dashboard') as mock_dashboard:
            mock_dashboard.return_value.stats.return_value = '{"status": "ok"}'
            
            response = client.get("/awvs/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data['code'] == 200
            assert data['data']['status'] == 'connected'
    
    def test_health_check_failure(self, client, mock_awvs_client):
        """测试健康检查失败"""
        with patch('backend.api.awvs.Dashboard') as mock_dashboard:
            mock_dashboard.return_value.stats.side_effect = Exception("Connection failed")
            
            response = client.get("/awvs/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data['code'] == 503
            assert data['data']['status'] == 'disconnected'


class TestAWVSTargetEndpoints:
    """测试AWVS目标管理端点"""
    
    def test_get_targets_success(self, client, mock_awvs_client):
        """测试获取目标列表成功"""
        with patch('backend.api.awvs.Target') as mock_target:
            mock_target.return_value.get_all.return_value = [
                {'target_id': 'target-001', 'address': 'http://example.com'}
            ]
            
            response = client.get("/awvs/targets")
            
            assert response.status_code == 200
            data = response.json()
            assert data['code'] == 200
            assert len(data['data']) == 1
    
    def test_add_target_success(self, client, mock_awvs_client):
        """测试添加目标成功"""
        with patch('backend.api.awvs.Target') as mock_target:
            mock_target.return_value.add.return_value = 'target-new-id'
            
            response = client.post("/awvs/target", json={
                'address': 'http://new-target.com',
                'description': 'Test target'
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data['code'] == 200
            assert data['data']['target_id'] == 'target-new-id'
    
    def test_add_target_failure(self, client, mock_awvs_client):
        """测试添加目标失败"""
        with patch('backend.api.awvs.Target') as mock_target:
            mock_target.return_value.add.return_value = None
            
            response = client.post("/awvs/target", json={
                'address': 'http://invalid-target.com'
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data['code'] == 400


class TestAWVSScanEndpoints:
    """测试AWVS扫描端点"""
    
    def test_create_scan_success(self, client, mock_awvs_client):
        """测试创建扫描任务成功"""
        with patch('backend.api.awvs.Task') as mock_task:
            mock_task.create = AsyncMock(return_value=Mock(
                id=1,
                task_name="AWVS Scan: http://example.com",
                target="http://example.com",
                status="pending",
                progress=0
            ))
            
            with patch('backend.task_executor.task_executor') as mock_executor:
                mock_executor.start_task = AsyncMock()
                
                response = client.post("/awvs/scan", json={
                    'url': 'http://example.com',
                    'scan_type': 'full_scan'
                })
                
                assert response.status_code == 200
                data = response.json()
                assert data['code'] == 200
                assert 'task_id' in data['data']
    
    def test_get_scans_success(self, client, mock_awvs_client):
        """测试获取扫描列表成功"""
        with patch('backend.api.awvs.sync_scans_from_awvs') as mock_sync, \
             patch('backend.api.awvs.Task') as mock_task, \
             patch('backend.api.awvs.Vulnerability') as mock_vuln:
            
            mock_sync.return_value = AsyncMock()
            mock_task.filter = Mock(return_value=Mock(
                order_by=Mock(return_value=Mock(
                    all=AsyncMock(return_value=[])
                ))
            ))
            
            response = client.get("/awvs/scans")
            
            assert response.status_code == 200
            data = response.json()
            assert data['code'] == 200


class TestAWVSVulnerabilityEndpoints:
    """测试AWVS漏洞端点"""
    
    def test_get_vulnerability_rank(self, client, mock_awvs_client):
        """测试获取漏洞排名"""
        with patch('backend.api.awvs.Dashboard') as mock_dashboard:
            mock_instance = Mock()
            mock_instance.stats.return_value = json.dumps({
                'top_vulnerabilities': [
                    {'name': 'XSS', 'count': 10},
                    {'name': 'SQL Injection', 'count': 5}
                ]
            })
            mock_dashboard.return_value = mock_instance
            
            response = client.get("/awvs/vulnerabilities/rank")
            
            assert response.status_code == 200
            data = response.json()
            assert data['code'] == 200
    
    def test_get_vulnerability_stats(self, client, mock_awvs_client):
        """测试获取漏洞统计"""
        with patch('backend.api.awvs.Dashboard') as mock_dashboard:
            mock_instance = Mock()
            mock_instance.stats.return_value = json.dumps({
                'vuln_count_by_criticality': {
                    'high': {'critical': 5, 'high': 10},
                    'normal': {'medium': 20, 'low': 30}
                }
            })
            mock_dashboard.return_value = mock_instance
            
            response = client.get("/awvs/vulnerabilities/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data['code'] == 200


class TestMiddlewarePOCEndpoints:
    """测试中间件POC端点"""
    
    def test_get_middleware_poc_list(self, client):
        """测试获取中间件POC列表"""
        response = client.get("/awvs/middleware/poc-list")
        
        assert response.status_code == 200
        data = response.json()
        assert data['code'] == 200
        assert len(data['data']) > 0
        
        poc_ids = [poc['cve_id'] for poc in data['data']]
        assert 'CVE-2020-2551' in poc_ids
        assert 'CVE-2017-12615' in poc_ids
    
    def test_create_middleware_scan(self, client, mock_awvs_client):
        """测试创建中间件扫描任务"""
        with patch('backend.api.awvs.Task') as mock_task:
            mock_task.create = AsyncMock(return_value=Mock(
                id=1,
                task_name="Middleware POC Scan: CVE_2020_2551",
                target="http://example.com",
                status="running",
                progress=0
            ))
            
            response = client.post("/awvs/middleware/scan", json={
                'url': 'http://example.com',
                'cve_id': 'CVE-2020-2551'
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data['code'] == 200
            assert 'task_id' in data['data']


class TestPOCCheck:
    """测试POC检查函数"""
    
    def test_poc_check_unknown_cve(self):
        """测试未知CVE ID"""
        result, message = POC_Check("http://example.com", "CVE-9999-9999")
        
        assert result == False
        assert "未知" in message
    
    def test_poc_check_format_handling(self):
        """测试CVE ID格式处理"""
        with patch('backend.api.awvs.cve_2020_2551_poc') as mock_poc:
            mock_poc.poc.return_value = (False, "Not vulnerable")
            
            result, message = POC_Check("http://example.com", "CVE-2020-2551")
            
            mock_poc.poc.assert_called_once()


class TestStatusMapping:
    """测试状态映射"""
    
    def test_map_awvs_status_processing(self):
        """测试AWVS状态映射 - processing"""
        from backend.api.awvs import map_awvs_status
        
        assert map_awvs_status('processing') == 'running'
        assert map_awvs_status('queued') == 'pending'
        assert map_awvs_status('completed') == 'completed'
        assert map_awvs_status('failed') == 'failed'
        assert map_awvs_status('aborted') == 'cancelled'
    
    def test_map_severity_critical(self):
        """测试严重程度映射 - Critical"""
        from backend.api.awvs import map_severity
        
        assert map_severity(3, 'SQL Injection') == 'Critical'
        assert map_severity(3, 'Remote Code Execution') == 'Critical'
        assert map_severity(3, 'Normal High') == 'High'
        assert map_severity(2, 'Medium Vuln') == 'Medium'
        assert map_severity(1, 'Low Vuln') == 'Low'
        assert map_severity(0, 'Info') == 'Info'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

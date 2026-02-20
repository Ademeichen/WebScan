"""
API错误处理测试

测试API端点的错误处理和边界条件。
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from main import app
from config import settings


class TestAPIErrorHandling:
    """API错误处理测试"""

    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)

    def test_health_endpoint_success(self, client):
        """测试健康检查端点成功"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_health_endpoint_with_error(self, client):
        """测试健康检查端点错误"""
        with patch('main.get_system_status') as mock_status:
            mock_status.side_effect = Exception("System error")
            response = client.get("/health")
            assert response.status_code == 500

    def test_poc_files_with_empty_list(self, client):
        """测试POC文件列表为空"""
        with patch('api.poc_files.get_poc_files') as mock_files:
            mock_files.return_value = []
            response = client.get("/api/poc/files")
            assert response.status_code == 200
            assert response.json()["files"] == []

    def test_poc_files_with_invalid_path(self, client):
        """测试POC文件无效路径"""
        response = client.get("/api/poc/files?path=../../../etc/passwd")
        assert response.status_code == 400

    def test_poc_files_with_nonexistent_file(self, client):
        """测试POC文件不存在"""
        response = client.get("/api/poc/files/nonexistent.py")
        assert response.status_code == 404

    def test_agent_scan_with_invalid_target(self, client):
        """测试Agent扫描无效目标"""
        response = client.post(
            "/api/ai_agents/scan",
            json={"target": ""}
        )
        assert response.status_code == 400

    def test_agent_scan_with_missing_target(self, client):
        """测试Agent扫描缺少目标"""
        response = client.post(
            "/api/ai_agents/scan",
            json={}
        )
        assert response.status_code == 422

    def test_agent_scan_with_very_long_target(self, client):
        """测试Agent扫描超长目标"""
        very_long_target = "http://" + "a" * 10000 + ".com"
        response = client.post(
            "/api/ai_agents/scan",
            json={"target": very_long_target}
        )
        assert response.status_code == 400

    def test_agent_scan_with_special_characters(self, client):
        """测试Agent扫描特殊字符"""
        response = client.post(
            "/api/ai_agents/scan",
            json={"target": "http://test.local?param=<script>alert('xss')</script>"}
        )
        assert response.status_code == 400

    def test_agent_scan_with_unicode_characters(self, client):
        """测试Agent扫描Unicode字符"""
        response = client.post(
            "/api/ai_agents/scan",
            json={"target": "http://测试.local"}
        )
        assert response.status_code == 200

    def test_tasks_with_empty_list(self, client):
        """测试任务列表为空"""
        with patch('api.tasks.get_tasks') as mock_tasks:
            mock_tasks.return_value = []
            response = client.get("/api/tasks")
            assert response.status_code == 200
            assert response.json()["tasks"] == []

    def test_tasks_with_invalid_status(self, client):
        """测试任务列表无效状态"""
        response = client.get("/api/tasks?status=invalid")
        assert response.status_code == 400

    def test_tasks_with_invalid_page(self, client):
        """测试任务列表无效页码"""
        response = client.get("/api/tasks?page=-1")
        assert response.status_code == 400

    def test_tasks_with_invalid_page_size(self, client):
        """测试任务列表无效页面大小"""
        response = client.get("/api/tasks?page_size=0")
        assert response.status_code == 400

    def test_tasks_with_very_large_page_size(self, client):
        """测试任务列表超大页面大小"""
        response = client.get("/api/tasks?page_size=10000")
        assert response.status_code == 400

    def test_poc_verification_with_missing_poc_id(self, client):
        """测试POC验证缺少POC ID"""
        response = client.post(
            "/api/poc/verify",
            json={}
        )
        assert response.status_code == 422

    def test_poc_verification_with_invalid_poc_id(self, client):
        """测试POC验证无效POC ID"""
        response = client.post(
            "/api/poc/verify",
            json={"poc_id": "invalid"}
        )
        assert response.status_code == 404

    def test_poc_verification_with_missing_target(self, client):
        """测试POC验证缺少目标"""
        response = client.post(
            "/api/poc/verify",
            json={"poc_id": "test"}
        )
        assert response.status_code == 422

    def test_reports_with_empty_list(self, client):
        """测试报告列表为空"""
        with patch('api.reports.get_reports') as mock_reports:
            mock_reports.return_value = []
            response = client.get("/api/reports")
            assert response.status_code == 200
            assert response.json()["reports"] == []

    def test_reports_with_invalid_report_id(self, client):
        """测试报告列表无效报告ID"""
        response = client.get("/api/reports/invalid")
        assert response.status_code == 404

    def test_reports_with_nonexistent_report(self, client):
        """测试报告列表不存在的报告"""
        response = client.get("/api/reports/999999")
        assert response.status_code == 404

    def test_kb_with_empty_query(self, client):
        """测试知识库空查询"""
        response = client.get("/api/kb/search?q=")
        assert response.status_code == 400

    def test_kb_with_very_long_query(self, client):
        """测试知识库超长查询"""
        very_long_query = "a" * 10000
        response = client.get(f"/api/kb/search?q={very_long_query}")
        assert response.status_code == 400

    def test_kb_with_special_characters(self, client):
        """测试知识库特殊字符"""
        response = client.get("/api/kb/search?q=<script>alert('xss')</script>")
        assert response.status_code == 400

    def test_awvs_with_missing_api_key(self, client):
        """测试AWVS缺少API密钥"""
        with patch('config.settings.AWVS_API_KEY', None):
            response = client.get("/api/awvs/scans")
            assert response.status_code == 500

    def test_awvs_with_invalid_api_key(self, client):
        """测试AWVS无效API密钥"""
        with patch('config.settings.AWVS_API_KEY', "invalid"):
            response = client.get("/api/awvs/scans")
            assert response.status_code == 401

    def test_awvs_with_connection_error(self, client):
        """测试AWVS连接错误"""
        with patch('api.awvs.AWVSClient') as mock_client:
            mock_client.return_value.get_scans.side_effect = ConnectionError("Connection failed")
            response = client.get("/api/awvs/scans")
            assert response.status_code == 503

    def test_seebug_with_missing_api_key(self, client):
        """测试Seebug缺少API密钥"""
        with patch('config.settings.SEEBUG_API_KEY', None):
            response = client.get("/api/seebug/search")
            assert response.status_code == 500

    def test_seebug_with_invalid_api_key(self, client):
        """测试Seebug无效API密钥"""
        with patch('config.settings.SEEBUG_API_KEY', "invalid"):
            response = client.get("/api/seebug/search")
            assert response.status_code == 401

    def test_seebug_with_connection_error(self, client):
        """测试Seebug连接错误"""
        with patch('api.seebug_client.SeebugUtils') as mock_client:
            mock_client.return_value.search_poc.side_effect = ConnectionError("Connection failed")
            response = client.get("/api/seebug/search?q=test")
            assert response.status_code == 503

    def test_scan_with_missing_target(self, client):
        """测试扫描缺少目标"""
        response = client.post("/api/scan", json={})
        assert response.status_code == 422

    def test_scan_with_invalid_target(self, client):
        """测试扫描无效目标"""
        response = client.post(
            "/api/scan",
            json={"target": "not-a-valid-url"}
        )
        assert response.status_code == 400

    def test_scan_with_timeout_error(self, client):
        """测试扫描超时错误"""
        with patch('api.scan.start_scan') as mock_scan:
            mock_scan.side_effect = TimeoutError("Scan timeout")
            response = client.post(
                "/api/scan",
                json={"target": "http://test.local"}
            )
            assert response.status_code == 504

    def test_dashboard_with_no_data(self, client):
        """测试仪表盘无数据"""
        with patch('api.tasks.get_statistics') as mock_stats:
            mock_stats.return_value = {
                "today_scans": 0,
                "high_risk_vulns": 0,
                "completed_scans": 0,
                "failed_scans": 0,
                "total_vulns": 0,
                "total_reports": 0
            }
            response = client.get("/api/dashboard")
            assert response.status_code == 200

    def test_dashboard_with_connection_error(self, client):
        """测试仪表盘连接错误"""
        with patch('api.tasks.get_statistics') as mock_stats:
            mock_stats.side_effect = ConnectionError("Database connection failed")
            response = client.get("/api/dashboard")
            assert response.status_code == 503

    def test_user_notification_with_missing_user_id(self, client):
        """测试用户通知缺少用户ID"""
        response = client.post(
            "/api/notifications",
            json={}
        )
        assert response.status_code == 422

    def test_user_notification_with_invalid_user_id(self, client):
        """测试用户通知无效用户ID"""
        response = client.post(
            "/api/notifications",
            json={"user_id": "invalid"}
        )
        assert response.status_code == 404

    def test_ai_chat_with_empty_message(self, client):
        """测试AI聊天空消息"""
        response = client.post(
            "/api/ai/chat",
            json={"message": ""}
        )
        assert response.status_code == 400

    def test_ai_chat_with_very_long_message(self, client):
        """测试AI聊天超长消息"""
        very_long_message = "a" * 100000
        response = client.post(
            "/api/ai/chat",
            json={"message": very_long_message}
        )
        assert response.status_code == 400

    def test_ai_chat_with_special_characters(self, client):
        """测试AI聊天特殊字符"""
        response = client.post(
            "/api/ai/chat",
            json={"message": "<script>alert('xss')</script>"}
        )
        assert response.status_code == 400

    def test_settings_with_invalid_key(self, client):
        """测试设置无效键"""
        response = client.get("/api/settings/invalid_key")
        assert response.status_code == 404

    def test_settings_with_read_only_key(self, client):
        """测试设置只读键"""
        response = client.post("/api/settings/DEBUG", json={"value": True})
        assert response.status_code == 403

    def test_settings_with_invalid_value_type(self, client):
        """测试设置无效值类型"""
        response = client.post(
            "/api/settings/DEBUG",
            json={"value": "invalid"}
        )
        assert response.status_code == 400

    def test_websocket_connection_error(self, client):
        """测试WebSocket连接错误"""
        with patch('api.websocket.WebSocketManager') as mock_manager:
            mock_manager.return_value.connect.side_effect = ConnectionError("Connection failed")
            response = client.get("/api/ai_agents/scan")
            assert response.status_code == 503

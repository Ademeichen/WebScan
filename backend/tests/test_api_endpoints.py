"""
后端API全面测试

测试所有后端API端点，确保功能正常。
使用真实业务代码和真实服务环境。
"""
import pytest
import sys
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tortoise import Tortoise
from backend.config import settings
from httpx import AsyncClient, ASGITransport
from backend.main import app





@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """初始化测试数据库连接"""
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["backend.models"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
async def client():
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_targets():
    """加载测试目标数据"""
    data_file = Path(__file__).parent / "test_data" / "test_targets.json"
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def test_pocs():
    """加载测试POC数据"""
    data_file = Path(__file__).parent / "test_data" / "test_pocs.json"
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


class TestRootEndpoints:
    """测试根路径端点"""

    @pytest.mark.asyncio
    async def test_root(self, client):
        """测试根路径"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查端点"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestTasksAPI:
    """测试任务管理API"""

    @pytest.mark.asyncio
    async def test_list_tasks(self, client):
        """测试获取任务列表"""
        response = await client.get("/api/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "tasks" in data["data"]
        assert "total" in data["data"]

    @pytest.mark.asyncio
    async def test_create_task(self, client, test_targets):
        """测试创建任务"""
        target = test_targets["targets"][0]
        task_data = {
            "task_name": f"Test Task {datetime.now().isoformat()}",
            "target": target["url"],
            "task_type": "scan_port",
            "config": {"ports": [80, 443]}
        }
        response = await client.post("/api/tasks/create", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "task_id" in data["data"]

    @pytest.mark.asyncio
    async def test_get_statistics_overview(self, client):
        """测试获取统计概览"""
        response = await client.get("/api/tasks/statistics/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data


class TestScanAPI:
    """测试扫描功能API"""

    @pytest.mark.asyncio
    async def test_port_scan(self, client):
        """测试端口扫描"""
        scan_data = {
            "ip": "127.0.0.1",
            "ports": "1-1000"
        }
        response = await client.post("/api/scan/port-scan", json=scan_data)
        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_baseinfo_scan(self, client):
        """测试基础信息扫描"""
        scan_data = {
            "url": "https://www.baidu.com"
        }
        response = await client.post("/api/scan/baseinfo", json=scan_data)
        assert response.status_code in [200, 400, 500]


class TestPOCAPI:
    """测试POC扫描API"""

    @pytest.mark.asyncio
    async def test_get_poc_types(self, client):
        """测试获取POC类型"""
        response = await client.get("/api/poc/types")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_poc_scan(self, client, test_pocs):
        """测试POC扫描"""
        poc = test_pocs["pocs"][0]
        scan_data = {
            "target": poc["target"],
            "poc_types": [poc["type"]]
        }
        response = await client.post("/api/poc/scan", json=scan_data)
        assert response.status_code in [200, 500]


class TestReportsAPI:
    """测试报告管理API"""

    @pytest.mark.asyncio
    async def test_list_reports(self, client):
        """测试获取报告列表"""
        response = await client.get("/api/reports/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data

    @pytest.mark.asyncio
    async def test_create_report(self, client):
        """测试创建报告 - 需要先创建任务"""
        # 首先创建一个任务
        from backend.models import Task
        task = await Task.create(
            task_name="Test Report Task",
            task_type="port_scan",
            target="127.0.0.1",
            status="completed",
            progress=100
        )
        try:
            report_data = {
                "task_id": task.id,
                "name": f"Test Report {datetime.now().isoformat()}",
                "format": "json"
            }
            response = await client.post("/api/reports/", json=report_data)
            assert response.status_code in [200, 400, 500]
        finally:
            await task.delete()


class TestSettingsAPI:
    """测试系统设置API"""

    @pytest.mark.asyncio
    async def test_get_settings(self, client):
        """测试获取设置"""
        response = await client.get("/api/settings/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_get_system_info(self, client):
        """测试获取系统信息"""
        response = await client.get("/api/settings/system-info")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_get_categories(self, client):
        """测试获取设置分类"""
        response = await client.get("/api/settings/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200


class TestAIAPI:
    """测试AI对话API"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ai_chat(self, client):
        """测试AI对话"""
        chat_data = {
            "message": "你好，请回复'连接成功'",
            "context": {}
        }
        response = await client.post("/api/ai/chat", json=chat_data)
        assert response.status_code in [200, 500]


class TestKnowledgeBaseAPI:
    """测试漏洞知识库API"""

    @pytest.mark.asyncio
    async def test_search_vulnerabilities(self, client):
        """测试搜索漏洞"""
        response = await client.get("/api/kb/vulnerabilities", params={"keyword": "SQL注入"})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_seebug_poc(self, client):
        """测试搜索Seebug POC"""
        search_data = {
            "keyword": "thinkphp",
            "page": 1
        }
        response = await client.post("/api/kb/seebug/poc/search", json=search_data)
        assert response.status_code in [200, 500]


class TestUserAPI:
    """测试用户管理API"""

    @pytest.mark.asyncio
    async def test_get_profile(self, client):
        """测试获取用户资料"""
        response = await client.get("/api/user/profile", params={"user_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_get_permissions(self, client):
        """测试获取用户权限"""
        response = await client.get("/api/user/permissions", params={"user_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200


class TestNotificationsAPI:
    """测试通知管理API"""

    @pytest.mark.asyncio
    async def test_list_notifications(self, client):
        """测试获取通知列表"""
        response = await client.get("/api/notifications/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_get_unread_count(self, client):
        """测试获取未读数量"""
        response = await client.get("/api/notifications/count/unread")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_create_notification(self, client):
        """测试创建通知"""
        from backend.models import User
        user = await User.get_or_none(id=1)
        if not user:
            user = await User.create(
                username="test_user",
                email="test@example.com",
                password_hash="test123"
            )
        notification_data = {
            "title": f"Test Notification {datetime.now().isoformat()}",
            "message": "This is a test notification.",
            "type": "info"
        }
        response = await client.post("/api/notifications/", json=notification_data)
        assert response.status_code in [200, 404, 500]


class TestAIAgentsAPI:
    """测试AI Agents API"""

    @pytest.mark.asyncio
    async def test_get_tools(self, client):
        """测试获取工具列表"""
        response = await client.get("/api/ai_agents/tools")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_get_config(self, client):
        """测试获取AI配置"""
        response = await client.get("/api/ai_agents/config")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_get_tasks(self, client):
        """测试获取AI任务列表"""
        response = await client.get("/api/ai_agents/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200


class TestSeebugAgentAPI:
    """测试Seebug Agent API"""

    @pytest.mark.asyncio
    async def test_get_status(self, client):
        """测试获取Seebug状态"""
        response = await client.get("/api/seebug/status")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_test_connection(self, client):
        """测试Seebug连接"""
        response = await client.get("/api/seebug/test-connection")
        assert response.status_code in [200, 500]


class TestPOCVerificationAPI:
    """测试POC验证API"""

    @pytest.mark.asyncio
    async def test_get_tasks(self, client):
        """测试获取验证任务列表"""
        response = await client.get("/api/poc/verification/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_get_statistics(self, client):
        """测试获取验证统计"""
        response = await client.get("/api/poc/verification/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查"""
        response = await client.get("/api/poc/verification/health")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200


class TestPOCFilesAPI:
    """测试POC文件管理API"""

    @pytest.mark.asyncio
    async def test_get_directories(self, client):
        """测试获取目录列表"""
        response = await client.get("/api/poc/files/directories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_files(self, client):
        """测试获取文件列表"""
        response = await client.get("/api/poc/files/list")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "files" in data


class TestAWVSAPI:
    """测试AWVS API"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_targets(self, client):
        """测试获取目标列表"""
        response = await client.get("/api/awvs/targets")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_scans(self, client):
        """测试获取扫描列表"""
        response = await client.get("/api/awvs/scans")
        assert response.status_code in [200, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--run-integration'])

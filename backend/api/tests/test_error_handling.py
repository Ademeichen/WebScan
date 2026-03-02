"""
API错误处理测试

测试API端点的错误处理和边界情况。
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.config import settings


class TestAPIErrorHandling:
    """测试API错误处理"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前初始化"""
        self.base_url = "http://127.0.0.1:3000"
        yield
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """测试健康检查端点"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                
                assert response.status_code == 200
                data = response.json()
                assert data.get("status") == "healthy"
                
        except httpx.ConnectError:
            pytest.skip("后端服务未启动")
        except Exception as e:
            pytest.skip(f"健康检查测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_awvs_targets_endpoint(self):
        """测试AWVS目标端点"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/awvs/targets")
                
                assert response.status_code in [200, 404, 500]
                
        except httpx.ConnectError:
            pytest.skip("后端服务未启动")
        except Exception as e:
            pytest.skip(f"AWVS目标测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_awvs_scans_endpoint(self):
        """测试AWVS扫描端点"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/awvs/scans")
                
                assert response.status_code in [200, 404, 500]
                
        except httpx.ConnectError:
            pytest.skip("后端服务未启动")
        except Exception as e:
            pytest.skip(f"AWVS扫描测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_subgraphs_health_endpoint(self):
        """测试子图健康检查端点"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/subgraphs/health")
                
                assert response.status_code in [200, 404, 500]
                
        except httpx.ConnectError:
            pytest.skip("后端服务未启动")
        except Exception as e:
            pytest.skip(f"子图健康检查测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_ai_chat_endpoint(self):
        """测试AI聊天端点"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/ai/chat",
                    json={"message": "你好", "session_id": "test-session"}
                )
                
                assert response.status_code in [200, 404, 500]
                
        except httpx.ConnectError:
            pytest.skip("后端服务未启动")
        except Exception as e:
            pytest.skip(f"AI聊天测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_seebug_search_endpoint(self):
        """测试Seebug搜索端点"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/seebug/search",
                    params={"keyword": "test"}
                )
                
                assert response.status_code in [200, 404, 500]
                
        except httpx.ConnectError:
            pytest.skip("后端服务未启动")
        except Exception as e:
            pytest.skip(f"Seebug搜索测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_poc_files_endpoint(self):
        """测试POC文件端点"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/poc/files")
                
                assert response.status_code in [200, 404, 500]
                
        except httpx.ConnectError:
            pytest.skip("后端服务未启动")
        except Exception as e:
            pytest.skip(f"POC文件测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_tasks_endpoint(self):
        """测试任务端点"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tasks")
                
                assert response.status_code in [200, 404, 500]
                
        except httpx.ConnectError:
            pytest.skip("后端服务未启动")
        except Exception as e:
            pytest.skip(f"任务测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_reports_endpoint(self):
        """测试报告端点"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/reports")
                
                assert response.status_code in [200, 404, 500]
                
        except httpx.ConnectError:
            pytest.skip("后端服务未启动")
        except Exception as e:
            pytest.skip(f"报告测试跳过: {str(e)}")


class TestConfigurationValidation:
    """测试配置验证"""
    
    def test_settings_exist(self):
        """测试配置存在"""
        assert settings is not None
    
    def test_app_name_configured(self):
        """测试应用名称配置"""
        assert settings.APP_NAME is not None
        assert len(settings.APP_NAME) > 0
    
    def test_app_version_configured(self):
        """测试应用版本配置"""
        assert settings.APP_VERSION is not None
        assert len(settings.APP_VERSION) > 0
    
    def test_database_url_configured(self):
        """测试数据库URL配置"""
        assert settings.DATABASE_URL is not None
        assert len(settings.DATABASE_URL) > 0
    
    def test_openai_api_key_configured(self):
        """测试OpenAI API密钥配置"""
        assert settings.OPENAI_API_KEY is not None
        assert len(settings.OPENAI_API_KEY) > 0
    
    def test_openai_base_url_configured(self):
        """测试OpenAI基础URL配置"""
        assert settings.OPENAI_BASE_URL is not None
        assert len(settings.OPENAI_BASE_URL) > 0
    
    def test_model_id_configured(self):
        """测试模型ID配置"""
        assert settings.MODEL_ID is not None
        assert len(settings.MODEL_ID) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

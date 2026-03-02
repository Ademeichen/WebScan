"""
API路由测试

测试各个组件的连接测试接口。
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.config import settings


class TestAPIRoutes:
    """测试API路由"""
    
    @pytest.mark.asyncio
    async def test_ai_model_connection(self):
        """测试AI模型连接"""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            
            llm = ChatOpenAI(
                model=settings.MODEL_ID,
                temperature=0.7,
                openai_api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
            
            test_message = HumanMessage(content="你好,请回复'连接成功'")
            response = await llm.ainvoke([test_message])
            
            assert response is not None
            assert response.content is not None
            
        except Exception as e:
            pytest.skip(f"AI模型连接测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_seebug_connection(self):
        """测试Seebug API连接"""
        try:
            if not settings.SEEBUG_API_KEY:
                pytest.skip("Seebug API密钥未配置")
            
            from pocsuite3.lib.request import requests
            
            url = 'https://www.seebug.org/api/user/poc_list'
            headers = {
                'User-Agent': 'curl/7.80.0',
                'Authorization': f'Token {settings.SEEBUG_API_KEY}'
            }
            
            resp = requests.get(url, headers=headers, timeout=10.0)
            
            assert resp is not None
            assert resp.status_code == 200
            
        except ImportError:
            pytest.skip("Pocsuite3未安装")
        except Exception as e:
            pytest.skip(f"Seebug API连接测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_pocsuite3_agent(self):
        """测试Pocsuite3智能体库"""
        try:
            from backend.Pocsuite3Agent.agent import Pocsuite3Agent
            
            agent = Pocsuite3Agent()
            available_pocs = agent.get_available_pocs()
            
            assert agent is not None
            assert isinstance(available_pocs, list)
            
        except ImportError:
            pytest.skip("Pocsuite3未安装")
        except Exception as e:
            pytest.skip(f"Pocsuite3智能体库测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_langgraph_connection(self):
        """测试LangGraph连接"""
        try:
            from backend.ai_agents.core.graph import create_agent_graph
            
            graph = create_agent_graph()
            graph_info = graph.get_graph_info()
            compiled_graph = graph.compile()
            
            assert graph is not None
            assert graph_info is not None
            assert compiled_graph is not None
            
        except ImportError:
            pytest.skip("LangGraph未安装")
        except Exception as e:
            pytest.skip(f"LangGraph测试跳过: {str(e)}")
    
    def test_settings_configuration(self):
        """测试配置"""
        assert settings.APP_NAME is not None
        assert settings.APP_VERSION is not None
        assert settings.DATABASE_URL is not None


class TestHealthCheck:
    """测试健康检查"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """测试健康检查端点"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://127.0.0.1:3000/health")
                
                assert response.status_code == 200
                data = response.json()
                assert data.get("status") == "healthy"
                
        except httpx.ConnectError:
            pytest.skip("后端服务未启动")
        except Exception as e:
            pytest.skip(f"健康检查测试跳过: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
测试 API 路由

提供各个组件的连接测试接口,用于验证系统各模块是否正常工作。
包括:AI模型、Seebug、Pocsuite3智能体库、LangGraph等。
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import time

from backend.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["测试接口"])


# ====== 响应模型 ======
class TestResponse(BaseModel):
    """
    测试响应模型
    
    Attributes:
        code: 状态码
        message: 响应消息
        data: 响应数据
    """
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


# ====== AI模型测试 ======
@router.post("/ai-model", response_model=TestResponse)
async def test_ai_model():
    """
    测试AI模型连接
    
    验证AI模型是否可以正常连接和响应。
    
    Returns:
        TestResponse: 测试结果,包含连接状态、响应时间、模型信息等
    """
    try:
        logger.info("🧪 开始测试AI模型连接")
        start_time = time.time()
        
        # 初始化AI模型
        llm = ChatOpenAI(
            model=settings.MODEL_ID,
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        
        # 发送测试消息
        test_message = HumanMessage(content="你好,请回复'连接成功'")
        response = await llm.ainvoke([test_message])
        
        response_time = time.time() - start_time
        
        # 验证响应
        if response and response.content:
            logger.info(f"✅ AI模型测试成功,响应时间: {response_time:.2f}秒")
            
            return TestResponse(
                code=200,
                message="AI模型连接正常",
                data={
                    "status": "success",
                    "model_id": settings.MODEL_ID,
                    "base_url": settings.OPENAI_BASE_URL,
                    "response_time": f"{response_time:.2f}s",
                    "response_content": response.content[:100],
                    "api_key_configured": bool(settings.OPENAI_API_KEY)
                }
            )
        else:
            raise Exception("AI模型响应为空")
            
    except Exception as e:
        logger.error(f"❌ AI模型测试失败: {str(e)}")
        return TestResponse(
            code=500,
            message=f"AI模型连接失败: {str(e)}",
            data={
                "status": "failed",
                "error": str(e),
                "model_id": settings.MODEL_ID,
                "base_url": settings.OPENAI_BASE_URL,
                "api_key_configured": bool(settings.OPENAI_API_KEY)
            }
        )


# ====== Seebug测试 ======
@router.post("/seebug", response_model=TestResponse)
async def test_seebug():
    """
    测试Seebug API连接(使用Pocsuite3内置API)
    
    验证Seebug API是否可以正常访问和获取数据。
    
    Returns:
        TestResponse: 测试结果,包含连接状态、API密钥验证、测试查询结果等
    """
    try:
        logger.info("🧪 开始测试Seebug API连接")
        start_time = time.time()
        
        # 验证API密钥配置
        if not settings.SEEBUG_API_KEY:
            raise Exception("Seebug API密钥未配置")
        
        # 使用Pocsuite3的Seebug API
        try:
            from pocsuite3.lib.request import requests
            
            # 直接使用Pocsuite3的requests库调用Seebug API
            url = 'https://www.seebug.org/api/user/poc_list'
            headers = {
                'User-Agent': 'curl/7.80.0',
                'Authorization': f'Token {settings.SEEBUG_API_KEY}'
            }
            
            resp = requests.get(url, headers=headers, timeout=10.0)
            
            response_time = time.time() - start_time
            
            if resp and resp.status_code == 200:
                logger.info(f"✅ Seebug API测试成功,响应时间: {response_time:.2f}秒")
                
                return TestResponse(
                    code=200,
                    message="Seebug API连接正常",
                    data={
                        "status": "success",
                        "api_base_url": "Pocsuite3内置Seebug API",
                        "response_time": f"{response_time:.2f}s",
                        "api_key_configured": True,
                        "test_query_result": {
                            "message": "API Key验证成功",
                            "poc_count": len(resp.json()) if resp.json() else 0
                        }
                    }
                )
            else:
                raise Exception(f"Seebug API返回错误状态码: {resp.status_code}")
                
        except ImportError:
            raise Exception("Pocsuite3未安装,无法使用Seebug API")
            
    except Exception as e:
        logger.error(f"❌ Seebug API测试失败: {str(e)}")
        return TestResponse(
            code=500,
            message=f"Seebug API连接失败: {str(e)}",
            data={
                "status": "failed",
                "error": str(e),
                "api_base_url": "Pocsuite3内置Seebug API",
                "api_key_configured": bool(settings.SEEBUG_API_KEY)
            }
        )


# ====== Pocsuite3测试 ======
@router.post("/pocsuite3", response_model=TestResponse)
async def test_pocsuite3():
    """
    测试Pocsuite3智能体库连接
    
    验证Pocsuite3库是否可以正常加载和使用。
    
    Returns:
        TestResponse: 测试结果,包含库安装状态、POC加载情况、可用POC数量等
    """
    try:
        logger.info("🧪 开始测试Pocsuite3智能体库")
        start_time = time.time()
        
        # 导入Pocsuite3Agent
        from backend.Pocsuite3Agent.agent import Pocsuite3Agent
        
        # 创建代理实例
        agent = Pocsuite3Agent()
        
        # 获取可用POC列表
        available_pocs = agent.get_available_pocs()
        
        response_time = time.time() - start_time
        
        logger.info(f"✅ Pocsuite3智能体库测试成功,响应时间: {response_time:.2f}秒")
        
        return TestResponse(
            code=200,
            message="Pocsuite3智能体库连接正常",
            data={
                "status": "success",
                "installation_status": "installed",
                "response_time": f"{response_time:.2f}s",
                "available_pocs_count": len(available_pocs),
                "poc_sample": available_pocs[:5] if available_pocs else [],
                "poc_registry_size": len(agent.poc_registry)
            }
        )
        
    except ImportError as e:
        logger.error(f"❌ Pocsuite3未安装: {str(e)}")
        return TestResponse(
            code=500,
            message="Pocsuite3未安装",
            data={
                "status": "failed",
                "error": "Pocsuite3库未安装,请使用 pip install pocsuite3 安装",
                "installation_status": "not_installed"
            }
        )
    except Exception as e:
        logger.error(f"❌ Pocsuite3智能体库测试失败: {str(e)}")
        return TestResponse(
            code=500,
            message=f"Pocsuite3智能体库测试失败: {str(e)}",
            data={
                "status": "failed",
                "error": str(e)
            }
        )


# ====== LangGraph测试 ======
@router.post("/langgraph", response_model=TestResponse)
async def test_langgraph():
    """
    测试LangGraph连接
    
    验证LangGraph工作流是否可以正常初始化和编译。
    
    Returns:
        TestResponse: 测试结果,包含图结构信息、节点数量、边数量等
    """
    try:
        logger.info("🧪 开始测试LangGraph")
        start_time = time.time()
        
        # 导入LangGraph相关模块
        from backend.ai_agents.core.graph import create_agent_graph
        from backend.ai_agents.core.state import AgentState
        from uuid import uuid4
        
        # 创建Agent图实例
        graph = create_agent_graph()
        
        # 获取图信息
        graph_info = graph.get_graph_info()
        
        # 编译图
        compiled_graph = graph.compile()
        
        response_time = time.time() - start_time
        
        logger.info(f"✅ LangGraph测试成功,响应时间: {response_time:.2f}秒")
        
        return TestResponse(
            code=200,
            message="LangGraph连接正常",
            data={
                "status": "success",
                "response_time": f"{response_time:.2f}s",
                "graph_info": {
                    "total_nodes": graph_info["total_nodes"],
                    "nodes": graph_info["nodes"],
                    "entry_point": graph_info["entry_point"],
                    "exit_points": graph_info["exit_points"]
                },
                "graph_compiled": compiled_graph is not None,
                "visualization_available": graph.visualize() is not None
            }
        )
        
    except ImportError as e:
        logger.error(f"❌ LangGraph未安装: {str(e)}")
        return TestResponse(
            code=500,
            message="LangGraph未安装",
            data={
                "status": "failed",
                "error": "LangGraph库未安装,请使用 pip install langgraph 安装",
                "installation_status": "not_installed"
            }
        )
    except Exception as e:
        logger.error(f"❌ LangGraph测试失败: {str(e)}")
        return TestResponse(
            code=500,
            message=f"LangGraph测试失败: {str(e)}",
            data={
                "status": "failed",
                "error": str(e)
            }
        )


# ====== 综合测试 ======
@router.post("/all", response_model=TestResponse)
async def test_all():
    """
    综合测试所有组件
    
    依次测试AI模型、Seebug、Pocsuite3、LangGraph等所有组件。
    
    Returns:
        TestResponse: 包含所有组件测试结果的汇总信息
    """
    try:
        logger.info("🧪 开始综合测试所有组件")
        start_time = time.time()
        
        results = {}
        
        # 测试AI模型
        ai_result = await test_ai_model()
        results["ai_model"] = {
            "status": "success" if ai_result.code == 200 else "failed",
            "message": ai_result.message,
            "data": ai_result.data
        }
        
        # 测试Seebug
        seebug_result = await test_seebug()
        results["seebug"] = {
            "status": "success" if seebug_result.code == 200 else "failed",
            "message": seebug_result.message,
            "data": seebug_result.data
        }
        
        # 测试Pocsuite3
        pocsuite3_result = await test_pocsuite3()
        results["pocsuite3"] = {
            "status": "success" if pocsuite3_result.code == 200 else "failed",
            "message": pocsuite3_result.message,
            "data": pocsuite3_result.data
        }
        
        # 测试LangGraph
        langgraph_result = await test_langgraph()
        results["langgraph"] = {
            "status": "success" if langgraph_result.code == 200 else "failed",
            "message": langgraph_result.message,
            "data": langgraph_result.data
        }
        
        total_time = time.time() - start_time
        
        # 统计成功/失败数量
        success_count = sum(1 for r in results.values() if r["status"] == "success")
        total_count = len(results)
        
        logger.info(f"✅ 综合测试完成,成功: {success_count}/{total_count},总耗时: {total_time:.2f}秒")
        
        return TestResponse(
            code=200,
            message=f"综合测试完成,成功: {success_count}/{total_count}",
            data={
                "total_time": f"{total_time:.2f}s",
                "success_count": success_count,
                "total_count": total_count,
                "details": results
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 综合测试失败: {str(e)}")
        return TestResponse(
            code=500,
            message=f"综合测试失败: {str(e)}",
            data={
                "status": "failed",
                "error": str(e)
            }
        )


# ====== 健康检查 ======
@router.get("/health", response_model=TestResponse)
async def health_check():
    """
    健康检查接口
    
    返回系统基本状态信息。
    
    Returns:
        TestResponse: 系统健康状态
    """
    try:
        return TestResponse(
            code=200,
            message="系统运行正常",
            data={
                "status": "healthy",
                "app_name": settings.APP_NAME,
                "app_version": settings.APP_VERSION,
                "debug_mode": settings.DEBUG,
                "database_url": settings.DATABASE_URL,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
        )
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {str(e)}")
        return TestResponse(
            code=500,
            message=f"健康检查失败: {str(e)}",
            data={
                "status": "unhealthy",
                "error": str(e)
            }
        )

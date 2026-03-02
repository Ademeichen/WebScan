"""
测试AI模型连接脚本

直接测试AI模型连接，不需要通过API端点。
"""
import sys
import time
import logging
from pathlib import Path

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from backend.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ai_model_connection():
    """
    测试AI模型连接
    
    Returns:
        dict: 测试结果
    """
    try:
        logger.info("🧪 开始测试AI模型连接")
        start_time = time.time()
        
        llm = ChatOpenAI(
            model=settings.MODEL_ID,
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        
        test_message = HumanMessage(content="你好,请回复'连接成功fyb'")
        response = llm.invoke([test_message])
        
        response_time = time.time() - start_time
        
        if response and response.content:
            logger.info(f"✅ AI模型测试成功,响应时间: {response_time:.2f}秒,响应内容: {response.content[:100]}")
        
            return {
                "status": "success",
                "message": "AI模型连接正常",
                "data": {
                    "model_id": settings.MODEL_ID,
                    "base_url": settings.OPENAI_BASE_URL,
                    "response_time": f"{response_time:.2f}s",
                    "response_content": response.content[:100],
                    "api_key_configured": bool(settings.OPENAI_API_KEY)
                }
            }
        else:
            raise Exception("AI模型响应为空")
            
    except Exception as e:
        logger.error(f"❌ AI模型测试失败: {str(e)}")
        return {
            "status": "failed",
            "message": f"AI模型连接失败: {str(e)}",
            "data": {
                "model_id": settings.MODEL_ID,
                "base_url": settings.OPENAI_BASE_URL,
                "api_key_configured": bool(settings.OPENAI_API_KEY),
                "error": str(e)
            }
        }

if __name__ == "__main__":
    print("=" * 60)
    print("测试AI模型连接")
    print("=" * 60)
    
    print(f"模型ID: {settings.MODEL_ID}")
    print(f"API基础URL: {settings.OPENAI_BASE_URL}")
    print(f"API密钥配置: {'已配置' if settings.OPENAI_API_KEY else '未配置'}")
    print()
    
    result = test_ai_model_connection()
    
    print("测试结果:")
    print(f"状态: {result['status']}")
    print(f"消息: {result['message']}")
    print()
    
    if result['data']:
        print("详细信息:")
        for key, value in result['data'].items():
            print(f"  {key}: {value}")
    
    print("=" * 60)

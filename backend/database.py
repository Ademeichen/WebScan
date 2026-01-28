"""
数据库连接和会话管理 - 使用 Tortoise-ORM

提供数据库初始化、连接管理、健康检查等功能。
支持异步操作，与 FastAPI 集成使用。
"""
import os
from tortoise import Tortoise, connections
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


async def init_db():
    """
    初始化数据库连接
    
    创建数据库表结构，建立连接池。
    支持多种数据库：SQLite、MySQL、PostgreSQL。
    
    Raises:
        Exception: 数据库初始化失败时抛出异常
    """
    try:
        # 确保数据库目录存在
        db_url = settings.DATABASE_URL
        if db_url.startswith("sqlite://"):
            db_path = db_url.replace("sqlite://", "")
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"✅ 创建数据库目录: {db_dir}")
        
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["backend.models"]},
            _create_db=True
        )
        await Tortoise.generate_schemas()
        logger.info(f"✅ 数据库初始化成功 - {db_url}")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        raise


async def close_db():
    """
    关闭数据库连接
    
    优雅关闭所有数据库连接，释放资源。
    
    Raises:
        Exception: 关闭连接失败时抛出异常
    """
    try:
        await Tortoise.close_connections()
        logger.info("✅ 数据库连接已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭数据库连接失败: {str(e)}")
        raise


async def get_db_connection():
    """
    获取数据库连接
    
    Returns:
        Connection: 默认数据库连接对象
    """
    conn = connections.get("default")
    return conn


async def health_check():
    """
    数据库健康检查
    
    执行简单查询验证数据库连接是否正常。
    
    Returns:
        bool: True表示健康，False表示异常
    """
    try:
        conn = connections.get("default")
        await conn.execute_query("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库健康检查失败: {str(e)}")
        return False

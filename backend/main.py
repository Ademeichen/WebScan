"""
FastAPI 主应用入口文件

本文件是 WebScan AI Security Platform 的主入口,负责:
- 创建和配置 FastAPI 应用实例
- 设置 CORS 中间件
- 注册 API 路由
- 配置日志系统
- 管理应用生命周期(启动/关闭)
- 初始化数据库连接
- 验证外部服务连接(如 AWVS)
- 启动后台任务
"""
import sys
import warnings
from pathlib import Path

# 抑制paramiko的Blowfish弃用警告
warnings.filterwarnings("ignore", category=DeprecationWarning, module="paramiko")

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from backend.config import settings
from backend.database import init_db, close_db
import logging

# 创建必要的目录
Path("logs").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    管理应用的启动和关闭流程:
    启动时:
    - 初始化数据库连接
    - 验证 AWVS API 连接
    - 启动后台数据同步任务
    
    关闭时:
    - 关闭数据库连接
    - 清理资源
    
    Args:
        app: FastAPI 应用实例
        
    Yields:
        None: 控制权交还给应用
    """
    # 启动时执行
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # 初始化数据库
    await init_db()
    
    # 验证AWVS连接
    try:
        from backend.AVWS.API.Base import Base as AWVSBase
        awvs_base = AWVSBase(settings.AWVS_API_URL, settings.AWVS_API_KEY)
        success, message = awvs_base.check_connection()
        if success:
            logger.info("AWVS API 连接测试成功")
        else:
            logger.error(f"AWVS API 连接测试失败: {message}")
            logger.warning("请检查配置文件中的 AWVS_API_URL 和 AWVS_API_KEY")
    except Exception as e:
        logger.error(f"执行 AWVS 连接测试时发生错误: {str(e)}")

    yield
    
    # 关闭时执行
    logger.info("应用关闭")
    
    # 关闭数据库连接
    await close_db()

# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI驱动的Web安全扫描平台",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    根路径
    
    返回 API 基本信息,用于验证服务是否正常运行。
    
    Returns:
        Dict: 包含欢迎消息、版本号和状态的响应
        
    Examples:
        >>> GET /
        >>> {
        ...     "message": "Welcome to WebScan AI Security Platform",
        ...     "version": "1.0.0",
        ...     "status": "running"
        ... }
    """
    return {
        "message": "Welcome to WebScan AI Security Platform",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    健康检查端点
    
    用于监控服务健康状态,负载均衡器和容器编排系统可以定期调用此端点。
    
    Returns:
        Dict: 包含健康状态的响应
        
    Examples:
        >>> GET /health
        >>> {"status": "healthy"}
    """
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    全局异常处理器
    
    捕获所有未处理的异常,统一返回错误响应。
    在生产环境中,不会返回详细的错误信息以避免泄露敏感信息。
    
    Args:
        request: 请求对象
        exc: 异常对象
        
    Returns:
        JSONResponse: 统一的错误响应格式
    """
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "error": str(exc) if settings.DEBUG else "Internal Server Error"
        }
    )


# 注册路由
from backend.api import api_router
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    """
    应用启动入口
    
    使用 Uvicorn ASGI 服务器运行 FastAPI 应用。
    """
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )

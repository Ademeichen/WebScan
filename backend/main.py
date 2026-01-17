"""
FastAPI 主应用入口文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from config import settings
from database import init_db, close_db
import logging
from pathlib import Path

# 创建必要的目录
Path("logs").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # 初始化数据库
    await init_db()
    
    # 验证AWVS连接
    try:
        from AVWS.API.Base import Base
        awvs_base = Base(settings.AWVS_API_URL, settings.AWVS_API_KEY)
        success, message = awvs_base.check_connection()
        if success:
            logger.info("AWVS API 连接测试成功")
            
            # 启动后台同步任务
            try:
                from api.awvs import sync_scans_from_awvs
                import asyncio
                logger.info("正在启动AWVS数据后台同步...")
                asyncio.create_task(sync_scans_from_awvs())
            except Exception as e:
                logger.error(f"启动AWVS同步任务失败: {e}")
                
        else:
            logger.error(f"AWVS API 连接测试失败: {message}")
            # 可以在这里选择是否抛出异常阻止启动，或者只是记录警告
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
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# 根路径
@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "Welcome to WebScan AI Security Platform",
        "version": settings.APP_VERSION,
        "status": "running"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
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
from api import api_router
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )





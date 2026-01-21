"""
FastAPI 应用配置文件

使用 Pydantic Settings 管理应用配置，支持从环境变量和 .env 文件加载。
配置包括：服务器、数据库、日志、扫描、API密钥等。
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    应用配置类
    
    所有配置项都可以通过环境变量或 .env 文件覆盖。
    """
    
    # ====================== 应用基础配置 ======================
    APP_NAME: str = "WebScan AI Security Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # ====================== 服务器配置 ======================
    HOST: str = "127.0.0.1"
    PORT: int = 3000
    
    # ====================== CORS 配置 ======================
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000"
    ]
    
    # ====================== 数据库配置 ======================
    # Tortoise-ORM 支持的数据库格式：
    # SQLite: sqlite://./database.db
    # MySQL: mysql://user:password@host:port/database
    # PostgreSQL: postgres://user:password@host:port/database
    DATABASE_URL: str = "sqlite://./data/webscan.db"
    
    # ====================== 日志配置 ======================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    CODE_EXECUTOR_LOG_FILE: str = "logs/code_executor.log"
    
    # ====================== 扫描配置 ======================
    MAX_CONCURRENT_SCANS: int = 5
    SCAN_TIMEOUT: int = 300
    
    # ====================== API 密钥配置 ======================
    # OpenAI API 密钥（用于 GPT 模型）
    OPENAI_API_KEY: Optional[str] = None
    
    # 阿里云通义千问 API 密钥（用于 Qwen 模型）
    QWEN_API_KEY: Optional[str] = None
    
    # ====================== AWVS 配置 ======================
    AWVS_API_URL: str = "https://127.0.0.1:3443"
    AWVS_API_KEY: str = "1986ad8c0a5b3df4d7028d5f3c06e936c986f9835bbf243cb9b33aee376ee7da9"
    
    # ====================== 代码执行配置 ======================
    # 代码执行工作空间路径
    CODE_EXECUTOR_WORKSPACE: str = "executor_workspace"
    # 代码执行超时时间（秒）
    CODE_EXECUTOR_TIMEOUT: int = 30
    # 是否允许代码执行
    CODE_EXECUTOR_ENABLED: bool = True
    
    # ====================== AI Agent 配置 ======================
    # Agent 最大执行时间（秒）
    AGENT_MAX_EXECUTION_TIME: int = 300
    # Agent 最大重试次数
    AGENT_MAX_RETRIES: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# ====================== Tortoise-ORM 配置 ======================
TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

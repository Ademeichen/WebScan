"""
FastAPI 应用配置文件

使用 Pydantic Settings 管理应用配置，支持从环境变量和 .env 文件加载。
配置包括：服务器、数据库、日志、扫描、API密钥等。

配置加载优先级：
1. 环境变量
2. .env 文件
3. 代码中的默认值

使用方式：
    from config import settings
    
    # 访问配置项
    app_name = settings.APP_NAME
    debug_mode = settings.DEBUG
    
    # 在 .env 文件中覆盖配置
    # APP_NAME=My Custom App
    # DEBUG=True
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    应用配置类
    
    所有配置项都可以通过环境变量或 .env 文件覆盖。
    使用 Pydantic BaseSettings 实现类型安全和自动验证。
    
    Attributes:
        APP_NAME: 应用名称
        APP_VERSION: 应用版本号
        DEBUG: 调试模式开关
        HOST: 服务器监听地址
        PORT: 服务器监听端口
        CORS_ORIGINS: 允许跨域请求的源列表
        DATABASE_URL: 数据库连接字符串
        LOG_LEVEL: 日志级别
        LOG_FILE: 主日志文件路径
        CODE_EXECUTOR_LOG_FILE: 代码执行器日志文件路径
        MAX_CONCURRENT_SCANS: 最大并发扫描任务数
        SCAN_TIMEOUT: 扫描任务超时时间（秒）
        OPENAI_API_KEY: OpenAI API 密钥
        QWEN_API_KEY: 阿里云通义千问 API 密钥
        AWVS_API_URL: AWVS API 地址
        AWVS_API_KEY: AWVS API 密钥
        CODE_EXECUTOR_WORKSPACE: 代码执行工作空间路径
        CODE_EXECUTOR_TIMEOUT: 代码执行超时时间（秒）
        CODE_EXECUTOR_ENABLED: 是否启用代码执行功能
        AGENT_MAX_EXECUTION_TIME: AI Agent 最大执行时间（秒）
        AGENT_MAX_RETRIES: AI Agent 最大重试次数
    """
    
    # ====================== 应用基础配置 ======================
    APP_NAME: str = "WebScan AI Security Platform"
    """
    应用名称
    
    用于标识应用程序，显示在日志、API 文档等位置。
    可以通过环境变量 APP_NAME 覆盖。
    """
    
    APP_VERSION: str = "1.0.0"
    """
    应用版本号
    
    遵循语义化版本规范（Semantic Versioning）。
    格式：主版本号.次版本号.修订号
    - 主版本号：不兼容的 API 修改
    - 次版本号：向下兼容的功能性新增
    - 修订号：向下兼容的问题修正
    """
    
    DEBUG: bool = False
    """
    调试模式开关
    
    设置为 True 时：
    - 显示详细的错误堆栈信息
    - 启用自动重载（开发时）
    - 禁用某些安全检查
    - 记录更详细的日志
    
    生产环境应设置为 False。
    可以通过环境变量 DEBUG=True 覆盖。
    """
    
    # ====================== 服务器配置 ======================
    HOST: str = "127.0.0.1"
    """
    服务器监听地址
    
    默认为 127.0.0.1，仅允许本地访问。
    如需允许外部访问，设置为 0.0.0.0。
    可以通过环境变量 HOST 覆盖。
    """
    
    PORT: int = 3000
    """
    服务器监听端口
    
    默认端口为 3000。
    确保端口未被其他服务占用。
    可以通过环境变量 PORT 覆盖。
    """
    
    # ====================== CORS 配置 ======================
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000"
    ]
    """
    允许跨域请求的源列表
    
    CORS（跨域资源共享）配置，指定哪些前端域名可以访问后端 API。
    默认包含常见的开发服务器端口（Vite: 5173, 5174; Next.js: 3000）。
    
    在生产环境中，应将此列表限制为实际的前端域名。
    可以通过环境变量 CORS_ORIGINS 覆盖，格式为逗号分隔的列表。
    例如：CORS_ORIGINS=https://example.com,https://api.example.com
    """
    
    # ====================== 数据库配置 ======================
    DATABASE_URL: str = "sqlite://./data/webscan.db"
    """
    数据库连接字符串
    
    Tortoise-ORM 支持的数据库格式：
    - SQLite: sqlite://./database.db（默认，无需额外配置）
    - MySQL: mysql://user:password@host:port/database
    - PostgreSQL: postgres://user:password@host:port/database
    
    默认使用 SQLite，适合开发和测试环境。
    生产环境建议使用 MySQL 或 PostgreSQL 以获得更好的性能。
    可以通过环境变量 DATABASE_URL 覆盖。
    """
    
    # ====================== 日志配置 ======================
    LOG_LEVEL: str = "INFO"
    """
    日志级别
    
    可选值：
    - DEBUG: 最详细的日志信息，包含调试信息
    - INFO: 一般信息，记录应用正常运行状态
    - WARNING: 警告信息，表示潜在问题
    - ERROR: 错误信息，记录错误事件
    - CRITICAL: 严重错误，表示应用可能无法继续运行
    
    生产环境建议使用 INFO 或 WARNING。
    开发环境可以使用 DEBUG。
    可以通过环境变量 LOG_LEVEL 覆盖。
    """
    
    LOG_FILE: str = "logs/app.log"
    """
    主日志文件路径
    
    记录应用程序的主要日志信息。
    路径相对于项目根目录。
    确保日志目录有写入权限。
    可以通过环境变量 LOG_FILE 覆盖。
    """
    
    CODE_EXECUTOR_LOG_FILE: str = "logs/code_executor.log"
    """
    代码执行器日志文件路径
    
    专门记录代码执行相关的日志信息。
    与主日志分离，便于单独查看和分析代码执行问题。
    路径相对于项目根目录。
    可以通过环境变量 CODE_EXECUTOR_LOG_FILE 覆盖。
    """
    
    # ====================== 扫描配置 ======================
    MAX_CONCURRENT_SCANS: int = 5
    """
    最大并发扫描任务数
    
    控制同时执行的扫描任务数量上限。
    避免过多并发任务导致系统资源耗尽。
    根据服务器性能和需求调整此值。
    可以通过环境变量 MAX_CONCURRENT_SCANS 覆盖。
    """
    
    SCAN_TIMEOUT: int = 300
    """
    扫描任务超时时间（秒）
    
    单个扫描任务的最大执行时间。
    超过此时间后任务将被标记为失败。
    默认为 300 秒（5 分钟）。
    可以根据实际扫描需求调整。
    可以通过环境变量 SCAN_TIMEOUT 覆盖。
    """
    
    # ====================== API 密钥配置 ======================
    OPENAI_API_KEY: str = "341787347bdc5374dc6377f29a192907:Nzk5NTk4OTFkYmE5MTUzODI1YTM0MjNj"
    """
    OpenAI API 密钥
    
    用于访问 OpenAI 的 GPT 系列模型。
    用于 AI Agent、代码生成、漏洞分析等功能。
    获取方式：https://platform.openai.com/api-keys
    
    如果不使用 OpenAI 模型，可以留空。
    必须通过环境变量 OPENAI_API_KEY 设置，不要在代码中硬编码。
    """
    
    OPENAI_BASE_URL: str = "https://maas-api.cn-huabei-1.xf-yun.com/v2"
    """
    OpenAI API 基础 URL
    
    用于指定 OpenAI API 的自定义端点。
    默认为官方 OpenAI API 地址。
    如果使用第三方兼容服务（如阿里云 MaaS），可以修改此地址。
    可以通过环境变量 OPENAI_BASE_URL 覆盖。
    """
    
    MODEL_ID: str = "xop3qwen1b7"
    """
    AI 模型 ID
    
    指定使用的大语言模型。
    默认为通义千问 1b7 模型。
    可以根据需求切换不同的模型。
    可以通过环境变量 MODEL_ID 覆盖。
    """
    
    QWEN_API_KEY: Optional[str] = None
    """
    阿里云通义千问 API 密钥
    
    用于访问阿里云的通义千问大语言模型。
    作为 OpenAI 的替代方案，提供中文优化的 AI 能力。
    获取方式：https://dashscope.console.aliyun.com/apiKey
    
    如果不使用通义千问模型，可以留空。
    必须通过环境变量 QWEN_API_KEY 设置，不要在代码中硬编码。
    """
    
    # ====================== AWVS 配置 ======================
    AWVS_API_URL: str = "https://127.0.0.1:3443"
    """
    AWVS API 地址
    
    Acunetix Web Vulnerability Scanner 的 API 端点。
    默认为本地安装的 AWVS 地址。
    
    如果 AWVS 安装在其他服务器，请修改此地址。
    确保地址格式正确，包含协议（https）。
    可以通过环境变量 AWVS_API_URL 覆盖。
    """
    
    AWVS_API_KEY: str = "1986ad8c0a5b3df4d7028d5f3c06e936c986f9835bbf243cb9b33aee376ee7da9"
    """
    AWVS API 密钥
    
    用于认证和访问 AWVS API。
    在 AWVS 的用户配置中生成 API Key。
    
    安全提示：
    - 不要将此密钥提交到版本控制系统
    - 生产环境应通过环境变量设置
    - 定期更换密钥以提高安全性
    可以通过环境变量 AWVS_API_KEY 覆盖。
    """
    
    # ====================== 代码执行配置 ======================
    CODE_EXECUTOR_WORKSPACE: str = "executor_workspace"
    """
    代码执行工作空间路径
    
    用于存放代码执行相关的临时文件和输出。
    路径相对于项目根目录。
    
    确保此目录有读写权限。
    可以定期清理此目录以释放磁盘空间。
    可以通过环境变量 CODE_EXECUTOR_WORKSPACE 覆盖。
    """
    
    CODE_EXECUTOR_TIMEOUT: int = 30
    """
    代码执行超时时间（秒）
    
    单个代码执行任务的最大执行时间。
    超过此时间后代码执行将被终止。
    防止恶意或死循环代码占用过多资源。
    
    默认为 30 秒。
    可以根据实际需求调整。
    可以通过环境变量 CODE_EXECUTOR_TIMEOUT 覆盖。
    """
    
    CODE_EXECUTOR_ENABLED: bool = True
    """
    是否启用代码执行功能
    
    设置为 False 时，所有代码执行相关的 API 将被禁用。
    用于在不需要代码执行功能时提高安全性。
    
    生产环境如果不需要代码执行功能，建议设置为 False。
    可以通过环境变量 CODE_EXECUTOR_ENABLED 覆盖。
    """
    
    # ====================== AI Agent 配置 ======================
    AGENT_MAX_EXECUTION_TIME: int = 300
    """
    AI Agent 最大执行时间（秒）
    
    单个 AI Agent 任务的最大执行时间。
    超过此时间后 Agent 将被强制终止。
    防止 Agent 任务无限期运行。
    
    默认为 300 秒（5 分钟）。
    可以根据任务复杂度调整。
    可以通过环境变量 AGENT_MAX_EXECUTION_TIME 覆盖。
    """
    
    AGENT_MAX_RETRIES: int = 3
    """
    AI Agent 最大重试次数
    
    当 AI Agent 任务失败时的最大重试次数。
    提高任务执行的成功率。
    
    默认为 3 次。
    可以根据实际需求调整。
    可以通过环境变量 AGENT_MAX_RETRIES 覆盖。
    """
    
    class Config:
        """
        Pydantic 配置类
        
        定义配置文件加载方式和行为。
        """
        env_file = ".env"
        """
        环境变量文件路径
        
        从项目根目录的 .env 文件加载配置。
        文件格式：KEY=VALUE
        例如：
            APP_NAME=My App
            DEBUG=True
            DATABASE_URL=sqlite://./data/mydb.db
        """
        
        case_sensitive = True
        """
        是否区分大小写
        
        设置为 True 时，环境变量名称必须与配置项名称完全匹配（包括大小写）。
        例如：OPENAI_API_KEY（不是 openai_api_key）
        """


settings = Settings()
"""
全局配置实例

在应用中导入此实例来访问配置：
    from config import settings
    app_name = settings.APP_NAME
"""

# ====================== Tortoise-ORM 配置 ======================
TORTOISE_ORM = {
    """
    Tortoise-ORM 配置字典
    
    定义数据库连接和模型注册信息。
    用于初始化 Tortoise-ORM 和数据库迁移工具 Aerich。
    
    配置结构：
    - connections: 数据库连接配置
      - default: 默认连接，使用 settings.DATABASE_URL
    - apps: 应用和模型注册
      - models: 模型应用
        - models: 模型模块列表
          - models: 自定义模型模块
          - aerich.models: Aerich 迁移模型
        - default_connection: 使用的连接名称
    """
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

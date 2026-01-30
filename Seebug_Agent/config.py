"""
配置模块

管理Seebug Agent的所有配置项。
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Seebug Agent配置类"""

    Seebug API配置
    SEEBUG_API_KEY: str = "a1c22e6365df93275fa82397dbbdbbb7d9c6a75b"
    SEEBUG_BASE_URL: str = "https://www.seebug.org/api"
    SEEBUG_TIMEOUT: int = 30

    AI模型配置
    AI_BASE_URL: str = "https://api-inference.modelscope.cn/v1"
    AI_API_KEY: str = "ms-5c9c1aaf-f843-4648-8e24-8e0a9e4f2118"
    AI_MODEL_ID: str = "ZhipuAI/GLM-4.7-Flash"

    POC生成配置
    MAX_RETRIES: int = 5
    BASE_DELAY: int = 2

    输出配置
    OUTPUT_DIR: str = str(Path.cwd() / "generated_pocs")

    def __post_init__(self):
        """初始化后处理，确保输出目录存在"""
        self.OUTPUT_DIR = os.environ.get("SEEBUG_OUTPUT_DIR", self.OUTPUT_DIR)
        Path(self.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

        SEEBUG_API_KEY = os.environ.get("SEEBUG_API_KEY", self.SEEBUG_API_KEY)
        AI_API_KEY = os.environ.get("SEEBUG_AI_API_KEY", self.AI_API_KEY)
        AI_BASE_URL = os.environ.get("SEEBUG_AI_BASE_URL", self.AI_BASE_URL)
        AI_MODEL_ID = os.environ.get("SEEBUG_AI_MODEL_ID", self.AI_MODEL_ID)

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        return cls(
            SEEBUG_API_KEY=os.environ.get("SEEBUG_API_KEY", cls.SEEBUG_API_KEY),
            AI_API_KEY=os.environ.get("SEEBUG_AI_API_KEY", cls.AI_API_KEY),
            AI_BASE_URL=os.environ.get("SEEBUG_AI_BASE_URL", cls.AI_BASE_URL),
            AI_MODEL_ID=os.environ.get("SEEBUG_AI_MODEL_ID", cls.AI_MODEL_ID),
            OUTPUT_DIR=os.environ.get("SEEBUG_OUTPUT_DIR", cls.OUTPUT_DIR)
        )


global_config = Config()

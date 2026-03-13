"""
Seebug 工具模块

统一管理Seebug_Agent的导入和配置，提供统一的接口访问Seebug_Agent功能。
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from backend.config import settings

# 添加Seebug_Agent到Python路径
seebug_agent_path = Path(__file__).parent.parent.parent / "Seebug_Agent"
if str(seebug_agent_path) not in sys.path:
    sys.path.insert(0, str(seebug_agent_path))

# 导入Seebug_Agent模块
try:
    from Seebug_Agent import SeebugClient, SeebugAgent, Config as SeebugConfig
    
    SEBUG_AGENT_AVAILABLE = True
except ImportError as e:
    SEBUG_AGENT_AVAILABLE = False
    print(f"Seebug_Agent导入失败: {e}")


class SeebugUtils:
    """
    Seebug工具类
    
    提供统一的Seebug_Agent功能访问接口
    """
    
    _instance: Optional['SeebugUtils'] = None
    
    def __new__(cls):
        """
        单例模式
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        初始化Seebug工具
        """
        if self._initialized:
            return
        
        self._initialized = True
        self.config = None
        self.client = None
        self.agent = None
        
        if SEBUG_AGENT_AVAILABLE:
            self._initialize_components()
    
    def _initialize_components(self):
        """
        初始化Seebug组件
        """
        # 创建配置
        self.config = SeebugConfig()
        
        # 覆盖默认配置
        if hasattr(settings, 'SEEBUG_API_KEY'):
            self.config.SEEBUG_API_KEY = settings.SEEBUG_API_KEY
        
        if hasattr(settings, 'AI_API_KEY'):
            self.config.AI_API_KEY = settings.AI_API_KEY
        
        if hasattr(settings, 'AI_BASE_URL'):
            self.config.AI_BASE_URL = settings.AI_BASE_URL
        
        # 创建客户端
        self.client = SeebugClient(self.config)
        self.agent = SeebugAgent(self.config)
    
    def is_available(self) -> bool:
        """
        检查Seebug_Agent是否可用
        
        Returns:
            bool: 是否可用
        """
        return SEBUG_AGENT_AVAILABLE and self._initialized
    
    def get_client(self) -> Optional['SeebugClient']:
        """
        获取Seebug客户端
        
        Returns:
            Optional[SeebugClient]: Seebug客户端实例
        """
        return self.client if self.is_available() else None
    
    def get_agent(self) -> Optional['SeebugAgent']:
        """
        获取Seebug Agent
        
        Returns:
            Optional['SeebugAgent']: Seebug Agent实例
        """
        return self.agent if self.is_available() else None
    
    def search_vulnerabilities(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        搜索漏洞
        
        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        if not self.is_available():
            return {"status": "error", "msg": "Seebug_Agent not available"}
        
        return self.agent.search_vulnerabilities(keyword, page, page_size)
    
    def get_vulnerability_detail(self, ssvid: str) -> Dict[str, Any]:
        """
        获取漏洞详情
        
        Args:
            ssvid: 漏洞的SSVID
            
        Returns:
            Dict[str, Any]: 漏洞详情
        """
        if not self.is_available():
            return {"status": "error", "msg": "Seebug_Agent not available"}
        
        return self.agent.get_vulnerability_detail(ssvid)
    
    def validate_api_key(self) -> Dict[str, Any]:
        """
        验证API Key
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        if not self.is_available():
            return {"status": "error", "msg": "Seebug_Agent not available"}
        
        return self.client.validate_key()
    
    def get_api_status(self) -> Dict[str, Any]:
        """
        获取API状态
        
        Returns:
            Dict[str, Any]: API状态信息
        """
        if not self.is_available():
            return {"available": False, "message": "Seebug_Agent not available"}
        
        status = self.client.validate_key()
        return {
            "available": status.get("status") == "success",
            "message": status.get("msg", ""),
            "data": status
        }


# 全局实例
seebug_utils = SeebugUtils()

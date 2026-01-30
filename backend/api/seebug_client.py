"""
Seebug API 客户端

提供统一的Seebug API调用接口,使用Seebug_Agent的SeebugClient实现。
支持:
- Seebug POC搜索
- Seebug POC详情获取
- Seebug POC下载
- API Key验证
- 网页爬取模式降级
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from backend.config import settings
from backend.utils.seebug_utils import seebug_utils

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """
    API响应数据类

    用于存储API响应的标准化数据
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    status_code: int = 200
    execution_time: float = 0.0


class SeebugAPIClient:
    """
    Seebug API客户端类

    基于Seebug_Agent的SeebugClient实现,提供统一的Seebug API调用接口。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://www.seebug.org/api",
        timeout: float = 5.0,
        max_retries: int = 3,
        enable_cache: bool = True
    ):
        """
        初始化Seebug API客户端

        Args:
            api_key: Seebug API密钥,默认从settings读取
            base_url: API基础URL
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            enable_cache: 是否启用缓存
        """
        self.api_key = api_key or settings.SEEBUG_API_KEY
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_cache = enable_cache

        self.cache: Dict[str, tuple] = {}
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

        # 使用统一的Seebug工具
        self.seebug_client = seebug_utils.get_client()

        logger.info(f"✅ Seebug API客户端初始化完成: {base_url}")

    async def validate_api_key(self) -> APIResponse:
        """
        验证API Key是否有效

        Args:
            无

        Returns:
            APIResponse: 验证结果
        """
        cache_key = f"validate_key_{self.api_key[:8]}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 3600:
                logger.info("✅ 使用缓存的API Key验证结果")
                return cached_data

        logger.info("🔍 开始验证Seebug API Key")

        try:
            result = self.seebug_client.validate_key()
            success = result.get("status") == "success"
            message = result.get("msg", "")

            response = APIResponse(
                success=success,
                message=message,
                status_code=200 if success else 401,
                execution_time=0.0
            )

            if success:
                logger.info("✅ Seebug API Key验证成功")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ Seebug API Key验证失败: {message}")

            return response

        except Exception as e:
            logger.error(f"❌ 验证Seebug API Key异常: {str(e)}")
            return APIResponse(
                success=False,
                message=f"验证异常: {str(e)}",
                status_code=500
            )

    async def search_poc(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 10
    ) -> APIResponse:
        """
        搜索POC

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            APIResponse: 搜索结果
        """
        cache_key = f"search_poc_{keyword}_{page}_{page_size}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 1800:
                logger.info("✅ 使用缓存的POC搜索结果")
                return cached_data

        logger.info(f"🔍 开始搜索POC: 关键词={keyword}, 页码={page}")

        try:
            result = self.seebug_client.search_poc(keyword, page, page_size)
            success = result.get("status") == "success"
            data = result.get("data", {})
            message = result.get("msg", "")

            response = APIResponse(
                success=success,
                data=data,
                message=message,
                status_code=200 if success else 404,
                execution_time=0.0
            )

            if success:
                logger.info(f"✅ POC搜索成功: 找到{data.get('total', 0)}个结果")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC搜索失败: {message}")

            return response

        except Exception as e:
            logger.error(f"❌ POC搜索异常: {str(e)}")
            return APIResponse(
                success=False,
                message=f"搜索异常: {str(e)}",
                status_code=500
            )

    async def download_poc(self, ssvid: int) -> APIResponse:
        """
        下载POC代码

        Args:
            ssvid: POC的SSVID

        Returns:
            APIResponse: 下载结果
        """
        cache_key = f"download_poc_{ssvid}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 21600:
                logger.info(f"✅ 使用缓存的POC代码: SSVID={ssvid}")
                return cached_data

        logger.info(f"📥 开始下载POC: SSVID={ssvid}")

        try:
            result = self.seebug_client.download_poc(ssvid)
            success = result.get("status") == "success"
            data = result.get("data", {})
            message = result.get("msg", "")

            response = APIResponse(
                success=success,
                data=data,
                message=message,
                status_code=200 if success else 404,
                execution_time=0.0
            )

            if success:
                logger.info(f"✅ POC下载成功: SSVID={ssvid}")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC下载失败: {message}")

            return response

        except Exception as e:
            logger.error(f"❌ POC下载异常: {str(e)}")
            return APIResponse(
                success=False,
                message=f"下载异常: {str(e)}",
                status_code=500
            )

    async def get_poc_detail(self, ssvid: int) -> APIResponse:
        """
        获取POC详情

        Args:
            ssvid: POC的SSVID

        Returns:
            APIResponse: POC详情
        """
        cache_key = f"poc_detail_{ssvid}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 21600:
                logger.info(f"✅ 使用缓存的POC详情: SSVID={ssvid}")
                return cached_data

        logger.info(f"🔍 开始获取POC详情: SSVID={ssvid}")

        try:
            result = self.seebug_client.get_poc_detail(ssvid)
            success = result.get("status") == "success"
            data = result.get("data", {})
            message = result.get("msg", "")

            response = APIResponse(
                success=success,
                data=data,
                message=message,
                status_code=200 if success else 404,
                execution_time=0.0
            )

            if success:
                logger.info(f"✅ POC详情获取成功: SSVID={ssvid}")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC详情获取失败: {message}")

            return response

        except Exception as e:
            logger.error(f"❌ POC详情获取异常: {str(e)}")
            return APIResponse(
                success=False,
                message=f"获取详情异常: {str(e)}",
                status_code=500
            )

    def clear_cache(self):
        """
        清除缓存
        """
        self.cache.clear()
        logger.info("✅ API缓存已清除")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict: 缓存统计
        """
        return {
            "cache_entries": len(self.cache),
            "cache_enabled": self.enable_cache,
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (
                self.success_count / self.request_count * 100
                if self.request_count > 0 else 0
            )
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取客户端统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "cache_enabled": self.enable_cache,
            "cache_stats": self.get_cache_stats(),
            "seebug_agent_available": bool(self.seebug_client)
        }
    
    async def generate_poc_from_seebug(
        self,
        ssvid: str
    ) -> APIResponse:
        """
        从Seebug生成POC代码

        Args:
            ssvid: 漏洞的SSVID

        Returns:
            APIResponse: 生成结果
        """
        logger.info(f"🤖 开始从Seebug生成POC,SSVID: {ssvid}")

        try:
            # 检查Seebug Agent是否可用
            if not self.seebug_client:
                return APIResponse(
                    success=False,
                    message="Seebug Agent不可用",
                    status_code=503
                )
            
            # 获取漏洞详情
            detail_result = self.seebug_client.get_poc_detail(ssvid)
            
            if detail_result.get("status") != "success":
                return APIResponse(
                    success=False,
                    message=detail_result.get("msg", "获取漏洞详情失败"),
                    status_code=404
                )
            
            vul_data = detail_result.get("data", {})
            
            # 生成POC代码
            from backend.utils.seebug_utils import seebug_utils
            generator = seebug_utils.get_generator()
            
            if not generator:
                return APIResponse(
                    success=False,
                    message="POC生成器不可用",
                    status_code=503
                )
            
            poc_code = generator.generate_poc(vul_data)
            
            if not poc_code:
                return APIResponse(
                    success=False,
                    message="POC生成失败",
                    status_code=500
                )
            
            logger.info(f"✅ POC生成成功,代码长度: {len(poc_code)}")
            
            return APIResponse(
                success=True,
                data={
                    "poc_code": poc_code,
                    "vulnerability": vul_data
                },
                message="POC生成成功"
            )

        except Exception as e:
            logger.error(f"❌ 从Seebug生成POC异常: {str(e)}")
            return APIResponse(
                success=False,
                message=f"生成POC异常: {str(e)}",
                status_code=500
            )
    
    async def search_and_generate(
        self,
        keyword: str,
        selection: int = 0
    ) -> APIResponse:
        """
        搜索漏洞并生成POC

        Args:
            keyword: 搜索关键词
            selection: 选择的结果索引

        Returns:
            APIResponse: 生成结果
        """
        logger.info(f"🔍 开始搜索并生成POC,关键词: {keyword}, 选择: {selection}")

        try:
            # 检查Seebug Agent是否可用
            if not self.seebug_client:
                return APIResponse(
                    success=False,
                    message="Seebug Agent不可用",
                    status_code=503
                )
            
            # 使用Seebug Agent搜索并生成
            from backend.utils.seebug_utils import seebug_utils
            agent = seebug_utils.get_agent()
            
            if not agent:
                return APIResponse(
                    success=False,
                    message="Seebug Agent不可用",
                    status_code=503
                )
            
            result = agent.search_and_generate(keyword, selection)
            
            success = result.get("success", False)
            
            if success:
                logger.info(f"✅ 搜索并生成POC成功,路径: {result.get('poc_path')}")
                return APIResponse(
                    success=True,
                    data=result,
                    message="搜索并生成POC成功"
                )
            else:
                message = result.get("message", "操作失败")
                logger.warning(f"⚠️ 搜索并生成POC失败: {message}")
                return APIResponse(
                    success=False,
                    message=message,
                    status_code=404
                )

        except Exception as e:
            logger.error(f"❌ 搜索并生成POC异常: {str(e)}")
            return APIResponse(
                success=False,
                message=f"操作异常: {str(e)}",
                status_code=500
            )

global_seebug_client = SeebugAPIClient()

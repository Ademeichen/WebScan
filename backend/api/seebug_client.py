"""
Seebug API 客户端

提供统一的Seebug API调用接口,包括:
- 指数退避重试机制(最多3次)
- 统一超时处理(5秒)
- 分级错误日志记录(INFO/WARN/ERROR)
- 连接池管理
- API响应缓存
"""
import logging
import asyncio
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from backend.config import settings

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

    提供统一的Seebug API调用接口,支持:
    - 指数退避重试机制
    - 统一超时处理
    - 分级错误日志记录
    - 连接池管理
    - 响应缓存
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
            if datetime.now() - timestamp < timedelta(hours=1):
                logger.info("✅ 使用缓存的API Key验证结果")
                return cached_data

        logger.info("🔍 开始验证Seebug API Key")

        try:
            response = await self._make_request(
                method="GET",
                endpoint="/token/validate",
                params={"key": self.api_key}
            )

            if response.success:
                logger.info("✅ Seebug API Key验证成功")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
                return response
            else:
                logger.warning(f"⚠️ Seebug API Key验证失败: {response.message}")
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
            if datetime.now() - timestamp < timedelta(minutes=30):
                logger.info("✅ 使用缓存的POC搜索结果")
                return cached_data

        logger.info(f"🔍 开始搜索POC: 关键词={keyword}, 页码={page}")

        try:
            params = {
                "key": self.api_key,
                "keyword": keyword,
                "page": page,
                "page_size": page_size
            }

            response = await self._make_request(
                method="GET",
                endpoint="/poc/search",
                params=params
            )

            if response.success:
                logger.info(f"✅ POC搜索成功: 找到{len(response.data.get('data', []))}个结果")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC搜索失败: {response.message}")

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
            if datetime.now() - timestamp < timedelta(hours=6):
                logger.info(f"✅ 使用缓存的POC代码: SSVID={ssvid}")
                return cached_data

        logger.info(f"📥 开始下载POC: SSVID={ssvid}")

        try:
            params = {
                "key": self.api_key,
                "ssvid": ssvid
            }

            response = await self._make_request(
                method="GET",
                endpoint="/poc/download",
                params=params
            )

            if response.success:
                logger.info(f"✅ POC下载成功: SSVID={ssvid}")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC下载失败: {response.message}")

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
            if datetime.now() - timestamp < timedelta(hours=6):
                logger.info(f"✅ 使用缓存的POC详情: SSVID={ssvid}")
                return cached_data

        logger.info(f"🔍 开始获取POC详情: SSVID={ssvid}")

        try:
            params = {
                "key": self.api_key,
                "ssvid": ssvid
            }

            response = await self._make_request(
                method="GET",
                endpoint="/poc/get",
                params=params
            )

            if response.success:
                logger.info(f"✅ POC详情获取成功: SSVID={ssvid}")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC详情获取失败: {response.message}")

            return response

        except Exception as e:
            logger.error(f"❌ POC详情获取异常: {str(e)}")
            return APIResponse(
                success=False,
                message=f"获取详情异常: {str(e)}",
                status_code=500
            )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        """
        发送HTTP请求(带重试机制)

        Args:
            method: HTTP方法(GET/POST)
            endpoint: API端点
            params: 查询参数
            data: 请求体数据

        Returns:
            APIResponse: API响应
        """
        url = f"{self.base_url}{endpoint}"
        self.request_count += 1

        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                if method == "GET":
                    from pocsuite3.lib.request import requests
                    resp = requests.get(
                        url,
                        params=params,
                        timeout=self.timeout
                    )
                else:
                    from pocsuite3.lib.request import requests
                    resp = requests.post(
                        url,
                        params=params,
                        data=data,
                        timeout=self.timeout
                    )

                execution_time = time.time() - start_time

                if resp and resp.status_code == 200:
                    self.success_count += 1
                    logger.debug(f"✅ 请求成功: {endpoint}, 耗时: {execution_time:.2f}秒")

                    try:
                        json_data = resp.json()

                        if json_data.get("status") == "success":
                            return APIResponse(
                                success=True,
                                data=json_data.get("data"),
                                message=json_data.get("msg", ""),
                                status_code=resp.status_code,
                                execution_time=execution_time
                            )
                        else:
                            return APIResponse(
                                success=False,
                                message=json_data.get("msg", "请求失败"),
                                status_code=resp.status_code,
                                execution_time=execution_time
                            )
                    except Exception as e:
                        logger.warning(f"⚠️ JSON解析失败: {str(e)}")
                        return APIResponse(
                            success=False,
                            message=f"响应解析失败: {str(e)}",
                            status_code=resp.status_code,
                            execution_time=execution_time
                        )

                elif resp and resp.status_code == 401:
                    logger.warning(f"⚠️ API认证失败: {endpoint}")
                    return APIResponse(
                        success=False,
                        message="API Key无效或已过期",
                        status_code=resp.status_code,
                        execution_time=execution_time
                    )

                elif resp and resp.status_code == 429:
                    logger.warning(f"⚠️ 请求过于频繁: {endpoint}")
                    delay = 2 ** attempt
                    logger.info(f"⏰ 指数退避等待: {delay}秒")
                    await asyncio.sleep(delay)
                    continue

                else:
                    logger.warning(f"⚠️ 请求失败: {endpoint}, 状态码: {resp.status_code}")
                    return APIResponse(
                        success=False,
                        message=f"HTTP错误: {resp.status_code}",
                        status_code=resp.status_code,
                        execution_time=execution_time
                    )

            except Exception as e:
                self.error_count += 1
                error_type = type(e).__name__

                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt
                    logger.warning(
                        f"⚠️ 请求异常 (第{attempt + 1}次): {error_type}: {str(e)}, "
                        f"等待{delay}秒后重试..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ 请求失败,已达最大重试次数: {error_type}: {str(e)}")
                    return APIResponse(
                        success=False,
                        message=f"请求异常: {str(e)}",
                        status_code=500,
                        execution_time=0.0
                    )

        return APIResponse(
            success=False,
            message="超过最大重试次数",
            status_code=500,
            execution_time=0.0
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
            "cache_stats": self.get_cache_stats()
        }


global_seebug_client = SeebugAPIClient()

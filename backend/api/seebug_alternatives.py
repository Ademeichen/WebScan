"""
Seebug API备选实现方案

提供2种不依赖pocsuite3的Seebug API实现方案：
- 方案A: 直接HTTP请求（使用requests）
- 方案B: 异步HTTP客户端（使用aiohttp）

这两种方案都可以在pocsuite3不可用或不满足需求时使用。
"""
import logging
import requests
import aiohttp
import asyncio
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SeebugAPIResponse:
    """
    Seebug API响应数据类
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    status_code: int = 200
    execution_time: float = 0.0


class DirectSeebugClient:
    """
    方案A: 直接HTTP请求的Seebug客户端

    使用requests库直接调用Seebug API，不依赖pocsuite3。

    特点:
    - 轻量级，易于集成
    - 完全控制实现细节
    - 适合同步场景

    使用场景:
    - pocsuite3不可用
    - 需要自定义API调用逻辑
    - 同步应用场景
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://www.seebug.org/api",
        timeout: float = 5.0,
        max_retries: int = 3,
        enable_cache: bool = True
    ):
        """
        初始化直接HTTP客户端

        Args:
            api_key: Seebug API密钥
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            enable_cache: 是否启用缓存
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_cache = enable_cache

        self.session = requests.Session()
        self.cache: Dict[str, tuple] = {}
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

        logger.info(f"✅ 直接HTTP客户端初始化完成: {base_url}")

    def validate_api_key(self) -> SeebugAPIResponse:
        """
        验证API Key是否有效

        Args:
            无

        Returns:
            SeebugAPIResponse: 验证结果
        """
        cache_key = f"validate_key_{self.api_key[:8]}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 3600:
                logger.info(f"✅ 使用缓存的API Key验证结果")
                return cached_data

        logger.info(f"🔍 开始验证Seebug API Key")

        try:
            url = f"{self.base_url}/token/validate"
            params = {"key": self.api_key}

            response = self._make_request("GET", url, params=params)

            if response.success:
                logger.info(f"✅ Seebug API Key验证成功")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
                return response
            else:
                logger.warning(f"⚠️ Seebug API Key验证失败: {response.message}")
                return response

        except Exception as e:
            logger.error(f"❌ 验证Seebug API Key异常: {str(e)}")
            return SeebugAPIResponse(
                success=False,
                message=f"验证异常: {str(e)}",
                status_code=500
            )

    def search_poc(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 10
    ) -> SeebugAPIResponse:
        """
        搜索POC

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            SeebugAPIResponse: 搜索结果
        """
        cache_key = f"search_poc_{keyword}_{page}_{page_size}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 1800:
                logger.info(f"✅ 使用缓存的POC搜索结果")
                return cached_data

        logger.info(f"🔍 开始搜索POC: 关键词={keyword}, 页码={page}")

        try:
            url = f"{self.base_url}/poc/search"
            params = {
                "key": self.api_key,
                "keyword": keyword,
                "page": page,
                "page_size": page_size
            }

            response = self._make_request("GET", url, params=params)

            if response.success:
                logger.info(f"✅ POC搜索成功: 找到{len(response.data.get('data', []))}个结果")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC搜索失败: {response.message}")

            return response

        except Exception as e:
            logger.error(f"❌ POC搜索异常: {str(e)}")
            return SeebugAPIResponse(
                success=False,
                message=f"搜索异常: {str(e)}",
                status_code=500
            )

    def download_poc(self, ssvid: int) -> SeebugAPIResponse:
        """
        下载POC代码

        Args:
            ssvid: POC的SSVID

        Returns:
            SeebugAPIResponse: 下载结果
        """
        cache_key = f"download_poc_{ssvid}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 21600:
                logger.info(f"✅ 使用缓存的POC代码: SSVID={ssvid}")
                return cached_data

        logger.info(f"📥 开始下载POC: SSVID={ssvid}")

        try:
            url = f"{self.base_url}/poc/download"
            params = {
                "key": self.api_key,
                "ssvid": ssvid
            }

            response = self._make_request("GET", url, params=params)

            if response.success:
                logger.info(f"✅ POC下载成功: SSVID={ssvid}")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC下载失败: {response.message}")

            return response

        except Exception as e:
            logger.error(f"❌ POC下载异常: {str(e)}")
            return SeebugAPIResponse(
                success=False,
                message=f"下载异常: {str(e)}",
                status_code=500
            )

    def get_poc_detail(self, ssvid: int) -> SeebugAPIResponse:
        """
        获取POC详情

        Args:
            ssvid: POC的SSVID

        Returns:
            SeebugAPIResponse: POC详情
        """
        cache_key = f"poc_detail_{ssvid}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 21600:
                logger.info(f"✅ 使用缓存的POC详情: SSVID={ssvid}")
                return cached_data

        logger.info(f"🔍 开始获取POC详情: SSVID={ssvid}")

        try:
            url = f"{self.base_url}/poc/get"
            params = {
                "key": self.api_key,
                "ssvid": ssvid
            }

            response = self._make_request("GET", url, params=params)

            if response.success:
                logger.info(f"✅ POC详情获取成功: SSVID={ssvid}")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC详情获取失败: {response.message}")

            return response

        except Exception as e:
            logger.error(f"❌ POC详情获取异常: {str(e)}")
            return SeebugAPIResponse(
                success=False,
                message=f"获取详情异常: {str(e)}",
                status_code=500
            )

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> SeebugAPIResponse:
        """
        发送HTTP请求（带重试机制）

        Args:
            method: HTTP方法（GET/POST）
            url: 请求URL
            params: 查询参数
            data: 请求体数据

        Returns:
            SeebugAPIResponse: API响应
        """
        self.request_count += 1

        for attempt in range(self.max_retries):
            try:
                import time
                start_time = time.time()

                if method == "GET":
                    resp = self.session.get(
                        url,
                        params=params,
                        timeout=self.timeout
                    )
                else:
                    resp = self.session.post(
                        url,
                        params=params,
                        data=data,
                        timeout=self.timeout
                    )

                execution_time = time.time() - start_time

                if resp and resp.status_code == 200:
                    self.success_count += 1
                    logger.debug(f"✅ 请求成功: {url}, 耗时: {execution_time:.2f}秒")

                    try:
                        json_data = resp.json()

                        if json_data.get("status") == "success":
                            return SeebugAPIResponse(
                                success=True,
                                data=json_data.get("data"),
                                message=json_data.get("msg", ""),
                                status_code=resp.status_code,
                                execution_time=execution_time
                            )
                        else:
                            return SeebugAPIResponse(
                                success=False,
                                message=json_data.get("msg", "请求失败"),
                                status_code=resp.status_code,
                                execution_time=execution_time
                            )
                    except Exception as e:
                        logger.warning(f"⚠️ JSON解析失败: {str(e)}")
                        return SeebugAPIResponse(
                            success=False,
                            message=f"响应解析失败: {str(e)}",
                            status_code=resp.status_code,
                            execution_time=execution_time
                        )

                elif resp and resp.status_code == 401:
                    logger.warning(f"⚠️ API认证失败: {url}")
                    return SeebugAPIResponse(
                        success=False,
                        message="API Key无效或已过期",
                        status_code=resp.status_code,
                        execution_time=execution_time
                    )

                elif resp and resp.status_code == 429:
                    logger.warning(f"⚠️ 请求过于频繁: {url}")
                    delay = 2 ** attempt
                    logger.info(f"⏰ 指数退避等待: {delay}秒")
                    time.sleep(delay)
                    continue

                else:
                    logger.warning(f"⚠️ 请求失败: {url}, 状态码: {resp.status_code}")
                    return SeebugAPIResponse(
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
                    time.sleep(delay)
                else:
                    logger.error(f"❌ 请求失败，已达最大重试次数: {error_type}: {str(e)}")
                    return SeebugAPIResponse(
                        success=False,
                        message=f"请求异常: {str(e)}",
                        status_code=500,
                        execution_time=0.0
                    )

        return SeebugAPIResponse(
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

    def close(self):
        """
        关闭会话
        """
        self.session.close()
        logger.info("✅ 直接HTTP客户端已关闭")


class AsyncSeebugClient:
    """
    方案B: 异步HTTP客户端的Seebug客户端

    使用aiohttp库实现高性能的异步API调用，不依赖pocsuite3。

    特点:
    - 异步高性能
    - 支持并发请求
    - 连接池管理
    - 适合高并发场景

    使用场景:
    - 高并发API调用
    - 异步应用架构
    - 需要高性能场景
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://www.seebug.org/api",
        timeout: float = 5.0,
        max_retries: int = 3,
        enable_cache: bool = True,
        max_connections: int = 10
    ):
        """
        初始化异步HTTP客户端

        Args:
            api_key: Seebug API密钥
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            enable_cache: 是否启用缓存
            max_connections: 最大连接数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self.connector = aiohttp.TCPConnector(limit=max_connections)
        self.session = None

        self.cache: Dict[str, tuple] = {}
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

        logger.info(f"✅ 异步HTTP客户端初始化完成: {base_url}")

    async def __aenter__(self):
        """
        异步上下文管理器入口
        """
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=self.timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器出口
        """
        if self.session:
            await self.session.close()

    async def validate_api_key(self) -> SeebugAPIResponse:
        """
        验证API Key是否有效

        Args:
            无

        Returns:
            SeebugAPIResponse: 验证结果
        """
        cache_key = f"validate_key_{self.api_key[:8]}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 3600:
                logger.info(f"✅ 使用缓存的API Key验证结果")
                return cached_data

        logger.info(f"🔍 开始验证Seebug API Key")

        try:
            url = f"{self.base_url}/token/validate"
            params = {"key": self.api_key}

            response = await self._make_request("GET", url, params=params)

            if response.success:
                logger.info(f"✅ Seebug API Key验证成功")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
                return response
            else:
                logger.warning(f"⚠️ Seebug API Key验证失败: {response.message}")
                return response

        except Exception as e:
            logger.error(f"❌ 验证Seebug API Key异常: {str(e)}")
            return SeebugAPIResponse(
                success=False,
                message=f"验证异常: {str(e)}",
                status_code=500
            )

    async def search_poc(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 10
    ) -> SeebugAPIResponse:
        """
        搜索POC

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            SeebugAPIResponse: 搜索结果
        """
        cache_key = f"search_poc_{keyword}_{page}_{page_size}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 1800:
                logger.info(f"✅ 使用缓存的POC搜索结果")
                return cached_data

        logger.info(f"🔍 开始搜索POC: 关键词={keyword}, 页码={page}")

        try:
            url = f"{self.base_url}/poc/search"
            params = {
                "key": self.api_key,
                "keyword": keyword,
                "page": page,
                "page_size": page_size
            }

            response = await self._make_request("GET", url, params=params)

            if response.success:
                logger.info(f"✅ POC搜索成功: 找到{len(response.data.get('data', []))}个结果")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC搜索失败: {response.message}")

            return response

        except Exception as e:
            logger.error(f"❌ POC搜索异常: {str(e)}")
            return SeebugAPIResponse(
                success=False,
                message=f"搜索异常: {str(e)}",
                status_code=500
            )

    async def download_poc(self, ssvid: int) -> SeebugAPIResponse:
        """
        下载POC代码

        Args:
            ssvid: POC的SSVID

        Returns:
            SeebugAPIResponse: 下载结果
        """
        cache_key = f"download_poc_{ssvid}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 21600:
                logger.info(f"✅ 使用缓存的POC代码: SSVID={ssvid}")
                return cached_data

        logger.info(f"📥 开始下载POC: SSVID={ssvid}")

        try:
            url = f"{self.base_url}/poc/download"
            params = {
                "key": self.api_key,
                "ssvid": ssvid
            }

            response = await self._make_request("GET", url, params=params)

            if response.success:
                logger.info(f"✅ POC下载成功: SSVID={ssvid}")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC下载失败: {response.message}")

            return response

        except Exception as e:
            logger.error(f"❌ POC下载异常: {str(e)}")
            return SeebugAPIResponse(
                success=False,
                message=f"下载异常: {str(e)}",
                status_code=500
            )

    async def get_poc_detail(self, ssvid: int) -> SeebugAPIResponse:
        """
        获取POC详情

        Args:
            ssvid: POC的SSVID

        Returns:
            SeebugAPIResponse: POC详情
        """
        cache_key = f"poc_detail_{ssvid}"

        if self.enable_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 21600:
                logger.info(f"✅ 使用缓存的POC详情: SSVID={ssvid}")
                return cached_data

        logger.info(f"🔍 开始获取POC详情: SSVID={ssvid}")

        try:
            url = f"{self.base_url}/poc/get"
            params = {
                "key": self.api_key,
                "ssvid": ssvid
            }

            response = await self._make_request("GET", url, params=params)

            if response.success:
                logger.info(f"✅ POC详情获取成功: SSVID={ssvid}")
                if self.enable_cache:
                    self.cache[cache_key] = (response, datetime.now())
            else:
                logger.warning(f"⚠️ POC详情获取失败: {response.message}")

            return response

        except Exception as e:
            logger.error(f"❌ POC详情获取异常: {str(e)}")
            return SeebugAPIResponse(
                success=False,
                message=f"获取详情异常: {str(e)}",
                status_code=500
            )

    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> SeebugAPIResponse:
        """
        发送异步HTTP请求（带重试机制）

        Args:
            method: HTTP方法（GET/POST）
            url: 请求URL
            params: 查询参数
            data: 请求体数据

        Returns:
            SeebugAPIResponse: API响应
        """
        self.request_count += 1

        for attempt in range(self.max_retries):
            try:
                import time
                start_time = time.time()

                if method == "GET":
                    async with self.session.get(url, params=params) as resp:
                        execution_time = time.time() - start_time

                        if resp.status == 200:
                            self.success_count += 1
                            logger.debug(f"✅ 请求成功: {url}, 耗时: {execution_time:.2f}秒")

                            json_data = await resp.json()

                            if json_data.get("status") == "success":
                                return SeebugAPIResponse(
                                    success=True,
                                    data=json_data.get("data"),
                                    message=json_data.get("msg", ""),
                                    status_code=resp.status,
                                    execution_time=execution_time
                                )
                            else:
                                return SeebugAPIResponse(
                                    success=False,
                                    message=json_data.get("msg", "请求失败"),
                                    status_code=resp.status,
                                    execution_time=execution_time
                                )

                        elif resp.status == 401:
                            logger.warning(f"⚠️ API认证失败: {url}")
                            return SeebugAPIResponse(
                                success=False,
                                message="API Key无效或已过期",
                                status_code=resp.status,
                                execution_time=execution_time
                            )

                        elif resp.status == 429:
                            logger.warning(f"⚠️ 请求过于频繁: {url}")
                            delay = 2 ** attempt
                            logger.info(f"⏰ 指数退避等待: {delay}秒")
                            await asyncio.sleep(delay)
                            continue

                        else:
                            logger.warning(f"⚠️ 请求失败: {url}, 状态码: {resp.status}")
                            return SeebugAPIResponse(
                                success=False,
                                message=f"HTTP错误: {resp.status}",
                                status_code=resp.status,
                                execution_time=execution_time
                            )

                else:
                    async with self.session.post(url, params=params, data=data) as resp:
                        execution_time = time.time() - start_time

                        if resp.status == 200:
                            self.success_count += 1
                            logger.debug(f"✅ 请求成功: {url}, 耗时: {execution_time:.2f}秒")

                            json_data = await resp.json()

                            if json_data.get("status") == "success":
                                return SeebugAPIResponse(
                                    success=True,
                                    data=json_data.get("data"),
                                    message=json_data.get("msg", ""),
                                    status_code=resp.status,
                                    execution_time=execution_time
                                )
                            else:
                                return SeebugAPIResponse(
                                    success=False,
                                    message=json_data.get("msg", "请求失败"),
                                    status_code=resp.status,
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
                    logger.error(f"❌ 请求失败，已达最大重试次数: {error_type}: {str(e)}")
                    return SeebugAPIResponse(
                        success=False,
                        message=f"请求异常: {str(e)}",
                        status_code=500,
                        execution_time=0.0
                    )

        return SeebugAPIResponse(
            success=False,
            message="超过最大重试次数",
            status_code=500,
            execution_time=0.0
        )

    async def batch_search_poc(
        self,
        keywords: List[str]
    ) -> Dict[str, SeebugAPIResponse]:
        """
        批量搜索POC

        Args:
            keywords: 关键词列表

        Returns:
            Dict: 搜索结果
        """
        tasks = [self.search_poc(keyword) for keyword in keywords]
        results = await asyncio.gather(*tasks)

        return dict(zip(keywords, results))

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


async def main():
    """
    使用示例
    """
    from backend.config import settings

    api_key = settings.SEEBUG_API_KEY

    # 使用方案A: 直接HTTP客户端
    print("=== 方案A: 直接HTTP客户端 ===")
    direct_client = DirectSeebugClient(api_key=api_key)

    validate_result = direct_client.validate_api_key()
    print(f"验证结果: {validate_result.success}")

    search_result = direct_client.search_poc("ThinkPHP")
    print(f"搜索结果: {search_result.success}")

    direct_client.close()

    # 使用方案B: 异步HTTP客户端
    print("\n=== 方案B: 异步HTTP客户端 ===")
    async with AsyncSeebugClient(api_key=api_key) as async_client:
        validate_result = await async_client.validate_api_key()
        print(f"验证结果: {validate_result.success}")

        search_result = await async_client.search_poc("ThinkPHP")
        print(f"搜索结果: {search_result.success}")

        # 批量搜索
        keywords = ["ThinkPHP", "Spring", "Log4j"]
        batch_results = await async_client.batch_search_poc(keywords)
        print(f"批量搜索结果: {len(batch_results)}")


if __name__ == "__main__":
    asyncio.run(main())

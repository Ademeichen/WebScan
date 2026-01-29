"""
数据源抽象层

提供统一的数据获取接口，包括：
- 数据源抽象基类
- 数据验证机制
- 缓存策略
- 数据去重和更新策略
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """
    数据源类型枚举
    """
    SEEBUG = "seebug"
    EXPLOIT_DB = "exploit_db"
    CVE = "cve"
    NVD = "nvd"


@dataclass
class VulnerabilityData:
    """
    漏洞数据标准化模型
    """
    cve_id: str
    name: str
    description: str
    severity: str
    cvss_score: float
    affected_product: str
    solution: str
    has_poc: bool
    source: str
    poc_code: Optional[str] = None
    ssvid: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        """
        return {
            "cve_id": self.cve_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "affected_product": self.affected_product,
            "solution": self.solution,
            "has_poc": self.has_poc,
            "source": self.source,
            "poc_code": self.poc_code,
            "ssvid": self.ssvid,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class DataValidator:
    """
    数据验证器
    """

    @staticmethod
    def validate_vulnerability_data(data: Dict[str, Any]) -> bool:
        """
        验证漏洞数据的有效性

        Args:
            data: 漏洞数据字典

        Returns:
            bool: 数据是否有效
        """
        required_fields = ["name", "description", "severity"]

        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"❌ 数据验证失败: 缺少必填字段 {field}")
                return False

        if "cvss_score" in data:
            try:
                score = float(data["cvss_score"])
                if not 0.0 <= score <= 10.0:
                    logger.warning(f"❌ 数据验证失败: CVSS分数超出范围 {score}")
                    return False
            except (ValueError, TypeError):
                logger.warning("❌ 数据验证失败: CVSS分数格式错误")
                return False

        if "severity" in data:
            valid_severities = ["Critical", "High", "Medium", "Low", "Unknown"]
            if data["severity"] not in valid_severities:
                logger.warning(f"⚠️ 数据验证警告: 未知严重级别 {data['severity']}")

        return True

    @staticmethod
    def sanitize_vulnerability_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理和标准化漏洞数据

        Args:
            data: 原始漏洞数据

        Returns:
            Dict: 清理后的数据
        """
        sanitized = {}

        for key, value in data.items():
            if value is None:
                continue

            if isinstance(value, str):
                sanitized[key] = value.strip()
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list):
                sanitized[key] = [item for item in value if item]
            elif isinstance(value, dict):
                sanitized[key] = DataValidator.sanitize_vulnerability_data(value)

        return sanitized


class CacheManager:
    """
    缓存管理器
    """

    def __init__(self, default_ttl: int = 3600):
        """
        初始化缓存管理器

        Args:
            default_ttl: 默认缓存时间（秒）
        """
        self.cache: Dict[str, tuple] = {}
        self.default_ttl = default_ttl
        self.cache_hits = 0
        self.cache_misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据

        Args:
            key: 缓存键

        Returns:
            Optional[Any]: 缓存的数据，如果不存在或已过期返回None
        """
        if key not in self.cache:
            self.cache_misses += 1
            return None

        data, timestamp, ttl = self.cache[key]

        if datetime.now() - timestamp > timedelta(seconds=ttl):
            del self.cache[key]
            self.cache_misses += 1
            return None

        self.cache_hits += 1
        return data

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存数据

        Args:
            key: 缓存键
            data: 要缓存的数据
            ttl: 缓存时间（秒），默认使用default_ttl
        """
        ttl = ttl or self.default_ttl
        self.cache[key] = (data, datetime.now(), ttl)

    def delete(self, key: str) -> bool:
        """
        删除缓存数据

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功删除
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        """
        清除所有缓存
        """
        self.cache.clear()
        logger.info("✅ 缓存已清除")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict: 缓存统计
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_entries": len(self.cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{hit_rate:.2f}%"
        }


class DataSource(ABC):
    """
    数据源抽象基类
    """

    def __init__(self, source_type: DataSourceType, enable_cache: bool = True):
        """
        初始化数据源

        Args:
            source_type: 数据源类型
            enable_cache: 是否启用缓存
        """
        self.source_type = source_type
        self.enable_cache = enable_cache
        self.cache_manager = CacheManager() if enable_cache else None
        self.validator = DataValidator()

    @abstractmethod
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """
        获取数据（抽象方法）

        Args:
            **kwargs: 查询参数

        Returns:
            List[Dict]: 原始数据列表
        """
        pass

    async def get_vulnerabilities(self, **kwargs) -> List[VulnerabilityData]:
        """
        获取标准化的漏洞数据

        Args:
            **kwargs: 查询参数

        Returns:
            List[VulnerabilityData]: 标准化的漏洞数据列表
        """
        cache_key = self._generate_cache_key(**kwargs)

        if self.enable_cache and self.cache_manager:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.info(f"✅ 使用缓存数据: {self.source_type.value}")
                return cached_data

        raw_data = await self.fetch_data(**kwargs)

        vulnerabilities = []
        for item in raw_data:
            if not self.validator.validate_vulnerability_data(item):
                continue

            sanitized_data = self.validator.sanitize_vulnerability_data(item)
            vuln_data = self._convert_to_vulnerability_data(sanitized_data)
            vulnerabilities.append(vuln_data)

        if self.enable_cache and self.cache_manager:
            self.cache_manager.set(cache_key, vulnerabilities, ttl=1800)

        logger.info(f"✅ 从 {self.source_type.value} 获取到 {len(vulnerabilities)} 条有效漏洞数据")
        return vulnerabilities

    @abstractmethod
    def _convert_to_vulnerability_data(self, raw_data: Dict[str, Any]) -> VulnerabilityData:
        """
        将原始数据转换为标准化的漏洞数据（抽象方法）

        Args:
            raw_data: 原始数据

        Returns:
            VulnerabilityData: 标准化的漏洞数据
        """
        pass

    def _generate_cache_key(self, **kwargs) -> str:
        """
        生成缓存键

        Args:
            **kwargs: 查询参数

        Returns:
            str: 缓存键
        """
        params = sorted(kwargs.items())
        params_str = "&".join([f"{k}={v}" for k, v in params])
        return f"{self.source_type.value}_{params_str}"

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict: 缓存统计
        """
        if self.cache_manager:
            return self.cache_manager.get_stats()
        return {"cache_enabled": False}


class SeebugDataSource(DataSource):
    """
    Seebug数据源实现
    """

    def __init__(self, enable_cache: bool = True):
        super().__init__(DataSourceType.SEEBUG, enable_cache)

    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """
        从Seebug获取数据

        Args:
            **kwargs: 查询参数

        Returns:
            List[Dict]: 原始数据列表
        """
        from backend.api.seebug_client import global_seebug_client

        keyword = kwargs.get("keyword", "")
        page = kwargs.get("page", 1)
        page_size = kwargs.get("page_size", 20)

        response = await global_seebug_client.search_poc(keyword, page, page_size)

        if response.success and response.data:
            return response.data.get("data", [])
        return []

    def _convert_to_vulnerability_data(self, raw_data: Dict[str, Any]) -> VulnerabilityData:
        """
        转换Seebug数据为标准格式

        Args:
            raw_data: Seebug原始数据

        Returns:
            VulnerabilityData: 标准化的漏洞数据
        """
        return VulnerabilityData(
            cve_id=raw_data.get("cve_id", ""),
            name=raw_data.get("name", raw_data.get("title", "Unknown")),
            description=raw_data.get("description", raw_data.get("summary", "")),
            severity=raw_data.get("level", raw_data.get("severity", "Unknown")),
            cvss_score=float(raw_data.get("cvss_score", 0.0)),
            affected_product=raw_data.get("product", raw_data.get("affected", "")),
            solution=raw_data.get("solution", raw_data.get("patch", "")),
            has_poc=True,
            source="seebug",
            ssvid=raw_data.get("ssvid"),
            created_at=raw_data.get("created_at"),
            updated_at=raw_data.get("updated_at")
        )


class ExploitDBDataSource(DataSource):
    """
    Exploit-DB数据源实现
    """

    def __init__(self, enable_cache: bool = True):
        super().__init__(DataSourceType.EXPLOIT_DB, enable_cache)

    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """
        从Exploit-DB获取数据

        Args:
            **kwargs: 查询参数

        Returns:
            List[Dict]: 原始数据列表
        """
        from backend.api.kb import fetch_exploit_db_data

        return await fetch_exploit_db_data()

    def _convert_to_vulnerability_data(self, raw_data: Dict[str, Any]) -> VulnerabilityData:
        """
        转换Exploit-DB数据为标准格式

        Args:
            raw_data: Exploit-DB原始数据

        Returns:
            VulnerabilityData: 标准化的漏洞数据
        """
        return VulnerabilityData(
            cve_id=raw_data.get("cve_id", ""),
            name=raw_data.get("name", raw_data.get("title", "Unknown")),
            description=raw_data.get("description", raw_data.get("summary", "")),
            severity=raw_data.get("severity", "Unknown"),
            cvss_score=float(raw_data.get("cvss_score", 0.0)),
            affected_product=raw_data.get("product", raw_data.get("affected", "")),
            solution=raw_data.get("solution", raw_data.get("patch", "")),
            has_poc=True,
            source="exploit_db",
            poc_code=raw_data.get("exploit", ""),
            created_at=raw_data.get("created_at"),
            updated_at=raw_data.get("updated_at")
        )


class DataSourceManager:
    """
    数据源管理器
    """

    def __init__(self):
        """
        初始化数据源管理器
        """
        self.data_sources: Dict[DataSourceType, DataSource] = {}
        self._initialize_data_sources()

    def _initialize_data_sources(self):
        """
        初始化所有数据源
        """
        self.data_sources[DataSourceType.SEEBUG] = SeebugDataSource(enable_cache=True)
        self.data_sources[DataSourceType.EXPLOIT_DB] = ExploitDBDataSource(enable_cache=True)
        logger.info("✅ 数据源管理器初始化完成")

    async def get_vulnerabilities(
        self,
        source_type: DataSourceType,
        **kwargs
    ) -> List[VulnerabilityData]:
        """
        从指定数据源获取漏洞数据

        Args:
            source_type: 数据源类型
            **kwargs: 查询参数

        Returns:
            List[VulnerabilityData]: 漏洞数据列表
        """
        if source_type not in self.data_sources:
            logger.error(f"❌ 未知的数据源类型: {source_type}")
            return []

        data_source = self.data_sources[source_type]
        return await data_source.get_vulnerabilities(**kwargs)

    async def get_all_vulnerabilities(self, **kwargs) -> List[VulnerabilityData]:
        """
        从所有数据源获取漏洞数据

        Args:
            **kwargs: 查询参数

        Returns:
            List[VulnerabilityData]: 合并后的漏洞数据列表
        """
        all_vulnerabilities = []

        for source_type, data_source in self.data_sources.items():
            try:
                vulnerabilities = await data_source.get_vulnerabilities(**kwargs)
                all_vulnerabilities.extend(vulnerabilities)
            except Exception as e:
                logger.error(f"❌ 从 {source_type.value} 获取数据失败: {e}")

        logger.info(f"✅ 从所有数据源共获取到 {len(all_vulnerabilities)} 条漏洞数据")
        return all_vulnerabilities

    def clear_all_caches(self):
        """
        清除所有数据源的缓存
        """
        for data_source in self.data_sources.values():
            if data_source.cache_manager:
                data_source.cache_manager.clear()

        logger.info("✅ 所有数据源缓存已清除")

    def get_all_cache_stats(self) -> Dict[str, Any]:
        """
        获取所有数据源的缓存统计信息

        Returns:
            Dict: 缓存统计信息
        """
        stats = {}
        for source_type, data_source in self.data_sources.items():
            stats[source_type.value] = data_source.get_cache_stats()
        return stats


global_data_source_manager = DataSourceManager()

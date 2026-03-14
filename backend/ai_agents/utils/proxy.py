# -*- coding:utf-8 -*-
"""
代理管理器

功能：
1. 支持HTTP/SOCKS代理
2. 支持代理池轮换
3. 支持Burp Suite联动
4. 代理健康检查
"""

import logging
import random
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class ProxyType(Enum):
    """代理类型枚举"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"
    SOCKS4 = "socks4"


@dataclass
class ProxyInfo:
    """代理信息"""
    host: str
    port: int
    proxy_type: ProxyType = ProxyType.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    enabled: bool = True
    last_used: float = 0.0
    fail_count: int = 0
    success_count: int = 0
    
    @property
    def url(self) -> str:
        """获取代理URL"""
        if self.username and self.password:
            return f"{self.proxy_type.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type.value}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.fail_count + self.success_count
        if total == 0:
            return 1.0
        return self.success_count / total


DEFAULT_PROXY_CONFIG = {
    "enabled": False,
    "type": "http",
    "host": "127.0.0.1",
    "port": 8080,
    "username": None,
    "password": None,
    "rotate": False,
    "max_fails": 3,
    "check_url": "http://httpbin.org/ip",
    "timeout": 10,
}


class ProxyManager:
    """
    代理管理器
    
    功能：
    1. 支持HTTP/SOCKS代理
    2. 支持代理池轮换
    3. 支持Burp Suite联动
    4. 代理健康检查
    """
    
    def __init__(self, config: Dict = None):
        self.config = {**DEFAULT_PROXY_CONFIG, **(config or {})}
        self.proxies: List[ProxyInfo] = []
        self.current_index = 0
        self._enabled = self.config.get("enabled", False)
        
        if self._enabled and self.config.get("host"):
            self.add_proxy(
                host=self.config["host"],
                port=self.config["port"],
                proxy_type=ProxyType(self.config.get("type", "http")),
                username=self.config.get("username"),
                password=self.config.get("password")
            )
        
        logger.info(f"代理管理器初始化: enabled={self._enabled}, proxies={len(self.proxies)}")
    
    @property
    def enabled(self) -> bool:
        """是否启用代理"""
        return self._enabled and len(self.proxies) > 0
    
    @enabled.setter
    def enabled(self, value: bool):
        """设置是否启用代理"""
        self._enabled = value
    
    def add_proxy(
        self,
        host: str,
        port: int,
        proxy_type: ProxyType = ProxyType.HTTP,
        username: str = None,
        password: str = None
    ) -> None:
        """添加代理"""
        proxy = ProxyInfo(
            host=host,
            port=port,
            proxy_type=proxy_type,
            username=username,
            password=password
        )
        self.proxies.append(proxy)
        logger.info(f"添加代理: {host}:{port} ({proxy_type.value})")
    
    def add_proxies_from_list(self, proxy_list: List[str]) -> None:
        """
        从列表批量添加代理
        
        Args:
            proxy_list: 代理列表，格式如 ["http://1.2.3.4:8080", "socks5://user:pass@5.6.7.8:1080"]
        """
        for proxy_str in proxy_list:
            try:
                parsed = urlparse(proxy_str)
                proxy_type = ProxyType(parsed.scheme or "http")
                self.add_proxy(
                    host=parsed.hostname,
                    port=parsed.port or 8080,
                    proxy_type=proxy_type,
                    username=parsed.username,
                    password=parsed.password
                )
            except Exception as e:
                logger.warning(f"解析代理失败: {proxy_str}, 错误: {e}")
    
    def get_proxy(self) -> Optional[str]:
        """
        获取当前代理
        
        Returns:
            Optional[str]: 代理URL或None
        """
        if not self.enabled or not self.proxies:
            return None
        
        if self.config.get("rotate"):
            return self._get_next_proxy()
        
        return self.proxies[0].url
    
    def _get_next_proxy(self) -> Optional[str]:
        """获取下一个代理（轮换模式）"""
        if not self.proxies:
            return None
        
        valid_proxies = [p for p in self.proxies if p.enabled and p.fail_count < self.config.get("max_fails", 3)]
        
        if not valid_proxies:
            logger.warning("没有可用的代理")
            return None
        
        valid_proxies.sort(key=lambda p: p.success_rate, reverse=True)
        
        self.current_index = (self.current_index + 1) % len(valid_proxies)
        proxy = valid_proxies[self.current_index]
        proxy.last_used = time.time()
        
        return proxy.url
    
    def rotate(self) -> Optional[str]:
        """轮换代理"""
        return self._get_next_proxy()
    
    def set_burp(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        """
        设置Burp Suite代理
        
        Args:
            host: Burp监听地址
            port: Burp监听端口
        """
        self.proxies.clear()
        self.add_proxy(host=host, port=port, proxy_type=ProxyType.HTTP)
        self._enabled = True
        logger.info(f"设置Burp代理: {host}:{port}")
    
    def remove_proxy(self, host: str, port: int) -> bool:
        """移除代理"""
        for i, proxy in enumerate(self.proxies):
            if proxy.host == host and proxy.port == port:
                self.proxies.pop(i)
                logger.info(f"移除代理: {host}:{port}")
                return True
        return False
    
    def mark_success(self, proxy_url: str) -> None:
        """标记代理使用成功"""
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                proxy.success_count += 1
                break
    
    def mark_failure(self, proxy_url: str) -> None:
        """标记代理使用失败"""
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                proxy.fail_count += 1
                if proxy.fail_count >= self.config.get("max_fails", 3):
                    proxy.enabled = False
                    logger.warning(f"代理 {proxy.host}:{proxy.port} 已禁用（失败次数过多）")
                break
    
    async def check_proxy_health(self, proxy: ProxyInfo) -> bool:
        """
        检查代理健康状态
        
        Args:
            proxy: 代理信息
            
        Returns:
            bool: 是否健康
        """
        try:
            async with httpx.AsyncClient(
                proxy=proxy.url,
                timeout=self.config.get("timeout", 10),
                verify=False
            ) as client:
                response = await client.get(self.config.get("check_url", "http://httpbin.org/ip"))
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"代理健康检查失败: {proxy.host}:{proxy.port}, 错误: {e}")
            return False
    
    async def check_all_proxies(self) -> Dict[str, bool]:
        """检查所有代理健康状态"""
        results = {}
        
        for proxy in self.proxies:
            is_healthy = await self.check_proxy_health(proxy)
            results[proxy.url] = is_healthy
            
            if is_healthy:
                proxy.enabled = True
                proxy.fail_count = 0
            else:
                proxy.fail_count += 1
                if proxy.fail_count >= self.config.get("max_fails", 3):
                    proxy.enabled = False
        
        return results
    
    def get_httpx_proxies(self) -> Dict[str, str]:
        """
        获取httpx格式的代理配置
        
        Returns:
            Dict[str, str]: {"http://": proxy_url, "https://": proxy_url}
        """
        proxy_url = self.get_proxy()
        if proxy_url:
            return {
                "http://": proxy_url,
                "https://": proxy_url
            }
        return {}
    
    def get_requests_proxies(self) -> Dict[str, str]:
        """
        获取requests格式的代理配置
        
        Returns:
            Dict[str, str]: {"http": proxy_url, "https": proxy_url}
        """
        proxy_url = self.get_proxy()
        if proxy_url:
            return {
                "http": proxy_url,
                "https": proxy_url
            }
        return {}
    
    def get_stats(self) -> Dict:
        """获取代理统计信息"""
        return {
            "enabled": self._enabled,
            "total_proxies": len(self.proxies),
            "active_proxies": sum(1 for p in self.proxies if p.enabled),
            "proxies": [
                {
                    "host": p.host,
                    "port": p.port,
                    "type": p.proxy_type.value,
                    "enabled": p.enabled,
                    "success_count": p.success_count,
                    "fail_count": p.fail_count,
                    "success_rate": f"{p.success_rate:.2%}"
                }
                for p in self.proxies
            ]
        }
    
    def clear(self) -> None:
        """清空所有代理"""
        self.proxies.clear()
        self.current_index = 0
        logger.info("已清空所有代理")


proxy_manager = ProxyManager()


def get_proxy_manager() -> ProxyManager:
    """获取全局代理管理器实例"""
    return proxy_manager

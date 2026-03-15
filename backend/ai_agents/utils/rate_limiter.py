# -*- coding:utf-8 -*-
"""
智能限速器

功能：
1. 基于QPS限速
2. 基于响应时间自适应
3. WAF触发后降速
4. 错误率过高降速
"""

import asyncio
import logging
import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """限速策略枚举"""
    FIXED = "fixed"
    ADAPTIVE = "adaptive"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
    """限速配置"""
    qps: int = 10
    min_delay: float = 0.1
    max_delay: float = 5.0
    initial_delay: float = 0.1
    adaptive_enabled: bool = True
    waf_delay_multiplier: float = 5.0
    error_delay_multiplier: float = 2.0
    success_delay_decrease: float = 0.9
    max_consecutive_errors: int = 5
    window_size: int = 100


@dataclass
class RequestStats:
    """请求统计"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    waf_detected: int = 0
    total_response_time: float = 0.0
    recent_requests: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_errors: deque = field(default_factory=lambda: deque(maxlen=20))
    
    @property
    def avg_response_time(self) -> float:
        if not self.recent_requests:
            return 0.0
        return sum(r for r in self.recent_requests if isinstance(r, float)) / len(self.recent_requests)
    
    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests


class RateLimiter:
    """
    智能限速器
    
    功能：
    1. 基于QPS限速
    2. 基于响应时间自适应
    3. WAF触发后降速
    4. 错误率过高降速
    """
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.current_delay = self.config.initial_delay
        self.stats = RequestStats()
        
        self._last_request_time = 0.0
        self._consecutive_errors = 0
        self._waf_detected = False
        self._lock = asyncio.Lock()
        
        self._tokens = self.config.qps
        self._last_refill = time.time()
        self._refill_rate = self.config.qps
        
        logger.info(f"限速器初始化: qps={self.config.qps}, delay={self.current_delay}s")
    
    async def acquire(self) -> None:
        """
        获取请求许可
        
        会阻塞直到可以发送下一个请求
        """
        async with self._lock:
            now = time.time()
            
            if self.config.adaptive_enabled:
                self._refill_tokens()
                
                while self._tokens < 1:
                    sleep_time = 1.0 / self._refill_rate
                    await asyncio.sleep(sleep_time)
                    self._refill_tokens()
            
            time_since_last = now - self._last_request_time
            if time_since_last < self.current_delay:
                sleep_time = self.current_delay - time_since_last
                await asyncio.sleep(sleep_time)
            
            self._tokens -= 1
            self._last_request_time = time.time()
    
    def _refill_tokens(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self._last_refill
        
        tokens_to_add = elapsed * self._refill_rate
        self._tokens = min(self.config.qps, self._tokens + tokens_to_add)
        self._last_refill = now
    
    def on_success(self, response_time: float) -> None:
        """
        成功回调
        
        Args:
            response_time: 响应时间（秒）
        """
        self.stats.total_requests += 1
        self.stats.successful_requests += 1
        self.stats.total_response_time += response_time
        self.stats.recent_requests.append(response_time)
        
        self._consecutive_errors = 0
        
        if self._waf_detected:
            self._waf_detected = False
            logger.info("WAF状态清除，恢复正常速度")
        
        if self.config.adaptive_enabled:
            self._adjust_delay_success(response_time)
    
    def on_error(self, error_type: str = "unknown") -> None:
        """
        错误回调
        
        Args:
            error_type: 错误类型
        """
        self.stats.total_requests += 1
        self.stats.failed_requests += 1
        self.stats.recent_errors.append({
            "time": time.time(),
            "type": error_type
        })
        
        self._consecutive_errors += 1
        
        if self.config.adaptive_enabled:
            if self._consecutive_errors >= self.config.max_consecutive_errors:
                self._increase_delay("连续错误")
            else:
                self._increase_delay(f"错误: {error_type}")
    
    def on_waf_detected(self) -> None:
        """WAF检测回调，大幅降速"""
        self.stats.waf_detected += 1
        self._waf_detected = True
        
        new_delay = self.current_delay * self.config.waf_delay_multiplier
        new_delay = min(new_delay, self.config.max_delay)
        
        logger.warning(f"检测到WAF，降速: {self.current_delay:.2f}s -> {new_delay:.2f}s")
        self.current_delay = new_delay
        
        self._refill_rate = max(1, self._refill_rate // 2)
    
    def on_rate_limit(self, retry_after: int = None) -> None:
        """
        速率限制回调
        
        Args:
            retry_after: 服务器建议的重试等待时间
        """
        if retry_after:
            self.current_delay = max(self.current_delay, retry_after)
        else:
            self._increase_delay("速率限制")
    
    def _adjust_delay_success(self, response_time: float) -> None:
        """成功时调整延迟"""
        avg_time = self.stats.avg_response_time
        
        if response_time > avg_time * 1.5:
            new_delay = min(self.current_delay * 1.1, self.config.max_delay)
            if new_delay > self.current_delay:
                logger.debug(f"响应时间较长，略微降速: {self.current_delay:.2f}s -> {new_delay:.2f}s")
                self.current_delay = new_delay
        else:
            new_delay = max(
                self.current_delay * self.config.success_delay_decrease,
                self.config.min_delay
            )
            if new_delay < self.current_delay:
                self.current_delay = new_delay
    
    def _increase_delay(self, reason: str) -> None:
        """增加延迟"""
        new_delay = min(
            self.current_delay * self.config.error_delay_multiplier,
            self.config.max_delay
        )
        
        logger.info(f"限速调整 ({reason}): {self.current_delay:.2f}s -> {new_delay:.2f}s")
        self.current_delay = new_delay
    
    def reset(self) -> None:
        """重置限速器"""
        self.current_delay = self.config.initial_delay
        self._consecutive_errors = 0
        self._waf_detected = False
        self._tokens = self.config.qps
        self._refill_rate = self.config.qps
        logger.info("限速器已重置")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "current_delay": round(self.current_delay, 3),
            "qps_limit": self.config.qps,
            "current_qps": round(self._refill_rate, 2),
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "error_rate": f"{self.stats.error_rate:.2%}",
            "avg_response_time": f"{self.stats.avg_response_time:.3f}s",
            "waf_detected_count": self.stats.waf_detected,
            "consecutive_errors": self._consecutive_errors,
            "waf_active": self._waf_detected
        }
    
    def set_qps(self, qps: int) -> None:
        """设置QPS"""
        self.config.qps = qps
        self._refill_rate = qps
        logger.info(f"QPS已设置为: {qps}")
    
    def set_delay(self, delay: float) -> None:
        """设置固定延迟"""
        self.current_delay = max(self.config.min_delay, min(delay, self.config.max_delay))
        logger.info(f"延迟已设置为: {self.current_delay:.2f}s")


class AdaptiveRateLimiter(RateLimiter):
    """
    自适应限速器
    
    根据服务器响应自动调整请求速率
    """
    
    def __init__(self, config: RateLimitConfig = None):
        super().__init__(config)
        
        self._response_times = deque(maxlen=20)
        self._target_response_time = 1.0
    
    def on_success(self, response_time: float) -> None:
        """成功回调"""
        super().on_success(response_time)
        self._response_times.append(response_time)
        self._adaptive_adjust()
    
    def _adaptive_adjust(self) -> None:
        """自适应调整"""
        if len(self._response_times) < 5:
            return
        
        avg_response = sum(self._response_times) / len(self._response_times)
        
        if avg_response > self._target_response_time * 1.5:
            self.current_delay = min(
                self.current_delay * 1.2,
                self.config.max_delay
            )
            self._refill_rate = max(1, int(self._refill_rate * 0.8))
            
        elif avg_response < self._target_response_time * 0.5:
            self.current_delay = max(
                self.current_delay * 0.9,
                self.config.min_delay
            )
            self._refill_rate = min(self.config.qps, int(self._refill_rate * 1.1))


rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """获取全局限速器实例"""
    return rate_limiter

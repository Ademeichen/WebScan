"""
API 日志中间件

提供统一的API请求日志记录功能，包括：
- 请求时间戳
- API端点路径
- 请求方法
- 请求参数
- 处理状态
- 错误信息
- 响应耗时

日志格式统一规范，便于开发者在开发和调试过程中快速定位问题。
"""
import time
import json
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime
import uuid

logger = logging.getLogger("api_logger")

class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    API 请求日志中间件
    
    记录所有API请求的详细信息，包括：
    - 请求ID（用于追踪）
    - 请求时间戳
    - API端点路径
    - 请求方法
    - 请求参数（Query、Path、Body）
    - 处理状态
    - 错误信息（如有）
    - 响应耗时
    """
    
    def __init__(self, app: ASGIApp, log_level: str = "INFO"):
        super().__init__(app)
        self.log_level = log_level
        self.sensitive_headers = {"authorization", "cookie", "set-cookie"}
        self.sensitive_body_fields = {"password", "token", "secret", "api_key", "apikey"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        request_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        request_info = {
            "request_id": request_id,
            "timestamp": request_timestamp,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params) if request.query_params else {},
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "Unknown"),
        }
        
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    body = await request.body()
                    if body:
                        try:
                            body_json = json.loads(body)
                            request_info["body"] = self._mask_sensitive_data(body_json)
                        except json.JSONDecodeError:
                            request_info["body"] = "[Non-JSON body]"
                elif "multipart/form-data" in content_type:
                    request_info["body"] = "[Multipart form data]"
                else:
                    request_info["body"] = "[Body content not logged]"
            except Exception as e:
                request_info["body"] = f"[Error reading body: {str(e)}]"
        
        logger.info(
            f"[{request_id}] API请求开始 | {request_info['method']} {request_info['path']} | "
            f"客户端: {request_info['client_ip']} | 参数: {json.dumps(request_info.get('query_params', {}), ensure_ascii=False)}"
        )
        
        if request_info.get("body"):
            logger.debug(
                f"[{request_id}] 请求体: {json.dumps(request_info.get('body', {}), ensure_ascii=False)}"
            )
        
        response = None
        error_info = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)
            
            log_level = logging.INFO
            if status_code >= 500:
                log_level = logging.ERROR
            elif status_code >= 400:
                log_level = logging.WARNING
            
            logger.log(
                log_level,
                f"[{request_id}] API请求完成 | {request_info['method']} {request_info['path']} | "
                f"状态码: {status_code} | 耗时: {process_time_ms}ms"
            )
            
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time_ms}ms"
            
            return response
            
        except Exception as e:
            error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)
            
            logger.error(
                f"[{request_id}] API请求异常 | {request_info['method']} {request_info['path']} | "
                f"异常: {error_info['error_type']} - {error_info['error_message']} | 耗时: {process_time_ms}ms",
                exc_info=True
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP地址"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "Unknown"
    
    def _mask_sensitive_data(self, data: dict) -> dict:
        """遮蔽敏感数据"""
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        for key, value in data.items():
            lower_key = key.lower()
            if any(sensitive in lower_key for sensitive in self.sensitive_body_fields):
                masked_data[key] = "******"
            elif isinstance(value, dict):
                masked_data[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    self._mask_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        
        return masked_data


def setup_api_logging(app, log_level: str = "INFO"):
    """
    配置API日志中间件
    
    Args:
        app: FastAPI应用实例
        log_level: 日志级别，默认为INFO
    """
    app.add_middleware(APILoggingMiddleware, log_level=log_level)
    logger.info(f"API日志中间件已启用，日志级别: {log_level}")


class APILogger:
    """
    API日志工具类
    
    提供在业务逻辑中记录详细日志的便捷方法。
    """
    
    @staticmethod
    def log_request_start(request_id: str, endpoint: str, method: str, params: dict = None):
        """记录请求开始"""
        logger.info(
            f"[{request_id}] 请求开始 | {method} {endpoint} | "
            f"参数: {json.dumps(params or {}, ensure_ascii=False)}"
        )
    
    @staticmethod
    def log_request_end(request_id: str, endpoint: str, status: str, duration_ms: float):
        """记录请求结束"""
        logger.info(
            f"[{request_id}] 请求结束 | {endpoint} | 状态: {status} | 耗时: {duration_ms}ms"
        )
    
    @staticmethod
    def log_business_logic(request_id: str, step: str, details: dict = None):
        """记录业务逻辑处理步骤"""
        logger.info(
            f"[{request_id}] 业务处理 | {step} | "
            f"详情: {json.dumps(details or {}, ensure_ascii=False)}"
        )
    
    @staticmethod
    def log_validation(request_id: str, field: str, value: any, is_valid: bool, message: str = None):
        """记录参数验证"""
        status = "通过" if is_valid else "失败"
        logger.debug(
            f"[{request_id}] 参数验证 | 字段: {field} | 值: {value} | "
            f"状态: {status}" + (f" | 消息: {message}" if message else "")
        )
    
    @staticmethod
    def log_db_operation(request_id: str, operation: str, table: str, details: dict = None):
        """记录数据库操作"""
        logger.debug(
            f"[{request_id}] 数据库操作 | {operation} | 表: {table} | "
            f"详情: {json.dumps(details or {}, ensure_ascii=False)}"
        )
    
    @staticmethod
    def log_external_call(request_id: str, service: str, endpoint: str, status: str, duration_ms: float = None):
        """记录外部服务调用"""
        duration_str = f" | 耗时: {duration_ms}ms" if duration_ms else ""
        logger.info(
            f"[{request_id}] 外部调用 | 服务: {service} | 端点: {endpoint} | "
            f"状态: {status}{duration_str}"
        )
    
    @staticmethod
    def log_error(request_id: str, error_type: str, error_message: str, stack_trace: str = None):
        """记录错误信息"""
        logger.error(
            f"[{request_id}] 错误 | 类型: {error_type} | 消息: {error_message}",
            exc_info=True if stack_trace else False
        )
    
    @staticmethod
    def log_warning(request_id: str, message: str, details: dict = None):
        """记录警告信息"""
        logger.warning(
            f"[{request_id}] 警告 | {message} | "
            f"详情: {json.dumps(details or {}, ensure_ascii=False)}"
        )


api_logger = APILogger()

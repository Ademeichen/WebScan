"""
POC 工具函数

提供 POC 相关的公共工具函数，包括输出解析、验证规则等
"""
from typing import Dict, List, Any


def parse_pocsuite_output(output: str) -> bool:
    """
    解析 Pocsuite3 输出,判断是否存在漏洞
    
    Args:
        output: Pocsuite3 的输出内容
        
    Returns:
        bool: 是否存在漏洞
    """
    success_keywords = [
        "success",
        "vulnerable",
        "vuln",
        "exploit",
        "exists",
        "[+]"
    ]
    
    output_lower = output.lower()
    
    for keyword in success_keywords:
        if keyword in output_lower:
            return True
    
    return False


def get_poc_validation_rules() -> List[tuple]:
    """
    获取 POC 验证规则列表
    
    Returns:
        List[tuple]: 验证规则列表，每个规则为(模式, 错误消息)元组
    """
    return [
        ("class POC", "缺少POC类定义"),
        ("from pocsuite3", "缺少pocsuite3导入"),
        ("def _verify", "缺少_verify方法"),
        ("app", "缺少app属性"),
        ("vulID", "缺少vulID属性"),
        ("version", "缺少version属性"),
        ("author", "缺少author属性"),
        ("references", "缺少references属性"),
        ("name", "缺少name属性"),
        ("severity", "缺少severity属性"),
        ("appPowerLink", "缺少appPowerLink属性"),
        ("vulDate", "缺少vulDate属性"),
        ("appVersion", "缺少appVersion属性"),
        ("desc", "缺少desc属性"),
        ("samples", "缺少samples属性"),
    ]


def validate_poc_script_code(poc_code: str) -> Dict[str, Any]:
    """
    验证POC脚本是否符合pocsuite3标准格式
    
    Args:
        poc_code: POC脚本代码
        
    Returns:
        Dict[str, Any]: 验证结果，包含is_valid和错误信息
    """
    validation_rules = get_poc_validation_rules()
    
    errors = []
    for pattern, error_msg in validation_rules:
        if pattern not in poc_code:
            errors.append(error_msg)
    
    is_valid = len(errors) == 0
    
    return {
        "is_valid": is_valid,
        "errors": errors
    }


def get_false_positive_keywords() -> List[str]:
    """
    获取误报检测关键词列表
    
    Returns:
        List[str]: 误报关键词列表
    """
    return [
        "timeout",
        "connection refused",
        "connection reset",
        "network unreachable",
        "dns resolution failed",
        "certificate error",
        "ssl error",
        "handshake failed",
        "404 not found",
        "403 forbidden",
        "401 unauthorized",
        "rate limit",
        "too many requests",
        "service unavailable",
        "gateway timeout",
        "bad gateway"
    ]


def get_success_keywords() -> List[str]:
    """
    获取成功验证关键词列表
    
    Returns:
        List[str]: 成功关键词列表
    """
    return [
        "success",
        "vulnerable",
        "exploit",
        "vuln",
        "shell",
        "code execution",
        "sql injection",
        "xss",
        "rce",
        "arbitrary file",
        "path traversal",
        "ssrf",
        "xxe",
        "deserialization"
    ]

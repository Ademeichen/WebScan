# -*- coding:utf-8 -*-
"""
Web爬虫配置
"""

CRAWLER_CONFIG = {
    "max_depth": 3,
    "max_pages": 500,
    "max_concurrent": 10,
    "timeout": 10,
    "delay": 0.5,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "follow_redirects": True,
    "max_redirects": 5,
    "verify_ssl": False,
    "exclude_extensions": [
        ".pdf", ".zip", ".rar", ".7z", ".tar", ".gz",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg", ".webp",
        ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".wav",
        ".css", ".woff", ".woff2", ".ttf", ".eot", ".otf",
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".exe", ".dll", ".so", ".dmg", ".iso"
    ],
    "exclude_patterns": [
        "logout", "signout", "exit", "logoff",
        "delete", "remove", "unlink", "destroy"
    ],
    "respect_robots": True,
    "extract_comments": True,
    "extract_scripts": True,
    "extract_forms": True,
    "extract_inputs": True,
}

DEFAULT_HEADERS = {
    "User-Agent": CRAWLER_CONFIG["user_agent"],
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
}

SENSITIVE_PATTERNS = [
    r"password\s*[=:]\s*['\"]?([^'\"\s]+)",
    r"api[_-]?key\s*[=:]\s*['\"]?([^'\"\s]+)",
    r"secret\s*[=:]\s*['\"]?([^'\"\s]+)",
    r"token\s*[=:]\s*['\"]?([^'\"\s]+)",
    r"auth[_-]?key\s*[=:]\s*['\"]?([^'\"\s]+)",
    r"private[_-]?key\s*[=:]\s*['\"]?([^'\"\s]+)",
]

LOGIN_PATHS = [
    "/login", "/signin", "/sign-in", "/admin/login",
    "/user/login", "/auth", "/account/login", "/portal",
    "/administrator", "/admin", "/wp-login.php", "/user",
]

UPLOAD_PATHS = [
    "/upload", "/uploads", "/files", "/attachments",
    "/api/upload", "/api/files", "/uploadfile",
]

"""
完整的测试配置文件
包含所有API模块的边界条件、异常场景和性能测试数据
"""

# ============ 基础配置 ============
API_BASE_URL = "http://127.0.0.1:3000/api"
API_TIMEOUT = 30
MAX_ITERATIONS = 10

# ============ 正常测试数据 ============
NORMAL_TEST_DATA = {
    "notification": {
        "title": "测试通知",
        "message": "这是一条测试通知",
        "type": "system"
    },
    "user": {
        "username": "test_user",
        "email": "test@example.com",
        "role": "admin"
    },
    "task": {
        "task_name": "测试扫描任务",
        "target": "http://127.0.0.1:8080",
        "task_type": "poc_scan",
        "config": {
            "poc_types": ["weblogic", "struts2"]
        }
    },
    "awvs_scan": {
        "task_name": "测试AWVS扫描",
        "target": "http://127.0.0.1:8080",
        "task_type": "awvs_scan",
        "config": {
            "profile_id": "11111111-1111-1111-1111-111111111111"
        }
    },
    "report": {
        "task_id": 1,
        "format": "html",
        "content": ["summary", "vulnerabilities"],
        "name": "测试报告"
    },
    "settings": {
        "general": {
            "systemName": "WebScan AI",
            "language": "zh-CN",
            "timezone": "Asia/Shanghai"
        }
    }
}

# ============ 边界条件测试数据 ============
BOUNDARY_TEST_DATA = {
    "empty_values": {
        "title": "",
        "message": "",
        "type": "",
        "username": "",
        "email": "",
        "task_name": "",
        "target": "",
        "task_type": ""
    },
    "null_values": {
        "title": None,
        "message": None,
        "type": None,
        "config": None,
        "task_id": None
    },
    "special_characters": {
        "xss_title": "<script>alert('XSS')</script>",
        "sql_message": "1' OR '1'='1",
        "path_traversal": "../../../etc/passwd",
        "unicode_title": "测试通知🔥",
        "emoji_title": "Test notification 🎉"
    },
    "length_boundaries": {
        "very_long_title": "a" * 1000,
        "max_length_title": "a" * 255,
        "min_length_title": "a",
        "very_long_message": "a" * 5000,
        "very_long_email": "a" * 1000 + "@example.com"
    },
    "numeric_boundaries": {
        "zero_id": 0,
        "negative_id": -1,
        "very_large_id": 999999999,
        "zero_port": 0,
        "negative_port": -1,
        "very_large_port": 65535
    },
    "invalid_types": {
        "invalid_notification_type": "invalid_type",
        "invalid_user_role": "invalid_role",
        "invalid_task_type": "invalid_type",
        "invalid_report_format": "invalid_format"
    },
    "date_boundaries": {
        "invalid_date": "2024-13-32",
        "future_date": "2099-12-31",
        "epoch_date": 0,
        "negative_timestamp": -1
    }
}

# ============ 异常场景测试数据 ============
EXCEPTION_TEST_DATA = {
    "network_errors": {
        "invalid_url": "http://nonexistent-domain-12345.com",
        "timeout_target": "http://10.0.0.1:9999",
        "connection_refused": "http://127.0.0.1:9999"
    },
    "invalid_ids": {
        "nonexistent_notification_id": 999999,
        "nonexistent_task_id": 999999,
        "nonexistent_user_id": 999999,
        "nonexistent_report_id": 999999
    },
    "permission_errors": {
        "unauthorized_access": "尝试访问未授权资源",
        "forbidden_access": "尝试访问禁止资源",
        "rate_limit_exceeded": "超过API速率限制"
    },
    "data_errors": {
        "malformed_json": "无效的JSON格式",
        "missing_required_fields": "缺少必需字段",
        "invalid_data_types": "无效的数据类型",
        "duplicate_data": "重复的数据"
    },
    "server_errors": {
        "internal_server_error": "服务器内部错误",
        "service_unavailable": "服务暂时不可用",
        "database_error": "数据库连接错误"
    }
}

# ============ 性能测试数据 ============
PERFORMANCE_TEST_DATA = {
    "high_load": {
        "description": "高负载测试",
        "concurrent_requests": 100,
        "test_duration": 60
    },
    "stress_test": {
        "description": "压力测试",
        "concurrent_requests": 500,
        "test_duration": 120
    },
    "response_time_thresholds": {
        "fast": 0.1,
        "normal": 0.5,
        "slow": 1.0,
        "very_slow": 3.0,
        "timeout": 5.0
    }
}

# ============ 安全测试数据 ============
SECURITY_TEST_DATA = {
    "injection_attacks": {
        "sql_injection": "1' OR '1'='1",
        "xss_attack": "<script>alert('XSS')</script>",
        "command_injection": "; rm -rf /",
        "path_traversal": "../../../etc/passwd"
    },
    "authentication_bypass": {
        "weak_password": "password123",
        "default_credentials": "admin:admin",
        "session_hijacking": "尝试会话劫持"
    },
    "data_exposure": {
        "sensitive_data": "包含敏感信息",
        "debug_info": "包含调试信息",
        "stack_trace": "包含堆栈跟踪"
    }
}

# ============ 测试场景定义 ============
TEST_SCENARIOS = {
    "happy_path": {
        "description": "验证API在正常情况下的功能",
        "test_types": ["normal", "boundary"]
    },
    "error_handling": {
        "description": "验证API对错误情况的处理",
        "test_types": ["exception"]
    },
    "performance": {
        "description": "验证API的性能表现",
        "test_types": ["performance"]
    },
    "security": {
        "description": "验证API的安全性",
        "test_types": ["security"]
    },
    "integration": {
        "description": "验证API与其他模块的集成",
        "test_types": ["normal"]
    }
}

# ============ 测试用例模板 ============
TEST_CASE_TEMPLATES = {
    "notification_tests": {
        "create_notification": {
            "name": "创建通知",
            "endpoint": "/notifications/",
            "method": "POST",
            "test_data": ["normal", "boundary", "exception"]
        },
        "get_notifications": {
            "name": "获取通知列表",
            "endpoint": "/notifications/",
            "method": "GET",
            "test_data": ["normal", "boundary"]
        },
        "mark_as_read": {
            "name": "标记通知为已读",
            "endpoint": "/notifications/{id}/read",
            "method": "PUT",
            "test_data": ["normal", "boundary"]
        },
        "delete_notification": {
            "name": "删除通知",
            "endpoint": "/notifications/{id}",
            "method": "DELETE",
            "test_data": ["normal", "boundary"]
        },
        "get_unread_count": {
            "name": "获取未读通知数量",
            "endpoint": "/notifications/count/unread",
            "method": "GET",
            "test_data": ["normal"]
        },
        "delete_read_notifications": {
            "name": "删除所有已读通知",
            "endpoint": "/notifications/",
            "method": "DELETE",
            "test_data": ["normal"]
        }
    },
    "user_tests": {
        "get_profile": {
            "name": "获取用户资料",
            "endpoint": "/user/profile",
            "method": "GET",
            "test_data": ["normal"]
        },
        "update_profile": {
            "name": "更新用户资料",
            "endpoint": "/user/profile",
            "method": "PUT",
            "test_data": ["normal", "boundary"]
        },
        "get_permissions": {
            "name": "获取用户权限",
            "endpoint": "/user/permissions",
            "method": "GET",
            "test_data": ["normal"]
        }
    },
    "task_tests": {
        "create_task": {
            "name": "创建任务",
            "endpoint": "/tasks/create",
            "method": "POST",
            "test_data": ["normal", "boundary", "exception"]
        },
        "get_tasks": {
            "name": "获取任务列表",
            "endpoint": "/tasks/",
            "method": "GET",
            "test_data": ["normal", "boundary"]
        },
        "get_task_detail": {
            "name": "获取任务详情",
            "endpoint": "/tasks/{id}",
            "method": "GET",
            "test_data": ["normal", "boundary"]
        },
        "update_task": {
            "name": "更新任务",
            "endpoint": "/tasks/{id}",
            "method": "PUT",
            "test_data": ["normal", "boundary"]
        },
        "delete_task": {
            "name": "删除任务",
            "endpoint": "/tasks/{id}",
            "method": "DELETE",
            "test_data": ["normal", "boundary"]
        },
        "cancel_task": {
            "name": "取消任务",
            "endpoint": "/tasks/{id}/cancel",
            "method": "POST",
            "test_data": ["normal", "boundary"]
        }
    },
    "scan_tests": {
        "port_scan": {
            "name": "端口扫描",
            "endpoint": "/scan/port-scan",
            "method": "POST",
            "test_data": ["normal", "boundary", "exception"]
        },
        "info_leak": {
            "name": "信息泄露检测",
            "endpoint": "/scan/info-leak",
            "method": "POST",
            "test_data": ["normal", "boundary"]
        },
        "web_side_scan": {
            "name": "Web侧栏扫描",
            "endpoint": "/scan/web-side",
            "method": "POST",
            "test_data": ["normal", "boundary"]
        },
        "comprehensive_scan": {
            "name": "综合扫描",
            "endpoint": "/scan/comprehensive",
            "method": "POST",
            "test_data": ["normal", "boundary", "exception"]
        }
    }
}

# ============ 测试配置 ============
TEST_CONFIG = {
    "environment": {
        "base_url": API_BASE_URL,
        "timeout": API_TIMEOUT,
        "max_iterations": MAX_ITERATIONS
    },
    "execution": {
        "parallel_tests": False,
        "retry_on_failure": True,
        "max_retries": 3,
        "stop_on_first_failure": False
    },
    "reporting": {
        "detailed_output": True,
        "save_results": True,
        "generate_html_report": True,
        "include_performance_metrics": True,
        "include_security_tests": True
    },
    "quality": {
        "min_success_rate": 95.0,
        "max_response_time": 2.0,
        "check_code_coverage": True
    }
}

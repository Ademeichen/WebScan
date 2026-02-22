"""
扩展的API测试配置文件
包含所有API模块的标准化测试数据
"""

API_BASE_URL = "http://127.0.0.1:3000/api"

# ============ 原有测试数据 ============
TEST_DATA = {
    "task": {
        "task_name": "测试POC扫描任务",
        "target": "http://127.0.0.1:8080",
        "task_type": "poc_scan",
        "config": {
            "poc_types": ["weblogic", "struts2", "tomcat"]
        }
    },
    "awvs_task": {
        "task_name": "测试AWVS扫描任务",
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
            "timezone": "Asia/Shanghai",
            "autoUpdate": True,
            "theme": "dark"
        },
        "scan": {
            "defaultDepth": 2,
            "defaultConcurrency": 5,
            "requestTimeout": 30,
            "maxRetries": 3,
            "enableProxy": False
        }
    },
    "user": {
        "username": "test_user",
        "email": "test@example.com",
        "role": "admin"
    },
    "notification": {
        "title": "测试通知",
        "message": "这是一条测试通知",
        "type": "info"
    },
    "ai_chat": {
        "title": "测试AI对话",
        "model": "gpt-4",
        "temperature": 0.7
    },
    "agent_task": {
        "tools": [
            {
                "name": "execute_code",
                "args": {"code": "print('Hello')"},
                "description": "执行Python代码"
            }
        ],
        "user_requirement": "打印Hello"
    }
}

# ============ 新增测试数据 ============

# POC验证API测试数据
POC_VERIFICATION_DATA = {
    "create_task": {
        "target": "http://127.0.0.1:8080",
        "poc_types": ["weblogic", "struts2", "tomcat"],
        "max_concurrent": 5,
        "timeout": 300
    },
    "batch_create_tasks": {
        "targets": [
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8081",
            "http://127.0.0.1:8082"
        ],
        "poc_types": ["weblogic", "struts2"]
    },
    "pause_task": {
        "reason": "暂停测试"
    },
    "resume_task": {
        "reason": "恢复测试"
    },
    "cancel_task": {
        "reason": "取消测试"
    },
    "generate_report": {
        "format": "html",
        "include_details": True
    }
}

# POC文件管理API测试数据
POC_FILES_DATA = {
    "upload_file": {
        "file_path": "test_poc.py",
        "description": "测试POC文件",
        "author": "测试作者",
        "tags": ["weblogic", "struts2"]
    },
    "update_file": {
        "file_id": 1,
        "description": "更新描述",
        "tags": ["weblogic"]
    }
}

# Seebug Agent API测试数据
SEEBUG_AGENT_DATA = {
    "search_vulnerability": {
        "keyword": "weblogic",
        "cve": "CVE-2020-2551",
        "limit": 10
    },
    "generate_poc": {
        "ssvid": "12345",
        "target": "http://127.0.0.1:8080",
        "template": "weblogic"
    }
}

# AI Agents API测试数据
AI_AGENTS_DATA = {
    "create_agent": {
        "name": "测试Agent",
        "description": "这是一个测试AI Agent",
        "config": {
            "model": "gpt-4",
            "temperature": 0.7
        }
    },
    "update_agent": {
        "agent_id": 1,
        "name": "更新Agent",
        "description": "更新后的描述"
    }
}

# 漏洞知识库API测试数据
KB_DATA = {
    "search_vulnerability": {
        "keyword": "weblogic",
        "cve": "CVE-2020-2551",
        "severity": "high",
        "limit": 10
    },
    "get_vulnerability": {
        "ssvid": "12345"
    }
}

# POC智能生成API测试数据
POC_GEN_DATA = {
    "generate_poc": {
        "vulnerability_info": {
            "name": "WebLogic反序列化漏洞",
            "cve": "CVE-2020-2551",
            "description": "WebLogic Server存在反序列化漏洞",
            "severity": "critical"
        },
        "target": "http://127.0.0.1:8080",
        "language": "python"
    }
}

# WebSocket测试数据
WEBSOCKET_DATA = {
    "test_message": {
        "type": "test",
        "content": "测试消息"
    },
    "scan_update": {
        "type": "scan_update",
        "task_id": 1,
        "progress": 50
    }
}

# ============ 边界条件测试数据 ============

# 空值测试
EMPTY_DATA = {
    "empty_string": "",
    "empty_list": [],
    "empty_dict": {}
}

# 特殊字符测试
SPECIAL_CHARS_DATA = {
    "xss_payload": "<script>alert('XSS')</script>",
    "sql_injection": "1' OR '1'='1",
    "path_traversal": "../../../etc/passwd"
}

# 长度边界测试
BOUNDARY_DATA = {
    "very_long_string": "a" * 1000,
    "very_short_string": "a",
    "max_length_string": "a" * 255,
    "min_length_string": "a"
}

# 数据类型测试
TYPE_TEST_DATA = {
    "invalid_number": "not_a_number",
    "negative_number": -1,
    "zero_number": 0,
    "very_large_number": 999999999
}

# ============ 测试目标 ============
TEST_TARGETS = {
    "url": "http://127.0.0.1:8080",
    "ip": "192.168.1.1",
    "domain": "example.com"
}

# ============ POC类型 ============
POC_TYPES = ["weblogic", "struts2", "tomcat", "jboss", "nexus", "drupal"]

# ============ 严重程度 ============
SEVERITY_LEVELS = ["critical", "high", "medium", "low", "info"]

# ============ 漏洞状态 ============
VULNERABILITY_STATUS = ["open", "fixed", "reopened"]

# ============ 任务状态 ============
TASK_STATUS = ["pending", "running", "completed", "failed", "cancelled"]

# ============ 报告格式 ============
REPORT_FORMATS = ["html", "pdf", "json"]

# ============ 通知类型 ============
NOTIFICATION_TYPES = ["high-vulnerability", "medium-vulnerability", "system", "info", "warning"]

# ============ 用户角色 ============
USER_ROLES = ["administrator", "user", "guest"]

# ============ 语言设置 ============
LANGUAGES = ["zh-CN", "en-US", "ja-JP", "ko-KR"]

# ============ 时区设置 ============
TIMEZONES = ["Asia/Shanghai", "Asia/Tokyo", "America/New_York", "Europe/London"]

# ============ 主题设置 ============
THEMES = ["dark", "light", "auto"]

# ============ AI模型 ============
AI_MODELS = ["gpt-3.5", "gpt-4", "gpt-4-turbo", "claude-3", "claude-3.5"]

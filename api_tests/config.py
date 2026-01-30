"""
API测试配置文件
"""

API_BASE_URL = "http://127.0.0.1:3000/api"

# 测试数据
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

# 测试目标
TEST_TARGETS = {
    "url": "http://127.0.0.1:8080",
    "ip": "192.168.1.1",
    "domain": "example.com"
}

# POC类型
POC_TYPES = ["weblogic", "struts2", "tomcat", "jboss", "nexus", "drupal"]

# 严重程度
SEVERITY_LEVELS = ["critical", "high", "medium", "low", "info"]

# 漏洞状态
VULNERABILITY_STATUS = ["open", "fixed", "reopened"]

# 任务状态
TASK_STATUS = ["pending", "running", "completed", "failed", "cancelled"]

# 报告格式
REPORT_FORMATS = ["html", "pdf", "json"]

# API Tests - WebScan AI Security Platform

<div align="center">

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**WebScan AI Security Platform API 测试套件**

基于 Python 的完整 API 测试框架，用于验证后端 API 的功能正确性和稳定性

[测试模块](#测试模块) • [快速开始](#快速开始) • [测试结果](#测试结果) • [开发指南](#-开发指南)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [测试模块](#-测试模块)
- [快速开始](#-快速开始)
- [测试配置](#-测试配置)
- [运行测试](#-运行测试)
- [测试结果](#-测试结果)
- [开发指南](#-开发指南)
- [常见问题](#-常见问题)

---

## 🎯 项目简介

API Tests 是 WebScan AI Security Platform 的自动化测试套件，用于验证后端 API 的功能正确性、性能和稳定性。该测试框架基于 Python 和 requests 库构建，支持模块化测试、结果记录和报告生成。

### 核心特点

- 🧪 **完整的 API 覆盖** - 覆盖所有主要 API 端点
- 📊 **详细的测试报告** - JSON 格式的测试结果记录
- 🚀 **快速执行** - 高效的测试执行机制
- 🔧 **易于扩展** - 模块化的测试结构
- 📝 **清晰的输出** - 彩色终端输出和详细日志

---

## 🧪 测试模块

### 测试模块列表

| 模块 | 功能描述 | 测试端点 |
|------|---------|---------|
| **test_dashboard** | 仪表盘和设置 API 测试 | `/settings/statistics`, `/settings/system-info`, `/settings/` |
| **test_tasks** | 扫描任务 API 测试 | `/tasks/`, `/tasks/create`, `/tasks/{id}`, `/tasks/statistics/overview` |
| **test_poc** | POC 扫描 API 测试 | `/poc/`, `/poc/scan`, `/poc/verify` |
| **test_awvs** | AWVS 扫描 API 测试 | `/awvs/health`, `/awvs/scans`, `/awvs/targets`, `/awvs/scan` |
| **test_agent** | AI Agent API 测试 | `/agent/tasks`, `/agent/config`, `/agent/tools`, `/agent/run` |
| **test_reports** | 报告生成 API 测试 | `/reports/`, `/reports/generate`, `/reports/{id}` |
| **test_scan** | 扫描功能 API 测试 | `/scan/`, `/scan/start`, `/scan/status/{id}`, `/scan/results/{id}` |
| **test_user_notification** | 用户和通知 API 测试 | `/user/profile`, `/notifications`, `/notifications/{id}/read` |
| **test_ai_chat** | AI 对话 API 测试 | `/ai/chat/instances`, `/ai/chat/instances/{id}/messages` |

### 测试覆盖范围

#### 仪表盘和设置 (test_dashboard.py)
- ✅ 获取统计信息
- ✅ 获取系统信息
- ✅ 获取系统设置
- ✅ 更新设置项

#### 扫描任务 (test_tasks.py)
- ✅ 获取任务列表
- ✅ 获取任务统计概览
- ✅ 创建 POC 扫描任务
- ✅ 创建 AWVS 扫描任务
- ✅ 获取任务详情
- ✅ 获取任务结果
- ✅ 获取任务漏洞列表
- ✅ 更新任务状态
- ✅ 取消任务
- ✅ 删除任务

#### POC 扫描 (test_poc.py)
- ✅ 获取 POC 列表
- ✅ 创建 POC 扫描任务
- ✅ 获取 POC 扫描结果
- ✅ 验证 POC

#### AWVS 扫描 (test_awvs.py)
- ✅ 检查 AWVS 服务连接状态
- ✅ 获取扫描列表
- ✅ 获取目标列表
- ✅ 添加扫描目标
- ✅ 创建 AWVS 扫描任务
- ✅ 获取漏洞排名
- ✅ 获取漏洞统计
- ✅ 获取中间件 POC 列表
- ✅ 获取中间件 POC 扫描任务
- ✅ 创建中间件 POC 扫描任务

#### AI Agent (test_agent.py)
- ✅ 获取 Agent 任务列表
- ✅ 获取 Agent 配置
- ✅ 获取可用工具列表
- ✅ 获取环境信息
- ✅ 获取环境可用工具
- ✅ 列出所有能力
- ✅ 运行 Agent 任务
- ✅ 获取 Agent 任务详情
- ✅ 生成扫描代码

#### 报告生成 (test_reports.py)
- ✅ 获取报告列表
- ✅ 生成报告
- ✅ 获取报告详情
- ✅ 下载报告

#### 扫描功能 (test_scan.py)
- ✅ 启动扫描
- ✅ 获取扫描状态
- ✅ 获取扫描结果
- ✅ 停止扫描
- ✅ 端口扫描
- ✅ 信息泄露扫描
- ✅ 目录扫描

#### 用户和通知 (test_user_notification.py)
- ✅ 获取用户资料
- ✅ 更新用户资料
- ✅ 获取通知列表
- ✅ 标记通知为已读
- ✅ 删除通知

#### AI 对话 (test_ai_chat.py)
- ✅ 创建对话实例
- ✅ 获取对话实例详情
- ✅ 获取对话消息历史
- ✅ 发送消息到对话实例
- ✅ 关闭对话实例
- ✅ 列出对话实例

---

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器
- 后端服务运行在 `http://127.0.0.1:3000`

### 安装步骤

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

依赖包：
- `requests>=2.28.0` - HTTP 请求库

#### 2. 配置测试环境

编辑 `config.py` 文件，配置 API 基础 URL：

```python
API_BASE_URL = "http://127.0.0.1:3000/api"
```

#### 3. 启动后端服务

确保后端服务正在运行：

```bash
cd backend
python main.py
```

---

## ⚙️ 测试配置

### 配置文件 (config.py)

```python
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
```

---

## 🏃 运行测试

### 运行所有测试

```bash
python run_tests.py
```

这将运行所有测试模块并生成完整的测试报告。

### 运行指定模块

```bash
python run_tests.py test_dashboard
python run_tests.py test_tasks
python run_tests.py test_poc
python run_tests.py test_awvs
python run_tests.py test_agent
python run_tests.py test_reports
python run_tests.py test_scan
python run_tests.py test_user_notification
python run_tests.py test_ai_chat
```

### 列出所有可用测试

```bash
python run_tests.py --list
```

### 直接运行单个测试模块

```bash
python test_dashboard.py
python test_tasks.py
python test_awvs.py
python test_agent.py
python test_ai_chat.py
```

---

## 📊 测试结果

### 测试输出格式

测试运行时会输出详细的测试结果：

```
================================================================================
WebScan AI Security Platform - 完整API测试套件
================================================================================
开始时间: 2026-01-31 10:00:00
API基础URL: http://127.0.0.1:3000/api
================================================================================

================================================================================
正在运行测试模块: 仪表盘和设置
================================================================================

✅ GET /settings/statistics
   Status: 200, Time: 0.123s

✅ GET /settings/system-info
   Status: 200, Time: 0.089s

✅ GET /settings/
   Status: 200, Time: 0.102s

================================================================================
总体测试摘要
================================================================================
总测试数: 50
成功: 45
失败: 5
成功率: 90.0%
平均响应时间: 0.156s

测试完成时间: 2026-01-31 10:05:00
================================================================================
```

### 测试结果文件

测试结果会自动保存为 JSON 文件：

```bash
api_test_results_20260131_100000.json
```

JSON 文件格式：

```json
{
  "timestamp": "2026-01-31T10:00:00",
  "total_tests": 50,
  "success_count": 45,
  "failure_count": 5,
  "success_rate": 90.0,
  "average_response_time": 0.156,
  "results": [
    {
      "timestamp": "2026-01-31T10:00:01",
      "method": "GET",
      "endpoint": "/settings/statistics",
      "status_code": 200,
      "success": true,
      "response_time": 0.123,
      "error": null
    }
  ]
}
```

### 测试结果文件列表

- `api_test_results_YYYYMMDD_HHMMSS.json` - 完整测试结果
- `dashboard_test_results.json` - 仪表盘测试结果
- `tasks_test_results.json` - 任务测试结果
- `poc_test_results.json` - POC 测试结果
- `awvs_test_results.json` - AWVS 测试结果
- `agent_test_results.json` - Agent 测试结果
- `reports_test_results.json` - 报告测试结果
- `scan_test_results.json` - 扫描测试结果
- `user_notification_test_results.json` - 用户和通知测试结果
- `ai_chat_test_results.json` - AI 对话测试结果

---

## 💻 开发指南

### 添加新的测试模块

#### 1. 创建测试文件

在 `api_tests/` 目录下创建新的测试文件，例如 `test_new_module.py`：

```python
"""
新模块API测试
"""

from api_tester import APITester
from config import TEST_DATA


def test_new_module_api(tester: APITester):
    """测试新模块API"""
    print("\n" + "=" * 60)
    print("测试新模块API")
    print("=" * 60 + "\n")

    # 测试GET请求
    tester.get("/new-module/endpoint")

    # 测试POST请求
    tester.post("/new-module/create", {
        "key": "value"
    })

    # 测试PUT请求
    tester.put("/new-module/update/1", {
        "key": "new_value"
    })

    # 测试DELETE请求
    tester.delete("/new-module/delete/1")


if __name__ == "__main__":
    tester = APITester()
    test_new_module_api(tester)
    tester.print_summary()
    tester.save_results("new_module_test_results.json")
```

#### 2. 注册测试模块

在 `run_tests.py` 中添加新模块：

```python
test_modules = [
    ("仪表盘和设置", "test_dashboard", "test_dashboard_api"),
    ("扫描任务", "test_tasks", "test_tasks_api"),
    # ... 其他模块
    ("新模块", "test_new_module", "test_new_module_api")  # 添加新模块
]
```

### 自定义测试数据

在 `config.py` 中添加自定义测试数据：

```python
TEST_DATA = {
    # ... 现有数据
    "new_module": {
        "key1": "value1",
        "key2": "value2"
    }
}
```

### 修改 API 基础 URL

在 `config.py` 中修改：

```python
API_BASE_URL = "http://your-api-domain.com/api"
```

或在运行时指定：

```bash
# 修改 api_tester.py 中的默认 URL
# 或使用环境变量
```

---

## ❓ 常见问题

### 1. 测试失败 - 连接被拒绝

**问题**: 测试运行时出现连接错误

**解决方案**:
```bash
# 检查后端服务是否运行
curl http://127.0.0.1:3000/api/settings/statistics

# 确保后端服务正在运行
cd backend
python main.py
```

### 2. 测试数据不匹配

**问题**: 测试使用的数据与后端期望的不匹配

**解决方案**:
- 检查 `config.py` 中的测试数据
- 根据后端 API 文档更新测试数据
- 确保数据格式正确

### 3. 某些测试总是失败

**问题**: 特定测试模块总是失败

**解决方案**:
- 检查后端日志获取详细错误信息
- 确认后端 API 是否已实现
- 检查测试数据是否正确
- 查看测试结果 JSON 文件中的错误信息

### 4. 测试运行缓慢

**问题**: 测试执行时间过长

**解决方案**:
- 检查网络连接
- 减少测试数据量
- 并行运行测试（需要修改代码）

### 5. JSON 结果文件无法打开

**问题**: 测试结果 JSON 文件格式错误

**解决方案**:
```bash
# 使用 Python 验证 JSON 格式
python -m json.tool api_test_results_20260131_100000.json

# 或使用在线 JSON 验证工具
```

---

## 📚 相关文档

- [后端 API 文档](../backend/README.md)
- [前端文档](../front/README.md)
- [项目根目录 README](../README.md)
- [API_DOCUMENTATION.md](../API_DOCUMENTATION.md)

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8 代码风格
- 添加详细的文档字符串
- 使用有意义的变量和函数名
- 保持测试代码简洁清晰

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情

---

## 📞 联系方式

- 项目主页: https://github.com/yourusername/webscan-ai
- 问题反馈: https://github.com/yourusername/webscan-ai/issues
- 邮箱: your.email@example.com

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 ⭐️**

Made with ❤️ by WebScan AI Team

</div>

# API测试套件

WebScan AI Security Platform 完整的API测试套件，用于测试所有后端API接口。

## 📁 目录结构

```
api_tests/
├── config.py                    # 测试配置和测试数据
├── api_tester.py               # API测试工具类
├── run_tests.py                # 主测试运行脚本
├── test_dashboard.py            # 仪表盘和设置API测试
├── test_tasks.py               # 扫描任务API测试
├── test_poc.py                # POC扫描API测试
├── test_awvs.py               # AWVS扫描API测试
├── test_agent.py               # AI Agent API测试
├── test_reports.py             # 报告生成API测试
├── test_scan.py               # 扫描功能API测试
├── test_user_notification.py    # 用户和通知API测试
├── test_ai_chat.py            # AI对话API测试
└── README.md                  # 本文件
```

## 🚀 快速开始

### 前置要求

- Python 3.7+
- requests 库
- 后端服务运行在 `http://127.0.0.1:3000`

### 安装依赖

```bash
pip install requests
```

### 运行测试

#### 运行所有测试

```bash
cd api_tests
python run_tests.py
```

#### 运行指定模块测试

```bash
cd api_tests
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

#### 列出所有测试模块

```bash
cd api_tests
python run_tests.py --list
```

#### 单独运行某个测试模块

```bash
cd api_tests
python test_dashboard.py
python test_tasks.py
python test_poc.py
```

## 📊 测试模块说明

### 1. test_dashboard.py - 仪表盘和设置API测试

测试以下API端点：
- `GET /settings/statistics` - 获取统计信息
- `GET /settings/system-info` - 获取系统信息
- `GET /settings/` - 获取所有设置
- `GET /settings/categories` - 获取设置分类
- `GET /settings/category/{category}` - 获取指定分类的设置
- `GET /settings/item/{category}/{key}` - 获取单个设置项
- `PUT /settings/item` - 更新单个设置项
- `PUT /settings/` - 更新设置
- `GET /settings/api-keys` - 获取API密钥列表
- `POST /settings/api-keys` - 创建API密钥
- `POST /settings/reset/{category}` - 重置设置

### 2. test_tasks.py - 扫描任务API测试

测试以下API端点：
- `GET /tasks/` - 获取任务列表
- `GET /tasks/statistics/overview` - 获取任务统计概览
- `POST /tasks/create` - 创建扫描任务
- `GET /tasks/{task_id}` - 获取任务详情
- `GET /tasks/{task_id}/results` - 获取任务结果
- `GET /tasks/{task_id}/vulnerabilities` - 获取任务漏洞列表
- `PUT /tasks/{task_id}` - 更新任务状态
- `POST /tasks/{task_id}/cancel` - 取消任务
- `DELETE /tasks/{task_id}` - 删除任务

### 3. test_poc.py - POC扫描API测试

测试以下API端点：
- `GET /poc/types` - 获取POC类型列表
- `GET /poc/info/{poc_type}` - 获取POC详细信息
- `POST /poc/scan` - 创建POC扫描任务

### 4. test_awvs.py - AWVS扫描API测试

测试以下API端点：
- `GET /awvs/health` - 检查AWVS服务连接状态
- `GET /awvs/scans` - 获取AWVS扫描列表
- `GET /awvs/targets` - 获取目标列表
- `POST /awvs/target` - 添加扫描目标
- `POST /awvs/scan` - 创建AWVS扫描任务
- `GET /awvs/vulnerabilities/rank` - 获取漏洞排名
- `GET /awvs/vulnerabilities/stats` - 获取漏洞统计
- `GET /awvs/middleware/poc-list` - 获取中间件POC列表
- `GET /awvs/middleware/scans` - 获取中间件POC扫描任务
- `POST /awvs/middleware/scan` - 创建中间件POC扫描任务
- `POST /awvs/middleware/scan/start` - 启动中间件POC扫描

### 5. test_agent.py - AI Agent API测试

测试以下API端点：
- `GET /ai_agents/tasks` - 获取Agent任务列表
- `GET /agent/config` - 获取Agent配置
- `GET /agent/tools` - 获取可用工具列表
- `GET /agent/environment/info` - 获取环境信息
- `GET /agent/environment/tools` - 获取环境可用工具
- `GET /agent/capabilities/list` - 列出所有能力
- `POST /agent/run` - 运行Agent任务
- `POST /agent/code/generate` - 生成扫描代码
- `POST /agent/code/execute` - 执行代码
- `POST /agent/code/generate-and-execute` - 生成并执行代码
- `POST /agent/capabilities/enhance` - 增强功能
- `GET /agent/capabilities/{capability_name}` - 获取能力详情

### 6. test_reports.py - 报告生成API测试

测试以下API端点：
- `GET /reports/` - 获取报告列表
- `POST /reports/` - 创建新报告
- `GET /reports/{report_id}` - 获取报告详情
- `PUT /reports/{report_id}` - 更新报告
- `DELETE /reports/{report_id}` - 删除报告
- `GET /reports/{report_id}/export` - 导出报告

### 7. test_scan.py - 扫描功能API测试

测试以下API端点：
- `POST /scan/port-scan` - 端口扫描
- `POST /scan/info-leak` - 信息泄露检测
- `POST /scan/web-side` - 旁站扫描
- `POST /scan/baseinfo` - 获取网站基本信息
- `POST /scan/web-weight` - 获取网站权重
- `POST /scan/ip-locating` - IP定位
- `POST /scan/cdn-check` - CDN检测
- `POST /scan/waf-check` - WAF检测
- `POST /scan/what-cms` - CMS指纹识别
- `POST /scan/subdomain` - 子域名扫描
- `POST /scan/dir-scan` - 目录扫描
- `POST /scan/comprehensive` - 综合扫描

### 8. test_user_notification.py - 用户和通知API测试

测试以下API端点：
- `GET /user/profile` - 获取用户信息
- `PUT /user/profile` - 更新用户信息
- `GET /user/permissions` - 获取用户权限
- `GET /user/list` - 获取用户列表
- `GET /notifications/` - 获取通知列表
- `GET /notifications/count/unread` - 获取未读通知数量
- `POST /notifications/` - 创建通知
- `GET /notifications/{notification_id}` - 获取通知详情
- `PUT /notifications/{notification_id}/read` - 标记通知为已读
- `PUT /notifications/read-all` - 标记所有通知为已读
- `DELETE /notifications/{notification_id}` - 删除通知
- `DELETE /notifications/` - 删除所有已读通知

### 9. test_ai_chat.py - AI对话API测试

测试以下API端点：
- `POST /ai/chat/instances` - 创建新的对话实例
- `GET /ai/chat/instances` - 列出对话实例
- `GET /ai/chat/instances/{chat_instance_id}` - 获取对话实例详情
- `DELETE /ai/chat/instances/{chat_instance_id}` - 删除对话实例
- `POST /ai/chat/instances/{chat_instance_id}/messages` - 发送消息到对话实例
- `GET /ai/chat/instances/{chat_instance_id}/messages` - 获取对话消息历史
- `POST /ai/chat/instances/{chat_instance_id}/close` - 关闭对话实例

## 📝 测试结果

测试结果会自动保存为JSON文件，包含以下信息：

- 测试时间戳
- API端点
- 请求方法
- 状态码
- 成功/失败状态
- 响应时间
- 错误信息（如果失败）

### 结果文件命名

- 完整测试：`api_test_results_YYYYMMDD_HHMMSS.json`
- 单模块测试：`{module_name}_results.json`

### 结果示例

```json
{
  "summary": {
    "total_tests": 50,
    "success_count": 45,
    "failed_count": 5,
    "success_rate": "90.00%",
    "average_response_time": "0.234s"
  },
  "results": [
    {
      "timestamp": "2026-01-30T22:30:00.123456",
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

## ⚙️ 配置说明

### 修改API基础URL

编辑 `config.py` 文件：

```python
API_BASE_URL = "http://your-api-url:port/api"
```

### 修改测试数据

编辑 `config.py` 文件中的 `TEST_DATA` 字典：

```python
TEST_DATA = {
    "task": {
        "task_name": "自定义任务名称",
        "target": "http://your-target.com",
        ...
    }
}
```

## 🔧 故障排除

### 连接错误

如果出现连接错误，请检查：
1. 后端服务是否正在运行
2. API基础URL是否正确
3. 防火墙是否阻止连接

### 超时错误

如果出现超时错误，可以：
1. 增加请求超时时间（在 `api_tester.py` 中修改）
2. 检查网络连接
3. 检查后端服务性能

### 导入错误

如果出现导入错误，请确保：
1. Python版本 >= 3.7
2. 已安装 requests 库
3. 在 `api_tests` 目录下运行脚本

## 📈 测试覆盖率

本测试套件覆盖以下API模块：

| 模块 | 测试端点数 | 覆盖率 |
|--------|------------|---------|
| 仪表盘和设置 | 12 | 100% |
| 扫描任务 | 10 | 100% |
| POC扫描 | 3 | 100% |
| AWVS扫描 | 12 | 100% |
| AI Agent | 13 | 100% |
| 报告生成 | 7 | 100% |
| 扫描功能 | 12 | 100% |
| 用户和通知 | 13 | 100% |
| AI对话 | 7 | 100% |
| **总计** | **89** | **100%** |

## 🤝 贡献

如果发现新的API端点未测试，可以：

1. 在相应的测试文件中添加测试用例
2. 在 `config.py` 中添加测试数据
3. 更新本README文档

## 📄 许可

本测试套件遵循与主项目相同的许可证。

## 👥 支持

如有问题，请查看项目文档或联系开发团队。

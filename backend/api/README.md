# API 包说明文档

## 简介

`api` 是 AI_WebSecurity 项目的应用程序接口模块集合，提供了系统核心功能的接口定义和实现。这些接口用于处理用户请求、管理扫描任务、调用漏洞验证、生成报告等核心功能，是整个系统的中枢神经系统。

## 功能模块列表

| 模块名称 | 文件位置 | 功能描述 |
|---------|---------|----------|
| **agent** | `agent.py` | AI Agent任务管理，启动和监控智能扫描任务 |
| **ai** | `ai.py` | AI对话模块，提供智能安全咨询和漏洞分析 |
| **awvs** | `awvs.py` | AWVS集成模块，调用AWVS进行漏洞扫描 |
| **kb** | `kb.py` | 知识库模块，管理安全知识库和漏洞信息 |
| **poc** | `poc.py` | POC漏洞验证接口，调用POC验证脚本 |
| **poc_gen** | `poc_gen.py` | POC智能生成模块，基于Seebug Agent生成POC |
| **poc_verification** | `poc_verification.py` | POC验证任务管理 |
| **poc_files** | `poc_files.py` | POC文件管理，上传和管理POC脚本 |
| **seebug_agent** | `seebug_agent.py` | Seebug Agent集成，搜索和生成POC |
| **seebug_client** | `seebug_client.py` | Seebug API客户端 |
| **reports** | `reports.py` | 报告生成模块，生成安全扫描报告 |
| **scan** | `scan.py` | 扫描管理模块，处理扫描任务的创建和执行 |
| **settings** | `settings.py` | 系统设置模块，管理系统配置和参数 |
| **tasks** | `tasks.py` | 任务管理模块，处理异步任务的调度和执行 |
| **user** | `user.py` | 用户管理模块，用户资料和权限管理 |
| **notifications** | `notifications.py` | 通知管理模块，系统通知和消息管理 |

## 核心功能说明

### 1. 扫描管理 (scan.py)

- 创建和管理安全扫描任务
- 配置扫描参数和选项
- 执行扫描并监控进度
- 处理扫描结果

### 2. 漏洞验证 (poc.py, poc_verification.py)

- 调用POC包中的验证脚本
- 管理漏洞验证任务
- 处理验证结果和报告
- 支持批量验证和并发执行

### 3. AWVS集成 (awvs.py)

- 与Acunetix Web Vulnerability Scanner集成
- 调用AWVS API进行漏洞扫描
- 处理AWVS返回的扫描结果
- 支持多种扫描类型

### 4. AI Agent (agent.py)

- 基于LangGraph的智能代理工作流
- 自动化任务规划和执行
- 集成多种扫描工具和POC
- 智能决策和结果验证

### 5. AI对话 (ai.py)

- 智能安全咨询
- 漏洞分析建议
- 代码审查辅助
- 会话管理

### 6. 报告生成 (reports.py)

- 生成安全扫描报告
- 支持多种报告格式
- 汇总漏洞信息和风险评估
- 执行轨迹报告

### 7. POC智能生成 (poc_gen.py, seebug_agent.py)

- 基于Seebug Agent的POC智能生成
- 漏洞信息分析和代码生成
- POC文件下载和管理

### 8. 知识库管理 (kb.py)

- 管理安全知识库和漏洞信息
- 提供漏洞详情和修复建议
- 支持知识库的更新和扩展

### 9. 任务管理 (tasks.py)

- 管理异步任务的调度和执行
- 处理任务队列和状态
- 支持任务的暂停、继续和取消

### 10. 用户和通知 (user.py, notifications.py)

- 用户资料管理
- 权限控制
- 系统通知和消息管理

## API端点

### 健康检查
- `GET /health` - 系统健康检查

### AI Agent
- `POST /api/ai_agents/scan` - 启动Agent扫描
- `GET /api/ai_agents/tasks` - 获取任务列表
- `GET /api/ai_agents/tasks/{task_id}` - 获取任务详情
- `GET /api/ai_agents/tools` - 获取可用工具列表

### AWVS
- `GET /api/awvs/health` - AWVS健康检查
- `GET /api/awvs/scans` - 获取扫描任务列表
- `POST /api/awvs/scan` - 创建扫描任务
- `GET /api/awvs/targets` - 获取目标列表
- `POST /api/awvs/target` - 添加目标
- `GET /api/awvs/vulnerabilities/{target_id}` - 获取漏洞列表

### POC管理
- `POST /api/poc/scan` - POC扫描
- `POST /api/poc/verification/tasks` - 创建验证任务
- `GET /api/poc/verification/tasks/{task_id}` - 获取验证任务状态
- `GET /api/poc/files` - 获取POC文件列表
- `POST /api/poc/files/upload` - 上传POC文件

### AI对话
- `POST /api/ai/chat` - 创建对话
- `POST /api/ai/chat/{chat_id}/message` - 发送消息
- `GET /api/ai/chat/{chat_id}/messages` - 获取对话历史

### 任务和报告
- `GET /api/tasks` - 获取任务列表
- `GET /api/tasks/{task_id}` - 获取任务详情
- `GET /api/reports` - 获取报告列表
- `POST /api/reports/generate` - 生成报告

### 知识库
- `GET /api/kb/vulnerabilities` - 获取漏洞列表
- `GET /api/kb/vulnerabilities/{vuln_id}` - 获取漏洞详情

### 用户和通知
- `GET /api/user/profile` - 获取用户资料
- `PUT /api/user/profile` - 更新用户资料
- `GET /api/notifications` - 获取通知列表
- `PUT /api/notifications/{id}/read` - 标记通知为已读

## 测试

### 测试目录结构

```
api/
└── tests/
    ├── test_routes.py           # API路由测试
    ├── test_awvs.py             # AWVS API测试
    └── test_error_handling.py   # 错误处理测试
```

### 运行测试

```bash
# 运行所有API测试
pytest api/tests/ -v

# 运行特定测试文件
pytest api/tests/test_routes.py -v

# 运行带覆盖率的测试
pytest api/tests/ --cov=api --cov-report=html
```

## 使用方法

### 导入和使用API模块

```python
# 示例：导入扫描管理模块
from backend.api.scan import create_scan_task

# 使用示例
target = "https://example.com"
scan_options = {
    "scan_type": "full",
    "timeout": 3600,
    "threads": 10
}
task_id = create_scan_task(target, scan_options)
print(f"创建扫描任务成功，任务ID: {task_id}")
```

### API调用示例

#### 1. 创建扫描任务

```python
from backend.api.scan import create_scan_task

target_url = "https://example.com"
options = {
    "scan_type": "full",
    "depth": 3,
    "include_subdomains": True
}
task_id = create_scan_task(target_url, options)
print(f"扫描任务创建成功，ID: {task_id}")
```

#### 2. 验证漏洞

```python
from backend.api.poc import verify_vulnerability

target = "https://example.com"
vuln_id = "CVE-2017-12615"
result = verify_vulnerability(target, vuln_id)
print(f"漏洞验证结果: {result}")
```

#### 3. 生成报告

```python
from backend.api.reports import generate_report

task_id = "123456"
report_format = "html"
report_path = generate_report(task_id, report_format)
print(f"报告生成成功，路径: {report_path}")
```

## API开发规范

### 新增API模块的步骤

1. 在 `api` 目录下创建新的模块文件，命名为 `[功能名称].py`
2. 实现核心功能函数，并提供清晰的文档字符串
3. 在 `__init__.py` 中注册路由
4. 添加必要的测试用例
5. 更新相关文档

### 代码规范

- 使用 UTF-8 编码
- 遵循 PEP 8 代码风格
- 提供详细的文档字符串
- 实现错误处理和异常捕获
- 使用标准的HTTP状态码返回结果
- 提供统一的错误处理机制

## 注意事项

1. **安全风险**：API可能会执行敏感操作，请确保访问控制安全
2. **性能考虑**：避免在API中执行耗时操作，使用异步处理大任务
3. **错误处理**：确保API能够优雅处理错误并返回有意义的错误信息
4. **参数验证**：对所有输入参数进行严格验证，防止注入攻击
5. **日志记录**：记录关键操作和错误信息，便于故障排查

## 版本历史

- **v1.0.0**：初始版本，包含基础API模块
- **v1.1.0**：添加了更多API功能
- **v1.2.0**：优化了API性能和稳定性
- **v1.3.0**：集成了AI能力和AWVS接口
- **v1.4.0**：添加了Seebug Agent集成和POC智能生成
- **v1.5.0**：优化测试结构，添加稳定性机制

## 贡献指南

欢迎提交Issue和Pull Request，共同改进API功能。提交代码时，请确保：

1. 代码符合项目的编码规范
2. 添加了必要的测试用例
3. 更新了相关文档
4. 提供了详细的变更说明

---

*本文档由 AI_WebSecurity 项目组维护*
*最后更新时间：2026-03-03*

# API 包说明文档

## 简介

`api` 是 AI_WebSecurity 项目的应用程序接口模块集合，提供了系统核心功能的接口定义和实现。这些接口用于处理用户请求、管理扫描任务、调用漏洞验证、生成报告等核心功能，是整个系统的中枢神经系统。

## 功能模块列表

| 模块名称 | 文件位置 | 功能描述 |
|---------|---------|----------|
| **agent** | `agent.py` | 代理管理模块，处理代理服务器的配置和使用 |
| **ai** | `ai.py` | 人工智能模块，集成AI能力用于漏洞检测和分析 |
| **awvs** | `awvs.py` | AWVS (Acunetix Web Vulnerability Scanner) 集成模块，用于调用AWVS进行漏洞扫描 |
| **kb** | `kb.py` | 知识库模块，管理安全知识库和漏洞信息 |
| **poc** | `poc.py` | 漏洞验证接口模块，调用poc包中的验证脚本 |
| **poc_gen** | `poc_gen.py` | POC生成模块，自动生成漏洞验证脚本 |
| **reports** | `reports.py` | 报告生成模块，生成安全扫描报告 |
| **scan** | `scan.py` | 扫描管理模块，处理扫描任务的创建和执行 |
| **settings** | `settings.py` | 系统设置模块，管理系统配置和参数 |
| **tasks** | `tasks.py` | 任务管理模块，处理异步任务的调度和执行 |

## 核心功能说明

### 1. 扫描管理 (scan.py)

- 创建和管理安全扫描任务
- 配置扫描参数和选项
- 执行扫描并监控进度
- 处理扫描结果

### 2. 漏洞验证 (poc.py)

- 调用poc包中的验证脚本
- 管理漏洞验证任务
- 处理验证结果和报告

### 3. AWVS集成 (awvs.py)

- 与Acunetix Web Vulnerability Scanner集成
- 调用AWVS API进行漏洞扫描
- 处理AWVS返回的扫描结果

### 4. 报告生成 (reports.py)

- 生成安全扫描报告
- 支持多种报告格式
- 汇总漏洞信息和风险评估

### 5. 任务管理 (tasks.py)

- 管理异步任务的调度和执行
- 处理任务队列和状态
- 支持任务的暂停、继续和取消

### 6. 人工智能集成 (ai.py)

- 集成AI能力用于漏洞检测
- 分析扫描结果和生成智能建议
- 优化扫描策略和优先级

### 7. POC生成 (poc_gen.py)

- 自动生成漏洞验证脚本
- 基于漏洞信息和规则生成POC
- 测试和验证生成的POC

### 8. 知识库管理 (kb.py)

- 管理安全知识库和漏洞信息
- 提供漏洞详情和修复建议
- 支持知识库的更新和扩展

### 9. 代理管理 (agent.py)

- 管理代理服务器的配置和使用
- 支持多种代理类型
- 优化网络请求和扫描性能

### 10. 系统设置 (settings.py)

- 管理系统配置和参数
- 提供配置的读取和写入功能
- 支持配置的验证和默认值

## 依赖项

- Python 3.7+
- requests: 用于HTTP请求
- 各模块可能有额外的依赖，具体请参考各模块的实现文件

## 使用方法

### 导入和使用API模块

```python
# 示例：导入扫描管理模块
from backend.api.scan import create_scan_task

# 使用示例
target = "https://www.baidu.com"
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

target_url = "https://www.baidu.com"
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

target = "https://www.baidu.com"
vuln_id = "CVE-2017-12615"
result = verify_vulnerability(target, vuln_id)
print(f"漏洞验证结果: {result}")
```

#### 3. 生成报告

```python
from backend.api.reports import generate_report

task_id = "123456"
report_format = "pdf"
report_path = generate_report(task_id, report_format)
print(f"报告生成成功，路径: {report_path}")
```

## API开发规范

### 新增API模块的步骤

1. 在 `api` 目录下创建新的模块文件，命名为 `[功能名称].py`
2. 实现核心功能函数，并提供清晰的文档字符串
3. 在 `__init__.py` 中导出必要的函数和类
4. 添加必要的依赖项说明

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

## 贡献指南

欢迎提交Issue和Pull Request，共同改进API功能。提交代码时，请确保：

1. 代码符合项目的编码规范
2. 添加了必要的测试用例
3. 更新了相关文档
4. 提供了详细的变更说明

## 联系信息

如有问题或建议，请联系项目维护者。

---

*本文档由 AI_WebSecurity 项目组维护*
*最后更新时间：2026-01-22*
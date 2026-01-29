# 基于 Pocsuite3 和 Seebug 的智能 POC 验证系统

## 📋 项目概述

本项目实现了一个完整的智能 POC 验证系统，作为独立节点集成到智能体工作流图中。通过集成代码执行节点与 LangGraph 框架，实现了端到端的自动化 POC 验证流程。

## 🎯 核心功能

### 1. 平台集成与认证机制
- ✅ 开发 Pocsuite3 与 Seebug 平台的双向技术对接模块
- ✅ 实现基于 API 密钥的认证机制
- ✅ 构建 API 请求封装层，确保 Seebug API 接口调用的稳定性
- ✅ 实现超时处理与错误重试机制
- ✅ 实现连接状态监控与自动重连功能

### 2. 核心功能模块
- ✅ 设计 POC 脚本管理系统，支持从 Seebug 平台同步及本地自定义脚本的加载与版本控制
- ✅ 开发目标信息输入模块，支持批量导入、单个输入及从智能体工作流接收目标数据
- ✅ 实现 POC 验证执行引擎，支持多线程并发执行与资源限制管理
- ✅ 构建结果分析模块，实现漏洞验证状态判定、漏洞等级评估及详细报告生成

### 3. 智能体工作流节点集成
- ✅ 基于 LangGraph 框架设计标准工作流节点，实现符合智能体生态的输入/输出接口规范
- ✅ 定义标准化数据交互格式，支持与其他工作流节点的无缝数据传递
- ✅ 实现节点状态管理功能，支持暂停、继续、终止等工作流控制操作

### 4. 代码执行节点组件
- ✅ 构建安全的代码沙箱环境，支持动态加载并执行 POC 验证代码
- ✅ 开发执行过程监控模块，实时捕获执行日志、异常信息与性能指标
- ✅ 实现执行结果结构化存储与标准化输出，确保结果可被智能体系统解析

### 5. 数据集成与替换
- ✅ 设计真实目标环境数据接入方案，支持从多种数据源获取目标信息
- ✅ 实现 Seebug 平台漏洞信息的实时同步机制，确保漏洞数据的时效性与准确性
- ✅ 开发数据清洗与标准化处理模块，统一不同来源数据的格式与字段定义

### 6. 辅助功能完善
- ✅ 构建全面的错误处理机制，包括参数验证、运行时异常捕获与友好提示
- ✅ 实现分级日志系统，支持调试、信息、警告、错误等多级别日志记录
- ✅ 开发结果报告生成模块，支持 HTML、JSON、PDF 等多种格式输出

### 7. 系统架构与可扩展性
- ✅ 采用模块化架构设计，确保各功能模块低耦合高内聚
- ✅ 实现插件化机制，支持新增 POC 验证规则与第三方平台集成
- ✅ 设计配置中心，支持系统参数的动态调整与功能开关控制

### 8. LangGraph 节点实现
- ✅ 基于 LangGraph 框架开发专用 POC 验证节点，实现 agent 驱动的 POC 验证流程
- ✅ 设计节点状态管理逻辑，支持验证任务的创建、执行、暂停与结果返回
- ✅ 实现与代码执行节点的无缝集成，确保 POC 生成代码能够被正确执行并返回验证结果

## 📁 文件结构

### 新增文件

```
backend/ai_agents/poc_system/
  ├── __init__.py                           # POC 系统模块入口
  ├── poc_manager.py                        # POC 脚本管理器
  ├── target_manager.py                      # 目标信息管理器
  ├── verification_engine.py                   # POC 验证执行引擎
  ├── result_analyzer.py                     # 结果分析器
  └── report_generator.py                    # 报告生成器

backend/ai_agents/core/
  └── poc_verification_node.py               # POC 验证节点（LangGraph）

backend/api/
  └── poc_verification.py                    # POC 验证 API 路由

backend/tests/
  └── test_poc_verification.py              # POC 验证系统单元测试
```

### 修改文件

```
backend/ai_agents/core/state.py              # 扩展 AgentState 添加 POC 验证相关字段
backend/models.py                           # 添加 POC 验证数据模型
backend/config.py                           # 添加 POC 验证相关配置项
backend/ai_agents/core/graph.py             # 集成 POC 验证节点到工作流
backend/api/__init__.py                    # 注册 POC 验证 API 路由
```

## 🔧 配置项

在 `backend/config.py` 中添加了以下配置项：

```python
# POC 验证配置
POC_VERIFICATION_ENABLED: bool = True              # 是否启用 POC 验证功能
POC_MAX_CONCURRENT_EXECUTIONS: int = 5         # POC 最大并发执行数
POC_EXECUTION_TIMEOUT: int = 60                # POC 执行超时时间（秒）
POC_RETRY_MAX_COUNT: int = 3                   # POC 验证最大重试次数
POC_RESULT_ACCURACY_THRESHOLD: float = 0.95     # POC 结果准确率阈值
POC_CACHE_ENABLED: bool = True                  # 是否启用 POC 缓存
POC_CACHE_TTL: int = 3600                       # POC 缓存生存时间（秒）
POC_REPORT_FORMAT: str = "html"                # POC 验证报告默认格式
```

## 📊 数据模型

### POCVerificationTask
POC 验证任务表，用于记录和管理 POC 验证任务。

**字段：**
- `id`: 任务唯一标识（UUID）
- `task_id`: 关联的任务 ID
- `poc_name`: POC 名称
- `poc_id`: POC ID（SSVID）
- `poc_code`: POC 代码
- `target`: 验证目标
- `priority`: 优先级（1-10）
- `status`: 任务状态（pending, running, completed, failed, cancelled）
- `progress`: 任务进度（0-100）
- `config`: 任务配置信息（JSON 格式）
- `created_at`: 任务创建时间
- `updated_at`: 任务最后更新时间

### POCVerificationResult
POC 验证结果表，用于存储 POC 验证的执行结果。

**字段：**
- `id`: 结果唯一标识
- `verification_task`: 关联的验证任务对象
- `poc_name`: POC 名称
- `poc_id`: POC ID
- `target`: 验证目标
- `vulnerable`: 是否存在漏洞
- `message`: 结果消息
- `output`: 完整输出
- `error`: 错误信息
- `execution_time`: 执行时间（秒）
- `confidence`: 结果置信度（0-1）
- `severity`: 漏洞严重度（critical, high, medium, low, info）
- `cvss_score`: CVSS 评分（0-10）
- `created_at`: 结果创建时间

### POCExecutionLog
POC 执行日志表，用于记录 POC 执行过程中的详细日志。

**字段：**
- `id`: 日志唯一标识
- `verification_result`: 关联的验证结果对象
- `log_level`: 日志级别（debug, info, warning, error, critical）
- `message`: 日志消息
- `details`: 详细信息（JSON 格式）
- `timestamp`: 日志时间戳

## 🔌 API 接口

### 1. 创建 POC 验证任务
```
POST /api/poc/verification/tasks
```

**请求参数：**
- `poc_id`: POC ID
- `target`: 验证目标
- `priority`: 优先级（1-10）
- `task_id`: 关联的任务 ID（可选）

**响应：**
```json
{
  "code": 200,
  "message": "POC 验证任务创建成功",
  "data": {
    "task": {...},
    "result": {...},
    "analysis": {...}
  }
}
```

### 2. 批量创建 POC 验证任务
```
POST /api/poc/verification/tasks/batch
```

**请求参数：**
- `poc_tasks`: POC 任务列表
- `target`: 验证目标
- `task_id`: 关联的任务 ID（可选）

**响应：**
```json
{
  "code": 200,
  "message": "批量 POC 验证任务创建成功",
  "data": {
    "tasks": [...],
    "results_count": 10,
    "analysis": {...}
  }
}
```

### 3. 列出 POC 验证任务
```
GET /api/poc/verification/tasks?status=completed&page=1&page_size=20
```

**查询参数：**
- `status`: 任务状态过滤（可选）
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 20）

**响应：**
```json
{
  "code": 200,
  "message": "查询验证任务成功",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

### 4. 获取 POC 验证任务详情
```
GET /api/poc/verification/tasks/{task_id}
```

**响应：**
```json
{
  "code": 200,
  "message": "查询验证任务成功",
  "data": {
    "task": {...},
    "results": [...],
    "results_count": 10,
    "vulnerable_count": 5
  }
}
```

### 5. 暂停 POC 验证任务
```
POST /api/poc/verification/tasks/{task_id}/pause
```

**响应：**
```json
{
  "code": 200,
  "message": "验证任务已暂停"
}
```

### 6. 继续 POC 验证任务
```
POST /api/poc/verification/tasks/{task_id}/resume
```

**响应：**
```json
{
  "code": 200,
  "message": "验证任务已继续"
}
```

### 7. 取消 POC 验证任务
```
POST /api/poc/verification/tasks/{task_id}/cancel
```

**响应：**
```json
{
  "code": 200,
  "message": "验证任务已取消"
}
```

### 8. 获取 POC 验证结果
```
GET /api/poc/verification/tasks/{task_id}/results
```

**响应：**
```json
{
  "code": 200,
  "message": "查询验证结果成功",
  "data": {
    "task_id": "...",
    "results": [...],
    "total_count": 10,
    "vulnerable_count": 5,
    "not_vulnerable_count": 5
  }
}
```

### 9. 生成 POC 验证报告
```
POST /api/poc/verification/tasks/{task_id}/report?format=html
```

**查询参数：**
- `format`: 报告格式（html, json, pdf，默认 html）
- `output_path`: 输出文件路径（可选）

**响应：**
```json
{
  "code": 200,
  "message": "报告生成成功",
  "data": {
    "task_id": "...",
    "format": "html",
    "report": "...",
    "generated_at": "..."
  }
}
```

### 10. 获取 POC 验证统计信息
```
GET /api/poc/verification/statistics
```

**响应：**
```json
{
  "code": 200,
  "message": "查询统计信息成功",
  "data": {
    "total_tasks": 100,
    "running_tasks": 5,
    "completed_tasks": 90,
    "failed_tasks": 5,
    "total_results": 90,
    "vulnerable_results": 20,
    "success_rate": 22.2,
    "active_executions": 2,
    "registered_pocs": 50,
    "cached_pocs": 30
  }
}
```

### 11. 获取 POC 注册表
```
GET /api/poc/verification/poc/registry
```

**响应：**
```json
{
  "code": 200,
  "message": "查询 POC 注册表成功",
  "data": {
    "total": 50,
    "pocs": [...]
  }
}
```

### 12. 从 Seebug 同步 POC
```
POST /api/poc/verification/poc/sync?keyword=thinkphp&limit=100&force_refresh=false
```

**查询参数：**
- `keyword`: 搜索关键词（可选）
- `limit`: 同步数量限制（默认 100）
- `force_refresh`: 是否强制刷新缓存（默认 false）

**响应：**
```json
{
  "code": 200,
  "message": "POC 同步成功",
  "data": {
    "synced_count": 50,
    "pocs": [...],
    "cache_stats": {...}
  }
}
```

### 13. 健康检查
```
GET /api/poc/verification/health
```

**响应：**
```json
{
  "code": 200,
  "message": "POC 验证系统运行正常",
  "data": {
    "status": "healthy",
    "enabled": true,
    "config": {...},
    "statistics": {...}
  }
}
```

## 🧪 LangGraph 工作流集成

POC 验证节点已成功集成到 LangGraph 工作流中，作为第 11 个节点。

### 工作流图结构

```
环境感知 → 任务规划 → 智能决策
                                    ↓
                    ┌──────────┼──────────┐
                    ↓          ↓          ↓
                固定工具    代码生成    POC 验证 ← 新增
                    ↓          ↓          ↓
                工具执行 → 代码执行    ↓
                    ↓          ↓          ↓
                结果验证 ←────────┘          ↓
                    ↓                      ↓
              ┌──────┴──────┐              ↓
              ↓             ↓              ↓
          继续工具      漏洞分析 ←──────────┘
              ↓             ↓
          工具执行      报告生成
                          ↓
                        结束
```

### 节点信息

**节点名称：** `poc_verification`

**节点描述：** POC 验证节点，负责执行 POC 验证任务

**节点功能：**
- 接收 AgentState 作为输入
- 执行 POC 验证任务
- 分析验证结果
- 更新漏洞列表
- 返回更新后的状态

**状态管理：**
- `pending`: 待执行
- `running`: 执行中
- `paused`: 已暂停
- `completed`: 已完成
- `failed`: 执行失败
- `cancelled`: 已取消

## 📈 质量保证

### 功能完整性
- ✅ 覆盖从漏洞信息获取到验证报告生成的全流程
- ✅ 支持批量目标处理
- ✅ 支持多种报告格式（HTML、JSON、PDF）
- ✅ 完整的错误处理和重试机制

### 执行稳定性
- ✅ 连接状态监控和自动重连
- ✅ 资源限制和超时控制
- ✅ 多线程并发执行优化
- ✅ 异常捕获和优雅降级

### 结果准确性
- ✅ 误报检测机制
- ✅ 结果置信度计算
- ✅ 多次验证确认
- ✅ CVSS 评分集成

## 🚀 部署指南

### 1. 环境要求

**Python 版本：** 3.8+

**依赖包：**
- FastAPI
- Tortoise-ORM
- LangChain
- LangGraph
- Pocsuite3
- httpx
- pytest（用于测试）

### 2. 安装步骤

1. 克隆项目仓库
```bash
git clone <repository-url>
cd AI_WebSecurity
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量（可选）
```bash
export OPENAI_API_KEY="your-api-key"
export SEEBUG_API_KEY="your-seebug-api-key"
```

4. 初始化数据库
```bash
cd backend
python -c "from tortoise import Tortoise; import asyncio; asyncio.run(Tortoise.init_db())"
```

5. 启动后端服务
```bash
python main.py
```

### 3. 配置说明

所有配置项都在 `backend/config.py` 中定义，可以通过环境变量覆盖：

```bash
# POC 验证配置
export POC_VERIFICATION_ENABLED=true
export POC_MAX_CONCURRENT_EXECUTIONS=5
export POC_EXECUTION_TIMEOUT=60
export POC_RETRY_MAX_COUNT=3
export POC_RESULT_ACCURACY_THRESHOLD=0.95
export POC_CACHE_ENABLED=true
export POC_CACHE_TTL=3600
export POC_REPORT_FORMAT=html
```

### 4. 运行测试

```bash
# 运行所有测试
pytest backend/tests/test_poc_verification.py -v

# 运行特定测试类
pytest backend/tests/test_poc_verification.py::TestPOCMetadata -v

# 运行特定测试方法
pytest backend/tests/test_poc_verification.py::TestPOCMetadata::test_poc_metadata_creation -v
```

## 📚 用户手册

### 1. 创建 POC 验证任务

**步骤：**
1. 确定要验证的 POC ID 和目标 URL
2. 调用 `POST /api/poc/verification/tasks` 接口
3. 等待验证完成

**示例：**
```bash
curl -X POST http://localhost:3000/api/poc/verification/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "poc_id": "seebug_123456",
    "target": "https://example.com",
    "priority": 5
  }'
```

### 2. 批量验证 POC

**步骤：**
1. 准备多个 POC 任务
2. 调用 `POST /api/poc/verification/tasks/batch` 接口
3. 系统会并发执行所有 POC 验证

**示例：**
```bash
curl -X POST http://localhost:3000/api/poc/verification/tasks/batch \
  -H "Content-Type: application/json" \
  -d '{
    "poc_tasks": [
      {"poc_id": "seebug_123456", "priority": 5},
      {"poc_id": "seebug_789012", "priority": 3}
    ],
    "target": "https://example.com"
  }'
```

### 3. 查询验证结果

**步骤：**
1. 调用 `GET /api/poc/verification/tasks/{task_id}` 接口
2. 查看验证结果和统计信息

**示例：**
```bash
curl http://localhost:3000/api/poc/verification/tasks/{task_id}
```

### 4. 生成验证报告

**步骤：**
1. 调用 `POST /api/poc/verification/tasks/{task_id}/report` 接口
2. 指定报告格式（html、json、pdf）
3. 下载或查看生成的报告

**示例：**
```bash
curl -X POST http://localhost:3000/api/poc/verification/tasks/{task_id}/report?format=html \
  -o report.html
```

### 5. 从 Seebug 同步 POC

**步骤：**
1. 调用 `POST /api/poc/verification/poc/sync` 接口
2. 指定搜索关键词和数量限制
3. 查看 POC 注册表

**示例：**
```bash
curl -X POST "http://localhost:3000/api/poc/verification/poc/sync?keyword=thinkphp&limit=100"
```

## 🔍 故障排除

### 常见问题

**1. POC 验证任务创建失败**
- 检查 POC ID 是否有效
- 检查目标 URL 是否可访问
- 检查 POC 验证功能是否启用

**2. POC 验证执行超时**
- 检查 `POC_EXECUTION_TIMEOUT` 配置
- 检查网络连接
- 检查目标服务器状态

**3. 报告生成失败**
- 检查报告格式是否支持
- 检查输出路径是否有写入权限
- 检查依赖包是否安装（如 weasyprint 用于 PDF）

**4. Seebug API 同步失败**
- 检查 API Key 是否有效
- 检查网络连接
- 检查 Seebug API 端点是否正确

## 📞 技术支持

如有问题或建议，请联系技术支持团队。

**联系方式：**
- 邮箱：support@example.com
- GitHub Issues：https://github.com/example/issues

## 📝 更新日志

### v1.0.0 (2026-01-28)
- ✅ 初始版本发布
- ✅ 实现所有核心功能
- ✅ 集成到 LangGraph 工作流
- ✅ 提供完整的 API 接口
- ✅ 编写单元测试和文档

---

**项目状态：** ✅ 已完成

**最后更新：** 2026-01-28

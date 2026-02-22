# Changelog

All notable changes to the WebScan AI Security Platform will be documented in this file.

## [1.0.0] - 2026-02-23

### Added

#### API日志系统增强
- **统一日志中间件**: 新增 `backend/api/logging_middleware.py`，提供统一的API请求日志记录功能
  - 请求ID追踪
  - 请求时间戳记录
  - API端点路径和方法记录
  - 请求参数记录（自动遮蔽敏感数据）
  - 处理状态和响应耗时记录
  - 错误信息详细记录
  - 日志级别控制机制

#### 前端API功能完善
- **POC验证API**: 新增 `pocVerificationApi` 模块，支持POC验证任务的完整生命周期管理
- **POC文件管理API**: 新增 `pocFilesApi` 模块，支持POC脚本文件的查询和管理
- **Seebug Agent API**: 新增 `seebugAgentApi` 模块，支持Seebug漏洞搜索和POC生成
- **AI Agents API**: 新增 `aiAgentsApi` 模块，支持AI Agent工作流管理

### Changed

#### 文档整理
- 删除冗余文档 `PROJECT_SUMMARY.md`，内容已整合到主 `README.md`
- 删除冗余文档 `AI_AGENT_WORKFLOW_LOGGING_REPORT.md`，内容已整合到 `backend/ai_agents/README.md`
- 更新 `COMPLETE_API_DOCUMENTATION.md` 的API端点列表

#### 后端优化
- 在 `main.py` 中集成API日志中间件
- 配置API专用日志器，日志输出到 `logs/api.log`

### Fixed

- 修复前端API模块缺失的问题，补充了4个新的API模块
- 修复API文档与实际API端点不一致的问题

---

## [0.9.0] - 2026-02-22

### Added

#### AI Agent功能
- **统一任务模型**: 使用单一 `Task` 模型替代双 `Task`/`AgentTask` 模型
- **串行任务执行**: 实现 `TaskExecutor` 串行队列，防止并发资源冲突
- **幂等性保护**: 在 `TaskExecutor` 中添加重复任务提交检查
- **全局超时控制**: 强制执行全局超时（默认1小时）
- **原子进度事件**: 添加四个关键阶段的粒度进度跟踪
- **WebSocket集成**: 实现实时双向通信进行进度更新
- **单元测试**: 添加 `AWVSScanningNode`、`ToolExecutionNode` 和 `TaskExecutor` 的综合单元测试

### Changed

#### API端点
- `POST /api/agent/scan`: 现在创建 `Task` 记录并提交到 `task_executor`
- `GET /api/agent/tasks/{task_id}`: 优先使用 `Task` 模型查找
- `GET /api/agent/tasks`: 更新为按 `task_type="ai_agent_scan"` 过滤

#### AWVS集成
- 重构 `AWVSScanningNode` 使用 `asyncio.to_thread` 进行非阻塞执行

#### LangGraph工作流
- 集成 `AWVSScanningNode` 和 `POCVerificationNode` 到 `ScanAgentGraph`
- 添加重试限制以防止能力增强期间的无限循环

### Fixed

- **无限循环**: 通过添加重试计数器解决代理在代码执行和能力增强之间卡住的问题
- **进度显示**: 通过WebSocket广播原子阶段更新修复前端进度条
- **任务调度**: 修复任务队列逻辑以确保扫描任务的严格串行执行

---

## [0.8.0] - 2026-02-20

### Added

- 初始版本发布
- POC漏洞扫描功能
- 端口扫描功能
- AWVS集成
- AI Agent扫描
- Seebug Agent集成
- 漏洞管理
- 扫描报告生成
- 实时监控
- 漏洞知识库
- 通知中心
- AI对话功能
- API测试套件

---

## 版本说明

- **[1.0.0]** - 生产就绪版本，包含完整的API日志系统和前端API功能
- **[0.9.0]** - AI Agent功能增强版本
- **[0.8.0]** - 初始发布版本

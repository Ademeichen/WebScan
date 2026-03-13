# Changelog
All notable changes to the WebScan AI Security Platform will be documented in this file.

## [1.0.0] - 2026-03-13

### Added
#### API兼容性分析
- **前端API匹配率100%**: 所有91个前端API接口都已成功匹配后端实现
- **API分析工具**: 新增 `analyze_all_apis_fixed.py` 完整的前后端API兼容性分析脚本
- **API文档更新**: 在主README.md中添加完整的API兼容性分析章节
- **API模块统计**: 13个API模块，共91个前端接口，141个后端接口

#### 前端API优化
- **移除未使用的API**: 清理了前端api.js中未使用的API定义
  - 移除 `vulnerabilitiesApi` 整个模块
  - 移除 `awvsApi.getVulnerabilities` 
  - 移除 `kbApi.addKnowledge`
  - 移除 `kbApi.updateKnowledge`
  - 移除 `kbApi.deleteKnowledge`

#### 文档优化
- **删除冗余文档**: 移除重复的README文件
  - 删除 `backend/README.md`（内容与根目录README重复）
  - 删除 `backend/api/README.md`（内容与根目录README重复）
- **更新主README**: 添加完整的API兼容性分析章节，包含：
  - API统计数据表格
  - 匹配成功率统计
  - 所有API模块的详细列表
  - 主要API端点示例
  - API分析工具使用说明

### Changed
#### API接口优化
- **前端API路径修复**: 修复了API解析脚本中的路径识别错误
- **API匹配算法改进**: 使用括号匹配算法确保每个API方法正确提取URL和HTTP方法

### API兼容性统计
| 指标 | 数值 | 说明 |
|------|------|------|
| 后端API总数 | 141 | FastAPI提供的所有接口 |
| 前端API总数 | 91 | Vue3项目使用的API接口 |
| 匹配成功 | 91 | 前后端接口完全匹配 |
| 前端未匹配 | 0 | 前端所有API都有对应的后端实现 |
| 后端未匹配 | 51 | 后端有51个接口前端暂未使用 |
| 前端API匹配率 | 100% | 所有前端API都已成功匹配 |
| 后端API使用率 | 64.5% | 前端使用了64.5%的后端接口 |

### API模块分布
| 模块 | 接口数量 | 状态 |
|------|---------|------|
| scanApi | 11 | ✅ 全部匹配 |
| tasksApi | 4 | ✅ 全部匹配 |
| reportsApi | 3 | ✅ 全部匹配 |
| settingsApi | 8 | ✅ 全部匹配 |
| pocApi | 2 | ✅ 全部匹配 |
| awvsApi | 9 | ✅ 全部匹配 |
| aiApi | 3 | ✅ 全部匹配 |
| kbApi | 4 | ✅ 全部匹配 |
| userApi | 4 | ✅ 全部匹配 |
| notificationsApi | 5 | ✅ 全部匹配 |
| pocVerificationApi | 7 | ✅ 全部匹配 |
| pocFilesApi | 5 | ✅ 全部匹配 |
| seebugAgentApi | 3 | ✅ 全部匹配 |
| aiAgentsApi | 18 | ✅ 全部匹配 |

---

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

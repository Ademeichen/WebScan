# AI Agents - Web安全漏洞扫描智能体编排系统

## 项目概述

基于LangGraph框架构建的Web安全漏洞扫描Agent智能体编排系统，实现自主任务规划、工具调用、结果迭代验证、漏洞分析与报告生成的端到端自动化扫描流程。

### 核心特性

✅ **完整的LangGraph工作流**：任务规划 → 工具执行 → 结果验证 → 漏洞分析 → 报告生成
✅ **统一的工具管理**：集成所有现有扫描插件和POC
✅ **智能决策优化**：基于优先级、资源分配、策略自适应
✅ **灵活的配置系统**：支持动态配置和扩展
✅ **完善的API接口**：RESTful API，易于集成
✅ **可扩展的架构**：预留插件注册接口，易于扩展

### 技术栈

- **LangGraph**：构建有向图工作流
- **LangChain**：LLM增强任务规划
- **FastAPI**：异步API接口
- **Tortoise-ORM**：数据持久化
- **asyncio**：异步任务执行

---

## 目录结构

```
ai_agents/
├── __init__.py              # 模块入口
├── config.py                # Agent配置管理
├── core/                    # 核心框架
│   ├── __init__.py
│   ├── state.py             # Agent状态管理
│   ├── graph.py             # LangGraph图构建
│   └── nodes.py            # 节点定义
├── tools/                   # 工具集成
│   ├── __init__.py
│   ├── registry.py          # 工具注册表
│   ├── wrappers.py          # 工具异步封装
│   └── adapters.py          # 工具适配器
├── analyzers/               # 结果分析
│   ├── __init__.py
│   ├── vuln_analyzer.py    # 漏洞分析器
│   └── report_gen.py       # 报告生成器
├── utils/                   # 工具函数
│   ├── __init__.py
│   ├── priority.py          # 优先级管理
│   └── retry.py            # 重试策略
├── api/                     # API路由
│   ├── __init__.py
│   └── routes.py            # Agent API接口
├── README.md                # 功能说明文档
└── PERFORMANCE_REPORT.md      # 性能测试报告
```

---

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

在`.env`文件中添加以下配置：

```bash
# AI Agent 配置
AGENT_MAX_EXECUTION_TIME=300
AGENT_MAX_RETRIES=3
MAX_CONCURRENT_TOOLS=5
TOOL_TIMEOUT=60
ENABLE_LLM_PLANNING=true
ENABLE_MEMORY=true
ENABLE_KB_INTEGRATION=true
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://127.0.0.1:3000` 启动。

### 4. 使用Agent扫描

```bash
# 启动Agent扫描
curl -X POST "http://127.0.0.1:3000/api/ai_agents/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "http://example.com"
  }'

# 查询任务状态
curl "http://127.0.0.1:3000/api/ai_agents/tasks/{task_id}"
```

---

## 核心功能

### 1. 任务规划

支持两种规划模式：

**规则化规划**：
- 基于预设规则生成任务序列
- 快速、可预测
- 适合标准化扫描场景

**LLM增强规划**：
- 使用大语言模型智能生成任务序列
- 根据目标特征动态调整
- 更适应复杂场景

### 2. 工具调用

统一的工具调用接口：

**插件工具**：
- baseinfo：基础信息收集
- portscan：端口扫描
- waf_detect：WAF检测
- cdn_detect：CDN检测
- cms_identify：CMS识别
- infoleak_scan：信息泄露扫描
- subdomain_scan：子域名扫描
- webside_scan：站点信息收集
- webweight_scan：网站权重查询

**POC工具**：
- WebLogic POC：CVE-2020-2551、CVE-2018-2628等
- Struts2 POC：S2-009、S2-032等
- Tomcat POC：CVE-2017-12615、CVE-2022-22965等
- JBoss POC：CVE-2017-12149
- Nexus POC：CVE-2020-10199
- Drupal POC：CVE-2018-7600

### 3. 结果验证

基于扫描结果动态调整扫描策略：

- 根据CMS类型补充相关POC
- 根据开放端口补充相关POC
- 检测到WAF/CDN时调整扫描策略
- 支持迭代验证和策略自适应

### 4. 漏洞分析

智能漏洞分析功能：

- 漏洞去重（根据CVE和目标组合）
- 按严重度排序（critical > high > medium > low）
- 生成漏洞统计信息
- 可选：从知识库获取修复建议

### 5. 报告生成

支持多种报告格式：

**JSON格式**：
- 结构化数据
- 易于程序处理
- 包含所有扫描结果

**HTML格式**：
- 可视化报告
- 包含图表和统计
- 易于人工阅读

---

## API接口

### 启动Agent扫描

**端点**：`POST /api/ai_agents/scan`

**请求示例**：
```json
{
  "target": "http://example.com",
  "enable_llm_planning": true,
  "custom_tasks": ["baseinfo", "portscan"]
}
```

**响应示例**：
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "running",
  "message": "Agent扫描任务已启动"
}
```

### 获取任务详情

**端点**：`GET /api/ai_agents/tasks/{task_id}`

**响应示例**：
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "final_output": {
    "task_id": "123e4567-e89b-12d3-a456-426614174000",
    "target": "http://example.com",
    "vulnerabilities": {
      "list": [...],
      "total": 5,
      "summary": "共发现 5 个漏洞: Critical: 1, High: 2, Medium: 2"
    }
  }
}
```

### 其他API

- `GET /api/ai_agents/tasks`：获取任务列表
- `DELETE /api/ai_agents/tasks/{task_id}`：取消任务
- `GET /api/ai_agents/tools`：获取可用工具列表
- `GET /api/ai_agents/config`：获取配置
- `POST /api/ai_agents/config`：更新配置

详细API文档请参考 [README.md](./README.md#接口定义)

---

## 扩展开发

### 添加新工具

1. 创建工具函数：
```python
async def my_scan_tool(target: str) -> dict:
    return {"status": "success", "data": {...}}
```

2. 注册工具：
```python
from ai_agents.tools import register_tool

@register_tool(
    name="my_tool",
    description="我的扫描工具",
    category="plugin",
    timeout=30
)
async def my_tool(target: str):
    return await my_scan_tool(target)
```

### 添加新节点

1. 创建节点类：
```python
from ai_agents.core.state import AgentState

class MyCustomNode:
    async def __call__(self, state: AgentState) -> AgentState:
        return state
```

2. 在graph.py中添加节点：
```python
from my_node import MyCustomNode

def _build_graph(self) -> StateGraph:
    workflow = StateGraph(AgentState)
    workflow.add_node("my_custom_node", MyCustomNode())
    return workflow
```

---

## 性能指标

根据性能测试报告（详见 [PERFORMANCE_REPORT.md](./PERFORMANCE_REPORT.md)）：

| 指标 | 数值 | 说明 |
|--------|------|------|
| 单目标扫描时间 | 45.2秒 | 比传统扫描快34% |
| 多目标并发效率 | 42.9秒/目标 | 比传统扫描快26% |
| 漏洞发现准确率 | 92% | 比传统扫描高18% |
| 内存占用 | 245MB | 比传统扫描低21% |
| 自动化程度 | 95% | 比传统扫描高111% |

---

## 配置说明

### 核心配置

| 配置项 | 默认值 | 说明 |
|--------|----------|------|
| MAX_EXECUTION_TIME | 300 | Agent最大执行时间（秒） |
| MAX_RETRIES | 3 | 工具执行最大重试次数 |
| MAX_CONCURRENT_TOOLS | 5 | 最大并发工具执行数 |
| TOOL_TIMEOUT | 60 | 单个工具执行超时时间（秒） |
| ENABLE_LLM_PLANNING | true | 是否启用LLM增强任务规划 |
| DEFAULT_SCAN_TASKS | [...] | 默认扫描任务列表 |
| ENABLE_MEMORY | true | 是否启用记忆机制 |
| ENABLE_KB_INTEGRATION | true | 是否启用漏洞知识库集成 |

详细配置说明请参考 [README.md](./README.md#配置说明)

---

## 文档

- [系统完整文档](./SYSTEM_DOCUMENTATION.md) - 整合了API路由、整合指南和性能测试报告的完整技术文档
- [代码阅读指南](./阅读顺序.md) - 按照推荐顺序阅读代码的指南

---

## 故障排查

### 常见问题

1. **工具执行失败**
   - 检查工具是否正确注册
   - 检查目标URL/IP是否可访问
   - 查看日志中的详细错误信息

2. **LLM规划失败**
   - 检查OPENAI_API_KEY和OPENAI_BASE_URL配置
   - 检查网络连接
   - 可以禁用LLM规划使用规则化规划

3. **任务超时**
   - 增加MAX_EXECUTION_TIME配置
   - 减少扫描任务数量
   - 优化工具超时时间

4. **内存占用过高**
   - 减少MEMORY_MAX_SIZE配置
   - 定期清理执行历史
   - 禁用记忆机制

### 日志查看

所有Agent执行日志记录在`logs/app.log`：

```bash
# 查看实时日志
tail -f logs/app.log

# 搜索特定任务的日志
grep "task_id: 123e4567" logs/app.log
```

---

## 许可证

本项目遵循原项目的许可证。

---

## 贡献

欢迎提交Issue和Pull Request来改进本项目。

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue
- 发送邮件

---

## 总结

AI Agents智能体编排系统提供了完整的Web安全漏洞扫描解决方案，具备：

✅ **完整的LangGraph工作流**：任务规划 → 工具执行 → 结果验证 → 漏洞分析 → 报告生成
✅ **统一的工具管理**：集成所有现有插件和POC
✅ **智能决策优化**：基于优先级、资源分配、策略自适应
✅ **灵活的配置系统**：支持动态配置和扩展
✅ **完善的API接口**：RESTful API，易于集成
✅ **可扩展的架构**：预留插件注册接口，易于扩展

通过本系统，可以实现自动化、智能化的Web安全漏洞扫描，大幅提升扫描效率和准确性。

# WebScan AI Security Platform - Backend

AI 驱动的 Web 安全扫描平台后端服务，提供漏洞扫描、POC 验证、AI 对话和自动化任务执行等功能。

## 目录

- [项目概述](#项目概述)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [核心功能模块](#核心功能模块)
- [Seebug Agent 集成](#seebug-agent-集成)
- [AI Agents 工作流](#ai-agents-工作流)
- [安装配置](#安装配置)
- [使用方法](#使用方法)
- [API 端点](#api-端点)
- [开发指南](#开发指南)

## 项目概述

WebScan AI Security Platform 是一个集成多种安全扫描工具和 AI 能力的综合安全平台，支持：

- **多种漏洞扫描**：AWVS 集成、POC 验证、端口扫描等
- **AI 智能对话和分析**：OpenAI GPT、通义千问
- **自动化任务执行**：基于 LangGraph 的智能代理工作流
- **POC 智能生成**：集成 Seebug Agent 的 POC 生成功能
- **扫描报告生成和管理**：支持多种格式输出
- **插件化架构**：易于扩展和维护

## 技术栈

- **Web 框架**: FastAPI 0.115.6
- **数据库 ORM**: Tortoise-ORM 0.21.7
- **数据库迁移**: Aerich 0.7.2
- **AI 框架**: LangChain 0.3.14, LangGraph 0.2.59
- **异步运行时**: asyncio + uvicorn
- **HTTP 客户端**: httpx, requests
- **安全扫描**: python-nmap, BeautifulSoup4, dnslib
- **其他**: Pydantic, loguru, python-dotenv

## 项目结构

```
backend/
├── main.py                     # FastAPI 主应用入口
├── config.py                   # 应用配置管理
├── models.py                   # 数据库模型定义
├── database.py                 # 数据库连接管理
├── task_executor.py            # 任务执行器
├── requirements.txt            # Python 依赖列表
├── .env                        # 环境变量配置
├── AWVS_API_README.md          # AWVS API 使用说明
│
├── api/                        # API 路由模块
│   ├── __init__.py             # 路由注册
│   ├── scan.py                 # 扫描功能 API
│   ├── poc.py                  # POC 漏洞扫描 API
│   ├── awvs.py                 # AWVS 集成 API
│   ├── ai.py                   # AI 对话 API
│   ├── agent.py                # AI Agent API
│   ├── settings.py             # 系统设置 API
│   ├── tasks.py                # 任务管理 API
│   ├── reports.py              # 报告生成 API
│   ├── kb.py                   # 知识库 API
│   ├── poc_gen.py              # POC 智能生成 API
│   ├── poc_verification.py     # POC 验证 API
│   ├── poc_files.py            # POC 文件管理 API
│   ├── seebug_agent.py         # Seebug Agent API
│   ├── seebug_client.py        # Seebug 客户端 API
│   ├── user.py                 # 用户管理 API
│   ├── notifications.py        # 通知管理 API
│   ├── common.py               # 通用工具
│   ├── decorators.py           # 装饰器
│   ├── task_utils.py           # 任务工具
│   └── validation_utils.py    # 验证工具
│
├── ai_agents/                  # AI Agents 智能代理系统
│   ├── __init__.py             # 模块初始化
│   ├── agent_config.py         # Agent 配置管理
│   ├── README.md               # AI Agents 文档
│   ├── core/                   # 核心组件
│   │   ├── graph.py            # LangGraph 图构建
│   │   ├── nodes.py            # 图节点定义
│   │   ├── state.py            # Agent 状态管理
│   │   └── test_*.py           # 单元测试
│   ├── analyzers/              # 分析器模块
│   │   ├── vuln_analyzer.py    # 漏洞分析器
│   │   ├── report_gen.py       # 报告生成器
│   │   └── test_*.py           # 单元测试
│   ├── code_execution/         # 代码执行模块
│   │   ├── code_generator.py    # 代码生成器
│   │   ├── executor.py         # 代码执行器
│   │   ├── environment.py      # 执行环境
│   │   ├── capability_enhancer.py # 能力增强器
│   │   ├── process_utils.py    # 进程工具
│   │   ├── README.md           # 代码执行文档
│   │   └── test_*.py           # 单元测试
│   ├── poc_system/             # POC 系统模块
│   │   ├── poc_manager.py      # POC 管理器
│   │   ├── target_manager.py   # 目标管理器
│   │   ├── verification_engine.py # 验证引擎
│   │   ├── result_analyzer.py  # 结果分析器
│   │   ├── report_generator.py # 报告生成器
│   │   ├── utils.py            # 工具函数
│   │   └── __init__.py         # 模块初始化
│   ├── tools/                  # 工具模块
│   │   ├── registry.py         # 工具注册表
│   │   ├── adapters.py         # 工具适配器
│   │   ├── wrappers.py         # 工具包装器
│   │   └── test_*.py           # 单元测试
│   ├── utils/                  # 工具函数
│   │   ├── cache.py            # 缓存管理
│   │   ├── file_sync.py        # 文件同步
│   │   ├── priority.py         # 优先级管理
│   │   ├── retry.py            # 重试机制
│   │   └── test_*.py           # 单元测试
│   └── api/                    # AI Agents API
│       ├── routes.py           # API 路由
│       └── __init__.py         # 模块初始化
│
├── plugins/                    # 扫描插件模块
│   ├── README.md               # 插件说明文档
│   ├── portscan/              # 端口扫描
│   ├── infoleak/              # 信息泄露扫描
│   ├── webside/               # 网站侧边栏扫描
│   ├── baseinfo/              # 基础信息收集
│   ├── webweight/             # 网站权重查询
│   ├── iplocating/            # IP 定位
│   ├── cdnexist/              # CDN 检测
│   ├── waf/                   # WAF 检测
│   ├── whatcms/               # CMS 识别
│   ├── subdomain/             # 子域名扫描
│   ├── loginfo/               # 日志处理
│   ├── randheader/            # 随机请求头生成
│   └── common/                # 通用工具
│
├── AVWS/                      # AWVS API 封装
│   └── API/                   # AWVS API 模块
│       ├── Base.py            # 基础 API 类
│       ├── Dashboard.py       # 仪表板 API
│       ├── Group.py           # 分组 API
│       ├── Report.py          # 报告 API
│       ├── Scan.py            # 扫描 API
│       ├── Target.py          # 目标 API
│       ├── TargetOption.py    # 目标选项 API
│       ├── Vuln.py            # 漏洞 API
│       └── __init__.py        # 模块初始化
│
├── geoip/                     # GeoIP 数据库
│   ├── GeoLite2-ASN.mmdb      # GeoIP 数据库文件
│   ├── apps.json              # 应用指纹数据库
│   ├── apps.txt               # 应用指纹文本
│   ├── infoleak.json          # 信息泄露指纹
│   └── __init__.py            # 模块初始化
│
├── data/                      # 数据目录
│   └── webscan.db             # SQLite 数据库文件
│
├── logs/                      # 日志目录
│   └── app.log                # 应用日志
│
└── Pocsuite3Agent/            # Pocsuite3 Agent 集成
    ├── agent.py               # Pocsuite3 Agent
    └── __init__.py            # 模块初始化
```

## 核心功能模块

### 数据库模型 (models.py)
包含所有数据模型定义：
- **Task**: 扫描任务管理
- **Report**: 扫描报告管理
- **Vulnerability**: 漏洞信息管理
- **ScanResult**: 扫描结果管理
- **POCScanResult**: POC 扫描结果
- **POCVerificationTask**: POC 验证任务
- **POCVerificationResult**: POC 验证结果
- **POCExecutionLog**: POC 执行日志
- **AIChatInstance**: AI 对话实例
- **AIChatMessage**: AI 对话消息
- **AgentTask**: AI Agent 任务
- **AgentResult**: AI Agent 结果
- **SystemLog**: 系统日志
- **SystemSetting**: 系统设置
- **User**: 用户管理
- **Notification**: 通知管理
- **KnowledgeBase**: 知识库

### API 路由模块
提供完整的 RESTful API 接口：
- **scan**: 扫描功能（端口扫描、子域名扫描、信息泄露扫描等）
- **poc**: POC 漏洞扫描
- **awvs**: AWVS 集成扫描
- **ai**: AI 对话功能
- **agent**: AI Agent 任务管理
- **tasks**: 任务管理
- **reports**: 报告生成和管理
- **kb**: 漏洞知识库
- **poc_gen**: POC 智能生成
- **poc_verification**: POC 验证
- **poc_files**: POC 文件管理
- **seebug_agent**: Seebug Agent 集成
- **settings**: 系统设置
- **user**: 用户管理
- **notifications**: 通知管理

### 扫描插件模块
提供多种安全扫描插件：
- **portscan**: 端口扫描
- **infoleak**: 信息泄露扫描
- **webside**: 网站侧边栏扫描
- **baseinfo**: 基础信息收集
- **webweight**: 网站权重查询
- **iplocating**: IP 定位
- **cdnexist**: CDN 检测
- **waf**: WAF 检测
- **whatcms**: CMS 识别
- **subdomain**: 子域名扫描
- **loginfo**: 日志处理
- **randheader**: 随机请求头生成

## Seebug Agent 集成

### 集成架构
Seebug Agent 已完整集成到后端系统中，包括：

1. **API 层集成** (`api/poc_gen.py`)
   - POC 智能生成接口
   - 漏洞信息分析
   - 代码自动生成

2. **AI Agents 集成** (`ai_agents/core/nodes.py`)
   - SeebugAgentNode 节点
   - 自动搜索 Seebug POC
   - 智能生成 POC 代码
   - 集成到 LangGraph 工作流

3. **工具层集成** (`api/seebug_client.py`)
   - 统一的 Seebug Agent 访问接口
   - 配置管理和错误处理

### 工作流程
```
用户请求 → API 路由 → Seebug Agent → POC 生成 → 验证 → 结果返回
```

## AI Agents 工作流

### 图结构 (ai_agents/core/graph.py)
基于 LangGraph 的智能代理工作流，包含多个核心节点：

```
环境感知 → 任务规划 → 智能决策 → 工具执行/代码生成/Seebug Agent → 结果验证 → 漏洞分析 → 报告生成
```

### 核心节点
1. **环境感知节点**: 分析目标环境特征
2. **任务规划节点**: 制定扫描策略
3. **智能决策节点**: 选择最优扫描方式
4. **Seebug Agent 节点**: 搜索和生成 POC
5. **POC 验证节点**: 执行 POC 验证
6. **漏洞分析节点**: 分析扫描结果
7. **报告生成节点**: 生成最终报告

### Seebug Agent 集成路径
```
智能决策节点
    ↓
Seebug Agent 节点 (搜索 POC → 生成代码 → 创建验证任务)
    ↓
POC 验证节点
    ↓
漏洞分析节点
```

## 安装配置

### 环境要求
- Python 3.8+
- SQLite（默认）或 PostgreSQL/MySQL
- AWVS（可选，用于 AWVS 扫描）

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd AI_WebSecurity/backend
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
# 复制 .env 文件（如果不存在）
# 编辑 .env 文件，配置以下参数
```

主要配置项：
```bash
# 应用配置
APP_NAME=WebScan AI Security Platform
APP_VERSION=1.0.0
DEBUG=False
HOST=127.0.0.1
PORT=3000

# 数据库配置
DATABASE_URL=sqlite://./data/webscan.db

# CORS 配置
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# AI API 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://maas-api.cn-huabei-1.xf-yun.com/v2
MODEL_ID=xop3qwen1b7

# AWVS 配置
AWVS_API_URL=https://127.0.0.1:3443
AWVS_API_KEY=your_awvs_api_key

# Seebug 配置
SEEBUG_API_KEY=your_seebug_api_key
SEEBUG_API_BASE_URL=https://www.seebug.org/api

# 扫描配置
MAX_CONCURRENT_SCANS=5
SCAN_TIMEOUT=300

# 代码执行配置
CODE_EXECUTOR_ENABLED=True
CODE_EXECUTOR_TIMEOUT=30
CODE_EXECUTOR_WORKSPACE=executor_workspace

# AI Agent 配置
AGENT_MAX_EXECUTION_TIME=300
AGENT_MAX_RETRIES=3

# POC 验证配置
POC_VERIFICATION_ENABLED=True
POC_MAX_CONCURRENT_EXECUTIONS=5
POC_EXECUTION_TIMEOUT=60
POC_RETRY_MAX_COUNT=3
```

4. 启动服务
```bash
python main.py
```

服务将在 `http://127.0.0.1:3000` 启动。

## 使用方法

### API 文档
启动服务后访问：
- Swagger UI: http://localhost:3000/docs
- ReDoc: http://localhost:3000/redoc

### 主要功能模块

#### 1. 扫描功能
- 端口扫描、子域名扫描、目录扫描
- 漏洞扫描（AWVS 集成）
- POC 验证扫描

#### 2. AI 对话
- 智能安全咨询
- 漏洞分析建议
- 代码审查辅助

#### 3. AI Agents
- 自动化任务执行
- 智能代码生成
- POC 验证工作流
- Seebug Agent 集成

#### 4. POC 管理
- POC 文件管理
- POC 智能生成（Seebug Agent）
- POC 验证执行

## API 端点

### 扫描相关
- `POST /scan/` - 创建扫描任务
- `GET /scan/{task_id}` - 获取扫描状态
- `GET /scan/{task_id}/results` - 获取扫描结果
- `GET /scan/plugins` - 获取可用插件列表

### AI 对话
- `POST /ai/chat` - 创建对话
- `POST /ai/chat/{chat_id}/message` - 发送消息
- `GET /ai/chat/{chat_id}/messages` - 获取对话历史

### AI Agents
- `POST /api/ai_agents/scan` - 启动 Agent 扫描
- `GET /api/ai_agents/tasks/{task_id}` - 获取任务状态
- `GET /api/ai_agents/tasks` - 获取任务列表
- `GET /api/ai_agents/tools` - 获取可用工具列表

### POC 管理
- `POST /poc-gen/generate` - 智能生成 POC（Seebug Agent）
- `POST /poc/verification/tasks` - 创建 POC 验证任务
- `GET /poc/verification/tasks/{task_id}` - 获取验证任务状态
- `GET /poc/files` - 获取 POC 文件列表
- `POST /poc/files/upload` - 上传 POC 文件

### AWVS 集成
- `GET /awvs/health` - AWVS 健康检查
- `GET /awvs/scans` - 获取所有扫描任务
- `POST /awvs/scan` - 创建扫描任务
- `GET /awvs/vulnerabilities/{target_id}` - 获取目标漏洞列表
- `GET /awvs/targets` - 获取所有目标

### 任务管理
- `GET /tasks` - 获取任务列表
- `GET /tasks/{task_id}` - 获取任务详情
- `DELETE /tasks/{task_id}` - 删除任务

### 报告管理
- `GET /reports` - 获取报告列表
- `GET /reports/{report_id}` - 获取报告详情
- `POST /reports/generate` - 生成报告

### 知识库
- `GET /kb/vulnerabilities` - 获取漏洞列表
- `GET /kb/vulnerabilities/{vuln_id}` - 获取漏洞详情

### 用户和通知
- `GET /user/profile` - 获取用户资料
- `PUT /user/profile` - 更新用户资料
- `GET /notifications` - 获取通知列表
- `PUT /notifications/{id}/read` - 标记通知为已读

## 开发指南

### 添加新的扫描插件
1. 在 `plugins/` 目录下创建新的插件目录
2. 实现插件类，提供扫描功能
3. 在 `api/scan.py` 中注册插件

### 扩展 AI Agents 功能
1. 在 `ai_agents/core/nodes.py` 中添加新的节点
2. 在 `ai_agents/core/graph.py` 中集成到工作流
3. 添加相应的工具函数

### 数据库模型扩展
1. 在 `models.py` 中添加新的模型类
2. 运行数据库迁移（如果使用 Aerich）
3. 更新相关的 API 路由

### Seebug Agent 集成开发
1. 修改 `api/seebug_client.py` 中的接口
2. 在 `ai_agents/core/nodes.py` 中优化 SeebugAgentNode
3. 更新 `api/poc_gen.py` 中的 POC 生成逻辑

### 测试
运行测试套件：
```bash
pytest tests/
```

## 部署说明

### 生产环境部署
1. 使用 Gunicorn 作为 WSGI 服务器
2. 配置 Nginx 反向代理
3. 设置环境变量和配置文件
4. 配置 SSL/TLS 证书

### 监控和日志
- 使用 `SystemLog` 模型记录系统日志
- 配置日志轮转和归档
- 集成监控工具（如 Prometheus + Grafana）

## 许可证

本项目采用 MIT 许可证。

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目。

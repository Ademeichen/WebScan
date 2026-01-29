# WebScan AI Security Platform - Backend

AI 驱动的 Web 安全扫描平台后端服务，提供漏洞扫描、POC 验证、AI 对话和自动化任务执行等功能。

## 目录

- [项目概述](#项目概述)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [核心文件说明](#核心文件说明)
- [安装配置](#安装配置)
- [使用方法](#使用方法)
- [API 端点](#api-端点)
- [开发指南](#开发指南)

## 项目概述

WebScan AI Security Platform 是一个集成多种安全扫描工具和 AI 能力的综合安全平台，支持：

- 多种漏洞扫描（AWVS 集成、POC 验证、端口扫描等）
- AI 智能对话和分析（OpenAI GPT、通义千问）
- 自动化任务执行和进度跟踪
- 扫描报告生成和管理
- 插件化架构，易于扩展

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
├── main.py                 # FastAPI 主应用入口
├── config.py               # 应用配置管理
├── models.py               # 数据库模型定义
├── database.py             # 数据库连接管理
├── task_executor.py        # 任务执行器
├── requirements.txt         # Python 依赖列表
├── pyproject.toml         # 项目配置
│
├── api/                   # API 路由模块
│   ├── __init__.py         # 路由注册
│   ├── scan.py            # 扫描功能 API
│   ├── poc.py             # POC 漏洞扫描 API
│   ├── awvs.py            # AWVS 集成 API
│   ├── ai.py              # AI 对话 API
│   ├── agent.py           # AI Agent API
│   ├── settings.py        # 系统设置 API
│   ├── tasks.py          # 任务管理 API
│   ├── reports.py        # 报告生成 API
│   ├── kb.py            # 知识库 API
│   └── poc_gen.py       # POC 生成 API
│
├── plugins/              # 扫描插件模块
│   ├── portscan/        # 端口扫描
│   ├── infoleak/        # 信息泄露扫描
│   ├── webside/         # 网站侧边栏扫描
│   ├── baseinfo/         # 基础信息收集
│   ├── webweight/       # 网站权重查询
│   ├── iplocating/      # IP 定位
│   ├── cdnexist/        # CDN 检测
│   ├── waf/            # WAF 检测
│   ├── whatcms/         # CMS 识别
│   ├── subdomain/       # 子域名扫描
│   ├── loginfo/         # 日志处理
│   ├── randheader/      # 随机请求头生成
│   └── common/         # 通用工具
│
├── poc/                # POC 漏洞检测脚本
│   ├── weblogic/        # WebLogic POC
│   ├── struts2/         # Struts2 POC
│   ├── tomcat/          # Tomcat POC
│   ├── jboss/           # JBoss POC
│   ├── nexus/           # Nexus POC
│   └── Drupal/          # Drupal POC
│
├── AVWS/               # AWVS API 封装
│   └── API/            # AWVS API 模块
│
├── agent/              # AI Agent 核心
│   └── core.py         # Agent 工作流
│
├── sandbox/            # 代码执行沙箱
│   ├── core_executor.py # 核心执行器
│   └── executor_workspace/ # 工作空间
│
├── code_executor/      # 代码执行器
│   └── code_executor.py
│
├── database/          # 数据库文件
│   └── GeoLite2-ASN.mmdb
│
└── tests/             # 测试文件
```

## 核心文件说明

### 主入口文件

#### [main.py](main.py)
FastAPI 主应用入口文件，负责：

- 创建和配置 FastAPI 应用实例
- 设置 CORS 中间件
- 注册 API 路由
- 配置日志系统
- 管理应用生命周期（启动/关闭）
- 初始化数据库连接
- 验证外部服务连接（如 AWVS）
- 启动后台任务

**使用方法**:
```bash
python main.py
```

### 配置文件

#### [config.py](config.py)
应用配置管理文件，使用 Pydantic Settings 管理所有配置项：

**配置项**:
- `APP_NAME`: 应用名称
- `APP_VERSION`: 应用版本号
- `DEBUG`: 调试模式开关
- `HOST`: 服务器监听地址
- `PORT`: 服务器监听端口
- `DATABASE_URL`: 数据库连接字符串
- `LOG_LEVEL`: 日志级别
- `OPENAI_API_KEY`: OpenAI API 密钥
- `OPENAI_BASE_URL`: OpenAI API 基础 URL
- `MODEL_ID`: AI 模型 ID
- `OPENAI_API_KEY`: 通义千问 API 密钥
- `AWVS_API_URL`: AWVS API 地址
- `AWVS_API_KEY`: AWVS API 密钥
- `CODE_EXECUTOR_ENABLED`: 是否启用代码执行功能

**使用方法**:
```python
from config import settings
app_name = settings.APP_NAME
debug_mode = settings.DEBUG
```

### 数据库文件

#### [models.py](models.py)
数据库模型定义文件，使用 Tortoise-ORM 定义数据模型：

**主要模型**:
- `Task`: 扫描任务表
- `Report`: 扫描报告表
- `Vulnerability`: 漏洞信息表
- `AIChatInstance`: AI 对话实例表
- `AIChatMessage`: AI 对话消息表
- `AgentTask`: AI Agent 任务表
- `AgentResult`: AI Agent 结果表
- `SystemSettings`: 系统设置表

#### [database.py](database.py)
数据库连接和会话管理文件：

**主要函数**:
- `init_db()`: 初始化数据库连接
- `close_db()`: 关闭数据库连接
- `get_db_connection()`: 获取数据库连接
- `health_check()`: 数据库健康检查

### 任务执行

#### [task_executor.py](task_executor.py)
任务执行器，负责执行扫描任务并实时更新进度：

**主要功能**:
- 执行 POC 扫描任务
- 执行 AWVS 扫描任务
- 执行插件扫描任务
- 实时更新任务进度
- 标准化漏洞严重程度

**POC 支持** (共 13 种):
- WebLogic: CVE-2020-2551, CVE-2018-2628, CVE-2018-2894, CVE-2020-14756, CVE-2023-21839
- Struts2: S2-009, S2-032
- Tomcat: CVE-2017-12615, CVE-2022-22965, CVE-2022-47986
- JBoss: CVE-2017-12149
- Nexus: CVE-2020-10199
- Drupal: CVE-2018-7600

### API 路由模块

#### [api/scan.py](api/scan.py)
扫描功能相关的 API 路由：

**主要端点**:
- `POST /scan/port-scan`: 端口扫描
- `POST /scan/infoleak`: 信息泄露扫描
- `POST /scan/webside`: 网站侧边栏扫描
- `POST /scan/baseinfo`: 基础信息收集
- `POST /scan/webweight`: 网站权重查询
- `POST /scan/iplocating`: IP 定位
- `POST /scan/cdn`: CDN 检测
- `POST /scan/waf`: WAF 检测
- `POST /scan/cms`: CMS 识别
- `POST /scan/subdomain`: 子域名扫描
- `POST /scan/dir`: 目录扫描
- `POST /scan/comprehensive`: 综合扫描

#### [api/poc.py](api/poc.py)
POC 漏洞扫描 API 路由：

**主要端点**:
- `GET /poc/types`: 获取所有可用的 POC 类型
- `POST /poc/scan`: 创建 POC 扫描任务（异步执行）
- `POST /poc/scan/{poc_type}`: 执行单个 POC 漏洞扫描
- `GET /poc/info/{poc_type}`: 获取 POC 详细信息

**支持的 POC 类型** (13 种):
- `weblogic_cve_2020_2551`
- `weblogic_cve_2018_2628`
- `weblogic_cve_2018_2894`
- `weblogic_cve_2020_14756`
- `weblogic_cve_2023_21839`
- `struts2_009`
- `struts2_032`
- `tomcat_cve_2017_12615`
- `tomcat_cve_2022_22965`
- `tomcat_cve_2022_47986`
- `jboss_cve_2017_12149`
- `nexus_cve_2020_10199`
- `drupal_cve_2018_7600`

#### [api/awvs.py](api/awvs.py)
AWVS 集成 API 路由：

**主要端点**:
- `GET /awvs/scans`: 获取所有扫描任务列表
- `POST /awvs/scan`: 创建新的扫描任务
- `GET /awvs/vulnerabilities/{target_id}`: 获取目标漏洞列表
- `GET /awvs/vulnerability/{vuln_id}`: 获取漏洞详情
- `GET /awvs/vulnerabilities/rank`: 获取漏洞排名
- `GET /awvs/dashboard/stats`: 获取仪表板统计
- `POST /awvs/middleware/scan`: 中间件 POC 扫描

#### [api/ai.py](api/ai.py)
AI 对话 API 路由：

**主要端点**:
- `POST /ai/chat`: 创建对话实例
- `POST /ai/chat/{chat_id}/message`: 发送消息
- `GET /ai/chat/{chat_id}/history`: 获取对话历史
- `GET /ai/chats`: 获取所有对话实例

**支持的 AI 模型**:
- 通义千问 xop3qwen1b7 (默认)
- 其他 OpenAI 兼容模型（通过配置 MODEL_ID 切换）

#### [api/agent.py](api/agent.py)
AI Agent API 路由：

**主要端点**:
- `POST /agent/execute`: 执行 AI Agent 任务
- `GET /agent/tasks`: 获取 Agent 任务列表
- `GET /agent/tasks/{task_id}`: 获取任务详情
- `GET /agent/tools`: 获取可用工具列表

#### [api/settings.py](api/settings.py)
系统设置 API 路由：

**主要端点**:
- `GET /settings`: 获取系统设置
- `PUT /settings`: 更新系统设置
- `GET /settings/category/{category}`: 按分类获取设置
- `GET /settings/info`: 获取系统信息
- `GET /settings/stats`: 获取系统统计

#### [api/tasks.py](api/tasks.py)
任务管理 API 路由：

**主要端点**:
- `GET /tasks`: 获取任务列表
- `GET /tasks/{task_id}`: 获取任务详情
- `DELETE /tasks/{task_id}`: 取消/删除任务
- `GET /tasks/{task_id}/result`: 获取任务结果

#### [api/reports.py](api/reports.py)
报告生成 API 路由：

**主要端点**:
- `GET /reports`: 获取报告列表
- `GET /reports/{report_id}`: 获取报告详情
- `POST /reports/generate`: 生成新报告
- `DELETE /reports/{report_id}`: 删除报告

#### [api/kb.py](api/kb.py)
知识库 API 路由：

**主要端点**:
- `GET /kb`: 获取知识库条目
- `POST /kb`: 添加知识库条目
- `PUT /kb/{kb_id}`: 更新知识库条目
- `DELETE /kb/{kb_id}`: 删除知识库条目

#### [api/poc_gen.py](api/poc_gen.py)
POC 生成 API 路由：

**主要端点**:
- `POST /poc-gen/generate`: 生成 POC 脚本
- `POST /poc-gen/validate`: 验证 POC 脚本
- `GET /poc-gen/templates`: 获取 POC 模板

### 插件模块

#### [plugins/portscan/portscan.py](plugins/portscan/portscan.py)
端口扫描插件，使用 python-nmap 进行端口扫描。

**使用方法**:
```python
from plugins.portscan.portscan import ScanPort
scanner = ScanPort(target)
if scanner.run_scan():
    results = scanner.get_results()
```

#### [plugins/infoleak/infoleak.py](plugins/infoleak/infoleak.py)
信息泄露扫描插件，检测网站敏感信息泄露。

**使用方法**:
```python
from plugins.infoleak.infoleak import get_infoleak
results = get_infoleak(target)
```

#### [plugins/webside/webside.py](plugins/webside/webside.py)
网站侧边栏扫描插件，收集网站侧边栏信息。

**使用方法**:
```python
from plugins.webside.webside import get_side_info
results = get_side_info(target)
```

#### [plugins/baseinfo/baseinfo.py](plugins/baseinfo/baseinfo.py)
基础信息收集插件，收集网站基础信息。

**使用方法**:
```python
from plugins.baseinfo.baseinfo import getbaseinfo
results = getbaseinfo(target)
```

#### [plugins/webweight/webweight.py](plugins/webweight/webweight.py)
网站权重查询插件，查询网站权重信息。

**使用方法**:
```python
from plugins.webweight.webweight import get_web_weight
results = get_web_weight(target)
```

#### [plugins/iplocating/iplocating.py](plugins/iplocating/iplocating.py)
IP 定位插件，查询 IP 地址的地理位置。

**使用方法**:
```python
from plugins.iplocating.iplocating import get_locating
results = get_locating(target)
```

#### [plugins/cdnexist/cdnexist.py](plugins/cdnexist/cdnexist.py)
CDN 检测插件，检测网站是否使用 CDN。

**使用方法**:
```python
from plugins.cdnexist.cdnexist import iscdn
result = iscdn(target)
```

#### [plugins/waf/waf.py](plugins/waf/waf.py)
WAF 检测插件，检测网站是否使用 WAF。

**使用方法**:
```python
from plugins.waf.waf import getwaf
result = getwaf(target)
```

#### [plugins/whatcms/whatcms.py](plugins/whatcms/whatcms.py)
CMS 识别插件，识别网站使用的 CMS 系统。

**使用方法**:
```python
from plugins.whatcms.whatcms import getwhatcms
result = getwhatcms(target)
```

#### [plugins/subdomain/subdomain.py](plugins/subdomain/subdomain.py)
子域名扫描插件，扫描目标域名的子域名。

**使用方法**:
```python
from plugins.subdomain.subdomain import get_subdomain
results = get_subdomain(target)
```

#### [plugins/loginfo/loginfo.py](plugins/loginfo/loginfo.py)
日志处理插件，提供自定义日志处理器，支持按天自动切割日志文件。

**使用方法**:
```python
from plugins.loginfo.loginfo import LogHandler
log = LogHandler('test', level=logging.INFO, stream=True, file=True)
log.info('这是一条测试日志')
```

#### [plugins/randheader/randheader.py](plugins/randheader/randheader.py)
随机请求头生成插件，生成随机的 User-Agent 和伪造 IP。

**使用方法**:
```python
from plugins.randheader.randheader import get_random_headers
headers = get_random_headers(conn_type="keep-alive")
```

### POC 模块

#### [poc/weblogic/](poc/weblogic/)
WebLogic POC 漏洞检测脚本：

- `cve_2020_2551_poc.py`: WebLogic CVE-2020-2551 反序列化漏洞
- `cve_2018_2628_poc.py`: WebLogic CVE-2018-2628 反序列化漏洞
- `cve_2018_2894_poc.py`: WebLogic CVE-2018-2894 任意文件上传漏洞
- `CVE-2020-14756.py`: WebLogic CVE-2020-14756 远程代码执行漏洞
- `CVE-2023-21839.py`: WebLogic CVE-2023-21839 远程代码执行漏洞

#### [poc/struts2/](poc/struts2/)
Struts2 POC 漏洞检测脚本：

- `struts2_009_poc.py`: Struts2 S2-009 远程代码执行漏洞
- `struts2_032_poc.py`: Struts2 S2-032 远程代码执行漏洞

#### [poc/tomcat/](poc/tomcat/)
Tomcat POC 漏洞检测脚本：

- `cve_2017_12615_poc.py`: Tomcat CVE-2017-12615 任意文件写入漏洞
- `CVE-2022-22965.py`: Spring Framework CVE-2022-22965 远程代码执行漏洞 (Spring4Shell)
- `CVE-2022-47986.py`: Aspera Faspex CVE-2022-47986 远程代码执行漏洞

#### [poc/jboss/](poc/jboss/)
JBoss POC 漏洞检测脚本：

- `cve_2017_12149_poc.py`: JBoss CVE-2017-12149 反序列化漏洞

#### [poc/nexus/](poc/nexus/)
Nexus POC 漏洞检测脚本：

- `cve_2020_10199_poc.py`: Nexus CVE-2020-10199 远程代码执行漏洞

#### [poc/Drupal/](poc/Drupal/)
Drupal POC 漏洞检测脚本：

- `cve_2018_7600_poc.py`: Drupal CVE-2018-7600 远程代码执行漏洞

### AI Agent 核心

#### [agent/core.py](agent/core.py)
AI Agent 核心工作流，使用 LangGraph 构建智能任务执行流程。

**主要功能**:
- 任务规划和分解
- 工具调用和管理
- 结果验证和反馈
- 多轮对话和记忆管理

### 代码执行沙箱

#### [sandbox/core_executor.py](sandbox/core_executor.py)
代码执行沙箱核心，提供安全的代码执行环境。

**主要功能**:
- 代码隔离执行
- 资源限制（CPU、内存、时间）
- 文件系统隔离
- 网络访问控制

#### [code_executor/code_executor.py](code_executor/code_executor.py)
代码执行器，提供代码执行 API 和管理。

**主要功能**:
- 代码执行请求处理
- 执行结果返回
- 执行历史记录
- 超时和错误处理

## 安装配置

### 环境要求

- Python 3.11+
- SQLite / MySQL / PostgreSQL
- AWVS (可选)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd backend
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**

创建 `.env` 文件：
```env
APP_NAME=WebScan AI Security Platform
APP_VERSION=1.0.0
DEBUG=False
HOST=127.0.0.1
PORT=3000
DATABASE_URL=sqlite://./data/webscan.db
LOG_LEVEL=INFO
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://maas-api.cn-huabei-1.xf-yun.com/v2
MODEL_ID=xop3qwen1b7
OPENAI_API_KEY=your_OPENAI_API_KEY
AWVS_API_URL=https://127.0.0.1:3443
AWVS_API_KEY=your_awvs_api_key
CODE_EXECUTOR_ENABLED=True
```

5. **初始化数据库**
```bash
python -c "from database import init_db; import asyncio; asyncio.run(init_db())"
```

## 使用方法

### 启动服务

```bash
python main.py
```

服务将在 `http://127.0.0.1:8888` 启动。

### 访问 API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://127.0.0.1:8888/docs
- ReDoc: http://127.0.0.1:8888/redoc

### 健康检查

```bash
curl http://127.0.0.1:8888/health
```

返回示例：
```json
{
  "status": "healthy"
}
```

## API 端点

### 扫描功能

| 方法 | 端点 | 描述 |
|------|--------|------|
| POST | `/api/scan/port-scan` | 端口扫描 |
| POST | `/api/scan/infoleak` | 信息泄露扫描 |
| POST | `/api/scan/webside` | 网站侧边栏扫描 |
| POST | `/api/scan/baseinfo` | 基础信息收集 |
| POST | `/api/scan/webweight` | 网站权重查询 |
| POST | `/api/scan/iplocating` | IP 定位 |
| POST | `/api/scan/cdn` | CDN 检测 |
| POST | `/api/scan/waf` | WAF 检测 |
| POST | `/api/scan/cms` | CMS 识别 |
| POST | `/api/scan/subdomain` | 子域名扫描 |
| POST | `/api/scan/dir` | 目录扫描 |
| POST | `/api/scan/comprehensive` | 综合扫描 |

### POC 扫描

| 方法 | 端点 | 描述 |
|------|--------|------|
| GET | `/api/poc/types` | 获取所有可用的 POC 类型 |
| POST | `/api/poc/scan` | 创建 POC 扫描任务（异步执行） |
| POST | `/api/poc/scan/{poc_type}` | 执行单个 POC 漏洞扫描 |
| GET | `/api/poc/info/{poc_type}` | 获取 POC 详细信息 |

### AWVS 集成

| 方法 | 端点 | 描述 |
|------|--------|------|
| GET | `/api/awvs/scans` | 获取所有扫描任务列表 |
| POST | `/api/awvs/scan` | 创建新的扫描任务 |
| GET | `/api/awvs/vulnerabilities/{target_id}` | 获取目标漏洞列表 |
| GET | `/api/awvs/vulnerability/{vuln_id}` | 获取漏洞详情 |
| GET | `/api/awvs/vulnerabilities/rank` | 获取漏洞排名 |
| GET | `/api/awvs/dashboard/stats` | 获取仪表板统计 |
| POST | `/api/awvs/middleware/scan` | 中间件 POC 扫描 |

### AI 对话

| 方法 | 端点 | 描述 |
|------|--------|------|
| POST | `/api/ai/chat` | 创建对话实例 |
| POST | `/api/ai/chat/{chat_id}/message` | 发送消息 |
| GET | `/api/ai/chat/{chat_id}/history` | 获取对话历史 |
| GET | `/api/ai/chats` | 获取所有对话实例 |

### AI Agent

| 方法 | 端点 | 描述 |
|------|--------|------|
| POST | `/api/agent/execute` | 执行 AI Agent 任务 |
| GET | `/api/agent/tasks` | 获取 Agent 任务列表 |
| GET | `/api/agent/tasks/{task_id}` | 获取任务详情 |
| GET | `/api/agent/tools` | 获取可用工具列表 |

### 系统设置

| 方法 | 端点 | 描述 |
|------|--------|------|
| GET | `/api/settings` | 获取系统设置 |
| PUT | `/api/settings` | 更新系统设置 |
| GET | `/api/settings/category/{category}` | 按分类获取设置 |
| GET | `/api/settings/info` | 获取系统信息 |
| GET | `/api/settings/stats` | 获取系统统计 |

### 任务管理

| 方法 | 端点 | 描述 |
|------|--------|------|
| GET | `/api/tasks` | 获取任务列表 |
| GET | `/api/tasks/{task_id}` | 获取任务详情 |
| DELETE | `/api/tasks/{task_id}` | 取消/删除任务 |
| GET | `/api/tasks/{task_id}/result` | 获取任务结果 |

### 报告生成

| 方法 | 端点 | 描述 |
|------|--------|------|
| GET | `/api/reports` | 获取报告列表 |
| GET | `/api/reports/{report_id}` | 获取报告详情 |
| POST | `/api/reports/generate` | 生成新报告 |
| DELETE | `/api/reports/{report_id}` | 删除报告 |

## 开发指南

### 添加新的扫描插件

1. 在 `plugins/` 目录下创建新插件目录
2. 实现扫描逻辑
3. 在 `api/scan.py` 中添加对应的 API 端点
4. 在 `task_executor.py` 中添加插件调用逻辑

### 添加新的 POC

1. 在 `poc/` 对应目录下创建 POC 脚本
2. 实现 `poc(url, timeout=10)` 函数
3. 在 `poc/__init__.py` 中导出 POC 函数
4. 在 `api/poc.py` 中添加 POC 映射和信息

### 数据库迁移

```bash
# 创建迁移
aerich init -t config.TORTOISE_ORM

# 生成迁移文件
aerich migrate

# 应用迁移
aerich upgrade
```

### 运行测试

```bash
python -m pytest tests/
```

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

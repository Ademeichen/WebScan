# WebScan AI Security Platform

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Vue](https://img.shields.io/badge/vue-3.5+-brightgreen.svg)
![Vite](https://img.shields.io/badge/vite-7.2+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**AI驱动的Web安全扫描平台**

一个功能强大的Web应用安全扫描平台，集成POC漏洞扫描、端口扫描、AWVS集成等多种安全检测能力

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [项目结构](#-项目结构) • [API文档](#-api文档)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [功能特性](#-功能特性)
- [技术栈](#-技术栈)
- [快速开始](#-快速开始)
- [项目结构](#-项目结构)
- [配置说明](#-配置说明)
- [API文档](#-api文档)
- [开发指南](#-开发指南)
- [部署指南](#-部署指南)
- [常见问题](#-常见问题)

---

## 🎯 项目简介

WebScan AI Security Platform 是一个基于AI技术的Web应用安全扫描平台，旨在帮助开发者和安全专业人员快速发现和修复Web应用中的安全漏洞。

### 核心特点

- 🔍 **全面的漏洞检测** - 支持POC漏洞扫描、端口扫描、AWVS集成等多种扫描方式
- 🤖 **AI智能分析** - 利用AI技术进行漏洞分析和风险评估
- 📊 **可视化报告** - 提供直观的扫描结果和详细的漏洞报告
- 🚀 **高性能架构** - 基于FastAPI和Vue 3构建，提供快速响应和流畅体验
- 🔧 **易于扩展** - 模块化设计，支持自定义扫描插件和规则

---

## ✨ 功能特性

### 核心功能

| 功能模块 | 描述 | 状态 |
|---------|------|------|
| **POC漏洞扫描** | 基于POC的漏洞检测，支持多种常见漏洞类型 | ✅ 已实现 |
| **端口扫描** | 快速扫描目标端口，识别开放服务和潜在风险 | ✅ 已实现 |
| **AWVS集成** | 集成Acunetix Web Vulnerability Scanner进行深度扫描 | ✅ 已实现 |
| **漏洞管理** | 统一管理扫描发现的漏洞，支持分类和优先级排序 | ✅ 已实现 |
| **扫描报告** | 生成详细的扫描报告，支持多种格式导出 | ✅ 已实现 |
| **实时监控** | 实时监控扫描进度和结果 | ✅ 已实现 |

### 高级特性

- 🎯 **智能扫描策略** - 根据目标类型自动选择最优扫描策略
- 🔔 **实时通知** - 扫描完成和发现高危漏洞时及时通知
- 📈 **趋势分析** - 漏洞趋势分析和安全评分
- 🔄 **定时扫描** - 支持定时任务和周期性扫描
- 👥 **多用户支持** - 支持多用户和权限管理
- 📱 **响应式界面** - 适配桌面、平板和移动设备

---

## 🛠 技术栈

### 后端技术

```yaml
核心框架:
  - FastAPI: 0.104.1          # 现代化Python Web框架
  - Uvicorn: 0.24.0           # ASGI服务器
  - Python-Multipart: 0.0.6   # 文件上传支持

数据库:
  - Tortoise-ORM: 0.20.0      # 异步ORM框架
  - Aerich: 0.7.2             # 数据库迁移工具
  - SQLite                    # 默认数据库（支持MySQL/PostgreSQL）

数据验证:
  - Pydantic: 2.5.0           # 数据验证和序列化
  - Pydantic-Settings: 2.1.0 # 配置管理

HTTP客户端:
  - HTTPX: 0.25.2             # 异步HTTP客户端
  - Requests: 2.31.0          # 同步HTTP客户端

安全扫描:
  - Nmap: 0.6.1               # 端口扫描
  - BeautifulSoup4: 4.12.2    # HTML解析
  - LXML: 4.9.3               # XML/HTML处理
  - DNSLib: 0.9.24            # DNS解析
  - GeoIP2: 4.7.0             # IP地理位置

工具库:
  - Loguru: 0.7.2             # 日志记录
  - Python-Dotenv: 1.0.0     # 环境变量管理
  - Colorama: 0.4.6           # 终端彩色输出
  - TQDM: 4.66.1              # 进度条
```

### 前端技术

```yaml
核心框架:
  - Vue: 3.5.24               # Vue 3核心框架
  - Vue Router: 4.2.5         # 官方路由管理器
  - Pinia: 2.3.0              # 状态管理库

构建工具:
  - Vite: 7.2.2               # 下一代前端构建工具
  - @Vitejs/Plugin-Vue: 6.0.1 # Vue 3插件

HTTP客户端:
  - Axios: 1.7.9              # HTTP请求库

开发工具:
  - ESLint: 9.17.0            # 代码检查
  - ESLint-Plugin-Vue: 9.31.0 # Vue代码规范
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- Node.js 16.0 或更高版本
- npm 7.0 或更高版本（或 yarn 1.22+）

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/yourusername/webscan-ai.git
cd webscan-ai
```

#### 2. 后端安装

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -c "from database import init_db; import asyncio; asyncio.run(init_db())"
```

#### 3. 配置后端

编辑 `backend/config.py` 文件，根据需要修改配置：

```python
# 服务器配置
HOST: str = "127.0.0.1"
PORT: int = 8888

# AWVS配置（如果使用AWVS）
AWVS_API_URL: str = "https://127.0.0.1:3443"
AWVS_API_KEY: str = "your-awvs-api-key"

# 数据库配置
DATABASE_URL: str = "sqlite://./webscan.db"
```

#### 4. 启动后端服务

```bash
# 开发模式
python main.py

# 或使用uvicorn
uvicorn main:app --host 127.0.0.1 --port 8888 --reload
```

后端服务将运行在：http://127.0.0.1:8888

#### 5. 前端安装

```bash
# 打开新终端，进入前端目录
cd front

# 安装依赖
npm install
```

#### 6. 配置前端

编辑 `front/.env.development` 文件：

```env
VITE_API_BASE_URL=http://127.0.0.1:8888/api
```

#### 7. 启动前端服务

```bash
npm run dev
```

前端服务将运行在：http://localhost:5173

#### 8. 访问应用

在浏览器中打开 http://localhost:5173 即可使用WebScan AI Security Platform

---

## 📁 项目结构

```
webscan-ai/
├── backend/                      # 后端项目
│   ├── api/                     # API路由
│   │   ├── __init__.py
│   │   ├── awvs.py             # AWVS相关API
│   │   ├── poc.py              # POC扫描API
│   │   ├── port_scan.py        # 端口扫描API
│   │   └── ...                 # 其他API模块
│   ├── AVWS/                   # AWVS集成模块
│   ├── database/               # 数据库相关
│   │   └── __init__.py
│   ├── plugins/                # 扫描插件
│   ├── poc/                    # POC漏洞库
│   ├── config.py               # 配置文件
│   ├── database.py             # 数据库初始化
│   ├── main.py                 # 应用入口
│   ├── models.py               # 数据模型
│   ├── requirements.txt        # Python依赖
│   ├── pyproject.toml         # 项目配置
│   └── AWVS_API_README.md      # AWVS API文档
│
├── front/                      # 前端项目
│   ├── src/
│   │   ├── components/         # 公共组件
│   │   ├── views/              # 页面视图
│   │   │   ├── Dashboard.vue
│   │   │   ├── ScanTasks.vue
│   │   │   ├── VulnerabilityResults.vue
│   │   │   ├── VulnerabilityDetail.vue
│   │   │   ├── Reports.vue
│   │   │   ├── Settings.vue
│   │   │   └── AwvsScan.vue    # AWVS扫描页面
│   │   ├── router/             # 路由配置
│   │   ├── utils/              # 工具函数
│   │   ├── style.css           # 全局样式
│   │   ├── App.vue             # 根组件
│   │   └── main.js             # 应用入口
│   ├── docs/                   # 前端文档
│   ├── index.html              # HTML模板
│   ├── package.json            # 项目配置
│   ├── vite.config.js          # Vite配置
│   └── README.md               # 前端说明文档
│
├── logs/                       # 日志目录
├── data/                       # 数据目录
├── README.md                   # 项目说明文档
└── .gitignore                  # Git忽略文件
```

---

## ⚙️ 配置说明

### 后端配置

主要配置文件：`backend/config.py`

```python
class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "WebScan AI Security Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8888
    
    # CORS配置
<<<<<<< HEAD
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:8888"]
=======
<<<<<<< HEAD
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:8888"]
=======
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
    
    # 数据库配置
    DATABASE_URL: str = "sqlite://./webscan.db"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # 扫描配置
    MAX_CONCURRENT_SCANS: int = 5
    SCAN_TIMEOUT: int = 300
    
    # AWVS配置
    AWVS_API_URL: str = "https://127.0.0.1:3443"
    AWVS_API_KEY: str = "your-api-key"
```

### 前端配置

主要配置文件：`front/vite.config.js`

```javascript
export default defineConfig({
  server: {
    port: 5173,
    host: true,
    open: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8888',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
```

环境变量配置：`front/.env.development`

```env
VITE_API_BASE_URL=http://127.0.0.1:8888/api
```

---

## 📚 API文档

### 启动API文档

启动后端服务后，访问以下地址查看自动生成的API文档：

- **Swagger UI**: http://127.0.0.1:8888/docs
- **ReDoc**: http://127.0.0.1:8888/redoc

### 主要API端点

#### 健康检查

```http
GET /health
```

#### POC扫描

```http
POST /api/poc/scan
Content-Type: application/json

{
<<<<<<< HEAD
  "target": "https://www.baidu.com",
=======
<<<<<<< HEAD
  "target": "https://www.baidu.com",
=======
  "target": "http://example.com",
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  "poc_list": ["poc1", "poc2"]
}
```

#### 端口扫描

```http
POST /api/port/scan
Content-Type: application/json

{
<<<<<<< HEAD
  "target": "www.baidu.com",
=======
<<<<<<< HEAD
  "target": "www.baidu.com",
=======
  "target": "example.com",
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  "ports": [80, 443, 8080]
}
```

#### AWVS扫描

```http
POST /api/awvs/scan
Content-Type: application/json

{
<<<<<<< HEAD
  "url": "https://www.baidu.com",
=======
<<<<<<< HEAD
  "url": "https://www.baidu.com",
=======
  "url": "http://example.com",
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  "scan_type": "full_scan"
}
```

#### 获取扫描任务

```http
GET /api/scan-tasks
```

#### 获取漏洞列表

```http
GET /api/vulnerabilities
```

详细API文档请参考：[后端API文档](backend/docs/API.md)

---

## 💻 开发指南

### 后端开发

#### 添加新的API端点

1. 在 `backend/api/` 目录下创建或编辑API模块
2. 定义路由和处理函数
3. 在 `backend/api/__init__.py` 中注册路由

示例：

```python
# backend/api/my_feature.py
from fastapi import APIRouter
from models import APIResponse

router = APIRouter()

@router.get("/my-feature")
async def get_my_feature():
    return APIResponse(
        code=200,
        message="Success",
        data={"feature": "data"}
    )
```

#### 添加新的扫描插件

1. 在 `backend/plugins/` 目录下创建插件文件
2. 实现扫描逻辑
3. 在主程序中注册插件

### 前端开发

#### 添加新页面

1. 在 `front/src/views/` 目录下创建Vue组件
2. 在 `front/src/router/index.js` 中添加路由

示例：

```vue
<!-- front/src/views/NewPage.vue -->
<template>
  <div class="page-container">
    <h1>新页面</h1>
  </div>
</template>

<script>
export default {
  name: 'NewPage'
}
</script>
```

```javascript
// front/src/router/index.js
import NewPage from '@/views/NewPage.vue'

const routes = [
  {
    path: '/new-page',
    name: 'NewPage',
    component: NewPage
  }
]
```

详细开发指南请参考：
- [后端开发文档](backend/docs/DEVELOPMENT.md)
- [前端开发文档](front/docs/DEVELOPMENT.md)

---

## 🚀 部署指南

### 后端部署

#### 使用Docker

```bash
# 构建镜像
docker build -t webscan-ai-backend ./backend

# 运行容器
docker run -d -p 8888:8888 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  webscan-ai-backend
```

#### 使用systemd（Linux）

创建服务文件 `/etc/systemd/system/webscan-ai.service`：

```ini
[Unit]
Description=WebScan AI Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/webscan-ai/backend
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start webscan-ai
sudo systemctl enable webscan-ai
```

### 前端部署

#### 构建生产版本

```bash
cd front
npm run build
```

#### 使用Nginx

配置Nginx：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/front/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## ❓ 常见问题

### 1. 后端启动失败

**问题**: 端口被占用

**解决方案**:
```bash
# Windows
netstat -ano | findstr :8888
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -ti:8888 | xargs kill -9
```

### 2. 数据库连接错误

**问题**: 无法连接到数据库

**解决方案**:
- 检查数据库配置是否正确
- 确保数据库文件有正确的权限
- 尝试删除数据库文件重新初始化

### 3. AWVS连接失败

**问题**: 无法连接到AWVS服务

**解决方案**:
- 确认AWVS服务正在运行
- 检查AWVS API URL和密钥配置
- 确认网络连接正常

### 4. 前端无法连接后端

**问题**: API请求失败

**解决方案**:
- 检查后端服务是否正常运行
- 确认API地址配置正确
- 检查CORS配置
- 查看浏览器控制台错误信息

### 5. 扫描任务卡住

**问题**: 扫描任务长时间无响应

**解决方案**:
- 检查目标网站是否可访问
- 查看后端日志获取详细信息
- 增加扫描超时时间配置
- 尝试减少并发扫描数量

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

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

- 后端遵循 PEP 8 代码规范
- 前端遵循 Vue 3 风格指南
- 提交信息使用清晰的描述

---

## 📞 联系方式

- 项目主页: https://github.com/yourusername/webscan-ai
- 问题反馈: https://github.com/yourusername/webscan-ai/issues
<<<<<<< HEAD
- 邮箱: your.email@www.baidu.com
=======
<<<<<<< HEAD
- 邮箱: your.email@www.baidu.com
=======
- 邮箱: your.email@example.com
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng

---

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！

特别感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue.js](https://vuejs.org/)
- [Vite](https://vitejs.dev/)
- [Acunetix](https://www.acunetix.com/)

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 ⭐️**

Made with ❤️ by WebScan AI Team

</div>

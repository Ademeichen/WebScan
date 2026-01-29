# WebScan AI - 前端项目

<div align="center">

![Vue](https://img.shields.io/badge/vue-3.5+-brightgreen.svg)
![Vite](https://img.shields.io/badge/vite-7.2+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**WebScan AI Security Platform 前端界面**

基于 Vue 3 + Vite 构建的现代化Web应用安全扫描平台前端

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [项目结构](#-项目结构) • [开发指南](#-开发指南)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [功能特性](#-功能特性)
- [技术栈](#-技术栈)
- [快速开始](#-快速开始)
- [项目结构](#-项目结构)
- [开发指南](#-开发指南)
- [组件说明](#-组件说明)
- [API集成](#-api集成)
- [样式系统](#-样式系统)
- [部署指南](#-部署指南)
- [常见问题](#-常见问题)

---

## 🎯 项目简介

WebScan AI 前端是 WebScan AI Security Platform 的用户界面部分，提供直观、专业的安全扫描管理界面。采用现代化的 Vue 3 框架构建，具有响应式设计，支持桌面、平板和手机设备。

### 核心特点

- 🎨 **专业简洁的界面设计** - 符合安全工具的专业形象
- 📊 **智能数据可视化** - 直观的图表和统计信息
- 🚀 **高性能渲染** - 基于 Vite 的快速构建和热更新
- 📱 **完全响应式** - 适配各种屏幕尺寸
- 🔧 **模块化架构** - 组件化开发，易于维护和扩展

---

## ✨ 功能特性

### 核心功能模块

| 模块 | 功能描述 | 状态 |
|------|---------|------|
| **仪表盘** | 实时显示扫描统计、漏洞趋势、最新结果 | ✅ 已实现 |
| **扫描任务管理** | 创建、监控、管理扫描任务 | ✅ 已实现 |
| **漏洞结果展示** | 按优先级展示漏洞，支持筛选和搜索 | ✅ 已实现 |
| **漏洞详情** | 详细的漏洞信息、技术细节、修复建议 | ✅ 已实现 |
| **报告生成** | 支持HTML、PDF、JSON多种格式报告 | ✅ 已实现 |
| **系统设置** | 灵活的配置选项和规则管理 | ✅ 已实现 |
| **AWVS扫描** | 集成Acunetix Web Vulnerability Scanner | ✅ 已实现 |

### 交互特性

- 🔔 **实时通知** - 扫描进度和结果实时推送
- 🔍 **智能搜索** - 快速查找漏洞和任务
- 📋 **批量操作** - 支持多选和批量处理
- 🎯 **快捷操作** - 一键跳转和快速访问
- 💾 **本地缓存** - 提升用户体验和性能

---

## 🛠 技术栈

### 核心框架

```json
{
  "vue": "^3.5.24",           // Vue 3 核心框架
  "vue-router": "^4.2.5",     // 官方路由管理器
  "pinia": "^2.3.0",          // 状态管理库
  "axios": "^1.7.9"           // HTTP 客户端
}
```

### 构建工具

```json
{
  "vite": "^7.2.2",                    // 下一代前端构建工具
  "@vitejs/plugin-vue": "^6.0.1"      // Vue 3 插件
}
```

### 开发工具

```json
{
  "eslint": "^9.17.0",                // 代码检查工具
  "eslint-plugin-vue": "^9.31.0"      // Vue 代码规范插件
}
```

### 技术特点

- **Composition API** - 使用 Vue 3 的组合式 API
- **单文件组件** - .vue 文件格式
- **模块化路由** - 基于文件的路由配置
- **CSS 变量** - 现代化的样式系统
- **ES6+** - 使用现代 JavaScript 特性
- **Axios** - HTTP 请求封装
- **Pinia** - 状态管理

---

## 🚀 快速开始

### 环境要求

- Node.js 16.0 或更高版本
- npm 7.0 或更高版本（或 yarn 1.22+）

### 安装步骤

#### 1. 安装依赖

```bash
npm install
```

或使用 yarn：

```bash
yarn install
```

#### 2. 开发模式

```bash
npm run dev
```

开发服务器将运行在：http://localhost:5173

#### 3. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录

#### 4. 预览生产版本

```bash
npm run preview
```

---

## 📁 项目结构

```
front/
├── public/                      # 静态资源
│   └── favicon.ico             # 网站图标
├── src/                        # 源代码目录
│   ├── components/             # 公共组件
│   │   └── AppLayout.vue       # 主布局组件
│   ├── views/                  # 页面视图
│   │   ├── Dashboard.vue       # 仪表盘页面
│   │   ├── ScanTasks.vue       # 扫描任务管理
│   │   ├── VulnerabilityResults.vue  # 漏洞结果列表
│   │   ├── VulnerabilityDetail.vue   # 漏洞详情
│   │   ├── Reports.vue         # 报告管理
│   │   ├── Settings.vue        # 系统设置
│   │   └── AwvsScan.vue        # AWVS扫描页面
│   ├── router/                 # 路由配置
│   │   └── index.js            # 路由定义
│   ├── utils/                  # 工具函数
│   │   └── api.js              # API 请求封装
│   ├── data/                   # 示例数据
│   │   └── mockData.js         # 模拟数据
│   ├── style.css               # 全局样式
│   ├── App.vue                 # 根组件
│   └── main.js                 # 应用入口
├── docs/                       # 文档
│   └── API.md                  # API 接口文档
├── index.html                  # HTML 模板
├── package.json                # 项目配置
├── vite.config.js              # Vite 配置
├── .env                        # 环境变量
├── .env.development            # 开发环境变量
├── .env.production             # 生产环境变量
├── README.md                   # 项目说明
└── .gitignore                  # Git 忽略文件
```

---

## 💻 开发指南

### 开发环境配置

#### 1. 配置 API 地址

在 `src/utils/api.js` 中配置后端 API 地址：

```javascript
const API_BASE_URL = 'http://127.0.0.1:8888/api';
```

或在 `.env.development` 文件中配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8888/api
```

#### 2. 开发模式启动

```bash
npm run dev
```

访问 http://localhost:5173 查看应用

### 添加新页面

#### 1. 创建页面组件

在 `src/views/` 目录下创建新的 Vue 组件：

```vue
<template>
  <div class="page-container">
    <h1>新页面标题</h1>
    <!-- 页面内容 -->
  </div>
</template>

<script>
export default {
  name: 'NewPage',
  // 组件逻辑
}
</script>

<style scoped>
/* 页面样式 */
</style>
```

#### 2. 配置路由

在 `src/router/index.js` 中添加路由：

```javascript
import NewPage from '../views/NewPage.vue'

const routes = [
  // 其他路由...
  {
    path: '/new-page',
    name: 'NewPage',
    component: NewPage
  }
]
```

### 添加新组件

#### 1. 创建组件

在 `src/components/` 目录下创建组件：

```vue
<template>
  <div class="my-component">
    <!-- 组件内容 -->
  </div>
</template>

<script>
export default {
  name: 'MyComponent',
  props: {
    // 组件属性
  },
  setup() {
    // 组件逻辑
    return {}
  }
}
</script>

<style scoped>
/* 组件样式 */
</style>
```

#### 2. 使用组件

在页面中引入和使用：

```vue
<template>
  <div>
    <MyComponent />
  </div>
</template>

<script>
import MyComponent from '@/components/MyComponent.vue'

export default {
  components: {
    MyComponent
  }
}
</script>
```

---

## 📦 组件说明

### AppLayout.vue

主布局组件，包含：
- 顶部导航栏
- 侧边菜单
- 内容区域
- 页脚

### Dashboard.vue

仪表盘页面，展示：
- 统计数据卡片
- 趋势图表
- 最新扫描结果
- 快速操作按钮

### ScanTasks.vue

扫描任务管理页面，功能：
- 任务列表展示
- 创建新任务
- 任务状态监控
- 批量操作

### VulnerabilityResults.vue

漏洞结果列表页面，功能：
- 漏洞列表展示
- 多维度筛选
- 关键词搜索
- 状态管理

### VulnerabilityDetail.vue

漏洞详情页面，展示：
- 基本信息
- 技术细节
- AI 分析结果
- 修复建议

### Reports.vue

报告管理页面，功能：
- 报告列表
- 生成新报告
- 下载报告
- 报告预览

### Settings.vue

系统设置页面，功能：
- 基本配置
- 扫描规则
- 通知设置
- 用户信息

### AwvsScan.vue

AWVS扫描页面，功能：
- 创建AWVS扫描任务
- 监控扫描进度
- 查看扫描结果
- 管理扫描配置

---

## 🔌 API 集成

### API 请求封装

在 `src/utils/api.js` 中封装了 API 请求：

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8888/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(config => {
  // 添加 token 等
  return config
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    // 错误处理
    return Promise.reject(error)
  }
)

export default api
```

### API 调用示例

```javascript
import api from '@/utils/api'

// 获取仪表盘数据
export async function getDashboardStats() {
  return await api.get('/dashboard/stats')
}

// 获取扫描任务列表
export async function getScanTasks(params) {
  return await api.get('/scan-tasks', { params })
}

// 创建扫描任务
export async function createScanTask(data) {
  return await api.post('/scan-tasks', data)
}

// 获取漏洞详情
export async function getVulnerabilityDetail(id) {
  return await api.get(`/vulnerabilities/${id}`)
}

// AWVS扫描
export async function createAwvsScan(data) {
  return await api.post('/awvs/scan', data)
}

// 获取AWVS扫描任务
export async function getAwvsScans() {
  return await api.get('/awvs/scans')
}
```

### TODO 标识说明

前端代码中所有需要对接后端 API 的地方都标记了 `TODO` 注释：

```javascript
// TODO: 替换为真实的API调用
// TODO: 从API获取数据 - GET /api/endpoint
```

这些标识帮助开发者快速定位需要替换为真实 API 调用的位置。

---

## 🎨 样式系统

### CSS 变量

在 `src/style.css` 中定义了全局 CSS 变量：

```css
:root {
  /* 主色调 */
  --primary-color: #1a3a6c;
  --secondary-color: #4a90e2;
  
  /* 风险等级颜色 */
  --high-risk: #e74c3c;
  --medium-risk: #f5a623;
  --low-risk: #f1c40f;
  
  /* 状态颜色 */
  --success-color: #2ecc71;
  --warning-color: #f5a623;
  --danger-color: #e74c3c;
  --info-color: #3498db;
  
  /* 背景颜色 */
  --background-color: #f8f9fa;
  --card-background: #ffffff;
  --border-color: #e1e4e8;
  
  /* 文字颜色 */
  --text-primary: #2c3e50;
  --text-secondary: #7f8c8d;
  --text-muted: #95a5a6;
  
  /* 间距 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  /* 圆角 */
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
  
  /* 阴影 */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
}
```

### 色彩系统

| 类型 | 颜色代码 | 用途 | CSS 变量 |
|------|----------|------|---------|
| 主色 | `#1a3a6c` | 标题、关键按钮 | `--primary-color` |
| 辅助色 | `#4a90e2` | 操作按钮、链接 | `--secondary-color` |
| 高危 | `#e74c3c` | 高危漏洞标识 | `--high-risk` |
| 中危 | `#f5a623` | 中危漏洞标识 | `--medium-risk` |
| 低危 | `#f1c40f` | 低危漏洞标识 | `--low-risk` |
| 成功 | `#2ecc71` | 成功状态 | `--success-color` |
| 背景 | `#f8f9fa` | 主背景色 | `--background-color` |
| 卡片 | `#ffffff` | 卡片背景 | `--card-background` |

### 响应式断点

```css
/* 移动设备 */
@media (max-width: 768px) {
  /* 移动端样式 */
}

/* 平板设备 */
@media (min-width: 769px) and (max-width: 1024px) {
  /* 平板样式 */
}

/* 桌面设备 */
@media (min-width: 1025px) {
  /* 桌面样式 */
}
```

---

## 🚀 部署指南

### 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录

### 部署到 Nginx

#### 1. 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

#### 2. 配置 Nginx

创建配置文件 `/etc/nginx/sites-available/webscan-ai`：

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
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3. 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/webscan-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 部署到 Vercel

#### 1. 安装 Vercel CLI

```bash
npm install -g vercel
```

#### 2. 部署

```bash
vercel
```

### 部署到 Netlify

#### 1. 构建项目

```bash
npm run build
```

#### 2. 部署

```bash
netlify deploy --prod --dir=dist
```

### 部署到 Docker

创建 `Dockerfile`：

```dockerfile
# 构建阶段
FROM node:18-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 生产阶段
FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

构建和运行：

```bash
docker build -t webscan-ai-front .
docker run -d -p 80:80 webscan-ai-front
```

---

## ❓ 常见问题

### 1. 安装依赖失败

**问题**: npm install 报错

**解决方案**:
```bash
# 清除缓存
npm cache clean --force

# 删除 node_modules 和 package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

### 2. 开发服务器启动失败

**问题**: 端口 5173 被占用

**解决方案**:
```bash
# 修改 vite.config.js 中的端口配置
export default defineConfig({
  server: {
    port: 3000  // 修改为其他端口
  }
})
```

### 3. 构建失败

**问题**: npm run build 报错

**解决方案**:
```bash
# 检查 Node.js 版本
node --version  # 应该 >= 16.0

# 更新依赖
npm update

# 清除缓存重新构建
npm run build
```

### 4. API 请求失败

**问题**: 前端无法连接后端

**解决方案**:
1. 检查后端服务是否正常运行
2. 检查 API 地址配置是否正确
3. 检查 CORS 配置
4. 查看浏览器控制台错误信息

### 5. 样式不生效

**问题**: 修改样式后没有效果

**解决方案**:
```bash
# 清除浏览器缓存
# 或使用硬刷新 Ctrl + Shift + R

# 清除构建缓存
rm -rf node_modules/.vite
npm run dev
```

### 6. 路由刷新404

**问题**: 刷新页面时出现404错误

**解决方案**:
确保 Nginx 或其他 Web 服务器配置了 SPA 路由回退：

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

---

## 📚 相关文档

- [Vue 3 官方文档](https://vuejs.org/)
- [Vite 官方文档](https://vitejs.dev/)
- [Vue Router 文档](https://router.vuejs.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Axios 文档](https://axios-http.com/)
- [后端 API 文档](../backend/docs/API.md)
- [项目根目录 README](../README.md)

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

- 使用 ESLint 进行代码检查
- 遵循 Vue 3 风格指南
- 组件命名使用 PascalCase
- 文件命名使用 kebab-case

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情

---

## 📞 联系方式

- 项目主页: https://github.com/yourusername/webscan-ai
- 问题反馈: https://github.com/yourusername/webscan-ai/issues
<<<<<<< HEAD
- 邮箱: your.email@www.baidu.com
=======
- 邮箱: your.email@example.com
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 ⭐️**

Made with ❤️ by WebScan AI Team

</div>

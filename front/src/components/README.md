# 前端组件结构

本目录包含前端 Vue.js 应用的所有可复用组件。

## 目录结构

```
components/
├── common/           # 通用组件
│   ├── StatCard.vue  # 统计卡片组件
│   ├── Loading.vue   # 加载动画组件
│   └── Alert.vue     # 警告提示组件
├── layout/           # 布局组件
│   └── AppLayout.vue # 应用主布局组件
└── business/         # 业务组件
    └── (待添加)
```

## 组件说明

### 通用组件 (common/)

#### StatCard
统计卡片组件，用于显示关键指标数据。

**Props:**
- `icon` (String, required): 图标
- `value` (Number/String, required): 数值
- `label` (String, required): 标签
- `type` (String, default: 'primary'): 卡片类型 (primary/danger/success/warning/trend)

**示例:**
```vue
<StatCard 
  icon="🔍"
  :value="todayScans"
  label="今日扫描任务"
  type="primary"
/>
```

#### Loading
加载动画组件，用于显示加载状态。

**Props:**
- `text` (String, default: '加载中...'): 加载文本

**示例:**
```vue
<Loading text="正在扫描..." />
```

#### Alert
警告提示组件，用于显示成功、错误、警告或信息提示。

**Props:**
- `type` (String, default: 'info'): 提示类型 (success/error/warning/info)
- `message` (String, required): 提示消息
- `dismissible` (Boolean, default: true): 是否可关闭
- `duration` (Number, default: 3000): 自动关闭时间（毫秒）

**示例:**
```vue
<Alert 
  type="success" 
  message="扫描任务创建成功"
  :duration="3000"
/>
```

### 布局组件 (layout/)

#### AppLayout
应用主布局组件，包含顶部导航栏、侧边栏和主内容区域。

**功能:**
- 响应式布局（支持移动端）
- 侧边栏折叠
- 用户菜单
- 通知面板

**示例:**
```vue
<template>
  <AppLayout>
    <router-view />
  </AppLayout>
</template>
```

## 使用指南

### 导入组件

```javascript
import StatCard from '@/components/common/StatCard.vue'
import Loading from '@/components/common/Loading.vue'
import Alert from '@/components/common/Alert.vue'
```

### 全局注册组件

在 `main.js` 中全局注册：

```javascript
import { createApp } from 'vue'
import App from './App.vue'

const app = createApp(App)

// 全局注册通用组件
import StatCard from './components/common/StatCard.vue'
import Loading from './components/common/Loading.vue'
import Alert from './components/common/Alert.vue'

app.component('StatCard', StatCard)
app.component('Loading', Loading)
app.component('Alert', Alert)

app.mount('#app')
```

## 开发规范

1. **命名规范**: 组件名称使用 PascalCase
2. **Props 验证**: 所有 props 都应该有类型和默认值
3. **样式作用域**: 使用 `scoped` 属性限制样式作用域
4. **文档注释**: 为每个组件添加详细的 JSDoc 注释
5. **事件命名**: 使用 kebab-case 命名自定义事件

## 扩展指南

添加新组件时，请遵循以下步骤：

1. 在对应的子目录中创建 `.vue` 文件
2. 在子目录的 `__init__.py` 中导出组件（如果是 Python 项目）
3. 在本 README 中添加组件文档
4. 添加单元测试（如果需要）
5. 更新组件示例

## 待办事项

- [ ] 添加更多通用组件（Button、Input、Modal 等）
- [ ] 添加业务组件（ScanForm、ReportTable 等）
- [ ] 添加组件单元测试
- [ ] 添加组件 Storybook 文档

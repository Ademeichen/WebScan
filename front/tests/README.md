# 前端功能测试文档

## 概述

本文档描述了 WebScan AI Security Platform 前端功能的测试策略、测试用例和测试执行方法。

## 测试环境配置

### 依赖安装

```bash
cd front
npm install
```

### 测试依赖

项目使用 Vitest 作为测试框架，主要依赖包括：

- `vitest`: 测试框架
- `@vue/test-utils`: Vue 组件测试工具
- `jsdom`: 浏览器环境模拟
- `@vitest/coverage-v8`: 代码覆盖率工具
- `@vitest/ui`: 测试 UI 界面

## 测试结构

```
front/
├── tests/
│   ├── setup.js              # 测试环境配置
│   ├── unit/                 # 单元测试
│   │   ├── api.test.js      # API 测试
│   │   ├── notifications.test.js  # 通知组件测试
│   │   ├── profile.test.js  # 个人信息组件测试
│   │   └── vulnerability-results.test.js  # 漏洞结果组件测试
│   └── integration/          # 集成测试（待添加）
└── vitest.config.js          # Vitest 配置文件
```

## 测试用例说明

### 1. API 测试 (api.test.js)

测试所有 API 方法的正确性，包括：

- **认证 API (authApi)**
  - 登录
  - 登出
  - 获取当前用户信息

- **任务 API (tasksApi)**
  - 获取任务列表
  - 获取任务详情
  - 创建任务
  - 删除任务
  - 获取任务漏洞
  - 获取任务结果

- **漏洞 API (vulnerabilitiesApi)**
  - 获取漏洞列表
  - 获取漏洞详情
  - 更新漏洞状态

- **通知 API (notificationsApi)**
  - 获取通知列表
  - 标记为已读
  - 删除通知

- **报告 API (reportsApi)**
  - 获取报告列表
  - 生成报告
  - 下载报告

- **扫描 API (scanApi)**
  - 启动扫描
  - 获取扫描状态
  - 获取扫描结果
  - 停止扫描

- **AI Agent API (aiAgentsApi)**
  - 执行 Agent
  - 获取任务
  - 取消任务

- **知识库 API (knowledgeBaseApi)**
  - 搜索知识库
  - 获取知识库条目

- **AWVS API (awvsApi)**
  - 获取目标列表
  - 添加目标
  - 启动扫描
  - 获取扫描列表

- **POC API (pocApi)**
  - 获取 POC 列表
  - 运行 POC

- **统计 API (statsApi)**
  - 获取仪表板统计
  - 获取漏洞统计
  - 获取任务统计

### 2. 通知组件测试 (notifications.test.js)

测试通知列表页面的功能：

- 渲染通知列表
- 按类型筛选通知
- 按已读状态筛选通知
- 标记通知为已读
- 删除通知
- 导航到通知详情
- 处理分页
- 刷新通知列表
- 显示加载状态
- 显示错误消息

### 3. 个人信息组件测试 (profile.test.js)

测试用户个人信息管理页面的功能：

- 渲染个人信息页面
- 加载用户信息
- 更新用户信息
- 验证表单
- 修改密码
- 验证密码表单
- 显示加载状态
- 显示错误消息
- 显示成功消息
- 重置表单
- 切换标签页
- 处理 API 错误

### 4. 漏洞结果组件测试 (vulnerability-results.test.js)

测试漏洞结果页面的功能：

- 渲染漏洞结果页面
- 加载漏洞列表
- 加载任务信息
- 按严重程度筛选漏洞
- 按状态筛选漏洞
- 搜索漏洞
- 更新漏洞状态
- 导航到漏洞详情
- 处理分页
- 刷新漏洞列表
- 显示加载状态
- 显示错误消息
- 显示漏洞统计
- 导出漏洞
- 处理缺少任务 ID 的情况

## 运行测试

### 运行所有测试

```bash
npm run test
```

### 运行测试并显示 UI

```bash
npm run test:ui
```

### 运行测试并生成覆盖率报告

```bash
npm run test:coverage
```

### 运行特定测试文件

```bash
npm run test api.test.js
```

### 监听模式运行测试

```bash
npm run test -- --watch
```

## 测试覆盖率

目标覆盖率：

- **语句覆盖率**: > 80%
- **分支覆盖率**: > 75%
- **函数覆盖率**: > 80%
- **行覆盖率**: > 80%

## 测试最佳实践

1. **隔离性**: 每个测试用例应该独立运行，不依赖其他测试用例
2. **可读性**: 测试用例应该清晰描述被测试的功能
3. **可维护性**: 测试代码应该易于维护和更新
4. **Mock 外部依赖**: 使用 mock 来模拟外部 API 调用
5. **测试边界条件**: 测试正常情况和异常情况
6. **测试用户交互**: 测试用户与组件的交互

## 持续集成

测试应该在每次代码提交时自动运行，确保代码质量。建议在 CI/CD 流程中添加以下步骤：

```yaml
- name: Run tests
  run: npm run test

- name: Generate coverage
  run: npm run test:coverage

- name: Upload coverage
  run: npm run test:coverage -- --reporter=html
```

## 测试数据

测试使用模拟数据，不依赖真实的后端 API。所有 API 调用都被 mock，确保测试的独立性和可重复性。

## 已知问题

1. 部分组件的集成测试尚未完成
2. E2E 测试尚未实现
3. 性能测试尚未实现

## 后续计划

1. 添加更多组件的单元测试
2. 实现集成测试
3. 实现 E2E 测试
4. 添加性能测试
5. 提高测试覆盖率到 90% 以上

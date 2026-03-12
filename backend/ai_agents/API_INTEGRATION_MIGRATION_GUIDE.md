# API集成迁移指南

## 迁移概述

本次迁移将 `standard_api.py` 中的POC API和工作流指标API功能集成到 `routes.py` 中，并删除了原文件。

## 迁移日期

2026-03-03

## 变更内容

### 1. 文件变更

**已删除的文件：**
- `backend/ai_agents/api/standard_api.py`

**已更新的文件：**
- `backend/ai_agents/api/routes.py` - 集成了POC和工作流指标API
- `backend/ai_agents/BUSINESS_LOGIC_REVIEW.md` - 更新了文档引用
- `front/src/utils/aiAgents.js` - 添加了新的API调用函数
- `backend/ai_agents/api/tests/test_routes.py` - 新增API路由测试文件

### 2. API端点变更

#### 新增的API端点（集成到routes.py）：

| 端点 | 方法 | 功能 | 原位置 |
|------|------|------|--------|
| `/ai_agents/poc/search` | POST | 搜索POC | standard_api.py |
| `/ai_agents/poc/execute` | POST | 执行POC | standard_api.py |
| `/ai_agents/poc/batch-execute` | POST | 批量执行POC | standard_api.py |
| `/ai_agents/workflow/metrics` | GET | 获取工作流执行指标 | standard_api.py |

### 3. 前端API调用新增

在 `front/src/utils/aiAgents.js` 中新增了以下API调用函数：

```javascript
// 搜索POC
searchPOC: async (cveId) => { ... }

// 执行POC
executePOC: async (data) => { ... }

// 批量执行POC
batchExecutePOC: async (targets, cveIds) => { ... }

// 获取工作流指标
getWorkflowMetrics: async (taskId = null) => { ... }
```

## 迁移步骤

### 步骤1：代码集成

✅ 已将 `standard_api.py` 中的所有API端点和模型类集成到 `routes.py`

### 步骤2：删除原文件

✅ 已删除 `standard_api.py` 文件

### 步骤3：更新文档

✅ 已更新 `BUSINESS_LOGIC_REVIEW.md` 中的文件引用

### 步骤4：前端集成

✅ 已在前端添加新的API调用函数

### 步骤5：测试创建

✅ 已创建API路由测试文件 `test_routes.py`

## 兼容性说明

### 向后兼容性

- 所有原有的API端点保持不变
- API请求/响应格式保持一致
- 错误处理机制保持一致

### 新增功能

1. **POC搜索API**：通过CVE编号搜索可用的POC
2. **POC执行API**：执行单个POC漏洞检测
3. **批量POC执行API**：对多个目标执行多个CVE的POC检测
4. **工作流指标API**：获取节点执行时间、重试次数、跳过状态等指标

## 测试验证

### 测试文件

- `backend/ai_agents/api/tests/test_routes.py` - API路由测试

### 测试覆盖范围

- POC API端点请求模型测试
- 工作流指标API查询参数测试
- 错误处理测试
- API响应格式测试
- 边界条件测试
- POC集成管理器功能测试
- 执行优化器功能测试

## 使用示例

### 1. 搜索POC

```javascript
import { aiAgentsApi } from '@/utils/aiAgents'

// 搜索POC
const result = await aiAgentsApi.searchPOC('CVE-2021-44228')
console.log(result)
```

### 2. 执行POC

```javascript
// 执行POC
const result = await aiAgentsApi.executePOC({
  target: 'http://example.com',
  cve_id: 'CVE-2021-44228',
  timeout: 60.0
})
```

### 3. 批量执行POC

```javascript
// 批量执行POC
const result = await aiAgentsApi.batchExecutePOC(
  ['http://example1.com', 'http://example2.com'],
  ['CVE-2021-44228', 'CVE-2019-12345']
)
```

### 4. 获取工作流指标

```javascript
// 获取所有工作流指标
const allMetrics = await aiAgentsApi.getWorkflowMetrics()

// 获取特定任务的工作流指标
const taskMetrics = await aiAgentsApi.getWorkflowMetrics('task-001')
```

## 注意事项

1. **依赖项**：确保所有依赖项已正确安装（pocsuite3、httpx等）
2. **配置**：检查Seebug API配置是否正确
3. **日志**：所有API操作都有详细的日志记录
4. **错误处理**：API具有完善的错误处理和返回格式

## 回滚方案

如需回滚到之前的版本：

1. 恢复 `standard_api.py` 文件
2. 从 `routes.py` 中移除新增的POC和工作流指标API代码
3. 从前端 `aiAgents.js` 中移除新增的API调用函数
4. 更新相关文档引用

## 相关文档

- [AI Agents README](./README.md)
- [业务逻辑审查报告](./BUSINESS_LOGIC_REVIEW.md)
- [项目根目录README](../../README.md)

## 迁移完成状态

✅ **迁移完成** - 所有任务已成功完成

---

**迁移负责人：** AI Assistant  
**迁移完成时间：** 2026-03-03

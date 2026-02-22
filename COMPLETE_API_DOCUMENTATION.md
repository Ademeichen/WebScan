# WebScan AI Security Platform - 完整API文档

## 文档说明
本文档提供了WebScan AI Security Platform所有API端点的完整参考，包括功能描述、请求参数、响应格式、错误码及示例。

## 更新日期
2026-02-22

---

## 一、API基础信息

### 基础配置
- **基础URL**: `http://127.0.0.1:3000/api`
- **请求超时**: 30000ms (30秒)
- **认证方式**: Bearer Token
- **WebSocket**: `ws://localhost:3000/api/ws`

### 认证机制
所有API请求（除了登录和注册）都需要在请求头中包含认证令牌：

```
Authorization: Bearer {token}
```

### 统一响应格式
所有API响应遵循以下格式：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": { ... }
}
```

### 统一错误码
| 错误码 | 说明 |
|---------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 422 | 参数验证失败 |
| 500 | 服务器内部错误 |

---

## 二、扫描相关API (scanApi)

### 2.1 启动扫描
**端点**: `POST /scan/start`
**功能**: 启动新的扫描任务

**请求参数**:
```json
{
  "url": "http://example.com",
  "scan_type": "comprehensive",
  "options": {}
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "扫描任务已创建",
  "data": {
    "task_id": 123,
    "status": "pending"
  }
}
```

### 2.2 获取扫描状态
**端点**: `GET /scan/status/{scanId}`
**功能**: 获取指定扫描任务的当前状态

**路径参数**:
- `scanId`: 扫描任务ID

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "task_id": 123,
    "status": "running",
    "progress": 45,
    "start_time": "2026-02-22T10:00:00Z",
    "end_time": null
  }
}
```

### 2.3 获取扫描结果
**端点**: `GET /scan/results/{scanId}`
**功能**: 获取指定扫描任务的完整结果

**路径参数**:
- `scanId`: 扫描任务ID

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "task_id": 123,
    "status": "completed",
    "results": [...],
    "vulnerabilities": [...]
  }
}
```

### 2.4 停止扫描
**端点**: `POST /scan/stop/{scanId}`
**功能**: 停止正在运行的扫描任务

**路径参数**:
- `scanId`: 扫描任务ID

**响应示例**:
```json
{
  "code": 200,
  "message": "扫描已停止",
  "data": {
    "task_id": 123,
    "status": "stopped"
  }
}
```

### 2.5 端口扫描
**端点**: `POST /scan/port-scan`
**功能**: 执行端口扫描

**请求参数**:
```json
{
  "target": "192.168.1.1",
  "port_range": "1-1000",
  "timeout": 30
}
```

### 2.6 信息泄露扫描
**端点**: `POST /scan/info-leak`
**功能**: 扫描信息泄露漏洞

**请求参数**:
```json
{
  "target": "http://example.com",
  "depth": 3
}
```

### 2.7 目录扫描
**端点**: `POST /scan/dir-scan`
**功能**: 扫描网站目录结构

**请求参数**:
```json
{
  "target": "http://example.com",
  "wordlist": "common.txt",
  "max_threads": 10
}
```

### 2.8 网站侧扫描
**端点**: `POST /scan/web-side`
**功能**: 扫描网站侧边栏和隐藏页面

**请求参数**:
```json
{
  "target": "http://example.com",
  "scan_depth": 3
}
```

### 2.9 基础信息扫描
**端点**: `POST /scan/baseinfo`
**功能**: 获取目标的基础信息

**请求参数**:
```json
{
  "target": "http://example.com"
}
```

### 2.10 子域名扫描
**端点**: `POST /scan/subdomain`
**功能**: 扫描目标的子域名

**请求参数**:
```json
{
  "domain": "example.com",
  "wordlist": "subdomains.txt"
}
```

### 2.11 综合扫描
**端点**: `POST /scan/comprehensive`
**功能**: 执行综合扫描，包含多种扫描类型

**请求参数**:
```json
{
  "target": "http://example.com",
  "scan_types": ["port", "dir", "web-side"]
}
```

---

## 三、任务管理API (tasksApi)

### 3.1 创建任务
**端点**: `POST /tasks/create`
**功能**: 创建新的扫描任务

**请求参数**:
```json
{
  "task_name": "综合扫描任务",
  "target": "http://example.com",
  "task_type": "comprehensive",
  "config": {
    "scan_depth": 3,
    "max_threads": 10
  }
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "任务创建成功",
  "data": {
    "task_id": 123,
    "status": "pending"
  }
}
```

### 3.2 获取任务列表
**端点**: `GET /tasks/`
**功能**: 获取任务列表，支持分页和过滤

**查询参数**:
- `status`: 任务状态过滤 (pending/running/completed/failed)
- `task_type`: 任务类型过滤
- `search`: 搜索关键词
- `start_date`: 开始日期
- `end_date`: 结束日期
- `skip`: 跳过记录数
- `limit`: 返回记录数

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "tasks": [...],
    "total": 100,
    "skip": 0,
    "limit": 20
  }
}
```

### 3.3 获取任务详情
**端点**: `GET /tasks/{taskId}`
**功能**: 获取指定任务的详细信息

**路径参数**:
- `taskId`: 任务ID

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "task_id": 123,
    "task_name": "综合扫描任务",
    "target": "http://example.com",
    "status": "running",
    "progress": 45,
    "config": {...},
    "result": {...}
  }
}
```

### 3.4 更新任务
**端点**: `PUT /tasks/{taskId}`
**功能**: 更新任务配置

**路径参数**:
- `taskId`: 任务ID

**请求体**:
```json
{
  "task_name": "更新后的任务名称",
  "config": {...}
}
```

### 3.5 删除任务
**端点**: `DELETE /agent/task/{taskId}`
**功能**: 删除指定任务

**路径参数**:
- `taskId`: 任务ID

**响应示例**:
```json
{
  "code": 200,
  "message": "任务删除成功",
  "data": null
}
```

### 3.6 取消任务
**端点**: `POST /agent/task/{taskId}/abort`
**功能**: 取消正在运行的任务

**路径参数**:
- `taskId`: 任务ID

**响应示例**:
```json
{
  "code": 200,
  "message": "任务已取消",
  "data": {
    "task_id": 123,
    "status": "cancelled"
  }
}
```

### 3.7 获取任务日志
**端点**: `GET /agent/task/{taskId}/logs`
**功能**: 获取任务执行日志

**路径参数**:
- `taskId`: 任务ID

**查询参数**:
- `keyword`: 日志关键词过滤
- `tail`: 返回最后N行

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": "日志内容..."
}
```

### 3.8 获取任务结果
**端点**: `GET /tasks/{taskId}/results`
**功能**: 获取任务的扫描结果

**路径参数**:
- `taskId`: 任务ID

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "task_id": 123,
    "results": [...],
    "vulnerabilities": [...]
  }
}
```

### 3.9 获取统计概览
**端点**: `GET /tasks/statistics/overview`
**功能**: 获取任务统计概览

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total_tasks": 100,
    "completed": 80,
    "running": 15,
    "failed": 5,
    "success_rate": 80.0
  }
}
```

---

## 四、报告管理API (reportsApi)

### 4.1 获取报告列表
**端点**: `GET /reports/`
**功能**: 获取报告列表

**查询参数**:
- `format`: 报告格式过滤 (html/pdf/json)
- `task_id`: 关联任务ID
- `skip`: 跳过记录数
- `limit`: 返回记录数

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "reports": [...],
    "total": 50,
    "skip": 0,
    "limit": 20
  }
}
```

### 4.2 创建报告
**端点**: `POST /reports/`
**功能**: 创建新的扫描报告

**请求参数**:
```json
{
  "task_id": 123,
  "name": "扫描报告",
  "format": "html",
  "content": {
    "summary": {
      "critical": 1,
      "high": 2,
      "medium": 3,
      "low": 4,
      "info": 5
    },
    "vulnerabilities": [...]
  }
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "报告创建成功",
  "data": {
    "id": 456,
    "task_id": 123,
    "report_name": "扫描报告",
    "report_type": "html",
    "created_at": "2026-02-22T10:00:00Z",
    "total_vulnerabilities": 15,
    "critical_count": 1,
    "high_count": 2,
    "medium_count": 3,
    "low_count": 4,
    "info_count": 5
  }
}
```

### 4.3 获取报告详情
**端点**: `GET /reports/{reportId}`
**功能**: 获取指定报告的详细信息

**路径参数**:
- `reportId`: 报告ID

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": 456,
    "task_id": 123,
    "report_name": "扫描报告",
    "report_type": "html",
    "content": {...},
    "created_at": "2026-02-22T10:00:00Z"
  }
}
```

### 4.4 更新报告
**端点**: `PUT /reports/{reportId}`
**功能**: 更新报告内容

**路径参数**:
- `reportId`: 报告ID

**请求体**:
```json
{
  "report_name": "更新后的报告名称",
  "content": {...}
}
```

### 4.5 删除报告
**端点**: `DELETE /reports/{reportId}`
**功能**: 删除指定报告

**路径参数**:
- `reportId`: 报告ID

**响应示例**:
```json
{
  "code": 200,
  "message": "报告删除成功",
  "data": null
}
```

### 4.6 导出报告
**端点**: `GET /reports/{reportId}/export`
**功能**: 导出报告为指定格式

**路径参数**:
- `reportId`: 报告ID

**查询参数**:
- `format`: 导出格式 (html/json)

**响应**:
- HTML格式: 返回HTML内容，Content-Type: text/html
- JSON格式: 返回JSON内容，Content-Type: application/json

---

## 五、系统设置API (settingsApi)

### 5.1 获取设置
**端点**: `GET /settings/`
**功能**: 获取系统设置

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "general": {
      "systemName": "WebScan AI",
      "language": "zh-CN",
      "timezone": "Asia/Shanghai"
    },
    "scan": {
      "defaultDepth": 2,
      "defaultConcurrency": 5
    },
    "notification": {
      "enabled": true,
      "email": "admin@example.com"
    },
    "security": {
      "enableAuth": true,
      "sessionTimeout": 3600
    }
  }
}
```

### 5.2 更新设置
**端点**: `PUT /settings/`
**功能**: 更新系统设置

**请求参数**:
```json
{
  "general": {...},
  "scan": {...},
  "notification": {...},
  "security": {...}
}
```

### 5.3 获取单项设置
**端点**: `GET /settings/item/{category}/{key}`
**功能**: 获取指定类别的单个设置项

**路径参数**:
- `category`: 设置类别 (general/scan/notification/security)
- `key`: 设置键名

### 5.4 更新单项设置
**端点**: `PUT /settings/item`
**功能**: 更新单个设置项

**请求参数**:
```json
{
  "category": "general",
  "key": "systemName",
  "value": "WebScan AI Platform"
}
```

### 5.5 删除单项设置
**端点**: `DELETE /settings/item/{category}/{key}`
**功能**: 删除指定设置项

### 5.6 获取系统信息
**端点**: `GET /settings/system-info`
**功能**: 获取系统运行信息

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "version": "1.0.0",
    "python_version": "3.9.0",
    "platform": "Linux",
    "uptime": 86400
  }
}
```

### 5.7 获取统计数据
**端点**: `GET /settings/statistics`
**功能**: 获取系统统计数据

**查询参数**:
- `period`: 统计周期 (daily/weekly/monthly)

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total_scans": 1000,
    "total_vulnerabilities": 500,
    "success_rate": 95.5
  }
}
```

### 5.8 获取设置分类
**端点**: `GET /settings/categories`
**功能**: 获取所有设置分类

### 5.9 获取分类设置
**端点**: `GET /settings/category/{category}`
**功能**: 获取指定分类的所有设置

### 5.10 重置设置
**端点**: `POST /settings/reset`
**功能**: 重置所有设置为默认值

### 5.11 重置分类设置
**端点**: `POST /settings/reset/{category}`
**功能**: 重置指定分类的设置为默认值

### 5.12 获取API密钥列表
**端点**: `GET /settings/api-keys`
**功能**: 获取所有API密钥

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "keys": [
      {
        "id": 1,
        "name": "Production Key",
        "created_at": "2026-02-01T00:00:00Z",
        "last_used": "2026-02-22T10:00:00Z"
      }
    ]
  }
}
```

### 5.13 创建API密钥
**端点**: `POST /settings/api-keys`
**功能**: 创建新的API密钥

**请求参数**:
```json
{
  "name": "Development Key",
  "expires_in": 30
}
```

### 5.14 删除API密钥
**端点**: `DELETE /settings/api-keys/{keyId}`
**功能**: 删除指定API密钥

### 5.15 重新生成API密钥
**端点**: `PUT /settings/api-keys/{keyId}/regenerate`
**功能**: 重新生成API密钥

---

## 六、POC扫描API (pocApi)

### 6.1 获取POC类型
**端点**: `GET /poc/types`
**功能**: 获取所有POC类型

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "types": [
      {
        "id": "weblogic",
        "name": "WebLogic",
        "description": "WebLogic中间件漏洞"
      },
      {
        "id": "struts2",
        "name": "Struts2",
        "description": "Struts2框架漏洞"
      }
    ]
  }
}
```

### 6.2 POC扫描
**端点**: `POST /poc/scan`
**功能**: 执行POC扫描

**请求参数**:
```json
{
  "task_name": "POC扫描任务",
  "target": "http://example.com",
  "task_type": "poc_scan",
  "config": {
    "poc_types": ["weblogic", "struts2", "tomcat"]
  }
}
```

### 6.3 获取POC信息
**端点**: `GET /poc/info/{pocType}`
**功能**: 获取指定POC类型的详细信息

**路径参数**:
- `pocType`: POC类型ID

### 6.4 单个POC扫描
**端点**: `POST /poc/scan/{pocType}`
**功能**: 对指定目标执行单个POC扫描

**路径参数**:
- `pocType`: POC类型ID

**请求参数**:
```json
{
  "target": "http://example.com",
  "timeout": 60
}
```

---

## 七、AWVS扫描API (awvsApi)

### 7.1 获取目标列表
**端点**: `GET /awvs/targets`
**功能**: 获取AWVS中的所有扫描目标

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "target_id": "1234567890",
      "address": "http://example.com",
      "description": "测试目标",
      "criticality": "10",
      "status": "processed"
    }
  ]
}
```

### 7.2 创建目标
**端点**: `POST /awvs/target`
**功能**: 在AWVS中创建新的扫描目标

**请求参数**:
```json
{
  "address": "http://example.com",
  "description": "测试目标"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "添加成功",
  "data": {
    "target_id": "1234567890",
    "address": "http://example.com",
    "description": "测试目标"
  }
}
```

### 7.3 删除目标
**端点**: `DELETE /awvs/target/{targetId}`
**功能**: 删除AWVS中的指定目标

**路径参数**:
- `targetId`: 目标ID

### 7.4 获取扫描列表
**端点**: `GET /awvs/scans`
**功能**: 获取AWVS扫描任务列表

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "scan_id": "1234567890",
      "target_id": "0987654321",
      "profile_name": "11111111-1111-1111-1111-111111111111",
      "current_session": {
        "status": "processing",
        "progress": 45,
        "severity_counts": {
          "critical": 1,
          "high": 2,
          "medium": 3
        }
      }
    }
  ]
}
```

### 7.5 启动扫描
**端点**: `POST /awvs/scan`
**功能**: 启动AWVS扫描任务

**请求参数**:
```json
{
  "url": "http://example.com",
  "scan_type": "full_scan"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "扫描任务已提交到队列",
  "data": {
    "task_id": 123,
    "status": "queued"
  }
}
```

### 7.6 停止扫描
**端点**: `POST /awvs/scans/{scanId}/stop`
**功能**: 停止AWVS扫描

**路径参数**:
- `scanId`: 扫描ID

### 7.7 获取漏洞列表
**端点**: `GET /awvs/vulnerabilities/{targetId}`
**功能**: 获取指定目标的漏洞列表

**路径参数**:
- `targetId`: 目标ID

**响应示例**:
```json
{
  "code": 200,
  "message": "获取漏洞列表成功",
  "data": [
    {
      "vuln_id": "1234567890",
      "severity": "High",
      "vuln_name": "SQL Injection",
      "target": "http://example.com/admin",
      "time": "2026-02-22 10:00:00"
    }
  ]
}
```

### 7.8 获取漏洞详情
**端点**: `GET /awvs/vulnerability/{vulnId}`
**功能**: 获取指定漏洞的详细信息

**路径参数**:
- `vulnId`: 漏洞ID

**响应示例**:
```json
{
  "code": 200,
  "message": "获取漏洞详情成功",
  "data": {
    "vuln_id": "1234567890",
    "severity": "High",
    "vt_name": "SQL Injection",
    "description": "SQL注入漏洞...",
    "affects_url": "http://example.com/admin",
    "recommendation": "使用参数化查询"
  }
}
```

### 7.9 获取漏洞排名
**端点**: `GET /awvs/vulnerabilities/rank`
**功能**: 获取漏洞排名（前5名）

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "name": "SQL Injection",
      "value": 15
    },
    {
      "name": "XSS",
      "value": 12
    }
  ]
}
```

### 7.10 获取漏洞统计
**端点**: `GET /awvs/vulnerabilities/stats`
**功能**: 获取漏洞统计信息

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "high": {
      "total": 20,
      "vulnerabilities": ["SQL Injection", "XSS", "RCE"]
    },
    "normal": {
      "total": 50,
      "vulnerabilities": [...]
    }
  }
}
```

### 7.11 获取中间件POC列表
**端点**: `GET /awvs/middleware/poc-list`
**功能**: 获取支持的中间件POC列表

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "cve_id": "CVE-2020-2551",
      "name": "WebLogic CVE-2020-2551",
      "description": "WebLogic Server 反序列化漏洞",
      "severity": "高危",
      "middleware": "WebLogic"
    }
  ]
}
```

### 7.12 获取中间件POC扫描任务
**端点**: `GET /awvs/middleware/scans`
**功能**: 获取所有中间件POC扫描任务

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "id": 1,
      "task_name": "Middleware POC Scan: CVE-2020-2551",
      "target": "http://example.com",
      "status": "completed",
      "progress": 100,
      "cve_id": "CVE-2020-2551"
    }
  ]
}
```

### 7.13 创建中间件POC扫描任务
**端点**: `POST /awvs/middleware/scan`
**功能**: 创建中间件POC扫描任务

**请求参数**:
```json
{
  "url": "http://example.com",
  "cve_id": "CVE-2020-2551"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "创建扫描任务成功",
  "data": {
    "task_id": 1
  }
}
```

### 7.14 启动中间件POC扫描
**端点**: `POST /awvs/middleware/scan/start`
**功能**: 启动中间件POC扫描（后台任务）

**请求参数**:
```json
{
  "url": "http://example.com",
  "cve_id": "CVE-2018-2628"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "扫描任务已启动",
  "data": null
}
```

### 7.15 停止中间件POC扫描
**端点**: `POST /awvs/middleware/scans/{scanId}/stop`
**功能**: 停止中间件POC扫描

**路径参数**:
- `scanId`: 扫描任务ID

### 7.16 AWVS健康检查
**端点**: `GET /awvs/health`
**功能**: 检查AWVS服务连接状态

**响应示例**:
```json
{
  "code": 200,
  "message": "AWVS服务连接正常",
  "data": {
    "status": "connected"
  }
}
```

---

## 八、AI相关API (aiApi)

### 8.1 AI对话
**端点**: `POST /ai/chat`
**功能**: 与AI助手进行对话

**请求参数**:
```json
{
  "message": "请帮我分析这个漏洞",
  "context": {...}
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "对话成功",
  "data": {
    "response": "根据漏洞描述，这是一个SQL注入漏洞...",
    "model": "gpt-4",
    "tokens_used": 150
  }
}
```

### 8.2 漏洞分析
**端点**: `POST /ai/analyze`
**功能**: 使用AI分析漏洞

**请求参数**:
```json
{
  "vulnerability": {
    "title": "SQL Injection",
    "description": "...",
    "severity": "High"
  }
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "分析成功",
  "data": {
    "analysis": "这是一个SQL注入漏洞...",
    "recommendations": [...],
    "risk_level": "High"
  }
}
```

### 8.3 POC生成
**端点**: `POST /ai/poc/generate`
**功能**: 使用AI生成POC代码

**请求参数**:
```json
{
  "vulnerability": {
    "title": "SQL Injection",
    "description": "...",
    "cve_id": "CVE-2020-1234"
  },
  "language": "python"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "POC生成成功",
  "data": {
    "poc_code": "import requests...",
    "language": "python",
    "explanation": "生成的POC代码..."
  }
}
```

---

## 九、Agent管理API (agentApi)

### 9.1 Agent列表
**端点**: `GET /agent/list`
**功能**: 获取所有可用的Agent

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "agents": [
      {
        "id": 1,
        "name": "Port Scanner",
        "type": "scanner",
        "description": "端口扫描Agent"
      }
    ]
  }
}
```

### 9.2 Agent状态
**端点**: `GET /agent/{agentId}/status`
**功能**: 获取指定Agent的运行状态

**路径参数**:
- `agentId`: Agent ID

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "agent_id": 1,
    "status": "running",
    "current_task": "扫描端口",
    "progress": 45
  }
}
```

### 9.3 执行Agent
**端点**: `POST /agent/execute`
**功能**: 执行指定的Agent

**请求参数**:
```json
{
  "agent_id": 1,
  "target": "http://example.com",
  "config": {...}
}
```

### 9.4 Agent类型
**端点**: `GET /agent/types`
**功能**: 获取所有Agent类型

### 9.5 Agent详情
**端点**: `GET /agent/{agentId}`
**功能**: 获取指定Agent的详细信息

### 9.6 创建Agent
**端点**: `POST /agent/create`
**功能**: 创建新的Agent

### 9.7 更新Agent
**端点**: `PUT /agent/{agentId}`
**功能**: 更新Agent配置

### 9.8 删除Agent
**端点**: `DELETE /agent/{agentId}`
**功能**: 删除指定Agent

### 9.9 任务详情
**端点**: `GET /agent/tasks/{taskId}`
**功能**: 获取Agent任务的详细信息

### 9.10 取消任务
**端点**: `DELETE /agent/tasks/{taskId}`
**功能**: 取消Agent任务

### 9.11 任务日志
**端点**: `GET /agent/task/{taskId}/logs`
**功能**: 获取Agent任务的执行日志

### 9.12 冻结任务
**端点**: `GET /agent/tasks/frozen`
**功能**: 获取冻结的任务列表

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "id": 1,
      "task_name": "扫描任务",
      "task_type": "port_scan",
      "duration": "25.5",
      "threshold": 15,
      "progress": 60
    }
  ]
}
```

### 9.13 任务漏洞
**端点**: `GET /agent/tasks/{taskId}/vulnerabilities`
**功能**: 获取Agent任务发现的漏洞

**路径参数**:
- `taskId`: 任务ID

**查询参数**:
- `severity`: 漏洞严重程度过滤
- `type`: 漏洞类型过滤
- `source`: 漏洞来源过滤
- `status`: 漏洞状态过滤
- `skip`: 跳过记录数
- `limit`: 返回记录数

---

## 十、知识库API (kbApi)

### 10.1 漏洞搜索
**端点**: `GET /kb/vulnerabilities`
**功能**: 搜索漏洞知识库

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）
- `search`: 搜索关键词
- `severity`: 严重程度过滤
- `source`: 来源过滤
- `has_poc`: 是否有POC过滤

**响应示例**:
```json
{
  "code": 200,
  "message": "搜索成功",
  "data": {
    "vulnerabilities": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

### 10.2 添加漏洞知识
**端点**: `POST /kb/vulnerabilities`
**功能**: 添加新的漏洞知识

**请求参数**:
```json
{
  "title": "SQL Injection",
  "description": "SQL注入漏洞描述",
  "severity": "High",
  "source": "manual",
  "poc_code": "..."
}
```

### 10.3 知识详情
**端点**: `GET /kb/vulnerabilities/{knowledgeId}`
**功能**: 获取指定知识的详细信息

**路径参数**:
- `knowledgeId`: 知识ID

### 10.4 更新知识
**端点**: `PUT /kb/vulnerabilities/{knowledgeId}`
**功能**: 更新漏洞知识

### 10.5 删除知识
**端点**: `DELETE /kb/vulnerabilities/{knowledgeId}`
**功能**: 删除指定漏洞知识

### 10.6 同步知识库
**端点**: `POST /kb/sync`
**功能**: 从外部源同步漏洞知识库

### 10.7 搜索POC
**端点**: `POST /kb/seebug/poc/search`
**功能**: 在Seebug数据库中搜索POC

**请求参数**:
```json
{
  "keyword": "SQL注入",
  "cve_id": "CVE-2020-1234"
}
```

### 10.8 下载POC
**端点**: `POST /kb/seebug/poc/download`
**功能**: 从Seebug下载POC

**请求参数**:
```json
{
  "ssvid": "123456"
}
```

### 10.9 POC详情
**端点**: `GET /kb/seebug/poc/{ssvid}/detail`
**功能**: 获取Seebug POC的详细信息

**路径参数**:
- `ssvid`: Seebug漏洞ID

---

## 十一、POC生成API (pocGenApi)

### 11.1 生成POC
**端点**: `POST /poc_gen/generate`
**功能**: 智能生成POC代码

**请求参数**:
```json
{
  "vulnerability": {
    "title": "SQL Injection",
    "description": "...",
    "cve_id": "CVE-2020-1234"
  },
  "language": "python",
  "framework": "requests"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "POC生成成功",
  "data": {
    "poc_code": "import requests\n...",
    "language": "python",
    "quality_score": 0.85
  }
}
```

### 11.2 验证POC
**端点**: `POST /poc_gen/validate`
**功能**: 验证生成的POC代码

**请求参数**:
```json
{
  "poc_code": "import requests\n...",
  "language": "python"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "验证成功",
  "data": {
    "is_valid": true,
    "syntax_errors": [],
    "security_issues": []
  }
}
```

---

## 十二、用户管理API (userApi)

### 12.1 用户资料
**端点**: `GET /user/profile`
**功能**: 获取用户资料信息

**查询参数**:
- `user_id`: 用户ID（可选，默认为当前用户）

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "user_id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "created_at": "2026-01-01T00:00:00Z",
    "last_login": "2026-02-22T10:00:00Z"
  }
}
```

### 12.2 更新资料
**端点**: `PUT /user/profile`
**功能**: 更新用户资料

**请求参数**:
```json
{
  "user_id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "phone": "1234567890"
}
```

### 12.3 用户权限
**端点**: `GET /user/permissions`
**功能**: 获取用户权限列表

**查询参数**:
- `user_id`: 用户ID（可选）

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "permissions": [
      "scan:create",
      "scan:read",
      "report:create",
      "report:read",
      "admin:all"
    ]
  }
}
```

### 12.4 用户列表
**端点**: `GET /user/list`
**功能**: 获取用户列表（管理员功能）

**查询参数**:
- `page`: 页码
- `page_size`: 每页数量
- `search`: 搜索关键词
- `role`: 角色过滤

---

## 十三、通知管理API (notificationsApi)

### 13.1 通知列表
**端点**: `GET /notifications/`
**功能**: 获取用户通知列表

**查询参数**:
- `limit`: 返回数量（默认10）
- `offset`: 偏移量
- `unread_only`: 仅未读通知

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "notifications": [
      {
        "id": 1,
        "title": "扫描完成",
        "message": "您的扫描任务已完成",
        "type": "info",
        "read": false,
        "created_at": "2026-02-22T10:00:00Z"
      }
    ],
    "total": 50,
    "unread_count": 10
  }
}
```

### 13.2 通知详情
**端点**: `GET /notifications/{notificationId}`
**功能**: 获取指定通知的详细信息

**路径参数**:
- `notificationId`: 通知ID

### 13.3 创建通知
**端点**: `POST /notifications/`
**功能**: 创建新的通知

**请求参数**:
```json
{
  "title": "系统通知",
  "message": "系统将在今晚进行维护",
  "type": "warning",
  "user_id": 1
}
```

### 13.4 标记已读
**端点**: `PUT /notifications/{notificationId}/read`
**功能**: 标记通知为已读

**路径参数**:
- `notificationId`: 通知ID

### 13.5 全部已读
**端点**: `PUT /notifications/read-all`
**功能**: 标记所有通知为已读

---

## 十四、AI Agents API (aiAgentsApi)

### 14.1 启动Agent扫描
**端点**: `POST /ai_agents/scan`
**功能**: 启动AI Agent扫描任务

**请求参数**:
```json
{
  "target": "https://example.com",
  "enable_llm_planning": true,
  "custom_tasks": [...],
  "need_custom_scan": false,
  "custom_scan_type": null,
  "custom_scan_requirements": null,
  "custom_scan_language": "python",
  "need_capability_enhancement": false,
  "capability_requirement": null
}
```

**响应示例**:
```json
{
  "task_id": "123",
  "status": "pending",
  "message": "Agent扫描任务已提交到队列"
}
```

### 14.2 获取任务列表
**端点**: `GET /ai_agents/tasks`
**功能**: 获取AI Agent任务列表

**查询参数**:
- `status`: 任务状态过滤
- `task_type`: 任务类型过滤
- `page`: 页码
- `page_size`: 每页数量

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "tasks": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

### 14.3 获取任务详情
**端点**: `GET /ai_agents/tasks/{task_id}`
**功能**: 获取AI Agent任务详情

**路径参数**:
- `task_id`: 任务ID（字符串或整数）

**响应示例**:
```json
{
  "task_id": "123",
  "target": "https://example.com",
  "status": "running",
  "progress": 45,
  "created_at": "2026-02-22T10:00:00Z",
  "updated_at": "2026-02-22T10:30:00Z",
  "result": {...}
}
```

### 14.4 取消任务
**端点**: `POST /ai_agents/tasks/{task_id}/cancel`
**功能**: 取消AI Agent任务

**路径参数**:
- `task_id`: 任务ID

**响应示例**:
```json
{
  "task_id": "123",
  "status": "cancelled",
  "message": "任务已取消"
}
```

### 14.5 删除任务
**端点**: `DELETE /ai_agents/tasks/{task_id}`
**功能**: 删除AI Agent任务

**路径参数**:
- `task_id`: 任务ID

**响应示例**:
```json
{
  "task_id": "123",
  "status": "deleted",
  "message": "任务已删除"
}
```

### 14.6 获取工具列表
**端点**: `GET /ai_agents/tools`
**功能**: 获取可用的扫描工具列表

**查询参数**:
- `category`: 工具分类过滤（plugin/poc/general）

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total": 15,
    "tools": [
      {
        "name": "execute_code",
        "description": "执行Python代码",
        "category": "general"
      },
      {
        "name": "port_scan",
        "description": "端口扫描",
        "category": "poc"
      }
    ]
  }
}
```

### 14.7 获取Agent配置
**端点**: `GET /ai_agents/config`
**功能**: 获取AI Agent配置

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "max_execution_time": 300,
    "max_retries": 3,
    "max_concurrent_tools": 5,
    "tool_timeout": 60,
    "enable_llm_planning": true,
    "default_scan_tasks": [...],
    "enable_memory": true,
    "enable_kb_integration": true
  }
}
```

### 14.8 更新Agent配置
**端点**: `POST /ai_agents/config`
**功能**: 更新AI Agent配置

**请求参数**:
```json
{
  "max_execution_time": 300,
  "max_retries": 3,
  "max_concurrent_tools": 5,
  "tool_timeout": 60,
  "enable_llm_planning": true,
  "enable_memory": true,
  "enable_kb_integration": true
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "配置更新成功",
  "data": {
    "max_execution_time": 300,
    "max_retries": 3,
    "max_concurrent_tools": 5,
    "tool_timeout": 60,
    "enable_llm_planning": true,
    "default_scan_tasks": [...],
    "enable_memory": true,
    "enable_kb_integration": true
  }
}
```

### 14.9 代码生成
**端点**: `POST /ai_agents/code/generate`
**功能**: 生成扫描代码

**请求参数**:
```json
{
  "scan_type": "port_scan",
  "target": "https://example.com",
  "requirements": "扫描所有常用端口",
  "language": "python",
  "additional_params": {}
}
```

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "code": "import socket\n...",
    "language": "python",
    "explanation": "生成的代码用于端口扫描..."
  }
}
```

### 14.10 代码执行
**端点**: `POST /ai_agents/code/execute`
**功能**: 执行生成的代码

**请求参数**:
```json
{
  "code": "import socket\n...",
  "language": "python",
  "target": "https://example.com"
}
```

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "output": "扫描结果...",
    "error": null,
    "execution_time": 5.2
  }
}
```

### 14.11 生成并执行代码
**端点**: `POST /ai_agents/code/generate-and-execute`
**功能**: 生成并执行代码

**请求参数**:
```json
{
  "scan_type": "port_scan",
  "target": "https://example.com",
  "requirements": "扫描所有常用端口",
  "language": "python",
  "additional_params": {}
}
```

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "output": "扫描结果...",
    "error": null,
    "execution_time": 8.5
  }
}
```

### 14.12 功能增强
**端点**: `POST /ai_agents/capabilities/enhance`
**功能**: 增强Agent功能

**请求参数**:
```json
{
  "requirement": "需要SQL注入检测功能",
  "target": "https://example.com",
  "capability_name": "sql_injection"
}
```

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "capability": "sql_injection",
    "description": "已增强SQL注入检测功能",
    "code": "..."
  }
}
```

### 14.13 获取能力列表
**端点**: `GET /ai_agents/capabilities/list`
**功能**: 获取所有可用能力列表

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "total": 20,
    "capabilities": [
      {
        "name": "port_scan",
        "description": "端口扫描能力",
        "enabled": true
      },
      {
        "name": "sql_injection",
        "description": "SQL注入检测能力",
        "enabled": true
      }
    ]
  }
}
```

### 14.14 获取环境信息
**端点**: `GET /ai_agents/environment/info`
**功能**: 获取执行环境信息

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "python_version": "3.9.0",
    "available_modules": ["requests", "socket", "re"],
    "system_info": {
      "os": "Linux",
      "cpu": "4 cores",
      "memory": "8GB"
    }
  }
}
```

### 14.15 获取可用工具
**端点**: `GET /ai_agents/environment/tools`
**功能**: 获取环境中可用的工具列表

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "total": 10,
    "tools": ["python", "nmap", "sqlmap", "curl", "wget"]
  }
}
```

---

## 十五、WebSocket通信

### 15.1 WebSocket连接
**端点**: `ws://localhost:3000/api/ws`
**功能**: 建立WebSocket连接进行实时通信

**连接参数**:
- `token`: Bearer Token（通过查询参数传递）

**消息类型**:

#### 客户端发送消息
```json
{
  "type": "chat_message",
  "message": "用户消息内容",
  "token": "..."
}
```

#### 服务端推送消息

**任务更新**:
```json
{
  "type": "task_update",
  "payload": {
    "task_id": 123,
    "status": "running",
    "progress": 45
  }
}
```

**任务进度**:
```json
{
  "type": "task_progress",
  "payload": {
    "task_id": 123,
    "progress": 50,
    "current_stage": "端口扫描"
  }
}
```

**任务完成**:
```json
{
  "type": "task_completed",
  "payload": {
    "task_id": 123,
    "result": {...}
  }
}
```

**阶段更新**:
```json
{
  "type": "stage_update",
  "payload": {
    "task_id": 123,
    "stage": "端口扫描",
    "status": "completed"
  }
}
```

**任务失败**:
```json
{
  "type": "task_failed",
  "payload": {
    "task_id": 123,
    "error": "执行失败：连接超时"
  }
}
```

**漏洞发现**:
```json
{
  "type": "vulnerability_found",
  "payload": {
    "task_id": 123,
    "vulnerability": {
      "id": 456,
      "title": "SQL Injection",
      "severity": "High",
      "url": "http://example.com/admin"
    }
  }
}
```

**扫描开始**:
```json
{
  "type": "scan_started",
  "payload": {
    "task_id": 123,
    "scan_type": "port_scan"
  }
}
```

**扫描停止**:
```json
{
  "type": "scan_stopped",
  "payload": {
    "task_id": 123,
    "reason": "用户取消"
  }
}
```

**通知**:
```json
{
  "type": "notification",
  "payload": {
    "id": 1,
    "title": "扫描完成",
    "message": "您的扫描任务已完成",
    "type": "info"
  }
}
```

**心跳**:
```json
{
  "type": "heartbeat",
  "payload": {
    "timestamp": 1234567890,
    "status": "ok"
  }
}
```

---

## 十六、错误处理

### 16.1 错误响应格式
所有错误响应遵循统一格式：

```json
{
  "code": 400,
  "message": "请求参数错误",
  "error": "详细错误信息"
}
```

### 16.2 常见错误码

| 错误码 | HTTP状态 | 说明 | 解决方案 |
|---------|----------|------|----------|
| INVALID_PARAMS | 400 | 请求参数无效 | 检查请求参数格式和内容 |
| UNAUTHORIZED | 401 | 未授权 | 检查认证令牌是否有效 |
| FORBIDDEN | 403 | 禁止访问 | 检查用户权限 |
| NOT_FOUND | 404 | 资源不存在 | 检查资源ID是否正确 |
| VALIDATION_ERROR | 422 | 参数验证失败 | 检查参数验证规则 |
| INTERNAL_ERROR | 500 | 服务器内部错误 | 联系管理员或查看日志 |

### 16.3 参数验证规则

#### 字符串验证
- 长度限制：1-255字符
- 格式：不允许特殊字符
- 必填字段检查

#### 数值验证
- 范围检查：min ≤ value ≤ max
- 类型检查：必须是整数或浮点数
- 默认值处理

#### 日期验证
- 格式：ISO 8601 (YYYY-MM-DDTHH:mm:ssZ)
- 范围：不能是未来日期
- 必填检查

#### URL验证
- 格式：有效的HTTP/HTTPS URL
- 可访问性：URL必须可访问
- 协议限制：仅允许http/https

#### 枚举验证
- 允许值：预定义的枚举值列表
- 大小写不敏感

---

## 十七、安全建议

### 17.1 认证安全
- 所有API请求（除了公开端点）都需要有效的Bearer Token
- Token过期时间：24小时
- Token刷新机制：支持刷新令牌

### 17.2 输入验证
- 所有用户输入必须经过验证和过滤
- 防止SQL注入：使用参数化查询
- 防止XSS：对输出进行HTML转义
- 防止CSRF：使用CSRF Token

### 17.3 速率限制
- 每个IP每分钟最多60次请求
- 每个用户每分钟最多120次请求
- 超过限制返回429状态码

### 17.4 日志记录
- 记录所有API请求和响应
- 记录错误和异常
- 日志保留时间：30天
- 敏感信息脱敏处理

---

## 十八、使用示例

### 18.1 完整的扫描流程

```bash
# 1. 创建扫描任务
curl -X POST http://127.0.0.1:3000/api/tasks/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "综合扫描",
    "target": "http://example.com",
    "task_type": "comprehensive"
  }'

# 2. 获取任务状态
curl -X GET http://127.0.0.1:3000/api/tasks/123 \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. 获取扫描结果
curl -X GET http://127.0.0.1:3000/api/tasks/123/results \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. 创建报告
curl -X POST http://127.0.0.1:3000/api/reports/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 123,
    "name": "扫描报告",
    "format": "html",
    "content": {
      "summary": {...},
      "vulnerabilities": [...]
    }
  }'

# 5. 导出报告
curl -X GET "http://127.0.0.1:3000/api/reports/456/export?format=html" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o report.html
```

### 18.2 WebSocket连接示例

```javascript
// 建立WebSocket连接
const token = localStorage.getItem('token');
const ws = new WebSocket(`ws://localhost:3000/api/ws?token=${token}`);

ws.onopen = () => {
  console.log('WebSocket连接成功');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'task_update':
      console.log('任务更新:', data.payload);
      break;
    case 'task_progress':
      console.log('任务进度:', data.payload);
      break;
    case 'vulnerability_found':
      console.log('发现漏洞:', data.payload);
      break;
    case 'notification':
      console.log('收到通知:', data.payload);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket错误:', error);
};

ws.onclose = () => {
  console.log('WebSocket连接关闭');
};

// 发送消息
ws.send(JSON.stringify({
  type: 'chat_message',
  message: '请帮我分析这个漏洞',
  token: token
}));
```

---

## 附录

### A. API端点索引
按模块分类的完整端点列表：

1. **扫描功能** (11个端点)
   - POST /scan/start
   - GET /scan/status/{scanId}
   - GET /scan/results/{scanId}
   - POST /scan/stop/{scanId}
   - POST /scan/port-scan
   - POST /scan/info-leak
   - POST /scan/dir-scan
   - POST /scan/web-side
   - POST /scan/baseinfo
   - POST /scan/subdomain
   - POST /scan/comprehensive

2. **任务管理** (9个端点)
   - POST /tasks/create
   - GET /tasks/
   - GET /tasks/{taskId}
   - PUT /tasks/{taskId}
   - DELETE /agent/task/{taskId}
   - POST /agent/task/{taskId}/abort
   - GET /agent/task/{taskId}/logs
   - GET /tasks/{taskId}/results
   - GET /tasks/statistics/overview

3. **报告管理** (6个端点)
   - GET /reports/
   - POST /reports/
   - GET /reports/{reportId}
   - PUT /reports/{reportId}
   - DELETE /reports/{reportId}
   - GET /reports/{reportId}/export

4. **系统设置** (16个端点)
   - GET /settings/
   - PUT /settings/
   - GET /settings/item/{category}/{key}
   - PUT /settings/item
   - DELETE /settings/item/{category}/{key}
   - GET /settings/system-info
   - GET /settings/statistics
   - GET /settings/categories
   - GET /settings/category/{category}
   - POST /settings/reset
   - POST /settings/reset/{category}
   - GET /settings/api-keys
   - POST /settings/api-keys
   - DELETE /settings/api-keys/{keyId}
   - PUT /settings/api-keys/{keyId}/regenerate

5. **POC扫描** (4个端点)
   - GET /poc/types
   - POST /poc/scan
   - GET /poc/info/{pocType}
   - POST /poc/scan/{pocType}

6. **AWVS扫描** (16个端点)
   - GET /awvs/targets
   - POST /awvs/target
   - DELETE /awvs/target/{targetId}
   - GET /awvs/scans
   - POST /awvs/scan
   - POST /awvs/scans/{scanId}/stop
   - GET /awvs/vulnerabilities/{targetId}
   - GET /awvs/vulnerability/{vulnId}
   - GET /awvs/vulnerabilities/rank
   - GET /awvs/vulnerabilities/stats
   - GET /awvs/middleware/poc-list
   - GET /awvs/middleware/scans
   - POST /awvs/middleware/scan
   - POST /awvs/middleware/scan/start
   - POST /awvs/middleware/scans/{scanId}/stop
   - GET /awvs/health

7. **AI对话** (3个端点)
   - POST /ai/chat
   - POST /ai/analyze
   - POST /ai/poc/generate

8. **Agent管理** (13个端点)
   - GET /agent/list
   - GET /agent/{agentId}/status
   - POST /agent/execute
   - GET /agent/types
   - GET /agent/{agentId}
   - POST /agent/create
   - PUT /agent/{agentId}
   - DELETE /agent/{agentId}
   - GET /agent/tasks/{taskId}
   - DELETE /agent/tasks/{taskId}
   - GET /agent/task/{taskId}/logs
   - GET /agent/tasks/frozen
   - GET /agent/tasks/{taskId}/vulnerabilities

9. **知识库** (9个端点)
   - GET /kb/vulnerabilities
   - POST /kb/vulnerabilities
   - GET /kb/vulnerabilities/{knowledgeId}
   - PUT /kb/vulnerabilities/{knowledgeId}
   - DELETE /kb/vulnerabilities/{knowledgeId}
   - POST /kb/sync
   - POST /kb/seebug/poc/search
   - POST /kb/seebug/poc/download
   - GET /kb/seebug/poc/{ssvid}/detail

10. **POC生成** (2个端点)
   - POST /poc_gen/generate
   - POST /poc_gen/validate

11. **用户管理** (4个端点)
   - GET /user/profile
   - PUT /user/profile
   - GET /user/permissions
   - GET /user/list

12. **通知管理** (5个端点)
   - GET /notifications/
   - GET /notifications/{notificationId}
   - POST /notifications/
   - PUT /notifications/{notificationId}/read
   - PUT /notifications/read-all

13. **AI Agents** (15个端点)
   - POST /ai_agents/scan
   - GET /ai_agents/tasks
   - GET /ai_agents/tasks/{task_id}
   - POST /ai_agents/tasks/{task_id}/cancel
   - DELETE /ai_agents/tasks/{task_id}
   - GET /ai_agents/tools
   - GET /ai_agents/config
   - POST /ai_agents/config
   - POST /ai_agents/code/generate
   - POST /ai_agents/code/execute
   - POST /ai_agents/code/generate-and-execute
   - POST /ai_agents/capabilities/enhance
   - GET /ai_agents/capabilities/list
   - GET /ai_agents/environment/info
   - GET /ai_agents/environment/tools

14. **WebSocket** (1个端点)
   - WS /api/ws

**总计**: 120+ 个API端点

---

### B. 数据模型

#### Task模型
```json
{
  "id": 123,
  "task_name": "综合扫描任务",
  "target": "http://example.com",
  "task_type": "comprehensive",
  "status": "running",
  "progress": 45,
  "config": {...},
  "result": {...},
  "created_at": "2026-02-22T10:00:00Z",
  "updated_at": "2026-02-22T10:30:00Z"
}
```

#### Vulnerability模型
```json
{
  "id": 456,
  "task_id": 123,
  "vuln_type": "SQL Injection",
  "severity": "High",
  "title": "SQL注入漏洞",
  "description": "...",
  "url": "http://example.com/admin",
  "status": "open",
  "remediation": "使用参数化查询",
  "source_id": "1234567890"
}
```

#### Report模型
```json
{
  "id": 789,
  "task_id": 123,
  "report_name": "扫描报告",
  "report_type": "html",
  "content": "{...}",
  "created_at": "2026-02-22T10:00:00Z",
  "updated_at": "2026-02-22T10:00:00Z"
}
```

---

### C. 更新日志

#### v1.0.0 (2026-02-22)
- 初始版本，包含所有120+个API端点的完整文档
- 提供详细的功能描述、请求参数、响应格式、错误码及示例
- 包含WebSocket通信协议
- 包含安全建议和使用示例

---

**文档版本**: 1.0.0
**最后更新**: 2026-02-22
**维护者**: AI Assistant

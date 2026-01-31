# WebScan AI Security Platform - API接口文档

## 概述

本文档详细列出了WebScan AI Security Platform的所有后端API接口，包括功能描述、请求方法、请求参数、响应格式等信息。

## API基础信息

- **基础URL**: `http://127.0.0.1:3000/api`
- **响应格式**: JSON
- **认证方式**: Bearer Token (可选)

## 1. 扫描功能 (/api/scan)

### 1.1 端口扫描
- **接口**: `POST /api/scan/port-scan`
- **功能**: 执行端口扫描
- **请求参数**:
  ```json
  {
    "target": "目标IP或域名",
    "ports": "端口范围，可选"
  }
  ```

### 1.2 信息泄露检测
- **接口**: `POST /api/scan/info-leak`
- **功能**: 检测信息泄露

### 1.3 Web侧栏扫描
- **接口**: `POST /api/scan/web-side`
- **功能**: 执行Web侧栏扫描

### 1.4 基础信息获取
- **接口**: `POST /api/scan/baseinfo`
- **功能**: 获取目标基础信息

### 1.5 Web权重检测
- **接口**: `POST /api/scan/web-weight`
- **功能**: 检测Web权重

### 1.6 IP定位
- **接口**: `POST /api/scan/ip-locating`
- **功能**: 定位IP地址

### 1.7 CDN检测
- **接口**: `POST /api/scan/cdn-check`
- **功能**: 检测是否使用CDN

### 1.8 WAF检测
- **接口**: `POST /api/scan/waf-check`
- **功能**: 检测Web应用防火墙

### 1.9 CMS识别
- **接口**: `POST /api/scan/what-cms`
- **功能**: 识别CMS类型

### 1.10 子域名扫描
- **接口**: `POST /api/scan/subdomain`
- **功能**: 扫描子域名

### 1.11 目录扫描
- **接口**: `POST /api/scan/dir-scan`
- **功能**: 扫描目录和文件

### 1.12 综合扫描
- **接口**: `POST /api/scan/comprehensive`
- **功能**: 执行综合扫描

## 2. 任务管理 (/api/tasks)

### 2.1 创建任务
- **接口**: `POST /api/tasks/create`
- **功能**: 创建新的扫描任务
- **请求参数**:
  ```json
  {
    "task_name": "任务名称",
    "target": "扫描目标",
    "task_type": "任务类型",
    "config": {}
  }
  ```

### 2.2 获取任务列表
- **接口**: `GET /api/tasks/`
- **功能**: 获取任务列表
- **查询参数**:
  - `status`: 任务状态过滤
  - `task_type`: 任务类型过滤
  - `start_date`: 起始日期
  - `end_date`: 结束日期
  - `search`: 搜索关键词
  - `skip`: 跳过记录数
  - `limit`: 返回记录数

### 2.3 获取任务详情
- **接口**: `GET /api/tasks/{task_id}`
- **功能**: 获取单个任务详情

### 2.4 更新任务
- **接口**: `PUT /api/tasks/{task_id}`
- **功能**: 更新任务状态和进度

### 2.5 删除任务
- **接口**: `DELETE /api/tasks/{task_id}`
- **功能**: 删除指定任务

### 2.6 获取任务结果
- **接口**: `GET /api/tasks/{task_id}/results`
- **功能**: 获取任务的详细扫描结果

### 2.7 取消任务
- **接口**: `POST /api/tasks/{task_id}/cancel`
- **功能**: 取消正在运行的任务

### 2.8 获取任务漏洞
- **接口**: `GET /api/tasks/{task_id}/vulnerabilities`
- **功能**: 获取任务相关的漏洞列表
- **查询参数**:
  - `type`: 漏洞类型过滤
  - `source`: 漏洞来源过滤
  - `severity`: 严重程度过滤
  - `skip`: 跳过记录数
  - `limit`: 返回记录数

### 2.9 获取统计概览
- **接口**: `GET /api/tasks/statistics/overview`
- **功能**: 获取任务统计概览

## 3. 报告管理 (/api/reports)

### 3.1 获取报告列表
- **接口**: `GET /api/reports/`
- **功能**: 获取报告列表
- **查询参数**:
  - `task_id`: 关联任务ID
  - `report_type`: 报告类型
  - `skip`: 跳过记录数
  - `limit`: 返回记录数

### 3.2 创建报告
- **接口**: `POST /api/reports/`
- **功能**: 创建新的扫描报告

### 3.3 获取报告详情
- **接口**: `GET /api/reports/{report_id}`
- **功能**: 获取单个报告详情

### 3.4 更新报告
- **接口**: `PUT /api/reports/{report_id}`
- **功能**: 更新报告信息

### 3.5 删除报告
- **接口**: `DELETE /api/reports/{report_id}`
- **功能**: 删除指定报告

### 3.6 导出报告
- **接口**: `GET /api/reports/{report_id}/export`
- **功能**: 导出报告为指定格式
- **查询参数**:
  - `format`: 导出格式 (json/html/pdf)

## 4. POC扫描 (/api/poc)

### 4.1 获取POC类型列表
- **接口**: `GET /api/poc/types`
- **功能**: 获取所有可用的POC类型
- **响应示例**:
  ```json
  {
    "code": 200,
    "message": "获取成功",
    "data": [
      {
        "value": "weblogic_cve_2020_2551",
        "label": "Weblogic Cve 2020 2551"
      }
    ]
  }
  ```

### 4.2 创建POC扫描任务
- **接口**: `POST /api/poc/scan`
- **功能**: 创建POC扫描任务
- **请求参数**:
  ```json
  {
    "target": "扫描目标URL",
    "poc_types": ["POC类型列表"],
    "timeout": 10
  }
  ```

### 4.3 执行单个POC扫描
- **接口**: `POST /api/poc/scan/{poc_type}`
- **功能**: 执行单个POC漏洞扫描

### 4.4 获取POC详细信息
- **接口**: `GET /api/poc/info/{poc_type}`
- **功能**: 获取指定POC类型的详细信息

## 5. AWVS漏洞扫描 (/api/awvs)

### 5.1 获取扫描列表
- **接口**: `GET /api/awvs/scans`
- **功能**: 获取AWVS扫描任务列表

### 5.2 获取目标漏洞
- **接口**: `GET /api/awvs/vulnerabilities/{target_id}`
- **功能**: 获取指定目标的漏洞列表

### 5.3 获取漏洞详情
- **接口**: `GET /api/awvs/vulnerability/{vuln_id}`
- **功能**: 获取单个漏洞的详细信息

### 5.4 启动扫描
- **接口**: `POST /api/awvs/scan`
- **功能**: 启动AWVS扫描任务

### 5.5 获取漏洞排名
- **接口**: `GET /api/awvs/vulnerabilities/rank`
- **功能**: 获取漏洞排名

### 5.6 获取漏洞统计
- **接口**: `GET /api/awvs/vulnerabilities/stats`
- **功能**: 获取漏洞统计信息

### 5.7 获取目标列表
- **接口**: `GET /api/awvs/targets`
- **功能**: 获取AWVS目标列表

### 5.8 创建目标
- **接口**: `POST /api/awvs/target`
- **功能**: 创建新的AWVS扫描目标

### 5.9 健康检查
- **接口**: `GET /api/awvs/health`
- **功能**: 检查AWVS服务健康状态

### 5.10 中间件扫描
- **接口**: `POST /api/awvs/middleware/scan`
- **功能**: 执行中间件漏洞扫描

### 5.11 启动中间件扫描
- **接口**: `POST /api/awvs/middleware/scan/start`
- **功能**: 启动中间件扫描任务

### 5.12 获取中间件扫描列表
- **接口**: `GET /api/awvs/middleware/scans`
- **功能**: 获取中间件扫描历史

### 5.13 获取POC列表
- **接口**: `GET /api/awvs/middleware/poc-list`
- **功能**: 获取可用的POC列表

## 6. 系统设置 (/api/settings)

### 6.1 获取设置
- **接口**: `GET /api/settings/`
- **功能**: 获取系统设置

### 6.2 更新设置
- **接口**: `PUT /api/settings/`
- **功能**: 更新系统设置

### 6.3 获取设置项
- **接口**: `GET /api/settings/item/{category}/{key}`
- **功能**: 获取指定设置项

### 6.4 更新设置项
- **接口**: `PUT /api/settings/item`
- **功能**: 更新指定设置项

### 6.5 删除设置项
- **接口**: `DELETE /api/settings/item/{category}/{key}`
- **功能**: 删除指定设置项

### 6.6 获取系统信息
- **接口**: `GET /api/settings/system-info`
- **功能**: 获取系统信息

### 6.7 获取统计信息
- **接口**: `GET /api/settings/statistics`
- **功能**: 获取系统统计信息
- **查询参数**:
  - `period`: 统计周期 (7/30/90)

### 6.8 获取分类列表
- **接口**: `GET /api/settings/categories`
- **功能**: 获取设置分类列表

### 6.9 获取分类设置
- **接口**: `GET /api/settings/category/{category}`
- **功能**: 获取指定分类的所有设置

### 6.10 重置设置
- **接口**: `POST /api/settings/reset`
- **功能**: 重置所有设置

### 6.11 重置分类设置
- **接口**: `POST /api/settings/reset/{category}`
- **功能**: 重置指定分类的设置

### 6.12 获取API密钥列表
- **接口**: `GET /api/settings/api-keys`
- **功能**: 获取所有API密钥

### 6.13 创建API密钥
- **接口**: `POST /api/settings/api-keys`
- **功能**: 创建新的API密钥

### 6.14 删除API密钥
- **接口**: `DELETE /api/settings/api-keys/{key_id}`
- **功能**: 删除指定API密钥

### 6.15 重新生成API密钥
- **接口**: `PUT /api/settings/api-keys/{key_id}/regenerate`
- **功能**: 重新生成API密钥

## 7. AI对话 (/api/ai)

### 7.1 创建聊天实例
- **接口**: `POST /api/ai/chat/instances`
- **功能**: 创建新的AI聊天实例

### 7.2 获取聊天实例列表
- **接口**: `GET /api/ai/chat/instances`
- **功能**: 获取所有聊天实例

### 7.3 获取聊天实例详情
- **接口**: `GET /api/ai/chat/instances/{chat_instance_id}`
- **功能**: 获取单个聊天实例详情

### 7.4 删除聊天实例
- **接口**: `DELETE /api/ai/chat/instances/{chat_instance_id}`
- **功能**: 删除指定聊天实例

### 7.5 发送消息
- **接口**: `POST /api/ai/chat/instances/{chat_instance_id}/messages`
- **功能**: 向聊天实例发送消息

### 7.6 获取消息列表
- **接口**: `GET /api/ai/chat/instances/{chat_instance_id}/messages`
- **功能**: 获取聊天消息列表

### 7.7 关闭聊天
- **接口**: `POST /api/ai/chat/instances/{chat_instance_id}/close`
- **功能**: 关闭聊天实例

## 8. Agent功能 (/api/agent)

### 8.1 执行Agent任务
- **接口**: `POST /api/agent/run`
- **功能**: 执行AI Agent任务

### 8.2 获取Agent任务详情
- **接口**: `GET /api/agent/tasks/{task_id}`
- **功能**: 获取Agent任务详情

### 8.3 获取Agent任务列表
- **接口**: `GET /api/agent/tasks`
- **功能**: 获取Agent任务列表

## 9. 漏洞知识库 (/api/kb)

### 9.1 获取漏洞列表
- **接口**: `GET /api/kb/vulnerabilities`
- **功能**: 获取知识库漏洞列表
- **查询参数**:
  - `search`: 搜索关键词
  - `severity`: 严重程度过滤
  - `skip`: 跳过记录数
  - `limit`: 返回记录数

### 9.2 获取漏洞详情
- **接口**: `GET /api/kb/vulnerabilities/{kb_id}`
- **功能**: 获取单个漏洞详情

### 9.3 搜索Seebug POC
- **接口**: `POST /api/kb/seebug/poc/search`
- **功能**: 在Seebug平台搜索POC

### 9.4 下载Seebug POC
- **接口**: `POST /api/kb/seebug/poc/download`
- **功能**: 从Seebug平台下载POC

### 9.5 获取Seebug POC详情
- **接口**: `GET /api/kb/seebug/poc/{ssvid}/detail`
- **功能**: 获取Seebug POC详细信息

### 9.6 同步知识库
- **接口**: `POST /api/kb/sync`
- **功能**: 同步漏洞知识库

## 10. POC智能生成 (/api/poc-gen)

### 10.1 生成POC
- **接口**: `POST /api/poc-gen/generate`
- **功能**: 使用AI生成POC

### 10.2 执行POC
- **接口**: `POST /api/poc-gen/execute`
- **功能**: 执行生成的POC

## 11. 用户管理 (/api/user)

### 11.1 获取用户信息
- **接口**: `GET /api/user/profile`
- **功能**: 获取当前用户信息
- **查询参数**:
  - `user_id`: 用户ID (可选，默认为1)

### 11.2 更新用户信息
- **接口**: `PUT /api/user/profile`
- **功能**: 更新用户信息
- **查询参数**:
  - `user_id`: 用户ID (可选，默认为1)

### 11.3 获取用户权限
- **接口**: `GET /api/user/permissions`
- **功能**: 获取用户权限列表
- **查询参数**:
  - `user_id`: 用户ID (可选，默认为1)

### 11.4 获取用户列表
- **接口**: `GET /api/user/list`
- **功能**: 获取用户列表
- **查询参数**:
  - `search`: 搜索关键词
  - `role`: 角色过滤
  - `skip`: 跳过记录数
  - `limit`: 返回记录数

## 12. 通知管理 (/api/notifications)

### 12.1 获取通知列表
- **接口**: `GET /api/notifications/`
- **功能**: 获取通知列表
- **查询参数**:
  - `status`: 状态过滤 (unread/read)
  - `type`: 类型过滤
  - `skip`: 跳过记录数
  - `limit`: 返回记录数

### 12.2 获取通知详情
- **接口**: `GET /api/notifications/{notification_id}`
- **功能**: 获取单个通知详情

### 12.3 创建通知
- **接口**: `POST /api/notifications/`
- **功能**: 创建新通知

### 12.4 标记通知为已读
- **接口**: `PUT /api/notifications/{notification_id}/read`
- **功能**: 标记指定通知为已读

### 12.5 标记所有通知为已读
- **接口**: `PUT /api/notifications/read-all`
- **功能**: 标记所有通知为已读

### 12.6 删除通知
- **接口**: `DELETE /api/notifications/{notification_id}`
- **功能**: 删除指定通知

### 12.7 删除所有已读通知
- **接口**: `DELETE /api/notifications/`
- **功能**: 删除所有已读通知

### 12.8 获取未读通知数量
- **接口**: `GET /api/notifications/count/unread`
- **功能**: 获取未读通知数量

## 13. AI Agents (/api/ai_agents)

### 13.1 启动Agent扫描
- **接口**: `POST /api/ai_agents/scan`
- **功能**: 启动AI Agent扫描任务
- **请求参数**:
  ```json
  {
    "target": "扫描目标",
    "enable_llm_planning": true,
    "custom_tasks": [],
    "need_custom_scan": false,
    "need_capability_enhancement": false
  }
  ```

### 13.2 获取Agent任务详情
- **接口**: `GET /api/ai_agents/tasks/{task_id}`
- **功能**: 获取Agent任务详情

### 13.3 获取Agent任务列表
- **接口**: `GET /api/ai_agents/tasks`
- **功能**: 获取Agent任务列表
- **查询参数**:
  - `status`: 状态过滤
  - `task_type`: 任务类型过滤
  - `page`: 页码
  - `page_size`: 每页数量

### 13.4 取消Agent任务
- **接口**: `DELETE /api/ai_agents/tasks/{task_id}`
- **功能**: 取消Agent任务

### 13.5 获取可用工具列表
- **接口**: `GET /api/ai_agents/tools`
- **功能**: 获取所有可用工具
- **查询参数**:
  - `category`: 工具分类过滤 (plugin/poc/general)

### 13.6 获取Agent配置
- **接口**: `GET /api/ai_agents/config`
- **功能**: 获取Agent配置

### 13.7 更新Agent配置
- **接口**: `POST /api/ai_agents/config`
- **功能**: 更新Agent配置

### 13.8 生成代码
- **接口**: `POST /api/ai_agents/code/generate`
- **功能**: 生成扫描代码

### 13.9 执行代码
- **接口**: `POST /api/ai_agents/code/execute`
- **功能**: 执行代码

### 13.10 生成并执行代码
- **接口**: `POST /api/ai_agents/code/generate-and-execute`
- **功能**: 生成并执行代码

### 13.11 增强功能
- **接口**: `POST /api/ai_agents/capabilities/enhance`
- **功能**: 增强Agent功能

### 13.12 列出所有能力
- **接口**: `GET /api/ai_agents/capabilities/list`
- **功能**: 列出所有能力

### 13.13 获取能力详情
- **接口**: `GET /api/ai_agents/capabilities/{capability_name}`
- **功能**: 获取能力详情

### 13.14 删除能力
- **接口**: `DELETE /api/ai_agents/capabilities/{capability_name}`
- **功能**: 删除能力

### 13.15 获取环境信息
- **接口**: `GET /api/ai_agents/environment/info`
- **功能**: 获取环境信息

### 13.16 获取环境工具
- **接口**: `GET /api/ai_agents/environment/tools`
- **功能**: 获取环境工具列表

### 13.17 获取工具详情
- **接口**: `GET /api/ai_agents/environment/tools/{tool_name}`
- **功能**: 获取工具详情

## 14. POC验证 (/api/poc-verification)

### 14.1 创建POC验证任务
- **接口**: `POST /api/poc-verification/tasks`
- **功能**: 创建POC验证任务

### 14.2 批量创建POC验证任务
- **接口**: `POST /api/poc-verification/tasks/batch`
- **功能**: 批量创建POC验证任务

### 14.3 获取POC验证任务列表
- **接口**: `GET /api/poc-verification/tasks`
- **功能**: 获取POC验证任务列表

### 14.4 获取POC验证任务详情
- **接口**: `GET /api/poc-verification/tasks/{task_id}`
- **功能**: 获取POC验证任务详情

### 14.5 暂停任务
- **接口**: `POST /api/poc-verification/tasks/{task_id}/pause`
- **功能**: 暂停POC验证任务

### 14.6 恢复任务
- **接口**: `POST /api/poc-verification/tasks/{task_id}/resume`
- **功能**: 恢复POC验证任务

### 14.7 取消任务
- **接口**: `POST /api/poc-verification/tasks/{task_id}/cancel`
- **功能**: 取消POC验证任务

### 14.8 获取任务结果
- **接口**: `GET /api/poc-verification/tasks/{task_id}/results`
- **功能**: 获取POC验证任务结果

### 14.9 生成报告
- **接口**: `POST /api/poc-verification/tasks/{task_id}/report`
- **功能**: 生成POC验证报告

### 14.10 获取统计信息
- **接口**: `GET /api/poc-verification/statistics`
- **功能**: 获取POC验证统计信息

### 14.11 获取POC注册表
- **接口**: `GET /api/poc-verification/poc/registry`
- **功能**: 获取POC注册表

### 14.12 同步POC
- **接口**: `POST /api/poc-verification/poc/sync`
- **功能**: 同步POC

### 14.13 健康检查
- **接口**: `GET /api/poc-verification/health`
- **功能**: POC验证服务健康检查

## 15. POC文件管理 (/api/poc-files)

### 15.1 获取POC文件列表
- **接口**: `GET /api/poc-files/list`
- **功能**: 获取POC文件列表
- **查询参数**:
  - `directory`: 目录路径
  - `recursive`: 是否递归

### 15.2 获取文件内容
- **接口**: `GET /api/poc-files/content/{file_path:path}`
- **功能**: 获取POC文件内容

### 15.3 获取文件信息
- **接口**: `GET /api/poc-files/info/{file_path:path}`
- **功能**: 获取POC文件信息

### 15.4 获取目录列表
- **接口**: `GET /api/poc-files/directories`
- **功能**: 获取POC目录列表

### 15.5 同步文件
- **接口**: `POST /api/poc-files/sync`
- **功能**: 同步POC文件

### 15.6 获取同步状态
- **接口**: `GET /api/poc-files/sync/status`
- **功能**: 获取文件同步状态

## 16. Seebug Agent (/api/seebug)

### 16.1 获取Seebug Agent状态
- **接口**: `GET /api/seebug/status`
- **功能**: 获取Seebug Agent运行状态

### 16.2 搜索漏洞
- **接口**: `POST /api/seebug/search`
- **功能**: 在Seebug平台搜索漏洞

### 16.3 获取漏洞详情
- **接口**: `GET /api/seebug/vulnerability/{ssvid}`
- **功能**: 获取Seebug漏洞详情

### 16.4 生成POC
- **接口**: `POST /api/seebug/generate-poc`
- **功能**: 使用Seebug Agent生成POC

### 16.5 获取POC生成状态
- **接口**: `GET /api/seebug/generate-poc/{ssvid}`
- **功能**: 获取POC生成状态

### 16.6 测试连接
- **接口**: `GET /api/seebug/test-connection`
- **功能**: 测试Seebug API连接

## 统一响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

### 错误响应
```json
{
  "code": 400/404/500,
  "message": "错误描述",
  "error": "详细错误信息"
}
```

## 状态码说明

- **200**: 请求成功
- **400**: 请求参数错误
- **401**: 未授权
- **404**: 资源不存在
- **500**: 服务器内部错误

## 任务状态说明

- **pending**: 待执行
- **running**: 执行中
- **completed**: 已完成
- **failed**: 失败
- **cancelled**: 已取消

## 漏洞严重程度说明

- **Critical**: 严重
- **High**: 高危
- **Medium**: 中危
- **Low**: 低危
- **Info**: 信息

## 任务类型说明

- **awvs_scan**: AWVS扫描
- **poc_scan**: POC扫描
- **scan_dir**: 目录扫描
- **scan_webside**: Web侧栏扫描
- **scan_port**: 端口扫描
- **scan_cms**: CMS识别
- **scan_comprehensive**: 综合扫描
- **agent_scan**: Agent扫描

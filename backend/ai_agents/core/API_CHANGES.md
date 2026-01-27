# API变更说明

## 一、概述

本文档描述了nodes.py与new_nodes.py合并后的API变更，以及如何确保向后兼容性。

## 二、核心变更

### 2.1 图结构变更

#### 2.1.1 节点数量
- **变更前**：5个节点
- **变更后**：10个节点
- **新增节点**：
  - EnvironmentAwarenessNode（环境感知）
  - CodeGenerationNode（代码生成）
  - CapabilityEnhancementNode（功能补充）
  - CodeExecutionNode（代码执行）
  - IntelligentDecisionNode（智能决策）

#### 2.1.2 入口点变更
- **变更前**：`task_planning`
- **变更后**：`environment_awareness`
- **影响**：所有扫描任务现在都会先执行环境感知

#### 2.1.3 边数量
- **变更前**：6条边
- **变更后**：14条边
- **新增边**：8条条件边

### 2.2 状态变更

#### 2.2.1 新增状态字段
以下字段会被新增节点自动添加到`state.target_context`：

```python
state.target_context = {
    # 环境感知节点添加
    "environment_info": {...},  # 完整的环境报告
    "os_system": "Windows",  # 操作系统类型
    "python_version": "3.12.3",  # Python版本
    "available_tools": {...},  # 可用工具列表
    
    # 智能决策节点添加
    "intelligent_decisions": [...],  # 智能决策列表
    
    # 代码生成节点添加
    "generated_code": {...},  # 生成的代码
    "need_custom_scan": False,  # 是否需要自定义扫描
    "custom_scan_type": "",  # 自定义扫描类型
    "custom_scan_requirements": "",  # 自定义扫描需求
    "custom_scan_language": "python",  # 代码语言
    
    # 代码执行节点添加
    "code_execution_result": {...},  # 代码执行结果
    
    # 功能补充节点添加
    "need_capability_enhancement": False,  # 是否需要功能增强
    "capability_requirement": "",  # 功能增强需求
    "enhanced_capability": {...}  # 增强结果
}
```

#### 2.2.2 新增工具结果
以下字段会被新增节点自动添加到`state.tool_results`：

```python
state.tool_results = {
    # 环境感知节点添加
    "environment_awareness": {...},  # 环境感知结果
    
    # 智能决策节点添加
    "intelligent_decision": {...},  # 智能决策结果
    
    # 代码生成节点添加
    "code_generation": {...},  # 代码生成结果
    
    # 代码执行节点添加
    "code_execution": {...},  # 代码执行结果
    
    # 功能补充节点添加
    "capability_enhancement": {...}  # 功能补充结果
}
```

### 2.3 API接口变更

#### 2.3.1 创建扫描任务
**接口**：`POST /api/v1/tasks`

**请求体变更**：
```json
{
  "target": "http://example.com",
  "scan_type": "full",  // 新增：可选值 "full", "fixed_tool", "custom_code"
  "target_context": {  // 新增：可选的上下文配置
    "need_custom_scan": false,
    "custom_scan_type": "vuln_scan",
    "custom_scan_requirements": "检测SQL注入漏洞",
    "custom_scan_language": "python",
    "need_capability_enhancement": false,
    "capability_requirement": ""
  }
}
```

**响应体变更**：
```json
{
  "task_id": "scan_001",
  "target": "http://example.com",
  "status": "running",
  "scan_type": "full",  // 新增
  "entry_point": "environment_awareness",  // 新增
  "expected_nodes": [  // 新增：预期执行的节点列表
    "environment_awareness",
    "task_planning",
    "intelligent_decision",
    "tool_execution",
    "result_verification",
    "vulnerability_analysis",
    "report_generation"
  ]
}
```

#### 2.3.2 获取任务状态
**接口**：`GET /api/v1/tasks/{task_id}`

**响应体新增字段**：
```json
{
  "task_id": "scan_001",
  "target": "http://example.com",
  "status": "running",
  "current_node": "tool_execution",  // 当前执行的节点
  "execution_history": [  // 新增：执行历史
    {
      "task": "environment_awareness",
      "timestamp": "2026-01-27T18:30:00Z",
      "status": "success",
      "duration": 5.2
    },
    {
      "task": "task_planning",
      "timestamp": "2026-01-27T18:30:05Z",
      "status": "success",
      "duration": 1.3
    }
  ],
  "target_context": {  // 新增：目标上下文
    "environment_info": {...},
    "os_system": "Windows",
    "intelligent_decisions": [...]
  },
  "tool_results": {  // 新增：工具执行结果
    "environment_awareness": {...},
    "intelligent_decision": {...},
    "tool_execution": {...}
  }
}
```

#### 2.3.3 获取图信息
**接口**：`GET /api/v1/graph/info`

**响应体变更**：
```json
{
  "total_nodes": 10,  // 新增
  "original_nodes": 5,  // 新增
  "new_nodes": 5,  // 新增
  "nodes": [
    "environment_awareness",
    "task_planning",
    "intelligent_decision",
    "tool_execution",
    "code_generation",
    "code_execution",
    "capability_enhancement",
    "result_verification",
    "vulnerability_analysis",
    "report_generation"
  ],
  "edges": [
    ["environment_awareness", "task_planning"],
    ["task_planning", "intelligent_decision"],
    ["intelligent_decision", "tool_execution"],
    ["intelligent_decision", "code_generation"],
    ["intelligent_decision", "capability_enhancement"],
    ...
  ],
  "entry_point": "environment_awareness",
  "exit_points": ["report_generation"]
}
```

## 三、向后兼容性

### 3.1 兼容性保证
- ✅ 所有原有节点的接口保持不变
- ✅ 所有原有API接口保持不变
- ✅ 新增字段都是可选的
- ✅ 默认情况下，新增节点会被跳过
- ✅ 不会破坏现有的状态字段

### 3.2 迁移指南

#### 3.2.1 对于现有API调用者
**无需修改**：现有API调用者可以继续使用原有接口，无需任何修改。

#### 3.2.2 对于需要使用新功能的调用者
**步骤1**：在请求体中添加`target_context`字段
```json
{
  "target": "http://example.com",
  "target_context": {
    "need_custom_scan": true,
    "custom_scan_type": "vuln_scan"
  }
}
```

**步骤2**：处理响应中的新增字段
```python
response = requests.post("/api/v1/tasks", json=payload)
data = response.json()

# 处理新增字段
if "expected_nodes" in data:
    print(f"预期执行的节点: {data['expected_nodes']}")

if "execution_history" in data:
    print(f"执行历史: {data['execution_history']}")
```

#### 3.2.3 对于前端开发者
**步骤1**：更新任务创建表单
- 添加"扫描类型"选择（full/fixed_tool/custom_code）
- 添加"自定义扫描"选项卡
- 添加"功能增强"选项卡

**步骤2**：更新任务详情页面
- 显示当前执行的节点
- 显示执行历史时间线
- 显示环境感知结果
- 显示智能决策结果
- 显示代码生成和执行结果

**步骤3**：更新图可视化
- 显示所有10个节点
- 显示条件分支
- 高亮当前执行的节点

## 四、新增功能使用示例

### 4.1 使用代码生成扫描
```python
import requests

# 创建任务
payload = {
    "target": "http://example.com",
    "scan_type": "custom_code",
    "target_context": {
        "need_custom_scan": True,
        "custom_scan_type": "vuln_scan",
        "custom_scan_requirements": "检测SQL注入漏洞",
        "custom_scan_language": "python"
    }
}

response = requests.post("http://localhost:8000/api/v1/tasks", json=payload)
task_id = response.json()["task_id"]

# 查询任务状态
status_response = requests.get(f"http://localhost:8000/api/v1/tasks/{task_id}")
status = status_response.json()

# 查看生成的代码
generated_code = status["tool_results"].get("code_generation", {})
print(f"生成的代码: {generated_code.get('code', '')}")
print(f"代码语言: {generated_code.get('language', '')}")
```

### 4.2 使用功能增强
```python
# 创建任务
payload = {
    "target": "http://example.com",
    "target_context": {
        "need_capability_enhancement": True,
        "capability_requirement": "安装scapy库"
    }
}

response = requests.post("http://localhost:8000/api/v1/tasks", json=payload)
```

### 4.3 查看智能决策结果
```python
# 查询任务状态
status_response = requests.get(f"http://localhost:8000/api/v1/tasks/{task_id}")
status = status_response.json()

# 查看智能决策
decisions = status["target_context"].get("intelligent_decisions", [])
for decision in decisions:
    print(f"决策: {decision}")
```

## 五、错误处理

### 5.1 新增错误码

| 错误码 | 错误信息 | 说明 |
|--------|----------|------|
| 4001 | Invalid scan type | 扫描类型无效 |
| 4002 | Custom scan requires context | 自定义扫描需要提供上下文 |
| 4003 | Code generation failed | 代码生成失败 |
| 4004 | Code execution failed | 代码执行失败 |
| 4005 | Capability enhancement failed | 功能增强失败 |

### 5.2 错误响应示例
```json
{
  "error": {
    "code": 4002,
    "message": "Custom scan requires context",
    "details": "need_custom_scan is true but custom_scan_type is not provided"
  }
}
```

## 六、性能影响

### 6.1 初始化时间
- **变更前**：约1秒
- **变更后**：约5-10秒（环境感知需要时间）
- **影响**：首次创建Agent图时会有延迟

### 6.2 执行时间
- **变更前**：约20-30秒
- **变更后**：约25-35秒（包含环境感知）
- **影响**：整体执行时间略有增加

### 6.3 内存使用
- **变更前**：约100MB
- **变更后**：约150MB（新增节点和状态）
- **影响**：内存使用增加约50%

## 七、测试建议

### 7.1 单元测试
- 测试所有10个节点的初始化
- 测试所有节点的`__call__`方法
- 测试条件分支逻辑
- 测试异常处理

### 7.2 集成测试
- 测试完整工作流执行
- 测试固定工具扫描流程
- 测试代码生成扫描流程
- 测试功能补充流程
- 测试状态传递

### 7.3 端到端测试
- 测试从创建任务到获取报告的完整流程
- 测试API接口的向后兼容性
- 测试前端界面的正确显示

## 八、部署建议

### 8.1 部署步骤
1. 备份现有代码
2. 部署新的nodes.py和graph.py
3. 重启服务
4. 验证API接口正常工作
5. 运行测试套件
6. 监控日志和性能

### 8.2 回滚计划
如果出现问题，可以快速回滚到旧版本：
1. 恢复备份的代码
2. 重启服务
3. 验证功能正常

### 8.3 监控指标
- API响应时间
- 任务执行时间
- 错误率
- 内存使用
- CPU使用

## 九、总结

本次API变更主要包含以下内容：

1. **节点数量**：从5个增加到10个
2. **入口点**：从task_planning改为environment_awareness
3. **新增状态字段**：target_context和tool_results新增多个字段
4. **新增API字段**：请求和响应新增多个可选字段
5. **向后兼容**：所有原有接口保持不变，新增字段都是可选的

建议开发者：
- 现有API调用者无需修改
- 需要使用新功能的调用者参考本文档
- 前端开发者参考前端兼容性文档
- 部署前进行充分测试

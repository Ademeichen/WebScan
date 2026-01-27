"""
AI Agents 代码执行模块 - README

提供环境感知、代码自动生成和功能补充能力。
"""

## 模块概述

本模块整合了代码执行沙箱功能，提供以下核心能力：

1. **环境感知**（EnvironmentAwareness）
   - 操作系统检测
   - Python版本和依赖检查
   - 可用工具检测
   - 网络状态检测
   - 磁盘空间和内存状态

2. **代码自动生成**（CodeGenerator）
   - 基于模板生成扫描脚本
   - 支持LLM增强代码生成
   - 支持多种扫描类型（端口扫描、漏洞扫描、目录扫描等）
   - 支持多种编程语言（Python、Bash、PowerShell）

3. **功能补充**（CapabilityEnhancer）
   - 根据需求动态生成功能补充代码
   - 支持新工具集成
   - 支持自定义扫描逻辑
   - 支持漏洞利用代码生成

4. **统一执行器**（UnifiedExecutor）
   - 整合环境感知、代码生成和功能补充能力
   - 提供安全的代码执行环境
   - 支持超时控制和资源限制
   - 支持多种编程语言

## 目录结构

```
code_execution/
├── __init__.py              # 模块入口
├── environment.py         # 环境感知模块
├── code_generator.py     # 代码自动生成模块
├── capability_enhancer.py # 功能补充模块
├── executor.py          # 统一执行器
└── workspace/           # 工作空间目录
```

## 使用示例

### 1. 环境感知

```python
from ai_agents.code_execution import EnvironmentAwareness

env = EnvironmentAwareness()
report = env.get_environment_report()

print(f"操作系统: {report['os_info']['system']}")
print(f"Python版本: {report['python_info']['version']}")
print(f"可用工具: {report['available_tools']}")
```

### 2. 代码生成

```python
from ai_agents.code_execution import CodeGenerator

generator = CodeGenerator()

# 使用模板生成
result = await generator.generate_code(
    scan_type="port_scan",
    target="https://www.baidu.com",
    language="python"
)

print(f"生成的代码:\n{result.code}")
```

### 3. 功能补充

```python
from ai_agents.code_execution import CapabilityEnhancer

enhancer = CapabilityEnhancer()

# 增强功能
result = await enhancer.enhance_capability(
    requirement="需要一个新的SQL注入扫描工具",
    target="https://www.baidu.com"
)

print(f"增强结果: {result}")
```

### 4. 统一执行器

```python
from ai_agents.code_execution import UnifiedExecutor

executor = UnifiedExecutor(
    timeout=60,
    enable_sandbox=True
)

# 执行代码
result = await executor.execute_code(
    code="print('Hello, World!')",
    language="python"
)

print(f"执行结果: {result.to_dict()}")
```

## API接口

### 1. 生成代码

**端点**：`POST /api/ai_agents/code/generate`

**请求示例**：
```json
{
  "scan_type": "port_scan",
  "target": "https://www.baidu.com",
  "requirements": "",
  "language": "python"
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "code": "#!/usr/bin/env python3\n...",
    "language": "python",
    "description": "基于模板生成的扫描脚本",
    "estimated_time": 60,
    "dependencies": []
  }
}
```

### 2. 执行代码

**端点**：`POST /api/ai_agents/code/execute`

**请求示例**：
```json
{
  "code": "print('Hello, World!')",
  "language": "python",
  "target": "https://www.baidu.com"
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "status": "success",
    "output": "Hello, World!\n",
    "error": "",
    "execution_time": 0.5,
    "exit_code": 0
  }
}
```

### 3. 增强功能

**端点**：`POST /api/ai_agents/capabilities/enhance`

**请求示例**：
```json
{
  "requirement": "需要一个新的SQL注入扫描工具",
  "target": "https://www.baidu.com"
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "enhancement": {
      "status": "success",
      "capability": {
        "name": "custom_20260123_120000",
        "description": "需要一个新的SQL注入扫描工具",
        "version": "1.0.0"
      }
    },
    "execution": {
      "status": "success",
      "data": {...}
    }
  }
}
```

### 4. 获取环境信息

**端点**：`GET /api/ai_agents/environment/info`

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "os_info": {
      "system": "Windows",
      "release": "10",
      "version": "10.0.19045",
      "machine": "AMD64",
      "processor": "Intel64 Family 6 Model 158",
      "architecture": ("64bit", "WindowsPE")
    },
    "python_info": {
      "version": "3.11.0",
      "executable": "C:\\Python311\\python.exe",
      "dependencies": {
        "langchain": "0.1.0",
        "langgraph": "0.0.26",
        "tortoise": "0.20.0",
        "fastapi": "0.104.1"
      }
    },
    "available_tools": {
      "nmap": {
        "name": "nmap",
        "available": false,
        "version": "unknown"
      },
      "sqlmap": {
        "name": "sqlmap",
        "available": false,
        "version": "unknown"
      }
    },
    "network_info": {
      "hostname": "DESKTOP-ABC123",
      "proxy_detected": false,
      "firewall_detected": false,
      "internet_available": true
    },
    "system_resources": {
      "disk_total": 500000000000,
      "disk_used": 250000000000,
      "disk_free": 250000000000,
      "disk_used_percent": 50.0
    },
    "scan_recommendations": [
      "建议使用PowerShell进行脚本执行",
      "建议启用LLM增强任务规划"
    ]
  }
}
```

### 5. 获取能力列表

**端点**：`GET /api/ai_agents/capabilities/list`

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "total": 2,
    "capabilities": [
      {
        "name": "custom_20260123_120000",
        "description": "需要一个新的SQL注入扫描工具",
        "version": "1.0.0",
        "dependencies": [],
        "created_at": "2026-01-23T12:00:00",
        "execution_count": 1
      }
    ]
  }
}
```

## 安全性

### 代码验证

所有代码在执行前都会进行安全性验证，检测以下危险操作：

- `eval(` - 代码注入
- `exec(` - 代码执行
- `system(` - 系统命令执行
- `__import__(` - 动态导入
- `subprocess.call(` - 子进程调用
- `os.system(` - 系统命令执行
- `shell=True` - Shell执行
- `rm -rf` - 危险文件操作
- `format ` - 磁盘格式化
- `pickle.loads` - 反序列化
- `yaml.load` - YAML加载

### 沙箱隔离

代码执行在沙箱环境中进行，提供以下保护：

- 文件系统隔离：限制对系统文件的访问
- 超时控制：防止无限循环
- 资源限制：限制CPU和内存使用
- 执行日志：记录所有执行操作

## 扩展开发

### 添加新的代码模板

在`code_generator.py`的`_get_template`方法中添加新模板：

```python
templates = {
    "my_custom_scan": """
#!/usr/bin/env python3
# 自定义扫描模板
def main():
    target = "{target}"
    # 扫描逻辑
    pass

if __name__ == "__main__":
    main()
"""
}
```

### 注册新的能力

使用`CapabilityEnhancer`注册新能力：

```python
from ai_agents.code_execution import CapabilityEnhancer

enhancer = CapabilityEnhancer()

async def my_custom_capability(target: str):
    return {"result": "success"}

enhancer.register_capability(
    name="my_custom_capability",
    description="我的自定义能力",
    execute_func=my_custom_capability,
    version="1.0.0"
)
```

## 性能优化

### 代码生成优化

- 使用模板缓存：避免重复生成相同模板
- LLM调用优化：减少不必要的LLM调用
- 并发生成：支持多个代码并发生成

### 执行优化

- 超时控制：防止长时间运行的代码
- 资源限制：限制CPU和内存使用
- 结果缓存：缓存执行结果

## 故障排查

### 常见问题

1. **代码生成失败**
   - 检查LLM配置是否正确
   - 检查网络连接
   - 可以使用模板生成作为备选

2. **代码执行失败**
   - 检查代码语法是否正确
   - 检查是否有危险操作
   - 查看执行日志中的详细错误

3. **功能补充失败**
   - 检查需求描述是否清晰
   - 检查是否有足够的资源
   - 查看增强日志中的详细错误

### 日志查看

所有代码执行日志记录在`logs/app.log`：

```bash
# 查看实时日志
tail -f logs/app.log

# 搜索特定任务的日志
grep "task_id: 123e4567" logs/app.log
```

## 总结

AI Agents代码执行模块提供了完整的代码生成和执行能力，具备：

✅ **环境感知**：全面了解执行环境
✅ **代码生成**：支持多种扫描类型的代码自动生成
✅ **功能补充**：动态增强AI Agent能力
✅ **安全执行**：沙箱隔离和代码验证
✅ **统一接口**：提供统一的代码执行接口
✅ **可扩展性**：支持模板扩展和能力注册

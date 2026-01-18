# Sandbox 核心业务执行层
# Services / Sandbox 核心业务执行层

本目录实现一个轻量化的“沙箱/执行层”服务，用于根据决策层（`decision` 目录）中的 JSON 工作流配置：

- 在执行器工作区生成脚本/文件；
- 调用本地解释器或系统命令执行这些脚本；
- 收集输出并生成执行报告（JSON）；
- 将执行日志写入 `backend/services/sandbox_execution.log`。

本文档包含目录结构、各文件作用、主要执行逻辑与核心代码说明，便于与其他执行器或上层模块集成。

## 目录结构

```
backend/services/
├─ __init__.py
├─ core_executor.py            # CodeExecutor：写/读/执行代码与命令的核心类
├─ run.py                     # CLI 入口：加载决策配置并执行工作流，生成报告
├─ test_sandbox.py            # 测试/示例脚本（本地调试用）
├─ README.md                  # 本文件
├─ sandbox_execution.log      # 运行日志（run.py 写入）
├─ decision/                  # 决策层 JSON 配置（任务定义）
│  ├─ default_task.json
│  └─ ...
└─ executor_workspace/        # 运行时工作区（生成的脚本、reports/）
     ├─ reports/
     └─ ...
```

## 快速开始 / 运行

在项目根目录下（或切换到 `backend/services`）执行：

```bash
python backend/services/run.py
```

- 日志文件（`sandbox_execution.log`）会写入 `backend/services/`。
- 执行报告会保存在 `backend/services/executor_workspace/reports/`，以 `execution_report_YYYYMMDD_HHMMSS.json` 命名。

## 主要文件与职责说明

- `__init__.py`
    - 将 `services` 作为 Python 包使用。通常为空或导出包级 API。

- `core_executor.py` (核心执行器)
    - 提供 `CodeExecutor` 类：负责工作区管理、写文件、读文件、执行脚本与系统命令，并返回统一的结果结构。
    - 关键点：
        - 构造函数 `__init__(workspace: Optional[str] = None)`：设置工作区（默认为 `executor_workspace`），并确保目录存在（使用 `parents=True`）。
        - `load_config(config_path: str) -> Dict`：从 JSON 文件加载配置。
        - `execute_from_config(config_path: str) -> List[Dict]`：加载配置并调用 `execute_actions`。
        - `execute_actions(config_data: Dict) -> List[Dict]`：遍历并执行 `actions` 列表，支持 `stop_on_error` 设置。
        - 内部动作函数：
            - `_write_code(action: Dict) -> Dict`：将 `action['code']` 写入文件，返回包含 `success, filepath, stdout, stderr, returncode` 的字典。
            - `_execute_code(action: Dict) -> Dict`：执行文件（支持多语言执行器配置），返回 `success, returncode, stdout, stderr, filepath, action`。
            - `_execute_command(action: Dict) -> Dict`：执行系统命令（在 Windows 上会自动使用 GBK 编码读取输出），返回统一字段。
            - `_read_code(action: Dict) -> Dict`：读取文件内容。
        - 返回字段规范化：每个返回结果会尽量包含 `action_name`, `action_type`, `success`, `stdout`, `stderr`, `returncode` 等字段，便于上层消费。
        - 执行器 `executors` 字典默认包含 `python`、`javascript`、`shell`、`powershell`、`batch`。注意：`python` 执行器使用 `sys.executable`，避免错误的解释器被调用。
        - 子进程调用使用 `subprocess.run(..., text=True, encoding=platform_encoding, errors='replace')`，在 Windows 上采用 `gbk` 编码以避免解码异常。

    - 返回示例（单个动作）:

```json
{
    "action_name": "执行测试脚本",
    "action_type": "execute_code",
    "success": true,
    "returncode": 0,
    "stdout": "Hello from Sandbox!\n",
    "stderr": "",
    "filepath": ".../executor_workspace/test_script.py"
}
```

- `run.py` (运行入口)
    - 功能：加载 `decision` 配置文件，初始化 `CodeExecutor`，通过 `execute_actions` 执行动作序列，打印摘要并保存执行报告。
    - 关键函数：
        - `load_decision_config(decision_dir: str) -> dict`：查找 `decision_dir` 下的第一个 JSON 配置文件；若不存在，则创建 `default_task.json`（包含示例动作：`write_code`、`execute_code`、`command`）。
        - `print_results_summary(results: list)`：打印控制台摘要，读取 `action_name`/`action_type`/`error`/`stderr` 字段显示进度。
        - `save_execution_report(executor: CodeExecutor, config: dict, results: list) -> str`：在 `executor.workspace/reports` 下保存 JSON 报告，报告字段包含 `execution_info`、`summary` 和 `detailed_results`。
    - 日志：使用 Python `logging` 配置，日志文件 `sandbox_execution.log` 写入到 `backend/services/`。
    - 运行返回值：若所有动作成功则返回 `0`，否则返回 `1`；遇到 `KeyboardInterrupt` 返回 `130`。

- `test_sandbox.py`
    - 若存在，包含单元/集成测试或示例用例，用于验证 `CodeExecutor` 与 `run.py` 的行为。可以作为开发时的快速自测脚本。

- `decision/` 目录
    - 存放工作流/决策层 JSON 文件。文件结构样例（最小示例）:

```json
{
    "name": "默认测试任务",
    "description": "自动化测试任务",
    "settings": {"timeout": 30, "stop_on_error": false},
    "actions": [
        {"type": "write_code", "name": "创建测试脚本", "filename": "test_script", "language": "python", "code": "print('Hello')"},
        {"type": "execute_code", "name": "执行测试脚本", "filepath": "test_script.py", "language": "python"},
        {"type": "command", "name": "系统信息", "command": "echo %DATE% %TIME%"}
    ]
}
```

## 集成与注意事项

- 如果其他执行器或服务要调用 `services`：推荐以 `CodeExecutor.execute_from_config()` 或 `CodeExecutor.execute_actions()` 为主入口，而不要直接调用 `_write_code/_execute_code` 等私有方法，以保证行为与返回结构一致。
- `executors` 配置项可以在 `core_executor.py` 中扩展或由外部传入（例如注入自定义解释器路径）。
- 当前实现并未提供强隔离（仅通过子进程与超时做基本限制），生产环境请使用容器/沙箱（例如 Docker、gVisor）或限制资源（Linux cgroups）以降低安全风险。

## 示例：在代码中调用 services

```python
from backend.services.core_executor import CodeExecutor

exec = CodeExecutor()
config = exec.load_config('decision/default_task.json')
results = exec.execute_actions(config)
for r in results:
        print(r['action_name'], r['success'])
```

## 变更记录（重要改动）

- 使用 `sys.executable` 作为 Python 执行器，避免虚拟环境或系统 Python 调用错误。
- 统一返回字段，便于上层服务解析和生成报告。
- 子进程读取使用平台编码并 `errors='replace'`，解决 Windows 环境下的 UnicodeDecodeError 问题。

---

如需我把此 README 内容整理为更精简的文档页面或将其提交为 Git commit（含说明与签名），我可以继续处理。

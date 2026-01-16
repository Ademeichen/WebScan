"""
代码执行工作流工具包
核心功能：读取JSON决策文件，执行代码读写、代码执行、Windows终端命令运行（全适配LangChain v0.1+ StructuredTool）

对外暴露的核心工具：
1. code_tool：LangChain结构化核心工具实例，支持4类操作（read_code/write_code/execute_code/run_terminal（cmd/powershell））(对应id：1、2、3、4、5)
2. LangChainWorkflowExecutor：流程执行器类，读取JSON文件按顺序执行所有步骤（execute_workflow为其核心方法）

使用示例：
    # 1. 导入工具
    from 包名 import code_tool, LangChainWorkflowExecutor

    # 2. 使用结构化工具执行单个操作
    result = code_tool.invoke({
        "step_type": "write_code",
        "params": {"file_path": "test.py", "code_content": "print('Hello')"}
    })

    # 3. 执行JSON配置的完整工作流
    executor = LangChainWorkflowExecutor()
    executor.execute_workflow("workflow_config.json")
"""

# 导出核心工具（适配LangChain StructuredTool版本）
from code_executor import code_tool, LangChainWorkflowExecutor

# 定义默认的测试JSON文件名（与你原版本保持一致）
DEFAULT_TEST_JSON = "workflow_config.json"

# 兼容你原版本的init_test_workflow函数（路径逻辑完全不变）
def init_test_workflow():
    """
    便捷函数：初始化测试工作流（自动生成测试JSON文件到当前目录）
    无需手动创建JSON文件，直接调用该函数即可生成测试配置
    """
    import os
    import json
    
    # 强制在当前目录创建测试JSON
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_json_path = os.path.join(current_dir, DEFAULT_TEST_JSON)
    
    if os.path.exists(test_json_path):
        print(f"⚠️  测试JSON文件已存在：{test_json_path}，跳过创建")
        return test_json_path
    
    # 测试工作流配置（与你原版本完全一致，仅适配LangChain参数规范）
    test_config = {
        "execution_flow": [
            {
                "step_id": 1,
                "step_type": "write_code",
                "params": {
                    "file_path": "test_script.py",
                    "code_content": "print('Hello from test script!')\nx = 10\ny = 20\nprint(f'Sum: {x+y}')"
                }
            },
            {
                "step_id": 2,
                "step_type": "read_code",
                "params": {"file_path": "test_script.py"}
            },
            {
                "step_id": 3,
                "step_type": "execute_code",
                "params": {"file_path": "test_script.py", "python_executable": "python"}
            },
            {
                "step_id": 4,
                "step_type": "run_terminal",
                "params": {"command": "dir", "terminal_type": "cmd"}
            },
            {
                "step_id": 5,
                "step_type": "run_terminal",
                "params": {"command": "Get-ChildItem", "terminal_type": "powershell"}
            }
        ]
    }
    
    # 写入JSON文件
    with open(test_json_path, "w", encoding="utf-8") as f:
        json.dump(test_config, f, ensure_ascii=False, indent=4)
    
    print(f"✅ 测试JSON文件已创建在当前目录：{test_json_path}")
    return test_json_path

# 兼容你原版本的main测试逻辑（适配LangChain执行器）
if __name__ == "__main__":
    print("===== 代码执行工作流包（LangChain StructuredTool版） =====")
    print("使用方式：")
    print(" 导入核心组件：from . import code_tool, LangChainWorkflowExecutor")

    # 运行测试（适配LangChain执行器）
    json_path = init_test_workflow()
    executor = LangChainWorkflowExecutor()
    executor.execute_workflow(json_path)
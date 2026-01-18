"""
代码执行工作流工具包
核心功能：读取JSON决策文件，执行代码读写、代码执行、Windows终端命令运行

对外暴露的核心工具：
1. CodeExecutionTool：核心工具类，支持4类操作（read_code/write_code/execute_code/run_terminal（cmd/powershell）)
    **以下创建文件函数提供json文件参数示例**
2. execute_workflow：流程执行函数，读取JSON文件按顺序执行所有步骤

使用示例：
    # 1. 导入工具
    from 包名 import CodeExecutionTool, execute_workflow

    # 2. 使用工具类执行单个操作
    tool = CodeExecutionTool()
    tool.run(step_type="write_code", params={"file_path": "test.py", "code_content": "print('Hello')"})

    # 3. 执行JSON配置的完整工作流
    execute_workflow("workflow_config.json")
"""

# 示例：
# 导出核心类和函数
from code_executor import CodeExecutionTool, execute_workflow

# 定义默认的测试JSON文件名
DEFAULT_TEST_JSON = "workflow_config.json"

# 创建json文件示例：
def init_test_workflow():
    """
    便捷函数：初始化测试工作流（自动生成测试JSON文件到当前目录）
    无需手动创建JSON文件，直接调用该函数即可生成测试配置
    """
    import os
    import json
    
    # 在当前目录创建测试JSON
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_json_path = os.path.join(current_dir, DEFAULT_TEST_JSON)
    
    if os.path.exists(test_json_path):
        print(f"⚠️  测试JSON文件已存在：{test_json_path}，跳过创建")
        return test_json_path
    
    # 测试工作流配置（与业务逻辑一致）
    test_config = {
        "execution_flow": [
            {
                "step_type": "write_code",
                "params": {
                    "file_path": "test_script.py",
                    "code_content": "print('Hello from test script!')\nx = 10\ny = 20\nprint(f'Sum: {x+y}')"
                }
            },
            {
                "step_type": "read_code",
                "params": {"file_path": "test_script.py"}
            },
            {
                "step_type": "execute_code",
                "params": {"file_path": "test_script.py", "python_executable": "python"}
            },
            {
                "step_type": "run_terminal",
                "params": {"command": "dir", "terminal_type": "cmd"}
            },
            {
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

    
if __name__ == "__main__":
    print("===== 代码执行工作流包 =====")
    print("使用方式：")
    print(" 导入核心组件：from . import CodeExecutionTool, execute_workflow")

    # 运行测试
    json_path = init_test_workflow() ##提供完整json文件路径即可

    execute_workflow(json_path)

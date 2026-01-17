"""
代码执行工作流工具包
核心功能：读取JSON决策文件，执行代码读写、代码执行、Windows终端命令运行（全适配LangChain v0.1+ StructuredTool，日志输出到文件）

对外暴露的核心工具：
1. code_tool：LangChain结构化核心工具实例，支持4类操作（read_code/write_code/execute_code/run_terminal（cmd/powershell））
    **以下创建json文件函数提供json文件结构参数示例**
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

import logging
import os

# 导出核心工具
from code_executor import code_tool, LangChainWorkflowExecutor

# 定义默认的测试JSON文件名
DEFAULT_TEST_JSON = "workflow_config.json"

# 创建json文件示例
def init_test_workflow():
    """
    便捷函数：初始化测试工作流（自动生成测试JSON文件到当前目录）
    无需手动创建JSON文件，直接调用该函数即可生成测试配置
    """
    import json
    
    # 初始化日志器
    logger = logging.getLogger(__name__)
    
    # 创建测试JSON
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_json_path = os.path.join(current_dir, DEFAULT_TEST_JSON)
    
    if os.path.exists(test_json_path):
        logger.warning(f"⚠️  测试JSON文件已存在：{test_json_path}，跳过创建")
        return test_json_path
    
    # josn文件示例
    test_config = {
        "execution_flow": [
                {
                    "step_type": "write_code",
                    "params": {
                        "file_path": "test_script.py",
                        "code_content": "print('Hello World!')\nx=100\ny=200\nprint(f'Sum: {x+y}')"
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
                    "params": {"command": "dir test_script.py", "terminal_type": "cmd"}
                },
                {
                    "step_type": "run_terminal",
                    "params": {"command": "Get-ChildItem test_script.py", "terminal_type": "powershell"}
                }
            ]
    }
    
    # 写入JSON文件
    with open(test_json_path, "w", encoding="utf-8") as f:
        json.dump(test_config, f, ensure_ascii=False, indent=4)
    
    logger.info(f"✅ 测试JSON文件已创建在当前目录：{test_json_path}")
    return test_json_path



# 使用示例

if __name__ == "__main__":

    from code_executor import setup_logger
    logger = setup_logger()
    
    logger.info("===== 代码执行工作流包 =====")
    logger.info("使用方式：")
    logger.info(" 导入核心组件：from . import code_tool, LangChainWorkflowExecutor")

    json_path = init_test_workflow()
    executor = LangChainWorkflowExecutor()
    executor.execute_workflow(json_path)
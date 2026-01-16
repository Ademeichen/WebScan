import os
import json
import subprocess
from typing import Dict, Any

# ====================== 核心功能工具类 ======================
class CodeExecutionTool:
    name = "code_execution_tool"
    description = "用于执行读取代码、写入代码、执行代码、运行Windows终端命令的工具"

    def run(self, step_type: str, params: Dict[str, Any]) -> Any:
        """统一入口方法：直接接收step_type和params，分发到对应功能"""
        step_handlers = {
            "read_code": self._read_code,
            "write_code": self._write_code,
            "execute_code": self._execute_code,
            "run_terminal": self._run_terminal
        }
        if step_type not in step_handlers:
            raise ValueError(f"不支持的步骤类型: {step_type}，仅支持{list(step_handlers.keys())}")
        return step_handlers[step_type](params)

    def _read_code(self, params: Dict[str, str]) -> str:
        """读取指定路径的代码文件内容"""
        file_name = params.get("file_path")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        if not file_path:
            raise ValueError("读取代码缺少必要参数：file_path")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在：{file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"✅ 成功读取文件 {file_path}，内容：\n{content}\n")
        return content

    def _write_code(self, params: Dict[str, str]) -> str:
        """将代码内容写入指定文件（强制在当前目录创建）"""
        # 提取文件名，忽略传入的路径，仅保留文件名，确保在当前目录创建
        file_name = os.path.basename(params.get("file_path"))
        code_content = params.get("code_content")
        
        if not file_name or code_content is None:
            raise ValueError("写入代码缺少必要参数：file_path（至少包含文件名）或 code_content")
        
        # 显式拼接当前目录路径，确保文件在本目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        # 无需创建目录（当前目录已存在）
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_content)
        print(f"✅ 代码已写入当前目录文件：{file_path}\n")
        return f"成功写入代码到当前目录：{file_path}"

    def _execute_code(self, params: Dict[str, str]) -> str:
        """执行Python代码文件（强制读取当前目录的文件）"""
        file_name = os.path.basename(params.get("file_path"))
        python_exec = params.get("python_executable", "python")
        
        if not file_name:
            raise ValueError("执行代码缺少必要参数：file_path（至少包含文件名）")
        
        # 显式拼接当前目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"当前目录中文件不存在：{file_path}")
        
        try:
            result = subprocess.run(
                [python_exec, file_path],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            if result.returncode == 0:
                output = f"✅ 代码执行成功，输出：\n{result.stdout}\n"
            else:
                output = f"❌ 代码执行失败，错误：\n{result.stderr}\n"
            print(output)
            return output
        except Exception as e:
            raise RuntimeError(f"执行代码异常：{str(e)}")

    def _run_terminal(self, params: Dict[str, str]) -> str:
        """运行Windows终端命令（默认在当前目录执行）"""
        command = params.get("command")
        terminal_type = params.get("terminal_type", "cmd")
        
        # 强制指定终端命令在当前目录执行
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        if not command:
            raise ValueError("运行终端命令缺少必要参数：command")
        
        try:
            # 构建终端执行命令
            if terminal_type.lower() == "cmd":
                cmd = ["cmd.exe", "/c", command]
            elif terminal_type.lower() == "powershell":
                cmd = ["powershell.exe", "-Command", command]
            else:
                raise ValueError(f"不支持的终端类型：{terminal_type}（仅支持cmd/powershell）")
            
            # 执行命令（强制在当前目录运行，解决中文乱码）
            result = subprocess.run(
                cmd,
                cwd=current_dir,  # 显式指定当前目录为工作目录
                capture_output=True,
                text=True,
                encoding="gbk"
            )
            
            if result.returncode == 0:
                output = f"✅ {terminal_type.upper()}命令执行成功，输出：\n{result.stdout}\n"
            else:
                output = f"❌ {terminal_type.upper()}命令执行失败，错误：\n{result.stderr}\n"
            print(output)
            return output
        except Exception as e:
            raise RuntimeError(f"运行终端命令异常：{str(e)}")

# ====================== 流程执行引擎 ======================
def execute_workflow(json_file_path: str) -> None:
    """读取JSON决策文件，按顺序执行所有步骤"""
    # 确保JSON文件路径为当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, os.path.basename(json_file_path))
    
    # 1. 校验并读取JSON文件
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"JSON决策文件不存在：{json_file_path}")
    
    with open(json_file_path, "r", encoding="utf-8") as f:
        workflow_data = json.load(f)
    
    # 2. 解析执行流程
    execution_flow = workflow_data.get("execution_flow", [])
    if not execution_flow:
        raise ValueError("JSON文件中未定义执行流程（execution_flow）")
    
    # 3. 初始化工具并执行步骤
    tool = CodeExecutionTool()
    print("========== 开始执行工作流 ==========\n")
    for step in execution_flow:
        step_id = step.get("step_id")
        step_type = step.get("step_type")
        params = step.get("params", {})
        
        print(f"📌 执行步骤 {step_id} - 类型：{step_type}")
        try:
            tool.run(step_type=step_type, params=params)
        except Exception as e:
            print(f"❌ 步骤 {step_id} 执行失败：{str(e)}\n")
            continue  # 单个步骤失败不中断整体流程
    
    print("========== 工作流执行完成 ==========")






# ====================== 测试入口（强制在当前目录创建JSON文件） ======================


if __name__ == "__main__":
    # 强制指定JSON文件在当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    TEST_JSON_FILE_NAME = "workflow_config.json"
    TEST_JSON_PATH = os.path.join(current_dir, TEST_JSON_FILE_NAME)
    
    # 自动生成测试JSON文件（若不存在，强制在当前目录）
    if not os.path.exists(TEST_JSON_PATH):
        test_config = {
            "execution_flow": [
                {
                    "step_id": 1,
                    "step_type": "write_code",
                    "params": {
                        # 仅指定文件名，确保在当前目录创建test_script.py
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
                    "params": {"command": "dir", "terminal_type": "cmd"}  # 移除cwd，强制用当前目录
                },
                {
                    "step_id": 5,
                    "step_type": "run_terminal",
                    "params": {"command": "Get-ChildItem", "terminal_type": "powershell"}  # 移除cwd
                }
            ]
        }
        with open(TEST_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(test_config, f, ensure_ascii=False, indent=4)
        print(f"📝 测试JSON文件已生成在当前目录：{TEST_JSON_PATH}\n")
    
    # 执行工作流
    try:
        execute_workflow(TEST_JSON_PATH)
    except Exception as e:
        print(f"❌ 工作流执行异常：{str(e)}")
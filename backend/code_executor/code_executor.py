import os
import json
import subprocess
import logging
from typing import Dict, Any

# ====================== 日志配置 ======================
def setup_logger():
    """配置日志系统：同时输出到控制台和日志文件"""
    # 日志文件路径（当前目录下的code_execution.log）
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code_execution.log")
    
    # 日志格式：时间 - 日志级别 - 模块 - 消息
    log_format = "%(asctime)s - %(levelname)s - %(module)s - %(message)s"
    
    # 配置根日志器
    logging.basicConfig(
        level=logging.INFO,  # 日志级别：INFO及以上
        format=log_format,
        handlers=[
            # 输出到文件（追加模式，编码UTF-8避免中文乱码）
            logging.FileHandler(log_file, mode='a', encoding='utf-8'),
            # 输出到控制台
            logging.StreamHandler()
        ]
    )

# 初始化日志
setup_logger()
logger = logging.getLogger(__name__)

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
            error_msg = f"不支持的步骤类型: {step_type}，仅支持{list(step_handlers.keys())}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        return step_handlers[step_type](params)

    def _read_code(self, params: Dict[str, str]) -> str:
        """读取指定路径的代码文件内容"""
        file_name = params.get("file_path")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        if not file_path:
            error_msg = "读取代码缺少必要参数：file_path"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not os.path.exists(file_path):
            error_msg = f"文件不存在：{file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        success_msg = f"✅ 成功读取文件 {file_path}，内容：\n{content}\n"
        logger.info(success_msg)
        return content

    def _write_code(self, params: Dict[str, str]) -> str:
        """将代码内容写入指定文件（强制在当前目录创建）"""
        # 提取文件名，忽略传入的路径，仅保留文件名，确保在当前目录创建
        file_name = os.path.basename(params.get("file_path"))
        code_content = params.get("code_content")
        
        if not file_name or code_content is None:
            error_msg = "写入代码缺少必要参数：file_path（至少包含文件名）或 code_content"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 显式拼接当前目录路径，确保文件在本目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        # 无需创建目录（当前目录已存在）
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_content)
        
        success_msg = f"✅ 代码已写入当前目录文件：{file_path}\n"
        logger.info(success_msg)
        return f"成功写入代码到当前目录：{file_path}"

    def _execute_code(self, params: Dict[str, str]) -> str:
        """执行Python代码文件（强制读取当前目录的文件）"""
        file_name = os.path.basename(params.get("file_path"))
        python_exec = params.get("python_executable", "python")
        
        if not file_name:
            error_msg = "执行代码缺少必要参数：file_path（至少包含文件名）"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 显式拼接当前目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        if not os.path.exists(file_path):
            error_msg = f"当前目录中文件不存在：{file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            result = subprocess.run(
                [python_exec, file_path],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            if result.returncode == 0:
                output = f"✅ 代码执行成功，输出：\n{result.stdout}\n"
                logger.info(output)
            else:
                output = f"❌ 代码执行失败，错误：\n{result.stderr}\n"
                logger.error(output)
            return output
        except Exception as e:
            error_msg = f"执行代码异常：{str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _run_terminal(self, params: Dict[str, str]) -> str:
        """运行Windows终端命令（默认在当前目录执行）"""
        command = params.get("command")
        terminal_type = params.get("terminal_type", "cmd")
        
        # 指定终端命令在当前目录执行
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        if not command:
            error_msg = "运行终端命令缺少必要参数：command"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # 构建终端执行命令
            if terminal_type.lower() == "cmd":
                cmd = ["cmd.exe", "/c", command]
            elif terminal_type.lower() == "powershell":
                cmd = ["powershell.exe", "-Command", command]
            else:
                error_msg = f"不支持的终端类型：{terminal_type}（仅支持cmd/powershell）"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 执行命令（在当前目录运行，解决中文乱码）
            result = subprocess.run(
                cmd,
                cwd=current_dir,  # 显式指定当前目录为工作目录
                capture_output=True,
                text=True,
                encoding="gbk"
            )
            
            if result.returncode == 0:
                output = f"✅ {terminal_type.upper()}命令执行成功，输出：\n{result.stdout}\n"
                logger.info(output)
            else:
                output = f"❌ {terminal_type.upper()}命令执行失败，错误：\n{result.stderr}\n"
                logger.error(output)
            return output
        except Exception as e:
            error_msg = f"运行终端命令异常：{str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

# ====================== 流程执行引擎 ======================
def execute_workflow(json_file_path: str) -> None:
    """读取JSON决策文件，按顺序执行所有步骤"""
    # 确保JSON文件路径为当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, os.path.basename(json_file_path))
    
    # 1. 校验并读取JSON文件
    if not os.path.exists(json_file_path):
        error_msg = f"JSON决策文件不存在：{json_file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    with open(json_file_path, "r", encoding="utf-8") as f:
        workflow_data = json.load(f)
    
    # 2. 解析执行流程
    execution_flow = workflow_data.get("execution_flow", [])
    if not execution_flow:
        error_msg = "JSON文件中未定义执行流程（execution_flow）"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 3. 初始化工具并执行步骤
    tool = CodeExecutionTool()
    logger.info("========== 开始执行工作流 ==========")
    
    for step in execution_flow:
        step_type = step.get("step_type")
        params = step.get("params", {})
        
        step_start_msg = f"📌 执行步骤类型：{step_type}"
        logger.info(step_start_msg)
        
        try:
            tool.run(step_type=step_type, params=params)
        except Exception as e:
            step_error_msg = f"❌ 步骤类型：{step_type} 执行失败：{str(e)}"
            logger.error(step_error_msg)
            continue  # 单个步骤失败不中断整体流程
    
    logger.info("========== 工作流执行完成 ==========")

# ====================== 测试入口======================
if __name__ == "__main__":
    # 指定JSON文件在当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    TEST_JSON_FILE_NAME = "workflow_config.json"
    TEST_JSON_PATH = os.path.join(current_dir, TEST_JSON_FILE_NAME)
    
    # 自动生成测试JSON文件（若不存在，在当前目录）
    if not os.path.exists(TEST_JSON_PATH):
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
        with open(TEST_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(test_config, f, ensure_ascii=False, indent=4)
        
        generate_msg = f"📝 测试JSON文件已生成在当前目录：{TEST_JSON_PATH}"
        logger.info(generate_msg)
    
    # 执行工作流
    try:
        execute_workflow(TEST_JSON_PATH)
    except Exception as e:
        error_msg = f"❌ 工作流执行异常：{str(e)}"
        logger.error(error_msg)
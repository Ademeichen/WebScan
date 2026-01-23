"""
代码执行器 - LangChain 集成版本

提供代码读取、写入、执行和终端命令运行功能。
使用 LangChain StructuredTool 与 AI Agent 集成。
支持工作流配置文件执行。
"""
import os
import sys
import json
import subprocess
import logging
from typing import Dict, Any, List
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


# ====================== 日志配置 ======================

def setup_logger():
    """
    配置日志系统
    
    同时输出到控制台和日志文件，使用 UTF-8 编码避免中文乱码。
    """
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", settings.CODE_EXECUTOR_LOG_FILE)
    log_file = os.path.abspath(log_file)
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    log_format = "%(asctime)s - %(levelname)s - %(module)s - %(message)s"
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


setup_logger()
logger = logging.getLogger(__name__)

# TODO: 集成该功能到 LangChain 工作流中，作为工具调用节点

# ====================== 结构化参数模型 ======================

class CodeToolInput(BaseModel):
    """代码工具输入参数模型"""
    step_type: str = Field(
        description="操作类型，仅支持：read_code、write_code、execute_code、run_terminal",
        enum=["read_code", "write_code", "execute_code", "run_terminal"]
    )
    params: Dict[str, Any] = Field(
        description="操作参数：\n"
        "- read_code: {file_path: 文件名}\n"
        "- write_code: {file_path: 文件名, code_content: 代码内容}\n"
        "- execute_code: {file_path: 文件名, python_executable: Python解释器路径（可选）}\n"
        "- run_terminal: {command: 终端命令, terminal_type: cmd/powershell（可选）}"
    )


# ====================== 业务逻辑函数 ======================

def read_code(params: Dict[str, str]) -> str:
    """
    读取当前目录的代码文件
    
    Args:
        params: 包含 file_path 的字典
        
    Returns:
        str: 读取结果或错误信息
    """
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(params.get("file_path", "")))
    if not os.path.exists(file_path):
        error_msg = f"❌ 文件不存在：{file_path}"
        logger.error(error_msg)
        return error_msg
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    success_msg = f"✅ 成功读取文件 {file_path}\n内容：\n{content}"
    logger.info(success_msg)
    return success_msg


def write_code(params: Dict[str, str]) -> str:
    """
    写入代码到当前目录文件
    
    Args:
        params: 包含 file_path 和 code_content 的字典
        
    Returns:
        str: 写入结果或错误信息
    """
    file_name = os.path.basename(params.get("file_path", ""))
    code_content = params.get("code_content")
    if not file_name or code_content is None:
        error_msg = "❌ 缺少必要参数：file_path（文件名）或 code_content（代码内容）"
        logger.error(error_msg)
        return error_msg
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code_content)
    success_msg = f"✅ 代码已写入当前目录文件：{file_path}"
    logger.info(success_msg)
    return success_msg


def execute_code(params: Dict[str, str]) -> str:
    """
    执行当前目录的Python代码文件
    
    Args:
        params: 包含 file_path 和可选 python_executable 的字典
        
    Returns:
        str: 执行结果或错误信息
    """
    file_name = os.path.basename(params.get("file_path", ""))
    python_exec = params.get("python_executable", "python")
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    if not os.path.exists(file_path):
        error_msg = f"❌ 文件不存在：{file_path}"
        logger.error(error_msg)
        return error_msg
    try:
        result = subprocess.run(
            [python_exec, file_path],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if result.returncode == 0:
            success_msg = f"✅ 代码执行成功\n输出：\n{result.stdout}"
            logger.info(success_msg)
            return success_msg
        else:
            error_msg = f"❌ 代码执行失败\n错误：\n{result.stderr}"
            logger.error(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"❌ 执行异常：{str(e)}"
        logger.error(error_msg)
        return error_msg


def run_terminal(params: Dict[str, str]) -> str:
    """
    运行Windows终端命令（当前目录）
    
    Args:
        params: 包含 command 和可选 terminal_type 的字典
        
    Returns:
        str: 执行结果或错误信息
    """
    command = params.get("command")
    terminal_type = params.get("terminal_type", "cmd")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    if not command:
        error_msg = "❌ 缺少必要参数：command（终端命令）"
        logger.error(error_msg)
        return error_msg
    try:
        cmd = ["cmd.exe", "/c", command] if terminal_type.lower() == "cmd" else ["powershell.exe", "-Command", command]
        result = subprocess.run(
            cmd,
            cwd=current_dir,
            capture_output=True,
            text=True,
            encoding="gbk"
        )
        if result.returncode == 0:
            success_msg = f"✅ {terminal_type.upper()}命令执行成功\n输出：\n{result.stdout}"
            logger.info(success_msg)
            return success_msg
        else:
            error_msg = f"❌ {terminal_type.upper()}命令执行失败\n错误：\n{result.stderr}"
            logger.error(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"❌ 终端命令执行异常：{str(e)}"
        logger.error(error_msg)
        return error_msg


# ====================== 多参数工具核心函数 ======================

def code_execution_tool(step_type: str, params: Dict[str, Any]) -> str:
    """
    StructuredTool 专用的多参数核心函数
    
    Args:
        step_type: 操作类型
        params: 操作参数字典
        
    Returns:
        str: 执行结果
    """
    handlers = {
        "read_code": read_code,
        "write_code": write_code,
        "execute_code": execute_code,
        "run_terminal": run_terminal
    }
    if step_type not in handlers:
        error_msg = f"❌ 不支持的操作类型：{step_type}，仅支持{list(handlers.keys())}"
        logger.error(error_msg)
        return error_msg
    return handlers[step_type](params)


# ====================== 创建 LangChain 结构化工具 ======================

code_tool = StructuredTool.from_function(
    func=code_execution_tool,
    name="code_execution_tool",
    description="用于在Windows当前目录执行代码读取、写入、执行和终端命令运行的工具",
    args_schema=CodeToolInput,
    return_direct=True
)


# ====================== 工作流执行器 ======================

class LangChainWorkflowExecutor:
    """LangChain 工作流执行器"""
    
    def __init__(self):
        self.tool = code_tool
        self.logger = logger

    def load_workflow_from_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """
        加载并校验 JSON 工作流
        
        Args:
            json_file_path: JSON 文件路径
            
        Returns:
            List[Dict]: 执行流程列表
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: JSON 格式错误
        """
        json_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(json_file_path))
        if not os.path.exists(json_file_path):
            error_msg = f"❌ JSON文件不存在：{json_file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "execution_flow" not in data:
            error_msg = "❌ JSON缺少execution_flow字段"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        self.logger.info(f"✅ 成功加载JSON工作流文件：{json_file_path}")
        return data["execution_flow"]

    def execute_workflow(self, json_file_path: str) -> List[str]:
        """
        执行工作流（输出日志到文件+控制台）
        
        Args:
            json_file_path: JSON 工作流文件路径
            
        Returns:
            List[str]: 执行结果列表
        """
        self.logger.info("========== 开始执行工作流 ==========")
        workflow = self.load_workflow_from_json(json_file_path)
        results = []
        
        for idx, step in enumerate(workflow, 1):
            step_type = step.get("step_type")
            params = step.get("params", {})
            step_msg = f"📌 执行步骤 {idx} - 类型：{step_type}"
            self.logger.info(step_msg)
            
            try:
                result = self.tool.invoke({
                    "step_type": step_type,
                    "params": params
                })
                results.append(result)
            except Exception as e:
                error_msg = f"❌ 步骤执行失败：{str(e)}"
                self.logger.error(error_msg)
                results.append(error_msg)
        
        self.logger.info("========== 工作流执行完成 ==========")
        return results


def execute_workflow(json_file_path: str) -> List[str]:
    """
    便捷函数：执行工作流
    
    Args:
        json_file_path: JSON 工作流文件路径
        
    Returns:
        List[str]: 执行结果列表
    """
    executor = LangChainWorkflowExecutor()
    return executor.execute_workflow(json_file_path)


# ====================== 测试入口 ======================

if __name__ == "__main__":
    TEST_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflow_config.json")

    if not os.path.exists(TEST_JSON_PATH):
        test_workflow = {
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
                    "params": {"command": "dir", "terminal_type": "cmd"}
                },
                {
                    "step_type": "run_terminal",
                    "params": {"command": "Get-ChildItem", "terminal_type": "powershell"}
                }
            ]
        }
        with open(TEST_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(test_workflow, f, ensure_ascii=False, indent=4)
        logger.info(f"📝 测试JSON已生成：{TEST_JSON_PATH}")

    try:
        executor = LangChainWorkflowExecutor()
        executor.execute_workflow(TEST_JSON_PATH)
    except Exception as e:
        logger.error(f"❌ 工作流执行异常：{str(e)}")


# ====================== 集成示例 ======================

"""
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

llm = ChatOpenAI(
    model=settings.MODEL_ID,
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    temperature=0
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是代码执行助手，所有文件都在当前目录创建/执行，严格调用结构化工具完成任务。"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, [code_tool], prompt)
agent_executor = AgentExecutor(agent=agent, tools=[code_tool], verbose=True)

result = agent_executor.invoke({
    "input": "创建calc.py，内容为计算10*20并打印，执行后用PowerShell查看文件信息"
})
print("大模型执行结果：", result["output"])
"""

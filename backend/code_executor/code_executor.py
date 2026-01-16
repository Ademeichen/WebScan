import os
import json
import subprocess
from typing import Dict, Any, List
# 导入StructuredTool（处理多参数）
from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field

# ====================== 1. 定义结构化参数模型（多参数专用） ======================
class CodeToolInput(BaseModel):
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

# ====================== 2. 核心业务逻辑（纯函数，无框架耦合） ======================
def read_code(params: Dict[str, str]) -> str:
    """读取当前目录的代码文件"""
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(params.get("file_path", "")))
    if not os.path.exists(file_path):
        return f"文件不存在：{file_path}"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return f"✅ 成功读取文件 {file_path}\n内容：\n{content}"

def write_code(params: Dict[str, str]) -> str:
    """写入代码到当前目录文件"""
    file_name = os.path.basename(params.get("file_path", ""))
    code_content = params.get("code_content")
    if not file_name or code_content is None:
        return "缺少必要参数：file_path（文件名）或 code_content（代码内容）"
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code_content)
    return f"✅ 代码已写入当前目录文件：{file_path}"

def execute_code(params: Dict[str, str]) -> str:
    """执行当前目录的Python代码文件"""
    file_name = os.path.basename(params.get("file_path", ""))
    python_exec = params.get("python_executable", "python")
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    if not os.path.exists(file_path):
        return f"文件不存在：{file_path}"
    try:
        result = subprocess.run(
            [python_exec, file_path],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if result.returncode == 0:
            return f"✅ 代码执行成功\n输出：\n{result.stdout}"
        else:
            return f"❌ 代码执行失败\n错误：\n{result.stderr}"
    except Exception as e:
        return f"❌ 执行异常：{str(e)}"

def run_terminal(params: Dict[str, str]) -> str:
    """运行Windows终端命令（当前目录）"""
    command = params.get("command")
    terminal_type = params.get("terminal_type", "cmd")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if not command:
        return "缺少必要参数：command（终端命令）"
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
            return f"✅ {terminal_type.upper()}命令执行成功\n输出：\n{result.stdout}"
        else:
            return f"❌ {terminal_type.upper()}命令执行失败\n错误：\n{result.stderr}"
    except Exception as e:
        return f"❌ 终端命令执行异常：{str(e)}"

# ====================== 3. 多参数工具核心函数（适配StructuredTool） ======================
def code_execution_tool(step_type: str, params: Dict[str, Any]) -> str:
    """StructuredTool专用的多参数核心函数"""
    handlers = {
        "read_code": read_code,
        "write_code": write_code,
        "execute_code": execute_code,
        "run_terminal": run_terminal
    }
    if step_type not in handlers:
        return f"不支持的操作类型：{step_type}，仅支持{list(handlers.keys())}"
    return handlers[step_type](params)

# ====================== 4. 创建LangChain结构化工具 ======================
# 改用StructuredTool（多参数专用）
code_tool = StructuredTool.from_function(
    func=code_execution_tool,
    name="code_execution_tool",
    description="用于在Windows当前目录执行代码读取、写入、执行和终端命令运行的工具",
    args_schema=CodeToolInput,  # 自动校验多参数
    return_direct=True
)

# ====================== 5. 工作流执行器（适配StructuredTool调用） ======================
class LangChainWorkflowExecutor:
    def __init__(self):
        self.tool = code_tool  # 初始化结构化工具

    def load_workflow_from_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """加载并校验JSON工作流"""
        json_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(json_file_path))
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"JSON文件不存在：{json_file_path}")
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "execution_flow" not in data:
            raise ValueError("JSON缺少execution_flow字段")
        return data["execution_flow"]

    def execute_workflow(self, json_file_path: str) -> List[str]:
        """执行工作流（StructuredTool正确调用方式）"""
        workflow = self.load_workflow_from_json(json_file_path)
        results = []
        print("========== 开始执行LangChain工作流 ==========\n")
        
        for idx, step in enumerate(workflow, 1):
            step_type = step.get("step_type")
            params = step.get("params", {})
            print(f"📌 执行步骤 {idx} - 类型：{step_type}")
            
            # StructuredTool的正确调用方式：传入结构化字典（单参数封装多字段）
            try:
                # invoke是新版LangChain推荐的调用方式（结构化输入）
                result = self.tool.invoke({
                    "step_type": step_type,
                    "params": params
                })
            except Exception as e:
                result = f"❌ 步骤执行失败：{str(e)}"
            
            results.append(result)
            print(f"{result}\n")
        
        print("========== LangChain工作流执行完成 ==========")
        return results

# ====================== 6. 测试入口 ======================
if __name__ == "__main__":
    # 测试JSON路径（当前目录）
    TEST_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflow_config.json")

    # 生成测试JSON
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
                    "params": {"command": "dir test_script.py", "terminal_type": "cmd"}
                },
                {
                    "step_type": "run_terminal",
                    "params": {"command": "Get-ChildItem test_script.py", "terminal_type": "powershell"}
                }
            ]
        }
        with open(TEST_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(test_workflow, f, ensure_ascii=False, indent=4)
        print(f"📝 测试JSON已生成：{TEST_JSON_PATH}\n")

    # 执行工作流
    try:
        executor = LangChainWorkflowExecutor()
        executor.execute_workflow(TEST_JSON_PATH)
    except Exception as e:
        print(f"❌ 执行异常：{str(e)}")

    # ====================== 大模型集成示例（StructuredTool适配） ======================
    """
    from langchain_openai import ChatOpenAI
    from langchain.agents import create_openai_tools_agent, AgentExecutor
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    # 1. 初始化大模型
    llm = ChatOpenAI(model="gpt-3.5-turbo", api_key="你的API_KEY", temperature=0)

    # 2. 构建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是代码执行助手，所有文件都在当前目录创建/执行，严格调用结构化工具完成任务。"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # 3. 创建Agent（支持结构化工具）
    agent = create_openai_tools_agent(llm, [code_tool], prompt)
    agent_executor = AgentExecutor(agent=agent, tools=[code_tool], verbose=True)

    # 4. 大模型自主执行任务
    result = agent_executor.invoke({
        "input": "创建calc.py，内容为计算10*20并打印，执行后用PowerShell查看文件信息"
    })
    print("大模型执行结果：", result["output"])
    """
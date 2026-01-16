# backend/agent/core.py
import json
from typing import Dict, List, Optional, Any, Callable
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

# --- 1. 定义模拟工具 ---
def get_weather(city: str) -> str:
    return f"【模拟数据】{city} 天气晴，25度"

def send_notification(user_id: str, message: str) -> str:
    return f"【模拟数据】已向用户 {user_id} 发送: {message}"

# 工具注册表
TOOL_REGISTRY = {
    "get_weather": get_weather,
    "send_notification": send_notification
}

# --- 2. 定义数据结构 ---
class PlanningResponse(BaseModel):
    plan: List[Dict[str, Any]]

class AgentState(Dict):
    user_tools: List[Dict] 
    user_requirement: str
    memory_info: str
    plan_data: Optional[Dict]
    execution_results: List[Dict]

# --- 3. 节点逻辑 ---
def planner_node(state: AgentState):
    """思考节点：生成计划"""
    tools_desc = "\n".join([str(t) for t in state["user_tools"]])
    
    system_prompt = """
    你是一个任务规划助手。请根据提供的工具和用户需求生成 JSON 执行计划。
    输出格式必须包含 'plan' 数组。
    """
    user_prompt = f"工具列表:\n{tools_desc}\n用户需求:\n{state['user_requirement']}"

    try:
        # ⚠️ 确保你有环境变量 OPENAI_API_KEY
        model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        # 构造链
        chain = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ]) | model | JsonOutputParser(pydantic_object=PlanningResponse)
        
        result = chain.invoke({})
    except Exception as e:
        # 容错处理
        result = {"plan": [], "error": str(e)}

    return {"plan_data": result}

def executor_node(state: AgentState):
    """执行节点：调用函数"""
    plan = state.get("plan_data", {}).get("plan", [])
    results = []

    for step in plan:
        tool_name = step.get("tool_name")
        args = step.get("arguments", {})
        
        func = TOOL_REGISTRY.get(tool_name)
        if func:
            try:
                output = func(**args)
                status = "success"
            except Exception as e:
                output = str(e)
                status = "error"
        else:
            output = "工具未找到"
            status = "error"
            
        results.append({
            "tool": tool_name,
            "output": output,
            "status": status
        })
        
    return {"execution_results": results}

# --- 4. 构建图 ---
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", END)

agent_app = workflow.compile()
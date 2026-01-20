"""
AI Agent 核心逻辑

使用 LangGraph 构建智能 Agent 工作流，实现任务规划和执行。
包含工具注册表、状态定义、节点逻辑和图构建。
"""
import json
from typing import Dict, List, Optional, Any, Callable
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

#TODO: 完善工具注册表，添加更多实际可用的工具
# ====================== 工具注册表 ======================

def get_weather(city: str) -> str:
    """获取天气信息（模拟）"""
    return f"【模拟数据】{city} 天气晴，25度"


def send_notification(user_id: str, message: str) -> str:
    """发送通知（模拟）"""
    return f"【模拟数据】已向用户 {user_id} 发送: {message}"


TOOL_REGISTRY = {
    "get_weather": get_weather,
    "send_notification": send_notification
}


# ====================== 数据结构定义 ======================

class PlanningResponse(BaseModel):
    """规划响应模型"""
    plan: List[Dict[str, Any]]


class AgentState(Dict):
    """
    Agent 状态
    
    Attributes:
        user_tools: 用户提供的工具列表
        user_requirement: 用户需求
        memory_info: 记忆信息
        plan_data: 规划数据
        execution_results: 执行结果列表
    """
    user_tools: List[Dict] 
    user_requirement: str
    memory_info: str
    plan_data: Optional[Dict]
    execution_results: List[Dict]


# ====================== 节点逻辑 ======================

def planner_node(state: AgentState):
    """
    规划节点：生成执行计划
    
    根据用户需求和可用工具，生成 JSON 格式的执行计划。
    
    Args:
        state: Agent 当前状态
        
    Returns:
        Dict: 包含规划数据的更新状态
    """
    tools_desc = "\n".join([str(t) for t in state["user_tools"]])
    
    system_prompt = """
    你是一个任务规划助手。请根据提供的工具和用户需求生成 JSON 执行计划。
    输出格式必须包含 'plan' 数组。
    """
    user_prompt = f"工具列表:\n{tools_desc}\n用户需求:\n{state['user_requirement']}"

    try:
        model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        chain = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ]) | model | JsonOutputParser(pydantic_object=PlanningResponse)
        
        result = chain.invoke({})
        logger.info(f"📋 规划节点生成计划: {result}")
    except Exception as e:
        logger.error(f"❌ 规划节点执行失败: {str(e)}")
        result = {"plan": [], "error": str(e)}

    return {"plan_data": result}


def executor_node(state: AgentState):
    """
    执行节点：调用工具函数
    
    根据规划数据，依次调用工具函数并收集执行结果。
    
    Args:
        state: Agent 当前状态
        
    Returns:
        Dict: 包含执行结果的更新状态
    """
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
                logger.info(f"✅ 工具 {tool_name} 执行成功")
            except Exception as e:
                output = str(e)
                status = "error"
                logger.error(f"❌ 工具 {tool_name} 执行失败: {str(e)}")
        else:
            output = "工具未找到"
            status = "error"
            logger.warning(f"⚠️ 工具 {tool_name} 未找到")
            
        results.append({
            "tool": tool_name,
            "output": output,
            "status": status
        })
        
    return {"execution_results": results}


# ====================== 工作流构建 ======================

workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", END)

agent_app = workflow.compile()
logger.info("🤖 AI Agent 工作流初始化完成")
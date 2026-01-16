# backend/api/agent.py
import json
from typing import List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

# 引入模型和逻辑
from backend.models import AgentTask, AgentResult
from backend.agent.core import agent_app

# 定义路由
router = APIRouter(prefix="/agent", tags=["AI Agent"])

class ToolDef(BaseModel):
    name: str
    args: Dict[str, Any]
    description: str

class AgentRequest(BaseModel):
    tools: List[ToolDef]
    memory_info: str = ""
    user_requirement: str

@router.post("/run")
async def run_agent(request: AgentRequest):
    # 1. 存入数据库 (Tortoise 异步写法)
    task_obj = await AgentTask.create(
        input_json=json.dumps(request.dict(), ensure_ascii=False)
    )
    
    # 2. 调用 AI (LangGraph 异步调用)
    initial_state = {
        "user_tools": [t.dict() for t in request.tools],
        "user_requirement": request.user_requirement,
        "memory_info": request.memory_info,
        "plan_data": None,
        "execution_results": []
    }
    
    # 使用 ainvoke 防止阻塞
    final_state = await agent_app.ainvoke(initial_state)
    
    final_output = {
        "plan": final_state.get("plan_data"),
        "results": final_state.get("execution_results")
    }

    # 3. 存结果
    await AgentResult.create(
        task=task_obj,
        final_output=json.dumps(final_output, ensure_ascii=False)
    )
    
    return {
        "task_id": str(task_obj.task_id),
        "data": final_output
    }
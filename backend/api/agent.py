"""
AI Agent API 路由

提供 AI Agent 任务执行接口，支持工具调用、任务规划和结果存储。
使用 LangGraph 构建工作流，实现智能任务执行。
"""
import json
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from models import AgentTask, AgentResult
from agent.core import agent_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI Agent"])


class ToolDef(BaseModel):
    """工具定义模型"""
    name: str
    args: Dict[str, Any]
    description: str


class AgentRequest(BaseModel):
    """Agent 请求模型"""
    tools: List[ToolDef]
    memory_info: str = ""
    user_requirement: str


@router.post("/run")
async def run_agent(request: AgentRequest):
    """
    执行 AI Agent 任务
    
    流程：
    1. 创建任务记录并保存到数据库
    2. 调用 LangGraph 工作流执行任务
    3. 保存执行结果到数据库
    
    Args:
        request: Agent 请求，包含工具列表和用户需求
        
    Returns:
        Dict: 包含任务ID和执行结果的响应
        
    Raises:
        HTTPException: 任务执行失败时抛出异常
    """
    try:
        logger.info(f"🤖 开始执行 Agent 任务: {request.user_requirement[:50]}...")
        
        task_obj = await AgentTask.create(
            input_json=json.dumps(request.dict(), ensure_ascii=False),
            task_type="general",
            status="running"
        )
        
        initial_state = {
            "user_tools": [t.dict() for t in request.tools],
            "user_requirement": request.user_requirement,
            "memory_info": request.memory_info,
            "plan_data": None,
            "execution_results": []
        }
        
        final_state = await agent_app.ainvoke(initial_state)
        
        final_output = {
            "plan": final_state.get("plan_data"),
            "results": final_state.get("execution_results")
        }

        await AgentResult.create(
            task=task_obj,
            final_output=json.dumps(final_output, ensure_ascii=False)
        )
        
        await task_obj.update_from_dict({"status": "completed"})
        await task_obj.save()
        
        logger.info(f"✅ Agent 任务执行完成: {task_obj.task_id}")
        
        return {
            "task_id": str(task_obj.task_id),
            "data": final_output
        }
    except Exception as e:
        logger.error(f"❌ Agent 任务执行失败: {str(e)}")
        if 'task_obj' in locals():
            await task_obj.update_from_dict({"status": "failed"})
            await task_obj.save()
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {str(e)}")
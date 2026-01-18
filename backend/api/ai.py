"""
AI 对话 API 路由

提供 AI 对话功能，支持创建对话实例、发送消息、获取历史等。
使用 LangChain 和阿里云通义千问模型实现智能对话。
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from tortoise.expressions import Q
import json
from datetime import datetime
import logging

from models import AIChatInstance, AIChatMessage
from config import settings

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains import LLMChain
from langchain_classic.prompts import PromptTemplate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI对话"])

conversation_memory_cache: Dict[str, ConversationBufferMemory] = {}

llm = ChatOpenAI(
    model="qwen-plus",
    temperature=0.7,
    openai_api_key=settings.QWEN_API_KEY or "sk-55446596eada420db8bf883864458e9f",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    streaming=True
)

SYSTEM_PROMPT = """
你是一个专业的Web安全顾问，名为WebScan AI。你的任务是帮助用户解决Web安全相关问题，包括漏洞分析、安全加固建议、扫描报告解读等。

你需要：
1. 提供专业、准确的安全建议
2. 解释技术概念时要清晰易懂
3. 针对用户的具体问题给出具体解决方案
4. 保持友好、专业的语气
5. 当用户提供扫描报告或漏洞信息时，进行深入分析
"""

@router.post("/chat/instances", response_model=Dict[str, Any])
async def create_chat_instance(
    chat_name: Optional[str] = None,
    chat_type: Optional[str] = "general",
    user_id: Optional[str] = None
):
    """
    创建新的对话实例
    
    Args:
        chat_name: 对话名称
        chat_type: 对话类型
        user_id: 用户ID
        
    Returns:
        Dict: 包含对话实例信息的响应
    """
    try:
        chat_instance = await AIChatInstance.create(
            id=uuid4(),
            user_id=user_id,
            chat_name=chat_name or f"新对话_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            chat_type=chat_type,
            status="active"
        )
        
        conversation_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        conversation_memory_cache[str(chat_instance.id)] = conversation_memory
        
        logger.info(f"✅ 创建对话实例: {chat_instance.id}")
        
        return {
            "code": 200,
            "message": "对话实例创建成功",
            "data": {
                "chat_instance_id": str(chat_instance.id),
                "chat_name": chat_instance.chat_name,
                "chat_type": chat_instance.chat_type,
                "created_at": chat_instance.created_at,
                "updated_at": chat_instance.updated_at
            }
        }
    except Exception as e:
        logger.error(f"❌ 创建对话实例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建对话实例失败: {str(e)}")


@router.get("/chat/instances", response_model=Dict[str, Any])
async def list_chat_instances(
    user_id: Optional[str] = None,
    status: Optional[str] = "active",
    page: int = 1,
    page_size: int = 20
):
    """
    列出对话实例
    """
    try:
        # 构建查询条件
        query = Q()
        if user_id:
            query &= Q(user_id=user_id)
        if status:
            query &= Q(status=status)
        
        # 查询对话实例
        instances = await AIChatInstance.filter(query) \
            .order_by("-updated_at") \
            .offset((page - 1) * page_size) \
            .limit(page_size)
        
        total = await AIChatInstance.filter(query).count()
        
        # 转换为响应格式
        instance_list = []
        for instance in instances:
            # 获取最新消息
            latest_message = await AIChatMessage.filter(
                chat_instance_id=instance.id
            ).order_by("-created_at").first()
            
            instance_list.append({
                "chat_instance_id": str(instance.id),
                "chat_name": instance.chat_name,
                "chat_type": instance.chat_type,
                "status": instance.status,
                "created_at": instance.created_at,
                "updated_at": instance.updated_at,
                "latest_message": {
                    "role": latest_message.role if latest_message else None,
                    "content": latest_message.content[:100] if latest_message else None,
                    "created_at": latest_message.created_at if latest_message else None
                } if latest_message else None
            })
        
        return {
            "code": 200,
            "message": "查询对话实例成功",
            "data": {
                "items": instance_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询对话实例失败: {str(e)}")


@router.get("/chat/instances/{chat_instance_id}", response_model=Dict[str, Any])
async def get_chat_instance(chat_instance_id: UUID):
    """
    获取对话实例详情
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        # 获取消息列表
        messages = await AIChatMessage.filter(chat_instance_id=chat_instance_id) \
            .order_by("created_at")
        
        message_list = [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "message_type": message.message_type,
                "created_at": message.created_at
            }
            for message in messages
        ]
        
        return {
            "code": 200,
            "message": "查询对话实例成功",
            "data": {
                "chat_instance": {
                    "chat_instance_id": str(chat_instance.id),
                    "chat_name": chat_instance.chat_name,
                    "chat_type": chat_instance.chat_type,
                    "status": chat_instance.status,
                    "created_at": chat_instance.created_at,
                    "updated_at": chat_instance.updated_at
                },
                "messages": message_list
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询对话实例失败: {str(e)}")


@router.delete("/chat/instances/{chat_instance_id}", response_model=Dict[str, Any])
async def delete_chat_instance(chat_instance_id: UUID):
    """
    删除对话实例
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        # 删除对话实例及其消息
        await AIChatMessage.filter(chat_instance_id=chat_instance_id).delete()
        await chat_instance.delete()
        
        # 从缓存中删除
        if str(chat_instance_id) in conversation_memory_cache:
            del conversation_memory_cache[str(chat_instance_id)]
        
        return {
            "code": 200,
            "message": "对话实例删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除对话实例失败: {str(e)}")


from pydantic import BaseModel


class MessageRequest(BaseModel):
    """消息请求模型"""
    content: str
    message_type: Optional[str] = "text"
    user_id: Optional[str] = None


@router.post("/chat/instances/{chat_instance_id}/messages", response_model=Dict[str, Any])
async def send_message(
    chat_instance_id: UUID,
    request: MessageRequest
):
    """
    发送消息到对话实例
    
    Args:
        chat_instance_id: 对话实例ID
        request: 消息请求
        
    Returns:
        Dict: 包含用户消息和AI响应的响应
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            logger.error(f"❌ 对话实例不存在: {chat_instance_id}")
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        if chat_instance.status != "active":
            logger.warning(f"⚠️ 对话实例已关闭: {chat_instance_id}")
            raise HTTPException(status_code=400, detail="对话实例已关闭")
        
        user_message = await AIChatMessage.create(
            chat_instance_id=chat_instance_id,
            role="user",
            content=request.content,
            message_type=request.message_type
        )
        
        if str(chat_instance_id) not in conversation_memory_cache:
            conversation_memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            history_messages = await AIChatMessage.filter(
                chat_instance_id=chat_instance_id
            ).order_by("created_at")
            
            for msg in history_messages:
                if msg.role == "user":
                    conversation_memory.chat_memory.add_user_message(msg.content)
                elif msg.role == "assistant":
                    conversation_memory.chat_memory.add_ai_message(msg.content)
            
            conversation_memory_cache[str(chat_instance_id)] = conversation_memory
        
        conversation_memory = conversation_memory_cache[str(chat_instance_id)]
        
        prompt = PromptTemplate(
            input_variables=["chat_history", "human_input"],
            template="""{chat_history}

Human: {human_input}
Assistant:"""
        )
        
        conversation = LLMChain(
            llm=llm,
            memory=conversation_memory,
            prompt=prompt
        )
        
        response_content = await conversation.arun(human_input=request.content)
        
        conversation_memory.chat_memory.add_user_message(request.content)
        conversation_memory.chat_memory.add_ai_message(response_content)
        
        ai_message = await AIChatMessage.create(
            chat_instance_id=chat_instance_id,
            role="assistant",
            content=response_content,
            message_type="text"
        )
        
        chat_instance.updated_at = datetime.now()
        await chat_instance.save()
        
        logger.info(f"✅ 消息发送成功: {chat_instance_id}")
        
        return {
            "code": 200,
            "message": "消息发送成功",
            "data": {
                "user_message": {
                    "id": user_message.id,
                    "role": user_message.role,
                    "content": user_message.content,
                    "created_at": user_message.created_at
                },
                "assistant_message": {
                    "id": ai_message.id,
                    "role": ai_message.role,
                    "content": ai_message.content,
                    "created_at": ai_message.created_at
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 发送消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


@router.get("/chat/instances/{chat_instance_id}/messages", response_model=Dict[str, Any])
async def get_chat_messages(
    chat_instance_id: UUID,
    page: int = 1,
    page_size: int = 50
):
    """
    获取对话消息历史
    """
    try:
        # 检查对话实例是否存在
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        # 查询消息
        messages = await AIChatMessage.filter(chat_instance_id=chat_instance_id) \
            .order_by("created_at") \
            .offset((page - 1) * page_size) \
            .limit(page_size)
        
        total = await AIChatMessage.filter(chat_instance_id=chat_instance_id).count()
        
        # 转换为响应格式
        message_list = []
        for message in messages:
            message_list.append({
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "message_type": message.message_type,
                "created_at": message.created_at
            })
        
        return {
            "code": 200,
            "message": "获取消息历史成功",
            "data": {
                "messages": message_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息历史失败: {str(e)}")


@router.post("/chat/instances/{chat_instance_id}/close", response_model=Dict[str, Any])
async def close_chat_instance(chat_instance_id: UUID):
    """
    关闭对话实例
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        # 更新状态
        chat_instance.status = "closed"
        await chat_instance.save()
        
        # 从缓存中删除
        if str(chat_instance_id) in conversation_memory_cache:
            del conversation_memory_cache[str(chat_instance_id)]
        
        return {
            "code": 200,
            "message": "对话实例关闭成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"关闭对话实例失败: {str(e)}")

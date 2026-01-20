"""
AI 对话 API 路由

提供 AI 对话功能，支持创建对话实例、发送消息、获取历史等。
使用 LangChain 和 OpenAI GPT-3.5-turbo 模型实现智能对话。
使用 ConversationSummaryMemory 进行对话总结和记忆管理。
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from tortoise.expressions import Q
from datetime import datetime
import logging

from models import AIChatInstance, AIChatMessage
from config import settings

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationSummaryMemory
from langchain.chains import ConversationChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI对话"])

#TODO: 优化模型参数
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    openai_api_key=settings.OPENAI_API_KEY,
    streaming=True
)

#TODO: 优化系统提示词
SYSTEM_PROMPT = """
你是一个专业的Web安全顾问，名为WebScan AI。你的任务是帮助用户解决Web安全相关问题，包括漏洞分析、安全加固建议、扫描报告解读等。

你需要：
1. 提供专业、准确的安全建议
2. 解释技术概念时要清晰易懂
3. 针对用户的具体问题给出具体解决方案
4. 保持友好、专业的语气
5. 当用户提供扫描报告或漏洞信息时，进行深入分析
"""

conversation_memory_cache: Dict[str, ConversationSummaryMemory] = {}


async def get_or_create_memory(chat_instance_id: UUID) -> ConversationSummaryMemory:
    """
    获取或创建对话记忆
    
    Args:
        chat_instance_id: 对话实例ID
        
    Returns:
        ConversationSummaryMemory: 对话记忆对象
    """
    chat_id = str(chat_instance_id)
    
    if chat_id not in conversation_memory_cache:
        memory = ConversationSummaryMemory(
            llm=llm,
            return_messages=True,
            max_token_limit=2000
        )
        
        history_messages = await AIChatMessage.filter(
            chat_instance_id=chat_instance_id
        ).order_by("created_at")
        
        for msg in history_messages:
            if msg.role == "user":
                memory.chat_memory.add_user_message(msg.content)
            elif msg.role == "assistant":
                memory.chat_memory.add_ai_message(msg.content)
        
        conversation_memory_cache[chat_id] = memory
        logger.info(f"✅ 创建对话记忆: {chat_id}")
    
    return conversation_memory_cache[chat_id]


async def clear_memory(chat_instance_id: UUID):
    """
    清除对话记忆
    
    Args:
        chat_instance_id: 对话实例ID
    """
    chat_id = str(chat_instance_id)
    if chat_id in conversation_memory_cache:
        del conversation_memory_cache[chat_id]
        logger.info(f"✅ 清除对话记忆: {chat_id}")


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
        
        await get_or_create_memory(chat_instance.id)
        
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
    
    Args:
        user_id: 用户ID
        status: 对话状态
        page: 页码
        page_size: 每页数量
        
    Returns:
        Dict: 包含对话实例列表的响应
    """
    try:
        query = Q()
        if user_id:
            query &= Q(user_id=user_id)
        if status:
            query &= Q(status=status)
        
        instances = await AIChatInstance.filter(query) \
            .order_by("-updated_at") \
            .offset((page - 1) * page_size) \
            .limit(page_size)
        
        total = await AIChatInstance.filter(query).count()
        
        instance_list = []
        for instance in instances:
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
        logger.error(f"❌ 查询对话实例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询对话实例失败: {str(e)}")


@router.get("/chat/instances/{chat_instance_id}", response_model=Dict[str, Any])
async def get_chat_instance(chat_instance_id: UUID):
    """
    获取对话实例详情
    
    Args:
        chat_instance_id: 对话实例ID
        
    Returns:
        Dict: 包含对话实例和消息列表的响应
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
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
        logger.error(f"❌ 查询对话实例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询对话实例失败: {str(e)}")


@router.delete("/chat/instances/{chat_instance_id}", response_model=Dict[str, Any])
async def delete_chat_instance(chat_instance_id: UUID):
    """
    删除对话实例
    
    Args:
        chat_instance_id: 对话实例ID
        
    Returns:
        Dict: 删除结果
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        await AIChatMessage.filter(chat_instance_id=chat_instance_id).delete()
        await chat_instance.delete()
        
        await clear_memory(chat_instance_id)
        
        return {
            "code": 200,
            "message": "对话实例删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除对话实例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除对话实例失败: {str(e)}")


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
        
        memory = await get_or_create_memory(chat_instance_id)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        conversation = ConversationChain(
            llm=llm,
            memory=memory,
            prompt=prompt,
            verbose=False
        )
        
        response_content = await conversation.ainvoke(
            {"input": request.content}
        )
        
        ai_message = await AIChatMessage.create(
            chat_instance_id=chat_instance_id,
            role="assistant",
            content=response_content["response"],
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
    
    Args:
        chat_instance_id: 对话实例ID
        page: 页码
        page_size: 每页数量
        
    Returns:
        Dict: 包含消息列表的响应
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        messages = await AIChatMessage.filter(chat_instance_id=chat_instance_id) \
            .order_by("created_at") \
            .offset((page - 1) * page_size) \
            .limit(page_size)
        
        total = await AIChatMessage.filter(chat_instance_id=chat_instance_id).count()
        
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
        logger.error(f"❌ 获取消息历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取消息历史失败: {str(e)}")


@router.post("/chat/instances/{chat_instance_id}/close", response_model=Dict[str, Any])
async def close_chat_instance(chat_instance_id: UUID):
    """
    关闭对话实例
    
    Args:
        chat_instance_id: 对话实例ID
        
    Returns:
        Dict: 关闭结果
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        chat_instance.status = "closed"
        await chat_instance.save()
        
        await clear_memory(chat_instance_id)
        
        return {
            "code": 200,
            "message": "对话实例关闭成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 关闭对话实例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"关闭对话实例失败: {str(e)}")

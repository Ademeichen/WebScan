"""
AI 对话 API 路由

提供 AI 对话功能，支持创建对话实例、发送消息、获取历史等。
使用 LangChain 和 OpenAI GPT-3.5-turbo 模型实现智能对话。
使用 ConversationSummaryMemory 进行对话总结和记忆管理。

主要功能：
- 创建和管理对话实例
- 发送消息并获取 AI 响应
- 对话历史记录查询
- 对话记忆管理
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from tortoise.expressions import Q
from datetime import datetime
import logging

from models import AIChatInstance, AIChatMessage
from backend.config import settings

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationSummaryMemory
from langchain.chains import ConversationChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI对话"])

llm = ChatOpenAI(
    model=settings.MODEL_ID,
    temperature=0.7,
    openai_api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    streaming=True
)

# TODO: 优化系统提示词
SYSTEM_PROMPT = """
你是一个专业的Web安全顾问，名为WebScan AI。你的任务是帮助用户解决Web安全相关问题，包括漏洞分析、安全加固建议、扫描报告解读等。

你需要：
1. 提供专业、准确的安全建议
2. 解释技术概念时要清晰易懂
3. 针对用户的具体问题给出具体解决方案
4. 保持友好、专业的语气
5. 当用户提供扫描报告或漏洞信息时，进行深入分析
"""

# 对话记忆缓存
conversation_memory_cache: Dict[str, ConversationSummaryMemory] = {}


async def get_or_create_memory(chat_instance_id: UUID) -> ConversationSummaryMemory:
    """
    获取或创建对话记忆
    
    从缓存中获取对话记忆，如果不存在则创建新的记忆对象并加载历史消息。
    
    Args:
        chat_instance_id: 对话实例 ID
        
    Returns:
        ConversationSummaryMemory: 对话记忆对象，包含历史对话内容
    """
    chat_id = str(chat_instance_id)
    
    if chat_id not in conversation_memory_cache:
        memory = ConversationSummaryMemory(
            llm=llm,
            return_messages=True,
            max_token_limit=2000
        )
        
        # 加载历史消息到记忆中
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
    
    从缓存中删除指定对话实例的记忆对象。
    
    Args:
        chat_instance_id: 对话实例 ID
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
    
    创建一个新的对话会话，并初始化对话记忆。
    
    Args:
        chat_name: 对话名称，如果不提供则自动生成
        chat_type: 对话类型，默认为 'general'
        user_id: 用户 ID，可选
        
    Returns:
        Dict: 包含对话实例信息的响应，结构如下:
            {
                "code": 200,
                "message": "对话实例创建成功",
                "data": {
                    "chat_instance_id": "对话ID",
                    "chat_name": "对话名称",
                    "chat_type": "对话类型",
                    "created_at": "创建时间",
                    "updated_at": "更新时间"
                }
            }
        
    Raises:
        HTTPException: 创建失败时抛出 500 错误
        
    Examples:
        >>> 创建新对话
        >>> POST /chat/instances
        >>> {
        ...     "chat_name": "漏洞分析",
        ...     "chat_type": "vulnerability",
        ...     "user_id": "user123"
        ... }
    """
    try:
        chat_instance = await AIChatInstance.create(
            id=uuid4(),
            user_id=user_id,
            chat_name=chat_name or f"新对话_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            chat_type=chat_type,
            status="active"
        )
        
        # 初始化对话记忆
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
    
    获取对话实例列表，支持按用户 ID 和状态过滤，以及分页查询。
    
    Args:
        user_id: 用户 ID，用于过滤
        status: 对话状态，默认为 'active'
        page: 页码，从 1 开始
        page_size: 每页数量
        
    Returns:
        Dict: 包含对话实例列表的响应，结构如下:
            {
                "code": 200,
                "message": "查询对话实例成功",
                "data": {
                    "items": [...],
                    "total": 总数,
                    "page": 当前页,
                    "page_size": 每页数量,
                    "total_pages": 总页数
                }
            }
        
    Raises:
        HTTPException: 查询失败时抛出 500 错误
        
    Examples:
        >>> 获取所有活跃对话
        >>> GET /chat/instances?status=active
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
            # 获取最新一条消息
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
    
    获取指定对话实例的详细信息，包括所有历史消息。
    
    Args:
        chat_instance_id: 对话实例 ID
        
    Returns:
        Dict: 包含对话实例和消息列表的响应，结构如下:
            {
                "code": 200,
                "message": "查询对话实例成功",
                "data": {
                    "chat_instance": {...},
                    "messages": [...]
                }
            }
        
    Raises:
        HTTPException: 当对话实例不存在时抛出 404 错误
        
    Examples:
        >>> 获取对话详情
        >>> GET /chat/instances/123e4567-e89b-12d3-a456-426614174000
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        # 获取所有消息
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
    
    删除指定的对话实例及其所有消息，并清除对话记忆缓存。
    
    Args:
        chat_instance_id: 对话实例 ID
        
    Returns:
        Dict: 删除结果，结构如下:
            {
                "code": 200,
                "message": "对话实例删除成功"
            }
        
    Raises:
        HTTPException: 当对话实例不存在时抛出 404 错误
        
    Examples:
        >>> 删除对话
        >>> DELETE /chat/instances/123e4567-e89b-12d3-a456-426614174000
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        # 删除所有消息
        await AIChatMessage.filter(chat_instance_id=chat_instance_id).delete()
        # 删除对话实例
        await chat_instance.delete()
        # 清除记忆缓存
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
    """
    消息请求模型
    
    Attributes:
        content: 消息内容
        message_type: 消息类型，默认为 'text'
        user_id: 用户 ID，可选
    """
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
    
    向指定对话实例发送用户消息，并获取 AI 的响应。
    
    Args:
        chat_instance_id: 对话实例 ID
        request: 消息请求，包含消息内容
        
    Returns:
        Dict: 包含用户消息和 AI 响应的响应，结构如下:
            {
                "code": 200,
                "message": "消息发送成功",
                "data": {
                    "user_message": {...},
                    "assistant_message": {...}
                }
            }
        
    Raises:
        HTTPException: 当对话实例不存在或已关闭时抛出错误
        
    Examples:
        >>> 发送消息
        >>> POST /chat/instances/123/messages
        >>> {
        ...     "content": "如何修复 SQL 注入漏洞？",
        ...     "message_type": "text"
        ... }
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            logger.error(f"❌ 对话实例不存在: {chat_instance_id}")
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        if chat_instance.status != "active":
            logger.warning(f"⚠️ 对话实例已关闭: {chat_instance_id}")
            raise HTTPException(status_code=400, detail="对话实例已关闭")
        
        # 保存用户消息
        user_message = await AIChatMessage.create(
            chat_instance_id=chat_instance_id,
            role="user",
            content=request.content,
            message_type=request.message_type
        )
        
        # 获取对话记忆
        memory = await get_or_create_memory(chat_instance_id)
        
        # 构建对话链
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
        
        # 调用 AI 获取响应
        response_content = await conversation.ainvoke(
            {"input": request.content}
        )
        
        # 保存 AI 响应
        ai_message = await AIChatMessage.create(
            chat_instance_id=chat_instance_id,
            role="assistant",
            content=response_content["response"],
            message_type="text"
        )
        
        # 更新对话实例时间
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
    
    获取指定对话实例的消息历史，支持分页查询。
    
    Args:
        chat_instance_id: 对话实例 ID
        page: 页码，从 1 开始
        page_size: 每页数量
        
    Returns:
        Dict: 包含消息列表的响应，结构如下:
            {
                "code": 200,
                "message": "获取消息历史成功",
                "data": {
                    "messages": [...],
                    "total": 总数,
                    "page": 当前页,
                    "page_size": 每页数量,
                    "total_pages": 总页数
                }
            }
        
    Raises:
        HTTPException: 当对话实例不存在时抛出 404 错误
        
    Examples:
        >>> 获取消息历史
        >>> GET /chat/instances/123/messages?page=1&page_size=20
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
    
    关闭指定的对话实例，并清除对话记忆缓存。
    
    Args:
        chat_instance_id: 对话实例 ID
        
    Returns:
        Dict: 关闭结果，结构如下:
            {
                "code": 200,
                "message": "对话实例关闭成功"
            }
        
    Raises:
        HTTPException: 当对话实例不存在时抛出 404 错误
        
    Examples:
        >>> 关闭对话
        >>> POST /chat/instances/123/close
    """
    try:
        chat_instance = await AIChatInstance.get_or_none(id=chat_instance_id)
        if not chat_instance:
            raise HTTPException(status_code=404, detail="对话实例不存在")
        
        # 更新状态
        chat_instance.status = "closed"
        await chat_instance.save()
        
        # 清除记忆缓存
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

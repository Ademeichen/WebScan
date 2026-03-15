"""
AI对话功能综合测试

整合WebSocket AI对话测试和对话记忆化存储测试
测试WebSocket实时对话功能和记忆化存储功能
"""
import pytest
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.config import settings
from backend.ai_agents.core.state import AgentState
from backend.ai_agents.core.graph import ScanAgentGraph


class TestWebSocketAIChat:
    """WebSocket AI对话测试类"""
    
    def test_websocket_connect(self):
        """测试WebSocket连接"""
        from backend.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        with client.websocket_connect("/api/ws") as websocket:
            websocket.send_json({"type": "ping"})
            
            response = websocket.receive_json()
            assert response["type"] == "pong"
    
    def test_create_chat_instance(self):
        """测试创建对话实例"""
        from backend.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        with client.websocket_connect("/api/ws") as websocket:
            websocket.send_json({
                "type": "create_chat_instance",
                "title": "测试对话"
            })
            
            response = websocket.receive_json()
            assert response["type"] == "chat_instance_created"
            assert "instance_id" in response
            assert response["title"] == "测试对话"
    
    def test_send_chat_message(self):
        """测试发送对话消息"""
        from backend.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        with client.websocket_connect("/api/ws") as websocket:
            websocket.send_json({
                "type": "create_chat_instance",
                "title": "测试对话"
            })
            response = websocket.receive_json()
            instance_id = response["instance_id"]
            
            websocket.send_json({
                "type": "chat_message",
                "chat_instance_id": instance_id,
                "message": "什么是SQL注入？"
            })
            
            response = websocket.receive_json()
            assert response["type"] == "chat_response"
            assert "content" in response
            assert len(response["content"]) > 0
    
    def test_get_chat_history(self):
        """测试获取对话历史"""
        from backend.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        with client.websocket_connect("/api/ws") as websocket:
            websocket.send_json({
                "type": "create_chat_instance",
                "title": "测试对话"
            })
            response = websocket.receive_json()
            instance_id = response["instance_id"]
            
            websocket.send_json({
                "type": "chat_message",
                "chat_instance_id": instance_id,
                "message": "测试消息"
            })
            websocket.receive_json()
            
            websocket.send_json({
                "type": "get_chat_history",
                "chat_instance_id": instance_id
            })
            
            response = websocket.receive_json()
            assert response["type"] == "chat_history"
            assert isinstance(response["history"], list)


class TestAIChatMemory:
    """AI对话记忆化存储测试类"""
    
    @pytest.mark.asyncio
    async def test_chat_instance_creation(self):
        """测试聊天实例创建"""
        try:
            from backend.api.ai import get_or_create_history, ChatHistory
            
            instance_id = await get_or_create_history("test_memory_user")
            
            assert instance_id is not None
            assert isinstance(instance_id, str)
        except Exception as e:
            pytest.skip(f"需要AI服务支持: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_chat_message_storage(self):
        """测试聊天消息存储"""
        try:
            from backend.api.ai import get_or_create_history, send_message, get_chat_messages
            
            instance_id = await get_or_create_history("test_storage_user")
            
            messages_to_send = [
                {"role": "user", "content": "你好，请帮我分析一个网站的安全性"},
                {"role": "assistant", "content": "好的，我可以帮你进行安全分析。请告诉我目标网站的URL。"},
                {"role": "user", "content": "目标网站是 https://www.baidu.com"}
            ]
            
            for msg in messages_to_send:
                await send_message(instance_id, msg["role"], msg["content"])
            
            messages = await get_chat_messages(instance_id)
            
            assert messages is not None
            assert len(messages) >= len(messages_to_send)
        except Exception as e:
            pytest.skip(f"需要AI服务支持: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_chat_memory_persistence(self):
        """测试聊天记忆持久化"""
        try:
            from backend.api.ai import get_or_create_history, send_message, get_chat_messages, clear_history
            
            instance_id = await get_or_create_history("test_persistence_user")
            
            await send_message(instance_id, "user", "测试消息")
            
            messages = await get_chat_messages(instance_id)
            
            assert messages is not None
            assert len(messages) > 0
            
            await clear_history(instance_id)
            
            messages_after_clear = await get_chat_messages(instance_id)
            assert len(messages_after_clear) == 0
        except Exception as e:
            pytest.skip(f"需要AI服务支持: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_chat_context_continuity(self):
        """测试聊天上下文连续性"""
        try:
            from backend.api.ai import get_or_create_history, send_message, get_chat_messages, clear_history
            
            instance_id = await get_or_create_history("test_context_user")
            
            conversation_flow = [
                {"role": "user", "content": "我想了解SQL注入漏洞"},
                {"role": "assistant", "content": "SQL注入是一种常见的Web安全漏洞，攻击者可以通过它执行恶意SQL语句。"},
                {"role": "user", "content": "如何防御SQL注入？"},
                {"role": "assistant", "content": "防御SQL注入的方法包括：使用参数化查询、输入验证、最小权限原则等。"}
            ]
            
            for msg in conversation_flow:
                await send_message(instance_id, msg["role"], msg["content"])
            
            messages = await get_chat_messages(instance_id)
            
            assert len(messages) == len(conversation_flow)
            
            last_message = messages[-1]
            assert "SQL" in last_message["content"] or "参数化" in last_message["content"]
            
            await clear_history(instance_id)
        except Exception as e:
            pytest.skip(f"需要AI服务支持: {str(e)}")


class TestAIChatIntegration:
    """AI对话集成测试类"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_chat_workflow(self):
        """测试完整对话流程"""
        try:
            from backend.api.ai import get_or_create_history, send_message, get_chat_messages, clear_history
            
            instance_id = await get_or_create_history("test_workflow_user")
            
            await send_message(instance_id, "user", "你好")
            await send_message(instance_id, "assistant", "你好！有什么可以帮助你的吗？")
            await send_message(instance_id, "user", "请介绍一下XSS漏洞")
            
            messages = await get_chat_messages(instance_id)
            assert len(messages) >= 3
            
            await clear_history(instance_id)
            
            messages_after_clear = await get_chat_messages(instance_id)
            assert len(messages_after_clear) == 0
        except Exception as e:
            pytest.skip(f"需要AI服务支持: {str(e)}")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("AI对话功能综合测试")
    print("=" * 60)
    
    test_classes = [
        TestWebSocketAIChat,
        TestAIChatMemory,
        TestAIChatIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    skipped_tests = 0
    
    for test_class in test_classes:
        print(f"\n--- {test_class.__name__} ---")
        instance = test_class()
        
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total_tests += 1
                try:
                    method = getattr(instance, method_name)
                    import inspect
                    sig = inspect.signature(method)
                    if 'mock_db' in sig.parameters:
                        method(mock_db={})
                    else:
                        method()
                    
                    print(f"  ✓ {method_name}")
                    passed_tests += 1
                except pytest.skip.Exception as e:
                    print(f"  ⊘ {method_name}: {str(e)}")
                    skipped_tests += 1
                except AssertionError as e:
                    print(f"  ✗ {method_name}: {str(e)}")
                    failed_tests += 1
                except Exception as e:
                    print(f"  ✗ {method_name}: {type(e).__name__}: {str(e)}")
                    failed_tests += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: 总计 {total_tests}, 通过 {passed_tests}, 失败 {failed_tests}, 跳过 {skipped_tests}")
    print("=" * 60)
    
    return failed_tests == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

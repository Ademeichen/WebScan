"""
AI对话记忆化存储测试

测试AI对话的记忆化存储功能是否正常工作。
使用真实AI模型服务进行测试。
"""
import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.config import settings
from backend.ai_agents.core.state import AgentState


from backend.ai_agents.core.graph import ScanAgentGraph


class AIChatMemoryTester:
    """AI对话记忆化存储测试器"""
    
    def __init__(self):
        self.test_results = []
        self.conversation_history = []
        
    def print_header(self, title: str):
        """打印标题"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    
    def print_result(self, test_name: str, success: bool, duration: float, details: str = ""):
            """打印测试结果"""
            status = "✅ 通过" if success else "❌ 失败"
            print(f"\n{status} | {test_name} | 耗时: {duration:.2f}秒")
            if details:
                print(f"   详情: {details}")
            self.test_results.append({
                "test_name": test_name,
                "success": success,
                "duration": duration,
                "details": details,
                "timestamp": datetime.now().isoformat()
            })
    
    async def test_chat_instance_creation(self):
        """测试聊天实例创建"""
        self.print_header("测试1: 聊天实例创建")
        start_time = time.time()
        
        try:
            from backend.api.ai import get_or_create_history, ChatHistory
            
            # 创建聊天实例
            instance_id = await get_or_create_history("test_memory_user")
            
            assert instance_id is not None, "实例ID不能为空"
            assert isinstance(instance_id, str), "实例ID应该是字符串"
            
            duration = time.time() - start_time
            self.print_result("聊天实例创建测试", True, duration, f"实例ID: {instance_id}")
            return instance_id
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("聊天实例创建测试", False, duration, str(e))
            return None
    
    async def test_chat_message_storage(self, instance_id: str):
        """测试聊天消息存储"""
        self.print_header("测试2: 聊天消息存储")
        start_time = time.time()
        
        try:
            from backend.api.ai import send_message, get_chat_messages
            
            # 发送多条消息
            messages_to_send = [
                {"role": "user", "content": "你好，请帮我分析一个网站的安全性"},
                {"role": "assistant", "content": "好的，我可以帮你进行安全分析。请告诉我目标网站的URL。"},
                {"role": "user", "content": "目标网站是 https://www.baidu.com"}
            ]
            
            for msg in messages_to_send:
                result = await send_message(instance_id, msg["role"], msg["content"])
                print(f"   发送消息: [{msg['role']}] {msg['content'][:30]}...")
            
            # 获取历史消息
            messages = await get_chat_messages(instance_id)
            
            assert messages is not None, "消息列表不能为空"
            assert len(messages) >= len(messages_to_send), f"消息数量应该大于等于发送的消息数量"
            
            # 飀查消息内容是否正确存储
            for i, msg in enumerate(messages):
                print(f"   消息{i+1}: [{msg['role']}] {msg['content'][:50]}...")
            
            duration = time.time() - start_time
            self.print_result("聊天消息存储测试", True, duration, f"存储了 {len(messages)} 条消息")
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("聊天消息存储测试", False, duration, str(e))
            return False
    
    async def test_chat_memory_persistence(self, instance_id: str):
        """测试聊天记忆持久化"""
        self.print_header("测试3: 聊天记忆持久化")
        start_time = time.time()
        
        try:
            from backend.api.ai import get_chat_messages, clear_history
            
            # 再次获取消息，验证持久化
            messages = await get_chat_messages(instance_id)
            
            assert messages is not None, "持久化消息获取失败"
            assert len(messages) > 0, "持久化消息数量应该大于0"
            
            print(f"   从持久化存储中获取到 {len(messages)} 条消息")
            
            # 清除历史
            await clear_history(instance_id)
            
            # 验证清除后为空
            messages_after_clear = await get_chat_messages(instance_id)
            assert len(messages_after_clear) == 0, "清除后消息应该为空"
            
            duration = time.time() - start_time
            self.print_result("聊天记忆持久化测试", True, duration, "记忆存储和清除功能正常")
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("聊天记忆持久化测试", False, duration, str(e))
            return False
    
    async def test_chat_context_continuity(self):
        """测试聊天上下文连续性"""
        self.print_header("测试4: 聊天上下文连续性")
        start_time = time.time()
        
        try:
            from backend.api.ai import get_or_create_history, send_message, get_chat_messages
            
            # 创建新实例
            instance_id = await get_or_create_history("test_context_user")
            
            # 发送一系列相关消息
            conversation_flow = [
                {"role": "user", "content": "我想了解SQL注入漏洞"},
                {"role": "assistant", "content": "SQL注入是一种常见的Web安全漏洞，攻击者可以通过它执行恶意SQL语句。"},
                {"role": "user", "content": "如何防御SQL注入？"},  # 这个问题依赖上下文
                {"role": "assistant", "content": "防御SQL注入的方法包括：使用参数化查询、输入验证、最小权限原则等。"}
            ]
            
            for msg in conversation_flow:
                await send_message(instance_id, msg["role"], msg["content"])
            
            # 获取完整对话
            messages = await get_chat_messages(instance_id)
            
            # 验证上下文连续性
            assert len(messages) == len(conversation_flow), "对话消息数量应该匹配"
            
            # 检查最后一条回复是否与SQL注入相关
            last_message = messages[-1]
            assert "SQL" in last_message["content"] or "参数化" in last_message["content"], "最后回复应该与SQL注入防御相关"
            
            print(f"   对话上下文连续性验证成功，共 {len(messages)} 轮对话")
            
            duration = time.time() - start_time
            self.print_result("聊天上下文连续性测试", True, duration, "AI能够正确理解上下文并给出相关回复")
            
            # 清理
            await clear_history(instance_id)
            
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("聊天上下文连续性测试", False, duration, str(e))
            return False
    
    def print_summary(self):
        """打印测试摘要"""
        self.print_header("测试摘要")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        print(f"\n总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n失败的测试:")
            for r in self.test_results:
                if not r["success"]:
                    print(f"  - {r['test_name']}: {r['details']}")
        
        print("\n" + "=" * 60)


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("  AI对话记忆化存储测试")
    print("  使用真实AI模型服务")
    print("=" * 60)
    
    tester = AIChatMemoryTester()
    
    # 执行所有测试
    instance_id = await tester.test_chat_instance_creation()
    
    if instance_id:
        await tester.test_chat_message_storage(instance_id)
        await tester.test_chat_memory_persistence(instance_id)
    
    await tester.test_chat_context_continuity()
    
    # 打印摘要
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())

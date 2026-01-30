"""
AI对话API测试
"""

from api_tester import APITester
from config import TEST_DATA


def test_ai_chat_api(tester: APITester):
    """测试AI对话API"""
    print("\n" + "=" * 60)
    print("测试AI对话API")
    print("=" * 60 + "\n")

    # 测试创建对话实例
    chat_response = tester.post("/ai/chat/instances", TEST_DATA["ai_chat"])

    if chat_response["success"]:
        chat_instance_id = chat_response["data"].get("data", {}).get("chat_instance_id")
        if chat_instance_id:
            # 测试获取对话实例详情
            tester.get(f"/ai/chat/instances/{chat_instance_id}")

            # 测试获取对话消息历史
            tester.get(f"/ai/chat/instances/{chat_instance_id}/messages")

            # 测试发送消息到对话实例
            tester.post(f"/ai/chat/instances/{chat_instance_id}/messages", {
                "content": "你好，请帮我分析这个漏洞",
                "role": "user"
            })

            # 测试关闭对话实例
            tester.post(f"/ai/chat/instances/{chat_instance_id}/close")

    # 测试列出对话实例
    tester.get("/ai/chat/instances")


if __name__ == "__main__":
    tester = APITester()
    test_ai_chat_api(tester)
    tester.print_summary()
    tester.save_results("ai_chat_test_results.json")

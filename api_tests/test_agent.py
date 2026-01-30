"""
AI Agent扫描API测试
"""

from api_tester import APITester
from config import TEST_DATA


def test_agent_api(tester: APITester):
    """测试AI Agent API"""
    print("\n" + "=" * 60)
    print("测试AI Agent API")
    print("=" * 60 + "\n")

    # 测试获取Agent任务列表
    tester.get("/ai_agents/tasks")

    # 测试获取Agent配置
    tester.get("/agent/config")

    # 测试获取可用工具列表
    tester.get("/agent/tools")

    # 测试获取环境信息
    tester.get("/agent/environment/info")

    # 测试获取环境可用工具
    tester.get("/agent/environment/tools")

    # 测试列出所有能力
    tester.get("/agent/capabilities/list")

    # 测试运行Agent任务
    agent_task_response = tester.post("/agent/run", TEST_DATA["agent_task"])

    if agent_task_response["success"]:
        task_id = agent_task_response["data"].get("data", {}).get("task_id")
        if task_id:
            # 测试获取Agent任务详情
            tester.get(f"/agent/tasks/{task_id}")

            # 测试取消Agent任务
            # tester.delete(f"/agent/tasks/{task_id}")

    # 测试生成扫描代码
    tester.post("/agent/code/generate", {
        "user_requirement": "扫描目标网站",
        "target": "http://127.0.0.1:8080"
    })

    # 测试执行代码
    tester.post("/agent/code/execute", {
        "code": "print('Hello World')",
        "language": "python"
    })

    # 测试生成并执行代码
    tester.post("/agent/code/generate-and-execute", {
        "user_requirement": "打印Hello",
        "target": "http://127.0.0.1:8080"
    })

    # 测试增强功能
    tester.post("/agent/capabilities/enhance", {
        "capability_name": "test_capability",
        "description": "测试功能"
    })

    # 测试获取能力详情
    tester.get("/agent/capabilities/test_capability")


if __name__ == "__main__":
    tester = APITester()
    test_agent_api(tester)
    tester.print_summary()
    tester.save_results("agent_test_results.json")

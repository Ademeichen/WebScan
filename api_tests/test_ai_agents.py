"""
AI Agents API测试
"""
from api_tester import APITester
from config import TEST_DATA

def test_ai_agents_api(tester: APITester):
    """测试AI Agents API"""
    print("\n" + "=" * 60)
    print("测试AI Agents API")
    print("=" * 60 + "\n")
    
    # 测试运行Agent任务
    print("1. 测试运行Agent任务")
    scan_response = tester.post("/ai_agents/scan", {
        "target": "https://example.com",
        "enable_llm_planning": True
    })
    
    # 获取实际创建的任务ID
    task_id = None
    if scan_response["success"] and scan_response.get("data"):
        task_id = scan_response["data"].get("data", {}).get("task_id")
        if task_id:
            print(f"✅ 创建任务成功，task_id: {task_id}")
    
    # 如果没有获取到task_id，尝试从任务列表获取
    if not task_id:
        print("\n1.5. 尝试获取已存在的任务ID")
        tasks_response = tester.get("/ai_agents/tasks")
        if tasks_response["success"] and tasks_response.get("data"):
            tasks = tasks_response["data"].get("data", {}).get("tasks", [])
            if tasks:
                task_id = tasks[0].get("task_id")
                print(f"✅ 使用已存在的任务，task_id: {task_id}")
    
    # 测试获取任务列表
    print("\n2. 测试获取Agent任务列表")
    tester.get("/ai_agents/tasks")
    
    # 测试获取任务详情
    print("\n3. 测试获取Agent任务详情")
    if task_id:
        tester.get(f"/ai_agents/tasks/{task_id}")
    else:
        print("   ⚠️ 跳过：没有可用的task_id")
    
    # 测试取消Agent任务
    print("\n4. 测试取消Agent任务")
    if task_id:
        tester.post(f"/ai_agents/tasks/{task_id}/cancel", {})
    else:
        print("   ⚠️ 跳过：没有可用的task_id")
    
    # 测试删除Agent任务
    print("\n5. 测试删除Agent任务")
    if task_id:
        tester.delete(f"/ai_agents/tasks/{task_id}")
    else:
        print("   ⚠️ 跳过：没有可用的task_id")
    
    # 测试获取工具列表
    print("\n6. 测试获取可用工具列表")
    tester.get("/ai_agents/tools")
    
    # 测试获取Agent配置
    print("\n7. 测试获取Agent配置")
    tester.get("/ai_agents/config")
    
    # 测试更新Agent配置
    print("\n8. 测试更新Agent配置")
    tester.post("/ai_agents/config", {
        "max_execution_time": 300,
        "enable_llm_planning": True
    })
    
    # 测试代码生成
    print("\n9. 测试代码生成")
    tester.post("/ai_agents/code/generate", {
        "scan_type": "port_scan",
        "target": "https://example.com",
        "language": "python"
    })
    
    # 测试代码执行
    print("\n10. 测试代码执行")
    tester.post("/ai_agents/code/execute", {
        "code": "print('Hello World')",
        "language": "python"
    })
    
    # 测试生成并执行代码
    print("\n11. 测试生成并执行代码")
    tester.post("/ai_agents/code/generate-and-execute", {
        "scan_type": "port_scan",
        "target": "https://example.com",
        "language": "python"
    })
    
    # 测试功能增强
    print("\n12. 测试功能增强")
    tester.post("/ai_agents/capabilities/enhance", {
        "requirement": "需要SQL注入检测功能",
        "target": "https://example.com"
    })
    
    # 测试获取能力列表
    print("\n13. 测试获取能力列表")
    tester.get("/ai_agents/capabilities/list")
    
    # 测试获取环境信息
    print("\n14. 测试获取环境信息")
    tester.get("/ai_agents/environment/info")
    
    # 测试获取可用工具
    print("\n15. 测试获取可用工具")
    tester.get("/ai_agents/environment/tools")

if __name__ == "__main__":
    tester = APITester()
    test_ai_agents_api(tester)
    tester.print_summary()
    tester.save_results("ai_agents_test_results.json")

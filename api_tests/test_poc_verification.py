"""
POC验证API测试
"""
from api_tester import APITester
from config import TEST_DATA, POC_VERIFICATION_DATA

def test_poc_verification_api(tester: APITester):
    """测试POC验证API"""
    print("\n" + "=" * 60)
    print("测试POC验证API")
    print("=" * 60 + "\n")
    
    # 测试创建POC验证任务
    print("1. 测试创建POC验证任务")
    tester.post("/poc-verification/tasks", POC_VERIFICATION_DATA["create_task"])
    
    # 测试批量创建POC验证任务
    print("\n2. 测试批量创建POC验证任务")
    tester.post("/poc-verification/tasks/batch", POC_VERIFICATION_DATA["batch_create_tasks"])
    
    # 测试获取POC验证任务列表
    print("\n3. 测试获取POC验证任务列表")
    tester.get("/poc-verification/tasks")
    
    # 测试获取POC验证任务详情
    print("\n4. 测试获取POC验证任务详情")
    task_id = 1
    tester.get(f"/poc-verification/tasks/{task_id}")
    
    # 测试暂停POC验证任务
    print("\n5. 测试暂停POC验证任务")
    tester.post(f"/poc-verification/tasks/{task_id}/pause", POC_VERIFICATION_DATA["pause_task"])
    
    # 测试恢复POC验证任务
    print("\n6. 测试恢复POC验证任务")
    tester.post(f"/poc-verification/tasks/{task_id}/resume", POC_VERIFICATION_DATA["resume_task"])
    
    # 测试取消POC验证任务
    print("\n7. 测试取消POC验证任务")
    tester.post(f"/poc-verification/tasks/{task_id}/cancel", POC_VERIFICATION_DATA["cancel_task"])
    
    # 测试获取POC验证任务结果
    print("\n8. 测试获取POC验证任务结果")
    tester.get(f"/poc-verification/tasks/{task_id}/results")
    
    # 测试生成POC验证报告
    print("\n9. 测试生成POC验证报告")
    tester.post(f"/poc-verification/tasks/{task_id}/report", POC_VERIFICATION_DATA["generate_report"])
    
    # 测试获取POC验证统计
    print("\n10. 测试获取POC验证统计")
    tester.get("/poc-verification/statistics")
    
    # 测试获取POC注册表
    print("\n11. 测试获取POC注册表")
    tester.get("/poc-verification/poc/registry")
    
    # 测试同步POC
    print("\n12. 测试同步POC")
    tester.post("/poc-verification/poc/sync", {})
    
    # 测试健康检查
    print("\n13. 测试健康检查")
    tester.get("/poc-verification/health")

if __name__ == "__main__":
    tester = APITester()
    test_poc_verification_api(tester)
    tester.print_summary()
    tester.save_results("poc_verification_test_results.json")

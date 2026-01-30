"""
扫描任务API测试
"""

from api_tester import APITester
from config import TEST_DATA, TEST_TARGETS


def test_tasks_api(tester: APITester):
    """测试扫描任务API"""
    print("\n" + "=" * 60)
    print("测试扫描任务API")
    print("=" * 60 + "\n")

    # 测试获取任务列表
    tester.get("/tasks/")

    # 测试获取任务统计概览
    tester.get("/tasks/statistics/overview")

    # 测试创建POC扫描任务
    poc_task_response = tester.post("/tasks/create", TEST_DATA["task"])
    if poc_task_response["success"]:
        task_id = poc_task_response["data"].get("data", {}).get("id")
        if task_id:
            # 测试获取任务详情
            tester.get(f"/tasks/{task_id}")

            # 测试获取任务结果
            tester.get(f"/tasks/{task_id}/results")

            # 测试获取任务漏洞列表
            tester.get(f"/tasks/{task_id}/vulnerabilities")

            # 测试更新任务状态
            tester.put(f"/tasks/{task_id}", {
                "status": "running",
                "progress": 50
            })

            # 测试取消任务
            tester.post(f"/tasks/{task_id}/cancel")

            # 测试删除任务
            # tester.delete(f"/tasks/{task_id}")

    # 测试创建AWVS扫描任务
    awvs_task_response = tester.post("/tasks/create", TEST_DATA["awvs_task"])
    if awvs_task_response["success"]:
        task_id = awvs_task_response["data"].get("data", {}).get("id")
        if task_id:
            # 测试获取任务详情
            tester.get(f"/tasks/{task_id}")

            # 测试获取任务结果
            tester.get(f"/tasks/{task_id}/results")

            # 测试获取任务漏洞列表
            tester.get(f"/tasks/{task_id}/vulnerabilities")

    # 测试带过滤条件的任务列表
    tester.get("/tasks/", {
        "status": "completed",
        "task_type": "poc_scan",
        "limit": 10,
        "skip": 0
    })


if __name__ == "__main__":
    tester = APITester()
    test_tasks_api(tester)
    tester.print_summary()
    tester.save_results("tasks_test_results.json")

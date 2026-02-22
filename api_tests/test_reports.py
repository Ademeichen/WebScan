"""
报告生成API测试
"""

from api_tester import APITester
from config import TEST_DATA


def test_reports_api(tester: APITester):
    """测试报告生成API"""
    print("\n" + "=" * 60)
    print("测试报告生成API")
    print("=" * 60 + "\n")

    # 测试获取报告列表
    tester.get("/reports/")

    # 测试获取报告列表（带过滤）
    tester.get("/reports/", {
        "task_id": 1,
        "limit": 10,
        "skip": 0
    })

    # 先创建一个任务，用于报告创建测试
    task_response = tester.post("/tasks/create", {
        "task_name": "测试报告任务",
        "target": "http://test.example.com",
        "task_type": "poc_scan",
        "config": {}
    })
    
    # 获取任务ID
    task_id = None
    if task_response["success"] and task_response.get("data"):
        task_id = task_response["data"].get("data", {}).get("task_id")
        if task_id:
            print(f"✅ 创建测试任务成功，task_id: {task_id}")
    
    # 如果任务创建失败，尝试使用已存在的任务
    if not task_id:
        tasks_list = tester.get("/tasks/")
        if tasks_list["success"] and tasks_list.get("data"):
            tasks = tasks_list["data"].get("data", {}).get("tasks", [])
            if tasks:
                task_id = tasks[0].get("id")
                print(f"✅ 使用已存在的任务，task_id: {task_id}")
    
    # 测试创建报告
    if task_id:
        report_data = {
            "task_id": task_id,
            "name": "测试报告",
            "format": "html",
            "content": {
                "summary": {"critical": 1, "high": 2, "medium": 3, "low": 4, "info": 5},
                "vulnerabilities": []
            }
        }
        report_response = tester.post("/reports/", report_data)

        if report_response["success"]:
            report_id = report_response["data"].get("data", {}).get("id")
            if report_id:
                # 测试获取报告详情
                tester.get(f"/reports/{report_id}")

                # 测试更新报告
                tester.put(f"/reports/{report_id}", {
                    "report_name": "更新后的报告名称",
                    "content": {"summary": "更新后的摘要"}
                })

                # 测试导出报告（JSON）
                tester.get(f"/reports/{report_id}/export", {
                    "format": "json"
                })

                # 测试导出报告（HTML）
                tester.get(f"/reports/{report_id}/export", {
                    "format": "html"
                })

                # 测试删除报告
                # tester.delete(f"/reports/{report_id}")
    else:
        print("❌ 无法获取有效的task_id，跳过报告创建测试")
        tester.test_results.append({
            "timestamp": "N/A",
            "method": "POST",
            "endpoint": "/reports/",
            "status_code": 0,
            "success": False,
            "response_time": 0,
            "error": "无法获取有效的task_id"
        })


if __name__ == "__main__":
    tester = APITester()
    test_reports_api(tester)
    tester.print_summary()
    tester.save_results("reports_test_results.json")

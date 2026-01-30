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

    # 测试创建报告
    report_response = tester.post("/reports/", TEST_DATA["report"])

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


if __name__ == "__main__":
    tester = APITester()
    test_reports_api(tester)
    tester.print_summary()
    tester.save_results("reports_test_results.json")

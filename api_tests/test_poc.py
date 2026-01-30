"""
POC扫描API测试
"""

from api_tester import APITester
from config import TEST_TARGETS, POC_TYPES


def test_poc_api(tester: APITester):
    """测试POC扫描API"""
    print("\n" + "=" * 60)
    print("测试POC扫描API")
    print("=" * 60 + "\n")

    # 测试获取POC类型列表
    tester.get("/poc/types")

    # 测试获取各个POC类型的详细信息
    for poc_type in POC_TYPES[:3]:  # 只测试前3个
        tester.get(f"/poc/info/{poc_type}")

    # 测试创建POC扫描任务
    tester.post("/poc/scan", {
        "target": TEST_TARGETS["url"],
        "poc_types": POC_TYPES[:3],
        "task_name": "POC扫描测试"
    })

    # 测试创建单个POC类型扫描
    tester.post("/poc/scan", {
        "target": TEST_TARGETS["url"],
        "poc_types": ["weblogic"],
        "task_name": "WebLogic POC扫描"
    })


if __name__ == "__main__":
    tester = APITester()
    test_poc_api(tester)
    tester.print_summary()
    tester.save_results("poc_test_results.json")

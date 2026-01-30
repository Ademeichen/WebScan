"""
AWVS扫描API测试
"""

from api_tester import APITester
from config import TEST_TARGETS


def test_awvs_api(tester: APITester):
    """测试AWVS扫描API"""
    print("\n" + "=" * 60)
    print("测试AWVS扫描API")
    print("=" * 60 + "\n")

    # 测试检查AWVS服务连接状态
    tester.get("/awvs/health")

    # 测试获取扫描列表
    tester.get("/awvs/scans")

    # 测试获取目标列表
    tester.get("/awvs/targets")

    # 测试添加扫描目标
    target_response = tester.post("/awvs/target", {
        "address": TEST_TARGETS["url"],
        "description": "测试目标"
    })

    # 测试创建AWVS扫描任务
    tester.post("/awvs/scan", {
        "target": TEST_TARGETS["url"],
        "profile_id": "11111111-1111-1111-1111-111111111111",
        "scan_name": "AWVS测试扫描"
    })

    # 测试获取漏洞排名
    tester.get("/awvs/vulnerabilities/rank")

    # 测试获取漏洞统计
    tester.get("/awvs/vulnerabilities/stats")

    # 测试获取中间件POC列表
    tester.get("/awvs/middleware/poc-list")

    # 测试获取中间件POC扫描任务
    tester.get("/awvs/middleware/scans")

    # 测试创建中间件POC扫描任务
    tester.post("/awvs/middleware/scan", {
        "target": TEST_TARGETS["url"],
        "middleware_types": ["weblogic", "tomcat"],
        "task_name": "中间件POC扫描"
    })

    # 测试启动中间件POC扫描
    tester.post("/awvs/middleware/scan/start", {
        "target": TEST_TARGETS["url"],
        "middleware_type": "weblogic"
    })


if __name__ == "__main__":
    tester = APITester()
    test_awvs_api(tester)
    tester.print_summary()
    tester.save_results("awvs_test_results.json")

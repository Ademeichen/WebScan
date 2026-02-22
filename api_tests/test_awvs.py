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
    print("1. 测试检查AWVS服务连接状态")
    tester.get("/awvs/health")

    # 测试获取扫描列表
    print("\n2. 测试获取扫描列表")
    tester.get("/awvs/scans")

    # 测试获取目标列表
    print("\n3. 测试获取目标列表")
    tester.get("/awvs/targets")

    # 测试添加扫描目标
    print("\n4. 测试添加扫描目标")
    target_response = tester.post("/awvs/target", {
        "address": TEST_TARGETS["url"],
        "description": "测试目标"
    })

    # 测试创建AWVS扫描任务
    print("\n5. 测试创建AWVS扫描任务")
    tester.post("/awvs/scan", {
        "url": TEST_TARGETS["url"],
        "scan_type": "full_scan"
    })

    # 测试获取漏洞排名
    print("\n6. 测试获取漏洞排名")
    tester.get("/awvs/vulnerabilities/rank")

    # 测试获取漏洞统计
    print("\n7. 测试获取漏洞统计")
    tester.get("/awvs/vulnerabilities/stats")

    # 测试获取中间件POC列表
    print("\n8. 测试获取中间件POC列表")
    tester.get("/awvs/middleware/poc-list")

    # 测试获取中间件POC扫描任务
    print("\n9. 测试获取中间件POC扫描任务")
    tester.get("/awvs/middleware/scans")

    # 测试创建中间件POC扫描任务
    print("\n10. 测试创建中间件POC扫描任务")
    tester.post("/awvs/middleware/scan", {
        "url": TEST_TARGETS["url"],
        "cve_id": "CVE-2020-2551"
    })

    # 测试启动中间件POC扫描
    print("\n11. 测试启动中间件POC扫描")
    tester.post("/awvs/middleware/scan/start", {
        "url": TEST_TARGETS["url"],
        "cve_id": "CVE-2018-2628"
    })


if __name__ == "__main__":
    tester = APITester()
    test_awvs_api(tester)
    tester.print_summary()
    tester.save_results("awvs_test_results.json")

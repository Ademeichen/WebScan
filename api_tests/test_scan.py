"""
扫描功能API测试
"""

from api_tester import APITester
from config import TEST_TARGETS


def test_scan_api(tester: APITester):
    """测试扫描功能API"""
    print("\n" + "=" * 60)
    print("测试扫描功能API")
    print("=" * 60 + "\n")

    # 测试端口扫描
    tester.post("/scan/port-scan", {
        "ip": TEST_TARGETS["ip"],
        "ports": "1-1000"
    })

    # 测试信息泄露检测
    tester.post("/scan/info-leak", {
        "url": TEST_TARGETS["url"]
    })

    # 测试旁站扫描
    tester.post("/scan/web-side", {
        "ip": TEST_TARGETS["ip"]
    })

    # 测试获取网站基本信息
    tester.post("/scan/baseinfo", {
        "url": TEST_TARGETS["url"]
    })

    # 测试获取网站权重
    tester.post("/scan/web-weight", {
        "url": TEST_TARGETS["url"]
    })

    # 测试IP定位
    tester.post("/scan/ip-locating", {
        "ip": TEST_TARGETS["ip"]
    })

    # 测试CDN检测
    tester.post("/scan/cdn-check", {
        "url": TEST_TARGETS["url"]
    })

    # 测试WAF检测
    tester.post("/scan/waf-check", {
        "url": TEST_TARGETS["url"]
    })

    # 测试CMS指纹识别
    tester.post("/scan/what-cms", {
        "url": TEST_TARGETS["url"]
    })

    # 测试子域名扫描
    tester.post("/scan/subdomain", {
        "domain": TEST_TARGETS["domain"],
        "deep_scan": False
    })

    # 测试目录扫描
    tester.post("/scan/dir-scan", {
        "url": TEST_TARGETS["url"]
    })

    # 测试综合扫描
    tester.post("/scan/comprehensive", {
        "url": TEST_TARGETS["url"]
    })


if __name__ == "__main__":
    tester = APITester()
    test_scan_api(tester)
    tester.print_summary()
    tester.save_results("scan_test_results.json")

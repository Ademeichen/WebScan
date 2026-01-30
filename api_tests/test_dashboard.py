"""
仪表盘和设置API测试
"""

from api_tester import APITester
from config import TEST_DATA


def test_dashboard_api(tester: APITester):
    """测试仪表盘API"""
    print("\n" + "=" * 60)
    print("测试仪表盘API")
    print("=" * 60 + "\n")

    # 测试获取统计信息
    tester.get("/settings/statistics")

    # 测试获取系统信息
    tester.get("/settings/system-info")

    # 测试获取设置
    tester.get("/settings/")


def test_settings_api(tester: APITester):
    """测试设置管理API"""
    print("\n" + "=" * 60)
    print("测试设置管理API")
    print("=" * 60 + "\n")

    # 测试获取所有设置
    tester.get("/settings/")

    # 测试获取设置分类
    tester.get("/settings/categories")

    # 测试获取指定分类的设置
    tester.get("/settings/category/general")
    tester.get("/settings/category/scan")

    # 测试获取单个设置项
    tester.get("/settings/item/general/systemName")

    # 测试更新单个设置项
    tester.put("/settings/item", {
        "category": "general",
        "key": "systemName",
        "value": "WebScan AI Test"
    })

    # 测试更新设置
    tester.put("/settings/", TEST_DATA["settings"])

    # 测试获取API密钥列表
    tester.get("/settings/api-keys")

    # 测试创建API密钥
    tester.post("/settings/api-keys", {
        "name": "Test API Key",
        "description": "测试用API密钥"
    })

    # 测试重置设置
    tester.post("/settings/reset/general")


if __name__ == "__main__":
    tester = APITester()
    test_dashboard_api(tester)
    test_settings_api(tester)
    tester.print_summary()
    tester.save_results("dashboard_test_results.json")

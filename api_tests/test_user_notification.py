"""
用户管理和通知API测试
"""

from api_tester import APITester
from config import TEST_DATA


def test_user_api(tester: APITester):
    """测试用户管理API"""
    print("\n" + "=" * 60)
    print("测试用户管理API")
    print("=" * 60 + "\n")

    # 测试获取用户信息
    tester.get("/user/profile")

    # 测试更新用户信息
    tester.put("/user/profile", TEST_DATA["user"])

    # 测试获取用户权限
    tester.get("/user/permissions")

    # 测试获取用户列表
    tester.get("/user/list")


def test_notification_api(tester: APITester):
    """测试通知管理API"""
    print("\n" + "=" * 60)
    print("测试通知管理API")
    print("=" * 60 + "\n")

    # 测试获取通知列表
    tester.get("/notifications/")

    # 测试获取未读通知数量
    tester.get("/notifications/count/unread")

    # 测试创建通知
    tester.post("/notifications/", TEST_DATA["notification"])

    # 测试获取通知详情
    tester.get("/notifications/1")

    # 测试标记通知为已读
    tester.put("/notifications/1/read")

    # 测试标记所有通知为已读
    print("\n9. 测试标记所有通知为已读")
    tester.put("/notifications/read-all")

    # 测试删除通知
    print("\n6. 测试删除通知")
    tester.delete("/notifications/1")

    # 测试删除所有已读通知
    print("\n7. 测试删除所有已读通知")
    tester.delete("/notifications/")


if __name__ == "__main__":
    tester = APITester()
    test_user_api(tester)
    test_notification_api(tester)
    tester.print_summary()
    tester.save_results("user_notification_test_results.json")

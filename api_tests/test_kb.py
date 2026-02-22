"""
漏洞知识库API测试
"""
from api_tester import APITester
from config import TEST_DATA, KB_DATA

def test_kb_api(tester: APITester):
    """测试漏洞知识库API"""
    print("\n" + "=" * 60)
    print("测试漏洞知识库API")
    print("=" * 60 + "\n")
    
    # 测试获取漏洞列表
    print("1. 测试获取漏洞列表")
    tester.get("/kb/vulnerabilities")
    
    # 测试获取漏洞详情
    print("\n2. 测试获取漏洞详情")
    ssvid = "12345"
    tester.get(f"/kb/vulnerability/{ssvid}")
    
    # 测试搜索漏洞
    print("\n3. 测试搜索漏洞")
    tester.post("/kb/vulnerabilities/search", KB_DATA["search_vulnerability"])

if __name__ == "__main__":
    tester = APITester()
    test_kb_api(tester)
    tester.print_summary()
    tester.save_results("kb_test_results.json")

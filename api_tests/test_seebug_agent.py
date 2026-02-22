"""
Seebug Agent API测试
"""
from api_tester import APITester
from config import TEST_DATA, SEEBUG_AGENT_DATA

def test_seebug_agent_api(tester: APITester):
    """测试Seebug Agent API"""
    print("\n" + "=" * 60)
    print("测试Seebug Agent API")
    print("=" * 60 + "\n")
    
    # 测试获取Seebug状态
    print("1. 测试获取Seebug状态")
    tester.get("/seebug/status")
    
    # 测试搜索Seebug漏洞
    print("\n2. 测试搜索Seebug漏洞")
    tester.post("/seebug/search", SEEBUG_AGENT_DATA["search_vulnerability"])
    
    # 测试获取漏洞详情
    print("\n3. 测试获取漏洞详情")
    ssvid = "12345"
    tester.get(f"/seebug/vulnerability/{ssvid}")
    
    # 测试生成POC
    print("\n4. 测试生成POC")
    tester.post("/seebug/generate-poc", SEEBUG_AGENT_DATA["generate_poc"])
    
    # 测试获取生成的POC
    print("\n5. 测试获取生成的POC")
    ssvid = "12345"
    tester.get(f"/seebug/generate-poc/{ssvid}")
    
    # 测试测试连接
    print("\n6. 测试测试连接")
    tester.get("/seebug/test-connection")

if __name__ == "__main__":
    tester = APITester()
    test_seebug_agent_api(tester)
    tester.print_summary()
    tester.save_results("seebug_agent_test_results.json")

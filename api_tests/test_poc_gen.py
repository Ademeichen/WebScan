"""
POC智能生成API测试
"""
from api_tester import APITester
from config import TEST_DATA, POC_GEN_DATA

def test_poc_gen_api(tester: APITester):
    """测试POC智能生成API"""
    print("\n" + "=" * 60)
    print("测试POC智能生成API")
    print("=" * 60 + "\n")
    
    # 测试生成POC
    print("1. 测试生成POC")
    tester.post("/poc-gen/generate", POC_GEN_DATA["generate_poc"])

if __name__ == "__main__":
    tester = APITester()
    test_poc_gen_api(tester)
    tester.print_summary()
    tester.save_results("poc_gen_test_results.json")

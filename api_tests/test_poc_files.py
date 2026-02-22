"""
POC文件管理API测试
"""
from api_tester import APITester
from config import TEST_DATA, POC_FILES_DATA

def test_poc_files_api(tester: APITester):
    """测试POC文件管理API"""
    print("\n" + "=" * 60)
    print("测试POC文件管理API")
    print("=" * 60 + "\n")
    
    # 测试获取POC文件列表
    print("1. 测试获取POC文件列表")
    tester.get("/poc-files/")
    
    # 测试上传POC文件
    print("\n2. 测试上传POC文件")
    tester.post("/poc-files/", POC_FILES_DATA["upload_file"])
    
    # 测试获取POC文件详情
    print("\n3. 测试获取POC文件详情")
    file_id = 1
    tester.get(f"/poc-files/{file_id}")
    
    # 测试更新POC文件
    print("\n4. 测试更新POC文件")
    tester.put(f"/poc-files/{file_id}", POC_FILES_DATA["update_file"])
    
    # 测试删除POC文件
    print("\n5. 测试删除POC文件")
    tester.delete(f"/poc-files/{file_id}")

if __name__ == "__main__":
    tester = APITester()
    test_poc_files_api(tester)
    tester.print_summary()
    tester.save_results("poc_files_test_results.json")

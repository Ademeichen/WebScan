"""
测试 Seebug API 连接
"""
import sys
from pathlib import Path

# 方式1: 直接使用 seebug_utils
from backend.utils.seebug_utils import seebug_utils

try:
    print("检查 Seebug_Agent 是否可用...")
    print(f"✓ seebug_utils.is_available() = {seebug_utils.is_available()}")
    
    if seebug_utils.is_available():
        print("✓ Seebug_Agent 可用")
        
        print("\n正在测试 API Key 验证...")
        result = seebug_utils.validate_api_key()
        print(f"✓ API Key 验证结果: {result}")
        
        if result.get("status") == "success":
            print("\n🎉 Seebug API 连接成功！")
        else:
            print("\n⚠️ Seebug API 连接失败，但将使用网页爬取模式")
        
        print("\n测试网页爬取模式搜索...")
        client = seebug_utils.get_client()
        if client and hasattr(client, '_search_poc_web'):
            web_result = client._search_poc_web("sql injection", page=1)
            print(f"✓ 网页爬取模式搜索结果: {web_result}")
            
        print("\n测试搜索漏洞...")
        search_result = seebug_utils.search_vulnerabilities("sql injection", page=1, page_size=5)
        print(f"✓ 搜索结果: {search_result}")
    else:
        print("✗ Seebug_Agent 不可用")
        
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()

"""
测试修复后的 Seebug API
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.api.seebug_agent import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(router, prefix="/seebug")

client = TestClient(app)

print("=" * 60)
print("测试修复后的 Seebug 状态 API")
print("=" * 60)

try:
    # 模拟调用 /seebug/status 端点
    print("\n1. 测试修复后的 API 响应:")
    response = client.get("/seebug/status")
    print(f"   状态码: {response.status_code}")
    print(f"   响应内容: {response.json()}")
    
    # 检查响应格式
    resp_json = response.json()
    print(f"\n   响应字段: {list(resp_json.keys())}")
    
    if 'code' in resp_json and 'data' in resp_json:
        print("   ✓ 响应包含 'code' 和 'data' 字段")
        data = resp_json['data']
        print(f"   ✓ data.available: {data.get('available')}")
        print(f"   ✓ data.message: {data.get('message')}")
        
        if data.get('available'):
            print("\n🎉 Seebug API 状态检查成功！")
        else:
            print("\n⚠️ Seebug API 不可用")
    else:
        print("   ✗ 响应格式不正确")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

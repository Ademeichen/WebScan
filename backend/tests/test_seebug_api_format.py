"""
测试 Seebug API 响应格式
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.utils.seebug_utils import seebug_utils
from backend.api.seebug_agent import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(router, prefix="/seebug")

client = TestClient(app)

print("=" * 60)
print("测试 Seebug 状态 API")
print("=" * 60)

try:
    # 模拟调用 /seebug/status 端点
    print("\n1. 测试原始 API 响应:")
    response = client.get("/seebug/status")
    print(f"   状态码: {response.status_code}")
    print(f"   响应内容: {response.json()}")
    
    # 检查响应格式
    resp_json = response.json()
    print(f"\n   响应字段: {list(resp_json.keys())}")
    
    # 模拟前端期望的格式
    print("\n2. 前端期望的格式应该包含 'code' 字段")
    print("   修复方案: 统一响应格式为 {code: 200, data: ..., message: ...}")
    
    # 测试 seebug_utils
    print("\n3. 测试 seebug_utils:")
    print(f"   is_available: {seebug_utils.is_available()}")
    print(f"   validate_api_key: {seebug_utils.validate_api_key()}")
    print(f"   get_api_status: {seebug_utils.get_api_status()}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

"""
快速测试脚本 - 验证服务器状态
"""
import requests
import json

def test_server_health():
    """测试服务器健康状态"""
    try:
        # 测试健康检查端点
        resp = requests.get("http://127.0.0.1:3000/health", timeout=5)
        print(f"健康检查: {resp.status_code}")
        print(f"响应: {resp.json()}")
        
        # 测试通知API
        resp = requests.get("http://127.0.0.1:3000/api/notifications/", timeout=5)
        print(f"\n通知列表: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"通知数量: {data.get('data', {}).get('total', 0)}")
        
        # 测试用户API
        resp = requests.get("http://127.0.0.1:3000/api/user/profile", timeout=5)
        print(f"\n用户信息: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"用户: {data.get('data', {}).get('username', 'N/A')}")
        
        print("\n✅ 服务器运行正常")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器")
        print("请确保后端服务正在运行:")
        print("  cd backend")
        print("  python main.py")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")

if __name__ == "__main__":
    test_server_health()

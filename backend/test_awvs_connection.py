#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试AWVS服务连接
"""
import requests
import urllib3

# 禁用SSL警告
urllib3.disable_warnings()

def test_awvs_connection():
    """测试AWVS服务连接"""
    api_url = "https://127.0.0.1:3443"
    api_key = "1986ad8c0a5b3df4d7028d5f3c06e936c266a8376a6364a69bf946e064f869b09"

    print("=" * 60)
    print("开始测试AWVS服务连接...")
    print("=" * 60)
    print(f"API URL: {api_url}")
    print(f"API Key: {api_key[:20]}...")
    print()

    # 测试1：检查端口连接
    print("【测试1】检查端口连接...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 3443))
        sock.close()
        if result == 0:
            print("✅ 端口3443连接成功")
        else:
            print(f"❌ 端口3443连接失败，错误码: {result}")
            return False
    except Exception as e:
        print(f"❌ 端口测试异常: {str(e)}")
        return False

    print()

    # 测试2：测试API连接
    print("【测试2】测试API连接...")
    try:
        response = requests.get(
            f"{api_url}/api/v1/info",
            headers={'X-Auth': api_key},
            verify=False,
            timeout=10
        )
        print(f"✅ API连接成功")
        print(f"   状态码: {response.status_code}")
        print(f"   响应内容: {response.text[:200]}")
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL证书错误: {str(e)}")
        print("   提示：AWVS使用自签名证书，已设置verify=False")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ 连接超时: {str(e)}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {str(e)}")
        print("   提示：请确认AWVS服务是否启动")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        return False

    print()

    # 测试3：测试获取扫描列表
    print("【测试3】测试获取扫描列表...")
    try:
        response = requests.get(
            f"{api_url}/api/v1/scans",
            headers={'X-Auth': api_key},
            verify=False,
            timeout=10
        )
        print(f"✅ 获取扫描列表成功")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            scans = data.get('scans', [])
            print(f"   当前扫描任务数: {len(scans)}")
    except Exception as e:
        print(f"❌ 获取扫描列表失败: {str(e)}")
        return False

    print()
    print("=" * 60)
    print("✅ AWVS服务连接测试完成！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_awvs_connection()

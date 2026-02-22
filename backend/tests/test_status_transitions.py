#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务状态转换业务规则验证测试
"""
import requests
import json

BASE_URL = "http://127.0.0.1:3000"

def test_task_status_transitions():
    print("=" * 60)
    print("任务状态转换业务规则验证测试")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # 1. 创建测试任务
    print("\n1. 创建测试任务...")
    create_data = {
        "task_name": "状态转换测试任务",
        "task_type": "scan_port",
        "target": "127.0.0.1"
    }
    response = requests.post(f"{BASE_URL}/api/tasks/create", json=create_data)
    if response.status_code == 200:
        result = response.json()
        task_id = result.get("data", {}).get("task_id")
        print(f"   [PASS] 任务创建成功, ID: {task_id}")
        passed += 1
    else:
        print(f"   [FAIL] 任务创建失败: {response.text}")
        failed += 1
        return passed, failed
    
    # 2. 测试非法状态转换: pending -> completed (应该失败)
    print("\n2. 测试非法状态转换: pending -> completed...")
    update_data = {"status": "completed", "progress": 100}
    response = requests.put(f"{BASE_URL}/api/tasks/{task_id}", json=update_data)
    if response.status_code == 400:
        print(f"   [PASS] 正确拒绝非法状态转换")
        print(f"   错误信息: {response.json().get('detail')}")
        passed += 1
    else:
        print(f"   [FAIL] 未正确拒绝非法状态转换: {response.text}")
        failed += 1
    
    # 3. 测试合法状态转换: pending -> running
    print("\n3. 测试合法状态转换: pending -> running...")
    update_data = {"status": "running", "progress": 50}
    response = requests.put(f"{BASE_URL}/api/tasks/{task_id}", json=update_data)
    if response.status_code == 200:
        print(f"   [PASS] 状态转换成功: pending -> running")
        passed += 1
    else:
        print(f"   [FAIL] 状态转换失败: {response.text}")
        failed += 1
    
    # 4. 测试合法状态转换: running -> completed
    print("\n4. 测试合法状态转换: running -> completed...")
    update_data = {"status": "completed", "progress": 100}
    response = requests.put(f"{BASE_URL}/api/tasks/{task_id}", json=update_data)
    if response.status_code == 200:
        print(f"   [PASS] 状态转换成功: running -> completed")
        passed += 1
    else:
        print(f"   [FAIL] 状态转换失败: {response.text}")
        failed += 1
    
    # 5. 测试非法状态转换: completed -> running (应该失败)
    print("\n5. 测试非法状态转换: completed -> running...")
    update_data = {"status": "running", "progress": 50}
    response = requests.put(f"{BASE_URL}/api/tasks/{task_id}", json=update_data)
    if response.status_code == 400:
        print(f"   [PASS] 正确拒绝非法状态转换")
        print(f"   错误信息: {response.json().get('detail')}")
        passed += 1
    else:
        print(f"   [FAIL] 未正确拒绝非法状态转换: {response.text}")
        failed += 1
    
    # 6. 清理测试数据
    print("\n6. 清理测试数据...")
    response = requests.delete(f"{BASE_URL}/api/tasks/{task_id}")
    if response.status_code == 200:
        print(f"   [PASS] 测试任务已删除")
        passed += 1
    else:
        print(f"   [FAIL] 删除失败: {response.text}")
        failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return passed, failed

if __name__ == "__main__":
    passed, failed = test_task_status_transitions()
    exit(0 if failed == 0 else 1)

#!/usr/bin/env python3
"""
Sandbox 测试脚本
用于测试和验证执行器功能
"""
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core_executor import CodeExecutor


def test_basic_functions():
    """测试基本功能"""
    print("测试 Sandbox 基本功能...")
    
    # 创建执行器
    executor = CodeExecutor()
    print(f"工作空间: {executor.workspace}")
    
    # 测试 1: 写入代码文件
    print("\n1. 测试写入代码文件:")
    code = """
print("Hello from Sandbox!")
for i in range(3):
    print(f"Count: {i}")
"""
    result = executor._write_code({
        "filename": "test_basic.py",
        "code": code,
        "language": "python"
    })
    
    if result.get("success"):
        print(f"   成功: {result.get('filepath')}")
    else:
        print(f"   失败: {result.get('error')}")
    
    # 测试 2: 执行代码文件
    print("\n2. 测试执行代码文件:")
    result = executor._execute_code({
        "filepath": "test_basic.py",
        "language": "python"
    })
    
    if result.get("success"):
        print(f"   成功，返回码: {result.get('returncode')}")
        print(f"   输出: {result.get('stdout', '')}")
    else:
        print(f"   失败: {result.get('error')}")
    
    # 测试 3: 执行命令
    print("\n3. 测试执行命令:")
    result = executor._execute_command({
        "command": "echo Test Command && dir /B",
        "shell": "cmd",
        "timeout": 10
    })
    
    if result.get("success"):
        print(f"   成功，返回码: {result.get('returncode')}")
        print(f"   输出: {result.get('stdout', '')[:200]}")
    else:
        print(f"   失败: {result.get('error')}")
    
    # 测试 4: 读取代码文件
    print("\n4. 测试读取代码文件:")
    result = executor._read_code({
        "filepath": "test_basic.py"
    })
    
    if result.get("success"):
        content = result.get("content", "")
        print(f"   成功，内容长度: {len(content)}")
        print(f"   前100字符: {content[:100]}...")
    else:
        print(f"   失败: {result.get('error')}")
    
    print("\n基本功能测试完成!")


def test_workflow():
    """测试完整工作流"""
    print("\n测试完整工作流...")
    
    # 创建执行器
    executor = CodeExecutor()
    
    # 测试配置
    test_config = {
        "name": "完整工作流测试",
        "actions": [
            {
                "type": "write_code",
                "name": "创建脚本11111",
                "filename": "workflow_test1.py",
                "language": "python",
                "code": "print('步骤1: 创建文件成功')"
            },
            {
                "type": "execute_code",
                "name": "执行脚本1111",
                "filepath": "workflow_test1.py",
                "language": "python"
            },
            {
                "type": "write_code",
                "name": "创建脚本2222",
                "filename": "workflow_test2.py",
                "language": "python",
                "code": "print('步骤2: 第二个脚本执行成功')"
            },
            {
                "type": "execute_code",
                "name": "执行脚本2222",
                "filepath": "workflow_test2.py",
                "language": "python"
            },
            {
                "type": "command",
                "name": "清理测试",
                "command": "echo 工作流测试完成",
                "shell": "cmd"
            }
        ]
    }
    
    # 执行工作流
    results = executor.execute_actions(test_config)
    
    # 输出结果
    print(f"总动作数: {len(results)}")
    successful = sum(1 for r in results if r.get("success", False))
    print(f"成功: {successful}")
    print(f"失败: {len(results) - successful}")
    
    for i, result in enumerate(results):
        status = "✓" if result.get("success") else "✗"
        print(f"{i+1}. [{status}] {result.get('action_type', 'unknown')}")
    
    print("\n工作流测试完成!")


def main():
    """主测试函数"""
    print("="*60)
    print("Sandbox 功能测试")
    print("="*60)
    
    try:
        test_basic_functions()
        test_workflow()
        
        print("\n" + "="*60)
        print("所有测试完成!")
        print("="*60)
        
        return 0
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
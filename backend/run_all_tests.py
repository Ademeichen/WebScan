"""
运行所有测试的脚本

执行项目中所有模块的测试。
"""
import sys
import subprocess
from pathlib import Path

backend_dir = Path(__file__).parent

# 定义测试目录
test_dirs = [
    "ai_agents/core/tests",
    "ai_agents/utils/tests",
    "ai_agents/tools/tests",
    "ai_agents/code_execution/tests",
    "ai_agents/analyzers/tests",
    "api/tests",
    "tests",
]

print("="*70)
print("运行所有测试")
print("="*70)

total_tests = 0
total_passed = 0
total_failed = 0

for test_dir in test_dirs:
    test_path = backend_dir / test_dir
    if not test_path.exists():
        print(f"\n⚠️  测试目录不存在: {test_dir}")
        continue
    
    print(f"\n运行测试: {test_dir}")
    print("-"*70)
    
    # 查找所有测试文件
    test_files = list(test_path.glob("test_*.py"))
    
    if not test_files:
        print(f"⚠️  没有找到测试文件")
        continue
    
    for test_file in test_files:
        print(f"  运行: {test_file.name}")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"    ✅ 通过")
                total_passed += 1
            else:
                print(f"    ❌ 失败")
                total_failed += 1
                if result.stdout:
                    print(f"    输出: {result.stdout[:200]}")
            
            total_tests += 1
            
        except subprocess.TimeoutExpired:
            print(f"    ⏱️  超时")
            total_failed += 1
            total_tests += 1
        except Exception as e:
            print(f"    ❌ 错误: {e}")
            total_failed += 1
            total_tests += 1

print("\n" + "="*70)
print("测试总结")
print("="*70)
print(f"总测试数: {total_tests}")
print(f"通过: {total_passed}")
print(f"失败: {total_failed}")
print(f"成功率: {total_passed/total_tests*100:.1f}%" if total_tests > 0 else "N/A")
print("="*70)

sys.exit(0 if total_failed == 0 else 1)

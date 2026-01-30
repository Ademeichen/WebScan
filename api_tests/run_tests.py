"""
主测试运行脚本 - 运行所有API测试
"""

import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_tester import APITester


def run_all_tests():
    """运行所有API测试"""
    print("=" * 80)
    print("WebScan AI Security Platform - 完整API测试套件")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API基础URL: http://127.0.0.1:3000/api")
    print("=" * 80)
    print()

    # 创建统一的测试器实例
    tester = APITester()

    # 测试模块列表
    test_modules = [
        ("仪表盘和设置", "test_dashboard", "test_dashboard_api"),
        ("扫描任务", "test_tasks", "test_tasks_api"),
        ("POC扫描", "test_poc", "test_poc_api"),
        ("AWVS扫描", "test_awvs", "test_awvs_api"),
        ("AI Agent", "test_agent", "test_agent_api"),
        ("报告生成", "test_reports", "test_reports_api"),
        ("扫描功能", "test_scan", "test_scan_api"),
        ("用户和通知", "test_user_notification", "test_user_api"),
        ("AI对话", "test_ai_chat", "test_ai_chat_api")
    ]

    # 运行每个测试模块
    for module_name, module_file, function_name in test_modules:
        try:
            print(f"\n{'=' * 80}")
            print(f"正在运行测试模块: {module_name}")
            print(f"{'=' * 80}\n")

            # 动态导入并运行测试模块
            module = __import__(module_file)
            if hasattr(module, function_name):
                func = getattr(module, function_name)
                func(tester)
            else:
                print(f"警告: {module_file} 模块没有 {function_name}() 函数")

        except ImportError as e:
            print(f"❌ 无法导入模块 {module_file}: {e}")
        except Exception as e:
            print(f"❌ 测试模块 {module_file} 执行失败: {e}")
            import traceback
            traceback.print_exc()

    # 打印总体测试摘要
    print("\n" + "=" * 80)
    print("总体测试摘要")
    print("=" * 80)
    tester.print_summary()

    # 保存总体测试结果
    filename = f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    tester.save_results(filename)

    print(f"\n测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


def run_specific_test(module_name: str):
    """运行指定的测试模块"""
    print("=" * 80)
    print(f"运行指定测试模块: {module_name}")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    tester = APITester()

    try:
        module = __import__(module_name)
        if hasattr(module, 'main'):
            module.main()
        else:
            print(f"警告: {module_name} 模块没有 main() 函数")

    except ImportError as e:
        print(f"❌ 无法导入模块 {module_name}: {e}")
    except Exception as e:
        print(f"❌ 测试模块 {module_name} 执行失败: {e}")
        import traceback
        traceback.print_exc()

    tester.print_summary()
    tester.save_results(f"{module_name}_results.json")


def list_tests():
    """列出所有可用的测试模块"""
    print("=" * 80)
    print("可用的测试模块")
    print("=" * 80)
    print()

    test_modules = [
        ("test_dashboard", "仪表盘和设置API测试"),
        ("test_tasks", "扫描任务API测试"),
        ("test_poc", "POC扫描API测试"),
        ("test_awvs", "AWVS扫描API测试"),
        ("test_agent", "AI Agent API测试"),
        ("test_reports", "报告生成API测试"),
        ("test_scan", "扫描功能API测试"),
        ("test_user_notification", "用户和通知API测试"),
        ("test_ai_chat", "AI对话API测试")
    ]

    for i, (module, description) in enumerate(test_modules, 1):
        print(f"{i}. {module:30s} - {description}")

    print()
    print("使用方法:")
    print("  python run_tests.py              # 运行所有测试")
    print("  python run_tests.py <module>     # 运行指定模块测试")
    print("  python run_tests.py --list       # 列出所有测试模块")
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--list" or arg == "-l":
            list_tests()
        else:
            run_specific_test(arg)
    else:
        run_all_tests()

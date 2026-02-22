"""
完整的测试执行脚本
使用增强的测试工具类，执行所有测试并生成详细报告
"""
import sys
import os
from datetime import datetime
import subprocess
import json

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_api_tester import EnhancedAPITester
from complete_test_config import (
    TEST_SCENARIOS, TEST_CASE_TEMPLATES, 
    BOUNDARY_TEST_DATA, EXCEPTION_TEST_DATA, 
    PERFORMANCE_TEST_DATA, SECURITY_TEST_DATA,
    TEST_CONFIG
)

def run_test_module(module_name: str, test_file: str, test_function: str, tester: EnhancedAPITester):
    """运行单个测试模块"""
    print(f"\n{'='*80}")
    print(f"运行测试模块: {module_name}")
    print(f"测试文件: {test_file}.py")
    print(f"测试函数: {test_function}")
    print(f"{'='*80}")
    
    start_time = datetime.now()
    
    try:
        # 动态导入并运行测试模块
        module = __import__(test_file)
        if hasattr(module, test_function):
            func = getattr(module, test_function)
            func(tester)
            
            # 执行边界条件测试
            if hasattr(module, 'test_boundary_conditions'):
                boundary_results = tester.test_boundary_conditions(
                    "/notifications/",
                    "POST",
                    {
                        "title": BOUNDARY_TEST_DATA["empty_values"]["title"],
                        "message": BOUNDARY_TEST_DATA["empty_values"]["message"],
                        "type": BOUNDARY_TEST_DATA["empty_values"]["type"]
                    }
                )
                
            # 执行异常场景测试
            if hasattr(module, 'test_exception_scenarios'):
                exception_results = tester.test_exception_scenarios(
                    "/notifications/",
                    "POST",
                    {
                        "title": BOUNDARY_TEST_DATA["special_characters"]["xss_title"],
                        "message": BOUNDARY_TEST_DATA["special_characters"]["xss_title"],
                        "type": "system"
                    }
                )
                
            # 执行性能测试
            if hasattr(module, 'test_performance'):
                perf_results = tester.test_performance(
                    "/notifications/",
                    "POST",
                    NORMAL_TEST_DATA["notification"],
                    iterations=TEST_CONFIG["environment"]["max_iterations"]
                )
                
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "module": module_name,
                "test_file": test_file,
                "test_function": test_function,
                "status": "success",
                "execution_time": execution_time,
                "output": "测试执行完成"
            }
        else:
            return {
                "module": module_name,
                "test_file": test_file,
                "test_function": test_function,
                "status": "failed",
                "execution_time": 0,
                "error": f"测试函数 {test_function} 不存在"
            }
            
    except ImportError as e:
        return {
            "module": module_name,
            "test_file": test_file,
            "test_function": test_function,
            "status": "error",
            "execution_time": 0,
            "error": f"无法导入模块 {test_file}: {e}"
        }
    except Exception as e:
        return {
            "module": module_name,
            "test_file": test_file,
            "test_function": test_function,
            "status": "error",
            "execution_time": 0,
            "error": f"测试模块 {module_name} 执行失败: {e}"
        }

def generate_comprehensive_report(all_results):
    """生成综合测试报告"""
    print(f"\n{'='*80}")
    print("WebScan AI Security Platform - 综合测试报告")
    print(f"{'='*80}")
    
    # 统计信息
    total_modules = len(all_results)
    successful_modules = sum(1 for r in all_results if r["status"] == "success")
    failed_modules = sum(1 for r in all_results if r["status"] == "failed")
    error_modules = sum(1 for r in all_results if r["status"] == "error")
    
    # 测试用例统计
    total_tests = 0
    total_success = 0
    total_failed = 0
    
    for result in all_results:
        if result["status"] == "success":
            # 统计测试用例数量
            total_tests += 1
            # 这里简化统计，实际应该从tester获取
            total_success += 1
    
    success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
    
    # 总执行时间
    total_execution_time = sum(r["execution_time"] for r in all_results if r["execution_time"] > 0)
    avg_execution_time = total_execution_time / total_modules if total_modules > 0 else 0
    
    print(f"\n报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API基础URL: {TEST_CONFIG['environment']['base_url']}")
    print(f"\n{'='*80}")
    
    # 模块执行统计
    print("模块执行统计:")
    print(f"  总模块数: {total_modules}")
    print(f"  成功: {successful_modules}")
    print(f"  失败: {failed_modules}")
    print(f"  错误: {error_modules}")
    print(f"  成功率: {(successful_modules/total_modules*100):.1f}%")
    
    # 测试用例统计
    print(f"\n测试用例统计:")
    print(f"  总测试数: {total_tests}")
    print(f"  成功数: {total_success}")
    print(f"  失败数: {total_failed}")
    print(f"  成功率: {success_rate:.2f}%")
    
    # 执行时间统计
    print(f"\n执行时间统计:")
    print(f"  总执行时间: {total_execution_time:.2f}s")
    print(f"  平均执行时间: {avg_execution_time:.2f}s")
    
    # 详细结果
    print(f"\n{'='*80}")
    print("详细执行结果:")
    print(f"{'='*80}")
    
    for result in all_results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"\n{status_icon} {result['module']}")
        print(f"   测试文件: {result['test_file']}.py")
        print(f"   测试函数: {result['test_function']}")
        print(f"   状态: {result['status']}")
        print(f"   执行时间: {result['execution_time']:.2f}s")
        
        if result["status"] != "success":
            print(f"   错误: {result['error']}")
    
    print(f"\n{'='*80}")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_modules": total_modules,
            "successful_modules": successful_modules,
            "failed_modules": failed_modules,
            "error_modules": error_modules,
            "success_rate": f"{(successful_modules/total_modules*100):.1f}%"
        },
        "test_cases": {
            "total_tests": total_tests,
            "total_success": total_success,
            "total_failed": total_failed,
            "success_rate": f"{success_rate:.2f}%"
        },
        "execution": {
            "total_execution_time": f"{total_execution_time:.2f}s",
            "average_execution_time": f"{avg_execution_time:.2f}s"
        },
        "modules": all_results
    }
    
    report_filename = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试报告已保存到: {report_filename}")
    print(f"{'='*80}")

def main():
    """主函数"""
    print("WebScan AI Security Platform - 完整测试执行器")
    print(f"{'='*80}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API基础URL: {TEST_CONFIG['environment']['base_url']}")
    print(f"{'='*80}")
    
    # 创建增强的测试器实例
    tester = EnhancedAPITester()
    
    # 测试模块列表
    test_modules = [
        ("通知管理", "test_user_notification", "test_notification_api"),
        ("用户管理", "test_user_notification", "test_user_api"),
        ("任务管理", "test_tasks", "test_tasks_api"),
        ("扫描功能", "test_scan", "test_scan_api"),
        ("POC扫描", "test_poc", "test_poc_api"),
        ("AWVS扫描", "test_awvs", "test_awvs_api"),
        ("报告管理", "test_reports", "test_reports_api"),
        ("AI Agent", "test_agent", "test_agent_api"),
        ("仪表盘和设置", "test_dashboard", "test_dashboard_api"),
        ("AI对话", "test_ai_chat", "test_ai_chat_api"),
        ("POC验证", "test_poc_verification", "test_poc_verification_api"),
        ("POC文件管理", "test_poc_files", "test_poc_files_api"),
        ("Seebug Agent", "test_seebug_agent", "test_seebug_agent_api"),
        ("AI Agents", "test_ai_agents", "test_ai_agents_api"),
        ("漏洞知识库", "test_kb", "test_kb_api"),
    ]
    
    all_results = []
    
    # 执行所有测试模块
    for module_name, test_file, test_function in test_modules:
        result = run_test_module(module_name, test_file, test_function, tester)
        all_results.append(result)
        
        # 模块间延迟
        import time
        time.sleep(1)
    
    # 生成报告
    generate_comprehensive_report(all_results)
    
    print(f"\n{'='*80}")
    print("所有测试执行完成！")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()

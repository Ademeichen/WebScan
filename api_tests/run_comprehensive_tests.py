"""
综合测试执行脚本
执行所有API测试并生成详细报告
"""
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

# 测试模块列表
TEST_MODULES = [
    ("仪表盘和设置", "test_dashboard", "test_dashboard_api"),
    ("扫描任务", "test_tasks", "test_tasks_api"),
    ("POC扫描", "test_poc", "test_poc_api"),
    ("AWVS扫描", "test_awvs", "test_awvs_api"),
    ("Agent功能", "test_agent", "test_agent_api"),
    ("报告管理", "test_reports", "test_reports_api"),
    ("扫描功能", "test_scan", "test_scan_api"),
    ("用户和通知", "test_user_notification", "test_user_notification_api"),
    ("AI对话", "test_ai_chat", "test_ai_chat_api"),
]

def run_test_module(module_name, test_file, test_function):
    """运行单个测试模块"""
    print(f"\n{'='*60}")
    print(f"运行测试模块: {module_name}")
    print(f"测试文件: {test_file}.py")
    print(f"测试函数: {test_function}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # 运行测试
        result = subprocess.run(
            ["python", f"{test_file}.py"],
            cwd="api_tests",
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        execution_time = time.time() - start_time
        
        # 解析测试结果
        if result.returncode == 0:
            # 尝试解析输出中的JSON结果
            output_lines = result.stdout.strip().split('\n')
            test_results = []
            
            for line in output_lines:
                if line.strip().startswith('{'):
                    try:
                        data = json.loads(line)
                        if 'total_tests' in data:
                            test_results.append(data)
                            break
                    except:
                        pass
            
            return {
                "module": module_name,
                "test_file": test_file,
                "test_function": test_function,
                "status": "success",
                "execution_time": execution_time,
                "output": result.stdout[:500],
                "test_results": test_results
            }
        else:
            return {
                "module": module_name,
                "test_file": test_file,
                "test_function": test_function,
                "status": "failed",
                "execution_time": time.time() - start_time,
                "error": result.stderr[:500] if result.stderr else "Unknown error",
                "output": result.stdout[:500]
            }
            
    except subprocess.TimeoutExpired:
        return {
            "module": module_name,
            "test_file": test_file,
            "test_function": test_function,
            "status": "timeout",
            "execution_time": time.time() - start_time,
            "error": "Test execution timeout after 5 minutes",
            "output": ""
        }
    except Exception as e:
        return {
            "module": module_name,
            "test_file": test_file,
            "test_function": test_function,
            "status": "error",
            "execution_time": time.time() - start_time,
            "error": str(e),
            "output": ""
        }

def generate_test_report(all_results):
    """生成测试报告"""
    print(f"\n{'='*80}")
    print("WebScan AI Security Platform - 综合测试报告")
    print(f"{'='*80}")
    
    # 统计信息
    total_modules = len(all_results)
    successful_modules = sum(1 for r in all_results if r["status"] == "success")
    failed_modules = sum(1 for r in all_results if r["status"] == "failed")
    timeout_modules = sum(1 for r in all_results if r["status"] == "timeout")
    error_modules = sum(1 for r in all_results if r["status"] == "error")
    
    # 测试用例统计
    total_tests = 0
    total_success = 0
    total_failed = 0
    
    for result in all_results:
        if result["status"] == "success" and result["test_results"]:
            for test_result in result["test_results"]:
                if 'total_tests' in test_result:
                    total_tests += test_result['total_tests']
                    total_success += test_result['success_count']
                    total_failed += test_result['failed_count']
    
    success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
    
    # 总执行时间
    total_execution_time = sum(r["execution_time"] for r in all_results)
    avg_execution_time = total_execution_time / total_modules if total_modules > 0 else 0
    
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API基础URL: http://127.0.0.1:3000/api")
    print(f"\n{'='*80}")
    
    # 模块执行统计
    print("模块执行统计:")
    print(f"  总模块数: {total_modules}")
    print(f"  成功: {successful_modules}")
    print(f"  失败: {failed_modules}")
    print(f"  超时: {timeout_modules}")
    print(f"  错误: {error_modules}")
    print(f"  成功率: {(successful_modules/total_modules*100):.1f}%")
    
    # 测试用例统计
    print(f"\n测试用例统计:")
    print(f"  总测试数: {total_tests}")
    print(f"  成功数: {total_success}")
    print(f"  失败数: {total_failed}")
    print(f"  成功率: {success_rate:.2f}%")
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
        
        if result["status"] == "success" and result["test_results"]:
            for test_result in result["test_results"]:
                if 'total_tests' in test_result:
                    print(f"   测试结果: {test_result['success_count']}/{test_result['total_tests']} 通过, 成功率: {test_result['success_rate']}")
        elif result["status"] != "success":
            print(f"   错误: {result['error']}")
    
    print(f"\n{'='*80}")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_modules": total_modules,
            "successful_modules": successful_modules,
            "failed_modules": failed_modules,
            "timeout_modules": timeout_modules,
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
    print("WebScan AI Security Platform - 综合测试执行器")
    print(f"{'='*80}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    all_results = []
    
    # 执行所有测试模块
    for module_name, test_file, test_function in TEST_MODULES:
        result = run_test_module(module_name, test_file, test_function)
        all_results.append(result)
        
        # 模块间延迟
        time.sleep(2)
    
    # 生成报告
    generate_test_report(all_results)
    
    print(f"\n{'='*80}")
    print("所有测试执行完成！")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()

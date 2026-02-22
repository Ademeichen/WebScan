"""
简化的测试执行脚本
"""
import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函数"""
    print("WebScan AI Security Platform - 简化测试执行器")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API基础URL: http://127.0.0.1:3000/api")
    print("=" * 80)
    
    # 测试模块列表
    test_modules = [
        ("通知管理", "test_user_notification"),
        ("用户管理", "test_user_notification"),
        ("任务管理", "test_tasks"),
        ("扫描功能", "test_scan"),
        ("POC扫描", "test_poc"),
        ("AWVS扫描", "test_awvs"),
        ("报告管理", "test_reports"),
        ("AI Agent", "test_agent"),
        ("仪表盘和设置", "test_dashboard"),
        ("AI对话", "test_ai_chat"),
    ]
    
    all_results = []
    
    # 执行每个测试模块
    for module_name, module_file in test_modules:
        print(f"\n{'='*80}")
        print(f"正在运行测试模块: {module_name}")
        print(f"测试文件: {module_file}.py")
        print(f"{'='*80}")
        
        start_time = datetime.now()
        
        try:
            # 运行测试模块
            result = subprocess.run(
                ["python", f"{module_file}.py"],
                cwd="api_tests",
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                all_results.append({
                    "module": module_name,
                    "test_file": module_file,
                    "status": "success",
                    "execution_time": execution_time,
                    "output": result.stdout[:500] if result.stdout else ""
                })
            else:
                all_results.append({
                    "module": module_name,
                    "test_file": module_file,
                    "status": "failed",
                    "execution_time": execution_time,
                    "error": result.stderr[:500] if result.stderr else "Unknown error",
                    "output": result.stdout[:500] if result.stdout else ""
                })
                
        except subprocess.TimeoutExpired:
            execution_time = (datetime.now() - start_time).total_seconds()
            all_results.append({
                "module": module_name,
                "test_file": module_file,
                "status": "timeout",
                "execution_time": execution_time,
                "error": "Test execution timeout after 5 minutes",
                "output": ""
            })
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            all_results.append({
                "module": module_name,
                "test_file": module_file,
                "status": "error",
                "execution_time": execution_time,
                "error": str(e),
                "output": ""
            })
        
        # 模块间延迟
        import time
        time.sleep(1)
    
    # 生成报告
    print(f"\n{'='*80}")
    print("测试执行摘要")
    print("=" * 80)
    
    total_modules = len(all_results)
    successful_modules = sum(1 for r in all_results if r["status"] == "success")
    failed_modules = sum(1 for r in all_results if r["status"] == "failed")
    timeout_modules = sum(1 for r in all_results if r["status"] == "timeout")
    error_modules = sum(1 for r in all_results if r["status"] == "error")
    
    print(f"总模块数: {total_modules}")
    print(f"成功: {successful_modules}")
    print(f"失败: {failed_modules}")
    print(f"超时: {timeout_modules}")
    print(f"错误: {error_modules}")
    print(f"成功率: {(successful_modules/total_modules*100):.1f}%")
    
    total_execution_time = sum(r["execution_time"] for r in all_results)
    avg_execution_time = total_execution_time / total_modules if total_modules > 0 else 0
    
    print(f"总执行时间: {total_execution_time:.2f}s")
    print(f"平均执行时间: {avg_execution_time:.2f}s")
    
    print("=" * 80)
    
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
        "execution": {
            "total_execution_time": f"{total_execution_time:.2f}s",
            "average_execution_time": f"{avg_execution_time:.2f}s"
        },
        "modules": all_results
    }
    
    report_filename = f"test_execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试报告已保存到: {report_filename}")
    print("=" * 80)

if __name__ == "__main__":
    main()

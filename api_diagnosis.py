"""
AI Agents API和报告管理API测试失败诊断脚本
收集并分析现有测试失败的具体表现、错误信息及复现步骤
"""
import requests
import json
from datetime import datetime

def test_api_endpoint(method, url, data=None, headers=None, description=""):
    """测试API端点并收集详细信息"""
    print(f"\n{'='*80}")
    print(f"测试: {description}")
    print(f"{'='*80}")
    print(f"方法: {method}")
    print(f"URL: {url}")
    if data:
        print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    if headers:
        print(f"请求头: {headers}")
    
    try:
        start_time = datetime.now()
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n状态码: {response.status_code}")
        print(f"响应时间: {duration:.3f}秒")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        else:
            print(f"错误响应: {response.text}")
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "duration": duration,
            "response": response.json() if response.status_code == 200 else response.text
        }
        
    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """主函数"""
    print("=" * 80)
    print("AI Agents API和报告管理API测试失败诊断")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 测试AI Agents API
    print("\n" + "=" * 80)
    print("AI Agents API测试")
    print("=" * 80)
    
    # 1. 测试启动Agent任务
    result = test_api_endpoint(
        "POST",
        "http://127.0.0.1:3000/api/ai_agents/scan",
        data={
            "target": "https://example.com",
            "enable_llm_planning": True,
            "custom_tasks": [],
            "need_custom_scan": False,
            "custom_scan_type": None,
            "custom_scan_requirements": None,
            "custom_scan_language": "python",
            "need_capability_enhancement": False,
            "capability_requirement": None
        },
        description="启动Agent任务 (POST /ai_agents/scan)"
    )
    results.append({"test": "POST /ai_agents/scan", **result})
    
    # 2. 测试获取任务列表
    result = test_api_endpoint(
        "GET",
        "http://127.0.0.1:3000/api/ai_agents/tasks",
        description="获取任务列表 (GET /ai_agents/tasks)"
    )
    results.append({"test": "GET /ai_agents/tasks", **result})
    
    # 3. 测试获取任务详情
    result = test_api_endpoint(
        "GET",
        "http://127.0.0.1:3000/api/ai_agents/tasks/1",
        description="获取任务详情 (GET /ai_agents/tasks/1)"
    )
    results.append({"test": "GET /ai_agents/tasks/1", **result})
    
    # 4. 测试取消任务
    result = test_api_endpoint(
        "POST",
        "http://127.0.0.1:3000/api/ai_agents/tasks/1/cancel",
        description="取消任务 (POST /ai_agents/tasks/1/cancel)"
    )
    results.append({"test": "POST /ai_agents/tasks/1/cancel", **result})
    
    # 5. 测试删除任务
    result = test_api_endpoint(
        "DELETE",
        "http://127.0.0.1:3000/api/ai_agents/tasks/1",
        description="删除任务 (DELETE /ai_agents/tasks/1)"
    )
    results.append({"test": "DELETE /ai_agents/tasks/1", **result})
    
    # 测试报告管理API
    print("\n" + "=" * 80)
    print("报告管理API测试")
    print("=" * 80)
    
    # 6. 测试获取报告列表
    result = test_api_endpoint(
        "GET",
        "http://127.0.0.1:3000/api/reports/",
        description="获取报告列表 (GET /reports/)"
    )
    results.append({"test": "GET /reports/", **result})
    
    # 7. 测试创建报告
    result = test_api_endpoint(
        "POST",
        "http://127.0.0.1:3000/api/reports/",
        data={
            "task_id": 35,
            "name": "测试报告",
            "format": "html",
            "content": {
                "summary": {"critical": 1, "high": 2, "medium": 3, "low": 4, "info": 5},
                "vulnerabilities": []
            }
        },
        description="创建报告 (POST /reports/)"
    )
    results.append({"test": "POST /reports/", **result})
    
    # 8. 测试获取报告详情
    result = test_api_endpoint(
        "GET",
        "http://127.0.0.1:3000/api/reports/1",
        description="获取报告详情 (GET /reports/1)"
    )
    results.append({"test": "GET /reports/1", **result})
    
    # 生成诊断报告
    print("\n" + "=" * 80)
    print("诊断报告摘要")
    print("=" * 80)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.get("success", False))
    failed_tests = total_tests - successful_tests
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"总测试数: {total_tests}")
    print(f"成功数: {successful_tests}")
    print(f"失败数: {failed_tests}")
    print(f"成功率: {success_rate:.2f}%")
    
    print("\n失败的测试:")
    for result in results:
        if not result.get("success", False):
            print(f"  ❌ {result['test']}")
            print(f"     状态码: {result.get('status_code', 'N/A')}")
            print(f"     错误: {result.get('error', result.get('response', 'N/A'))}")
    
    print("\n成功的测试:")
    for result in results:
        if result.get("success", False):
            print(f"  ✅ {result['test']}")
            print(f"     响应时间: {result.get('duration', 0):.3f}秒")
    
    # 保存详细报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{success_rate:.2f}%"
        },
        "results": results
    }
    
    report_file = "api_diagnosis_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细报告已保存到: {report_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()

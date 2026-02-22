"""
增强的API测试工具类
支持边界条件测试、异常场景测试和性能测试
"""
import requests
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import time

class EnhancedAPITester:
    """增强的API测试工具类"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:3000/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.performance_metrics = []
    
    def log_test(self, method: str, endpoint: str, status_code: int,
                success: bool, response_time: float, error: str = None,
                test_type: str = "normal"):
        """记录测试结果"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "success": success,
            "response_time": response_time,
            "error": error,
            "test_type": test_type
        }
        self.test_results.append(result)
        
        # 打印测试结果
        status_icon = "✅" if success else "❌"
        test_type_icon = {
            "normal": "🟢",
            "boundary": "🟡",
            "exception": "🔴",
            "performance": "⚡"
        }.get(test_type, "🔵")
        
        print(f"{status_icon} {test_type_icon} {method} {endpoint}")
        print(f"   Status: {status_code}, Time: {response_time:.3f}s, Type: {test_type}")
        if error:
            print(f"   Error: {error}")
        print()
        
        return result
    
    def get(self, endpoint: str, params: Dict = None, 
             test_type: str = "normal") -> Dict[str, Any]:
        """GET请求"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            error = None if success else f"Expected 200, got {response.status_code}"
            
            self.log_test("GET", endpoint, response.status_code, success, response_time, error, test_type)
            
            return {
                "success": success,
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "response_time": response_time
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("GET", endpoint, 0, False, response_time, str(e), test_type)
            return {
                "success": False,
                "status_code": 0,
                "error": str(e),
                "response_time": response_time
            }
    
    def post(self, endpoint: str, data: Dict = None, 
              test_type: str = "normal") -> Dict[str, Any]:
        """POST请求"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = self.session.post(url, json=data, timeout=30)
            response_time = time.time() - start_time
            
            success = response.status_code in [200, 201]
            error = None if success else f"Expected 200/201, got {response.status_code}"
            
            self.log_test("POST", endpoint, response.status_code, success, response_time, error, test_type)
            
            return {
                "success": success,
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "response_time": response_time
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("POST", endpoint, 0, False, response_time, str(e), test_type)
            return {
                "success": False,
                "status_code": 0,
                "error": str(e),
                "response_time": response_time
            }
    
    def put(self, endpoint: str, data: Dict = None, 
             test_type: str = "normal") -> Dict[str, Any]:
        """PUT请求"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = self.session.put(url, json=data, timeout=30)
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            error = None if success else f"Expected 200, got {response.status_code}"
            
            self.log_test("PUT", endpoint, response.status_code, success, response_time, error, test_type)
            
            return {
                "success": success,
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "response_time": response_time
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("PUT", endpoint, 0, False, response_time, str(e), test_type)
            return {
                "success": False,
                "status_code": 0,
                "error": str(e),
                "response_time": response_time
            }
    
    def delete(self, endpoint: str, 
               test_type: str = "normal") -> Dict[str, Any]:
        """DELETE请求"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = self.session.delete(url, timeout=30)
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            error = None if success else f"Expected 200, got {response.status_code}"
            
            self.log_test("DELETE", endpoint, response.status_code, success, response_time, error, test_type)
            
            return {
                "success": success,
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "response_time": response_time
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("DELETE", endpoint, 0, False, response_time, str(e), test_type)
            return {
                "success": False,
                "status_code": 0,
                "error": str(e),
                "response_time": response_time
            }
    
    def test_boundary_conditions(self, endpoint: str, method: str, 
                           boundary_data: Dict) -> List[Dict[str, Any]]:
        """测试边界条件"""
        results = []
        for test_name, test_data in boundary_data.items():
            print(f"\n🟡 边界测试: {test_name}")
            
            if method == "GET":
                result = self.get(endpoint, params=test_data, test_type="boundary")
            elif method == "POST":
                result = self.post(endpoint, data=test_data, test_type="boundary")
            elif method == "PUT":
                result = self.put(endpoint, data=test_data, test_type="boundary")
            elif method == "DELETE":
                result = self.delete(endpoint, test_type="boundary")
            
            results.append({
                "test_name": test_name,
                "result": result
            })
        
        return results
    
    def test_exception_scenarios(self, endpoint: str, method: str,
                             exception_scenarios: List[Tuple[str, Dict]]) -> List[Dict[str, Any]]:
        """测试异常场景"""
        results = []
        for test_name, test_data in exception_scenarios:
            print(f"\n🔴 异常测试: {test_name}")
            
            if method == "GET":
                result = self.get(endpoint, params=test_data, test_type="exception")
            elif method == "POST":
                result = self.post(endpoint, data=test_data, test_type="exception")
            elif method == "PUT":
                result = self.put(endpoint, data=test_data, test_type="exception")
            elif method == "DELETE":
                result = self.delete(endpoint, test_type="exception")
            
            results.append({
                "test_name": test_name,
                "result": result
            })
        
        return results
    
    def test_performance(self, endpoint: str, method: str, 
                     test_data: Dict, iterations: int = 10) -> Dict[str, Any]:
        """性能测试"""
        print(f"\n⚡ 性能测试: {endpoint} ({iterations}次迭代)")
        
        response_times = []
        for i in range(iterations):
            if method == "GET":
                result = self.get(endpoint, params=test_data, test_type="performance")
            elif method == "POST":
                result = self.post(endpoint, data=test_data, test_type="performance")
            elif method == "PUT":
                result = self.put(endpoint, data=test_data, test_type="performance")
            elif method == "DELETE":
                result = self.delete(endpoint, test_type="performance")
            
            if result["success"]:
                response_times.append(result["response_time"])
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            performance_result = {
                "endpoint": endpoint,
                "method": method,
                "iterations": iterations,
                "avg_response_time": avg_time,
                "min_response_time": min_time,
                "max_response_time": max_time,
                "success_rate": f"{(len(response_times) / iterations * 100):.1f}%"
            }
            
            self.performance_metrics.append(performance_result)
            
            print(f"  平均响应时间: {avg_time:.3f}s")
            print(f"  最小响应时间: {min_time:.3f}s")
            print(f"  最大响应时间: {max_time:.3f}s")
            print(f"  成功率: {performance_result['success_rate']}")
            
            return performance_result
        else:
            return {
                "endpoint": endpoint,
                "method": method,
                "iterations": iterations,
                "error": "All requests failed"
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取测试统计信息"""
        total = len(self.test_results)
        success = sum(1 for r in self.test_results if r["success"])
        failed = total - success
        success_rate = (success / total * 100) if total > 0 else 0
        
        # 按测试类型统计
        normal_count = sum(1 for r in self.test_results if r["test_type"] == "normal")
        boundary_count = sum(1 for r in self.test_results if r["test_type"] == "boundary")
        exception_count = sum(1 for r in self.test_results if r["test_type"] == "exception")
        performance_count = sum(1 for r in self.test_results if r["test_type"] == "performance")
        
        avg_response_time = sum(r["response_time"] for r in self.test_results) / total if total > 0 else 0
        
        return {
            "total_tests": total,
            "success_count": success,
            "failed_count": failed,
            "success_rate": f"{success_rate:.2f}%",
            "average_response_time": f"{avg_response_time:.3f}s",
            "test_type_breakdown": {
                "normal": normal_count,
                "boundary": boundary_count,
                "exception": exception_count,
                "performance": performance_count
            }
        }
    
    def print_summary(self):
        """打印测试摘要"""
        print("=" * 80)
        print("API测试摘要")
        print("=" * 80)
        
        stats = self.get_statistics()
        
        print(f"总测试数: {stats['total_tests']}")
        print(f"成功数: {stats['success_count']}")
        print(f"失败数: {stats['failed_count']}")
        print(f"成功率: {stats['success_rate']}")
        print(f"平均响应时间: {stats['average_response_time']}")
        
        print(f"\n测试类型统计:")
        print(f"  正常测试: {stats['test_type_breakdown']['normal']}")
        print(f"  边界测试: {stats['test_type_breakdown']['boundary']}")
        print(f"  异常测试: {stats['test_type_breakdown']['exception']}")
        print(f"  性能测试: {stats['test_type_breakdown']['performance']}")
        
        print("=" * 80)
        
        # 打印失败的测试
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print("\n失败的测试:")
            for test in failed_tests:
                print(f"  - {test['test_type']} {test['method']} {test['endpoint']}: {test['error']}")
            print("=" * 80)
    
    def save_results(self, filename: str = "api_test_results.json"):
        """保存测试结果到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": self.get_statistics(),
                "performance_metrics": self.performance_metrics,
                "results": self.test_results
            }, f, ensure_ascii=False, indent=2)
        print(f"\n测试结果已保存到: {filename}")

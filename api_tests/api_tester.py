"""
API测试工具类
"""

import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import time


class APITester:
    """API测试工具类"""

    def __init__(self, base_url: str = "http://127.0.0.1:3000/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []

    def log_test(self, method: str, endpoint: str, status_code: int,
                success: bool, response_time: float, error: str = None):
        """记录测试结果"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "success": success,
            "response_time": response_time,
            "error": error
        }
        self.test_results.append(result)

        # 打印测试结果
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {method} {endpoint}")
        print(f"   Status: {status_code}, Time: {response_time:.3f}s")
        if error:
            print(f"   Error: {error}")
        print()

        return result

    def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """GET请求"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            response = self.session.get(url, params=params, timeout=30)
            response_time = time.time() - start_time

            success = response.status_code == 200
            error = None if success else f"Expected 200, got {response.status_code}"

            self.log_test("GET", endpoint, response.status_code, success, response_time, error)

            return {
                "success": success,
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "response_time": response_time
            }

        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("GET", endpoint, 0, False, response_time, str(e))
            return {
                "success": False,
                "status_code": 0,
                "error": str(e),
                "response_time": response_time
            }

    def post(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """POST请求"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            response = self.session.post(url, json=data, timeout=30)
            response_time = time.time() - start_time

            success = response.status_code in [200, 201]
            error = None if success else f"Expected 200/201, got {response.status_code}"

            self.log_test("POST", endpoint, response.status_code, success, response_time, error)

            return {
                "success": success,
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "response_time": response_time
            }

        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("POST", endpoint, 0, False, response_time, str(e))
            return {
                "success": False,
                "status_code": 0,
                "error": str(e),
                "response_time": response_time
            }

    def put(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """PUT请求"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            response = self.session.put(url, json=data, timeout=30)
            response_time = time.time() - start_time

            success = response.status_code == 200
            error = None if success else f"Expected 200, got {response.status_code}"

            self.log_test("PUT", endpoint, response.status_code, success, response_time, error)

            return {
                "success": success,
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "response_time": response_time
            }

        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("PUT", endpoint, 0, False, response_time, str(e))
            return {
                "success": False,
                "status_code": 0,
                "error": str(e),
                "response_time": response_time
            }

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE请求"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            response = self.session.delete(url, timeout=30)
            response_time = time.time() - start_time

            success = response.status_code == 200
            error = None if success else f"Expected 200, got {response.status_code}"

            self.log_test("DELETE", endpoint, response.status_code, success, response_time, error)

            return {
                "success": success,
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "response_time": response_time
            }

        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("DELETE", endpoint, 0, False, response_time, str(e))
            return {
                "success": False,
                "status_code": 0,
                "error": str(e),
                "response_time": response_time
            }

    def get_statistics(self) -> Dict[str, Any]:
        """获取测试统计信息"""
        total = len(self.test_results)
        success = sum(1 for r in self.test_results if r["success"])
        failed = total - success
        success_rate = (success / total * 100) if total > 0 else 0

        avg_response_time = sum(r["response_time"] for r in self.test_results) / total if total > 0 else 0

        return {
            "total_tests": total,
            "success_count": success,
            "failed_count": failed,
            "success_rate": f"{success_rate:.2f}%",
            "average_response_time": f"{avg_response_time:.3f}s"
        }

    def print_summary(self):
        """打印测试摘要"""
        print("=" * 60)
        print("API测试摘要")
        print("=" * 60)

        stats = self.get_statistics()

        print(f"总测试数: {stats['total_tests']}")
        print(f"成功数: {stats['success_count']}")
        print(f"失败数: {stats['failed_count']}")
        print(f"成功率: {stats['success_rate']}")
        print(f"平均响应时间: {stats['average_response_time']}")
        print("=" * 60)

        # 打印失败的测试
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print("\n失败的测试:")
            for test in failed_tests:
                print(f"  - {test['method']} {test['endpoint']}: {test['error']}")
            print("=" * 60)

    def save_results(self, filename: str = "api_test_results.json"):
        """保存测试结果到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": self.get_statistics(),
                "results": self.test_results
            }, f, ensure_ascii=False, indent=2)
        print(f"\n测试结果已保存到: {filename}")

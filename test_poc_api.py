#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POC扫描后端API接口测试脚本
测试目标: http://127.0.0.1:8888/api

实际API端点:
1. POC类型列表: GET /api/poc/types
2. POC扫描任务创建: POST /api/poc/scan
3. 任务状态查询: GET /api/tasks/{task_id}
4. 任务结果获取: GET /api/tasks/{task_id}/results
5. POC验证: POST /api/poc/verification/tasks
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

BASE_URL = "http://127.0.0.1:8888/api"
TIMEOUT = 30

class TestResult:
    def __init__(self, name: str, endpoint: str, method: str):
        self.name = name
        self.endpoint = endpoint
        self.method = method
        self.status_code: Optional[int] = None
        self.response_time: float = 0.0
        self.success: bool = False
        self.response_data: Any = None
        self.error_message: str = ""
        self.test_cases: List[Dict] = []

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "response_time_ms": round(self.response_time * 1000, 2),
            "success": self.success,
            "error_message": self.error_message,
            "test_cases": self.test_cases
        }


class POCApiTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.session = requests.Session()

    def make_request(self, method: str, endpoint: str, 
                     params: Dict = None, json_data: Dict = None,
                     expected_status: int = 200) -> tuple:
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=TIMEOUT)
            elif method.upper() == "POST":
                response = self.session.post(url, json=json_data, params=params, timeout=TIMEOUT)
            else:
                response = self.session.request(method, url, params=params, json=json_data, timeout=TIMEOUT)
            
            elapsed = time.time() - start_time
            return response, elapsed, None
        except requests.exceptions.ConnectionError as e:
            elapsed = time.time() - start_time
            return None, elapsed, f"连接错误: {str(e)}"
        except requests.exceptions.Timeout as e:
            elapsed = time.time() - start_time
            return None, elapsed, f"请求超时: {str(e)}"
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            return None, elapsed, f"请求异常: {str(e)}"

    def test_poc_types(self) -> TestResult:
        result = TestResult("POC类型列表获取接口", "/poc/types", "GET")
        print("\n" + "="*60)
        print("测试接口: GET /api/poc/types")
        print("="*60)

        test_cases = []

        print("\n[测试用例1] 正常获取POC类型列表")
        response, elapsed, error = self.make_request("GET", "/poc/types")
        case1 = {
            "name": "正常获取POC类型列表",
            "params": None,
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": False,
            "response_data": None,
            "error": error
        }
        if response:
            try:
                data = response.json()
                case1["response_data"] = data
                case1["success"] = response.status_code == 200 and "code" in data
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                case1["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case1['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case1)

        print("\n[测试用例2] 获取POC详细信息")
        response, elapsed, error = self.make_request("GET", "/poc/info/weblogic")
        case2 = {
            "name": "获取POC详细信息(weblogic类别)",
            "params": {"poc_type": "weblogic"},
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": False,
            "response_data": None,
            "error": error
        }
        if response:
            try:
                data = response.json()
                case2["response_data"] = data
                case2["success"] = response.status_code == 200
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                case2["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case2['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case2)

        print("\n[测试用例3] 获取不存在的POC类型")
        response, elapsed, error = self.make_request("GET", "/poc/info/nonexistent_poc_type")
        case3 = {
            "name": "获取不存在的POC类型",
            "params": {"poc_type": "nonexistent_poc_type"},
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": response.status_code == 404 if response else False,
            "response_data": None,
            "error": error
        }
        if response:
            try:
                data = response.json()
                case3["response_data"] = data
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                case3["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case3['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case3)

        result.test_cases = test_cases
        result.success = any(case["success"] for case in test_cases)
        result.response_time = sum(case["response_time_ms"] for case in test_cases) / len(test_cases)
        result.status_code = test_cases[0]["status_code"]
        return result

    def test_poc_scan_create(self) -> TestResult:
        result = TestResult("POC扫描任务创建接口", "/poc/scan", "POST")
        print("\n" + "="*60)
        print("测试接口: POST /api/poc/scan")
        print("="*60)

        test_cases = []

        print("\n[测试用例1] 正常创建扫描任务")
        scan_data = {
            "target": "http://example.com",
            "poc_ids": ["poc-001", "poc-002"]
        }
        response, elapsed, error = self.make_request("POST", "/poc/scan", json_data=scan_data)
        case1 = {
            "name": "正常创建扫描任务",
            "params": scan_data,
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": False,
            "response_data": None,
            "error": error
        }
        task_id = None
        if response:
            try:
                data = response.json()
                case1["response_data"] = data
                case1["success"] = response.status_code in [200, 201]
                task_id = data.get("task_id") or data.get("data", {}).get("task_id")
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                if task_id:
                    print(f"  获取到task_id: {task_id}")
            except json.JSONDecodeError:
                case1["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case1['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case1)

        print("\n[测试用例2] 空参数创建扫描任务")
        response, elapsed, error = self.make_request("POST", "/poc/scan", json_data={})
        case2 = {
            "name": "空参数创建扫描任务",
            "params": {},
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": response.status_code in [400, 422] if response else False,
            "response_data": None,
            "error": error
        }
        if response:
            try:
                data = response.json()
                case2["response_data"] = data
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                case2["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case2['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case2)

        print("\n[测试用例3] 无效目标地址测试")
        invalid_data = {
            "target": "invalid-url",
            "poc_ids": []
        }
        response, elapsed, error = self.make_request("POST", "/poc/scan", json_data=invalid_data)
        case3 = {
            "name": "无效目标地址测试",
            "params": invalid_data,
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": response.status_code in [400, 422] if response else False,
            "response_data": None,
            "error": error
        }
        if response:
            try:
                data = response.json()
                case3["response_data"] = data
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                case3["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case3['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case3)

        result.test_cases = test_cases
        result.success = case1["success"]
        result.response_time = sum(case["response_time_ms"] for case in test_cases) / len(test_cases)
        result.status_code = test_cases[0]["status_code"]
        result.response_data = {"task_id": task_id}
        return result

    def test_task_status(self, task_id: int = None) -> TestResult:
        result = TestResult("任务状态查询接口", "/tasks/{task_id}", "GET")
        print("\n" + "="*60)
        print("测试接口: GET /api/tasks/{task_id}")
        print("="*60)

        test_cases = []

        if task_id:
            print(f"\n[测试用例1] 查询存在的任务状态 - task_id: {task_id}")
            response, elapsed, error = self.make_request("GET", f"/tasks/{task_id}")
            case1 = {
                "name": "查询存在的任务状态",
                "params": {"task_id": task_id},
                "status_code": response.status_code if response else None,
                "response_time_ms": round(elapsed * 1000, 2),
                "success": False,
                "response_data": None,
                "error": error
            }
            if response:
                try:
                    data = response.json()
                    case1["response_data"] = data
                    case1["success"] = response.status_code == 200 and "code" in data
                    print(f"  状态码: {response.status_code}")
                    print(f"  响应时间: {elapsed*1000:.2f}ms")
                    print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                except json.JSONDecodeError:
                    case1["error"] = "响应不是有效的JSON格式"
                    print(f"  错误: {case1['error']}")
            else:
                print(f"  错误: {error}")
            test_cases.append(case1)
        else:
            print("\n[测试用例1] 查询任务状态 - 使用task_id=1")
            response, elapsed, error = self.make_request("GET", "/tasks/1")
            case1 = {
                "name": "查询任务状态(task_id=1)",
                "params": {"task_id": 1},
                "status_code": response.status_code if response else None,
                "response_time_ms": round(elapsed * 1000, 2),
                "success": response.status_code in [200, 404] if response else False,
                "response_data": None,
                "error": error
            }
            if response:
                try:
                    data = response.json()
                    case1["response_data"] = data
                    print(f"  状态码: {response.status_code}")
                    print(f"  响应时间: {elapsed*1000:.2f}ms")
                    print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                except json.JSONDecodeError:
                    case1["error"] = "响应不是有效的JSON格式"
                    print(f"  错误: {case1['error']}")
            else:
                print(f"  错误: {error}")
            test_cases.append(case1)

        print("\n[测试用例2] 查询不存在的任务状态")
        fake_task_id = 999999
        response, elapsed, error = self.make_request("GET", f"/tasks/{fake_task_id}")
        case2 = {
            "name": "查询不存在的任务状态",
            "params": {"task_id": fake_task_id},
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": response.status_code == 404 if response else False,
            "response_data": None,
            "error": error
        }
        if response:
            try:
                data = response.json()
                case2["response_data"] = data
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                case2["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case2['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case2)

        print("\n[测试用例3] 无效task_id测试")
        response, elapsed, error = self.make_request("GET", "/tasks/invalid")
        case3 = {
            "name": "无效task_id测试",
            "params": {"task_id": "invalid"},
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": response.status_code in [400, 404, 422] if response else False,
            "response_data": None,
            "error": error
        }
        if response:
            try:
                data = response.json()
                case3["response_data"] = data
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                case3["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case3['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case3)

        result.test_cases = test_cases
        result.success = any(case["success"] for case in test_cases)
        result.response_time = sum(case["response_time_ms"] for case in test_cases) / len(test_cases)
        result.status_code = test_cases[0]["status_code"]
        return result

    def test_task_results(self, task_id: int = None) -> TestResult:
        result = TestResult("任务结果获取接口", "/tasks/{task_id}/results", "GET")
        print("\n" + "="*60)
        print("测试接口: GET /api/tasks/{task_id}/results")
        print("="*60)

        test_cases = []

        if task_id:
            print(f"\n[测试用例1] 获取存在任务的扫描结果 - task_id: {task_id}")
            response, elapsed, error = self.make_request("GET", f"/tasks/{task_id}/results")
            case1 = {
                "name": "获取存在任务的扫描结果",
                "params": {"task_id": task_id},
                "status_code": response.status_code if response else None,
                "response_time_ms": round(elapsed * 1000, 2),
                "success": False,
                "response_data": None,
                "error": error
            }
            if response:
                try:
                    data = response.json()
                    case1["response_data"] = data
                    case1["success"] = response.status_code == 200 and "code" in data
                    print(f"  状态码: {response.status_code}")
                    print(f"  响应时间: {elapsed*1000:.2f}ms")
                    print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                except json.JSONDecodeError:
                    case1["error"] = "响应不是有效的JSON格式"
                    print(f"  错误: {case1['error']}")
            else:
                print(f"  错误: {error}")
            test_cases.append(case1)
        else:
            print("\n[测试用例1] 获取扫描结果 - 使用task_id=1")
            response, elapsed, error = self.make_request("GET", "/tasks/1/results")
            case1 = {
                "name": "获取扫描结果(task_id=1)",
                "params": {"task_id": 1},
                "status_code": response.status_code if response else None,
                "response_time_ms": round(elapsed * 1000, 2),
                "success": response.status_code in [200, 404] if response else False,
                "response_data": None,
                "error": error
            }
            if response:
                try:
                    data = response.json()
                    case1["response_data"] = data
                    print(f"  状态码: {response.status_code}")
                    print(f"  响应时间: {elapsed*1000:.2f}ms")
                    print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                except json.JSONDecodeError:
                    case1["error"] = "响应不是有效的JSON格式"
                    print(f"  错误: {case1['error']}")
            else:
                print(f"  错误: {error}")
            test_cases.append(case1)

        print("\n[测试用例2] 获取不存在任务的扫描结果")
        fake_task_id = 999999
        response, elapsed, error = self.make_request("GET", f"/tasks/{fake_task_id}/results")
        case2 = {
            "name": "获取不存在任务的扫描结果",
            "params": {"task_id": fake_task_id},
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": response.status_code == 404 if response else False,
            "response_data": None,
            "error": error
        }
        if response:
            try:
                data = response.json()
                case2["response_data"] = data
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                case2["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case2['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case2)

        result.test_cases = test_cases
        result.success = any(case["success"] for case in test_cases)
        result.response_time = sum(case["response_time_ms"] for case in test_cases) / len(test_cases)
        result.status_code = test_cases[0]["status_code"]
        return result

    def test_poc_verify(self) -> TestResult:
        result = TestResult("POC验证接口", "/poc/verification/tasks", "POST")
        print("\n" + "="*60)
        print("测试接口: POST /api/poc/verification/tasks")
        print("="*60)

        test_cases = []

        print("\n[测试用例1] 正常验证POC")
        verify_data = {
            "poc_id": "weblogic_cve_2020_2551",
            "target": "http://example.com",
            "priority": 5
        }
        response, elapsed, error = self.make_request("POST", "/poc/verification/tasks", json_data=verify_data)
        case1 = {
            "name": "正常验证POC",
            "params": verify_data,
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": False,
            "response_data": None,
            "error": error
        }
        if response:
            try:
                data = response.json()
                case1["response_data"] = data
                case1["success"] = response.status_code in [200, 201] and "code" in data
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                case1["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case1['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case1)

        print("\n[测试用例2] 空参数验证POC")
        response, elapsed, error = self.make_request("POST", "/poc/verification/tasks", json_data={})
        case2 = {
            "name": "空参数验证POC",
            "params": {},
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": response.status_code in [400, 422] if response else False,
            "response_data": None,
            "error": error
        }
        if response:
            try:
                data = response.json()
                case2["response_data"] = data
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                case2["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case2['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case2)

        print("\n[测试用例3] 缺少必填字段验证")
        invalid_data = {
            "priority": 5
        }
        response, elapsed, error = self.make_request("POST", "/poc/verification/tasks", json_data=invalid_data)
        case3 = {
            "name": "缺少必填字段验证",
            "params": invalid_data,
            "status_code": response.status_code if response else None,
            "response_time_ms": round(elapsed * 1000, 2),
            "success": response.status_code in [400, 422] if response else False,
            "response_data": None,
            "error": error
        }
        if response:
            try:
                data = response.json()
                case3["response_data"] = data
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {elapsed*1000:.2f}ms")
                print(f"  响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                case3["error"] = "响应不是有效的JSON格式"
                print(f"  错误: {case3['error']}")
        else:
            print(f"  错误: {error}")
        test_cases.append(case3)

        result.test_cases = test_cases
        result.success = case1["success"]
        result.response_time = sum(case["response_time_ms"] for case in test_cases) / len(test_cases)
        result.status_code = test_cases[0]["status_code"]
        return result

    def run_all_tests(self):
        print("\n" + "#"*60)
        print("# POC扫描后端API接口测试")
        print(f"# 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"# 目标地址: {self.base_url}")
        print("#"*60)

        result1 = self.test_poc_types()
        self.results.append(result1)

        result2 = self.test_poc_scan_create()
        self.results.append(result2)

        task_id = result2.response_data.get("task_id") if result2.response_data else None
        result3 = self.test_task_status(task_id)
        self.results.append(result3)

        result4 = self.test_task_results(task_id)
        self.results.append(result4)

        result5 = self.test_poc_verify()
        self.results.append(result5)

        return self.generate_report()

    def generate_report(self) -> Dict:
        print("\n" + "#"*60)
        print("# 测试报告摘要")
        print("#"*60)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests

        avg_response_time = sum(r.response_time for r in self.results) / total_tests if total_tests > 0 else 0

        print(f"\n总体统计:")
        print(f"  测试接口总数: {total_tests}")
        print(f"  通过: {passed_tests}")
        print(f"  失败: {failed_tests}")
        print(f"  通过率: {passed_tests/total_tests*100:.1f}%")
        print(f"  平均响应时间: {avg_response_time:.2f}ms")

        print(f"\n各接口测试结果:")
        for r in self.results:
            status = "✓ 通过" if r.success else "✗ 失败"
            print(f"  [{status}] {r.name} ({r.method} {r.endpoint})")
            print(f"         平均响应时间: {r.response_time:.2f}ms")

        report = {
            "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "base_url": self.base_url,
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": f"{passed_tests/total_tests*100:.1f}%",
                "avg_response_time_ms": round(avg_response_time, 2)
            },
            "details": [r.to_dict() for r in self.results]
        }

        return report


def main():
    tester = POCApiTester(BASE_URL)
    report = tester.run_all_tests()
    
    report_file = "poc_api_test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n详细测试报告已保存至: {report_file}")

    return report


if __name__ == "__main__":
    main()

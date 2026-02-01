"""
WebScan AI Security Platform - 全面API测试套件

测试所有后端API接口的功能正确性，包括：
- 扫描功能
- 任务管理
- 报告管理
- AWVS扫描
- POC扫描
- 知识库
- AI对话
- 系统设置
- 用户管理
- 通知管理
- POC生成
- Agent任务
- POC验证
- POC文件管理
- Seebug Agent
- AI Agents
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
import logging

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

from backend.config import settings
from backend.models import Task, Vulnerability, Report, VulnerabilityKB, POCScanResult, AgentTask, AgentResult, AIChatInstance

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APITestResult:
    """测试结果类"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.success = False
        self.message = ""
        self.response_time = 0
        self.response_data = None
        self.error = None

    def to_dict(self) -> Dict:
        return {
            "test_name": self.test_name,
            "success": self.success,
            "message": self.message,
            "response_time_ms": self.response_time,
            "response_data": self.response_data,
            "error": str(self.error) if self.error else None
        }


class APITestSuite:
    """API测试套件"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or f"http://{settings.HOST}:{settings.PORT}"
        self.results: List[APITestResult] = []
        self.test_data: Dict[str, Any] = {}

    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        if level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
        elif level == "SUCCESS":
            logger.info(f"✅ {message}")
        elif level == "FAIL":
            logger.error(f"❌ {message}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Optional[Dict]:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            start_time = time.time()
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, params=params, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, params=params, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, params=params, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response_time = (time.time() - start_time) * 1000
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return {
                "status_code": response.status_code,
                "response_time": response_time,
                "data": response_data,
                "text": response.text
            }
        except requests.exceptions.ConnectionError:
            self.log(f"连接失败: {url}", "ERROR")
            return None
        except requests.exceptions.Timeout:
            self.log(f"请求超时: {url}", "ERROR")
            return None
        except Exception as e:
            self.log(f"请求异常: {str(e)}", "ERROR")
            return None

    def run_test(self, test_name: str, test_func) -> APITestResult:
        """运行单个测试"""
        result = APITestResult(test_name)
        self.log(f"\n{'='*60}", "INFO")
        self.log(f"测试: {test_name}", "INFO")
        self.log(f"{'='*60}", "INFO")
        
        try:
            start_time = time.time()
            test_func(result)
            result.response_time = (time.time() - start_time) * 1000
            if result.success:
                self.log(f"✅ 测试通过: {test_name}", "SUCCESS")
            else:
                self.log(f"❌ 测试失败: {test_name} - {result.message}", "FAIL")
        except Exception as e:
            result.success = False
            result.error = e
            result.message = f"测试异常: {str(e)}"
            self.log(f"❌ 测试异常: {test_name} - {str(e)}", "FAIL")
        
        self.results.append(result)
        return result

    def print_summary(self):
        """打印测试摘要"""
        self.log(f"\n{'='*80}", "INFO")
        self.log(f"测试摘要", "INFO")
        self.log(f"{'='*80}", "INFO")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        
        self.log(f"总测试数: {total}", "INFO")
        self.log(f"通过: {passed}", "SUCCESS" if passed > 0 else "INFO")
        self.log(f"失败: {failed}", "FAIL" if failed > 0 else "INFO")
        self.log(f"通过率: {(passed/total*100):.2f}%", "INFO")
        
        if failed > 0:
            self.log(f"\n失败的测试:", "FAIL")
            for result in self.results:
                if not result.success:
                    self.log(f"  - {result.test_name}: {result.message}", "FAIL")
        
        self.log(f"\n详细测试结果:", "INFO")
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            self.log(f"  {status} | {result.test_name} | {result.response_time:.2f}ms", "INFO")

    def save_results(self, filename: str = "test_results.json"):
        """保存测试结果到文件"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if r.success is False),
            "results": [r.to_dict() for r in self.results]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        self.log(f"测试结果已保存到: {filename}", "INFO")


async def init_database():
    """初始化数据库连接"""
    from tortoise import Tortoise
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["models"]}
    )
    await Tortoise.generate_schemas()
    logger.info("数据库初始化成功")


async def close_database():
    """关闭数据库连接"""
    from tortoise import Tortoise
    await Tortoise.close_connections()


class TestScanAPI(APITestSuite):
    """测试扫描功能API"""

    def test_root_endpoint(self, result: APITestResult):
        """测试根端点"""
        response = self.make_request("GET", "/")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "根端点访问成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"根端点访问失败: {response}"

    def test_health_check(self, result: APITestResult):
        """测试健康检查"""
        response = self.make_request("GET", "/health")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "健康检查通过"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"健康检查失败: {response}"

    def test_port_scan(self, result: APITestResult):
        """测试端口扫描"""
        data = {
            "ip": "127.0.0.1",
            "ports": "1-100"
        }
        response = self.make_request("POST", "/api/scan/port-scan", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "端口扫描任务创建成功"
            result.response_data = response["data"]
            self.test_data["port_scan_task_id"] = response["data"].get("data", {}).get("task_id")
        else:
            result.success = False
            result.message = f"端口扫描失败: {response}"

    def test_info_leak(self, result: APITestResult):
        """测试信息泄露检测"""
        data = {
            "url": "https://www.baidu.com"
        }
        response = self.make_request("POST", "/api/scan/info-leak", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "信息泄露检测任务创建成功"
            result.response_data = response["data"]
            self.test_data["info_leak_task_id"] = response["data"].get("data", {}).get("task_id")
        else:
            result.success = False
            result.message = f"信息泄露检测失败: {response}"

    def test_web_side_scan(self, result: APITestResult):
        """测试旁站扫描"""
        data = {
            "ip": "127.0.0.1"
        }
        response = self.make_request("POST", "/api/scan/web-side", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "旁站扫描任务创建成功"
            result.response_data = response["data"]
            self.test_data["web_side_task_id"] = response["data"].get("data", {}).get("task_id")
        else:
            result.success = False
            result.message = f"旁站扫描失败: {response}"

    def test_baseinfo_scan(self, result: APITestResult):
        """测试网站基本信息获取"""
        data = {
            "url": "https://www.baidu.com"
        }
        response = self.make_request("POST", "/api/scan/baseinfo", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "网站基本信息获取任务创建成功"
            result.response_data = response["data"]
            self.test_data["baseinfo_task_id"] = response["data"].get("data", {}).get("task_id")
        else:
            result.success = False
            result.message = f"网站基本信息获取失败: {response}"

    def test_subdomain_scan(self, result: APITestResult):
        """测试子域名扫描"""
        data = {
            "domain": "baidu.com",
            "deep_scan": False
        }
        response = self.make_request("POST", "/api/scan/subdomain", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "子域名扫描任务创建成功"
            result.response_data = response["data"]
            self.test_data["subdomain_task_id"] = response["data"].get("data", {}).get("task_id")
        else:
            result.success = False
            result.message = f"子域名扫描失败: {response}"

    def test_dir_scan(self, result: APITestResult):
        """测试目录扫描"""
        data = {
            "url": "https://www.baidu.com"
        }
        response = self.make_request("POST", "/api/scan/dir-scan", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "目录扫描任务创建成功"
            result.response_data = response["data"]
            self.test_data["dir_scan_task_id"] = response["data"].get("data", {}).get("task_id")
        else:
            result.success = False
            result.message = f"目录扫描失败: {response}"

    def test_comprehensive_scan(self, result: APITestResult):
        """测试综合扫描"""
        data = {
            "url": "https://www.baidu.com"
        }
        response = self.make_request("POST", "/api/scan/comprehensive", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "综合扫描任务创建成功"
            result.response_data = response["data"]
            self.test_data["comprehensive_task_id"] = response["data"].get("data", {}).get("task_id")
        else:
            result.success = False
            result.message = f"综合扫描失败: {response}"

    def run_all_tests(self):
        """运行所有扫描API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试扫描功能API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("根端点", self.test_root_endpoint)
        self.run_test("健康检查", self.test_health_check)
        self.run_test("端口扫描", self.test_port_scan)
        self.run_test("信息泄露检测", self.test_info_leak)
        self.run_test("旁站扫描", self.test_web_side_scan)
        self.run_test("网站基本信息获取", self.test_baseinfo_scan)
        self.run_test("子域名扫描", self.test_subdomain_scan)
        self.run_test("目录扫描", self.test_dir_scan)
        self.run_test("综合扫描", self.test_comprehensive_scan)


class TestTasksAPI(APITestSuite):
    """测试任务管理API"""

    def test_create_task(self, result: APITestResult):
        """测试创建任务"""
        data = {
            "task_name": "测试任务-API测试",
            "target": "https://test.example.com",
            "task_type": "scan_comprehensive",
            "config": {"test": True}
        }
        response = self.make_request("POST", "/api/tasks/create", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "任务创建成功"
            result.response_data = response["data"]
            self.test_data["test_task_id"] = response["data"].get("data", {}).get("task_id")
        else:
            result.success = False
            result.message = f"任务创建失败: {response}"

    def test_list_tasks(self, result: APITestResult):
        """测试获取任务列表"""
        response = self.make_request("GET", "/api/tasks/")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取任务列表成功"
            result.response_data = response["data"]
            self.test_data["tasks_count"] = len(response["data"].get("data", {}).get("tasks", []))
        else:
            result.success = False
            result.message = f"获取任务列表失败: {response}"

    def test_get_task(self, result: APITestResult):
        """测试获取任务详情"""
        task_id = self.test_data.get("test_task_id")
        if not task_id:
            result.success = False
            result.message = "没有可用的任务ID"
            return
        
        response = self.make_request("GET", f"/api/tasks/{task_id}")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取任务详情成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取任务详情失败: {response}"

    def test_update_task(self, result: APITestResult):
        """测试更新任务"""
        task_id = self.test_data.get("test_task_id")
        if not task_id:
            result.success = False
            result.message = "没有可用的任务ID"
            return
        
        data = {
            "status": "completed",
            "progress": 100
        }
        response = self.make_request("PUT", f"/api/tasks/{task_id}", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "更新任务成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"更新任务失败: {response}"

    def test_get_task_results(self, result: APITestResult):
        """测试获取任务结果"""
        task_id = self.test_data.get("test_task_id")
        if not task_id:
            result.success = False
            result.message = "没有可用的任务ID"
            return
        
        response = self.make_request("GET", f"/api/tasks/{task_id}/results")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取任务结果成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取任务结果失败: {response}"

    def run_all_tests(self):
        """运行所有任务管理API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试任务管理API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("创建任务", self.test_create_task)
        self.run_test("获取任务列表", self.test_list_tasks)
        self.run_test("获取任务详情", self.test_get_task)
        self.run_test("更新任务", self.test_update_task)
        self.run_test("获取任务结果", self.test_get_task_results)


class TestReportsAPI(APITestSuite):
    """测试报告管理API"""

    def test_list_reports(self, result: APITestResult):
        """测试获取报告列表"""
        response = self.make_request("GET", "/api/reports/")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取报告列表成功"
            result.response_data = response["data"]
            self.test_data["reports_count"] = len(response["data"].get("data", {}).get("reports", []))
        else:
            result.success = False
            result.message = f"获取报告列表失败: {response}"

    def test_create_report(self, result: APITestResult):
        """测试创建报告"""
        data = {
            "task_id": 1,
            "name": "测试报告-API测试",
            "format": "json",
            "content": []
        }
        response = self.make_request("POST", "/api/reports/", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "创建报告成功"
            result.response_data = response["data"]
            self.test_data["test_report_id"] = response["data"].get("data", {}).get("id")
        else:
            result.success = False
            result.message = f"创建报告失败: {response}"

    def test_get_report(self, result: APITestResult):
        """测试获取报告详情"""
        report_id = self.test_data.get("test_report_id")
        if not report_id:
            result.success = False
            result.message = "没有可用的报告ID"
            return
        
        response = self.make_request("GET", f"/api/reports/{report_id}")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取报告详情成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取报告详情失败: {response}"

    def run_all_tests(self):
        """运行所有报告管理API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试报告管理API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("获取报告列表", self.test_list_reports)
        self.run_test("创建报告", self.test_create_report)
        self.run_test("获取报告详情", self.test_get_report)


class TestAWVSAPI(APITestSuite):
    """测试AWVS扫描API"""

    def test_get_awvs_scans(self, result: APITestResult):
        """测试获取AWVS扫描列表"""
        response = self.make_request("GET", "/api/awvs/scans")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取AWVS扫描列表成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取AWVS扫描列表失败: {response}"

    def test_create_awvs_scan(self, result: APITestResult):
        """测试创建AWVS扫描"""
        data = {
            "url": "https://www.baidu.com",
            "scan_type": "full_scan"
        }
        response = self.make_request("POST", "/api/awvs/scan", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "创建AWVS扫描成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"创建AWVS扫描失败: {response}"

    def test_get_vulnerability_rank(self, result: APITestResult):
        """测试获取漏洞排名"""
        response = self.make_request("GET", "/api/awvs/vulnerabilities/rank")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取漏洞排名成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取漏洞排名失败: {response}"

    def test_get_vulnerability_stats(self, result: APITestResult):
        """测试获取漏洞统计"""
        response = self.make_request("GET", "/api/awvs/vulnerabilities/stats")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取漏洞统计成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取漏洞统计失败: {response}"

    def run_all_tests(self):
        """运行所有AWVS API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试AWVS扫描API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("获取AWVS扫描列表", self.test_get_awvs_scans)
        self.run_test("创建AWVS扫描", self.test_create_awvs_scan)
        self.run_test("获取漏洞排名", self.test_get_vulnerability_rank)
        self.run_test("获取漏洞统计", self.test_get_vulnerability_stats)


class TestPOCAPI(APITestSuite):
    """测试POC扫描API"""

    def test_get_poc_types(self, result: APITestResult):
        """测试获取POC类型"""
        response = self.make_request("GET", "/api/poc/types")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取POC类型成功"
            result.response_data = response["data"]
            self.test_data["poc_types"] = response["data"].get("data", [])
        else:
            result.success = False
            result.message = f"获取POC类型失败: {response}"

    def test_scan_poc(self, result: APITestResult):
        """测试POC扫描"""
        data = {
            "target": "https://www.baidu.com",
            "poc_types": ["struts2_009"],
            "timeout": 10
        }
        response = self.make_request("POST", "/api/poc/scan", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "POC扫描任务创建成功"
            result.response_data = response["data"]
            self.test_data["poc_scan_task_id"] = response["data"].get("data", {}).get("task_id")
        else:
            result.success = False
            result.message = f"POC扫描失败: {response}"

    def test_get_poc_info(self, result: APITestResult):
        """测试获取POC信息"""
        response = self.make_request("GET", "/api/poc/info/struts2_009")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取POC信息成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取POC信息失败: {response}"

    def run_all_tests(self):
        """运行所有POC API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试POC扫描API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("获取POC类型", self.test_get_poc_types)
        self.run_test("POC扫描", self.test_scan_poc)
        self.run_test("获取POC信息", self.test_get_poc_info)


class TestKBAPI(APITestSuite):
    """测试知识库API"""

    def test_list_kb_vulnerabilities(self, result: APITestResult):
        """测试获取知识库漏洞列表"""
        response = self.make_request("GET", "/api/kb/vulnerabilities?page=1&page_size=10")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取知识库漏洞列表成功"
            result.response_data = response["data"]
            self.test_data["kb_count"] = response["data"].get("data", {}).get("total", 0)
        else:
            result.success = False
            result.message = f"获取知识库漏洞列表失败: {response}"

    def test_get_kb_vulnerability(self, result: APITestResult):
        """测试获取知识库漏洞详情"""
        response = self.make_request("GET", "/api/kb/vulnerabilities/1")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取知识库漏洞详情成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取知识库漏洞详情失败: {response}"

    def test_sync_kb(self, result: APITestResult):
        """测试同步知识库"""
        response = self.make_request("POST", "/api/kb/sync")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "同步知识库任务启动成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"同步知识库失败: {response}"

    def run_all_tests(self):
        """运行所有知识库API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试知识库API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("获取知识库漏洞列表", self.test_list_kb_vulnerabilities)
        self.run_test("获取知识库漏洞详情", self.test_get_kb_vulnerability)
        self.run_test("同步知识库", self.test_sync_kb)


class TestAIAPI(APITestSuite):
    """测试AI对话API"""

    def test_create_chat_instance(self, result: APITestResult):
        """测试创建AI对话实例"""
        params = {
            "chat_name": "测试对话-API测试",
            "chat_type": "general",
            "user_id": "test_user"
        }
        response = self.make_request("POST", "/api/ai/chat/instances", params=params)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "创建AI对话实例成功"
            result.response_data = response["data"]
            self.test_data["chat_instance_id"] = response["data"].get("data", {}).get("chat_instance_id")
        else:
            result.success = False
            result.message = f"创建AI对话实例失败: {response}"

    def test_list_chat_instances(self, result: APITestResult):
        """测试获取AI对话实例列表"""
        response = self.make_request("GET", "/api/ai/chat/instances")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取AI对话实例列表成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取AI对话实例列表失败: {response}"

    def test_send_message(self, result: APITestResult):
        """测试发送消息"""
        chat_id = self.test_data.get("chat_instance_id")
        if not chat_id:
            result.success = False
            result.message = "没有可用的对话实例ID"
            return
        
        data = {
            "content": "你好，请介绍一下SQL注入漏洞",
            "message_type": "text"
        }
        response = self.make_request("POST", f"/api/ai/chat/instances/{chat_id}/messages", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "发送消息成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"发送消息失败: {response}"

    def run_all_tests(self):
        """运行所有AI对话API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试AI对话API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("创建AI对话实例", self.test_create_chat_instance)
        self.run_test("获取AI对话实例列表", self.test_list_chat_instances)
        self.run_test("发送消息", self.test_send_message)


class TestSettingsAPI(APITestSuite):
    """测试系统设置API"""

    def test_get_settings(self, result: APITestResult):
        """测试获取系统设置"""
        response = self.make_request("GET", "/api/settings/")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取系统设置成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取系统设置失败: {response}"

    def test_get_system_info(self, result: APITestResult):
        """测试获取系统信息"""
        response = self.make_request("GET", "/api/settings/system-info")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取系统信息成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取系统信息失败: {response}"

    def test_get_statistics(self, result: APITestResult):
        """测试获取统计信息"""
        response = self.make_request("GET", "/api/settings/statistics?period=7")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取统计信息成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取统计信息失败: {response}"

    def run_all_tests(self):
        """运行所有系统设置API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试系统设置API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("获取系统设置", self.test_get_settings)
        self.run_test("获取系统信息", self.test_get_system_info)
        self.run_test("获取统计信息", self.test_get_statistics)


class TestUserAPI(APITestSuite):
    """测试用户管理API"""

    def test_get_user_profile(self, result: APITestResult):
        """测试获取用户信息"""
        response = self.make_request("GET", "/api/user/profile?user_id=1")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取用户信息成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取用户信息失败: {response}"

    def test_get_user_permissions(self, result: APITestResult):
        """测试获取用户权限"""
        response = self.make_request("GET", "/api/user/permissions?user_id=1")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取用户权限成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取用户权限失败: {response}"

    def test_get_user_list(self, result: APITestResult):
        """测试获取用户列表"""
        response = self.make_request("GET", "/api/user/list")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取用户列表成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取用户列表失败: {response}"

    def run_all_tests(self):
        """运行所有用户管理API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试用户管理API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("获取用户信息", self.test_get_user_profile)
        self.run_test("获取用户权限", self.test_get_user_permissions)
        self.run_test("获取用户列表", self.test_get_user_list)


class TestNotificationsAPI(APITestSuite):
    """测试通知管理API"""

    def test_get_notifications(self, result: APITestResult):
        """测试获取通知列表"""
        response = self.make_request("GET", "/api/notifications/")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取通知列表成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取通知列表失败: {response}"

    def test_create_notification(self, result: APITestResult):
        """测试创建通知"""
        data = {
            "title": "测试通知-API测试",
            "message": "这是一个测试通知",
            "type": "info"
        }
        response = self.make_request("POST", "/api/notifications/", data=data)
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "创建通知成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"创建通知失败: {response}"

    def test_get_unread_count(self, result: APITestResult):
        """测试获取未读通知数量"""
        response = self.make_request("GET", "/api/notifications/count/unread")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取未读通知数量成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取未读通知数量失败: {response}"

    def run_all_tests(self):
        """运行所有通知管理API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试通知管理API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("获取通知列表", self.test_get_notifications)
        self.run_test("创建通知", self.test_create_notification)
        self.run_test("获取未读通知数量", self.test_get_unread_count)


class TestAgentAPI(APITestSuite):
    """测试Agent API"""

    def test_list_agent_tasks(self, result: APITestResult):
        """测试获取Agent任务列表"""
        response = self.make_request("GET", "/api/agent/tasks")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取Agent任务列表成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取Agent任务列表失败: {response}"

    def run_all_tests(self):
        """运行所有Agent API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试Agent API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("获取Agent任务列表", self.test_list_agent_tasks)


class TestAIAgentsAPI(APITestSuite):
    """测试AI Agents API"""

    def test_list_ai_agents_tasks(self, result: APITestResult):
        """测试获取AI Agents任务列表"""
        response = self.make_request("GET", "/api/ai_agents/tasks")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取AI Agents任务列表成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取AI Agents任务列表失败: {response}"

    def test_get_ai_agents_tools(self, result: APITestResult):
        """测试获取AI Agents工具列表"""
        response = self.make_request("GET", "/api/ai_agents/tools")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取AI Agents工具列表成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取AI Agents工具列表失败: {response}"

    def test_get_ai_agents_config(self, result: APITestResult):
        """测试获取AI Agents配置"""
        response = self.make_request("GET", "/api/ai_agents/config")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取AI Agents配置成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取AI Agents配置失败: {response}"

    def run_all_tests(self):
        """运行所有AI Agents API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试AI Agents API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("获取AI Agents任务列表", self.test_list_ai_agents_tasks)
        self.run_test("获取AI Agents工具列表", self.test_get_ai_agents_tools)
        self.run_test("获取AI Agents配置", self.test_get_ai_agents_config)


class TestSeebugAgentAPI(APITestSuite):
    """测试Seebug Agent API"""

    def test_get_seebug_status(self, result: APITestResult):
        """测试获取Seebug Agent状态"""
        response = self.make_request("GET", "/api/seebug/status")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "获取Seebug Agent状态成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"获取Seebug Agent状态失败: {response}"

    def test_test_seebug_connection(self, result: APITestResult):
        """测试Seebug连接"""
        response = self.make_request("GET", "/api/seebug/test-connection")
        if response and response["status_code"] == 200:
            result.success = True
            result.message = "测试Seebug连接成功"
            result.response_data = response["data"]
        else:
            result.success = False
            result.message = f"测试Seebug连接失败: {response}"

    def run_all_tests(self):
        """运行所有Seebug Agent API测试"""
        self.log("\n" + "="*80, "INFO")
        self.log("开始测试Seebug Agent API", "INFO")
        self.log("="*80, "INFO")
        
        self.run_test("获取Seebug Agent状态", self.test_get_seebug_status)
        self.run_test("测试Seebug连接", self.test_test_seebug_connection)


async def run_all_tests():
    """运行所有测试套件"""
    logger.info("="*80)
    logger.info("WebScan AI Security Platform - 全面API测试")
    logger.info("="*80)
    logger.info(f"测试目标: {settings.HOST}:{settings.PORT}")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    base_url = f"http://{settings.HOST}:{settings.PORT}"
    
    all_results = []
    
    test_suites = [
        ("扫描功能API", TestScanAPI(base_url)),
        ("任务管理API", TestTasksAPI(base_url)),
        ("报告管理API", TestReportsAPI(base_url)),
        ("AWVS扫描API", TestAWVSAPI(base_url)),
        ("POC扫描API", TestPOCAPI(base_url)),
        ("知识库API", TestKBAPI(base_url)),
        ("AI对话API", TestAIAPI(base_url)),
        ("系统设置API", TestSettingsAPI(base_url)),
        ("用户管理API", TestUserAPI(base_url)),
        ("通知管理API", TestNotificationsAPI(base_url)),
        ("Agent API", TestAgentAPI(base_url)),
        ("AI Agents API", TestAIAgentsAPI(base_url)),
        ("Seebug Agent API", TestSeebugAgentAPI(base_url))
    ]
    
    for suite_name, test_suite in test_suites:
        try:
            test_suite.run_all_tests()
            all_results.extend(test_suite.results)
        except Exception as e:
            logger.error(f"测试套件 {suite_name} 执行失败: {str(e)}")
    
    logger.info("\n" + "="*80)
    logger.info("所有测试套件执行完成")
    logger.info("="*80)
    
    total = len(all_results)
    passed = sum(1 for r in all_results if r.success)
    failed = total - passed
    
    logger.info(f"\n总测试数: {total}")
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {failed}")
    logger.info(f"通过率: {(passed/total*100):.2f}%")
    
    if failed > 0:
        logger.info(f"\n失败的测试:")
        for result in all_results:
            if not result.success:
                logger.info(f"  - {result.test_name}: {result.message}")
    
    results_file = "test_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed/total*100):.2f}%",
            "results": [r.to_dict() for r in all_results]
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n测试结果已保存到: {results_file}")
    
    return passed, failed, total


if __name__ == "__main__":
    asyncio.run(run_all_tests())

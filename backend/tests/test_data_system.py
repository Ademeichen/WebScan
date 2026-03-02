"""
测试数据体系构建

包含:
1. 正常用例 - 标准扫描场景
2. 边界用例 - 极限条件测试
3. 异常用例 - 错误处理测试
4. 日志系统 - 完整的测试日志记录
"""
import asyncio
import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCaseType(Enum):
    NORMAL = "normal"
    BOUNDARY = "boundary"
    EXCEPTION = "exception"


class TestCasePriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TestCase:
    id: str
    name: str
    description: str
    test_type: TestCaseType
    priority: TestCasePriority
    target: str
    expected_status: str = "success"
    expected_min_tasks: int = 0
    expected_max_time: int = 300
    tags: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "test_type": self.test_type.value,
            "priority": self.priority.value,
            "target": self.target,
            "expected_status": self.expected_status,
            "expected_min_tasks": self.expected_min_tasks,
            "expected_max_time": self.expected_max_time,
            "tags": self.tags,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions
        }


@dataclass
class TestResult:
    test_id: str
    test_name: str
    test_type: str
    status: str
    start_time: str
    end_time: str
    execution_time: float
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TestLogger:
    """
    测试日志系统
    """
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path(__file__).parent / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"test_run_{self.timestamp}.log"
        self.json_log_file = self.log_dir / f"test_run_{self.timestamp}.json"
        
        self.logger = logging.getLogger("TestDataSystem")
        self.logger.setLevel(logging.DEBUG)
        
        fh = logging.FileHandler(self.log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        self.test_results: List[TestResult] = []
    
    def log_test_start(self, test_case: TestCase):
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"开始测试: {test_case.name}")
        self.logger.info(f"测试ID: {test_case.id}")
        self.logger.info(f"测试类型: {test_case.test_type.value}")
        self.logger.info(f"优先级: {test_case.priority.value}")
        self.logger.info(f"目标: {test_case.target}")
        self.logger.info(f"{'='*60}")
    
    def log_test_result(self, result: TestResult):
        status_icon = "✅" if result.passed else "❌"
        self.logger.info(f"{status_icon} 测试完成: {result.test_name}")
        self.logger.info(f"   状态: {result.status}")
        self.logger.info(f"   执行时间: {result.execution_time:.2f}秒")
        self.logger.info(f"   结果: {result.message}")
        
        if result.errors:
            for error in result.errors:
                self.logger.error(f"   错误: {error}")
        
        self.test_results.append(result)
    
    def log_summary(self, summary: Dict[str, Any]):
        self.logger.info(f"\n{'='*60}")
        self.logger.info("测试汇总报告")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"总测试数: {summary['total']}")
        self.logger.info(f"通过: {summary['passed']}")
        self.logger.info(f"失败: {summary['failed']}")
        self.logger.info(f"通过率: {summary['pass_rate']:.1f}%")
        self.logger.info(f"总执行时间: {summary['total_time']:.2f}秒")
        
        self.logger.info(f"\n按类型统计:")
        for type_name, stats in summary['by_type'].items():
            self.logger.info(f"  {type_name}: {stats['passed']}/{stats['total']} 通过")
    
    def save_results(self):
        results_data = {
            "timestamp": self.timestamp,
            "summary": {
                "total": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r.passed),
                "failed": sum(1 for r in self.test_results if not r.passed)
            },
            "results": [r.to_dict() for r in self.test_results]
        }
        
        with open(self.json_log_file, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"\n📄 测试结果已保存: {self.json_log_file}")


class TestDataBuilder:
    """
    测试数据构建器
    """
    
    @staticmethod
    def build_normal_test_cases() -> List[TestCase]:
        """
        构建正常用例
        
        标准扫描场景，验证基本功能
        """
        return [
            TestCase(
                id="NORMAL_001",
                name="HTTP网站基础扫描",
                description="对标准HTTP网站进行完整扫描流程",
                test_type=TestCaseType.NORMAL,
                priority=TestCasePriority.HIGH,
                target="http://example.com",
                expected_status="success",
                expected_min_tasks=3,
                expected_max_time=120,
                tags=["http", "basic", "scan"],
                preconditions=["网络连接正常", "目标可访问"],
                postconditions=["生成扫描报告", "漏洞列表完整"]
            ),
            TestCase(
                id="NORMAL_002",
                name="HTTPS网站安全扫描",
                description="对HTTPS网站进行安全扫描",
                test_type=TestCaseType.NORMAL,
                priority=TestCasePriority.HIGH,
                target="https://www.baidu.com",
                expected_status="success",
                expected_min_tasks=3,
                expected_max_time=180,
                tags=["https", "ssl", "scan"],
                preconditions=["SSL证书有效", "网络连接正常"],
                postconditions=["SSL检测完成", "漏洞扫描完成"]
            ),
            TestCase(
                id="NORMAL_003",
                name="域名信息收集",
                description="对域名进行信息收集扫描",
                test_type=TestCaseType.NORMAL,
                priority=TestCasePriority.MEDIUM,
                target="www.qq.com",
                expected_status="success",
                expected_min_tasks=2,
                expected_max_time=60,
                tags=["domain", "info", "reconnaissance"],
                preconditions=["域名有效", "DNS解析正常"],
                postconditions=["域名信息收集完成"]
            ),
            TestCase(
                id="NORMAL_004",
                name="IP地址端口扫描",
                description="对IP地址进行端口扫描",
                test_type=TestCaseType.NORMAL,
                priority=TestCasePriority.MEDIUM,
                target="127.0.0.1",
                expected_status="success",
                expected_min_tasks=1,
                expected_max_time=60,
                tags=["ip", "port", "scan"],
                preconditions=["IP可达"],
                postconditions=["端口列表生成"]
            ),
            TestCase(
                id="NORMAL_005",
                name="完整漏洞扫描流程",
                description="执行完整的漏洞扫描流程",
                test_type=TestCaseType.NORMAL,
                priority=TestCasePriority.HIGH,
                target="https://www.sina.com.cn",
                expected_status="success",
                expected_min_tasks=4,
                expected_max_time=300,
                tags=["full", "vulnerability", "scan"],
                preconditions=["目标可访问", "AI模型连接正常"],
                postconditions=["完整报告生成"]
            )
        ]
    
    @staticmethod
    def build_boundary_test_cases() -> List[TestCase]:
        """
        构建边界用例
        
        极限条件测试，验证系统稳定性
        """
        return [
            TestCase(
                id="BOUNDARY_001",
                name="超长URL处理",
                description="测试超长URL的处理能力",
                test_type=TestCaseType.BOUNDARY,
                priority=TestCasePriority.MEDIUM,
                target="https://example.com/" + "a" * 2000,
                expected_status="success",
                expected_min_tasks=0,
                expected_max_time=60,
                tags=["url", "length", "boundary"],
                preconditions=["URL长度限制检查"],
                postconditions=["正确处理或拒绝"]
            ),
            TestCase(
                id="BOUNDARY_002",
                name="特殊字符URL",
                description="测试包含特殊字符的URL",
                test_type=TestCaseType.BOUNDARY,
                priority=TestCasePriority.MEDIUM,
                target="https://example.com/path?query=<script>alert(1)</script>",
                expected_status="success",
                expected_min_tasks=0,
                expected_max_time=60,
                tags=["special", "character", "xss"],
                preconditions=["特殊字符编码处理"],
                postconditions=["安全处理特殊字符"]
            ),
            TestCase(
                id="BOUNDARY_003",
                name="非标准端口扫描",
                description="测试非标准端口的扫描",
                test_type=TestCaseType.BOUNDARY,
                priority=TestCasePriority.LOW,
                target="https://example.com:8443",
                expected_status="success",
                expected_min_tasks=1,
                expected_max_time=60,
                tags=["port", "non-standard", "scan"],
                preconditions=["端口可达"],
                postconditions=["端口扫描完成"]
            ),
            TestCase(
                id="BOUNDARY_004",
                name="IPv6地址处理",
                description="测试IPv6地址的处理",
                test_type=TestCaseType.BOUNDARY,
                priority=TestCasePriority.LOW,
                target="http://[::1]",
                expected_status="success",
                expected_min_tasks=0,
                expected_max_time=60,
                tags=["ipv6", "address", "boundary"],
                preconditions=["IPv6支持"],
                postconditions=["正确处理IPv6"]
            ),
            TestCase(
                id="BOUNDARY_005",
                name="并发扫描压力测试",
                description="测试系统并发处理能力",
                test_type=TestCaseType.BOUNDARY,
                priority=TestCasePriority.HIGH,
                target="https://www.baidu.com",
                expected_status="success",
                expected_min_tasks=3,
                expected_max_time=180,
                tags=["concurrent", "stress", "performance"],
                preconditions=["系统资源充足"],
                postconditions=["并发处理正常"]
            )
        ]
    
    @staticmethod
    def build_exception_test_cases() -> List[TestCase]:
        """
        构建异常用例
        
        错误处理测试，验证系统健壮性
        """
        return [
            TestCase(
                id="EXCEPTION_001",
                name="无效URL格式",
                description="测试无效URL格式的错误处理",
                test_type=TestCaseType.EXCEPTION,
                priority=TestCasePriority.HIGH,
                target="invalid-url-format",
                expected_status="failed",
                expected_min_tasks=0,
                expected_max_time=30,
                tags=["invalid", "url", "error"],
                preconditions=["无"],
                postconditions=["返回错误信息"]
            ),
            TestCase(
                id="EXCEPTION_002",
                name="不可达目标",
                description="测试不可达目标的错误处理",
                test_type=TestCaseType.EXCEPTION,
                priority=TestCasePriority.HIGH,
                target="https://this-domain-does-not-exist-12345.com",
                expected_status="failed",
                expected_min_tasks=0,
                expected_max_time=60,
                tags=["unreachable", "dns", "error"],
                preconditions=["域名不存在"],
                postconditions=["返回DNS错误"]
            ),
            TestCase(
                id="EXCEPTION_003",
                name="超时处理",
                description="测试请求超时的处理",
                test_type=TestCaseType.EXCEPTION,
                priority=TestCasePriority.MEDIUM,
                target="https://10.255.255.1",
                expected_status="failed",
                expected_min_tasks=0,
                expected_max_time=120,
                tags=["timeout", "network", "error"],
                preconditions=["IP不可达"],
                postconditions=["返回超时错误"]
            ),
            TestCase(
                id="EXCEPTION_004",
                name="空目标处理",
                description="测试空目标的错误处理",
                test_type=TestCaseType.EXCEPTION,
                priority=TestCasePriority.HIGH,
                target="",
                expected_status="failed",
                expected_min_tasks=0,
                expected_max_time=10,
                tags=["empty", "validation", "error"],
                preconditions=["无"],
                postconditions=["返回验证错误"]
            ),
            TestCase(
                id="EXCEPTION_005",
                name="SQL注入目标",
                description="测试SQL注入目标的安全处理",
                test_type=TestCaseType.EXCEPTION,
                priority=TestCasePriority.MEDIUM,
                target="https://example.com?id=1' OR '1'='1",
                expected_status="success",
                expected_min_tasks=0,
                expected_max_time=60,
                tags=["sqli", "security", "sanitization"],
                preconditions=["输入过滤"],
                postconditions=["安全处理注入字符"]
            )
        ]
    
    @staticmethod
    def build_all_test_cases() -> List[TestCase]:
        """
        构建所有测试用例
        """
        normal = TestDataBuilder.build_normal_test_cases()
        boundary = TestDataBuilder.build_boundary_test_cases()
        exception = TestDataBuilder.build_exception_test_cases()
        
        return normal + boundary + exception


class TestDataSystem:
    """
    测试数据体系
    """
    
    def __init__(self):
        self.logger = TestLogger()
        self.test_cases = TestDataBuilder.build_all_test_cases()
        self.results: List[TestResult] = []
    
    async def run_test(self, test_case: TestCase) -> TestResult:
        """
        运行单个测试用例
        """
        self.logger.log_test_start(test_case)
        
        start_time = datetime.now()
        status = "running"
        passed = False
        message = ""
        details = {}
        errors = []
        
        try:
            from ai_agents.core.graph import create_agent_graph
            from ai_agents.core.state import AgentState
            
            if not test_case.target:
                raise ValueError("目标不能为空")
            
            graph = create_agent_graph()
            state = AgentState(
                target=test_case.target,
                task_id=test_case.id
            )
            
            final_state = await graph.invoke(state)
            
            completed_tasks = getattr(final_state, 'completed_tasks', [])
            vulnerabilities = getattr(final_state, 'vulnerabilities', [])
            
            details = {
                "completed_tasks": completed_tasks,
                "vulnerabilities_count": len(vulnerabilities),
                "target": test_case.target
            }
            
            if len(completed_tasks) >= test_case.expected_min_tasks:
                status = "success"
                passed = True
                message = f"测试通过，完成 {len(completed_tasks)} 个任务"
            else:
                status = "partial"
                passed = False
                message = f"部分完成，仅完成 {len(completed_tasks)} 个任务"
                
        except Exception as e:
            status = "failed"
            passed = test_case.expected_status == "failed"
            error_msg = str(e)
            errors.append(error_msg)
            
            if passed:
                message = f"预期失败，错误符合预期: {error_msg[:100]}"
            else:
                message = f"测试失败: {error_msg[:100]}"
            
            details = {"error": error_msg}
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        result = TestResult(
            test_id=test_case.id,
            test_name=test_case.name,
            test_type=test_case.test_type.value,
            status=status,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            execution_time=execution_time,
            passed=passed,
            message=message,
            details=details,
            errors=errors
        )
        
        self.logger.log_test_result(result)
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        运行所有测试用例
        """
        self.logger.logger.info("\n" + "="*60)
        self.logger.logger.info("开始运行测试数据体系")
        self.logger.logger.info(f"总测试用例: {len(self.test_cases)}")
        self.logger.logger.info("="*60)
        
        start_time = time.time()
        
        for test_case in self.test_cases:
            result = await self.run_test(test_case)
            self.results.append(result)
            await asyncio.sleep(0.5)
        
        total_time = time.time() - start_time
        
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        by_type = {}
        for result in self.results:
            if result.test_type not in by_type:
                by_type[result.test_type] = {"total": 0, "passed": 0}
            by_type[result.test_type]["total"] += 1
            if result.passed:
                by_type[result.test_type]["passed"] += 1
        
        summary = {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / len(self.results)) * 100 if self.results else 0,
            "total_time": total_time,
            "by_type": by_type
        }
        
        self.logger.log_summary(summary)
        self.logger.save_results()
        
        return {
            "summary": summary,
            "results": [r.to_dict() for r in self.results]
        }


async def main():
    """
    主函数
    """
    system = TestDataSystem()
    report = await system.run_all_tests()
    
    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}")
    print(f"通过率: {report['summary']['pass_rate']:.1f}%")
    print(f"总测试: {report['summary']['total']}")
    print(f"通过: {report['summary']['passed']}")
    print(f"失败: {report['summary']['failed']}")
    
    return report


if __name__ == "__main__":
    asyncio.run(main())

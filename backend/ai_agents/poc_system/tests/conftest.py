"""
POC系统测试配置

提供pytest fixtures和测试配置，包括：
- 模拟POC管理器
- 模拟验证引擎
- 测试数据加载
- 测试环境配置
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.ai_agents.poc_system.poc_manager import POCMetadata, POCManager
from backend.ai_agents.poc_system.verification_engine import (
    ExecutionConfig,
    ExecutionStats,
    ResourceLimits,
    VerificationEngine,
)


TEST_DATA_DIR = Path(__file__).parent / "test_data"


def load_test_data(file_path: str) -> Dict[str, Any]:
    """加载测试数据文件"""
    full_path = TEST_DATA_DIR / file_path
    if not full_path.exists():
        return {}
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


class MockPOCResult:
    """模拟POC执行结果"""
    
    def __init__(
        self,
        poc_name: str = "test_poc",
        target: str = "http://example.com",
        vulnerable: bool = False,
        message: str = "Test completed",
        output: str = "",
        error: Optional[str] = None,
        execution_time: float = 1.0
    ):
        self.poc_name = poc_name
        self.target = target
        self.vulnerable = vulnerable
        self.message = message
        self.output = output
        self.error = error
        self.execution_time = execution_time


class MockVerificationTask:
    """模拟POC验证任务"""
    
    def __init__(
        self,
        id: str = "test_task_001",
        poc_name: str = "test_poc",
        poc_id: str = "test-001",
        target: str = "http://example.com",
        status: str = "pending",
        progress: int = 0,
        timeout: int = 60,
        max_retries: int = 3
    ):
        self.id = id
        self.poc_name = poc_name
        self.poc_id = poc_id
        self.target = target
        self.status = status
        self.progress = progress
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_count = 0
        self.result = None
        self.config = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    async def save(self):
        self.updated_at = datetime.now()


class MockVerificationResult:
    """模拟POC验证结果"""
    
    def __init__(
        self,
        id: str = "result_001",
        task_id: str = "test_task_001",
        poc_name: str = "test_poc",
        poc_id: str = "test-001",
        target: str = "http://example.com",
        vulnerable: bool = False,
        message: str = "Test completed",
        output: str = "",
        error: Optional[str] = None,
        execution_time: float = 1.0,
        confidence: float = 0.8,
        severity: str = "info",
        cvss_score: float = 0.0
    ):
        self.id = id
        self.task_id = task_id
        self.poc_name = poc_name
        self.poc_id = poc_id
        self.target = target
        self.vulnerable = vulnerable
        self.message = message
        self.output = output
        self.error = error
        self.execution_time = execution_time
        self.confidence = confidence
        self.severity = severity
        self.cvss_score = cvss_score
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "task_id": self.task_id,
            "poc_name": self.poc_name,
            "poc_id": self.poc_id,
            "target": self.target,
            "vulnerable": self.vulnerable,
            "message": self.message,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "confidence": self.confidence,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "created_at": self.created_at.isoformat()
        }


class MockPocsuite3Agent:
    """模拟Pocsuite3代理"""
    
    def __init__(self):
        self.poc_registry = {}
        self._setup_mock_pocs()
    
    def _setup_mock_pocs(self):
        mock_pocs = load_test_data("poc_execution/mock_pocs.json")
        for poc in mock_pocs.get("mock_pocs", []):
            self.poc_registry[poc["poc_id"]] = poc["file_path"]
    
    async def execute_custom_poc(
        self,
        poc_code: str,
        target: str,
        **kwargs
    ) -> MockPOCResult:
        await asyncio.sleep(0.1)
        
        if "timeout" in target.lower():
            await asyncio.sleep(120)
            return MockPOCResult(
                poc_name="timeout_poc",
                target=target,
                vulnerable=False,
                message="Execution timeout",
                execution_time=120.0
            )
        
        if "error" in target.lower():
            return MockPOCResult(
                poc_name="error_poc",
                target=target,
                vulnerable=False,
                message="Execution error occurred",
                error="RuntimeError: Simulated execution error",
                execution_time=0.1
            )
        
        if "vulnerable" in target.lower():
            return MockPOCResult(
                poc_name="vulnerable_poc",
                target=target,
                vulnerable=True,
                message="Vulnerability detected",
                output="Critical vulnerability confirmed",
                execution_time=2.5
            )
        
        return MockPOCResult(
            poc_name="simple_poc",
            target=target,
            vulnerable=False,
            message="Target is accessible",
            output="HTTP 200 OK",
            execution_time=1.0
        )
    
    def search_pocs(self, keyword: str) -> List[str]:
        return ["test_poc_1", "test_poc_2", "test_poc_3"]


class MockSeebugClient:
    """模拟Seebug客户端"""
    
    def __init__(self):
        self._search_data = load_test_data("seebug/search_response.json")
        self._detail_data = load_test_data("seebug/vuln_detail_response.json")
        self._validate_data = load_test_data("seebug/api_validate_response.json")
    
    def search_poc(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        return self._search_data
    
    def download_poc(self, ssvid: int) -> Dict[str, Any]:
        return self._detail_data
    
    def validate_key(self) -> Dict[str, Any]:
        return self._validate_data


class MockSeebugAgent:
    """模拟Seebug Agent"""
    
    def __init__(self):
        self._client = MockSeebugClient()
    
    def search_vulnerabilities(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        return self._client.search_poc(keyword, page, page_size)
    
    def get_vulnerability_detail(self, ssvid: str) -> Dict[str, Any]:
        return self._client.download_poc(int(ssvid))


@pytest.fixture
def test_data_dir() -> Path:
    """测试数据目录fixture"""
    return TEST_DATA_DIR


@pytest.fixture
def mock_pocs_data() -> Dict[str, Any]:
    """模拟POC数据fixture"""
    return load_test_data("poc_execution/mock_pocs.json")


@pytest.fixture
def mock_targets_data() -> Dict[str, Any]:
    """模拟目标数据fixture"""
    return load_test_data("poc_execution/test_targets.json")


@pytest.fixture
def mock_seebug_search_response() -> Dict[str, Any]:
    """模拟Seebug搜索响应fixture"""
    return load_test_data("seebug/search_response.json")


@pytest.fixture
def mock_verification_results_data() -> Dict[str, Any]:
    """模拟验证结果数据fixture"""
    return load_test_data("reports/mock_verification_results.json")


@pytest.fixture
def mock_report_template() -> Dict[str, Any]:
    """模拟报告模板fixture"""
    return load_test_data("reports/report_template.json")


@pytest.fixture
def mock_pocsuite3_agent():
    """模拟Pocsuite3代理fixture"""
    return MockPocsuite3Agent()


@pytest.fixture
def mock_seebug_client():
    """模拟Seebug客户端fixture"""
    return MockSeebugClient()


@pytest.fixture
def mock_seebug_agent():
    """模拟Seebug Agent fixture"""
    return MockSeebugAgent()


@pytest.fixture
def mock_poc_manager(mock_seebug_client, mock_seebug_agent, mock_pocsuite3_agent):
    """模拟POC管理器fixture"""
    with patch('backend.ai_agents.poc_system.poc_manager.seebug_utils') as mock_utils:
        mock_utils.get_client.return_value = mock_seebug_client
        mock_utils.get_agent.return_value = mock_seebug_agent
        
        with patch('backend.ai_agents.poc_system.poc_manager.CacheManager'):
            with patch('backend.ai_agents.poc_system.poc_manager.get_pocsuite3_agent') as mock_get_agent:
                mock_get_agent.return_value = mock_pocsuite3_agent
                
                manager = POCManager()
                
                test_metadata = POCMetadata(
                    poc_name="Test POC",
                    poc_id="test-001",
                    poc_type="web",
                    severity="high",
                    cvss_score=7.5,
                    description="Test POC for unit testing",
                    author="test",
                    source="test",
                    version="1.0",
                    tags=["test", "unit"]
                )
                manager.poc_registry["test-001"] = test_metadata
                
                yield manager


@pytest.fixture
def mock_verification_task():
    """模拟验证任务fixture"""
    return MockVerificationTask(
        id="test_task_001",
        poc_name="Test POC",
        poc_id="test-001",
        target="http://example.com",
        status="pending",
        progress=0
    )


@pytest.fixture
def mock_verification_result():
    """模拟验证结果fixture"""
    return MockVerificationResult(
        id="result_001",
        task_id="test_task_001",
        poc_name="Test POC",
        poc_id="test-001",
        target="http://example.com",
        vulnerable=False,
        message="Test completed",
        execution_time=1.0,
        confidence=0.8,
        severity="info",
        cvss_score=0.0
    )


@pytest.fixture
def mock_vulnerable_result():
    """模拟漏洞结果fixture"""
    return MockVerificationResult(
        id="result_002",
        task_id="test_task_002",
        poc_name="Vulnerable POC",
        poc_id="test-002",
        target="http://vulnerable.example.com",
        vulnerable=True,
        message="Critical vulnerability detected",
        output="Remote code execution confirmed",
        execution_time=2.5,
        confidence=0.95,
        severity="critical",
        cvss_score=9.8
    )


@pytest.fixture
def execution_config():
    """执行配置fixture"""
    return ExecutionConfig(
        poc_id="test-001",
        target="http://example.com",
        poc_code="print('test')",
        timeout=60,
        max_retries=3,
        enable_sandbox=True,
        max_memory_mb=512,
        max_cpu_percent=80.0
    )


@pytest.fixture
def execution_stats():
    """执行统计fixture"""
    return ExecutionStats(
        total_pocs=10,
        executed_count=8,
        vulnerable_count=3,
        failed_count=2,
        total_execution_time=25.5,
        average_execution_time=3.19,
        success_rate=37.5
    )


@pytest.fixture
def resource_limits():
    """资源限制fixture"""
    return ResourceLimits(
        max_memory_mb=1024,
        max_cpu_percent=80.0,
        max_concurrent_executions=10,
        throttle_threshold_memory=0.8,
        throttle_threshold_cpu=0.8,
        pause_threshold_memory=0.95,
        pause_threshold_cpu=0.95
    )


@pytest.fixture
def mock_verification_engine(mock_pocsuite3_agent):
    """模拟验证引擎fixture"""
    with patch('backend.ai_agents.poc_system.verification_engine.Pocsuite3Agent') as mock_agent_class:
        mock_agent_class.return_value = mock_pocsuite3_agent
        
        with patch('backend.ai_agents.poc_system.verification_engine.poc_manager'):
            engine = VerificationEngine()
            yield engine


@pytest.fixture
def sample_poc_metadata():
    """样本POC元数据fixture"""
    return POCMetadata(
        poc_name="Sample POC",
        poc_id="sample-001",
        poc_type="web",
        severity="high",
        cvss_score=7.5,
        description="Sample POC for testing",
        author="test_author",
        source="test",
        version="1.0",
        tags=["test", "sample"]
    )


@pytest.fixture
def sample_poc_metadata_list():
    """样本POC元数据列表fixture"""
    return [
        POCMetadata(
            poc_name="POC 1",
            poc_id="poc-001",
            poc_type="web",
            severity="critical",
            cvss_score=9.8,
            tags=["rce", "critical"]
        ),
        POCMetadata(
            poc_name="POC 2",
            poc_id="poc-002",
            poc_type="web",
            severity="high",
            cvss_score=7.5,
            tags=["xss", "high"]
        ),
        POCMetadata(
            poc_name="POC 3",
            poc_id="poc-003",
            poc_type="network",
            severity="medium",
            cvss_score=5.5,
            tags=["sqli", "medium"]
        )
    ]


@pytest.fixture
def mock_seebug_pocs_list():
    """模拟Seebug POC列表fixture"""
    return [
        {
            "ssvid": 99617,
            "name": "thinkphp 5.x 远程代码执行漏洞",
            "type": "web",
            "severity": "critical",
            "cvss_score": 9.8,
            "description": "thinkphp 5.x 版本存在远程代码执行漏洞",
            "author": "seebug",
            "tags": ["rce", "thinkphp", "php"]
        },
        {
            "ssvid": 99618,
            "name": "Apache Log4j2 远程代码执行漏洞",
            "type": "web",
            "severity": "critical",
            "cvss_score": 10.0,
            "description": "Apache Log4j2 存在严重的远程代码执行漏洞",
            "author": "seebug",
            "tags": ["rce", "log4j", "java"]
        }
    ]


@pytest.fixture
def event_loop():
    """事件循环fixture"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "poc: mark test as POC system test"
    )
    config.addinivalue_line(
        "markers", "verification: mark test as verification test"
    )
    config.addinivalue_line(
        "markers", "seebug: mark test as Seebug integration test"
    )
    config.addinivalue_line(
        "markers", "report: mark test as report generation test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """根据标记修改测试收集"""
    skip_slow = pytest.mark.skip(reason="慢速测试，使用 --run-slow 运行")
    skip_integration = pytest.mark.skip(reason="集成测试，使用 --run-integration 运行")
    
    for item in items:
        if "slow" in item.keywords and not config.getoption("--run-slow", default=False):
            item.add_marker(skip_slow)
        if "integration" in item.keywords and not config.getoption("--run-integration", default=False):
            item.add_marker(skip_integration)

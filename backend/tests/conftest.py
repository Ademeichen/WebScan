"""
综合测试框架配置

提供统一的测试基础设施，包括：
- 超时控制和自动跳过机制
- AWVS集成测试支持
- AI服务测试支持
- 测试报告生成
- 真实外部服务配置
"""
import pytest
import asyncio
import time
import json
import logging
import sys
import os
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from backend.config import settings

logger = logging.getLogger(__name__)


def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "awvs: mark test as requiring AWVS service"
    )
    config.addinivalue_line(
        "markers", "ai: mark test as requiring AI model service"
    )
    config.addinivalue_line(
        "markers", "seebug: mark test as requiring Seebug service"
    )


def pytest_collection_modifyitems(config, items):
    """根据标记修改测试收集"""
    skip_integration = pytest.mark.skip(reason="需要外部服务，使用 --run-integration 运行")
    skip_slow = pytest.mark.skip(reason="慢速测试，使用 --run-slow 运行")
    
    for item in items:
        if "integration" in item.keywords and not config.getoption("--run-integration", default=False):
            item.add_marker(skip_integration)
        if "slow" in item.keywords and not config.getoption("--run-slow", default=False):
            item.add_marker(skip_slow)


@dataclass
class TestResult:
    """测试结果数据类"""
    name: str
    status: str
    duration: float
    message: str = ""
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestReport:
    """测试报告数据类"""
    title: str
    timestamp: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration: float = 0.0
    results: List[TestResult] = field(default_factory=list)
    coverage: Dict[str, Any] = field(default_factory=dict)
    security_findings: List[Dict] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    ai_recommendations: List[str] = field(default_factory=list)


class TimeoutSkip:
    """超时跳过装饰器"""
    
    def __init__(self, timeout_seconds: float = 30.0, skip_message: str = "测试超时，已自动跳过"):
        self.timeout = timeout_seconds
        self.skip_message = skip_message
    
    def __call__(self, func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                pytest.skip(self.skip_message)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                pytest.skip(self.skip_message)
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, self.timeout)
            
            try:
                result = func(*args, **kwargs)
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper


class AWVSTestClient:
    """AWVS集成测试客户端"""
    
    def __init__(self):
        self.api_url = settings.AWVS_API_URL
        self.api_key = settings.AWVS_API_KEY
    
    async def health_check(self) -> Dict[str, Any]:
        """检查AWVS服务健康状态"""
        try:
            from backend.AVWS.API.Dashboard import Dashboard
            dashboard = Dashboard(self.api_url, self.api_key)
            stats = dashboard.stats()
            return {
                "status": "healthy",
                "connected": True,
                "stats": json.loads(stats) if stats else {}
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    async def create_target(self, address: str, description: str = "") -> Optional[str]:
        """创建扫描目标"""
        try:
            from backend.AVWS.API.Target import Target
            target = Target(self.api_url, self.api_key)
            return target.add(address, description)
        except Exception as e:
            logger.error(f"创建目标失败: {str(e)}")
            return None
    
    async def start_scan(self, target_id: str, profile: str = "full_scan") -> Optional[str]:
        """启动扫描任务"""
        try:
            from backend.AVWS.API.Scan import Scan
            scan = Scan(self.api_url, self.api_key)
            return scan.launch(target_id, profile)
        except Exception as e:
            logger.error(f"启动扫描失败: {str(e)}")
            return None


class AIModelTestClient:
    """AI模型测试客户端"""
    
    def __init__(self):
        self.model_id = settings.MODEL_ID
        self.api_base = settings.OPENAI_BASE_URL
        self.api_key = settings.OPENAI_API_KEY
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试AI模型连接"""
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            
            start_time = time.time()
            response = client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": "你好，请回复'连接成功'"}],
                max_tokens=50
            )
            duration = time.time() - start_time
            
            return {
                "status": "success",
                "connected": True,
                "response": response.choices[0].message.content,
                "response_time": duration,
                "model": self.model_id
            }
        except Exception as e:
            return {
                "status": "failed",
                "connected": False,
                "error": str(e)
            }


class SeebugTestClient:
    """Seebug服务测试客户端"""
    
    def __init__(self):
        self.api_key = settings.SEEBUG_API_KEY
        self.api_base = settings.SEEBUG_API_BASE_URL
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试Seebug连接"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_base}/user/info",
                    headers={"Authorization": f"Token {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "connected": True,
                        "response": response.json()
                    }
                else:
                    return {
                        "status": "failed",
                        "connected": False,
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "failed",
                "connected": False,
                "error": str(e)
            }


class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, title: str = "综合测试报告"):
        self.report = TestReport(
            title=title,
            timestamp=datetime.now().isoformat()
        )
    
    def add_result(self, result: TestResult):
        """添加测试结果"""
        self.report.results.append(result)
        self.report.total_tests += 1
        
        if result.status == "passed":
            self.report.passed += 1
        elif result.status == "failed":
            self.report.failed += 1
        else:
            self.report.skipped += 1
        
        self.report.duration += result.duration
    
    def generate_html(self, output_path: str = None) -> str:
        """生成HTML报告"""
        if output_path is None:
            output_dir = Path(__file__).parent / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"test_report_{timestamp}.html"
        
        passed_rate = (self.report.passed / self.report.total_tests * 100) if self.report.total_tests > 0 else 0
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.report.title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .timestamp {{ opacity: 0.8; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }}
        .summary-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .summary-card .number {{ font-size: 36px; font-weight: bold; margin-bottom: 5px; }}
        .summary-card .label {{ color: #666; }}
        .passed {{ color: #22c55e; }}
        .failed {{ color: #ef4444; }}
        .skipped {{ color: #f59e0b; }}
        .total {{ color: #3b82f6; }}
        .section {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ font-size: 20px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #eee; }}
        .result-item {{ padding: 15px; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }}
        .result-item.passed {{ background: #f0fdf4; border-left: 4px solid #22c55e; }}
        .result-item.failed {{ background: #fef2f2; border-left: 4px solid #ef4444; }}
        .result-item.skipped {{ background: #fffbeb; border-left: 4px solid #f59e0b; }}
        .result-name {{ font-weight: 500; }}
        .result-duration {{ color: #666; font-size: 14px; }}
        .progress-bar {{ height: 20px; background: #e5e7eb; border-radius: 10px; overflow: hidden; margin-top: 20px; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #22c55e, #3b82f6); transition: width 0.3s; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.report.title}</h1>
            <div class="timestamp">生成时间: {self.report.timestamp}</div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="number total">{self.report.total_tests}</div>
                <div class="label">总测试数</div>
            </div>
            <div class="summary-card">
                <div class="number passed">{self.report.passed}</div>
                <div class="label">通过</div>
            </div>
            <div class="summary-card">
                <div class="number failed">{self.report.failed}</div>
                <div class="label">失败</div>
            </div>
            <div class="summary-card">
                <div class="number skipped">{self.report.skipped}</div>
                <div class="label">跳过</div>
            </div>
        </div>
        
        <div class="section">
            <h2>测试结果详情</h2>
            {self._generate_results_html()}
        </div>
    </div>
</body>
</html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def _generate_results_html(self) -> str:
        """生成测试结果HTML"""
        html = ""
        for result in self.report.results:
            html += f"""
            <div class="result-item {result.status}">
                <div>
                    <div class="result-name">{result.name}</div>
                    <div class="result-duration">{result.message}</div>
                </div>
                <div class="result-duration">{result.duration:.2f}s</div>
            </div>
            """
        return html


@pytest.fixture
def awvs_client():
    """AWVS测试客户端fixture"""
    return AWVSTestClient()


@pytest.fixture
def ai_client():
    """AI模型测试客户端fixture"""
    return AIModelTestClient()


@pytest.fixture
def seebug_client():
    """Seebug测试客户端fixture"""
    return SeebugTestClient()


@pytest.fixture
def report_generator():
    """测试报告生成器fixture"""
    return TestReportGenerator()


def timeout_skip(timeout_seconds: float = 30.0, message: str = "测试超时，已自动跳过"):
    """超时跳过装饰器快捷函数"""
    return TimeoutSkip(timeout_seconds, message)

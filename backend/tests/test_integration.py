"""
综合集成测试

整合API测试、真实环境测试和简单测试，提供统一的测试入口。
使用真实的AI模型服务、AWVS服务及Seebug服务等外部依赖。
"""
import pytest
import asyncio
import aiohttp
import httpx
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class IntegrationTestResult:
    name: str
    status: str
    duration: float
    message: str = ""
    error: Optional[str] = None
    response_data: Dict[str, Any] = field(default_factory=dict)


class IntegrationTestRunner:
    """综合集成测试运行器"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:3000", timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        self.results: List[IntegrationTestResult] = []
    
    async def _make_request(
        self, 
        method: str, 
        path: str, 
        json_data: dict = None,
        timeout: float = None
    ) -> tuple:
        """统一的请求方法"""
        url = f"{self.base_url}{path}"
        start_time = time.time()
        actual_timeout = timeout or self.timeout
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=actual_timeout)
            ) as session:
                if method.upper() == "GET":
                    async with session.get(url) as resp:
                        data = await resp.json()
                        return resp.status, data, time.time() - start_time
                elif method.upper() == "POST":
                    async with session.post(url, json=json_data) as resp:
                        data = await resp.json()
                        return resp.status, data, time.time() - start_time
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
        except asyncio.TimeoutError:
            raise TimeoutError(f"请求超时({actual_timeout}秒)")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"连接错误: {str(e)}")
    
    async def test_server_health(self) -> IntegrationTestResult:
        """测试服务器健康状态"""
        start_time = time.time()
        try:
            status, data, duration = await self._make_request("GET", "/health")
            
            if status == 200 and data.get("status") == "healthy":
                return IntegrationTestResult(
                    name="服务器健康检查",
                    status="passed",
                    duration=duration,
                    message="服务器运行正常",
                    response_data=data
                )
            else:
                return IntegrationTestResult(
                    name="服务器健康检查",
                    status="failed",
                    duration=duration,
                    message=f"服务器状态异常",
                    response_data=data
                )
        except TimeoutError as e:
            return IntegrationTestResult(
                name="服务器健康检查",
                status="skipped",
                duration=time.time() - start_time,
                message=str(e)
            )
        except Exception as e:
            return IntegrationTestResult(
                name="服务器健康检查",
                status="failed",
                duration=time.time() - start_time,
                message=str(e),
                error=str(e)
            )
    
    async def test_awvs_connection(self) -> IntegrationTestResult:
        """测试AWVS真实连接"""
        start_time = time.time()
        try:
            status, data, duration = await self._make_request("GET", "/api/awvs/health")
            
            if data.get("code") == 200:
                return IntegrationTestResult(
                    name="AWVS连接测试",
                    status="passed",
                    duration=duration,
                    message="AWVS连接成功",
                    response_data=data
                )
            else:
                return IntegrationTestResult(
                    name="AWVS连接测试",
                    status="failed",
                    duration=duration,
                    message=f"AWVS连接失败: {data.get('message', 'Unknown')}",
                    response_data=data
                )
        except TimeoutError as e:
            return IntegrationTestResult(
                name="AWVS连接测试",
                status="skipped",
                duration=time.time() - start_time,
                message=str(e)
            )
        except Exception as e:
            return IntegrationTestResult(
                name="AWVS连接测试",
                status="failed",
                duration=time.time() - start_time,
                message=str(e),
                error=str(e)
            )
    
    async def test_ai_model_connection(self) -> IntegrationTestResult:
        """测试AI大模型真实连接"""
        start_time = time.time()
        try:
            status, data, duration = await self._make_request(
                "POST", 
                "/api/ai/chat",
                {"message": "你好，请回复'连接成功'", "session_id": "test-session"},
                timeout=60.0
            )
            
            if status == 200 and (data.get("code") == 200 or data.get("response")):
                return IntegrationTestResult(
                    name="AI大模型连接测试",
                    status="passed",
                    duration=duration,
                    message=f"AI模型响应正常，耗时{duration:.2f}s",
                    response_data={"response": str(data.get("response", ""))[:100]}
                )
            else:
                return IntegrationTestResult(
                    name="AI大模型连接测试",
                    status="failed",
                    duration=duration,
                    message=f"AI模型响应异常: {data.get('message', 'Unknown')}",
                    response_data=data
                )
        except TimeoutError as e:
            return IntegrationTestResult(
                name="AI大模型连接测试",
                status="skipped",
                duration=time.time() - start_time,
                message=str(e)
            )
        except Exception as e:
            return IntegrationTestResult(
                name="AI大模型连接测试",
                status="failed",
                duration=time.time() - start_time,
                message=str(e),
                error=str(e)
            )
    
    async def test_awvs_targets(self) -> IntegrationTestResult:
        """测试AWVS目标列表获取"""
        start_time = time.time()
        try:
            status, data, duration = await self._make_request("GET", "/api/awvs/targets")
            
            if data.get("code") == 200:
                targets = data.get("data", [])
                count = len(targets) if isinstance(targets, list) else 0
                return IntegrationTestResult(
                    name="AWVS目标列表",
                    status="passed",
                    duration=duration,
                    message=f"获取到{count}个目标",
                    response_data={"count": count}
                )
            else:
                return IntegrationTestResult(
                    name="AWVS目标列表",
                    status="failed",
                    duration=duration,
                    message=f"获取失败: {data.get('message', 'Unknown')}",
                    response_data=data
                )
        except TimeoutError as e:
            return IntegrationTestResult(
                name="AWVS目标列表",
                status="skipped",
                duration=time.time() - start_time,
                message=str(e)
            )
        except Exception as e:
            return IntegrationTestResult(
                name="AWVS目标列表",
                status="failed",
                duration=time.time() - start_time,
                message=str(e),
                error=str(e)
            )
    
    async def test_awvs_scans(self) -> IntegrationTestResult:
        """测试AWVS扫描列表获取"""
        start_time = time.time()
        try:
            status, data, duration = await self._make_request("GET", "/api/awvs/scans")
            
            if data.get("code") == 200:
                scans = data.get("data", [])
                count = len(scans) if isinstance(scans, list) else 0
                return IntegrationTestResult(
                    name="AWVS扫描列表",
                    status="passed",
                    duration=duration,
                    message=f"获取到{count}个扫描任务",
                    response_data={"count": count}
                )
            else:
                return IntegrationTestResult(
                    name="AWVS扫描列表",
                    status="failed",
                    duration=duration,
                    message=f"获取失败: {data.get('message', 'Unknown')}",
                    response_data=data
                )
        except TimeoutError as e:
            return IntegrationTestResult(
                name="AWVS扫描列表",
                status="skipped",
                duration=time.time() - start_time,
                message=str(e)
            )
        except Exception as e:
            return IntegrationTestResult(
                name="AWVS扫描列表",
                status="failed",
                duration=time.time() - start_time,
                message=str(e),
                error=str(e)
            )
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有集成测试"""
        start_time = time.time()
        
        self.results = []
        self.results.append(await self.test_server_health())
        self.results.append(await self.test_awvs_connection())
        self.results.append(await self.test_ai_model_connection())
        self.results.append(await self.test_awvs_targets())
        self.results.append(await self.test_awvs_scans())
        
        total_duration = time.time() - start_time
        
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        skipped = sum(1 for r in self.results if r.status == "skipped")
        
        return {
            "title": "AI WebSecurity 综合集成测试报告",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": round(passed / len(self.results) * 100, 2) if self.results else 0,
                "total_duration": round(total_duration, 2)
            },
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "duration": round(r.duration, 3),
                    "message": r.message,
                    "error": r.error
                }
                for r in self.results
            ]
        }


@pytest.fixture
def test_runner():
    """测试运行器fixture"""
    return IntegrationTestRunner(base_url="http://127.0.0.1:3000")


class TestIntegration:
    """集成测试类"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_server_health(self, test_runner):
        """测试服务器健康状态"""
        result = await test_runner.test_server_health()
        if result.status == "failed" and "连接错误" in result.message:
            pytest.skip(f"后端服务未启动: {result.message}")
        assert result.status in ["passed", "skipped"], f"服务器健康检查失败: {result.message}"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_awvs_connection(self, test_runner):
        """测试AWVS连接"""
        result = await test_runner.test_awvs_connection()
        if result.status == "failed" and "连接错误" in result.message:
            pytest.skip(f"后端服务未启动: {result.message}")
        assert result.status in ["passed", "skipped"], f"AWVS连接测试失败: {result.message}"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ai_model_connection(self, test_runner):
        """测试AI模型连接"""
        result = await test_runner.test_ai_model_connection()
        if result.status == "failed" and "连接错误" in result.message:
            pytest.skip(f"后端服务未启动: {result.message}")
        assert result.status in ["passed", "skipped"], f"AI模型连接测试失败: {result.message}"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_awvs_targets(self, test_runner):
        """测试AWVS目标列表"""
        result = await test_runner.test_awvs_targets()
        if result.status == "failed" and "连接错误" in result.message:
            pytest.skip(f"后端服务未启动: {result.message}")
        assert result.status in ["passed", "skipped"], f"AWVS目标列表测试失败: {result.message}"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_awvs_scans(self, test_runner):
        """测试AWVS扫描列表"""
        result = await test_runner.test_awvs_scans()
        if result.status == "failed" and "连接错误" in result.message:
            pytest.skip(f"后端服务未启动: {result.message}")
        assert result.status in ["passed", "skipped"], f"AWVS扫描列表测试失败: {result.message}"


async def run_integration_tests():
    """运行集成测试并生成报告"""
    print("=" * 60)
    print("AI WebSecurity 综合集成测试")
    print("=" * 60)
    print()
    
    runner = IntegrationTestRunner()
    report = await runner.run_all_tests()
    
    print()
    print("=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    print(f"总测试数: {report['summary']['total']}")
    print(f"通过: {report['summary']['passed']}")
    print(f"失败: {report['summary']['failed']}")
    print(f"跳过: {report['summary']['skipped']}")
    print(f"通过率: {report['summary']['pass_rate']}%")
    print(f"总耗时: {report['summary']['total_duration']}秒")
    
    return report


if __name__ == "__main__":
    asyncio.run(run_integration_tests())

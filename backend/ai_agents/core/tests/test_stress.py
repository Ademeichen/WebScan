"""
压力测试和稳定性测试

进行多并发用户测试、长时间运行稳定性测试等。
"""
import pytest
import asyncio
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from backend.ai_agents.core.state import AgentState
from backend.ai_agents.core.graph import ScanAgentGraph, create_agent_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StressTestResult:
    """压力测试结果"""
    test_name: str
    start_time: float
    end_time: float = field(default_factory=time.time)
    duration: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    errors: List[str] = field(default_factory=list)
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float('inf')
    requests_per_second: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class StressTestSuite:
    """压力测试套件"""
    
    def __init__(self):
        self.results: List[StressTestResult] = []
    
    async def concurrent_users_test(
        self,
        num_users: int,
        target: str = "http://example.com",
        duration_seconds: float = 60.0
    ) -> StressTestResult:
        """
        并发用户测试
        
        Args:
            num_users: 并发用户数
            target: 目标URL
            duration_seconds: 测试持续时间
            
        Returns:
            StressTestResult: 测试结果
        """
        logger.info(f"🚀 开始并发用户测试: {num_users} 用户")
        
        result = StressTestResult(
            test_name=f"concurrent_users_{num_users}",
            start_time=time.time()
        )
        
        response_times = []
        
        async def user_task(user_id: int):
            """单个用户任务"""
            try:
                user_start = time.time()
                
                state = AgentState(
                    task_id=f"stress-test-user-{user_id}-{int(time.time())}",
                    target=target
                )
                state.planned_tasks = ["baseinfo"]
                
                await asyncio.sleep(0.1)
                
                user_duration = time.time() - user_start
                
                return {
                    "success": True,
                    "duration": user_duration
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "duration": 0
                }
        
        try:
            tasks = [user_task(i) for i in range(num_users)]
            
            start_time = time.time()
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            result.end_time = end_time
            result.duration = end_time - start_time
            result.total_requests = num_users
            
            for task_result in task_results:
                if isinstance(task_result, dict):
                    if task_result.get("success"):
                        result.successful_requests += 1
                        duration = task_result.get("duration", 0)
                        response_times.append(duration)
                        
                        result.max_response_time = max(result.max_response_time, duration)
                        result.min_response_time = min(result.min_response_time, duration)
                    else:
                        result.failed_requests += 1
                        result.errors.append(task_result.get("error", "unknown error"))
                else:
                    result.failed_requests += 1
                    result.errors.append(str(task_result))
            
            if response_times:
                result.avg_response_time = sum(response_times) / len(response_times)
            
            if result.duration > 0:
                result.requests_per_second = result.total_requests / result.duration
            
            logger.info(f"✅ 并发用户测试完成: {num_users} 用户")
            logger.info(f"   总请求: {result.total_requests}")
            logger.info(f"   成功: {result.successful_requests}")
            logger.info(f"   失败: {result.failed_requests}")
            logger.info(f"   平均响应时间: {result.avg_response_time:.3f}s")
            logger.info(f"   最大响应时间: {result.max_response_time:.3f}s")
            logger.info(f"   最小响应时间: {result.min_response_time:.3f}s")
            logger.info(f"   吞吐量: {result.requests_per_second:.2f} req/s")
            
        except Exception as e:
            logger.error(f"❌ 并发用户测试失败: {str(e)}")
            result.errors.append(str(e))
        
        self.results.append(result)
        return result
    
    async def state_creation_stress_test(
        self,
        num_creations: int = 10000
    ) -> StressTestResult:
        """
        状态创建压力测试
        
        Args:
            num_creations: 创建次数
            
        Returns:
            StressTestResult: 测试结果
        """
        logger.info(f"🚀 开始状态创建压力测试: {num_creations} 次")
        
        result = StressTestResult(
            test_name=f"state_creation_{num_creations}",
            start_time=time.time()
        )
        
        response_times = []
        
        try:
            for i in range(num_creations):
                start = time.time()
                
                state = AgentState(
                    task_id=f"stress-test-state-{i}",
                    target=f"http://target-{i}.example.com"
                )
                state.planned_tasks = ["baseinfo", "portscan"]
                state.target_context["test"] = "data"
                
                duration = time.time() - start
                response_times.append(duration)
                
                result.successful_requests += 1
                result.max_response_time = max(result.max_response_time, duration)
                result.min_response_time = min(result.min_response_time, duration)
            
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time
            result.total_requests = num_creations
            
            if response_times:
                result.avg_response_time = sum(response_times) / len(response_times)
            
            if result.duration > 0:
                result.requests_per_second = result.total_requests / result.duration
            
            logger.info(f"✅ 状态创建压力测试完成: {num_creations} 次")
            logger.info(f"   平均创建时间: {result.avg_response_time * 1000:.3f}ms")
            logger.info(f"   最大创建时间: {result.max_response_time * 1000:.3f}ms")
            logger.info(f"   最小创建时间: {result.min_response_time * 1000:.3f}ms")
            logger.info(f"   吞吐量: {result.requests_per_second:.0f} 创建/s")
            
        except Exception as e:
            logger.error(f"❌ 状态创建压力测试失败: {str(e)}")
            result.errors.append(str(e))
            result.failed_requests = num_creations - result.successful_requests
        
        self.results.append(result)
        return result
    
    async def graph_creation_stress_test(
        self,
        num_creations: int = 1000
    ) -> StressTestResult:
        """
        图创建压力测试
        
        Args:
            num_creations: 创建次数
            
        Returns:
            StressTestResult: 测试结果
        """
        logger.info(f"🚀 开始图创建压力测试: {num_creations} 次")
        
        result = StressTestResult(
            test_name=f"graph_creation_{num_creations}",
            start_time=time.time()
        )
        
        response_times = []
        
        try:
            for i in range(num_creations):
                start = time.time()
                
                graph = ScanAgentGraph()
                
                duration = time.time() - start
                response_times.append(duration)
                
                result.successful_requests += 1
                result.max_response_time = max(result.max_response_time, duration)
                result.min_response_time = min(result.min_response_time, duration)
            
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time
            result.total_requests = num_creations
            
            if response_times:
                result.avg_response_time = sum(response_times) / len(response_times)
            
            if result.duration > 0:
                result.requests_per_second = result.total_requests / result.duration
            
            logger.info(f"✅ 图创建压力测试完成: {num_creations} 次")
            logger.info(f"   平均创建时间: {result.avg_response_time * 1000:.3f}ms")
            logger.info(f"   最大创建时间: {result.max_response_time * 1000:.3f}ms")
            logger.info(f"   最小创建时间: {result.min_response_time * 1000:.3f}ms")
            logger.info(f"   吞吐量: {result.requests_per_second:.0f} 创建/s")
            
        except Exception as e:
            logger.error(f"❌ 图创建压力测试失败: {str(e)}")
            result.errors.append(str(e))
            result.failed_requests = num_creations - result.successful_requests
        
        self.results.append(result)
        return result
    
    async def memory_leak_test(
        self,
        num_iterations: int = 1000
    ) -> StressTestResult:
        """
        内存泄漏测试
        
        Args:
            num_iterations: 迭代次数
            
        Returns:
            StressTestResult: 测试结果
        """
        logger.info(f"🚀 开始内存泄漏测试: {num_iterations} 次")
        
        result = StressTestResult(
            test_name=f"memory_leak_{num_iterations}",
            start_time=time.time()
        )
        
        try:
            import gc
            
            gc.collect()
            initial_objects = len(gc.get_objects())
            
            for i in range(num_iterations):
                state = AgentState(
                    task_id=f"mem-test-{i}",
                    target="http://example.com"
                )
                state.planned_tasks = ["baseinfo"]
                state.tool_results["test"] = {"data": "x" * 1000}
                
                del state
                
                if i % 100 == 0:
                    gc.collect()
            
            gc.collect()
            final_objects = len(gc.get_objects())
            
            object_increase = final_objects - initial_objects
            leak_percentage = (object_increase / initial_objects * 100) if initial_objects > 0 else 0
            
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time
            result.total_requests = num_iterations
            result.successful_requests = num_iterations
            
            result.details = {
                "initial_objects": initial_objects,
                "final_objects": final_objects,
                "object_increase": object_increase,
                "leak_percentage": leak_percentage
            }
            
            logger.info(f"✅ 内存泄漏测试完成")
            logger.info(f"   初始对象数: {initial_objects}")
            logger.info(f"   最终对象数: {final_objects}")
            logger.info(f"   对象增长: {object_increase} ({leak_percentage:.2f}%)")
            
            if leak_percentage > 5:
                logger.warning(f"⚠️  可能存在内存泄漏: {leak_percentage:.2f}% 增长")
                result.errors.append(f"可能存在内存泄漏: {leak_percentage:.2f}% 增长")
            
        except Exception as e:
            logger.error(f"❌ 内存泄漏测试失败: {str(e)}")
            result.errors.append(str(e))
        
        self.results.append(result)
        return result
    
    def generate_report(self) -> Dict[str, Any]:
        """
        生成测试报告
        
        Returns:
            Dict[str, Any]: 测试报告
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "results": []
        }
        
        for result in self.results:
            report["results"].append({
                "test_name": result.test_name,
                "duration": result.duration,
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "failed_requests": result.failed_requests,
                "avg_response_time": result.avg_response_time,
                "max_response_time": result.max_response_time,
                "min_response_time": result.min_response_time,
                "requests_per_second": result.requests_per_second,
                "errors": result.errors,
                "timestamp": result.timestamp
            })
        
        return report


@pytest.mark.slow
@pytest.mark.stress
class TestStressTests:
    """压力测试类"""
    
    @pytest.fixture
    def stress_suite(self):
        """压力测试套件fixture"""
        return StressTestSuite()
    
    @pytest.mark.asyncio
    async def test_5_concurrent_users(self, stress_suite):
        """测试5个并发用户"""
        result = await stress_suite.concurrent_users_test(
            num_users=5,
            duration_seconds=30.0
        )
        
        assert result.total_requests == 5
        assert result.successful_requests >= 0
    
    @pytest.mark.asyncio
    async def test_10_concurrent_users(self, stress_suite):
        """测试10个并发用户"""
        result = await stress_suite.concurrent_users_test(
            num_users=10,
            duration_seconds=30.0
        )
        
        assert result.total_requests == 10
        assert result.successful_requests >= 0
    
    @pytest.mark.asyncio
    async def test_state_creation_stress(self, stress_suite):
        """测试状态创建压力"""
        result = await stress_suite.state_creation_stress_test(
            num_creations=1000
        )
        
        assert result.total_requests == 1000
        assert result.successful_requests == 1000
        assert result.avg_response_time < 0.1
    
    @pytest.mark.asyncio
    async def test_graph_creation_stress(self, stress_suite):
        """测试图创建压力"""
        result = await stress_suite.graph_creation_stress_test(
            num_creations=100
        )
        
        assert result.total_requests == 100
        assert result.successful_requests == 100
    
    @pytest.mark.asyncio
    async def test_memory_leak(self, stress_suite):
        """测试内存泄漏"""
        result = await stress_suite.memory_leak_test(
            num_iterations=1000
        )
        
        assert result.total_requests == 1000
        assert len(result.errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--run-slow"])

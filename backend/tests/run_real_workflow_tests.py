"""
AI Agent工作流实际测试

测试要求:
- 禁止使用MOCK模式
- 调用实际的AI大模型接口
- 测试不少于3次
- 错误率控制在0.1%以下
"""
import asyncio
import sys
import os
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_agents.core.graph import ScanAgentGraph, create_agent_graph
from ai_agents.core.state import AgentState

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowTestResult:
    def __init__(self, test_id: str, target: str):
        self.test_id = test_id
        self.target = target
        self.start_time = datetime.now()
        self.end_time = None
        self.status = "running"
        self.error = None
        self.vulnerabilities = []
        self.completed_tasks = []
        self.execution_time = 0
        self.final_state = None
    
    def complete(self, status: str, final_state: AgentState = None, error: str = None):
        self.end_time = datetime.now()
        self.status = status
        self.error = error
        self.final_state = final_state
        self.execution_time = (self.end_time - self.start_time).total_seconds()
        
        if final_state:
            self.vulnerabilities = getattr(final_state, 'vulnerabilities', [])
            self.completed_tasks = getattr(final_state, 'completed_tasks', [])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "target": self.target,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "error": self.error,
            "vulnerabilities_count": len(self.vulnerabilities),
            "completed_tasks": self.completed_tasks,
            "execution_time": self.execution_time
        }


async def run_single_workflow_test(test_id: str, target: str) -> WorkflowTestResult:
    """
    运行单次工作流测试
    
    Args:
        test_id: 测试ID
        target: 扫描目标
        
    Returns:
        WorkflowTestResult: 测试结果
    """
    result = WorkflowTestResult(test_id, target)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"开始测试 #{test_id}")
    logger.info(f"目标: {target}")
    logger.info(f"时间: {result.start_time.isoformat()}")
    logger.info(f"{'='*60}")
    
    try:
        graph = create_agent_graph()
        
        initial_state = AgentState(
            target=target,
            task_id=test_id
        )
        
        logger.info(f"[{test_id}] 开始执行工作流...")
        
        final_state = await graph.invoke(initial_state)
        
        result.complete(
            status="success",
            final_state=final_state
        )
        
        logger.info(f"[{test_id}] ✅ 测试完成")
        logger.info(f"[{test_id}] 执行时间: {result.execution_time:.2f}秒")
        logger.info(f"[{test_id}] 完成任务: {result.completed_tasks}")
        logger.info(f"[{test_id}] 发现漏洞: {len(result.vulnerabilities)}个")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{test_id}] ❌ 测试失败: {error_msg}")
        result.complete(
            status="failed",
            error=error_msg
        )
    
    return result


async def run_workflow_tests(test_targets: List[str], min_tests: int = 3) -> Dict[str, Any]:
    """
    运行多次工作流测试
    
    Args:
        test_targets: 测试目标列表
        min_tests: 最小测试次数
        
    Returns:
        Dict: 测试报告
    """
    logger.info("\n" + "="*60)
    logger.info("AI Agent工作流实际测试")
    logger.info("禁止MOCK模式 - 使用实际AI大模型接口")
    logger.info("="*60)
    
    start_time = time.time()
    results: List[WorkflowTestResult] = []
    
    test_count = max(len(test_targets), min_tests)
    
    for i in range(test_count):
        target = test_targets[i % len(test_targets)]
        test_id = f"real_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}"
        
        result = await run_single_workflow_test(test_id, target)
        results.append(result)
        
        await asyncio.sleep(1)
    
    total_time = time.time() - start_time
    
    success_count = sum(1 for r in results if r.status == "success")
    failed_count = sum(1 for r in results if r.status == "failed")
    total_vulnerabilities = sum(len(r.vulnerabilities) for r in results)
    
    error_rate = (failed_count / len(results)) * 100 if results else 0
    
    report = {
        "test_summary": {
            "total_tests": len(results),
            "success_count": success_count,
            "failed_count": failed_count,
            "error_rate": error_rate,
            "error_rate_target": 0.1,
            "error_rate_passed": error_rate <= 0.1,
            "total_vulnerabilities": total_vulnerabilities,
            "total_execution_time": total_time,
            "average_execution_time": total_time / len(results) if results else 0
        },
        "test_results": [r.to_dict() for r in results],
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info("\n" + "="*60)
    logger.info("测试报告汇总")
    logger.info("="*60)
    logger.info(f"总测试数: {len(results)}")
    logger.info(f"成功: {success_count}")
    logger.info(f"失败: {failed_count}")
    logger.info(f"错误率: {error_rate:.2f}% (目标: <= 0.1%)")
    logger.info(f"错误率达标: {'✅ 是' if error_rate <= 0.1 else '❌ 否'}")
    logger.info(f"总漏洞发现: {total_vulnerabilities}个")
    logger.info(f"总执行时间: {total_time:.2f}秒")
    logger.info(f"平均执行时间: {total_time/len(results):.2f}秒")
    
    for r in results:
        status_icon = "✅" if r.status == "success" else "❌"
        logger.info(f"  {status_icon} {r.test_id}: {r.status} ({r.execution_time:.2f}s)")
    
    return report


def save_report(report: Dict[str, Any], output_dir: Path = None):
    """
    保存测试报告
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "reports"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"real_workflow_test_report_{timestamp}.json"
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"\n📄 测试报告已保存: {report_file}")
    return report_file


async def main():
    """
    主函数
    """
    test_targets = [
        "https://www.baidu.com",
        "https://www.qq.com",
        "https://www.sina.com.cn"
    ]
    
    report = await run_workflow_tests(test_targets, min_tests=3)
    
    save_report(report)
    
    if report["test_summary"]["error_rate_passed"]:
        logger.info("\n✅ 测试通过 - 错误率符合要求 (<= 0.1%)")
        return 0
    else:
        logger.error(f"\n❌ 测试失败 - 错误率 {report['test_summary']['error_rate']:.2f}% 超过目标 0.1%")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

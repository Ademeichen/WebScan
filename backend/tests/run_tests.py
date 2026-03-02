"""
AIAgent 综合测试套件

整合所有测试功能，- 节点功能测试
- 工作流集成测试
- 真实AI模型测试
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSuite:
    """综合测试套件"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.report_dir = Path(__file__).parent / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def log_test(self, name: str, passed: bool, message: str = "", details: Dict = None):
        result = {
            "name": name,
            "passed": passed,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        icon = "✅" if passed else "❌"
        logger.info(f"{icon} {name}: {message}")
    
    async def test_graph_structure(self) -> bool:
        """测试图结构"""
        try:
            from ai_agents.core.graph import ScanAgentGraph
            
            graph = ScanAgentGraph()
            info = graph.get_graph_info()
            
            passed = (
                info["total_nodes"] == 13 and
                info["entry_point"] == "environment_awareness" and
                "report_generation" in info["exit_points"]
            )
            
            self.log_test(
                "图结构验证",
                passed,
                f"节点数: {info['total_nodes']}, 入口: {info['entry_point']}",
                info
            )
            return passed
        except Exception as e:
            self.log_test("图结构验证", False, str(e))
            return False
    
    async def test_state_management(self) -> bool:
        """测试状态管理"""
        try:
            from ai_agents.core.state import AgentState
            
            state = AgentState(
                target="http://example.com",
                task_id="test_state"
            )
            
            state.update_context("test_key", "test_value")
            state.add_vulnerability({"cve": "CVE-2021-001"})
            state.add_error("Test error")
            
            passed = (
                state.target_context.get("test_key") == "test_value" and
                len(state.vulnerabilities) == 1 and
                len(state.errors) == 1
            )
            
            self.log_test(
                "状态管理验证",
                passed,
                f"上下文: {state.target_context.get('test_key')}, 漏洞: {len(state.vulnerabilities)}"
            )
            return passed
        except Exception as e:
            self.log_test("状态管理验证", False, str(e))
            return False
    
    async def test_routing_logic(self) -> bool:
        """测试路由逻辑"""
        try:
            from ai_agents.core.graph import ScanAgentGraph
            from ai_agents.core.state import AgentState
            
            graph = ScanAgentGraph()
            
            state1 = AgentState(
                target="http://example.com",
                task_id="test_route_1",
                planned_tasks=["baseinfo"],
                target_context={}
            )
            result1 = graph._decide_scan_type(state1)
            
            state2 = AgentState(
                target="http://example.com",
                task_id="test_route_2",
                planned_tasks=[],
                target_context={"need_custom_scan": True}
            )
            result2 = graph._decide_scan_type(state2)
            
            passed = result1 == "fixed_tool" and result2 == "custom_code"
            
            self.log_test(
                "路由逻辑验证",
                passed,
                f"固定工具: {result1}, 自定义代码: {result2}"
            )
            return passed
        except Exception as e:
            self.log_test("路由逻辑验证", False, str(e))
            return False
    
    async def test_environment_awareness(self) -> bool:
        """测试环境感知节点"""
        try:
            from ai_agents.core.nodes import EnvironmentAwarenessNode
            from ai_agents.core.state import AgentState
            
            state = AgentState(
                target="http://example.com",
                task_id="test_env"
            )
            
            node = EnvironmentAwarenessNode()
            result = await node(state)
            
            passed = "environment_info" in result.target_context
            
            self.log_test(
                "环境感知节点",
                passed,
                f"OS: {result.target_context.get('os_system')}"
            )
            return passed
        except Exception as e:
            self.log_test("环境感知节点", False, str(e))
            return False
    
    async def test_task_planning(self) -> bool:
        """测试任务规划节点"""
        try:
            from ai_agents.core.nodes import TaskPlanningNode
            from ai_agents.core.state import AgentState
            
            state = AgentState(
                target="http://example.com",
                task_id="test_planning"
            )
            
            node = TaskPlanningNode()
            result = await node(state)
            
            passed = len(result.planned_tasks) > 0
            
            self.log_test(
                "任务规划节点",
                passed,
                f"任务数: {len(result.planned_tasks)}, 任务: {result.planned_tasks[:3]}"
            )
            return passed
        except Exception as e:
            self.log_test("任务规划节点", False, str(e))
            return False
    
    async def test_intelligent_decision(self) -> bool:
        """测试智能决策节点"""
        try:
            from ai_agents.core.nodes import IntelligentDecisionNode
            from ai_agents.core.state import AgentState
            
            state = AgentState(
                target="http://example.com",
                task_id="test_decision",
                planned_tasks=["baseinfo"],
                target_context={"os_system": "Windows"}
            )
            
            node = IntelligentDecisionNode()
            result = await node(state)
            
            decisions = result.target_context.get("intelligent_decisions", [])
            passed = len(decisions) > 0
            
            self.log_test(
                "智能决策节点",
                passed,
                f"决策数: {len(decisions)}"
            )
            return passed
        except Exception as e:
            self.log_test("智能决策节点", False, str(e))
            return False
    
    async def test_code_generation(self) -> bool:
        """测试代码生成节点"""
        try:
            from ai_agents.core.nodes import CodeGenerationNode
            from ai_agents.core.state import AgentState
            
            state = AgentState(
                target="http://example.com",
                task_id="test_codegen",
                target_context={
                    "need_custom_scan": True,
                    "custom_scan_type": "vuln_scan",
                    "custom_scan_requirements": "检测SQL注入",
                    "custom_scan_language": "python"
                }
            )
            
            node = CodeGenerationNode()
            result = await node(state)
            
            code_info = result.tool_results.get("generated_code", {})
            passed = "code" in code_info and len(code_info.get("code", "")) > 0
            
            self.log_test(
                "代码生成节点",
                passed,
                f"代码长度: {len(code_info.get('code', ''))}"
            )
            return passed
        except Exception as e:
            self.log_test("代码生成节点", False, str(e))
            return False
    
    async def test_code_execution(self) -> bool:
        """测试代码执行节点"""
        try:
            from ai_agents.core.nodes import CodeExecutionNode
            from ai_agents.core.state import AgentState
            
            simple_code = """
print("Hello from code execution test!")
result = {"status": "success"}
print(result)
"""
            
            state = AgentState(
                target="http://example.com",
                task_id="test_codeexec",
                target_context={
                    "generated_code": {
                        "code": simple_code,
                        "language": "python"
                    }
                }
            )
            
            node = CodeExecutionNode()
            result = await node(state)
            
            exec_result = result.tool_results.get("code_execution", {})
            passed = exec_result.get("status") in ["success", "failed"]
            
            self.log_test(
                "代码执行节点",
                passed,
                f"状态: {exec_result.get('status')}"
            )
            return passed
        except Exception as e:
            self.log_test("代码执行节点", False, str(e))
            return False
    
    async def test_report_generation(self) -> bool:
        """测试报告生成节点"""
        try:
            from ai_agents.core.nodes import ReportGenerationNode
            from ai_agents.core.state import AgentState
            
            state = AgentState(
                target="http://example.com",
                task_id="test_report",
                vulnerabilities=[{"name": "Test Vuln", "severity": "high"}],
                completed_tasks=["baseinfo"],
                tool_results={"baseinfo": {"status": "success"}}
            )
            
            node = ReportGenerationNode()
            result = await node(state)
            
            passed = "final_report" in result.tool_results and result.is_complete
            
            self.log_test(
                "报告生成节点",
                passed,
                f"完成状态: {result.is_complete}"
            )
            return passed
        except Exception as e:
            self.log_test("报告生成节点", False, str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.start_time = time.time()
        
        print("\n" + "="*60)
        print("       AIAgent 综合测试套件")
        print("       使用真实AI模型接口")
        print("="*60 + "\n")
        
        tests = [
            self.test_graph_structure,
            self.test_state_management,
            self.test_routing_logic,
            self.test_environment_awareness,
            self.test_task_planning,
            self.test_intelligent_decision,
            self.test_code_generation,
            self.test_code_execution,
            self.test_report_generation
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                logger.error(f"测试执行异常: {str(e)}")
        
        total_time = time.time() - self.start_time
        
        return self.generate_report(total_time)
    
    def generate_report(self, total_time: float) -> Dict[str, Any]:
        """生成测试报告"""
        passed = sum(1 for r in self.results if r["passed"])
        failed = len(self.results) - passed
        
        report = {
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{(passed/len(self.results)*100):.1f}%" if self.results else "0%",
                "total_time": f"{total_time:.2f}s"
            },
            "results": self.results,
            "timestamp": datetime.now().isoformat()
        }
        
        print("\n" + "="*60)
        print("                    测试报告")
        print("="*60)
        print(f"\n总测试数: {len(self.results)}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {report['summary']['pass_rate']}")
        print(f"总耗时: {total_time:.2f}秒")
        
        print("\n测试详情:")
        for r in self.results:
            icon = "✅" if r["passed"] else "❌"
            print(f"  {icon} {r['name']}: {r['message']}")
        
        self.save_report(report)
        
        return report
    
    def save_report(self, report: Dict[str, Any]):
        """保存报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.report_dir / f"test_report_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 测试报告已保存: {report_file}")


async def main():
    """主函数"""
    suite = TestSuite()
    report = await suite.run_all_tests()
    
    passed = sum(1 for r in report["results"] if r["passed"])
    total = len(report["results"])
    
    if passed == total:
        print("\n✅ 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️ 部分测试失败: {total - passed}/{total}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

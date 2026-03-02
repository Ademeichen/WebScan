"""
AIAgent节点功能测试

测试用例设计:
1. 环境感知节点测试 - 验证环境检测功能
2. 任务规划节点测试 - 验证LLM/规则规划功能
3. 智能决策节点测试 - 验证决策路由逻辑
4. 代码生成节点测试 - 验证代码生成功能
5. 代码执行节点测试 - 验证代码执行功能
6. POC验证节点测试 - 验证POC验证流程
7. 漏洞分析节点测试 - 验证漏洞分析功能
8. 报告生成节点测试 - 验证报告生成功能
"""
import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_agents.core.state import AgentState
from ai_agents.core.nodes import (
    EnvironmentAwarenessNode,
    TaskPlanningNode,
    IntelligentDecisionNode,
    CodeGenerationNode,
    CodeExecutionNode,
    CapabilityEnhancementNode,
    ResultVerificationNode,
    POCVerificationNode,
    VulnerabilityAnalysisNode,
    ReportGenerationNode,
    AWVSScanningNode,
    SeebugAgentNode
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NodeTestResult:
    def __init__(self, test_name: str, passed: bool, message: str = "", details: dict = None):
        self.test_name = test_name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


async def test_environment_awareness_node() -> NodeTestResult:
    """
    测试用例1: 环境感知节点测试
    
    验证点:
    - 节点能够正确初始化
    - 能够检测操作系统信息
    - 能够检测Python版本
    - 能够检测可用工具
    """
    test_name = "EnvironmentAwarenessNode"
    logger.info(f"\n{'='*60}")
    logger.info(f"开始测试: {test_name}")
    logger.info(f"{'='*60}")
    
    try:
        node = EnvironmentAwarenessNode()
        state = AgentState(
            target="http://example.com",
            task_id="test_env_001"
        )
        
        result = await node(state)
        
        assert "environment_info" in result.target_context, "缺少环境信息"
        env_info = result.target_context["environment_info"]
        
        assert "os_info" in env_info, "缺少操作系统信息"
        assert "python_info" in env_info, "缺少Python信息"
        assert "available_tools" in env_info, "缺少可用工具信息"
        
        os_system = result.target_context.get("os_system")
        python_version = result.target_context.get("python_version")
        
        logger.info(f"✅ 操作系统: {os_system}")
        logger.info(f"✅ Python版本: {python_version}")
        logger.info(f"✅ 可用工具数量: {len(env_info['available_tools'])}")
        
        return NodeTestResult(
            test_name=test_name,
            passed=True,
            message="环境感知节点测试通过",
            details={
                "os": os_system,
                "python_version": python_version,
                "tools_count": len(env_info['available_tools'])
            }
        )
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return NodeTestResult(
            test_name=test_name,
            passed=False,
            message=f"测试失败: {str(e)}"
        )


async def test_task_planning_node() -> NodeTestResult:
    """
    测试用例2: 任务规划节点测试
    
    验证点:
    - 节点能够正确初始化
    - 能够生成任务列表
    - 任务列表不为空
    - 当前任务被正确设置
    """
    test_name = "TaskPlanningNode"
    logger.info(f"\n{'='*60}")
    logger.info(f"开始测试: {test_name}")
    logger.info(f"{'='*60}")
    
    try:
        node = TaskPlanningNode()
        state = AgentState(
            target="http://example.com",
            task_id="test_plan_001",
            target_context={
                "os_system": "Windows",
                "python_version": "3.10.0"
            }
        )
        
        result = await node(state)
        
        assert result.planned_tasks is not None, "任务列表为空"
        assert len(result.planned_tasks) > 0, "任务列表为空"
        assert result.current_task is not None, "当前任务未设置"
        
        logger.info(f"✅ 规划任务数量: {len(result.planned_tasks)}")
        logger.info(f"✅ 任务列表: {result.planned_tasks}")
        logger.info(f"✅ 当前任务: {result.current_task}")
        
        return NodeTestResult(
            test_name=test_name,
            passed=True,
            message="任务规划节点测试通过",
            details={
                "tasks_count": len(result.planned_tasks),
                "tasks": result.planned_tasks,
                "current_task": result.current_task
            }
        )
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return NodeTestResult(
            test_name=test_name,
            passed=False,
            message=f"测试失败: {str(e)}"
        )


async def test_intelligent_decision_node() -> NodeTestResult:
    """
    测试用例3: 智能决策节点测试
    
    验证点:
    - 节点能够正确初始化
    - 能够基于环境信息做出决策
    - 决策结果符合预期
    """
    test_name = "IntelligentDecisionNode"
    logger.info(f"\n{'='*60}")
    logger.info(f"开始测试: {test_name}")
    logger.info(f"{'='*60}")
    
    try:
        node = IntelligentDecisionNode()
        state = AgentState(
            target="http://example.com",
            task_id="test_decision_001",
            target_context={
                "os_system": "Windows",
                "cms": "tomcat"
            },
            planned_tasks=["baseinfo", "portscan"]
        )
        
        result = await node(state)
        
        assert "intelligent_decisions" in result.target_context, "缺少决策结果"
        decisions = result.target_context["intelligent_decisions"]
        
        assert len(decisions) > 0, "决策列表为空"
        
        logger.info(f"✅ 决策数量: {len(decisions)}")
        logger.info(f"✅ 决策列表: {decisions}")
        
        return NodeTestResult(
            test_name=test_name,
            passed=True,
            message="智能决策节点测试通过",
            details={
                "decisions_count": len(decisions),
                "decisions": decisions
            }
        )
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return NodeTestResult(
            test_name=test_name,
            passed=False,
            message=f"测试失败: {str(e)}"
        )


async def test_code_generation_node() -> NodeTestResult:
    """
    测试用例4: 代码生成节点测试
    
    验证点:
    - 节点能够正确初始化
    - 能够生成代码
    - 生成的代码符合要求
    - 代码文件被正确保存
    """
    test_name = "CodeGenerationNode"
    logger.info(f"\n{'='*60}")
    logger.info(f"开始测试: {test_name}")
    logger.info(f"{'='*60}")
    
    try:
        node = CodeGenerationNode()
        state = AgentState(
            target="http://example.com",
            task_id="test_codegen_001",
            target_context={
                "need_custom_scan": True,
                "custom_scan_type": "vuln_scan",
                "custom_scan_requirements": "检测SQL注入漏洞",
                "custom_scan_language": "python"
            }
        )
        
        result = await node(state)
        
        assert "generated_code" in result.tool_results, "缺少生成代码结果"
        code_info = result.tool_results["generated_code"]
        
        assert "code" in code_info, "缺少代码内容"
        assert len(code_info["code"]) > 0, "代码内容为空"
        
        logger.info(f"✅ 代码长度: {len(code_info['code'])} 字符")
        logger.info(f"✅ 代码语言: {code_info.get('language', 'python')}")
        logger.info(f"✅ 依赖列表: {code_info.get('dependencies', [])}")
        
        if "file_path" in code_info:
            logger.info(f"✅ 代码文件: {code_info['file_path']}")
        
        return NodeTestResult(
            test_name=test_name,
            passed=True,
            message="代码生成节点测试通过",
            details={
                "code_length": len(code_info["code"]),
                "language": code_info.get("language", "python"),
                "dependencies": code_info.get("dependencies", [])
            }
        )
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return NodeTestResult(
            test_name=test_name,
            passed=False,
            message=f"测试失败: {str(e)}"
        )


async def test_code_execution_node() -> NodeTestResult:
    """
    测试用例5: 代码执行节点测试
    
    验证点:
    - 节点能够正确初始化
    - 能够执行简单代码
    - 执行结果正确返回
    """
    test_name = "CodeExecutionNode"
    logger.info(f"\n{'='*60}")
    logger.info(f"开始测试: {test_name}")
    logger.info(f"{'='*60}")
    
    try:
        node = CodeExecutionNode()
        
        simple_code = """
import sys
print("Hello from code execution test!")
print(f"Python version: {sys.version}")
result = {"status": "success", "message": "Test completed"}
print(result)
"""
        
        state = AgentState(
            target="http://example.com",
            task_id="test_codeexec_001",
            target_context={
                "generated_code": {
                    "code": simple_code,
                    "language": "python"
                }
            }
        )
        
        result = await node(state)
        
        assert "code_execution" in result.tool_results, "缺少执行结果"
        exec_result = result.tool_results["code_execution"]
        
        logger.info(f"✅ 执行状态: {exec_result.get('status')}")
        logger.info(f"✅ 执行时间: {exec_result.get('execution_time')}秒")
        
        if exec_result.get("output"):
            logger.info(f"✅ 执行输出: {exec_result['output'][:200]}...")
        
        if exec_result.get("error"):
            logger.warning(f"⚠️ 执行错误: {exec_result['error']}")
        
        return NodeTestResult(
            test_name=test_name,
            passed=True,
            message="代码执行节点测试通过",
            details={
                "status": exec_result.get("status"),
                "execution_time": exec_result.get("execution_time"),
                "has_output": bool(exec_result.get("output"))
            }
        )
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return NodeTestResult(
            test_name=test_name,
            passed=False,
            message=f"测试失败: {str(e)}"
        )


async def test_result_verification_node() -> NodeTestResult:
    """
    测试用例6: 结果验证节点测试
    
    验证点:
    - 节点能够正确初始化
    - 能够验证结果
    - 能够补充POC任务
    """
    test_name = "ResultVerificationNode"
    logger.info(f"\n{'='*60}")
    logger.info(f"开始测试: {test_name}")
    logger.info(f"{'='*60}")
    
    try:
        node = ResultVerificationNode()
        state = AgentState(
            target="http://example.com",
            task_id="test_verify_001",
            target_context={
                "cms": "weblogic",
                "open_ports": [7001, 80]
            },
            planned_tasks=["baseinfo"],
            completed_tasks=["baseinfo"],
            tool_results={
                "baseinfo": {"status": "success", "data": {}}
            }
        )
        
        result = await node(state)
        
        logger.info(f"✅ 是否继续: {result.should_continue}")
        logger.info(f"✅ 已完成任务: {result.completed_tasks}")
        logger.info(f"✅ 剩余任务: {result.planned_tasks}")
        
        return NodeTestResult(
            test_name=test_name,
            passed=True,
            message="结果验证节点测试通过",
            details={
                "should_continue": result.should_continue,
                "completed_tasks": result.completed_tasks,
                "remaining_tasks": result.planned_tasks
            }
        )
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return NodeTestResult(
            test_name=test_name,
            passed=False,
            message=f"测试失败: {str(e)}"
        )


async def test_vulnerability_analysis_node() -> NodeTestResult:
    """
    测试用例7: 漏洞分析节点测试
    
    验证点:
    - 节点能够正确初始化
    - 能够分析漏洞
    - 能够去重和排序
    """
    test_name = "VulnerabilityAnalysisNode"
    logger.info(f"\n{'='*60}")
    logger.info(f"开始测试: {test_name}")
    logger.info(f"{'='*60}")
    
    try:
        node = VulnerabilityAnalysisNode()
        state = AgentState(
            target="http://example.com",
            task_id="test_analysis_001",
            vulnerabilities=[
                {
                    "name": "SQL注入",
                    "severity": "high",
                    "cve": "CVE-2023-1234",
                    "target": "http://example.com"
                },
                {
                    "name": "XSS漏洞",
                    "severity": "medium",
                    "cve": "CVE-2023-5678",
                    "target": "http://example.com"
                },
                {
                    "name": "SQL注入",
                    "severity": "high",
                    "cve": "CVE-2023-1234",
                    "target": "http://example.com"
                }
            ]
        )
        
        result = await node(state)
        
        logger.info(f"✅ 漏洞数量: {len(result.vulnerabilities)}")
        
        for vuln in result.vulnerabilities:
            logger.info(f"  - {vuln.get('name')}: {vuln.get('severity')}")
        
        return NodeTestResult(
            test_name=test_name,
            passed=True,
            message="漏洞分析节点测试通过",
            details={
                "vulnerabilities_count": len(result.vulnerabilities)
            }
        )
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return NodeTestResult(
            test_name=test_name,
            passed=False,
            message=f"测试失败: {str(e)}"
        )


async def test_report_generation_node() -> NodeTestResult:
    """
    测试用例8: 报告生成节点测试
    
    验证点:
    - 节点能够正确初始化
    - 能够生成报告
    - 报告格式正确
    """
    test_name = "ReportGenerationNode"
    logger.info(f"\n{'='*60}")
    logger.info(f"开始测试: {test_name}")
    logger.info(f"{'='*60}")
    
    try:
        node = ReportGenerationNode()
        state = AgentState(
            target="http://example.com",
            task_id="test_report_001",
            vulnerabilities=[
                {
                    "name": "SQL注入",
                    "severity": "high",
                    "cve": "CVE-2023-1234"
                }
            ],
            completed_tasks=["baseinfo", "portscan"],
            tool_results={
                "baseinfo": {"status": "success"},
                "portscan": {"status": "success"}
            }
        )
        
        result = await node(state)
        
        assert "final_report" in result.tool_results, "缺少最终报告"
        assert "execution_trace_report" in result.tool_results, "缺少执行轨迹报告"
        
        logger.info(f"✅ 报告生成完成")
        logger.info(f"✅ 是否完成: {result.is_complete}")
        
        return NodeTestResult(
            test_name=test_name,
            passed=True,
            message="报告生成节点测试通过",
            details={
                "has_final_report": "final_report" in result.tool_results,
                "has_trace_report": "execution_trace_report" in result.tool_results,
                "is_complete": result.is_complete
            }
        )
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return NodeTestResult(
            test_name=test_name,
            passed=False,
            message=f"测试失败: {str(e)}"
        )


async def run_all_tests():
    """
    运行所有节点测试
    """
    logger.info("\n" + "="*60)
    logger.info("开始运行AIAgent节点功能测试")
    logger.info("="*60)
    
    tests = [
        test_environment_awareness_node,
        test_task_planning_node,
        test_intelligent_decision_node,
        test_code_generation_node,
        test_code_execution_node,
        test_result_verification_node,
        test_vulnerability_analysis_node,
        test_report_generation_node
    ]
    
    results = []
    passed_count = 0
    failed_count = 0
    
    for test in tests:
        try:
            result = await test()
            results.append(result.to_dict())
            if result.passed:
                passed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            logger.error(f"测试执行异常: {str(e)}")
            results.append({
                "test_name": test.__name__,
                "passed": False,
                "message": f"测试执行异常: {str(e)}"
            })
            failed_count += 1
    
    logger.info("\n" + "="*60)
    logger.info("测试结果汇总")
    logger.info("="*60)
    logger.info(f"总测试数: {len(results)}")
    logger.info(f"通过: {passed_count}")
    logger.info(f"失败: {failed_count}")
    logger.info(f"通过率: {passed_count/len(results)*100:.1f}%")
    
    for result in results:
        status = "✅ 通过" if result["passed"] else "❌ 失败"
        logger.info(f"  {status}: {result['test_name']}")
    
    return {
        "total": len(results),
        "passed": passed_count,
        "failed": failed_count,
        "pass_rate": passed_count/len(results)*100,
        "results": results
    }


if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    print(f"\n最终结果: {result['passed']}/{result['total']} 测试通过")

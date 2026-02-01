"""
AI Agent Web安全漏洞扫描综合测试

测试每个节点和工具的功能，验证AI Agent在Web安全漏洞扫描过程中的工作情况。
"""
import sys
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List

# 统一导入路径配置
sys.path.insert(0, str(Path(__file__).parent))

from ai_agents.core.state import AgentState
from ai_agents.core.graph import create_agent_graph, initialize_tools
from ai_agents.core.nodes import (
    EnvironmentAwarenessNode,
    TaskPlanningNode,
    IntelligentDecisionNode,
    ToolExecutionNode,
    CodeGenerationNode,
    CodeExecutionNode,
    CapabilityEnhancementNode,
    ResultVerificationNode,
    VulnerabilityAnalysisNode,
    ReportGenerationNode,
    SeebugAgentNode,
    POCVerificationNode
)
from ai_agents.tools.registry import registry


class AgentNodeTester:
    """AI Agent节点测试器"""
    
    def __init__(self):
        self.test_results = []
        self.graph = create_agent_graph()
    
    def log_test(self, test_name: str, status: str, details: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {test_name}: {status}")
        if details:
            print(f"   详情: {details}")
    
    def print_summary(self):
        """打印测试摘要"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.test_results if r["status"] == "SKIP")
        
        print("\n" + "="*60)
        print("测试摘要")
        print("="*60)
        print(f"总计: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"跳过: {skipped}")
        print(f"通过率: {passed/total*100:.1f}%" if total > 0 else "通过率: 0%")
        print("="*60)
        
        if failed > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test_name']}: {result['details']}")
    
    async def test_environment_awareness_node(self):
        """测试环境感知节点"""
        print("\n" + "="*60)
        print("测试1: 环境感知节点")
        print("="*60)
        
        try:
            node = EnvironmentAwarenessNode()
            state = AgentState(
                task_id="test_env_awareness",
                target="https://www.baidu.com"
            )
            
            result = await node(state)
            
            # 验证结果
            has_env_info = "environment_info" in result.target_context
            has_os_info = "os_system" in result.target_context
            has_python_version = "python_version" in result.target_context
            has_available_tools = "available_tools" in result.target_context
            has_execution_history = len(result.execution_history) > 0
            
            if all([has_env_info, has_os_info, has_python_version, has_available_tools, has_execution_history]):
                self.log_test(
                    "环境感知节点",
                    "PASS",
                    f"成功获取环境信息: OS={result.target_context.get('os_system')}, Python={result.target_context.get('python_version')}"
                )
            else:
                self.log_test(
                    "环境感知节点",
                    "FAIL",
                    f"缺少必要的环境信息: env_info={has_env_info}, os_info={has_os_info}, python_version={has_python_version}, available_tools={has_available_tools}, execution_history={has_execution_history}"
                )
            
        except Exception as e:
            self.log_test("环境感知节点", "FAIL", f"异常: {str(e)}")
    
    async def test_task_planning_node(self):
        """测试任务规划节点"""
        print("\n" + "="*60)
        print("测试2: 任务规划节点")
        print("="*60)
        
        try:
            node = TaskPlanningNode()
            state = AgentState(
                task_id="test_task_planning",
                target="https://www.baidu.com",
                target_context={
                    "environment_info": {},
                    "os_system": "Windows",
                    "python_version": "3.11"
                }
            )
            
            result = await node(state)
            
            # 验证结果
            has_planned_tasks = len(result.planned_tasks) > 0
            has_current_task = result.current_task is not None
            has_execution_history = len(result.execution_history) > 0
            
            if all([has_planned_tasks, has_current_task, has_execution_history]):
                self.log_test(
                    "任务规划节点",
                    "PASS",
                    f"成功规划任务: {result.planned_tasks}, 当前任务: {result.current_task}"
                )
            else:
                self.log_test(
                    "任务规划节点",
                    "FAIL",
                    f"任务规划失败: planned_tasks={has_planned_tasks}, current_task={has_current_task}, execution_history={has_execution_history}"
                )
            
        except Exception as e:
            self.log_test("任务规划节点", "FAIL", f"异常: {str(e)}")
    
    async def test_intelligent_decision_node(self):
        """测试智能决策节点"""
        print("\n" + "="*60)
        print("测试3: 智能决策节点")
        print("="*60)
        
        try:
            node = IntelligentDecisionNode()
            state = AgentState(
                task_id="test_intelligent_decision",
                target="https://www.baidu.com",
                target_context={
                    "environment_info": {},
                    "need_custom_scan": False,
                    "need_capability_enhancement": False,
                    "need_seebug_agent": False
                }
            )
            
            result = await node(state)
            
            # 验证结果
            has_execution_history = len(result.execution_history) > 0
            has_target_context = len(result.target_context) > 0
            
            if all([has_execution_history, has_target_context]):
                self.log_test(
                    "智能决策节点",
                    "PASS",
                    f"成功执行智能决策, 上下文更新: {list(result.target_context.keys())}"
                )
            else:
                self.log_test(
                    "智能决策节点",
                    "FAIL",
                    f"智能决策失败: execution_history={has_execution_history}, target_context={has_target_context}"
                )
            
        except Exception as e:
            self.log_test("智能决策节点", "FAIL", f"异常: {str(e)}")
    
    async def test_tool_execution_node(self):
        """测试工具执行节点"""
        print("\n" + "="*60)
        print("测试4: 工具执行节点")
        print("="*60)
        
        try:
            node = ToolExecutionNode()
            state = AgentState(
                task_id="test_tool_execution",
                target="https://www.baidu.com",
                planned_tasks=["baseinfo"],
                current_task="baseinfo"
            )
            
            result = await node(state)
            
            # 验证结果
            has_tool_results = "baseinfo" in result.tool_results
            has_completed_tasks = "baseinfo" in result.completed_tasks
            has_execution_history = len(result.execution_history) > 0
            
            if all([has_tool_results, has_completed_tasks, has_execution_history]):
                tool_result = result.tool_results.get("baseinfo", {})
                self.log_test(
                    "工具执行节点",
                    "PASS",
                    f"成功执行工具: baseinfo, 状态: {tool_result.get('status', 'unknown')}"
                )
            else:
                self.log_test(
                    "工具执行节点",
                    "FAIL",
                    f"工具执行失败: tool_results={has_tool_results}, completed_tasks={has_completed_tasks}, execution_history={has_execution_history}"
                )
            
        except Exception as e:
            self.log_test("工具执行节点", "FAIL", f"异常: {str(e)}")
    
    async def test_code_generation_node(self):
        """测试代码生成节点"""
        print("\n" + "="*60)
        print("测试5: 代码生成节点")
        print("="*60)
        
        try:
            node = CodeGenerationNode()
            state = AgentState(
                task_id="test_code_generation",
                target="https://www.baidu.com",
                target_context={
                    "need_custom_scan": True,
                    "scan_type": "sql_injection"
                }
            )
            
            result = await node(state)
            
            # 验证结果
            has_generated_code = "generated_code" in result.target_context
            has_tool_results = "code_generation" in result.tool_results
            has_execution_history = len(result.execution_history) > 0
            
            if all([has_generated_code, has_tool_results, has_execution_history]):
                generated_code = result.target_context.get("generated_code", {})
                self.log_test(
                    "代码生成节点",
                    "PASS",
                    f"成功生成代码: 语言={generated_code.get('language', 'unknown')}"
                )
            else:
                self.log_test(
                    "代码生成节点",
                    "FAIL",
                    f"代码生成失败: generated_code={has_generated_code}, tool_results={has_tool_results}, execution_history={has_execution_history}"
                )
            
        except Exception as e:
            self.log_test("代码生成节点", "FAIL", f"异常: {str(e)}")
    
    async def test_code_execution_node(self):
        """测试代码执行节点"""
        print("\n" + "="*60)
        print("测试6: 代码执行节点")
        print("="*60)
        
        try:
            node = CodeExecutionNode()
            state = AgentState(
                task_id="test_code_execution",
                target="https://www.baidu.com",
                target_context={
                    "generated_code": {
                        "code": "print('Hello, World!')",
                        "language": "python"
                    }
                }
            )
            
            result = await node(state)
            
            # 验证结果
            has_execution_result = "code_execution" in result.tool_results
            has_execution_history = len(result.execution_history) > 0
            
            if all([has_execution_result, has_execution_history]):
                execution_result = result.tool_results.get("code_execution", {})
                self.log_test(
                    "代码执行节点",
                    "PASS",
                    f"成功执行代码, 状态: {execution_result.get('status', 'unknown')}"
                )
            else:
                self.log_test(
                    "代码执行节点",
                    "FAIL",
                    f"代码执行失败: execution_result={has_execution_result}, execution_history={has_execution_history}"
                )
            
        except Exception as e:
            self.log_test("代码执行节点", "FAIL", f"异常: {str(e)}")
    
    async def test_capability_enhancement_node(self):
        """测试功能增强节点"""
        print("\n" + "="*60)
        print("测试7: 功能增强节点")
        print("="*60)
        
        try:
            node = CapabilityEnhancementNode()
            state = AgentState(
                task_id="test_capability_enhancement",
                target="https://www.baidu.com",
                target_context={
                    "need_capability_enhancement": True,
                    "capability_requirement": "安装requests库",
                    "capability_name": "http_requests"
                }
            )
            
            result = await node(state)
            
            # 验证结果
            has_enhancement_result = "capability_enhancement" in result.tool_results
            has_execution_history = len(result.execution_history) > 0
            need_enhancement_cleared = not result.target_context.get("need_capability_enhancement", False)
            
            if all([has_enhancement_result, has_execution_history, need_enhancement_cleared]):
                enhancement_result = result.tool_results.get("capability_enhancement", {})
                self.log_test(
                    "功能增强节点",
                    "PASS",
                    f"成功执行功能增强, 状态: {enhancement_result.get('status', 'unknown')}"
                )
            else:
                self.log_test(
                    "功能增强节点",
                    "FAIL",
                    f"功能增强失败: enhancement_result={has_enhancement_result}, execution_history={has_execution_history}, need_enhancement_cleared={need_enhancement_cleared}"
                )
            
        except Exception as e:
            self.log_test("功能增强节点", "FAIL", f"异常: {str(e)}")
    
    async def test_poc_verification_node(self):
        """测试POC验证节点"""
        print("\n" + "="*60)
        print("测试8: POC验证节点")
        print("="*60)
        
        try:
            node = POCVerificationNode()
            state = AgentState(
                task_id="test_poc_verification",
                target="https://www.baidu.com",
                poc_verification_tasks=[
                    {
                        "poc_name": "poc_weblogic_2020_2551",
                        "poc_id": "poc_cve_2020_2551",
                        "poc_code": "test_code",
                        "target": "https://www.baidu.com",
                        "priority": "high",
                        "status": "pending"
                    }
                ]
            )
            
            result = await node(state)
            
            # 验证结果
            has_verification_results = len(result.poc_verification_results) > 0
            has_execution_history = len(result.execution_history) > 0
            
            if all([has_verification_results, has_execution_history]):
                self.log_test(
                    "POC验证节点",
                    "PASS",
                    f"成功执行POC验证, 结果数: {len(result.poc_verification_results)}"
                )
            else:
                self.log_test(
                    "POC验证节点",
                    "FAIL",
                    f"POC验证失败: verification_results={has_verification_results}, execution_history={has_execution_history}"
                )
            
        except Exception as e:
            self.log_test("POC验证节点", "FAIL", f"异常: {str(e)}")
    
    async def test_complete_workflow(self):
        """测试完整工作流"""
        print("\n" + "="*60)
        print("测试9: 完整工作流")
        print("="*60)
        
        try:
            initial_state = AgentState(
                task_id="test_complete_workflow",
                target="https://www.baidu.com",
                target_context={}
            )
            
            start_time = time.time()
            final_state = await self.graph.invoke(initial_state)
            execution_time = time.time() - start_time
            
            # 处理返回值，可能是字典或对象
            if isinstance(final_state, dict):
                final_state = AgentState(**final_state)
            
            # 验证结果
            has_execution_history = len(final_state.execution_history) > 0
            has_tool_results = len(final_state.tool_results) > 0
            is_complete = final_state.is_complete
            
            if all([has_execution_history, has_tool_results, is_complete]):
                self.log_test(
                    "完整工作流",
                    "PASS",
                    f"成功执行完整工作流, 耗时: {execution_time:.2f}秒, 执行步骤: {len(final_state.execution_history)}, 工具结果: {len(final_state.tool_results)}"
                )
            else:
                self.log_test(
                    "完整工作流",
                    "FAIL",
                    f"完整工作流执行失败: execution_history={has_execution_history}, tool_results={has_tool_results}, is_complete={is_complete}"
                )
            
        except Exception as e:
            self.log_test("完整工作流", "FAIL", f"异常: {str(e)}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("AI Agent Web安全漏洞扫描综合测试")
        print("="*60)
        
        await self.test_environment_awareness_node()
        await self.test_task_planning_node()
        await self.test_intelligent_decision_node()
        await self.test_tool_execution_node()
        await self.test_code_generation_node()
        await self.test_code_execution_node()
        await self.test_capability_enhancement_node()
        await self.test_poc_verification_node()
        await self.test_complete_workflow()
        
        self.print_summary()


async def main():
    """主函数"""
    # 初始化工具注册表
    print("正在初始化工具注册表...")
    initialize_tools()
    print("工具注册表初始化完成\n")
    
    tester = AgentNodeTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

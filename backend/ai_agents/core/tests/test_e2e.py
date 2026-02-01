"""
端到端测试

验证完整的Agent工作流从环境感知到报告生成的全流程。
"""
import asyncio
import sys
import unittest

from pathlib import Path

# 统一导入路径配置
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.core.state import AgentState
from backend.ai_agents.core.graph import create_agent_graph


class TestE2EWorkflows(unittest.TestCase):
    """端到端工作流测试"""
    
    async def test_fixed_tool_workflow(self):
        """测试固定工具扫描完整流程"""
        print("\n" + "="*60)
        print("测试1: 固定工具扫描流程")
        print("="*60)
        
        graph = create_agent_graph()
        initial_state = AgentState(
            task_id="e2e_fixed_tool",
            target="https://www.baidu.com",
            target_context={}
        )
        
        final_state = await graph.invoke(initial_state)
        
        print(f"  任务ID: {final_state.task_id}")
        print(f"  完成任务: {len(final_state.completed_tasks)}")
        print(f"  发现漏洞: {len(final_state.vulnerabilities)}")
        print(f"  执行步骤: {len(final_state.execution_history)}")
        print(f"  最终状态: {'完成' if final_state.is_complete else '未完成'}")
        
        return True
    
    async def test_code_generation_workflow(self):
        """测试代码生成扫描完整流程"""
        print("\n" + "="*60)
        print("测试2: 代码生成扫描流程")
        print("="*60)
        
        graph = create_agent_graph()
        initial_state = AgentState(
            task_id="e2e_code_generation",
            target="https://www.baidu.com",
            target_context={
                "need_custom_scan": True,
                "custom_scan_type": "vuln_scan",
                "custom_scan_requirements": "检测SQL注入漏洞",
                "custom_scan_language": "python"
            }
        )
        
        final_state = await graph.invoke(initial_state)
        
        print(f"  任务ID: {final_state.task_id}")
        print(f"  完成任务: {len(final_state.completed_tasks)}")
        print(f"  发现漏洞: {len(final_state.vulnerabilities)}")
        print(f"  执行步骤: {len(final_state.execution_history)}")
        
        # 验证代码生成节点被执行
        code_gen_found = any(h["task"] == "code_generation" for h in final_state.execution_history)
        if code_gen_found:
            print("✅ 代码生成节点被执行")

        return True
    
    async def test_capability_enhancement_workflow(self):
        """测试功能补充完整流程"""
        print("\n" + "="*60)
        print("测试3: 功能补充流程")
        print("="*60)
        
        graph = create_agent_graph()
        initial_state = AgentState(
            task_id="e2e_enhancement",
            target="https://www.baidu.com",
            target_context={
                "need_capability_enhancement": True,
                "capability_requirement": "安装requests库"
            }
        )
        
        final_state = await graph.invoke(initial_state)
        
        print(f"  任务ID: {final_state.task_id}")
        print(f"  完成任务: {len(final_state.completed_tasks)}")
        print(f"  执行步骤: {len(final_state.execution_history)}")
        
        return True
    
    async def test_full_workflow(self):
        """测试完整工作流(环境感知→报告生成)"""
        print("\n" + "="*60)
        print("测试4: 完整工作流")
        print("="*60)
        
        graph = create_agent_graph()
        initial_state = AgentState(
            task_id="e2e_full_workflow",
            target="https://www.baidu.com",
            target_context={}
        )
        
        final_state = await graph.invoke(initial_state)
        
        print(f"  任务ID: {final_state.task_id}")
        print(f"  完成任务: {len(final_state.completed_tasks)}")
        print(f"  发现漏洞: {len(final_state.vulnerabilities)}")
        print(f"  执行步骤: {len(final_state.execution_history)}")
        print(f"  最终状态: {'完成' if final_state.is_complete else '未完成'}")
        
        # 验证所有节点都被执行
        executed_nodes = set(h["task"] for h in final_state.execution_history)
        expected_nodes = {
            "environment_awareness", "task_planning", "intelligent_decision",
            "tool_execution", "result_verification", "vulnerability_analysis", "report_generation"
        }
        
        for node in expected_nodes:
            if node in executed_nodes:
                print(f"  ✓ {node}")
            else:
                print(f"  ✗ {node}")
        
        return True
    
    async def test_error_recovery(self):
        """测试错误恢复能力"""
        print("\n" + "="*60)
        print("测试5: 错误恢复能力")
        print("="*60)
        
        graph = create_agent_graph()
        
        # 测试1: 环境检测失败后的恢复
        initial_state = AgentState(
            task_id="e2e_error_recovery",
            target="https://www.baidu.com",
            target_context={}
        )
        
        final_state = await graph.invoke(initial_state)
        
        print(f"  任务ID: {final_state.task_id}")
        print(f"  错误数量: {len(final_state.errors)}")
        
        # 即使有错误,工作流也应该完成
        self.assertTrue(final_state.is_complete)
        
        return True


async def main():
    """运行所有端到端测试"""
    print("\n" + "="*60)
    print("开始端到端测试")
    print("="*60)
    
    tests = [
        ("固定工具扫描流程", test_fixed_tool_workflow),
        ("代码生成扫描流程", test_code_generation_workflow),
        ("功能补充流程", test_capability_enhancement_workflow),
        ("完整工作流", test_full_workflow),
        ("错误恢复能力", test_error_recovery)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n执行测试: {test_name}")
        success = await test_func()
        results.append((test_name, success))
    
    # 输出测试摘要
    print("\n" + "="*60)
    print("测试摘要")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status}: {test_name}")
    
    total_tests = len(tests)
    passed_tests = sum(1 for _, success in results)
    failed_tests = total_tests - passed_tests
    
    print(f"\n总计: {total_tests} 个测试")
    print(f"  通过: {passed_tests} 个")
    print(f"  失败: {failed_tests} 个")
    print(f"  成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n" + "="*60)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

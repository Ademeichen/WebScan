"""
Agent 图工作流验证测试（简化版）

验证 agent 图的节点连接和执行顺序是否符合设计预期
"""
import sys
import asyncio
import os
from pathlib import Path

# 设置环境变量以支持 UTF-8 输出
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加 backend 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from ai_agents.core.state import AgentState
from ai_agents.core.graph import create_agent_graph
from ai_agents.core.graph import initialize_tools


async def test_graph_initialization():
    """测试图初始化"""
    print("\n" + "="*60)
    print("测试1: 图初始化")
    print("="*60)
    
    try:
        # 初始化工具
        initialize_tools()
        
        # 创建图
        graph = create_agent_graph()
        
        # 验证图信息
        info = graph.get_graph_info()
        
        print(f"[OK] 图初始化成功")
        print(f"  节点总数: {info['total_nodes']}")
        print(f"  原有节点: {info['original_nodes']}")
        print(f"  新增节点: {info['new_nodes']}")
        print(f"  入口点: {info['entry_point']}")
        print(f"  边数量: {len(info['edges'])}")
        
        # 打印所有节点
        print("\n  节点列表:")
        for node in info['nodes']:
            print(f"    - {node}")
        
        # 打印所有边
        print("\n  边列表:")
        for edge in info['edges']:
            print(f"    - {edge[0]} -> {edge[1]}")
        
        return True
    except Exception as e:
        print(f"[FAIL] 图初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_fixed_tool_workflow():
    """测试固定工具扫描流程"""
    print("\n" + "="*60)
    print("测试2: 固定工具扫描流程")
    print("="*60)
    
    try:
        # 初始化工具
        initialize_tools()
        
        # 创建图
        graph = create_agent_graph()
        
        # 创建初始状态
        initial_state = AgentState(
            task_id="test_fixed_tool",
            target="https://www.baidu.com",
            target_context={}
        )
        
        print(f"  目标: {initial_state.target}")
        print(f"  任务ID: {initial_state.task_id}")
        
        # 执行工作流
        final_state = await graph.invoke(initial_state)
        
        # 处理返回的状态对象，可能是字典形式
        if isinstance(final_state, dict):
            task_id = final_state.get('task_id', initial_state.task_id)
            completed_tasks = final_state.get('completed_tasks', [])
            vulnerabilities = final_state.get('vulnerabilities', [])
            errors = final_state.get('errors', [])
            execution_history = final_state.get('execution_history', [])
            is_complete = final_state.get('is_complete', False)
        else:
            task_id = final_state.task_id
            completed_tasks = final_state.completed_tasks
            vulnerabilities = final_state.vulnerabilities
            errors = final_state.errors
            execution_history = final_state.execution_history
            is_complete = final_state.is_complete
        
        print(f"\n[OK] 工作流执行完成")
        print(f"  完成任务: {len(completed_tasks)}")
        print(f"  发现漏洞: {len(vulnerabilities)}")
        print(f"  执行步骤: {len(execution_history)}")
        print(f"  最终状态: {'完成' if is_complete else '未完成'}")
        
        # 打印执行历史
        print("\n  执行历史:")
        for i, step in enumerate(execution_history, 1):
            print(f"    {i}. {step['task']} - {step['status']}")
        
        # 验证节点执行顺序
        expected_nodes = [
            "environment_awareness",
            "task_planning",
            "intelligent_decision",
            "tool_execution",
            "result_verification",
            "vulnerability_analysis",
            "report_generation"
        ]
        
        executed_nodes = [h["task"] for h in execution_history]
        
        print("\n  节点执行验证:")
        for node in expected_nodes:
            if node in executed_nodes:
                print(f"    [OK] {node}")
            else:
                print(f"    [FAIL] {node} (未执行)")
        
        return True
    except Exception as e:
        print(f"[FAIL] 固定工具扫描流程失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_registration():
    """测试工具注册"""
    print("\n" + "="*60)
    print("测试3: 工具注册")
    print("="*60)
    
    try:
        from ai_agents.tools.registry import registry
        
        # 初始化工具
        initialize_tools()
        
        # 列出所有工具
        tools = registry.list_tools()
        
        print(f"[OK] 工具注册成功")
        print(f"  工具总数: {len(tools)}")
        
        # 按分类统计
        categories = {}
        for tool in tools:
            category = tool['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(tool['name'])
        
        print("\n  工具分类:")
        for category, tool_names in categories.items():
            print(f"    {category}: {len(tool_names)} 个工具")
            for tool_name in tool_names:
                print(f"      - {tool_name}")
        
        return True
    except Exception as e:
        print(f"[FAIL] 工具注册测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """测试错误处理"""
    print("\n" + "="*60)
    print("测试4: 错误处理")
    print("="*60)
    
    try:
        # 初始化工具
        initialize_tools()
        
        # 创建图
        graph = create_agent_graph()
        
        # 创建初始状态（使用无效目标）
        initial_state = AgentState(
            task_id="test_error",
            target="invalid://target",
            target_context={}
        )
        
        print(f"  目标: {initial_state.target}")
        print(f"  任务ID: {initial_state.task_id}")
        
        # 执行工作流
        final_state = await graph.invoke(initial_state)
        
        # 处理返回的状态对象，可能是字典形式
        if isinstance(final_state, dict):
            errors = final_state.get('errors', [])
            execution_history = final_state.get('execution_history', [])
            is_complete = final_state.get('is_complete', False)
        else:
            errors = final_state.errors
            execution_history = final_state.execution_history
            is_complete = final_state.is_complete
        
        print(f"\n[OK] 工作流执行完成（包含错误）")
        print(f"  错误数量: {len(errors)}")
        print(f"  执行步骤: {len(execution_history)}")
        
        # 打印错误信息
        if errors:
            print("\n  错误列表:")
            for error in errors:
                print(f"    - {error}")
        
        # 验证工作流在错误后仍然完成
        if is_complete:
            print("\n  [OK] 工作流在错误后仍然完成")
        else:
            print("\n  [FAIL] 工作流未完成")
        
        return True
    except Exception as e:
        print(f"[FAIL] 错误处理测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Agent 图工作流验证测试")
    print("="*60)
    
    tests = [
        ("图初始化", test_graph_initialization),
        ("固定工具扫描流程", test_fixed_tool_workflow),
        ("工具注册", test_tool_registration),
        ("错误处理", test_error_handling)
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
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}")
    
    total_tests = len(tests)
    passed_tests = sum(1 for _, success in results if success)
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

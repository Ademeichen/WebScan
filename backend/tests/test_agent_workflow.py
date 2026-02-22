#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI Agent工作流验证测试脚本
验证所有核心组件是否正常初始化和工作
"""
import sys
import os
import asyncio

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.dirname(backend_dir))

def test_imports():
    """测试所有关键模块导入"""
    print("=" * 60)
    print("1. 测试模块导入")
    print("=" * 60)
    
    modules_to_test = [
        ("backend.ai_agents.core.graph", "ScanAgentGraph"),
        ("backend.ai_agents.core.nodes", "所有节点"),
        ("backend.ai_agents.tools.registry", "ToolRegistry"),
        ("backend.ai_agents.code_execution.environment", "EnvironmentAwareness"),
        ("backend.ai_agents.code_execution.code_generator", "LLMCodeGenerator"),
        ("backend.ai_agents.code_execution.capability_enhancer", "CapabilityEnhancer"),
        ("backend.ai_agents.code_execution.executor", "UnifiedExecutor"),
        ("backend.ai_agents.analyzers.vuln_analyzer", "VulnerabilityAnalyzer"),
        ("backend.ai_agents.analyzers.report_gen", "ReportGenerator"),
        ("backend.ai_agents.poc_system.poc_manager", "POCManager"),
        ("backend.ai_agents.poc_system.verification_engine", "VerificationEngine"),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, component in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name} - {component}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {module_name} - {component}: {e}")
            failed += 1
    
    print(f"\n导入测试结果: {passed}/{len(modules_to_test)} 通过")
    return failed == 0

def test_tool_registry():
    """测试工具注册表"""
    print("\n" + "=" * 60)
    print("2. 测试工具注册表")
    print("=" * 60)
    
    try:
        from backend.ai_agents.tools.registry import ToolRegistry, tool_registry
        
        tools = tool_registry.list_tools()
        print(f"  已注册工具数量: {len(tools)}")
        
        categories = {}
        for tool in tools:
            cat = tool.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool.get('name'))
        
        print("\n  工具分类:")
        for cat, tool_names in categories.items():
            print(f"    - {cat}: {len(tool_names)} 个工具")
            for name in tool_names[:5]:
                print(f"        • {name}")
            if len(tool_names) > 5:
                print(f"        ... 还有 {len(tool_names) - 5} 个")
        
        return True
    except Exception as e:
        print(f"  ❌ 工具注册表测试失败: {e}")
        return False

def test_graph_structure():
    """测试图结构"""
    print("\n" + "=" * 60)
    print("3. 测试LangGraph图结构")
    print("=" * 60)
    
    try:
        from backend.ai_agents.core.graph import ScanAgentGraph
        
        graph = ScanAgentGraph()
        
        nodes = graph.get_nodes()
        print(f"  节点数量: {len(nodes)}")
        print("  节点列表:")
        for node in nodes:
            print(f"    • {node}")
        
        return True
    except Exception as e:
        print(f"  ❌ 图结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_poc_system():
    """测试POC系统"""
    print("\n" + "=" * 60)
    print("4. 测试POC验证系统")
    print("=" * 60)
    
    try:
        from backend.ai_agents.poc_system.poc_manager import poc_manager
        from backend.ai_agents.poc_system.verification_engine import verification_engine
        
        pocs = poc_manager.list_pocs()
        print(f"  已加载POC数量: {len(pocs)}")
        
        if pocs:
            print("  示例POC:")
            for poc in pocs[:5]:
                print(f"    • {poc}")
        
        return True
    except Exception as e:
        print(f"  ❌ POC系统测试失败: {e}")
        return False

def test_code_execution():
    """测试代码执行环境"""
    print("\n" + "=" * 60)
    print("5. 测试代码执行环境")
    print("=" * 60)
    
    try:
        from backend.ai_agents.code_execution.executor import UnifiedExecutor
        from backend.ai_agents.code_execution.code_generator import LLMCodeGenerator
        
        executor = UnifiedExecutor(timeout=30, sandbox=True)
        print(f"  ✅ 统一执行器初始化成功 (timeout=30s, sandbox=True)")
        
        code_gen = LLMCodeGenerator()
        print(f"  ✅ LLM代码生成器初始化成功")
        
        return True
    except Exception as e:
        print(f"  ❌ 代码执行环境测试失败: {e}")
        return False

def test_analyzers():
    """测试分析器"""
    print("\n" + "=" * 60)
    print("6. 测试漏洞分析和报告生成器")
    print("=" * 60)
    
    try:
        from backend.ai_agents.analyzers.vuln_analyzer import VulnerabilityAnalyzer
        from backend.ai_agents.analyzers.report_gen import ReportGenerator
        
        vuln_analyzer = VulnerabilityAnalyzer()
        print(f"  ✅ 漏洞分析器初始化成功")
        
        report_gen = ReportGenerator()
        print(f"  ✅ 报告生成器初始化成功")
        
        return True
    except Exception as e:
        print(f"  ❌ 分析器测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("AI Agent工作流验证测试")
    print("=" * 60)
    
    results = []
    
    results.append(("模块导入", test_imports()))
    results.append(("工具注册表", test_tool_registry()))
    results.append(("图结构", test_graph_structure()))
    results.append(("POC系统", test_poc_system()))
    results.append(("代码执行环境", test_code_execution()))
    results.append(("分析器", test_analyzers()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有AI Agent工作流组件验证通过！")
        return 0
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())

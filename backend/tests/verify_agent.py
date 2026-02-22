#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.dirname(backend_dir))

print("=" * 60)
print("AI Agent Workflow Verification")
print("=" * 60)

# 1. Test module imports
print("\n1. Testing module imports...")
try:
    from backend.ai_agents.core.graph import ScanAgentGraph
    from backend.ai_agents.core import nodes
    from backend.ai_agents.tools.registry import tool_registry
    print("   [PASS] Core modules imported successfully")
except Exception as e:
    print(f"   [FAIL] Import failed: {e}")

# 2. Test tool registry
print("\n2. Testing tool registry...")
try:
    tools = tool_registry.list_tools()
    print(f"   [PASS] Registered {len(tools)} tools")
    categories = set(t.get("category") for t in tools)
    print(f"   Categories: {categories}")
except Exception as e:
    print(f"   [FAIL] Tool registry test failed: {e}")

# 3. Test graph structure
print("\n3. Testing LangGraph structure...")
try:
    graph = ScanAgentGraph()
    nodes_list = graph.get_nodes()
    print(f"   [PASS] Graph nodes count: {len(nodes_list)}")
    print(f"   Nodes: {nodes_list}")
except Exception as e:
    print(f"   [FAIL] Graph structure test failed: {e}")

# 4. Test POC system
print("\n4. Testing POC system...")
try:
    from backend.ai_agents.poc_system.poc_manager import poc_manager
    pocs = poc_manager.list_pocs()
    print(f"   [PASS] Loaded {len(pocs)} POCs")
except Exception as e:
    print(f"   [FAIL] POC system test failed: {e}")

# 5. Test code execution environment
print("\n5. Testing code execution environment...")
try:
    from backend.ai_agents.code_execution.executor import UnifiedExecutor
    from backend.ai_agents.code_execution.code_generator import LLMCodeGenerator
    executor = UnifiedExecutor(timeout=30, sandbox=True)
    code_gen = LLMCodeGenerator()
    print("   [PASS] Code execution environment initialized")
except Exception as e:
    print(f"   [FAIL] Code execution environment test failed: {e}")

# 6. Test analyzers
print("\n6. Testing analyzers...")
try:
    from backend.ai_agents.analyzers.vuln_analyzer import VulnerabilityAnalyzer
    from backend.ai_agents.analyzers.report_gen import ReportGenerator
    vuln_analyzer = VulnerabilityAnalyzer()
    report_gen = ReportGenerator()
    print("   [PASS] Analyzers initialized")
except Exception as e:
    print(f"   [FAIL] Analyzers test failed: {e}")

print("\n" + "=" * 60)
print("AI Agent Workflow Verification Complete!")
print("=" * 60)

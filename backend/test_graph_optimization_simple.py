"""
简单的图结构优化测试脚本
"""
import sys
import asyncio
import time
from pathlib import Path

# 设置路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from ai_agents.core.graph import create_agent_graph, initialize_tools
from ai_agents.tools.registry import registry

print("=" * 60)
print("图结构优化验证")
print("=" * 60)

print("\n1. 初始化工具...")
initialize_tools()
print(f"   ✅ 工具初始化完成，共 {len(registry.tools)} 个工具")

print("\n2. 列出所有注册的工具...")
all_tools = registry.list_tools()
plugins = [t for t in all_tools if t.get("category") == "plugin"]
pocs = [t for t in all_tools if t.get("category") == "poc"]

print(f"   插件数量: {len(plugins)}")
print(f"   POC数量: {len(pocs)}")
print(f"   插件列表: {[t['name'] for t in plugins]}")

print("\n3. 创建图实例...")
graph = create_agent_graph()
print("   ✅ 图实例创建完成")

print("\n4. 测试图编译...")
try:
    compiled_graph = graph.compile()
    print("   ✅ 完整图编译成功")
except Exception as e:
    print(f"   ❌ 完整图编译失败: {str(e)}")

print("\n5. 测试子图编译...")
try:
    info_graph = graph.compile_info_collection()
    print("   ✅ 信息收集子图编译成功")
    
    scan_graph = graph.compile_vulnerability_scan()
    print("   ✅ 漏洞扫描子图编译成功")
    
    analysis_graph = graph.compile_result_analysis()
    print("   ✅ 结果分析子图编译成功")
except Exception as e:
    print(f"   ❌ 子图编译失败: {str(e)}")

print("\n" + "=" * 60)
print("验证完成！")
print("=" * 60)
print("\n总结:")
print(f"- 插件数量: {len(plugins)} (期望: 14个)")
print(f"- POC数量: {len(pocs)}")
print(f"- 图结构: 完整图 + 3个子图")
print("=" * 60)

"""
测试工具注册表和工具调用
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from ai_agents.core.graph import ScanAgentGraph
from ai_agents.tools.registry import registry

print("=" * 80)
print("工具注册表测试")
print("=" * 80)

# 创建图实例，这会触发工具初始化
print("\n创建ScanAgentGraph实例...")
graph = ScanAgentGraph()
print("✅ ScanAgentGraph实例创建完成")

# 获取工具统计信息
stats = registry.get_stats()
print(f"\n工具统计:")
print(f"  总工具数: {stats['total_tools']}")
print(f"  按分类: {stats['by_category']}")

# 列出所有工具
all_tools = registry.list_tools()
print(f"\n所有工具列表:")
if all_tools:
    for tool_name in all_tools:
        metadata = registry.get_tool_metadata(tool_name)
        if metadata:
            print(f"  - {tool_name}")
            print(f"    描述: {metadata.get('description', 'N/A')}")
            print(f"    分类: {metadata.get('category', 'N/A')}")
            print(f"    优先级: {metadata.get('priority', 'N/A')}")
            print(f"    超时: {metadata.get('timeout', 'N/A')}秒")
else:
    print("  ⚠️ 没有注册任何工具")

# 测试工具调用
print("\n" + "=" * 80)
print("测试工具调用")
print("=" * 80)

if all_tools:
    test_tool = all_tools[0]
    print(f"\n尝试调用工具: {test_tool}")
    
    try:
        result = registry.call_tool(test_tool, "https://www.baidu.com")
        print(f"✅ 工具调用成功")
        print(f"  状态: {result.get('status')}")
        print(f"  数据: {result.get('data')}")
    except Exception as e:
        print(f"❌ 工具调用失败: {str(e)}")
else:
    print("⚠️ 没有可用的工具进行测试")

print("\n" + "=" * 80)
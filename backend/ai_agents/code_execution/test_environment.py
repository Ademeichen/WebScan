"""
简单的功能测试脚本
"""
import sys
import os
from pathlib import Path

# 统一导入路径配置
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.code_execution.environment import EnvironmentAwareness

print("="*60)
print("环境感知模块功能测试")
print("="*60)

try:
    print("\n1. 测试初始化...")
    env = EnvironmentAwareness()
    print("   ✅ 初始化成功")
    
    print("\n2. 测试操作系统检测...")
    os_info = env.os_info
    print(f"   系统: {os_info['system']} {os_info['release']}")
    print("   ✅ 操作系统检测成功")
    
    print("\n3. 测试Python检测...")
    python_info = env.python_info
    print(f"   版本: {python_info['version']}")
    print(f"   可执行文件: {python_info['executable']}")
    print("   ✅ Python检测成功")
    
    print("\n4. 测试工具检测...")
    tools = env.available_tools
    available_count = sum(1 for t in tools.values() if t.get('available'))
    print(f"   检测到 {len(tools)} 个工具，其中 {available_count} 个可用")
    for tool_name, tool_info in tools.items():
        status = "✓" if tool_info['available'] else "✗"
        print(f"   {status} {tool_name}: {tool_info.get('version', 'unknown')}")
    print("   ✅ 工具检测成功")
    
    print("\n5. 测试网络检测...")
    network = env.network_info
    print(f"   主机名: {network['hostname']}")
    print(f"   代理: {'是' if network['proxy_detected'] else '否'}")
    print(f"   防火墙: {'是' if network['firewall_detected'] else '否'}")
    print(f"   网络: {'在线' if network['internet_available'] else '离线'}")
    print("   ✅ 网络检测成功")
    
    print("\n6. 测试资源检测...")
    resources = env.system_resources
    print(f"   磁盘总空间: {resources['disk_total'] / (1024**3):.2f}GB")
    print(f"   磁盘已用: {resources['disk_used'] / (1024**3):.2f}GB")
    print(f"   磁盘可用: {resources['disk_free'] / (1024**3):.2f}GB")
    print(f"   使用率: {resources['disk_used_percent']:.1f}%")
    print("   ✅ 资源检测成功")
    
    print("\n7. 测试环境报告...")
    report = env.get_environment_report()
    print(f"   报告包含 {len(report)} 个部分")
    print(f"   扫描建议: {len(report['scan_recommendations'])} 条")
    print("   ✅ 环境报告生成成功")
    
    print("\n8. 测试工具可用性检查...")
    nmap_available = env.is_tool_available('nmap')
    print(f"   nmap可用: {nmap_available}")
    print("   ✅ 工具可用性检查成功")
    
    print("\n9. 测试Python版本获取...")
    version = env.get_python_version()
    print(f"   Python版本: {version}")
    print("   ✅ Python版本获取成功")
    
    print("\n10. 测试初始化状态...")
    is_init = env.is_initialized()
    error = env.get_init_error()
    print(f"   已初始化: {is_init}")
    print(f"   初始化错误: {error}")
    print("   ✅ 初始化状态检查成功")
    
    print("\n" + "="*60)
    print("✅ 所有测试通过！")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

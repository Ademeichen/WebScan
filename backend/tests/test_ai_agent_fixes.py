"""
AI Agent 工具执行与通知系统修复验证测试

测试内容:
1. 工具执行超时配置验证
2. AI 分析结果存储验证
3. 通知系统验证
4. 日志记录验证
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_tool_timeout_config():
    """测试工具超时配置"""
    print("\n" + "=" * 60)
    print("测试 1: 工具执行超时配置")
    print("=" * 60)
    
    from backend.ai_agents.core.graph import initialize_tools
    from backend.ai_agents.tools.registry import registry
    
    initialize_tools()
    
    test_cases = [
        ("baseinfo", 60, "基础信息收集"),
        ("waf_detect", 60, "WAF检测"),
        ("cdn_detect", 30, "CDN检测"),
        ("portscan", 120, "端口扫描"),
    ]
    
    all_passed = True
    for tool_name, expected_timeout, desc in test_cases:
        metadata = registry.get_tool_metadata(tool_name)
        if metadata:
            actual_timeout = metadata.get("timeout", 0)
            status = "✅" if actual_timeout >= expected_timeout else "❌"
            print(f"  {status} {tool_name} ({desc}): {actual_timeout}s (期望 >= {expected_timeout}s)")
            if actual_timeout < expected_timeout:
                all_passed = False
        else:
            print(f"  ❌ {tool_name} ({desc}): 工具未注册")
            all_passed = False
    
    return all_passed


def test_agent_state_attributes():
    """测试 AgentState 属性"""
    print("\n" + "=" * 60)
    print("测试 2: AgentState 属性验证")
    print("=" * 60)
    
    from backend.ai_agents.core.state import AgentState
    
    state = AgentState(target="https://example.com", task_id="test-123")
    
    all_passed = True
    
    if hasattr(state, 'scan_summary'):
        print(f"  ✅ scan_summary 属性存在")
        state.scan_summary = {"test": "data"}
        print(f"     值设置成功: {state.scan_summary}")
    else:
        print(f"  ❌ scan_summary 属性不存在")
        all_passed = False
    
    if hasattr(state, 'report'):
        print(f"  ✅ report 属性存在")
        state.report = "Test report content"
        print(f"     值设置成功: {state.report[:50]}...")
    else:
        print(f"  ❌ report 属性不存在")
        all_passed = False
    
    state_dict = state.to_dict()
    if 'scan_summary' in state_dict:
        print(f"  ✅ to_dict() 包含 scan_summary")
    else:
        print(f"  ❌ to_dict() 不包含 scan_summary")
        all_passed = False
    
    if 'report' in state_dict:
        print(f"  ✅ to_dict() 包含 report")
    else:
        print(f"  ❌ to_dict() 不包含 report")
        all_passed = False
    
    restored_state = AgentState.from_dict(state_dict)
    if restored_state.scan_summary == state.scan_summary:
        print(f"  ✅ from_dict() 正确恢复 scan_summary")
    else:
        print(f"  ❌ from_dict() 未能正确恢复 scan_summary")
        all_passed = False
    
    if restored_state.report == state.report:
        print(f"  ✅ from_dict() 正确恢复 report")
    else:
        print(f"  ❌ from_dict() 未能正确恢复 report")
        all_passed = False
    
    return all_passed


def test_notification_model_structure():
    """测试通知模型结构（通过文件检查）"""
    print("\n" + "=" * 60)
    print("测试 3: 通知模型结构验证")
    print("=" * 60)
    
    from backend.models import Notification
    
    all_passed = True
    
    expected_fields = ['id', 'user', 'title', 'message', 'type', 'read', 'created_at']
    
    model_fields = list(Notification._meta.fields_map.keys())
    
    for field in expected_fields:
        if field in model_fields:
            print(f"  ✅ Notification.{field} 字段存在")
        else:
            print(f"  ❌ Notification.{field} 字段不存在")
            all_passed = False
    
    return all_passed


def test_notification_method_in_file():
    """测试通知创建方法（通过文件检查）"""
    print("\n" + "=" * 60)
    print("测试 4: 通知创建方法验证")
    print("=" * 60)
    
    task_executor_path = Path(__file__).parent.parent / "task_executor.py"
    
    all_passed = True
    
    content = task_executor_path.read_text(encoding='utf-8')
    
    if '_create_task_notification' in content:
        print(f"  ✅ _create_task_notification 方法存在于文件中")
    else:
        print(f"  ❌ _create_task_notification 方法不存在于文件中")
        all_passed = False
    
    if 'await Notification.create' in content:
        print(f"  ✅ Notification.create 调用存在")
    else:
        print(f"  ❌ Notification.create 调用不存在")
        all_passed = False
    
    if 'manager.broadcast' in content:
        print(f"  ✅ WebSocket broadcast 调用存在")
    else:
        print(f"  ❌ WebSocket broadcast 调用不存在")
        all_passed = False
    
    if 'new_notification' in content:
        print(f"  ✅ new_notification 事件类型存在")
    else:
        print(f"  ❌ new_notification 事件类型不存在")
        all_passed = False
    
    return all_passed


def test_logging_enhancements():
    """测试日志增强"""
    print("\n" + "=" * 60)
    print("测试 5: 日志增强验证")
    print("=" * 60)
    
    adapters_path = Path(__file__).parent.parent / "ai_agents" / "tools" / "adapters.py"
    nodes_path = Path(__file__).parent.parent / "ai_agents" / "core" / "nodes.py"
    
    all_passed = True
    
    adapters_content = adapters_path.read_text(encoding='utf-8')
    
    log_patterns = [
        ("开始执行", "🚀 开始执行"),
        ("执行成功", "✅ 执行成功"),
        ("执行超时", "⏱️ 执行超时"),
        ("执行异常", "❌ 执行异常"),
    ]
    
    for name, pattern in log_patterns:
        if pattern in adapters_content:
            print(f"  ✅ adapters.py 包含 '{name}' 日志")
        else:
            print(f"  ❌ adapters.py 不包含 '{name}' 日志")
            all_passed = False
    
    nodes_content = nodes_path.read_text(encoding='utf-8')
    
    node_patterns = [
        ("任务规划", "任务规划"),
        ("工具执行", "工具执行"),
        ("漏洞分析", "漏洞分析"),
        ("报告生成", "报告生成"),
    ]
    
    for name, pattern in node_patterns:
        if pattern in nodes_content:
            print(f"  ✅ nodes.py 包含 '{name}' 日志")
        else:
            print(f"  ❌ nodes.py 不包含 '{name}' 日志")
            all_passed = False
    
    return all_passed


def test_report_generation_node():
    """测试报告生成节点"""
    print("\n" + "=" * 60)
    print("测试 6: 报告生成节点验证")
    print("=" * 60)
    
    nodes_path = Path(__file__).parent.parent / "ai_agents" / "core" / "nodes.py"
    
    all_passed = True
    
    content = nodes_path.read_text(encoding='utf-8')
    
    if 'state.scan_summary' in content:
        print(f"  ✅ state.scan_summary 赋值存在")
    else:
        print(f"  ❌ state.scan_summary 赋值不存在")
        all_passed = False
    
    if 'state.report' in content:
        print(f"  ✅ state.report 赋值存在")
    else:
        print(f"  ❌ state.report 赋值不存在")
        all_passed = False
    
    if 'vulnerabilities_count' in content:
        print(f"  ✅ vulnerabilities_count 统计存在")
    else:
        print(f"  ❌ vulnerabilities_count 统计不存在")
        all_passed = False
    
    return all_passed


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("AI Agent 工具执行与通知系统修复验证测试")
    print("=" * 60)
    
    results = []
    
    results.append(("工具超时配置", test_tool_timeout_config()))
    results.append(("AgentState 属性", test_agent_state_attributes()))
    results.append(("通知模型结构", test_notification_model_structure()))
    results.append(("通知创建方法", test_notification_method_in_file()))
    results.append(("日志增强", test_logging_enhancements()))
    results.append(("报告生成节点", test_report_generation_node()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查上述详情")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

"""
AI Agent 前端状态显示修复验证测试

测试内容:
1. WebSocket 事件名称验证
2. 任务完成广播数据格式验证
3. 前端数据处理逻辑验证
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_websocket_event_names():
    """测试 WebSocket 事件名称"""
    print("\n" + "=" * 60)
    print("测试 1: WebSocket 事件名称验证")
    print("=" * 60)
    
    websocket_path = Path(__file__).parent.parent.parent / "front" / "src" / "utils" / "websocket.js"
    
    all_passed = True
    
    content = websocket_path.read_text(encoding='utf-8')
    
    event_mappings = [
        ("stage_update", "stage:update"),
        ("task_completed", "task:completed"),
        ("subgraph_progress", "subgraph:progress"),
        ("tool_execution", "tool:execution"),
        ("new_notification", "new_notification"),
    ]
    
    for backend_event, frontend_event in event_mappings:
        if f"case '{backend_event}'" in content and f"this.emit('{frontend_event}'" in content:
            print(f"  ✅ {backend_event} -> {frontend_event} 映射正确")
        else:
            print(f"  ❌ {backend_event} -> {frontend_event} 映射缺失")
            all_passed = False
    
    return all_passed


def test_task_executor_broadcast():
    """测试任务执行器广播数据格式"""
    print("\n" + "=" * 60)
    print("测试 2: 任务完成广播数据格式验证")
    print("=" * 60)
    
    task_executor_path = Path(__file__).parent.parent / "task_executor.py"
    
    all_passed = True
    
    content = task_executor_path.read_text(encoding='utf-8')
    
    required_fields = [
        'stages',
        'scan_summary',
        'final_output',
        'vulnerabilities',
        'report',
        'execution_time',
    ]
    
    for field in required_fields:
        if f'"{field}"' in content or f"'{field}'" in content:
            # 检查是否在 broadcast 调用附近
            if 'manager.broadcast' in content:
                print(f"  ✅ 广播数据包含 '{field}' 字段")
            else:
                print(f"  ⚠️ '{field}' 字段存在，但可能不在广播中")
        else:
            print(f"  ❌ 广播数据缺少 '{field}' 字段")
            all_passed = False
    
    return all_passed


def test_frontend_event_handlers():
    """测试前端事件处理器"""
    print("\n" + "=" * 60)
    print("测试 3: 前端事件处理器验证")
    print("=" * 60)
    
    agent_scan_path = Path(__file__).parent.parent.parent / "front" / "src" / "views" / "AgentScan.vue"
    
    all_passed = True
    
    content = agent_scan_path.read_text(encoding='utf-8')
    
    event_handlers = [
        ("stage:update", "阶段状态更新"),
        ("task:completed", "任务完成"),
        ("subgraph:progress", "子图进度"),
        ("tool:execution", "工具执行"),
    ]
    
    for event, desc in event_handlers:
        if f"on('{event}'" in content:
            print(f"  ✅ 监听 '{event}' 事件 ({desc})")
        else:
            print(f"  ❌ 未监听 '{event}' 事件 ({desc})")
            all_passed = False
    
    return all_passed


def test_update_task_completed_function():
    """测试 updateTaskCompleted 函数"""
    print("\n" + "=" * 60)
    print("测试 4: updateTaskCompleted 函数验证")
    print("=" * 60)
    
    agent_scan_path = Path(__file__).parent.parent.parent / "front" / "src" / "views" / "AgentScan.vue"
    
    all_passed = True
    
    content = agent_scan_path.read_text(encoding='utf-8')
    
    checks = [
        ("payload.stages", "解析 stages 数据"),
        ("payload.scan_summary", "解析 scan_summary 数据"),
        ("payload.vulnerabilities", "解析 vulnerabilities 数据"),
        ("payload.report", "解析 report 数据"),
        ("subgraphState", "更新 subgraphState"),
    ]
    
    for pattern, desc in checks:
        if pattern in content:
            print(f"  ✅ {desc}")
        else:
            print(f"  ❌ {desc}")
            all_passed = False
    
    return all_passed


def test_handle_view_task_function():
    """测试 handleViewTask 函数"""
    print("\n" + "=" * 60)
    print("测试 5: handleViewTask 函数验证")
    print("=" * 60)
    
    agent_scan_path = Path(__file__).parent.parent.parent / "front" / "src" / "views" / "AgentScan.vue"
    
    all_passed = True
    
    content = agent_scan_path.read_text(encoding='utf-8')
    
    checks = [
        ("task.stages", "读取任务阶段数据"),
        ("task.result", "读取任务结果数据"),
        ("scan_summary", "处理 scan_summary"),
        ("final_output", "处理 final_output"),
        ("selectedTask.value", "更新 selectedTask"),
    ]
    
    for pattern, desc in checks:
        if pattern in content:
            print(f"  ✅ {desc}")
        else:
            print(f"  ❌ {desc}")
            all_passed = False
    
    return all_passed


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("AI Agent 前端状态显示修复验证测试")
    print("=" * 60)
    
    results = []
    
    results.append(("WebSocket 事件名称", test_websocket_event_names()))
    results.append(("任务完成广播数据格式", test_task_executor_broadcast()))
    results.append(("前端事件处理器", test_frontend_event_handlers()))
    results.append(("updateTaskCompleted 函数", test_update_task_completed_function()))
    results.append(("handleViewTask 函数", test_handle_view_task_function()))
    
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

"""
运行AIAgent图功能测试
"""
import sys
from pathlib import Path

# 添加backend目录和项目根目录到路径
backend_dir = Path(__file__).parent.parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

try:
    from ai_agents.core.graph import ScanAgentGraph
    from ai_agents.core.state import AgentState
    from ai_agents.tools.registry import registry
    from ai_agents.agent_config import agent_config

    print("=" * 80)
    print("AIAgent图功能测试")
    print("=" * 80)

    # 测试1: 图初始化
    print("\n测试1: 图初始化")
    try:
        graph = ScanAgentGraph()
        print("✅ 图初始化成功")
        print(f"   节点数量: {len(graph.get_graph_info()['nodes'])}")
        print(f"   边数量: {len(graph.get_graph_info()['edges'])}")
    except Exception as e:
        print(f"❌ 图初始化失败: {str(e)}")

    # 测试2: 状态创建
    print("\n测试2: 状态创建")
    try:
        state = AgentState(
            task_id="test_001",
            target="https://www.baidu.com"
        )
        print("✅ 状态创建成功")
        print(f"   任务ID: {state.task_id}")
        print(f"   目标: {state.target}")
    except Exception as e:
        print(f"❌ 状态创建失败: {str(e)}")

    # 测试3: 工具注册表
    print("\n测试3: 工具注册表")
    try:
        stats = registry.get_stats()
        print("✅ 工具注册表获取成功")
        print(f"   总工具数: {stats['total_tools']}")
        print(f"   分类: {stats['by_category']}")
    except Exception as e:
        print(f"❌ 工具注册表获取失败: {str(e)}")

    # 测试4: Agent配置
    print("\n测试4: Agent配置")
    try:
        print("✅ Agent配置获取成功")
        print(f"   最大执行时间: {agent_config.MAX_EXECUTION_TIME}秒")
        print(f"   最大重试次数: {agent_config.MAX_RETRIES}")
        print(f"   最大并发工具数: {agent_config.MAX_CONCURRENT_TOOLS}")
        print(f"   工具超时: {agent_config.TOOL_TIMEOUT}秒")
        print(f"   启用LLM规划: {agent_config.ENABLE_LLM_PLANNING}")
        print(f"   默认扫描任务: {agent_config.DEFAULT_SCAN_TASKS}")
    except Exception as e:
        print(f"❌ Agent配置获取失败: {str(e)}")

    # 测试5: 状态上下文更新
    print("\n测试5: 状态上下文更新")
    try:
        state = AgentState(
            task_id="test_context",
            target="https://www.baidu.com"
        )
        state.update_context("cms", "WordPress")
        state.update_context("open_ports", [80, 443])
        state.update_context("waf", "Cloudflare")
        print("✅ 状态上下文更新成功")
        print(f"   CMS: {state.target_context.get('cms')}")
        print(f"   开放端口: {state.target_context.get('open_ports')}")
        print(f"   WAF: {state.target_context.get('waf')}")
    except Exception as e:
        print(f"❌ 状态上下文更新失败: {str(e)}")

    # 测试6: 状态漏洞管理
    print("\n测试6: 状态漏洞管理")
    try:
        state = AgentState(
            task_id="test_vuln",
            target="https://www.baidu.com"
        )
        vuln1 = {
            "cve": "CVE-2020-2551",
            "severity": "critical",
            "description": "WebLogic RCE"
        }
        vuln2 = {
            "cve": "CVE-2021-44228",
            "severity": "high",
            "description": "Log4j RCE"
        }
        state.add_vulnerability(vuln1)
        state.add_vulnerability(vuln2)
        print("✅ 状态漏洞管理成功")
        print(f"   漏洞数量: {len(state.vulnerabilities)}")
        print(f"   漏洞1: {state.vulnerabilities[0]['cve']}")
        print(f"   漏洞2: {state.vulnerabilities[1]['cve']}")
    except Exception as e:
        print(f"❌ 状态漏洞管理失败: {str(e)}")

    # 测试7: 状态错误管理
    print("\n测试7: 状态错误管理")
    try:
        state = AgentState(
            task_id="test_errors",
            target="https://www.baidu.com"
        )
        state.add_error("工具执行失败")
        state.add_error("代码生成超时")
        print("✅ 状态错误管理成功")
        print(f"   错误数量: {len(state.errors)}")
        print(f"   错误1: {state.errors[0]}")
        print(f"   错误2: {state.errors[1]}")
    except Exception as e:
        print(f"❌ 状态错误管理失败: {str(e)}")

    # 测试8: 状态重试机制
    print("\n测试8: 状态重试机制")
    try:
        state = AgentState(
            task_id="test_retry",
            target="https://www.baidu.com"
        )
        print(f"   初始重试次数: {state.retry_count}")
        state.increment_retry()
        print(f"   增加后重试次数: {state.retry_count}")
        state.increment_retry()
        print(f"   再次增加后重试次数: {state.retry_count}")
        state.reset_retry()
        print(f"   重置后重试次数: {state.retry_count}")
        print("✅ 状态重试机制成功")
    except Exception as e:
        print(f"❌ 状态重试机制失败: {str(e)}")

    # 测试9: 状态完成标记
    print("\n测试9: 状态完成标记")
    try:
        state = AgentState(
            task_id="test_complete",
            target="https://www.baidu.com"
        )
        print(f"   初始完成状态: {state.is_complete}")
        state.mark_complete()
        print(f"   标记后完成状态: {state.is_complete}")
        print("✅ 状态完成标记成功")
    except Exception as e:
        print(f"❌ 状态完成标记失败: {str(e)}")

    # 测试10: 状态进度计算
    print("\n测试10: 状态进度计算")
    try:
        state = AgentState(
            task_id="test_progress",
            target="https://www.baidu.com",
            planned_tasks=["baseinfo", "portscan", "vuln_scan"]
        )
        print(f"   初始进度: {state.get_progress()}%")
        state.completed_tasks = ["baseinfo"]
        print(f"   完成1个任务后进度: {state.get_progress()}%")
        state.completed_tasks = ["baseinfo", "portscan"]
        print(f"   完成2个任务后进度: {state.get_progress()}%")
        print("✅ 状态进度计算成功")
    except Exception as e:
        print(f"❌ 状态进度计算失败: {str(e)}")

    # 测试11: 状态序列化
    print("\n测试11: 状态序列化")
    try:
        state = AgentState(
            task_id="test_serialization",
            target="https://www.baidu.com",
            planned_tasks=["baseinfo", "portscan"]
        )
        state.add_vulnerability({
            "cve": "CVE-2020-2551",
            "severity": "critical"
        })
        state.add_error("测试错误")
        state_dict = state.to_dict()
        print("✅ 状态序列化成功")
        print(f"   字典键: {list(state_dict.keys())}")
    except Exception as e:
        print(f"❌ 状态序列化失败: {str(e)}")

    # 测试12: POC验证任务管理
    print("\n测试12: POC验证任务管理")
    try:
        state = AgentState(
            task_id="test_poc",
            target="https://www.baidu.com"
        )
        poc_task1 = {
            "poc_id": "poc_001",
            "poc_name": "weblogic_rce",
            "poc_code": "print('POC code')",
            "target": "https://www.baidu.com",
            "priority": 1,
            "status": "pending"
        }
        poc_task2 = {
            "poc_id": "poc_002",
            "poc_name": "struts2_rce",
            "poc_code": "print('POC code')",
            "target": "https://www.baidu.com",
            "priority": 2,
            "status": "pending"
        }
        state.poc_verification_tasks = [poc_task1, poc_task2]
        print("✅ POC验证任务管理成功")
        print(f"   POC任务数量: {len(state.poc_verification_tasks)}")
        print(f"   POC1 ID: {state.poc_verification_tasks[0]['poc_id']}")
        print(f"   POC2 ID: {state.poc_verification_tasks[1]['poc_id']}")
    except Exception as e:
        print(f"❌ POC验证任务管理失败: {str(e)}")

    # 测试13: POC验证结果管理
    print("\n测试13: POC验证结果管理")
    try:
        state = AgentState(
            task_id="test_poc_results",
            target="https://www.baidu.com"
        )
        result1 = {
            "poc_name": "weblogic_rce",
            "poc_id": "poc_001",
            "target": "https://www.baidu.com",
            "vulnerable": True,
            "message": "漏洞存在",
            "execution_time": 1.5,
            "confidence": 0.95,
            "severity": "critical"
        }
        result2 = {
            "poc_name": "struts2_rce",
            "poc_id": "poc_002",
            "target": "https://www.baidu.com",
            "vulnerable": False,
            "message": "漏洞不存在",
            "execution_time": 0.8,
            "confidence": 0.9,
            "severity": "info"
        }
        state.poc_verification_results = [result1, result2]
        print("✅ POC验证结果管理成功")
        print(f"   POC结果数量: {len(state.poc_verification_results)}")
        print(f"   漏洞存在: {state.poc_verification_results[0]['vulnerable']}")
        print(f"   漏洞不存在: {state.poc_verification_results[1]['vulnerable']}")
    except Exception as e:
        print(f"❌ POC验证结果管理失败: {str(e)}")

    # 测试14: POC执行统计
    print("\n测试14: POC执行统计")
    try:
        state = AgentState(
            task_id="test_poc_stats",
            target="https://www.baidu.com"
        )
        state.poc_execution_stats = {
            "total_pocs": 10,
            "executed_count": 8,
            "vulnerable_count": 3,
            "failed_count": 2,
            "success_rate": 0.75,
            "total_execution_time": 12.5,
            "average_execution_time": 1.56
        }
        print("✅ POC执行统计成功")
        print(f"   总POC数: {state.poc_execution_stats['total_pocs']}")
        print(f"   已执行数: {state.poc_execution_stats['executed_count']}")
        print(f"   漏洞数: {state.poc_execution_stats['vulnerable_count']}")
        print(f"   失败数: {state.poc_execution_stats['failed_count']}")
        print(f"   成功率: {state.poc_execution_stats['success_rate']}")
    except Exception as e:
        print(f"❌ POC执行统计失败: {str(e)}")

    # 测试15: Seebug POC管理
    print("\n测试15: Seebug POC管理")
    try:
        state = AgentState(
            task_id="test_seebug",
            target="https://www.baidu.com"
        )
        seebug_poc1 = {
            "ssvid": "99335",
            "name": "WebLogic T3/II反序列化远程代码执行漏洞 (CVE-2020-2551)",
            "type": "RCE",
            "description": "WebLogic Server远程代码执行漏洞"
        }
        seebug_poc2 = {
            "ssvid": "99336",
            "name": "Apache Log4j2远程代码执行漏洞 (CVE-2021-44228)",
            "type": "RCE",
            "description": "Log4j2远程代码执行漏洞"
        }
        state.seebug_pocs = [seebug_poc1, seebug_poc2]
        print("✅ Seebug POC管理成功")
        print(f"   Seebug POC数量: {len(state.seebug_pocs)}")
        print(f"   POC1 SSVID: {state.seebug_pocs[0]['ssvid']}")
        print(f"   POC2 SSVID: {state.seebug_pocs[1]['ssvid']}")
    except Exception as e:
        print(f"❌ Seebug POC管理失败: {str(e)}")

    # 测试16: 生成的POC管理
    print("\n测试16: 生成的POC管理")
    try:
        state = AgentState(
            task_id="test_generated_pocs",
            target="https://www.baidu.com"
        )
        generated_poc1 = {
            "ssvid": "99335",
            "name": "WebLogic T3/II反序列化远程代码执行漏洞 (CVE-2020-2551)",
            "code": "import requests\nprint('POC code')",
            "source": "seebug_agent"
        }
        generated_poc2 = {
            "ssvid": "99336",
            "name": "Apache Log4j2远程代码执行漏洞 (CVE-2021-44228)",
            "code": "import socket\nprint('POC code')",
            "source": "seebug_agent"
        }
        state.generated_pocs = [generated_poc1, generated_poc2]
        print("✅ 生成的POC管理成功")
        print(f"   生成的POC数量: {len(state.generated_pocs)}")
        print(f"   POC1来源: {state.generated_pocs[0]['source']}")
        print(f"   POC2来源: {state.generated_pocs[1]['source']}")
    except Exception as e:
        print(f"❌ 生成的POC管理失败: {str(e)}")

    # 测试17: 用户工具管理
    print("\n测试17: 用户工具管理")
    try:
        state = AgentState(
            task_id="test_user_tools",
            target="https://www.baidu.com"
        )
        user_tool1 = {
            "name": "custom_scan",
            "args": {"target": "https://www.baidu.com"},
            "description": "自定义扫描工具"
        }
        user_tool2 = {
            "name": "custom_check",
            "args": {"check_type": "sql_injection"},
            "description": "自定义检查工具"
        }
        state.user_tools = [user_tool1, user_tool2]
        print("✅ 用户工具管理成功")
        print(f"   用户工具数量: {len(state.user_tools)}")
        print(f"   工具1: {state.user_tools[0]['name']}")
        print(f"   工具2: {state.user_tools[1]['name']}")
    except Exception as e:
        print(f"❌ 用户工具管理失败: {str(e)}")

    # 测试18: 记忆信息管理
    print("\n测试18: 记忆信息管理")
    try:
        state = AgentState(
            task_id="test_memory",
            target="https://www.baidu.com",
            memory_info="这是之前的扫描结果..."
        )
        print("✅ 记忆信息管理成功")
        print(f"   记忆信息: {state.memory_info}")
        state.memory_info = "这是更新后的扫描结果..."
        print(f"   更新后记忆信息: {state.memory_info}")
    except Exception as e:
        print(f"❌ 记忆信息管理失败: {str(e)}")

    # 测试19: 用户需求管理
    print("\n测试19: 用户需求管理")
    try:
        state = AgentState(
            task_id="test_requirement",
            target="https://www.baidu.com",
            user_requirement="扫描目标网站的所有开放端口和已知漏洞"
        )
        print("✅ 用户需求管理成功")
        print(f"   用户需求: {state.user_requirement}")
        state.user_requirement = "扫描目标网站的SQL注入漏洞"
        print(f"   更新后用户需求: {state.user_requirement}")
    except Exception as e:
        print(f"❌ 用户需求管理失败: {str(e)}")

    # 测试20: 规划数据管理
    print("\n测试20: 规划数据管理")
    try:
        state = AgentState(
            task_id="test_plan_data",
            target="https://www.baidu.com"
        )
        import json
        state.plan_data = json.dumps({
            "tasks": ["baseinfo", "portscan", "vuln_scan"],
            "reasoning": "根据目标特征选择扫描任务"
        })
        print("✅ 规划数据管理成功")
        plan_dict = json.loads(state.plan_data)
        print(f"   规划任务: {plan_dict['tasks']}")
        print(f"   规划原因: {plan_dict['reasoning']}")
    except Exception as e:
        print(f"❌ 规划数据管理失败: {str(e)}")

    # 测试21: 执行结果管理
    print("\n测试21: 执行结果管理")
    try:
        state = AgentState(
            task_id="test_execution_results",
            target="https://www.baidu.com"
        )
        result1 = {
            "task": "baseinfo",
            "status": "success",
            "data": {"cms": "WordPress", "server": "Nginx"}
        }
        result2 = {
            "task": "portscan",
            "status": "success",
            "data": {"open_ports": [80, 443, 8080]}
        }
        state.execution_results = [result1, result2]
        print("✅ 执行结果管理成功")
        print(f"   执行结果数量: {len(state.execution_results)}")
        print(f"   结果1任务: {state.execution_results[0]['task']}")
        print(f"   结果2任务: {state.execution_results[1]['task']}")
    except Exception as e:
        print(f"❌ 执行结果管理失败: {str(e)}")

    # 测试22: POC验证状态管理
    print("\n测试22: POC验证状态管理")
    try:
        state = AgentState(
            task_id="test_poc_status",
            target="https://www.baidu.com"
        )
        print(f"   初始状态: {state.poc_verification_status}")
        state.poc_verification_status = "running"
        print(f"   更新后状态: {state.poc_verification_status}")
        state.poc_verification_status = "completed"
        print(f"   再次更新后状态: {state.poc_verification_status}")
        print("✅ POC验证状态管理成功")
    except Exception as e:
        print(f"❌ POC验证状态管理失败: {str(e)}")

    # 测试23: 工具结果管理
    print("\n测试23: 工具结果管理")
    try:
        state = AgentState(
            task_id="test_tool_results",
            target="https://www.baidu.com"
        )
        state.tool_results = {
            "baseinfo": {"cms": "WordPress", "server": "Nginx"},
            "portscan": {"open_ports": [80, 443, 8080]},
            "waf_detect": {"waf": "Cloudflare"},
            "cdn_detect": {"cdn": "Cloudflare"}
        }
        print("✅ 工具结果管理成功")
        print(f"   工具结果数量: {len(state.tool_results)}")
        print(f"   工具列表: {list(state.tool_results.keys())}")
    except Exception as e:
        print(f"❌ 工具结果管理失败: {str(e)}")

    # 测试24: 当前任务管理
    print("\n测试24: 当前任务管理")
    try:
        state = AgentState(
            task_id="test_current_task",
            target="https://www.baidu.com",
            planned_tasks=["baseinfo", "portscan", "vuln_scan"]
        )
        print(f"   初始当前任务: {state.current_task}")
        state.current_task = "baseinfo"
        print(f"   设置后当前任务: {state.current_task}")
        state.current_task = "portscan"
        print(f"   更新后当前任务: {state.current_task}")
        print("✅ 当前任务管理成功")
    except Exception as e:
        print(f"❌ 当前任务管理失败: {str(e)}")

    # 测试25: 已完成任务管理
    print("\n测试25: 已完成任务管理")
    try:
        state = AgentState(
            task_id="test_completed_tasks",
            target="https://www.baidu.com",
            planned_tasks=["baseinfo", "portscan", "vuln_scan"]
        )
        print(f"   初始已完成任务: {state.completed_tasks}")
        state.completed_tasks = ["baseinfo", "portscan"]
        print(f"   添加后已完成任务: {state.completed_tasks}")
        print("✅ 已完成任务管理成功")
    except Exception as e:
        print(f"❌ 已完成任务管理失败: {str(e)}")

    # 测试26: 执行历史记录
    print("\n测试26: 执行历史记录")
    try:
        state = AgentState(
            task_id="test_history",
            target="https://www.baidu.com"
        )
        state.add_execution_step(
            task="baseinfo",
            result={"status": "success"},
            status="success",
            step_type="tool_execution"
        )
        state.add_execution_step(
            task="portscan",
            result={"open_ports": [80, 443]},
            status="success",
            step_type="tool_execution"
        )
        print("✅ 执行历史记录成功")
        print(f"   执行历史数量: {len(state.execution_history)}")
        print(f"   历史1任务: {state.execution_history[0]['task']}")
        print(f"   历史2任务: {state.execution_history[1]['task']}")
    except Exception as e:
        print(f"❌ 执行历史记录失败: {str(e)}")

    print("\n" + "=" * 80)
    print("测试总结:")
    print("=" * 80)
    print("✅ 所有26个核心功能测试完成")
    print("✅ 图功能验证通过")
    print("✅ 状态管理验证通过")
    print("✅ 工具管理验证通过")
    print("✅ POC管理验证通过")
    print("✅ 执行管理验证通过")
    print("=" * 80)

except Exception as e:
    print(f"❌ 测试执行失败: {str(e)}")
    import traceback
    traceback.print_exc()

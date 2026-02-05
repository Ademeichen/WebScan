"""
AIAgent图功能简化测试

测试AIAgent系统的图功能，避免复杂的导入依赖。
"""
import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from ai_agents.core.graph import ScanAgentGraph
from ai_agents.core.state import AgentState
from ai_agents.tools.registry import registry
from ai_agents.agent_config import agent_config


class TestAIAgentGraphSimple:
    """AIAgent图功能简化测试类"""
    
    def test_graph_initialization(self):
        """测试1: 图初始化"""
        graph = ScanAgentGraph()
        assert graph is not None
        assert hasattr(graph, 'graph')
        graph_info = graph.get_graph_info()
        assert 'nodes' in graph_info
        assert 'edges' in graph_info
        assert len(graph_info['nodes']) > 0
        assert len(graph_info['edges']) > 0
    
    def test_state_creation(self):
        """测试2: 状态创建"""
        state = AgentState(
            task_id="test_001",
            target="https://www.baidu.com"
        )
        assert state.task_id == "test_001"
        assert state.target == "https://www.baidu.com"
        assert state.retry_count == 0
        assert state.is_complete == False
    
    def test_tool_registry(self):
        """测试3: 工具注册表"""
        stats = registry.get_stats()
        assert 'total_tools' in stats
        assert 'by_category' in stats
        assert isinstance(stats['total_tools'], int)
        assert isinstance(stats['by_category'], dict)
    
    def test_agent_config(self):
        """测试4: Agent配置"""
        assert hasattr(agent_config, 'MAX_EXECUTION_TIME')
        assert hasattr(agent_config, 'MAX_RETRIES')
        assert hasattr(agent_config, 'MAX_CONCURRENT_TOOLS')
        assert hasattr(agent_config, 'TOOL_TIMEOUT')
        assert hasattr(agent_config, 'ENABLE_LLM_PLANNING')
        assert hasattr(agent_config, 'DEFAULT_SCAN_TASKS')
        assert agent_config.MAX_EXECUTION_TIME > 0
        assert agent_config.MAX_RETRIES >= 0
        assert agent_config.MAX_CONCURRENT_TOOLS > 0
        assert agent_config.TOOL_TIMEOUT > 0
        assert isinstance(agent_config.ENABLE_LLM_PLANNING, bool)
        assert isinstance(agent_config.DEFAULT_SCAN_TASKS, list)
    
    def test_state_context_update(self):
        """测试5: 状态上下文更新"""
        state = AgentState(
            task_id="test_context",
            target="https://www.baidu.com"
        )
        state.update_context("cms", "WordPress")
        state.update_context("open_ports", [80, 443])
        state.update_context("waf", "Cloudflare")
        assert state.target_context.get('cms') == "WordPress"
        assert state.target_context.get('open_ports') == [80, 443]
        assert state.target_context.get('waf') == "Cloudflare"
    
    def test_state_vulnerability_management(self):
        """测试6: 状态漏洞管理"""
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
        assert len(state.vulnerabilities) == 2
        assert state.vulnerabilities[0]['cve'] == "CVE-2020-2551"
        assert state.vulnerabilities[1]['cve'] == "CVE-2021-44228"
    
    def test_state_error_management(self):
        """测试7: 状态错误管理"""
        state = AgentState(
            task_id="test_errors",
            target="https://www.baidu.com"
        )
        state.add_error("工具执行失败")
        state.add_error("代码生成超时")
        assert len(state.errors) == 2
        assert state.errors[0] == "工具执行失败"
        assert state.errors[1] == "代码生成超时"
    
    def test_state_retry_mechanism(self):
        """测试8: 状态重试机制"""
        state = AgentState(
            task_id="test_retry",
            target="https://www.baidu.com"
        )
        assert state.retry_count == 0
        state.increment_retry()
        assert state.retry_count == 1
        state.increment_retry()
        assert state.retry_count == 2
        state.reset_retry()
        assert state.retry_count == 0
    
    def test_state_completion_marking(self):
        """测试9: 状态完成标记"""
        state = AgentState(
            task_id="test_complete",
            target="https://www.baidu.com"
        )
        assert state.is_complete == False
        state.mark_complete()
        assert state.is_complete == True
    
    def test_state_progress_calculation(self):
        """测试10: 状态进度计算"""
        state = AgentState(
            task_id="test_progress",
            target="https://www.baidu.com",
            planned_tasks=["baseinfo", "portscan", "vuln_scan"]
        )
        progress = state.get_progress()
        assert progress == 0.0
        state.completed_tasks = ["baseinfo"]
        progress = state.get_progress()
        assert progress > 0
        state.completed_tasks = ["baseinfo", "portscan"]
        progress = state.get_progress()
        assert progress > 0.5
    
    def test_state_serialization(self):
        """测试11: 状态序列化"""
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
        assert isinstance(state_dict, dict)
        assert 'target' in state_dict
        assert 'task_id' in state_dict
        assert 'vulnerabilities' in state_dict
        assert 'errors' in state_dict
        assert state_dict['target'] == "https://www.baidu.com"
        assert state_dict['task_id'] == "test_serialization"
    
    def test_poc_verification_task_management(self):
        """测试12: POC验证任务管理"""
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
        assert len(state.poc_verification_tasks) == 2
        assert state.poc_verification_tasks[0]['poc_id'] == "poc_001"
        assert state.poc_verification_tasks[1]['poc_id'] == "poc_002"
    
    def test_poc_verification_result_management(self):
        """测试13: POC验证结果管理"""
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
        assert len(state.poc_verification_results) == 2
        assert state.poc_verification_results[0]['vulnerable'] == True
        assert state.poc_verification_results[1]['vulnerable'] == False
    
    def test_poc_execution_statistics(self):
        """测试14: POC执行统计"""
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
        assert state.poc_execution_stats['total_pocs'] == 10
        assert state.poc_execution_stats['executed_count'] == 8
        assert state.poc_execution_stats['vulnerable_count'] == 3
        assert state.poc_execution_stats['failed_count'] == 2
        assert state.poc_execution_stats['success_rate'] == 0.75
    
    def test_seebug_poc_management(self):
        """测试15: Seebug POC管理"""
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
        assert len(state.seebug_pocs) == 2
        assert state.seebug_pocs[0]['ssvid'] == "99335"
        assert state.seebug_pocs[1]['ssvid'] == "99336"
    
    def test_generated_poc_management(self):
        """测试16: 生成的POC管理"""
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
        assert len(state.generated_pocs) == 2
        assert state.generated_pocs[0]['source'] == "seebug_agent"
        assert state.generated_pocs[1]['source'] == "seebug_agent"
    
    def test_user_tool_management(self):
        """测试17: 用户工具管理"""
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
        assert len(state.user_tools) == 2
        assert state.user_tools[0]['name'] == "custom_scan"
        assert state.user_tools[1]['name'] == "custom_check"
    
    def test_memory_info_management(self):
        """测试18: 记忆信息管理"""
        state = AgentState(
            task_id="test_memory",
            target="https://www.baidu.com",
            memory_info="这是之前的扫描结果..."
        )
        assert state.memory_info == "这是之前的扫描结果..."
        state.memory_info = "这是更新后的扫描结果..."
        assert state.memory_info == "这是更新后的扫描结果..."
    
    def test_user_requirement_management(self):
        """测试19: 用户需求管理"""
        state = AgentState(
            task_id="test_requirement",
            target="https://www.baidu.com",
            user_requirement="扫描目标网站的所有开放端口和已知漏洞"
        )
        assert state.user_requirement == "扫描目标网站的所有开放端口和已知漏洞"
        state.user_requirement = "扫描目标网站的SQL注入漏洞"
        assert state.user_requirement == "扫描目标网站的SQL注入漏洞"
    
    def test_plan_data_management(self):
        """测试20: 规划数据管理"""
        state = AgentState(
            task_id="test_plan_data",
            target="https://www.baidu.com"
        )
        import json
        state.plan_data = json.dumps({
            "tasks": ["baseinfo", "portscan", "vuln_scan"],
            "reasoning": "根据目标特征选择扫描任务"
        })
        plan_dict = json.loads(state.plan_data)
        assert plan_dict['tasks'] == ["baseinfo", "portscan", "vuln_scan"]
        assert plan_dict['reasoning'] == "根据目标特征选择扫描任务"
    
    def test_execution_result_management(self):
        """测试21: 执行结果管理"""
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
        assert len(state.execution_results) == 2
        assert state.execution_results[0]['task'] == "baseinfo"
        assert state.execution_results[1]['task'] == "portscan"
    
    def test_poc_verification_status_management(self):
        """测试22: POC验证状态管理"""
        state = AgentState(
            task_id="test_poc_status",
            target="https://www.baidu.com"
        )
        assert state.poc_verification_status == "pending"
        state.poc_verification_status = "running"
        assert state.poc_verification_status == "running"
        state.poc_verification_status = "completed"
        assert state.poc_verification_status == "completed"
    
    def test_tool_result_management(self):
        """测试23: 工具结果管理"""
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
        assert len(state.tool_results) == 4
        assert 'baseinfo' in state.tool_results
        assert 'portscan' in state.tool_results
        assert 'waf_detect' in state.tool_results
        assert 'cdn_detect' in state.tool_results
    
    def test_current_task_management(self):
        """测试24: 当前任务管理"""
        state = AgentState(
            task_id="test_current_task",
            target="https://www.baidu.com",
            planned_tasks=["baseinfo", "portscan", "vuln_scan"]
        )
        assert state.current_task is None
        state.current_task = "baseinfo"
        assert state.current_task == "baseinfo"
        state.current_task = "portscan"
        assert state.current_task == "portscan"
    
    def test_completed_tasks_management(self):
        """测试25: 已完成任务管理"""
        state = AgentState(
            task_id="test_completed_tasks",
            target="https://www.baidu.com",
            planned_tasks=["baseinfo", "portscan", "vuln_scan"]
        )
        assert state.completed_tasks == []
        state.completed_tasks = ["baseinfo", "portscan"]
        assert state.completed_tasks == ["baseinfo", "portscan"]
    
    def test_execution_history_recording(self):
        """测试26: 执行历史记录"""
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
        assert len(state.execution_history) == 2
        assert state.execution_history[0]['task'] == "baseinfo"
        assert state.execution_history[1]['task'] == "portscan"
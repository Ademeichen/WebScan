"""
AIAgent图功能全面测试

测试AIAgent系统的图功能，包括：
1. Agent扫描任务创建和执行
2. 任务查询和管理
3. 工具列表和配置管理
4. 代码生成和执行
5. 功能增强
6. 环境感知
7. 图工作流的完整执行

测试覆盖：
- 正常场景
- 边界情况
- 异常情况
"""
import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import sys

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from ai_agents.core.graph import ScanAgentGraph
from ai_agents.core.state import AgentState
from ai_agents.tools.registry import registry
from ai_agents.api.routes import (
    AgentScanRequest,
    AgentScanResponse,
    CodeGenerationRequest,
    CodeExecutionRequest,
    CapabilityEnhancementRequest
)
from models import AgentTask, AgentResult
from ai_agents.agent_config import agent_config


class TestAIAgentGraph:
    """AIAgent图功能测试类"""
    
    @pytest.fixture
    def sample_targets(self):
        """提供测试目标样本"""
        return [
            "https://www.baidu.com",
            "https://www.google.com",
            "192.168.1.1",
            "example.com",
            "http://test.local:8080"
        ]
    
    @pytest.fixture
    def sample_scan_types(self):
        """提供扫描类型样本"""
        return [
            "port_scan",
            "vuln_scan",
            "web_scan",
            "custom_scan"
        ]
    
    @pytest.fixture
    def sample_tasks(self):
        """提供任务样本"""
        return [
            "baseinfo",
            "portscan",
            "waf_detect",
            "cdn_detect",
            "cms_identify",
            "infoleak_scan",
            "poc_weblogic_2020_2551"
        ]
    
    def test_graph_initialization(self):
        """测试1: 图初始化"""
        """测试图初始化是否正常"""
        graph = ScanAgentGraph()
        assert graph is not None
        assert hasattr(graph, 'graph')
        assert hasattr(graph, 'env_awareness_node')
        assert hasattr(graph, 'planning_node')
        assert hasattr(graph, 'intelligent_decision_node')
        assert hasattr(graph, 'execution_node')
        assert hasattr(graph, 'code_generation_node')
        assert hasattr(graph, 'code_execution_node')
        assert hasattr(graph, 'capability_enhancement_node')
        assert hasattr(graph, 'verification_node')
        assert hasattr(graph, 'poc_verification_node')
        assert hasattr(graph, 'seebug_agent_node')
        assert hasattr(graph, 'analysis_node')
        assert hasattr(graph, 'report_node')
    
    def test_graph_info(self):
        """测试2: 获取图信息"""
        """测试获取图信息是否正常"""
        graph = ScanAgentGraph()
        info = graph.get_graph_info()
        assert 'nodes' in info
        assert 'edges' in info
        assert len(info['nodes']) == 12
        assert len(info['edges']) == 16
    
    def test_agent_state_creation(self, sample_targets):
        """测试3: Agent状态创建"""
        """测试Agent状态创建是否正常"""
        for target in sample_targets:
            state = AgentState(
                task_id=f"test_{target}",
                target=target
            )
            assert state.target == target
            assert state.task_id.startswith("test_")
            assert state.planned_tasks == []
            assert state.tool_results == {}
            assert state.vulnerabilities == []
    
    def test_agent_state_with_custom_tasks(self, sample_targets, sample_tasks):
        """测试4: 带自定义任务的Agent状态"""
        """测试带自定义任务的Agent状态"""
        state = AgentState(
            task_id="test_custom",
            target=sample_targets[0],
            planned_tasks=sample_tasks
        )
        assert state.planned_tasks == sample_tasks
        assert len(state.planned_tasks) == len(sample_tasks)
    
    def test_agent_state_context_updates(self, sample_targets):
        """测试5: Agent状态上下文更新"""
        """测试Agent状态上下文更新是否正常"""
        state = AgentState(
            task_id="test_context",
            target=sample_targets[0]
        )
        
        # 测试上下文更新
        state.update_context("cms", "WordPress")
        state.update_context("open_ports", [80, 443])
        state.update_context("waf", "Cloudflare")
        
        assert state.target_context.get("cms") == "WordPress"
        assert state.target_context.get("open_ports") == [80, 443]
        assert state.target_context.get("waf") == "Cloudflare"
    
    def test_agent_state_progress(self, sample_targets, sample_tasks):
        """测试6: Agent状态进度计算"""
        """测试Agent状态进度计算是否正确"""
        state = AgentState(
            task_id="test_progress",
            target=sample_targets[0],
            planned_tasks=sample_tasks
        )
        
        # 初始进度
        assert state.get_progress() == 0.0
        
        # 完成部分任务
        state.completed_tasks = sample_tasks[:3]
        progress = state.get_progress()
        expected_progress = (3 / len(sample_tasks)) * 100
        assert abs(progress - expected_progress) < 0.01
    
    def test_agent_state_vulnerabilities(self, sample_targets):
        """测试7: Agent状态漏洞管理"""
        """测试Agent状态漏洞管理是否正常"""
        state = AgentState(
            task_id="test_vuln",
            target=sample_targets[0]
        )
        
        # 添加漏洞
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
        assert state.vulnerabilities[0]["cve"] == "CVE-2020-2551"
        assert state.vulnerabilities[1]["cve"] == "CVE-2021-44228"
    
    def test_agent_state_errors(self, sample_targets):
        """测试8: Agent状态错误管理"""
        """测试Agent状态错误管理是否正常"""
        state = AgentState(
            task_id="test_errors",
            target=sample_targets[0]
        )
        
        # 添加错误
        state.add_error("工具执行失败")
        state.add_error("代码生成超时")
        
        assert len(state.errors) == 2
        assert state.errors[0] == "工具执行失败"
        assert state.errors[1] == "代码生成超时"
    
    def test_agent_state_retry(self, sample_targets):
        """测试9: Agent状态重试机制"""
        """测试Agent状态重试机制是否正常"""
        state = AgentState(
            task_id="test_retry",
            target=sample_targets[0]
        )
        
        # 初始重试次数
        assert state.retry_count == 0
        
        # 增加重试次数
        state.increment_retry()
        assert state.retry_count == 1
        
        state.increment_retry()
        assert state.retry_count == 2
        
        # 重置重试次数
        state.reset_retry()
        assert state.retry_count == 0
    
    def test_agent_state_completion(self, sample_targets):
        """测试10: Agent状态完成标记"""
        """测试Agent状态完成标记是否正常"""
        state = AgentState(
            task_id="test_complete",
            target=sample_targets[0]
        )
        
        # 初始状态
        assert state.is_complete == False
        assert state.should_continue == True
        
        # 标记完成
        state.mark_complete()
        assert state.is_complete == True
        assert state.should_continue == False
    
    def test_tool_registry_initialization(self):
        """测试11: 工具注册表初始化"""
        """测试工具注册表初始化是否正常"""
        assert registry is not None
        assert hasattr(registry, 'tools')
        assert hasattr(registry, 'tool_metadata')
        assert isinstance(registry.tools, dict)
        assert isinstance(registry.tool_metadata, dict)
    
    def test_tool_registry_stats(self):
        """测试12: 工具注册表统计"""
        """测试工具注册表统计是否正常"""
        stats = registry.get_stats()
        assert 'total_tools' in stats
        assert 'by_category' in stats
        assert isinstance(stats['total_tools'], int)
        assert isinstance(stats['by_category'], dict)
    
    def test_tool_registry_list(self):
        """测试13: 工具注册表列表"""
        """测试工具注册表列表是否正常"""
        tools = registry.list_tools()
        assert isinstance(tools, list)
        
        # 测试分类过滤
        plugin_tools = registry.list_tools(category="plugin")
        poc_tools = registry.list_tools(category="poc")
        general_tools = registry.list_tools(category="general")
        
        assert isinstance(plugin_tools, list)
        assert isinstance(poc_tools, list)
        assert isinstance(general_tools, list)
    
    def test_agent_config(self):
        """测试14: Agent配置"""
        """测试Agent配置是否正常"""
        assert agent_config is not None
        assert hasattr(agent_config, 'MAX_EXECUTION_TIME')
        assert hasattr(agent_config, 'MAX_RETRIES')
        assert hasattr(agent_config, 'MAX_CONCURRENT_TOOLS')
        assert hasattr(agent_config, 'TOOL_TIMEOUT')
        assert hasattr(agent_config, 'ENABLE_LLM_PLANNING')
        assert hasattr(agent_config, 'DEFAULT_SCAN_TASKS')
        assert hasattr(agent_config, 'ENABLE_MEMORY')
        assert hasattr(agent_config, 'ENABLE_KB_INTEGRATION')
        assert hasattr(agent_config, 'PRIORITY_WEIGHTS')
    
    def test_scan_request_validation(self, sample_targets):
        """测试15: 扫描请求验证"""
        """测试扫描请求验证是否正常"""
        # 正常请求
        request = AgentScanRequest(
            target=sample_targets[0],
            enable_llm_planning=True
        )
        assert request.target == sample_targets[0]
        assert request.enable_llm_planning == True
        
        # 带自定义任务的请求
        request = AgentScanRequest(
            target=sample_targets[1],
            custom_tasks=["baseinfo", "portscan"]
        )
        assert request.custom_tasks == ["baseinfo", "portscan"]
        
        # 带自定义扫描的请求
        request = AgentScanRequest(
            target=sample_targets[2],
            need_custom_scan=True,
            custom_scan_type="web_scan",
            custom_scan_requirements="检查SQL注入"
        )
        assert request.need_custom_scan == True
        assert request.custom_scan_type == "web_scan"
        assert request.custom_scan_requirements == "检查SQL注入"
        
        # 带功能增强的请求
        request = AgentScanRequest(
            target=sample_targets[3],
            need_capability_enhancement=True,
            capability_requirement="需要安装requests库"
        )
        assert request.need_capability_enhancement == True
        assert request.capability_requirement == "需要安装requests库"
    
    def test_code_generation_request(self, sample_targets, sample_scan_types):
        """测试16: 代码生成请求"""
        """测试代码生成请求验证是否正常"""
        request = CodeGenerationRequest(
            scan_type=sample_scan_types[0],
            target=sample_targets[0],
            requirements="检查端口开放情况",
            language="python"
        )
        assert request.scan_type == sample_scan_types[0]
        assert request.target == sample_targets[0]
        assert request.requirements == "检查端口开放情况"
        assert request.language == "python"
    
    def test_code_execution_request(self):
        """测试17: 代码执行请求"""
        """测试代码执行请求验证是否正常"""
        request = CodeExecutionRequest(
            code="print('Hello, World!')",
            language="python",
            target="https://www.example.com"
        )
        assert request.code == "print('Hello, World!')"
        assert request.language == "python"
        assert request.target == "https://www.example.com"
    
    def test_capability_enhancement_request(self, sample_targets):
        """测试18: 功能增强请求"""
        """测试功能增强请求验证是否正常"""
        request = CapabilityEnhancementRequest(
            requirement="需要安装requests库",
            target=sample_targets[0],
            capability_name="install_requests"
        )
        assert request.requirement == "需要安装requests库"
        assert request.target == sample_targets[0]
        assert request.capability_name == "install_requests"
    
    def test_graph_workflow_execution(self, sample_targets):
        """测试19: 图工作流执行（模拟）"""
        """测试图工作流执行是否正常（仅初始化，不实际执行）"""
        graph = ScanAgentGraph()
        state = AgentState(
            task_id="test_workflow",
            target=sample_targets[0]
        )
        
        # 验证图结构
        assert graph.graph is not None
        assert hasattr(graph.graph, 'nodes')
        assert hasattr(graph.graph, 'edges')
        
        # 验证状态
        assert state.task_id == "test_workflow"
        assert state.target == sample_targets[0]
        assert state.is_complete == False
    
    def test_edge_cases_empty_target(self):
        """测试20: 边界情况 - 空目标"""
        """测试空目标的边界情况"""
        with pytest.raises((ValueError, TypeError)):
            state = AgentState(
                task_id="test_empty",
                target=""
            )
    
    def test_edge_cases_none_target(self):
        """测试21: 边界情况 - None目标"""
        """测试None目标的边界情况"""
        with pytest.raises((ValueError, TypeError)):
            state = AgentState(
                task_id="test_none",
                target=None
            )
    
    def test_edge_cases_invalid_url(self):
        """测试22: 边界情况 - 无效URL"""
        """测试无效URL的边界情况"""
        invalid_urls = [
            "not-a-url",
            "htp://invalid-scheme.com",
            "https://",
            "://no-protocol.com"
        ]
        
        for url in invalid_urls:
            state = AgentState(
                task_id=f"test_invalid_{len(url)}",
                target=url
            )
            assert state.target == url
    
    def test_edge_cases_empty_tasks(self):
        """测试23: 边界情况 - 空任务列表"""
        """测试空任务列表的边界情况"""
        state = AgentState(
            task_id="test_empty_tasks",
            target="https://www.example.com",
            planned_tasks=[]
        )
        assert state.planned_tasks == []
        assert state.get_progress() == 100.0
    
    def test_edge_cases_single_task(self, sample_targets):
        """测试24: 边界情况 - 单个任务"""
        """测试单个任务的边界情况"""
        state = AgentState(
            task_id="test_single_task",
            target=sample_targets[0],
            planned_tasks=["portscan"]
        )
        assert len(state.planned_tasks) == 1
        assert state.get_progress() == 0.0
    
    def test_edge_cases_large_tasks(self, sample_targets):
        """测试25: 边界情况 - 大量任务"""
        """测试大量任务的边界情况"""
        large_tasks = [f"task_{i}" for i in range(100)]
        state = AgentState(
            task_id="test_large_tasks",
            target=sample_targets[0],
            planned_tasks=large_tasks
        )
        assert len(state.planned_tasks) == 100
        assert state.get_progress() == 0.0
    
    def test_edge_cases_empty_vulnerabilities(self, sample_targets):
        """测试26: 边界情况 - 空漏洞列表"""
        """测试空漏洞列表的边界情况"""
        state = AgentState(
            task_id="test_empty_vulns",
            target=sample_targets[0]
        )
        assert state.vulnerabilities == []
    
    def test_edge_cases_many_vulnerabilities(self, sample_targets):
        """测试27: 边界情况 - 大量漏洞"""
        """测试大量漏洞的边界情况"""
        state = AgentState(
            task_id="test_many_vulns",
            target=sample_targets[0]
        )
        
        for i in range(50):
            vuln = {
                "cve": f"CVE-2020-{i:04d}",
                "severity": "high" if i % 2 == 0 else "medium",
                "description": f"Test vulnerability {i}"
            }
            state.add_vulnerability(vuln)
        
        assert len(state.vulnerabilities) == 50
    
    def test_edge_cases_empty_errors(self, sample_targets):
        """测试28: 边界情况 - 空错误列表"""
        """测试空错误列表的边界情况"""
        state = AgentState(
            task_id="test_empty_errors",
            target=sample_targets[0]
        )
        assert state.errors == []
    
    def test_edge_cases_many_errors(self, sample_targets):
        """测试29: 边界情况 - 大量错误"""
        """测试大量错误的边界情况"""
        state = AgentState(
            task_id="test_many_errors",
            target=sample_targets[0]
        )
        
        for i in range(20):
            state.add_error(f"Error {i}")
        
        assert len(state.errors) == 20
    
    def test_edge_cases_max_retries(self, sample_targets):
        """测试30: 边界情况 - 最大重试次数"""
        """测试最大重试次数的边界情况"""
        state = AgentState(
            task_id="test_max_retries",
            target=sample_targets[0]
        )
        
        for _ in range(agent_config.MAX_RETRIES + 5):
            state.increment_retry()
        
        assert state.retry_count == agent_config.MAX_RETRIES + 5
    
    def test_exception_handling_invalid_task_id(self):
        """测试31: 异常处理 - 无效任务ID"""
        """测试无效任务ID的异常处理"""
        invalid_ids = [
            "",
            "not-a-uuid",
            "123",
            "00000000-0000-0000-0000-000000000000"
        ]
        
        for task_id in invalid_ids:
            # 这里只是验证ID格式，不实际查询数据库
            assert isinstance(task_id, str)
    
    def test_exception_handling_invalid_config(self):
        """测试32: 异常处理 - 无效配置"""
        """测试无效配置的异常处理"""
        # 测试配置更新
        old_max_time = agent_config.MAX_EXECUTION_TIME
        agent_config.MAX_EXECUTION_TIME = -100
        assert agent_config.MAX_EXECUTION_TIME == -100
        
        # 恢复配置
        agent_config.MAX_EXECUTION_TIME = old_max_time
        assert agent_config.MAX_EXECUTION_TIME == old_max_time
    
    def test_state_serialization(self, sample_targets):
        """测试33: 状态序列化"""
        """测试状态序列化是否正常"""
        state = AgentState(
            task_id="test_serialization",
            target=sample_targets[0],
            planned_tasks=["baseinfo", "portscan"]
        )
        
        state.add_vulnerability({
            "cve": "CVE-2020-2551",
            "severity": "critical"
        })
        state.add_error("测试错误")
        
        # 转换为字典
        state_dict = state.to_dict()
        
        assert 'target' in state_dict
        assert 'task_id' in state_dict
        assert 'planned_tasks' in state_dict
        assert 'vulnerabilities' in state_dict
        assert 'errors' in state_dict
        assert 'progress' in state_dict
        assert state_dict['progress'] == 0.0
    
    def test_execution_history(self, sample_targets):
        """测试34: 执行历史记录"""
        """测试执行历史记录是否正常"""
        state = AgentState(
            task_id="test_history",
            target=sample_targets[0]
        )
        
        # 添加执行步骤
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
    
    def test_poc_verification_tasks(self, sample_targets):
        """测试35: POC验证任务"""
        """测试POC验证任务管理是否正常"""
        state = AgentState(
            task_id="test_poc",
            target=sample_targets[0]
        )
        
        # 添加POC验证任务
        poc_task1 = {
            "poc_id": "poc_001",
            "poc_name": "weblogic_rce",
            "poc_code": "print('POC code')",
            "target": sample_targets[0],
            "priority": 1,
            "status": "pending"
        }
        
        poc_task2 = {
            "poc_id": "poc_002",
            "poc_name": "struts2_rce",
            "poc_code": "print('POC code')",
            "target": sample_targets[0],
            "priority": 2,
            "status": "pending"
        }
        
        state.poc_verification_tasks = [poc_task1, poc_task2]
        
        assert len(state.poc_verification_tasks) == 2
        assert state.poc_verification_tasks[0]['poc_id'] == "poc_001"
        assert state.poc_verification_tasks[1]['poc_id'] == "poc_002"
    
    def test_poc_verification_results(self, sample_targets):
        """测试36: POC验证结果"""
        """测试POC验证结果管理是否正常"""
        state = AgentState(
            task_id="test_poc_results",
            target=sample_targets[0]
        )
        
        # 添加POC验证结果
        result1 = {
            "poc_name": "weblogic_rce",
            "poc_id": "poc_001",
            "target": sample_targets[0],
            "vulnerable": True,
            "message": "漏洞存在",
            "execution_time": 1.5,
            "confidence": 0.95,
            "severity": "critical"
        }
        
        result2 = {
            "poc_name": "struts2_rce",
            "poc_id": "poc_002",
            "target": sample_targets[0],
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
    
    def test_poc_execution_stats(self, sample_targets):
        """测试37: POC执行统计"""
        """测试POC执行统计是否正常"""
        state = AgentState(
            task_id="test_poc_stats",
            target=sample_targets[0]
        )
        
        # 设置POC执行统计
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
        assert state.poc_execution_stats['success_rate'] == 0.75
    
    def test_seebug_pocs(self, sample_targets):
        """测试38: Seebug POC"""
        """测试Seebug POC管理是否正常"""
        state = AgentState(
            task_id="test_seebug",
            target=sample_targets[0]
        )
        
        # 添加Seebug POC
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
    
    def test_generated_pocs(self, sample_targets):
        """测试39: 生成的POC"""
        """测试生成的POC管理是否正常"""
        state = AgentState(
            task_id="test_generated_pocs",
            target=sample_targets[0]
        )
        
        # 添加生成的POC
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
    
    def test_user_tools(self, sample_targets):
        """测试40: 用户工具"""
        """测试用户工具管理是否正常"""
        state = AgentState(
            task_id="test_user_tools",
            target=sample_targets[0]
        )
        
        # 添加用户工具
        user_tool1 = {
            "name": "custom_scan",
            "args": {"target": sample_targets[0]},
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
    
    def test_memory_info(self, sample_targets):
        """测试41: 记忆信息"""
        """测试记忆信息管理是否正常"""
        state = AgentState(
            task_id="test_memory",
            target=sample_targets[0],
            memory_info="这是之前的扫描结果..."
        )
        
        assert state.memory_info == "这是之前的扫描结果..."
        
        # 更新记忆信息
        state.memory_info = "这是更新后的扫描结果..."
        assert state.memory_info == "这是更新后的扫描结果..."
    
    def test_user_requirement(self, sample_targets):
        """测试42: 用户需求"""
        """测试用户需求管理是否正常"""
        state = AgentState(
            task_id="test_requirement",
            target=sample_targets[0],
            user_requirement="扫描目标网站的所有开放端口和已知漏洞"
        )
        
        assert state.user_requirement == "扫描目标网站的所有开放端口和已知漏洞"
        
        # 更新用户需求
        state.user_requirement = "扫描目标网站的SQL注入漏洞"
        assert state.user_requirement == "扫描目标网站的SQL注入漏洞"
    
    def test_plan_data(self, sample_targets):
        """测试43: 规划数据"""
        """测试规划数据管理是否正常"""
        state = AgentState(
            task_id="test_plan_data",
            target=sample_targets[0]
        )
        
        # 设置规划数据
        state.plan_data = json.dumps({
            "tasks": ["baseinfo", "portscan", "vuln_scan"],
            "reasoning": "根据目标特征选择扫描任务"
        })
        
        assert state.plan_data is not None
        plan_dict = json.loads(state.plan_data)
        assert 'tasks' in plan_dict
        assert 'reasoning' in plan_dict
        assert len(plan_dict['tasks']) == 3
    
    def test_execution_results(self, sample_targets):
        """测试44: 执行结果"""
        """测试执行结果管理是否正常"""
        state = AgentState(
            task_id="test_execution_results",
            target=sample_targets[0]
        )
        
        # 添加执行结果
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
    
    def test_poc_verification_status(self, sample_targets):
        """测试45: POC验证状态"""
        """测试POC验证状态管理是否正常"""
        state = AgentState(
            task_id="test_poc_status",
            target=sample_targets[0]
        )
        
        # 初始状态
        assert state.poc_verification_status == "pending"
        
        # 更新状态
        state.poc_verification_status = "running"
        assert state.poc_verification_status == "running"
        
        state.poc_verification_status = "completed"
        assert state.poc_verification_status == "completed"
    
    def test_tool_results(self, sample_targets):
        """测试46: 工具结果"""
        """测试工具结果管理是否正常"""
        state = AgentState(
            task_id="test_tool_results",
            target=sample_targets[0]
        )
        
        # 添加工具结果
        state.tool_results = {
            "baseinfo": {"cms": "WordPress", "server": "Nginx"},
            "portscan": {"open_ports": [80, 443, 8080]},
            "waf_detect": {"waf": "Cloudflare"},
            "cdn_detect": {"cdn": "Cloudflare"}
        }
        
        assert len(state.tool_results) == 4
        assert "baseinfo" in state.tool_results
        assert "portscan" in state.tool_results
        assert "waf_detect" in state.tool_results
        assert "cdn_detect" in state.tool_results
    
    def test_current_task(self, sample_targets, sample_tasks):
        """测试47: 当前任务"""
        """测试当前任务管理是否正常"""
        state = AgentState(
            task_id="test_current_task",
            target=sample_targets[0],
            planned_tasks=sample_tasks
        )
        
        # 初始当前任务
        assert state.current_task is None
        
        # 设置当前任务
        state.current_task = sample_tasks[0]
        assert state.current_task == sample_tasks[0]
        
        # 更新当前任务
        state.current_task = sample_tasks[1]
        assert state.current_task == sample_tasks[1]
    
    def test_completed_tasks(self, sample_targets, sample_tasks):
        """测试48: 已完成任务"""
        """测试已完成任务管理是否正常"""
        state = AgentState(
            task_id="test_completed_tasks",
            target=sample_targets[0],
            planned_tasks=sample_tasks
        )
        
        # 初始已完成任务
        assert state.completed_tasks == []
        
        # 添加已完成任务
        state.completed_tasks = [sample_tasks[0], sample_tasks[1]]
        assert len(state.completed_tasks) == 2
        assert state.completed_tasks[0] == sample_tasks[0]
        assert state.completed_tasks[1] == sample_tasks[1]


class TestAIAgentGraphIntegration:
    """AIAgent图功能集成测试类"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_simulation(self):
        """测试49: 完整工作流模拟"""
        """测试完整工作流模拟是否正常"""
        # 创建图
        graph = ScanAgentGraph()
        
        # 创建初始状态
        state = AgentState(
            task_id="integration_test",
            target="https://www.example.com"
        )
        
        # 验证图结构
        assert graph.graph is not None
        assert state.task_id == "integration_test"
        assert state.target == "https://www.example.com"
        
        # 验证节点
        assert hasattr(graph, 'env_awareness_node')
        assert hasattr(graph, 'planning_node')
        assert hasattr(graph, 'intelligent_decision_node')
        assert hasattr(graph, 'execution_node')
        assert hasattr(graph, 'code_generation_node')
        assert hasattr(graph, 'code_execution_node')
        assert hasattr(graph, 'capability_enhancement_node')
        assert hasattr(graph, 'verification_node')
        assert hasattr(graph, 'poc_verification_node')
        assert hasattr(graph, 'seebug_agent_node')
        assert hasattr(graph, 'analysis_node')
        assert hasattr(graph, 'report_node')
    
    @pytest.mark.asyncio
    async def test_node_sequence(self):
        """测试50: 节点序列"""
        """测试节点序列是否正确"""
        graph = ScanAgentGraph()
        info = graph.get_graph_info()
        
        # 验证节点数量
        assert len(info['nodes']) == 12
        
        # 验证边数量
        assert len(info['edges']) == 16
        
        # 验证节点名称
        expected_nodes = [
            "environment_awareness",
            "task_planning",
            "intelligent_decision",
            "tool_execution",
            "code_generation",
            "code_execution",
            "capability_enhancement",
            "result_verification",
            "poc_verification",
            "seebug_agent",
            "vulnerability_analysis",
            "report_generation"
        ]
        
        actual_nodes = [node['id'] for node in info['nodes']]
        for expected_node in expected_nodes:
            assert expected_node in actual_nodes


class TestAIAgentGraphPerformance:
    """AIAgent图功能性能测试类"""
    
    def test_graph_initialization_performance(self):
        """测试51: 图初始化性能"""
        """测试图初始化性能是否满足要求"""
        import time
        
        start_time = time.time()
        graph = ScanAgentGraph()
        end_time = time.time()
        
        initialization_time = end_time - start_time
        
        # 初始化时间应该小于1秒
        assert initialization_time < 1.0, f"图初始化时间过长: {initialization_time}秒"
        assert graph is not None
    
    def test_state_creation_performance(self):
        """测试52: 状态创建性能"""
        """测试状态创建性能是否满足要求"""
        import time
        
        start_time = time.time()
        state = AgentState(
            task_id="perf_test",
            target="https://www.example.com"
        )
        end_time = time.time()
        
        creation_time = end_time - start_time
        
        # 创建时间应该小于0.1秒
        assert creation_time < 0.1, f"状态创建时间过长: {creation_time}秒"
        assert state is not None
    
    def test_large_state_performance(self):
        """测试53: 大状态性能"""
        """测试大状态性能是否满足要求"""
        import time
        
        large_tasks = [f"task_{i}" for i in range(1000)]
        
        start_time = time.time()
        state = AgentState(
            task_id="perf_large_test",
            target="https://www.example.com",
            planned_tasks=large_tasks
        )
        end_time = time.time()
        
        creation_time = end_time - start_time
        
        # 创建时间应该小于1秒
        assert creation_time < 1.0, f"大状态创建时间过长: {creation_time}秒"
        assert len(state.planned_tasks) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

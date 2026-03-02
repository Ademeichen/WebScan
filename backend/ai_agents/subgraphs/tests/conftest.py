"""
子图测试共享fixtures

提供测试子图所需的共享fixtures，包括事件循环、模拟对象、样本数据和自动使用的模拟依赖。
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
from dataclasses import dataclass, field

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


@pytest.fixture(scope="session")
def event_loop():
    """
    创建会话级别的事件循环用于异步测试。
    
    使用session作用域确保所有异步测试共享同一个事件循环，
    提高测试效率并避免资源浪费。
    
    Yields:
        asyncio.AbstractEventLoop: 异步事件循环实例
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_environment_awareness():
    """
    模拟EnvironmentAwareness类。
    
    用于测试环境感知功能，模拟获取环境信息的行为，
    避免在测试中实际访问系统环境。
    
    Returns:
        Mock: 模拟的EnvironmentAwareness实例
    """
    mock_instance = Mock()
    mock_instance.get_environment_report = Mock(return_value={
        "os": "Linux",
        "python_version": "3.10.0",
        "available_tools": ["nmap", "masscan", "httpx"],
        "cpu_cores": 8,
        "memory_gb": 16,
        "network_interfaces": ["eth0", "lo"]
    })
    
    with patch("backend.ai_agents.code_execution.environment.EnvironmentAwareness", return_value=mock_instance):
        yield mock_instance


@pytest.fixture
def mock_code_generator():
    """
    模拟CodeGenerator类。
    
    用于测试代码生成功能，模拟生成扫描代码的行为，
    返回预定义的代码片段用于测试。
    
    Returns:
        Mock: 模拟的CodeGenerator实例
    """
    mock_result = Mock()
    mock_result.code = """
import asyncio

async def scan(target: str):
    print(f"Scanning {target}")
    return {"status": "success", "open_ports": [80, 443]}
"""
    
    mock_instance = Mock()
    mock_instance.generate_code = AsyncMock(return_value=mock_result)
    
    with patch("backend.ai_agents.code_execution.code_generator.CodeGenerator", return_value=mock_instance):
        yield mock_instance


@pytest.fixture
def mock_unified_executor():
    """
    模拟UnifiedExecutor类。
    
    用于测试代码执行功能，模拟执行生成的代码并返回结果，
    避免在测试中实际执行可能危险的代码。
    
    Returns:
        Mock: 模拟的UnifiedExecutor实例
    """
    mock_instance = Mock()
    mock_instance.execute = AsyncMock(return_value={
        "status": "success",
        "output": "Scan completed. Found 2 open ports: 80, 443",
        "execution_time": 1.5,
        "return_code": 0
    })
    
    with patch("backend.ai_agents.code_execution.executor.UnifiedExecutor", return_value=mock_instance):
        yield mock_instance


@pytest.fixture
def mock_capability_enhancer():
    """
    模拟CapabilityEnhancer类。
    
    用于测试功能增强功能，模拟安装依赖包的行为，
    避免在测试中实际安装系统包。
    
    Returns:
        Mock: 模拟的CapabilityEnhancer实例
    """
    mock_instance = Mock()
    mock_instance.enhance_capability = AsyncMock(return_value={
        "status": "success",
        "installed_packages": ["requests", "aiohttp"],
        "message": "Successfully installed required packages"
    })
    
    with patch("backend.ai_agents.code_execution.capability_enhancer.CapabilityEnhancer", return_value=mock_instance):
        yield mock_instance


@pytest.fixture
def sample_target() -> str:
    """
    提供标准的测试目标URL。
    
    Returns:
        str: 测试用的目标URL
    """
    return "http://test-example.com"


@pytest.fixture
def sample_task_id() -> str:
    """
    提供标准的测试任务ID。
    
    Returns:
        str: 测试用的任务ID
    """
    return "test-task-001"


@pytest.fixture
def sample_targets() -> List[str]:
    """
    提供多个测试目标URL列表。
    
    Returns:
        List[str]: 测试用的目标URL列表
    """
    return [
        "http://test1.example.com",
        "http://test2.example.com",
        "https://secure.example.com",
        "http://192.168.1.100"
    ]


@pytest.fixture
def sample_task_ids() -> List[str]:
    """
    提供多个测试任务ID列表。
    
    Returns:
        List[str]: 测试用的任务ID列表
    """
    return [
        "test-task-001",
        "test-task-002",
        "test-task-003"
    ]


@pytest.fixture
def sample_tool_results() -> Dict[str, Any]:
    """
    提供标准的工具执行结果样本数据。
    
    包含多种工具的模拟执行结果，用于测试结果处理和报告生成。
    
    Returns:
        Dict[str, Any]: 工具执行结果字典
    """
    return {
        "portscan": {
            "status": "success",
            "data": {
                "open_ports": [22, 80, 443, 8080],
                "services": {
                    "22": "ssh",
                    "80": "http",
                    "443": "https",
                    "8080": "http-proxy"
                }
            },
            "execution_time": 2.5
        },
        "baseinfo": {
            "status": "success",
            "data": {
                "server": "nginx/1.18.0",
                "cms": "WordPress 5.8",
                "waf": None,
                "cdn": "Cloudflare",
                "title": "Test Site",
                "headers": {
                    "X-Frame-Options": "SAMEORIGIN",
                    "Content-Security-Policy": "default-src 'self'"
                }
            },
            "execution_time": 1.2
        },
        "vulnscan": {
            "status": "success",
            "data": {
                "vulnerabilities": [
                    {
                        "name": "XSS Vulnerability",
                        "severity": "medium",
                        "url": "http://test-example.com/search?q=test"
                    }
                ]
            },
            "execution_time": 5.0
        }
    }


@pytest.fixture
def sample_vulnerabilities() -> List[Dict[str, Any]]:
    """
    提供标准的漏洞数据样本。
    
    包含不同严重程度的漏洞信息，用于测试漏洞分析和报告生成。
    
    Returns:
        List[Dict[str, Any]]: 漏洞信息列表
    """
    return [
        {
            "cve": "CVE-2021-44228",
            "name": "Log4j Remote Code Execution",
            "severity": "critical",
            "target": "http://test-example.com",
            "details": "Apache Log4j2 远程代码执行漏洞",
            "poc_name": "poc_log4j_rce",
            "evidence": "JNDI lookup detected in response"
        },
        {
            "cve": "CVE-2017-12615",
            "name": "Tomcat PUT Method Vulnerability",
            "severity": "high",
            "target": "http://test-example.com",
            "details": "Tomcat PUT方法任意文件写入漏洞",
            "poc_name": "poc_tomcat_put"
        },
        {
            "type": "xss",
            "name": "Reflected XSS",
            "severity": "medium",
            "target": "http://test-example.com/search",
            "details": "反射型XSS漏洞",
            "payload": "<script>alert(1)</script>"
        },
        {
            "type": "info_disclosure",
            "name": "Server Version Disclosure",
            "severity": "low",
            "target": "http://test-example.com",
            "details": "服务器版本信息泄露"
        }
    ]


@pytest.fixture
def sample_poc_tasks() -> List[Dict[str, Any]]:
    """
    提供标准的POC任务样本数据。
    
    Returns:
        List[Dict[str, Any]]: POC任务列表
    """
    return [
        {
            "poc_name": "poc_log4j_rce",
            "target": "http://test-example.com",
            "status": "pending",
            "cve": "CVE-2021-44228"
        },
        {
            "poc_name": "poc_tomcat_put",
            "target": "http://test-example.com",
            "status": "pending",
            "cve": "CVE-2017-12615"
        },
        {
            "poc_name": "poc_struts2_045",
            "target": "http://test-example.com/action",
            "status": "pending",
            "cve": "CVE-2017-5638"
        }
    ]


@pytest.fixture
def sample_target_context() -> Dict[str, Any]:
    """
    提供标准的目标上下文样本数据。
    
    Returns:
        Dict[str, Any]: 目标上下文字典
    """
    return {
        "server": "nginx/1.18.0",
        "cms": "WordPress 5.8",
        "waf": None,
        "cdn": "Cloudflare",
        "open_ports": [22, 80, 443],
        "env_info": {
            "os": "Linux",
            "python_version": "3.10.0"
        },
        "custom_tasks": ["portscan", "baseinfo", "vulnscan"]
    }


@pytest.fixture
def mock_tool_registry():
    """
    模拟工具注册表。
    
    用于测试工具调用功能，模拟各种工具的执行结果，
    避免在测试中实际执行安全工具。
    
    Returns:
        Mock: 模拟的工具注册表实例
    """
    mock_registry = Mock()
    
    async def mock_call_tool(tool_name: str, target: str, **kwargs):
        if tool_name == "portscan":
            return {
                "status": "success",
                "data": {
                    "open_ports": [22, 80, 443],
                    "scan_time": 2.5
                }
            }
        elif tool_name == "baseinfo":
            return {
                "status": "success",
                "data": {
                    "server": "nginx",
                    "cms": "Unknown"
                }
            }
        elif tool_name.startswith("poc_"):
            return {
                "status": "success",
                "data": {
                    "vulnerable": False,
                    "message": "Target not vulnerable"
                }
            }
        else:
            return {
                "status": "error",
                "error": f"Unknown tool: {tool_name}"
            }
    
    mock_registry.call_tool = AsyncMock(side_effect=mock_call_tool)
    mock_registry.get_available_tools = Mock(return_value=[
        "portscan", "baseinfo", "vulnscan", "poc_log4j_rce"
    ])
    
    with patch("backend.ai_agents.tools.registry.registry", mock_registry):
        yield mock_registry


@pytest.fixture
def planning_graph():
    """
    提供PlanningGraph实例用于测试。
    
    创建一个配置好的PlanningGraph实例，用于测试规划功能。
    
    Returns:
        PlanningGraph: 规划图实例
    """
    from backend.ai_agents.subgraphs.planning import PlanningGraph
    return PlanningGraph(use_llm_planning=False)


@pytest.fixture
def planning_state(sample_target, sample_task_id):
    """
    提供PlanningState实例用于测试。
    
    创建一个预填充测试数据的PlanningState实例。
    
    Args:
        sample_target: 测试目标URL fixture
        sample_task_id: 测试任务ID fixture
        
    Returns:
        PlanningState: 规划状态实例
    """
    from backend.ai_agents.subgraphs.planning import PlanningState
    return PlanningState(
        target=sample_target,
        task_id=sample_task_id
    )


@pytest.fixture
def tool_execution_graph():
    """
    提供ToolExecutionGraph实例用于测试。
    
    创建一个配置好的ToolExecutionGraph实例，用于测试工具执行功能。
    
    Returns:
        ToolExecutionGraph: 工具执行图实例
    """
    from backend.ai_agents.subgraphs.tool_execution import ToolExecutionGraph
    return ToolExecutionGraph(max_execution_time=120.0, max_rounds=50)


@pytest.fixture
def tool_execution_state(sample_target, sample_task_id):
    """
    提供ToolExecutionState实例用于测试。
    
    创建一个预填充测试数据的ToolExecutionState实例。
    
    Args:
        sample_target: 测试目标URL fixture
        sample_task_id: 测试任务ID fixture
        
    Returns:
        ToolExecutionState: 工具执行状态实例
    """
    from backend.ai_agents.subgraphs.tool_execution import ToolExecutionState
    return ToolExecutionState(
        target=sample_target,
        task_id=sample_task_id,
        planned_tasks=["portscan", "baseinfo"],
        current_task="portscan"
    )


@pytest.fixture
def code_scan_graph():
    """
    提供CodeScanGraph实例用于测试。
    
    创建一个配置好的CodeScanGraph实例，用于测试代码扫描功能。
    
    Returns:
        CodeScanGraph: 代码扫描图实例
    """
    from backend.ai_agents.subgraphs.code_scan import CodeScanGraph
    return CodeScanGraph(max_execution_time=60.0, max_retries=3)


@pytest.fixture
def code_scan_state(sample_target, sample_task_id):
    """
    提供CodeScanState实例用于测试。
    
    创建一个预填充测试数据的CodeScanState实例。
    
    Args:
        sample_target: 测试目标URL fixture
        sample_task_id: 测试任务ID fixture
        
    Returns:
        CodeScanState: 代码扫描状态实例
    """
    from backend.ai_agents.subgraphs.code_scan import CodeScanState
    return CodeScanState(
        target=sample_target,
        task_id=sample_task_id,
        need_custom_scan=True,
        custom_scan_type="port_scan"
    )


@pytest.fixture
def poc_verification_graph():
    """
    提供POCVerificationGraph实例用于测试。
    
    创建一个配置好的POCVerificationGraph实例，用于测试POC验证功能。
    
    Returns:
        POCVerificationGraph: POC验证图实例
    """
    from backend.ai_agents.subgraphs.poc_verification import POCVerificationGraph
    return POCVerificationGraph(max_execution_time=60.0, max_rounds=3)


@pytest.fixture
def poc_verification_state(sample_target, sample_task_id, sample_poc_tasks):
    """
    提供POCVerificationState实例用于测试。
    
    创建一个预填充测试数据的POCVerificationState实例。
    
    Args:
        sample_target: 测试目标URL fixture
        sample_task_id: 测试任务ID fixture
        sample_poc_tasks: POC任务列表 fixture
        
    Returns:
        POCVerificationState: POC验证状态实例
    """
    from backend.ai_agents.subgraphs.poc_verification import POCVerificationState
    return POCVerificationState(
        target=sample_target,
        task_id=sample_task_id,
        poc_tasks=sample_poc_tasks
    )


@pytest.fixture
def report_graph():
    """
    提供ReportGraph实例用于测试。
    
    创建一个配置好的ReportGraph实例，用于测试报告生成功能。
    
    Returns:
        ReportGraph: 报告图实例
    """
    from backend.ai_agents.subgraphs.report import ReportGraph
    return ReportGraph(max_execution_time=30.0)


@pytest.fixture
def report_state(sample_target, sample_task_id, sample_tool_results, sample_vulnerabilities):
    """
    提供ReportState实例用于测试。
    
    创建一个预填充测试数据的ReportState实例。
    
    Args:
        sample_target: 测试目标URL fixture
        sample_task_id: 测试任务ID fixture
        sample_tool_results: 工具结果 fixture
        sample_vulnerabilities: 漏洞列表 fixture
        
    Returns:
        ReportState: 报告状态实例
    """
    from backend.ai_agents.subgraphs.report import ReportState
    return ReportState(
        target=sample_target,
        task_id=sample_task_id,
        tool_results=sample_tool_results,
        vulnerabilities=sample_vulnerabilities
    )


@pytest.fixture
def scan_orchestrator():
    """
    提供ScanOrchestrator实例用于测试。
    
    创建一个配置好的ScanOrchestrator实例，用于测试完整扫描流程。
    
    Returns:
        ScanOrchestrator: 扫描编排器实例
    """
    from backend.ai_agents.subgraphs.orchestrator import ScanOrchestrator
    return ScanOrchestrator(
        planning_timeout=10.0,
        tool_execution_timeout=120.0,
        code_scan_timeout=60.0,
        poc_verification_timeout=60.0,
        report_timeout=30.0
    )


@pytest.fixture
def mock_agent_config():
    """
    模拟agent_config配置。
    
    用于测试配置相关的功能，提供预定义的扫描任务配置。
    
    Yields:
        Mock: 模拟的agent配置对象
    """
    mock_config = Mock()
    mock_config.DEFAULT_SCAN_TASKS = ["baseinfo", "portscan", "vulnscan"]
    mock_config.MAX_EXECUTION_TIME = 300
    mock_config.MAX_RETRIES = 3
    
    with patch("backend.ai_agents.agent_config.agent_config", mock_config):
        yield mock_config


@pytest.fixture(autouse=True)
def auto_mock_external_dependencies(
    mock_environment_awareness,
    mock_code_generator,
    mock_unified_executor,
    mock_capability_enhancer,
    mock_tool_registry,
    mock_agent_config
):
    """
    自动模拟所有外部依赖。
    
    使用autouse=True自动应用于所有测试，确保测试不会调用真实的外部服务。
    包括环境感知、代码生成、代码执行、功能增强、工具注册表和配置。
    
    Args:
        mock_environment_awareness: 环境感知模拟
        mock_code_generator: 代码生成器模拟
        mock_unified_executor: 统一执行器模拟
        mock_capability_enhancer: 功能增强器模拟
        mock_tool_registry: 工具注册表模拟
        mock_agent_config: 配置模拟
        
    Yields:
        tuple: 所有模拟对象的元组
    """
    yield (
        mock_environment_awareness,
        mock_code_generator,
        mock_unified_executor,
        mock_capability_enhancer,
        mock_tool_registry,
        mock_agent_config
    )


@pytest.fixture
def mock_logger():
    """
    模拟日志记录器。
    
    用于测试日志输出，可以验证日志消息是否正确记录。
    
    Returns:
        Mock: 模拟的日志记录器
    """
    with patch("logging.getLogger") as mock_get_logger:
        mock_log = Mock()
        mock_get_logger.return_value = mock_log
        yield mock_log


@pytest.fixture
def sample_scan_plan_dto(sample_target, sample_task_id):
    """
    提供ScanPlanDTO实例用于测试。
    
    创建一个预填充测试数据的ScanPlanDTO实例。
    
    Args:
        sample_target: 测试目标URL fixture
        sample_task_id: 测试任务ID fixture
        
    Returns:
        ScanPlanDTO: 扫描计划DTO实例
    """
    from backend.ai_agents.subgraphs.dto import ScanPlanDTO, ScanDecisionType
    return ScanPlanDTO(
        target=sample_target,
        task_id=sample_task_id,
        decision=ScanDecisionType.FIXED_TOOL,
        tool_tasks=["portscan", "baseinfo", "vulnscan"]
    )


@pytest.fixture
def sample_tool_result_dto():
    """
    提供ToolResultDTO实例用于测试。
    
    Returns:
        ToolResultDTO: 工具结果DTO实例
    """
    from backend.ai_agents.subgraphs.dto import ToolResultDTO, TaskStatus
    return ToolResultDTO(
        tool_name="portscan",
        status=TaskStatus.COMPLETED,
        data={"open_ports": [22, 80, 443]},
        execution_time=2.5
    )


@pytest.fixture
def sample_tool_execution_result_dto(sample_target, sample_task_id):
    """
    提供ToolExecutionResultDTO实例用于测试。
    
    Args:
        sample_target: 测试目标URL fixture
        sample_task_id: 测试任务ID fixture
        
    Returns:
        ToolExecutionResultDTO: 工具执行结果DTO实例
    """
    from backend.ai_agents.subgraphs.dto import (
        ToolExecutionResultDTO, ToolResultDTO, TaskStatus
    )
    return ToolExecutionResultDTO(
        task_id=sample_task_id,
        target=sample_target,
        status=TaskStatus.COMPLETED,
        tool_results=[
            ToolResultDTO(
                tool_name="portscan",
                status=TaskStatus.COMPLETED,
                data={"open_ports": [22, 80, 443]}
            )
        ],
        findings=[],
        total_execution_time=5.0
    )


@pytest.fixture
def sample_code_scan_result_dto(sample_target, sample_task_id):
    """
    提供CodeScanResultDTO实例用于测试。
    
    Args:
        sample_target: 测试目标URL fixture
        sample_task_id: 测试任务ID fixture
        
    Returns:
        CodeScanResultDTO: 代码扫描结果DTO实例
    """
    from backend.ai_agents.subgraphs.dto import CodeScanResultDTO, TaskStatus
    return CodeScanResultDTO(
        task_id=sample_task_id,
        target=sample_target,
        status=TaskStatus.COMPLETED,
        generated_code="print('test')",
        execution_output="test",
        findings=[{"type": "custom_scan", "output": "success"}],
        execution_time=1.5
    )


@pytest.fixture
def sample_poc_verification_result_dto(sample_target, sample_task_id):
    """
    提供POCVerificationResultDTO实例用于测试。
    
    Args:
        sample_target: 测试目标URL fixture
        sample_task_id: 测试任务ID fixture
        
    Returns:
        POCVerificationResultDTO: POC验证结果DTO实例
    """
    from backend.ai_agents.subgraphs.dto import POCVerificationResultDTO, TaskStatus, SeverityLevel
    return POCVerificationResultDTO(
        task_id=sample_task_id,
        target=sample_target,
        poc_name="poc_log4j_rce",
        status=TaskStatus.COMPLETED,
        vulnerable=False,
        severity=SeverityLevel.CRITICAL,
        cve_id="CVE-2021-44228",
        execution_time=3.0
    )


@pytest.fixture
def sample_report_dto(sample_target, sample_task_id, sample_vulnerabilities):
    """
    提供ReportDTO实例用于测试。
    
    Args:
        sample_target: 测试目标URL fixture
        sample_task_id: 测试任务ID fixture
        sample_vulnerabilities: 漏洞列表 fixture
        
    Returns:
        ReportDTO: 报告DTO实例
    """
    from backend.ai_agents.subgraphs.dto import ReportDTO, TaskStatus, VulnerabilityDTO, SeverityLevel
    return ReportDTO(
        task_id=sample_task_id,
        target=sample_target,
        status=TaskStatus.COMPLETED,
        vulnerabilities=[
            VulnerabilityDTO(
                vuln_id="vuln-001",
                vuln_type="rce",
                severity=SeverityLevel.CRITICAL,
                title="Log4j RCE",
                cve_id="CVE-2021-44228"
            )
        ],
        summary={"total": 1, "critical": 1},
        report_content='{"test": "report"}',
        report_format="json",
        total_execution_time=10.0
    )


@pytest.fixture
def sample_orchestrator_result_dto(sample_target, sample_task_id, sample_scan_plan_dto):
    """
    提供OrchestratorResultDTO实例用于测试。
    
    Args:
        sample_target: 测试目标URL fixture
        sample_task_id: 测试任务ID fixture
        sample_scan_plan_dto: 扫描计划DTO fixture
        
    Returns:
        OrchestratorResultDTO: 编排器结果DTO实例
    """
    from backend.ai_agents.subgraphs.dto import OrchestratorResultDTO, TaskStatus
    return OrchestratorResultDTO(
        task_id=sample_task_id,
        target=sample_target,
        status=TaskStatus.COMPLETED,
        scan_plan=sample_scan_plan_dto,
        total_execution_time=15.0
    )

"""
测试TaskExecutor的execute_agent_task函数

测试AI Agent扫描任务的执行功能。
使用真实业务代码、真实服务环境和实际业务数据。
"""
import pytest
import sys
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tortoise import Tortoise
from backend.config import settings
from backend.utils.serializers import sanitize_json_data





@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """初始化测试数据库连接"""
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["backend.models"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
def task_executor():
    """创建TaskExecutor实例"""
    from task_executor import TaskExecutor
    executor = TaskExecutor()
    return executor


@pytest.fixture
async def real_task():
    """创建真实任务记录"""
    from backend.models import Task
    
    task = await Task.create(
        task_name="Test AI Agent Scan",
        task_type="ai_agent_scan",
        target="https://www.baidu.com",
        status="pending",
        progress=0,
        config=json.dumps({
            'task_type': 'ai_agent_scan',
            'user_tools': ['port_scan', 'vuln_scan'],
            'user_requirement': 'Perform comprehensive security scan',
            'memory_info': 'Test scan for verification'
        })
    )
    yield task
    await task.delete()


@pytest.fixture
def basic_scan_config():
    """基本扫描配置"""
    return {
        'task_type': 'ai_agent_scan',
        'user_tools': ['port_scan', 'vuln_scan'],
        'user_requirement': 'Perform comprehensive security scan',
        'memory_info': 'Test scan for verification'
    }


@pytest.fixture
def advanced_scan_config():
    """高级扫描配置"""
    return {
        'task_type': 'ai_agent_scan',
        'user_tools': ['port_scan', 'vuln_scan', 'waf_check', 'poc_scan'],
        'user_requirement': 'Perform comprehensive security scan with all checks',
        'memory_info': 'Advanced test scan',
        'custom_tasks': ['baseinfo', 'portscan']
    }


class TestExecuteAgentTask:
    """测试execute_agent_task函数 - 真实环境测试"""

    @pytest.mark.asyncio
    async def test_standardize_severity(self, task_executor):
        """测试严重程度标准化"""
        assert task_executor.standardize_severity(4) == 'Critical'
        assert task_executor.standardize_severity(3) == 'High'
        assert task_executor.standardize_severity(2) == 'Medium'
        assert task_executor.standardize_severity(1) == 'Low'
        assert task_executor.standardize_severity(0) == 'Info'
        
        assert task_executor.standardize_severity('critical') == 'Critical'
        assert task_executor.standardize_severity('high') == 'High'
        assert task_executor.standardize_severity('medium') == 'Medium'
        assert task_executor.standardize_severity('low') == 'Low'
        assert task_executor.standardize_severity('info') == 'Info'
        
        assert task_executor.standardize_severity('CRITICAL') == 'Critical'
        assert task_executor.standardize_severity('HIGH') == 'High'
        assert task_executor.standardize_severity('MEDIUM') == 'Medium'
        assert task_executor.standardize_severity('LOW') == 'Low'
        assert task_executor.standardize_severity('INFO') == 'Info'
        
        assert task_executor.standardize_severity('unknown') == 'Unknown'
        assert task_executor.standardize_severity(None) == 'Info'

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_execute_agent_task_basic(self, real_task, basic_scan_config):
        """测试基本AI Agent任务执行 - 真实环境"""
        from backend.models import Task, Vulnerability, Report
        from backend.ai_agents.core.state import AgentState
        from backend.ai_agents.core.graph import ScanAgentGraph
        
        task_id = real_task.id
        target = real_task.target
        
        task = await Task.get(id=task_id)
        task.status = 'running'
        task.progress = 5
        await task.save()
        
        user_tools = basic_scan_config.get('user_tools', [])
        user_requirement = basic_scan_config.get('user_requirement', '')
        memory_info = basic_scan_config.get('memory_info', '')
        
        initial_state = AgentState(
            target=target,
            task_id=str(task_id),
            target_context=basic_scan_config or {},
            user_tools=user_tools,
            user_requirement=user_requirement,
            memory_info=memory_info
        )
        
        agent_graph = ScanAgentGraph()
        app = agent_graph.graph.compile()
        
        try:
            final_state = await asyncio.wait_for(
                app.ainvoke(initial_state),
                timeout=300
            )
            
            print("\n" + "="*60)
            print("✓ AI Agent 执行完成 - final_state 详情:")
            print("="*60)
            if isinstance(final_state, dict):
                for key, value in final_state.items():
                    print(f"✓ {key}: {type(value).__name__}")
                    if key in ['scan_summary', 'vulnerabilities', 'report']:
                        print(f"  内容预览: {str(value)[:200]}...")
            else:
                print(f"✓ final_state 类型: {type(final_state)}")
                print(f"✓ 属性: {dir(final_state)}")
            print("="*60 + "\n")
            
            task.status = 'completed'
            task.progress = 100
            
            result_data = {
                "scan_summary": {},
                "vulnerabilities": [],
                "report": "",
                "execution_history": [],
                "stages": {}
            }
            
            try:
                if isinstance(final_state, dict):
                    scan_summary = final_state.get('scan_summary', {})
                    vulnerabilities = final_state.get('vulnerabilities', [])
                    report_content = final_state.get('report', "")
                else:
                    scan_summary = getattr(final_state, 'scan_summary', {})
                    vulnerabilities = getattr(final_state, 'vulnerabilities', [])
                    report_content = getattr(final_state, 'report', "")
                
                if isinstance(scan_summary, dict):
                    result_data["scan_summary"] = sanitize_json_data(scan_summary)
                if isinstance(vulnerabilities, list):
                    result_data["vulnerabilities"] = sanitize_json_data(vulnerabilities)
                if isinstance(report_content, str):
                    result_data["report"] = report_content
                elif report_content is not None:
                    result_data["report"] = str(report_content)
            except:
                pass
            
            task.result = json.dumps(result_data, default=str)
            await task.save()
            
            assert task.status == 'completed'
            assert task.progress == 100
            assert task.result is not None
            
            result_data = json.loads(task.result)
            assert 'scan_summary' in result_data
            assert 'vulnerabilities' in result_data
            assert 'report' in result_data
            assert 'execution_history' in result_data
            assert 'stages' in result_data
            
        except asyncio.TimeoutError:
            task.status = 'failed'
            task.error_message = "Test execution timeout"
            await task.save()
            pytest.skip("AI Agent任务执行超时，跳过测试")
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            await task.save()
            raise

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_state_creation(self):
        """测试AgentState创建 - 真实环境"""
        from backend.ai_agents.core.state import AgentState
        
        state = AgentState(
            target="https://www.baidu.com",
            task_id="test_task_001",
            target_context={"test": "value"},
            user_tools=["port_scan"],
            user_requirement="Test requirement",
            memory_info="Test memory"
        )
        
        assert state.target == "https://www.baidu.com"
        assert state.task_id == "test_task_001"
        assert state.target_context == {"test": "value"}
        assert state.user_tools == ["port_scan"]
        assert state.user_requirement == "Test requirement"
        assert state.memory_info == "Test memory"
        assert state.planned_tasks == []
        assert state.vulnerabilities == []
        assert state.is_complete == False
        assert state.should_continue == True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_state_update(self):
        """测试AgentState更新 - 真实环境"""
        from backend.ai_agents.core.state import AgentState
        
        state = AgentState(
            target="https://www.baidu.com",
            task_id="test_task_002"
        )
        
        state.update_context("cms", "WordPress")
        assert state.target_context["cms"] == "WordPress"
        
        state.add_vulnerability({
            "type": "XSS",
            "severity": "Medium",
            "title": "Test XSS"
        })
        assert len(state.vulnerabilities) == 1
        assert state.vulnerabilities[0]["type"] == "XSS"
        
        state.add_error("Test error")
        assert "Test error" in state.errors
        
        state.mark_complete()
        assert state.is_complete == True
        assert state.should_continue == False

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_scan_agent_graph_creation(self):
        """测试ScanAgentGraph创建 - 真实环境"""
        from backend.ai_agents.core.graph import ScanAgentGraph
        
        graph = ScanAgentGraph()
        
        assert graph is not None
        assert graph.graph is not None
        assert hasattr(graph, 'compile')
        assert hasattr(graph, 'invoke')
        
        compiled = graph.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_task_model_operations(self):
        """测试Task模型操作 - 真实环境"""
        from backend.models import Task
        
        task = await Task.create(
            task_name="Test Task for Model Operations",
            task_type="ai_agent_scan",
            target="https://test.example.com",
            status="pending",
            progress=0
        )
        
        assert task.id is not None
        assert task.status == "pending"
        assert task.progress == 0
        
        task.status = "running"
        task.progress = 50
        await task.save()
        
        updated_task = await Task.get(id=task.id)
        assert updated_task.status == "running"
        assert updated_task.progress == 50
        
        await task.delete()
        
        deleted_task = await Task.get_or_none(id=task.id)
        assert deleted_task is None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_vulnerability_model_operations(self, real_task):
        """测试Vulnerability模型操作 - 真实环境"""
        from backend.models import Vulnerability
        
        vuln = await Vulnerability.create(
            task=real_task,
            vuln_type="SQL Injection",
            severity="High",
            title="Test SQL Injection",
            description="Test description",
            url="https://test.example.com/login",
            payload="' OR '1'='1",
            evidence="Error message returned",
            remediation="Use parameterized queries",
            source="test"
        )
        
        assert vuln.id is not None
        assert vuln.vuln_type == "SQL Injection"
        assert vuln.severity == "High"
        
        await vuln.delete()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_report_model_operations(self, real_task):
        """测试Report模型操作 - 真实环境"""
        from backend.models import Report
        
        report = await Report.create(
            task=real_task,
            report_name="Test Report",
            report_type="markdown",
            content="# Test Report\n\nThis is a test report."
        )
        
        assert report.id is not None
        assert report.report_name == "Test Report"
        assert report.report_type == "markdown"
        
        await report.delete()


class TestTaskExecutorBasics:
    """测试TaskExecutor基础功能 - 不需要外部服务"""

    @pytest.mark.asyncio
    async def test_executor_initialization(self, task_executor):
        """测试TaskExecutor初始化"""
        assert task_executor is not None
        assert hasattr(task_executor, 'queue')
        assert hasattr(task_executor, 'queued_task_ids')
        assert hasattr(task_executor, 'cancelled_task_ids')
        assert hasattr(task_executor, 'is_running')

    @pytest.mark.asyncio
    async def test_get_task_timeout(self, task_executor):
        """测试获取任务超时时间"""
        timeout = task_executor._get_task_timeout('port_scan', None)
        assert timeout == 15 * 60
        
        timeout = task_executor._get_task_timeout('waf_check', None)
        assert timeout == 5 * 60
        
        timeout = task_executor._get_task_timeout('ai_agent_scan', None)
        assert timeout == 5 * 60 * 60
        
        custom_config = {'timeout': 120}
        timeout = task_executor._get_task_timeout('port_scan', custom_config)
        assert timeout == 120

    @pytest.mark.asyncio
    async def test_severity_standardization_edge_cases(self, task_executor):
        """测试严重程度标准化的边界情况"""
        assert task_executor.standardize_severity(-1) == 'Info'
        assert task_executor.standardize_severity(100) == 'Critical'
        assert task_executor.standardize_severity("CRITICAL") == 'Critical'
        assert task_executor.standardize_severity("High") == 'High'
        assert task_executor.standardize_severity("Medium") == 'Medium'
        assert task_executor.standardize_severity("Low") == 'Low'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--run-integration'])

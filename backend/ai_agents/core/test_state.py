"""
测试Agent状态管理模块

测试 AgentState 类的各项功能。
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.core.state import AgentState


class TestAgentState:
    """
    测试Agent状态类
    """

    @pytest.fixture
    def state(self):
        """
        创建Agent状态实例
        """
        return AgentState(
            target='https://www.baidu.com',
            task_id='test-task-001'
        )

    def test_initialization(self, state):
        """
        测试初始化
        """
        assert state.target == 'https://www.baidu.com'
        assert state.task_id == 'test-task-001'
        assert state.planned_tasks == []
        assert state.completed_tasks == []
        assert state.current_task is None
        assert state.tool_results == {}
        assert state.vulnerabilities == []
        assert state.target_context == {}
        assert state.execution_history == []
        assert state.errors == []
        assert state.retry_count == 0
        assert state.is_complete is False
        assert state.should_continue is True

    def test_add_execution_step(self, state):
        """
        测试添加执行步骤
        """
        state.add_execution_step('baseinfo', {'status': 'success'}, 'success')
        
        assert len(state.execution_history) == 1
        assert state.execution_history[0]['task'] == 'baseinfo'
        assert state.execution_history[0]['status'] == 'success'
        assert 'timestamp' in state.execution_history[0]

    def test_add_multiple_execution_steps(self, state):
        """
        测试添加多个执行步骤
        """
        state.add_execution_step('baseinfo', {'status': 'success'}, 'success')
        state.add_execution_step('portscan', {'status': 'success'}, 'success')
        state.add_execution_step('poc_test', {'status': 'failed'}, 'failed')
        
        assert len(state.execution_history) == 3
        assert state.execution_history[0]['task'] == 'baseinfo'
        assert state.execution_history[1]['task'] == 'portscan'
        assert state.execution_history[2]['task'] == 'poc_test'

    def test_update_context(self, state):
        """
        测试更新目标上下文
        """
        state.update_context('cms', 'WordPress')
        state.update_context('server', 'nginx/1.18.0')
        state.update_context('open_ports', [80, 443, 8080])
        
        assert state.target_context['cms'] == 'WordPress'
        assert state.target_context['server'] == 'nginx/1.18.0'
        assert state.target_context['open_ports'] == [80, 443, 8080]

    def test_update_context_overwrite(self, state):
        """
        测试覆盖上下文值
        """
        state.update_context('cms', 'WordPress')
        assert state.target_context['cms'] == 'WordPress'
        
        state.update_context('cms', 'Drupal')
        assert state.target_context['cms'] == 'Drupal'

    def test_add_vulnerability(self, state):
        """
        测试添加漏洞
        """
        vuln = {
            'cve': 'CVE-2020-2551',
            'severity': 'critical',
            'details': 'WebLogic RCE vulnerability'
        }
        state.add_vulnerability(vuln)
        
        assert len(state.vulnerabilities) == 1
        assert state.vulnerabilities[0] == vuln

    def test_add_multiple_vulnerabilities(self, state):
        """
        测试添加多个漏洞
        """
        vuln1 = {'cve': 'CVE-2020-2551', 'severity': 'critical', 'details': 'Test'}
        vuln2 = {'cve': 'CVE-2018-2628', 'severity': 'high', 'details': 'Test'}
        vuln3 = {'cve': 'CVE-2017-12149', 'severity': 'medium', 'details': 'Test'}
        
        state.add_vulnerability(vuln1)
        state.add_vulnerability(vuln2)
        state.add_vulnerability(vuln3)
        
        assert len(state.vulnerabilities) == 3
        assert state.vulnerabilities[0] == vuln1
        assert state.vulnerabilities[1] == vuln2
        assert state.vulnerabilities[2] == vuln3

    def test_add_error(self, state):
        """
        测试添加错误
        """
        state.add_error('Error 1: Connection timeout')
        state.add_error('Error 2: Invalid response')
        
        assert len(state.errors) == 2
        assert state.errors[0] == 'Error 1: Connection timeout'
        assert state.errors[1] == 'Error 2: Invalid response'

    def test_increment_retry(self, state):
        """
        测试增加重试次数
        """
        assert state.retry_count == 0
        
        state.increment_retry()
        assert state.retry_count == 1
        
        state.increment_retry()
        assert state.retry_count == 2

    def test_reset_retry(self, state):
        """
        测试重置重试次数
        """
        state.increment_retry()
        state.increment_retry()
        assert state.retry_count == 2
        
        state.reset_retry()
        assert state.retry_count == 0

    def test_mark_complete(self, state):
        """
        测试标记任务完成
        """
        assert state.is_complete is False
        assert state.should_continue is True
        
        state.mark_complete()
        
        assert state.is_complete is True
        assert state.should_continue is False

    def test_get_progress_empty(self, state):
        """
        测试获取进度（空任务列表）
        """
        progress = state.get_progress()
        assert progress == 100.0

    def test_get_progress_with_tasks(self, state):
        """
        测试获取进度（有任务列表）
        """
        state.planned_tasks = ['task1', 'task2', 'task3']
        state.completed_tasks = ['task1']
        
        progress = state.get_progress()
        assert abs(progress - 33.33) < 0.1  # 1/3 ≈ 33.33%

    def test_get_progress_half_complete(self, state):
        """
        测试获取进度（完成一半）
        """
        state.planned_tasks = ['task1', 'task2', 'task3', 'task4']
        state.completed_tasks = ['task1', 'task2']
        
        progress = state.get_progress()
        assert progress == 50.0

    def test_get_progress_all_complete(self, state):
        """
        测试获取进度（全部完成）
        """
        state.planned_tasks = ['task1', 'task2', 'task3']
        state.completed_tasks = ['task1', 'task2', 'task3']
        
        progress = state.get_progress()
        assert progress == 100.0

    def test_to_dict(self, state):
        """
        测试转换为字典
        """
        state.planned_tasks = ['task1', 'task2']
        state.completed_tasks = ['task1']
        state.current_task = 'task2'
        state.add_vulnerability({'cve': 'CVE-2020-2551', 'severity': 'critical'})
        state.update_context('cms', 'WordPress')
        state.add_error('Test error')
        
        state_dict = state.to_dict()
        
        assert state_dict['target'] == 'https://www.baidu.com'
        assert state_dict['task_id'] == 'test-task-001'
        assert state_dict['planned_tasks'] == ['task1', 'task2']
        assert state_dict['completed_tasks'] == ['task1']
        assert state_dict['current_task'] == 'task2'
        assert len(state_dict['vulnerabilities']) == 1
        assert state_dict['target_context']['cms'] == 'WordPress'
        assert len(state_dict['errors']) == 1
        assert state_dict['retry_count'] == 0
        assert state_dict['is_complete'] is False
        assert state_dict['should_continue'] is True
        assert 'progress' in state_dict

    def test_state_with_full_workflow(self, state):
        """
        测试完整工作流的状态变化
        """
        state.planned_tasks = ['baseinfo', 'portscan', 'poc_test']
        
        state.add_execution_step('baseinfo', {'status': 'success'}, 'success')
        state.completed_tasks.append('baseinfo')
        state.update_context('server', 'nginx')
        
        state.add_execution_step('portscan', {'status': 'success'}, 'success')
        state.completed_tasks.append('portscan')
        state.update_context('open_ports', [80, 443])
        
        state.add_execution_step('poc_test', {'status': 'success'}, 'success')
        state.completed_tasks.append('poc_test')
        state.add_vulnerability({'cve': 'CVE-2020-2551', 'severity': 'critical'})
        
        state.mark_complete()
        
        assert len(state.execution_history) == 3
        assert len(state.completed_tasks) == 3
        assert len(state.vulnerabilities) == 1
        assert state.is_complete is True
        assert state.get_progress() == 100.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
测试报告生成器模块

测试 ReportGenerator 类的各项功能。
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.analyzers.report_gen import ReportGenerator
from backend.ai_agents.core.state import AgentState


class TestReportGenerator:
    """
    测试报告生成器类
    """

    @pytest.fixture
    def report_generator(self):
        """
        创建报告生成器实例
        """
        return ReportGenerator()

    @pytest.fixture
    def sample_state(self):
        """
        创建示例Agent状态
        """
        state = AgentState(
            target='https://www.baidu.com',
            task_id='test-task-001'
        )
        
        state.planned_tasks = ['baseinfo', 'portscan', 'poc_weblogic_2020_2551']
        state.completed_tasks = ['baseinfo', 'portscan']
        state.current_task = 'poc_weblogic_2020_2551'
        
        state.tool_results = {
            'baseinfo': {
                'status': 'success',
                'data': {
                    'server': 'nginx/1.18.0',
                    'cms': 'WordPress'
                }
            },
            'portscan': {
                'status': 'success',
                'data': {
                    'open_ports': [80, 443, 8080]
                }
            }
        }
        
        state.vulnerabilities = [
            {
                'cve': 'CVE-2020-2551',
                'severity': 'critical',
                'details': 'WebLogic RCE vulnerability',
                'fix_suggestion': 'Upgrade to latest version'
            },
            {
                'cve': 'CVE-2018-2628',
                'severity': 'high',
                'details': 'WebLogic RCE vulnerability'
            }
        ]
        
        state.target_context = {
            'server': 'nginx/1.18.0',
            'cms': 'WordPress',
            'open_ports': [80, 443, 8080],
            'waf': 'Cloudflare',
            'cdn': True
        }
        
        state.execution_history = [
            {
                'task': 'baseinfo',
                'result': {'status': 'success'},
                'status': 'success',
                'timestamp': 1234567890.0
            },
            {
                'task': 'portscan',
                'result': {'status': 'success'},
                'status': 'success',
                'timestamp': 1234567900.0
            }
        ]
        
        state.errors = []
        
        return state

    def test_initialization(self, report_generator):
        """
        测试初始化
        """
        assert report_generator is not None

    def test_generate_report(self, report_generator, sample_state):
        """
        测试生成报告
        """
        report = report_generator.generate_report(sample_state)
        
        assert isinstance(report, dict)
        assert 'task_id' in report
        assert 'target' in report
        assert 'scan_time' in report
        assert 'duration' in report
        assert 'status' in report
        assert 'progress' in report
        assert 'tasks' in report
        assert 'target_context' in report
        assert 'vulnerabilities' in report
        assert 'tool_results' in report
        assert 'errors' in report
        assert 'execution_history' in report

    def test_generate_report_task_info(self, report_generator, sample_state):
        """
        测试报告任务信息
        """
        report = report_generator.generate_report(sample_state)
        
        assert report['task_id'] == 'test-task-001'
        assert report['target'] == 'https://www.baidu.com'
        assert report['status'] in ['completed', 'failed']

    def test_generate_report_tasks_section(self, report_generator, sample_state):
        """
        测试报告任务部分
        """
        report = report_generator.generate_report(sample_state)
        
        tasks = report['tasks']
        assert 'planned' in tasks
        assert 'completed' in tasks
        assert 'total' in tasks
        assert len(tasks['planned']) == 3
        assert len(tasks['completed']) == 2
        assert tasks['total'] == 5

    def test_generate_report_vulnerabilities_section(self, report_generator, sample_state):
        """
        测试报告漏洞部分
        """
        report = report_generator.generate_report(sample_state)
        
        vulns = report['vulnerabilities']
        assert 'list' in vulns
        assert 'total' in vulns
        assert 'summary' in vulns
        assert vulns['total'] == 2
        assert len(vulns['list']) == 2

    def test_generate_report_tool_results_section(self, report_generator, sample_state):
        """
        测试报告工具结果部分
        """
        report = report_generator.generate_report(sample_state)
        
        tool_results = report['tool_results']
        assert 'total' in tool_results
        assert 'success' in tool_results
        assert 'failed' in tool_results
        assert 'timeout' in tool_results
        assert 'details' in tool_results
        assert tool_results['total'] == 2
        assert tool_results['success'] == 2

    def test_generate_html_report(self, report_generator, sample_state):
        """
        测试生成HTML报告
        """
        html = report_generator.generate_html_report(sample_state)
        
        assert isinstance(html, str)
        assert '<!DOCTYPE html>' in html
        assert '<html' in html
        assert '</html>' in html
        assert '<head>' in html
        assert '<body>' in html
        assert 'https://www.baidu.com' in html
        assert 'test-task-001' in html

    def test_generate_html_report_structure(self, report_generator, sample_state):
        """
        测试HTML报告结构
        """
        html = report_generator.generate_html_report(sample_state)
        
        assert 'Web安全扫描报告' in html
        assert '扫描摘要' in html
        assert '目标信息' in html
        assert '漏洞详情' in html
        assert '工具执行结果' in html

    def test_calculate_duration(self, report_generator, sample_state):
        """
        测试计算持续时间
        """
        duration = report_generator._calculate_duration(sample_state)
        
        assert isinstance(duration, float)
        assert duration > 0

    def test_calculate_duration_empty_history(self, report_generator):
        """
        测试空历史记录的持续时间
        """
        state = AgentState(target='https://www.baidu.com', task_id='test-001')
        duration = report_generator._calculate_duration(state)
        
        assert duration == 0.0

    def test_generate_vuln_summary(self, report_generator):
        """
        测试生成漏洞摘要
        """
        vulnerabilities = [
            {'severity': 'critical', 'details': 'Test'},
            {'severity': 'high', 'details': 'Test'},
            {'severity': 'high', 'details': 'Test'},
            {'severity': 'medium', 'details': 'Test'}
        ]
        
        summary = report_generator._generate_vuln_summary(vulnerabilities)
        
        assert '共发现' in summary
        assert '个漏洞' in summary
        assert 'Critical' in summary or 'critical' in summary
        assert 'High' in summary or 'high' in summary
        assert 'Medium' in summary or 'medium' in summary

    def test_generate_vuln_summary_empty(self, report_generator):
        """
        测试空漏洞列表摘要
        """
        summary = report_generator._generate_vuln_summary([])
        
        assert summary == '未发现漏洞'

    def test_summarize_tool_results(self, report_generator):
        """
        测试汇总工具结果
        """
        tool_results = {
            'tool1': {'status': 'success', 'data': {}},
            'tool2': {'status': 'failed', 'error': 'Test error'},
            'tool3': {'status': 'timeout', 'error': 'Timeout'},
            'tool4': {'status': 'success'}
        }
        
        summary = report_generator._summarize_tool_results(tool_results)
        
        assert summary['total'] == 4
        assert summary['success'] == 2
        assert summary['failed'] == 1
        assert summary['timeout'] == 1
        assert 'details' in summary

    def test_generate_context_rows(self, report_generator):
        """
        测试生成上下文表格行
        """
        context = {
            'server': 'nginx/1.18.0',
            'cms': 'WordPress',
            'open_ports': [80, 443, 8080]
        }
        
        rows = report_generator._generate_context_rows(context)
        
        assert '<tr>' in rows
        assert '</tr>' in rows
        assert 'server' in rows
        assert 'cms' in rows
        assert 'open_ports' in rows

    def test_generate_vuln_rows(self, report_generator):
        """
        测试生成漏洞HTML行
        """
        vulnerabilities = [
            {
                'cve': 'CVE-2020-2551',
                'severity': 'critical',
                'details': 'Test vulnerability',
                'fix_suggestion': 'Upgrade'
            },
            {
                'cve': 'CVE-2018-2628',
                'severity': 'high',
                'details': 'Test vulnerability'
            }
        ]
        
        rows = report_generator._generate_vuln_rows(vulnerabilities)
        
        assert 'CVE-2020-2551' in rows
        assert 'CVE-2018-2628' in rows
        assert 'critical' in rows
        assert 'high' in rows

    def test_generate_vuln_rows_empty(self, report_generator):
        """
        测试空漏洞列表HTML行
        """
        rows = report_generator._generate_vuln_rows([])
        
        assert '未发现漏洞' in rows

    def test_generate_tool_rows(self, report_generator):
        """
        测试生成工具结果HTML行
        """
        tool_results = {
            'tool1': {'status': 'success', 'data': {}},
            'tool2': {'status': 'failed', 'error': 'Test'},
            'tool3': {'status': 'timeout'}
        }
        
        rows = report_generator._generate_tool_rows(tool_results)
        
        assert 'tool1' in rows
        assert 'tool2' in rows
        assert 'tool3' in rows
        assert 'SUCCESS' in rows
        assert 'FAILED' in rows
        assert 'TIMEOUT' in rows

    def test_generate_error_section(self, report_generator):
        """
        测试生成错误部分
        """
        errors = ['Error 1', 'Error 2', 'Error 3']
        
        section = report_generator._generate_error_section(errors)
        
        assert '执行错误' in section
        assert 'Error 1' in section
        assert 'Error 2' in section
        assert 'Error 3' in section

    def test_generate_error_section_empty(self, report_generator):
        """
        测试空错误列表部分
        """
        section = report_generator._generate_error_section([])
        
        assert section == ''


if __name__ == '__main__':
    import sys
    
    pytest.main([__file__, '-v'])

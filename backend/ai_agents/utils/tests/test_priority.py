"""
测试任务优先级管理模块

测试 TaskPriorityManager 类的各项功能。
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.utils.priority import TaskPriorityManager


class TestTaskPriorityManager:
    """
    测试任务优先级管理器类
    """

    @pytest.fixture
    def priority_manager(self):
        """
        创建任务优先级管理器实例
        """
        return TaskPriorityManager()

    def test_initialization(self, priority_manager):
        """
        测试初始化
        """
        assert priority_manager is not None
        assert hasattr(priority_manager, 'priority_weights')
        assert isinstance(priority_manager.priority_weights, dict)

    def test_get_base_priority_poc(self, priority_manager):
        """
        测试获取POC任务的基础优先级
        """
        priority = priority_manager._get_base_priority('poc_weblogic_2020_2551')
        
        assert priority > 0
        assert priority >= 0.8

    def test_get_base_priority_portscan(self, priority_manager):
        """
        测试获取端口扫描任务的基础优先级
        """
        priority = priority_manager._get_base_priority('portscan')
        
        assert priority > 0
        assert priority >= 0.4

    def test_get_base_priority_baseinfo(self, priority_manager):
        """
        测试获取基础信息收集任务的基础优先级
        """
        priority = priority_manager._get_base_priority('baseinfo')
        
        assert priority > 0
        assert priority >= 0.2

    def test_get_base_priority_waf_detect(self, priority_manager):
        """
        测试获取WAF检测任务的基础优先级
        """
        priority = priority_manager._get_base_priority('waf_detect')
        
        assert priority > 0
        assert priority >= 0.3

    def test_get_base_priority_cdn_detect(self, priority_manager):
        """
        测试获取CDN检测任务的基础优先级
        """
        priority = priority_manager._get_base_priority('cdn_detect')
        
        assert priority > 0
        assert priority >= 0.3

    def test_get_base_priority_cms_identify(self, priority_manager):
        """
        测试获取CMS识别任务的基础优先级
        """
        priority = priority_manager._get_base_priority('cms_identify')
        
        assert priority > 0
        assert priority >= 0.3

    def test_get_base_priority_infoleak_scan(self, priority_manager):
        """
        测试获取信息泄露扫描任务的基础优先级
        """
        priority = priority_manager._get_base_priority('infoleak_scan')
        
        assert priority > 0
        assert priority >= 0.3

    def test_get_base_priority_subdomain_scan(self, priority_manager):
        """
        测试获取子域名扫描任务的基础优先级
        """
        priority = priority_manager._get_base_priority('subdomain_scan')
        
        assert priority > 0
        assert priority >= 0.3

    def test_get_base_priority_unknown_task(self, priority_manager):
        """
        测试获取未知任务的基础优先级
        """
        priority = priority_manager._get_base_priority('unknown_task')
        
        assert priority > 0
        assert priority >= 0.4

    def test_calculate_priority_without_context(self, priority_manager):
        """
        测试计算优先级(无上下文)
        """
        priority = priority_manager.calculate_priority('poc_weblogic_2020_2551')
        
        assert priority > 0
        assert isinstance(priority, float)

    def test_calculate_priority_with_waf(self, priority_manager):
        """
        测试计算优先级(有WAF)
        """
        context = {'waf': 'Cloudflare'}
        priority = priority_manager.calculate_priority('poc_weblogic_2020_2551', context)
        
        base_priority = priority_manager._get_base_priority('poc_weblogic_2020_2551')
        assert priority < base_priority

    def test_calculate_priority_with_cdn(self, priority_manager):
        """
        测试计算优先级(有CDN)
        """
        context = {'cdn': True}
        priority = priority_manager.calculate_priority('portscan', context)
        
        base_priority = priority_manager._get_base_priority('portscan')
        assert priority < base_priority

    def test_calculate_priority_with_cms_match(self, priority_manager):
        """
        测试计算优先级(CMS匹配)
        """
        context = {'cms': 'WebLogic'}
        priority = priority_manager.calculate_priority('poc_weblogic_2020_2551', context)
        
        base_priority = priority_manager._get_base_priority('poc_weblogic_2020_2551')
        assert priority > base_priority

    def test_calculate_priority_with_open_ports(self, priority_manager):
        """
        测试计算优先级(开放端口)
        """
        context = {'open_ports': [7001]}
        priority = priority_manager.calculate_priority('poc_weblogic_2020_2551', context)
        
        base_priority = priority_manager._get_base_priority('poc_weblogic_2020_2551')
        assert priority > base_priority

    def test_sort_tasks(self, priority_manager):
        """
        测试任务排序
        """
        tasks = ['baseinfo', 'portscan', 'poc_weblogic_2020_2551', 'cdn_detect']
        
        sorted_tasks = priority_manager.sort_tasks(tasks)
        
        assert len(sorted_tasks) == len(tasks)
        assert isinstance(sorted_tasks, list)

    def test_sort_tasks_with_context(self, priority_manager):
        """
        测试任务排序(带上下文)
        """
        tasks = ['baseinfo', 'portscan', 'poc_weblogic_2020_2551', 'cdn_detect']
        context = {'cms': 'WebLogic', 'open_ports': [7001]}
        
        sorted_tasks = priority_manager.sort_tasks(tasks, context)
        
        assert len(sorted_tasks) == len(tasks)
        assert isinstance(sorted_tasks, list)

    def test_sort_tasks_priority_order(self, priority_manager):
        """
        测试任务排序的优先级顺序
        """
        tasks = ['baseinfo', 'poc_weblogic_2020_2551', 'portscan']
        
        sorted_tasks = priority_manager.sort_tasks(tasks)
        
        poc_index = sorted_tasks.index('poc_weblogic_2020_2551')
        baseinfo_index = sorted_tasks.index('baseinfo')
        
        assert poc_index < baseinfo_index

    def test_sort_tasks_empty(self, priority_manager):
        """
        测试空任务列表排序
        """
        sorted_tasks = priority_manager.sort_tasks([])
        
        assert sorted_tasks == []

    def test_sort_tasks_single(self, priority_manager):
        """
        测试单个任务排序
        """
        tasks = ['portscan']
        
        sorted_tasks = priority_manager.sort_tasks(tasks)
        
        assert sorted_tasks == tasks

    def test_get_critical_tasks(self, priority_manager):
        """
        测试获取关键任务
        """
        tasks = [
            'baseinfo',
            'portscan',
            'poc_weblogic_2020_2551',
            'poc_struts2_009',
            'cdn_detect'
        ]
        
        critical_tasks = priority_manager.get_critical_tasks(tasks)
        
        assert isinstance(critical_tasks, list)
        assert len(critical_tasks) >= 2
        assert all('poc_' in task for task in critical_tasks)

    def test_get_critical_tasks_empty(self, priority_manager):
        """
        测试获取关键任务(空列表)
        """
        critical_tasks = priority_manager.get_critical_tasks([])
        
        assert critical_tasks == []

    def test_get_critical_tasks_no_critical(self, priority_manager):
        """
        测试获取关键任务(无关键任务)
        """
        tasks = ['baseinfo', 'cdn_detect', 'subdomain_scan']
        
        critical_tasks = priority_manager.get_critical_tasks(tasks)
        
        assert isinstance(critical_tasks, list)
        assert len(critical_tasks) == 0

    def test_adjust_by_context_waf(self, priority_manager):
        """
        测试根据WAF调整优先级
        """
        base_priority = 0.9
        context = {'waf': 'Cloudflare'}
        
        adjusted = priority_manager._adjust_by_context(
            'poc_weblogic_2020_2551',
            base_priority,
            context
        )
        
        assert adjusted < base_priority
        assert adjusted >= 0

    def test_adjust_by_context_cdn(self, priority_manager):
        """
        测试根据CDN调整优先级
        """
        base_priority = 0.5
        context = {'cdn': True}
        
        adjusted = priority_manager._adjust_by_context(
            'portscan',
            base_priority,
            context
        )
        
        assert adjusted < base_priority
        assert adjusted >= 0

    def test_adjust_by_context_cms_match(self, priority_manager):
        """
        测试根据CMS匹配调整优先级
        """
        base_priority = 0.9
        context = {'cms': 'WebLogic'}
        
        adjusted = priority_manager._adjust_by_context(
            'poc_weblogic_2020_2551',
            base_priority,
            context
        )
        
        assert adjusted > base_priority
        assert adjusted <= 1.0

    def test_adjust_by_context_no_context(self, priority_manager):
        """
        测试无上下文时调整优先级
        """
        base_priority = 0.5
        context = {}
        
        adjusted = priority_manager._adjust_by_context(
            'portscan',
            base_priority,
            context
        )
        
        assert adjusted == base_priority

    def test_get_pocs_by_port_7001(self, priority_manager):
        """
        测试根据端口7001获取POC
        """
        pocs = priority_manager._get_pocs_by_port(7001)
        
        assert isinstance(pocs, list)
        assert len(pocs) > 0
        assert any('weblogic' in poc.lower() for poc in pocs)

    def test_get_pocs_by_port_8080(self, priority_manager):
        """
        测试根据端口8080获取POC
        """
        pocs = priority_manager._get_pocs_by_port(8080)
        
        assert isinstance(pocs, list)
        assert len(pocs) > 0
        assert any('tomcat' in poc.lower() for poc in pocs)

    def test_get_pocs_by_port_unknown(self, priority_manager):
        """
        测试根据未知端口获取POC
        """
        pocs = priority_manager._get_pocs_by_port(9999)
        
        assert isinstance(pocs, list)
        assert len(pocs) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

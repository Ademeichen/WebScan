"""
测试环境感知模块

测试 EnvironmentAwareness 类的各项功能。
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_agents.code_execution.environment import EnvironmentAwareness


class TestEnvironmentAwareness:
    """
    测试环境感知类
    """

    @pytest.fixture
    def env_awareness(self):
        """
        创建环境感知实例
        """
        return EnvironmentAwareness()

    def test_initialization(self, env_awareness):
        """
        测试初始化
        """
        assert env_awareness is not None
        assert hasattr(env_awareness, 'os_info')
        assert hasattr(env_awareness, 'python_info')
        assert hasattr(env_awareness, 'available_tools')
        assert hasattr(env_awareness, 'network_info')
        assert hasattr(env_awareness, 'system_resources')

    def test_detect_os(self, env_awareness):
        """
        测试操作系统检测
        """
        os_info = env_awareness.os_info
        assert 'system' in os_info
        assert 'release' in os_info
        assert 'version' in os_info
        assert 'machine' in os_info
        assert os_info['system'] in ['Windows', 'Linux', 'Darwin', 'Java']

    def test_detect_python(self, env_awareness):
        """
        测试Python版本检测
        """
        python_info = env_awareness.python_info
        assert 'version' in python_info
        assert 'executable' in python_info
        assert 'dependencies' in python_info
        
        version = python_info['version']
        assert isinstance(version, str)
        assert len(version.split('.')) >= 2

    def test_detect_tools(self, env_awareness):
        """
        测试工具检测
        """
        tools = env_awareness.available_tools
        assert isinstance(tools, dict)
        
        expected_tools = ['nmap', 'sqlmap', 'burpsuite', 'metasploit', 'nikto', 'dirb', 'gobuster']
        for tool in expected_tools:
            assert tool in tools
            assert 'available' in tools[tool]
            assert 'version' in tools[tool]
            assert isinstance(tools[tool]['available'], bool)

    def test_detect_network(self, env_awareness):
        """
        测试网络检测
        """
        network_info = env_awareness.network_info
        assert 'hostname' in network_info
        assert 'proxy_detected' in network_info
        assert 'firewall_detected' in network_info
        assert 'internet_available' in network_info
        assert isinstance(network_info['hostname'], str)
        assert isinstance(network_info['proxy_detected'], bool)
        assert isinstance(network_info['firewall_detected'], bool)
        assert isinstance(network_info['internet_available'], bool)

    def test_detect_resources(self, env_awareness):
        """
        测试系统资源检测
        """
        resources = env_awareness.system_resources
        assert 'disk_total' in resources
        assert 'disk_used' in resources
        assert 'disk_free' in resources
        assert 'disk_used_percent' in resources
        assert resources['disk_total'] > 0
        assert resources['disk_used'] >= 0
        assert resources['disk_free'] >= 0
        assert 0 <= resources['disk_used_percent'] <= 100

    def test_get_environment_report(self, env_awareness):
        """
        测试获取环境报告
        """
        report = env_awareness.get_environment_report()
        assert 'os_info' in report
        assert 'python_info' in report
        assert 'available_tools' in report
        assert 'network_info' in report
        assert 'system_resources' in report
        assert 'scan_recommendations' in report
        assert isinstance(report['scan_recommendations'], list)

    def test_is_tool_available(self, env_awareness):
        """
        测试检查工具是否可用
        """
        result = env_awareness.is_tool_available('nmap')
        assert isinstance(result, bool)
        
        result = env_awareness.is_tool_available('nonexistent_tool')
        assert result is False

    def test_get_python_version(self, env_awareness):
        """
        测试获取Python版本
        """
        version = env_awareness.get_python_version()
        assert isinstance(version, str)
        assert version != 'unknown'
        assert len(version) >= 3

    def test_generate_scan_recommendations(self, env_awareness):
        """
        测试生成扫描建议
        """
        recommendations = env_awareness._generate_scan_recommendations()
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

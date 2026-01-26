"""
测试漏洞分析器模块

测试 VulnerabilityAnalyzer 类的各项功能。
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_agents.analyzers.vuln_analyzer import VulnerabilityAnalyzer


class TestVulnerabilityAnalyzer:
    """
    测试漏洞分析器类
    """

    @pytest.fixture
    def analyzer(self):
        """
        创建漏洞分析器实例
        """
        return VulnerabilityAnalyzer()

    @pytest.fixture
    def sample_vulnerabilities(self):
        """
        创建示例漏洞列表
        """
        return [
            {
                'cve': 'CVE-2020-2551',
                'target': 'example.com',
                'severity': 'critical',
                'details': 'WebLogic RCE vulnerability'
            },
            {
                'cve': 'CVE-2018-2628',
                'target': 'example.com',
                'severity': 'high',
                'details': 'WebLogic RCE vulnerability'
            },
            {
                'cve': 'CVE-2017-12149',
                'target': 'example.com',
                'severity': 'medium',
                'details': 'JBoss deserialization vulnerability'
            },
            {
                'cve': 'CVE-2020-14756',
                'target': 'example.com',
                'severity': 'low',
                'details': 'WebLogic information disclosure'
            },
            {
                'cve': 'CVE-2020-2551',
                'target': 'example.com',
                'severity': 'critical',
                'details': 'Duplicate vulnerability'
            },
            {
                'cve': 'CVE-2018-2628',
                'target': 'test.com',
                'severity': 'high',
                'details': 'Same CVE different target'
            }
        ]

    def test_initialization(self, analyzer):
        """
        测试初始化
        """
        assert analyzer is not None
        assert hasattr(analyzer, 'severity_order')
        assert isinstance(analyzer.severity_order, dict)

    def test_deduplicate(self, analyzer, sample_vulnerabilities):
        """
        测试漏洞去重
        """
        deduplicated = analyzer.deduplicate(sample_vulnerabilities)
        
        assert len(deduplicated) == 5
        cve_list = [v['cve'] for v in deduplicated]
        assert cve_list.count('CVE-2020-2551') == 1

    def test_deduplicate_empty(self, analyzer):
        """
        测试空列表去重
        """
        deduplicated = analyzer.deduplicate([])
        assert len(deduplicated) == 0

    def test_deduplicate_single(self, analyzer):
        """
        测试单个漏洞去重
        """
        vulnerabilities = [
            {
                'cve': 'CVE-2020-2551',
                'target': 'example.com',
                'severity': 'critical',
                'details': 'Test vulnerability'
            }
        ]
        deduplicated = analyzer.deduplicate(vulnerabilities)
        assert len(deduplicated) == 1

    def test_sort_by_severity(self, analyzer, sample_vulnerabilities):
        """
        测试按严重度排序
        """
        sorted_vulns = analyzer.sort_by_severity(sample_vulnerabilities)
        
        assert len(sorted_vulns) == len(sample_vulnerabilities)
        assert sorted_vulns[0]['severity'] == 'critical'
        assert sorted_vulns[1]['severity'] == 'critical'
        assert sorted_vulns[-1]['severity'] in ['low', 'info']

    def test_sort_by_severity_empty(self, analyzer):
        """
        测试空列表排序
        """
        sorted_vulns = analyzer.sort_by_severity([])
        assert len(sorted_vulns) == 0

    def test_analyze_empty(self, analyzer):
        """
        测试分析空漏洞列表
        """
        result = analyzer.analyze([])
        
        assert result['total'] == 0
        assert result['by_severity'] == {}
        assert result['summary'] == '未发现漏洞'

    def test_analyze_with_vulnerabilities(self, analyzer, sample_vulnerabilities):
        """
        测试分析漏洞列表
        """
        result = analyzer.analyze(sample_vulnerabilities)
        
        assert result['total'] > 0
        assert 'by_severity' in result
        assert 'summary' in result
        assert '共发现' in result['summary']
        assert '个漏洞' in result['summary']

    def test_analyze_severity_stats(self, analyzer):
        """
        测试严重度统计
        """
        vulnerabilities = [
            {'cve': 'CVE-1', 'severity': 'critical', 'details': 'Test'},
            {'cve': 'CVE-2', 'severity': 'high', 'details': 'Test'},
            {'cve': 'CVE-3', 'severity': 'high', 'details': 'Test'},
            {'cve': 'CVE-4', 'severity': 'medium', 'details': 'Test'},
            {'cve': 'CVE-5', 'severity': 'low', 'details': 'Test'},
            {'cve': 'CVE-6', 'severity': 'info', 'details': 'Test'}
        ]
        
        result = analyzer.analyze(vulnerabilities)
        
        assert result['total'] == 6
        assert result['by_severity']['critical'] == 1
        assert result['by_severity']['high'] == 2
        assert result['by_severity']['medium'] == 1
        assert result['by_severity']['low'] == 1
        assert result['by_severity']['info'] == 1

    def test_enrich_with_kb(self, analyzer):
        """
        测试使用知识库丰富漏洞信息
        """
        vulnerabilities = [
            {
                'cve': 'CVE-2020-2551',
                'target': 'example.com',
                'severity': 'critical',
                'details': 'Test vulnerability'
            },
            {
                'cve': 'CVE-2018-2628',
                'target': 'example.com',
                'severity': 'high',
                'details': 'Test vulnerability'
            }
        ]
        
        enriched = analyzer.enrich_with_kb(vulnerabilities)
        
        assert len(enriched) == 2
        assert all('cve' in v for v in enriched)

    def test_enrich_with_kb_no_cve(self, analyzer):
        """
        测试没有CVE的漏洞
        """
        vulnerabilities = [
            {
                'target': 'example.com',
                'severity': 'medium',
                'details': 'Test vulnerability without CVE'
            }
        ]
        
        enriched = analyzer.enrich_with_kb(vulnerabilities)
        
        assert len(enriched) == 1
        assert 'kb_info' not in enriched[0]

    def test_get_vuln_key(self, analyzer):
        """
        测试获取漏洞唯一键
        """
        vuln = {
            'cve': 'CVE-2020-2551',
            'target': 'example.com',
            'severity': 'critical'
        }
        
        key = analyzer._get_vuln_key(vuln)
        
        assert key == 'CVE-2020-2551_example.com'

    def test_get_vuln_key_missing_fields(self, analyzer):
        """
        测试缺少字段的漏洞键
        """
        vuln = {
            'severity': 'critical'
        }
        
        key = analyzer._get_vuln_key(vuln)
        
        assert key == '_'

    def test_analyze_summary_format(self, analyzer):
        """
        测试分析结果摘要格式
        """
        vulnerabilities = [
            {'cve': 'CVE-1', 'severity': 'critical', 'details': 'Test'},
            {'cve': 'CVE-2', 'severity': 'high', 'details': 'Test'},
            {'cve': 'CVE-3', 'severity': 'medium', 'details': 'Test'}
        ]
        
        result = analyzer.analyze(vulnerabilities)
        
        assert 'Critical' in result['summary'] or 'critical' in result['summary']
        assert 'High' in result['summary'] or 'high' in result['summary']
        assert 'Medium' in result['summary'] or 'medium' in result['summary']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

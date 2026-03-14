import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from vulnerability_scan_plugins.sqli.scanner import SQLiScanner
from vulnerability_scan_plugins.payloads import sqli_payloads


class TestSQLiPlugin:
    """SQL注入插件测试"""
    
    def test_scanner_initialization(self):
        """测试扫描器初始化"""
        scanner = SQLiScanner()
        assert scanner is not None
        assert hasattr(scanner, 'scan')
        assert hasattr(scanner, 'name')
        assert scanner.name == "sqli"
    
    def test_payload_loading(self):
        """测试payload加载"""
        payloads = sqli_payloads.get_all_payloads()
        assert payloads is not None
        assert len(payloads) > 0
        assert isinstance(payloads, list)
    
    def test_error_based_payloads(self):
        """测试报错注入payload"""
        payloads = sqli_payloads.ERROR_BASED_PAYLOADS
        assert len(payloads) > 0
        assert any("'" in p for p in payloads)
    
    def test_union_based_payloads(self):
        """测试联合注入payload"""
        payloads = sqli_payloads.UNION_BASED_PAYLOADS
        assert len(payloads) > 0
        assert any("UNION" in p.upper() for p in payloads)
    
    def test_time_based_payloads(self):
        """测试时间盲注payload"""
        payloads = sqli_payloads.TIME_BASED_PAYLOADS
        assert len(payloads) > 0
        assert any("SLEEP" in p.upper() or "WAITFOR" in p.upper() for p in payloads)
    
    def test_boolean_based_payloads(self):
        """测试布尔盲注payload"""
        payloads = sqli_payloads.BOOLEAN_BASED_PAYLOADS
        assert len(payloads) > 0
    
    def test_scan_with_empty_target(self, sample_target):
        """测试空目标扫描"""
        scanner = SQLiScanner()
        sample_target["params"] = {}
        result = scanner.scan(sample_target)
        assert result is not None
    
    def test_scan_with_params(self, sample_target_with_params):
        """测试带参数目标扫描"""
        scanner = SQLiScanner()
        result = scanner.scan(sample_target_with_params)
        assert result is not None
    
    def test_detection_patterns(self):
        """测试检测模式"""
        patterns = sqli_payloads.DETECTION_PATTERNS
        assert len(patterns) > 0
        assert any("error" in p.lower() or "sql" in p.lower() for p in patterns)
    
    def test_database_specific_payloads(self):
        """测试数据库特定payload"""
        mysql_payloads = sqli_payloads.MYSQL_PAYLOADS
        postgres_payloads = sqli_payloads.POSTGRES_PAYLOADS
        mssql_payloads = sqli_payloads.MSSQL_PAYLOADS
        
        assert len(mysql_payloads) > 0
        assert len(postgres_payloads) > 0
        assert len(mssql_payloads) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

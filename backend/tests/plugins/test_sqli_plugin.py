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
        scanner = SQLiScanner("http://example.com")
        assert scanner is not None
        assert hasattr(scanner, 'scan')
        assert scanner.metadata.name == "sqli_scanner"
    
    def test_payload_loading(self):
        """测试payload加载"""
        assert sqli_payloads.SQLI_PAYLOADS is not None
        assert len(sqli_payloads.SQLI_PAYLOADS) > 0
        assert isinstance(sqli_payloads.SQLI_PAYLOADS, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

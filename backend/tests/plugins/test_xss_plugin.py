import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from vulnerability_scan_plugins.xss.scanner import XSSScanner
from vulnerability_scan_plugins.payloads import xss_payloads


class TestXSSPlugin:
    """XSS插件测试"""
    
    def test_scanner_initialization(self):
        """测试扫描器初始化"""
        scanner = XSSScanner("http://example.com")
        assert scanner is not None
        assert hasattr(scanner, 'scan')
        assert scanner.metadata.name == "xss_scanner"
    
    def test_payload_loading(self):
        """测试payload加载"""
        assert xss_payloads.XSS_PAYLOADS is not None
        assert len(xss_payloads.XSS_PAYLOADS) > 0
        assert isinstance(xss_payloads.XSS_PAYLOADS, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

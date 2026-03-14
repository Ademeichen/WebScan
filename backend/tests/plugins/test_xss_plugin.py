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
        scanner = XSSScanner()
        assert scanner is not None
        assert hasattr(scanner, 'scan')
        assert hasattr(scanner, 'name')
        assert scanner.name == "xss"
    
    def test_payload_loading(self):
        """测试payload加载"""
        payloads = xss_payloads.get_all_payloads()
        assert payloads is not None
        assert len(payloads) > 0
        assert isinstance(payloads, list)
    
    def test_reflected_xss_payloads(self):
        """测试反射型XSS payload"""
        payloads = xss_payloads.REFLECTED_XSS_PAYLOADS
        assert len(payloads) > 0
        assert any("<script>" in p.lower() for p in payloads)
    
    def test_stored_xss_payloads(self):
        """测试存储型XSS payload"""
        payloads = xss_payloads.STORED_XSS_PAYLOADS
        assert len(payloads) > 0
    
    def test_dom_xss_payloads(self):
        """测试DOM型XSS payload"""
        payloads = xss_payloads.DOM_XSS_PAYLOADS
        assert len(payloads) > 0
        assert any("javascript:" in p.lower() or "onerror" in p.lower() for p in payloads)
    
    def test_bypass_payloads(self):
        """测试绕过payload"""
        payloads = xss_payloads.BYPASS_PAYLOADS
        assert len(payloads) > 0
    
    def test_scan_with_empty_target(self, sample_target):
        """测试空目标扫描"""
        scanner = XSSScanner()
        sample_target["params"] = {}
        result = scanner.scan(sample_target)
        assert result is not None
    
    def test_scan_with_params(self, sample_target_with_params):
        """测试带参数目标扫描"""
        scanner = XSSScanner()
        result = scanner.scan(sample_target_with_params)
        assert result is not None
    
    def test_event_handler_payloads(self):
        """测试事件处理器payload"""
        payloads = xss_payloads.EVENT_HANDLER_PAYLOADS
        assert len(payloads) > 0
        assert any("on" in p.lower() for p in payloads)
    
    def test_encoding_payloads(self):
        """测试编码payload"""
        payloads = xss_payloads.ENCODING_PAYLOADS
        assert len(payloads) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

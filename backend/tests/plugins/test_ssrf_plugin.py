import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from vulnerability_scan_plugins.ssrf.scanner import SSRFScanner
from vulnerability_scan_plugins.payloads import ssrf_payloads


class TestSSRFPlugin:
    """SSRF插件测试"""
    
    def test_scanner_initialization(self):
        """测试扫描器初始化"""
        scanner = SSRFScanner()
        assert scanner is not None
        assert hasattr(scanner, 'scan')
        assert hasattr(scanner, 'name')
        assert scanner.name == "ssrf"
    
    def test_payload_loading(self):
        """测试payload加载"""
        payloads = ssrf_payloads.get_all_payloads()
        assert payloads is not None
        assert len(payloads) > 0
        assert isinstance(payloads, list)
    
    def test_internal_ip_payloads(self):
        """测试内网IP payload"""
        payloads = ssrf_payloads.INTERNAL_IP_PAYLOADS
        assert len(payloads) > 0
        assert any("127.0.0.1" in p or "localhost" in p or "192.168" in p for p in payloads)
    
    def test_cloud_metadata_payloads(self):
        """测试云元数据payload"""
        payloads = ssrf_payloads.CLOUD_METADATA_PAYLOADS
        assert len(payloads) > 0
        assert any("metadata" in p.lower() or "169.254" in p for p in payloads)
    
    def test_protocol_payloads(self):
        """测试协议payload"""
        payloads = ssrf_payloads.PROTOCOL_PAYLOADS
        assert len(payloads) > 0
        assert any("file://" in p.lower() or "gopher://" in p.lower() or "dict://" in p.lower() for p in payloads)
    
    def test_bypass_payloads(self):
        """测试绕过payload"""
        payloads = ssrf_payloads.BYPASS_PAYLOADS
        assert len(payloads) > 0
    
    def test_scan_with_empty_target(self, sample_target):
        """测试空目标扫描"""
        scanner = SSRFScanner()
        sample_target["params"] = {}
        result = scanner.scan(sample_target)
        assert result is not None
    
    def test_scan_with_url_param(self, sample_target_with_params):
        """测试带URL参数目标扫描"""
        scanner = SSRFScanner()
        sample_target_with_params["params"]["url"] = "http://example.com"
        result = scanner.scan(sample_target_with_params)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

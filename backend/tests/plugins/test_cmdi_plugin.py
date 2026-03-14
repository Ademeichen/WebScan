import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from vulnerability_scan_plugins.cmdi.scanner import CmdiScanner
from vulnerability_scan_plugins.payloads import cmdi_payloads


class TestCmdiPlugin:
    """命令注入插件测试"""
    
    def test_scanner_initialization(self):
        """测试扫描器初始化"""
        scanner = CmdiScanner()
        assert scanner is not None
        assert hasattr(scanner, 'scan')
        assert hasattr(scanner, 'name')
        assert scanner.name == "cmdi"
    
    def test_payload_loading(self):
        """测试payload加载"""
        payloads = cmdi_payloads.get_all_payloads()
        assert payloads is not None
        assert len(payloads) > 0
        assert isinstance(payloads, list)
    
    def test_linux_payloads(self):
        """测试Linux命令注入payload"""
        payloads = cmdi_payloads.LINUX_PAYLOADS
        assert len(payloads) > 0
        assert any("cat" in p or "ls" in p or "id" in p for p in payloads)
    
    def test_windows_payloads(self):
        """测试Windows命令注入payload"""
        payloads = cmdi_payloads.WINDOWS_PAYLOADS
        assert len(payloads) > 0
        assert any("dir" in p.lower() or "type" in p.lower() or "whoami" in p.lower() for p in payloads)
    
    def test_bypass_payloads(self):
        """测试绕过payload"""
        payloads = cmdi_payloads.BYPASS_PAYLOADS
        assert len(payloads) > 0
    
    def test_blind_payloads(self):
        """测试盲注payload"""
        payloads = cmdi_payloads.BLIND_PAYLOADS
        assert len(payloads) > 0
        assert any("sleep" in p.lower() or "ping" in p.lower() or "timeout" in p.lower() for p in payloads)
    
    def test_scan_with_empty_target(self, sample_target):
        """测试空目标扫描"""
        scanner = CmdiScanner()
        sample_target["params"] = {}
        result = scanner.scan(sample_target)
        assert result is not None
    
    def test_scan_with_params(self, sample_target_with_params):
        """测试带参数目标扫描"""
        scanner = CmdiScanner()
        result = scanner.scan(sample_target_with_params)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

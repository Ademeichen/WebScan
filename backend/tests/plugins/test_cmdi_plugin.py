import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from vulnerability_scan_plugins.cmdi.scanner import CmdiScanner


class TestCmdiPlugin:
    """命令注入插件测试"""
    
    def test_scanner_initialization(self):
        """测试扫描器初始化"""
        scanner = CmdiScanner("http://example.com")
        assert scanner is not None
        assert hasattr(scanner, 'scan')
        assert scanner.metadata.name == "cmdi"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

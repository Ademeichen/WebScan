import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from vulnerability_scan_plugins.fileupload.scanner import FileUploadScanner


class TestFileUploadPlugin:
    """文件上传插件测试"""
    
    def test_scanner_initialization(self):
        """测试扫描器初始化"""
        scanner = FileUploadScanner()
        assert scanner is not None
        assert hasattr(scanner, 'scan')
        assert hasattr(scanner, 'name')
        assert scanner.name == "fileupload"
    
    def test_dangerous_extensions(self):
        """测试危险扩展名检测"""
        scanner = FileUploadScanner()
        dangerous_exts = scanner.get_dangerous_extensions()
        assert len(dangerous_exts) > 0
        assert ".php" in dangerous_exts
        assert ".jsp" in dangerous_exts
        assert ".asp" in dangerous_exts
    
    def test_allowed_extensions(self):
        """测试允许的扩展名"""
        scanner = FileUploadScanner()
        allowed_exts = scanner.get_allowed_extensions()
        assert len(allowed_exts) > 0
        assert ".jpg" in allowed_exts or ".png" in allowed_exts
    
    def test_bypass_techniques(self):
        """测试绕过技术"""
        scanner = FileUploadScanner()
        bypass_techniques = scanner.get_bypass_techniques()
        assert len(bypass_techniques) > 0
    
    def test_scan_with_empty_target(self, sample_target):
        """测试空目标扫描"""
        scanner = FileUploadScanner()
        sample_target["params"] = {}
        result = scanner.scan(sample_target)
        assert result is not None
    
    def test_scan_with_file_param(self, sample_target_with_params):
        """测试带文件参数目标扫描"""
        scanner = FileUploadScanner()
        sample_target_with_params["params"]["file"] = "test.php"
        result = scanner.scan(sample_target_with_params)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

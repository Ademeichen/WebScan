import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from vulnerability_scan_plugins.weakpass.scanner import WeakPassScanner


class TestWeakPassPlugin:
    """弱口令检测插件测试"""
    
    def test_scanner_initialization(self):
        """测试扫描器初始化"""
        scanner = WeakPassScanner()
        assert scanner is not None
        assert hasattr(scanner, 'scan')
        assert hasattr(scanner, 'name')
        assert scanner.name == "weakpass"
    
    def test_common_passwords(self):
        """测试常见密码列表"""
        scanner = WeakPassScanner()
        passwords = scanner.get_common_passwords()
        assert len(passwords) > 0
        assert "123456" in passwords
        assert "admin" in passwords
        assert "password" in passwords
    
    def test_admin_passwords(self):
        """测试管理员密码列表"""
        scanner = WeakPassScanner()
        passwords = scanner.get_admin_passwords()
        assert len(passwords) > 0
    
    def test_database_passwords(self):
        """测试数据库密码列表"""
        scanner = WeakPassScanner()
        passwords = scanner.get_database_passwords()
        assert len(passwords) > 0
        assert "root" in passwords or "admin" in passwords
    
    def test_username_password_pairs(self):
        """测试用户名密码组合"""
        scanner = WeakPassScanner()
        pairs = scanner.get_username_password_pairs()
        assert len(pairs) > 0
        assert any("admin" in pair for pair in pairs)
    
    def test_scan_with_empty_target(self, sample_target):
        """测试空目标扫描"""
        scanner = WeakPassScanner()
        sample_target["params"] = {}
        result = scanner.scan(sample_target)
        assert result is not None
    
    def test_scan_with_auth_params(self, sample_target_with_params):
        """测试带认证参数目标扫描"""
        scanner = WeakPassScanner()
        sample_target_with_params["params"]["username"] = "admin"
        sample_target_with_params["params"]["password"] = "123456"
        result = scanner.scan(sample_target_with_params)
        assert result is not None
    
    def test_password_strength_check(self):
        """测试密码强度检查"""
        scanner = WeakPassScanner()
        
        weak_passwords = ["123456", "password", "admin", "qwerty"]
        for pwd in weak_passwords:
            assert scanner.is_weak_password(pwd) == True
        
        strong_passwords = ["Str0ng@Pass!", "C0mpl3x#Pwd2024"]
        for pwd in strong_passwords:
            assert scanner.is_weak_password(pwd) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

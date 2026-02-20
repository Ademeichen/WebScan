import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from plugins.portscan import portscan_main
from plugins.subdomain import subdomain_main
from plugins.vulnscan import vulnscan_main


class TestPluginFunctionality:
    """插件功能测试"""
    
    @pytest.mark.asyncio
    async def test_portscan_plugin(self):
        """测试端口扫描插件"""
        result = await portscan_main("127.0.0.1", ports=[22, 80, 443])
        assert result is not None
        assert isinstance(result, dict)
        assert "target" in result
        assert "open_ports" in result
    
    @pytest.mark.asyncio
    async def test_portscan_empty_target(self):
        """测试端口扫描插件-空目标"""
        with pytest.raises(ValueError):
            await portscan_main("", ports=[22, 80])
    
    @pytest.mark.asyncio
    async def test_portscan_invalid_port(self):
        """测试端口扫描插件-无效端口"""
        with pytest.raises(ValueError):
            await portscan_main("127.0.0.1", ports=[-1, 99999])
    
    @pytest.mark.asyncio
    async def test_subdomain_plugin(self):
        """测试子域名扫描插件"""
        result = await subdomain_main("example.com")
        assert result is not None
        assert isinstance(result, dict)
        assert "domain" in result
        assert "subdomains" in result
    
    @pytest.mark.asyncio
    async def test_subdomain_empty_domain(self):
        """测试子域名扫描插件-空域名"""
        with pytest.raises(ValueError):
            await subdomain_main("")
    
    @pytest.mark.asyncio
    async def test_vulnscan_plugin(self):
        """测试漏洞扫描插件"""
        result = await vulnscan_main("http://127.0.0.1:8080")
        assert result is not None
        assert isinstance(result, dict)
        assert "target" in result
        assert "vulnerabilities" in result
    
    @pytest.mark.asyncio
    async def test_vulnscan_invalid_url(self):
        """测试漏洞扫描插件-无效URL"""
        with pytest.raises(ValueError):
            await vulnscan_main("not-a-valid-url")

"""
测试工具适配器模块

测试 PluginAdapter 和 POCAdapter 类的各项功能。
"""
import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_agents.tools.adapters import PluginAdapter, POCAdapter


class TestPluginAdapter:
    """
    测试插件适配器类
    """

    @pytest.fixture
    def plugin_adapter(self):
        """
        创建插件适配器实例
        """
        return PluginAdapter()

    def test_adapt_baseinfo(self, plugin_adapter):
        """
        测试适配基础信息收集插件
        """
        func = plugin_adapter.adapt_baseinfo()
        assert func is not None
        assert callable(func)

    def test_adapt_portscan(self, plugin_adapter):
        """
        测试适配端口扫描插件
        """
        func = plugin_adapter.adapt_portscan()
        assert func is not None
        assert callable(func)

    def test_adapt_waf_detect(self, plugin_adapter):
        """
        测试适配WAF检测插件
        """
        func = plugin_adapter.adapt_waf_detect()
        assert func is not None
        assert callable(func)

    def test_adapt_cdn_detect(self, plugin_adapter):
        """
        测试适配CDN检测插件
        """
        func = plugin_adapter.adapt_cdn_detect()
        assert func is not None
        assert callable(func)

    def test_adapt_cms_identify(self, plugin_adapter):
        """
        测试适配CMS识别插件
        """
        func = plugin_adapter.adapt_cms_identify()
        assert func is not None
        assert callable(func)

    def test_adapt_infoleak_scan(self, plugin_adapter):
        """
        测试适配信息泄露扫描插件
        """
        func = plugin_adapter.adapt_infoleak_scan()
        assert func is not None
        assert callable(func)

    def test_adapt_subdomain_scan(self, plugin_adapter):
        """
        测试适配子域名扫描插件
        """
        func = plugin_adapter.adapt_subdomain_scan()
        assert func is not None
        assert callable(func)

    def test_adapt_webside_scan(self, plugin_adapter):
        """
        测试适配站点信息扫描插件
        """
        func = plugin_adapter.adapt_webside_scan()
        assert func is not None
        assert callable(func)

    def test_adapt_webweight_scan(self, plugin_adapter):
        """
        测试适配网站权重扫描插件
        """
        func = plugin_adapter.adapt_webweight_scan()
        assert func is not None
        assert callable(func)

    def test_adapt_iplocating(self, plugin_adapter):
        """
        测试适配IP定位插件
        """
        func = plugin_adapter.adapt_iplocating()
        assert func is not None
        assert callable(func)

    @pytest.mark.asyncio
    async def test_cdn_wrapper_success(self):
        """
        测试CDN检测包装器（成功情况）
        """
        func = PluginAdapter.adapt_cdn_detect()
        
        mock_iscdn = Mock(return_value='Cloudflare')
        
        import plugins.cdnexist.cdnexist as cdn_module
        original_iscdn = cdn_module.iscdn
        cdn_module.iscdn = mock_iscdn
        
        try:
            result = await func('example.com')
            
            assert result['status'] == 'success'
            assert result['has_cdn'] is True
            assert result['cdn_info'] == 'Cloudflare'
        finally:
            cdn_module.iscdn = original_iscdn

    @pytest.mark.asyncio
    async def test_cdn_wrapper_no_cdn(self):
        """
        测试CDN检测包装器（无CDN）
        """
        func = PluginAdapter.adapt_cdn_detect()
        
        mock_iscdn = Mock(return_value=None)
        
        import plugins.cdnexist.cdnexist as cdn_module
        original_iscdn = cdn_module.iscdn
        cdn_module.iscdn = mock_iscdn
        
        try:
            result = await func('example.com')
            
            assert result['status'] == 'success'
            assert result['has_cdn'] is False
            assert result['cdn_info'] is None
        finally:
            cdn_module.iscdn = original_iscdn


class TestPOCAdapter:
    """
    测试POC适配器类
    """

    @pytest.fixture
    def poc_adapter(self):
        """
        创建POC适配器实例
        """
        return POCAdapter()

    def test_adapt_poc(self, poc_adapter):
        """
        测试适配单个POC
        """
        mock_poc_module = Mock()
        mock_poc_module.poc = Mock(return_value=(False, 'Not vulnerable'))
        
        func = poc_adapter.adapt_poc('test_poc', mock_poc_module)
        
        assert func is not None
        assert callable(func)

    def test_get_all_pocs(self, poc_adapter):
        """
        测试获取所有POC模块
        """
        pocs = poc_adapter.get_all_pocs()
        
        assert isinstance(pocs, dict)
        assert len(pocs) > 0
        
        expected_pocs = [
            'poc_weblogic_2020_2551',
            'poc_weblogic_2018_2628',
            'poc_struts2_009',
            'poc_tomcat_2017_12615'
        ]
        
        for poc_name in expected_pocs:
            assert poc_name in pocs

    def test_get_poc_by_cms_weblogic(self, poc_adapter):
        """
        测试根据CMS获取WebLogic相关POC
        """
        pocs = poc_adapter.get_poc_by_cms('WebLogic')
        
        assert isinstance(pocs, list)
        assert len(pocs) > 0
        assert any('weblogic' in poc.lower() for poc in pocs)

    def test_get_poc_by_cms_struts2(self, poc_adapter):
        """
        测试根据CMS获取Struts2相关POC
        """
        pocs = poc_adapter.get_poc_by_cms('Struts2')
        
        assert isinstance(pocs, list)
        assert len(pocs) > 0
        assert any('struts2' in poc.lower() for poc in pocs)

    def test_get_poc_by_cms_tomcat(self, poc_adapter):
        """
        测试根据CMS获取Tomcat相关POC
        """
        pocs = poc_adapter.get_poc_by_cms('Tomcat')
        
        assert isinstance(pocs, list)
        assert len(pocs) > 0
        assert any('tomcat' in poc.lower() for poc in pocs)

    def test_get_poc_by_cms_jboss(self, poc_adapter):
        """
        测试根据CMS获取JBoss相关POC
        """
        pocs = poc_adapter.get_poc_by_cms('JBoss')
        
        assert isinstance(pocs, list)
        assert len(pocs) > 0
        assert any('jboss' in poc.lower() for poc in pocs)

    def test_get_poc_by_cms_unknown(self, poc_adapter):
        """
        测试根据CMS获取未知CMS的POC
        """
        pocs = poc_adapter.get_poc_by_cms('UnknownCMS')
        
        assert isinstance(pocs, list)
        assert len(pocs) == 0

    def test_get_poc_by_port_7001(self, poc_adapter):
        """
        测试根据端口7001获取POC
        """
        pocs = poc_adapter.get_poc_by_port(7001)
        
        assert isinstance(pocs, list)
        assert len(pocs) > 0
        assert any('weblogic' in poc.lower() for poc in pocs)

    def test_get_poc_by_port_8080(self, poc_adapter):
        """
        测试根据端口8080获取POC
        """
        pocs = poc_adapter.get_poc_by_port(8080)
        
        assert isinstance(pocs, list)
        assert len(pocs) > 0
        assert any('tomcat' in poc.lower() for poc in pocs)

    def test_get_poc_by_port_unknown(self, poc_adapter):
        """
        测试根据未知端口获取POC
        """
        pocs = poc_adapter.get_poc_by_port(9999)
        
        assert isinstance(pocs, list)
        assert len(pocs) == 0

    def test_get_poc_by_cms_case_insensitive(self, poc_adapter):
        """
        测试根据CMS获取POC（不区分大小写）
        """
        pocs1 = poc_adapter.get_poc_by_cms('weblogic')
        pocs2 = poc_adapter.get_poc_by_cms('WEBLOGIC')
        pocs3 = poc_adapter.get_poc_by_cms('WebLogic')
        
        assert pocs1 == pocs2 == pocs3

    @pytest.mark.asyncio
    async def test_poc_wrapper_vulnerable(self, poc_adapter):
        """
        测试POC包装器（存在漏洞）
        """
        mock_poc_module = Mock()
        mock_poc_module.poc = Mock(return_value=(True, 'Vulnerable!'))
        
        func = poc_adapter.adapt_poc('test_poc', mock_poc_module)
        
        result = await func('example.com')
        
        assert result['status'] == 'success'
        assert result['vulnerable'] is True
        assert result['message'] == 'Vulnerable!'
        assert result['poc_name'] == 'test_poc'

    @pytest.mark.asyncio
    async def test_poc_wrapper_not_vulnerable(self, poc_adapter):
        """
        测试POC包装器（不存在漏洞）
        """
        mock_poc_module = Mock()
        mock_poc_module.poc = Mock(return_value=(False, 'Not vulnerable'))
        
        func = poc_adapter.adapt_poc('test_poc', mock_poc_module)
        
        result = await func('example.com')
        
        assert result['status'] == 'success'
        assert result['vulnerable'] is False
        assert result['message'] == 'Not vulnerable'
        assert result['poc_name'] == 'test_poc'

    @pytest.mark.asyncio
    async def test_poc_wrapper_exception(self, poc_adapter):
        """
        测试POC包装器（异常情况）
        """
        mock_poc_module = Mock()
        mock_poc_module.poc = Mock(side_effect=Exception('Test error'))
        
        func = poc_adapter.adapt_poc('test_poc', mock_poc_module)
        
        result = await func('example.com')
        
        assert result['status'] == 'failed'
        assert result['vulnerable'] is False
        assert 'error' in result
        assert result['poc_name'] == 'test_poc'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

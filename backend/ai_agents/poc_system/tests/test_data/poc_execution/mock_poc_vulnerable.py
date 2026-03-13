"""
模拟POC脚本 - 漏洞检测POC

这是一个模拟存在漏洞的测试POC，用于测试漏洞检测逻辑
"""
from pocsuite3.api import Output, POCBase, register_poc, requests, VUL_TYPE
from pocsuite3.api import POC_CATEGORY


class TestPOC_Vulnerable(POCBase):
    vulID = 'test-002'
    version = '1.0'
    author = ['test']
    vulDate = '2024-01-01'
    createDate = '2024-01-01'
    updateDate = '2024-01-01'
    references = ['https://example.com/vuln']
    name = 'Test POC - Vulnerable Detection'
    appPowerLink = 'https://example.com'
    appName = 'Vulnerable Application'
    appVersion = '1.0'
    vulType = VUL_TYPE.CODE_EXECUTION
    desc = '''
    这是一个模拟漏洞检测的测试POC。
    它会模拟检测到一个代码执行漏洞。
    '''
    samples = ['http://vulnerable.example.com']
    category = POC_CATEGORY.EXPLOITS.REMOTE

    def _verify(self):
        result = {}
        
        try:
            url = self.url.rstrip('/')
            test_url = f"{url}/api/test?cmd=id"
            
            response = requests.get(test_url, timeout=5, verify=False)
            
            if 'uid=' in response.text or 'vulnerable' in response.text.lower():
                result['VerifyInfo'] = {}
                result['VerifyInfo']['URL'] = url
                result['VerifyInfo']['Vulnerability'] = 'Remote Code Execution'
                result['VerifyInfo']['Severity'] = 'Critical'
                result['VerifyInfo']['Evidence'] = 'Command execution detected'
                return self.parse_output(result)
        except Exception as e:
            pass
        
        return self.parse_output(result)

    def _attack(self):
        return self._verify()

    def parse_output(self, result):
        output = Output(self)
        if result:
            output.success(result)
        else:
            output.fail('Target is not vulnerable')
        return output


register_poc(TestPOC_Vulnerable)

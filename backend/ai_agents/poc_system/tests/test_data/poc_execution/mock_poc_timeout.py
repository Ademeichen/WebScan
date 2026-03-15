"""
模拟POC脚本 - 超时测试POC

这是一个会故意超时的测试POC，用于测试超时处理机制
"""
from pocsuite3.api import Output, POCBase, register_poc, requests, VUL_TYPE
from pocsuite3.api import POC_CATEGORY
import time


class TestPOC_Timeout(POCBase):
    vulID = 'test-003'
    version = '1.0'
    author = ['test']
    vulDate = '2024-01-01'
    createDate = '2024-01-01'
    updateDate = '2024-01-01'
    references = ['https://example.com/timeout']
    name = 'Test POC - Timeout Test'
    appPowerLink = 'https://example.com'
    appName = 'Timeout Test Application'
    appVersion = '1.0'
    vulType = VUL_TYPE.OTHER
    desc = '''
    这是一个会故意超时的测试POC，用于测试超时处理机制。
    '''
    samples = ['http://timeout.example.com']
    category = POC_CATEGORY.EXPLOITS.REMOTE

    def _verify(self):
        result = {}
        
        time.sleep(120)
        
        result['VerifyInfo'] = {}
        result['VerifyInfo']['URL'] = self.url
        result['VerifyInfo']['Status'] = 'Should not reach here'
        
        return self.parse_output(result)

    def _attack(self):
        return self._verify()

    def parse_output(self, result):
        output = Output(self)
        if result:
            output.success(result)
        else:
            output.fail('Timeout test failed')
        return output


register_poc(TestPOC_Timeout)

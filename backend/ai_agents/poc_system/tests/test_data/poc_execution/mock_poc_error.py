"""
模拟POC脚本 - 异常测试POC

这是一个会抛出异常的测试POC，用于测试异常处理机制
"""
from pocsuite3.api import Output, POCBase, register_poc, VUL_TYPE
from pocsuite3.api import POC_CATEGORY


class TestPOC_Error(POCBase):
    vulID = 'test-004'
    version = '1.0'
    author = ['test']
    vulDate = '2024-01-01'
    createDate = '2024-01-01'
    updateDate = '2024-01-01'
    references = ['https://example.com/error']
    name = 'Test POC - Error Test'
    appPowerLink = 'https://example.com'
    appName = 'Error Test Application'
    appVersion = '1.0'
    vulType = VUL_TYPE.OTHER
    desc = '''
    这是一个会抛出异常的测试POC，用于测试异常处理机制。
    '''
    samples = ['http://error.example.com']
    category = POC_CATEGORY.EXPLOITS.REMOTE

    def _verify(self):
        raise RuntimeError("Simulated POC execution error for testing")

    def _attack(self):
        return self._verify()

    def parse_output(self, result):
        output = Output(self)
        if result:
            output.success(result)
        else:
            output.fail('Error test')
        return output


register_poc(TestPOC_Error)

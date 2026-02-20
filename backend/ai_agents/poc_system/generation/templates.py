"""
POC Templates for Dynamic Generation
"""
from string import Template

BASE_POC_TEMPLATE = Template("""
import requests
from pocsuite3.api import Output, POCBase, register_poc, requests, logger
from pocsuite3.lib.core.common import index_of_keyword

class TestPOC(POCBase):
    vulID = '99999'  # Dynamic ID
    version = '1.0'
    author = 'DynamicGenerator'
    vulDate = '2025-01-01'
    createDate = '2025-01-01'
    updateDate = '2025-01-01'
    references = []
    name = '$poc_name'
    appPowerLink = ''
    appName = '$app_name'
    appVersion = '$app_version'
    vulType = '$vuln_type'
    desc = '''
    $description
    '''
    samples = []
    install_requires = ['']

    def _verify(self):
        result = {}
        target_url = self.url
        
        try:
            $verify_logic
        except Exception as e:
            logger.error(str(e))
            
        return self.parse_output(result)

    def parse_output(self, result):
        output = Output(self)
        if result:
            output.success(result)
        else:
            output.fail('Target is not vulnerable')
        return output

register_poc(TestPOC)
""")

LOGIC_GET_KEYWORD = """
            # GET Request Verification
            path = '{path}'
            url = target_url + path
            resp = requests.get(url, timeout=10, verify=False)
            
            if resp.status_code == {status_code} and '{keyword}' in resp.text:
                result['VerifyInfo'] = {{}}
                result['VerifyInfo']['URL'] = url
                result['VerifyInfo']['Payload'] = path
"""

LOGIC_POST_KEYWORD = """
            # POST Request Verification
            path = '{path}'
            url = target_url + path
            data = '{data}'
            headers = {headers}
            
            resp = requests.post(url, data=data, headers=headers, timeout=10, verify=False)
            
            if resp.status_code == {status_code} and '{keyword}' in resp.text:
                result['VerifyInfo'] = {{}}
                result['VerifyInfo']['URL'] = url
                result['VerifyInfo']['Payload'] = data
"""

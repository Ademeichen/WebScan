#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import logging
import requests.packages.urllib3

class Base(object):
    def __init__(self, api_base_url, api_key):
        self.api_base_url = api_base_url
        self._api_key = api_key

        api_base_url = api_base_url.strip('/')
        self.targets_api = f'{api_base_url}/api/v1/targets'
        self.scan_api = f'{api_base_url}/api/v1/scans'
        self.vuln_api = f'{api_base_url}/api/v1/vulnerabilities'
        self.report_api = f'{api_base_url}/api/v1/reports'
        self.create_group_api = f'{api_base_url}/api/v1/target_groups'

        self.report_template_dict = {
            'affected_items': '11111111-1111-1111-1111-111111111115',
            'cwe_2011': '11111111-1111-1111-1111-111111111116',
            'developer': '11111111-1111-1111-1111-111111111111',
            'executive_summary': '11111111-1111-1111-1111-111111111113',
            'hipaa': '11111111-1111-1111-1111-111111111114',
            'iso_27001': '11111111-1111-1111-1111-111111111117',
            'nist_SP800_53': '11111111-1111-1111-1111-111111111118',
            'owasp_top_10_2013': '11111111-1111-1111-1111-111111111119',
            'pci_dss_3.2': '11111111-1111-1111-1111-111111111120',
            'quick': '11111111-1111-1111-1111-111111111112',
            'sarbanes_oxley': '11111111-1111-1111-1111-111111111121',
            'scan_comparison': '11111111-1111-1111-1111-111111111124',
            'stig_disa': '11111111-1111-1111-1111-111111111122',
            'wasc_threat_classification': '11111111-1111-1111-1111-111111111123'
        }

        # 禁用https证书相关警告
        requests.packages.urllib3.disable_warnings()

    def check_connection(self):
        """
        检查API连接是否正常
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            # 尝试访问 info 或 me 接口，这里使用 targets 接口作为简单测试
            # AWVS通常没有专门的 ping 接口，但可以用 targets 列表 (limit=1) 测试权限
            response = requests.get(
                self.targets_api,
                headers=self.auth_headers,
                params={'l': 1},
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Connection successful"
            elif response.status_code == 401:
                return False, "Authentication failed: Invalid API Key"
            else:
                return False, f"Connection failed with status code: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, f"Network error: Unable to connect to {self.api_base_url}"
        except requests.exceptions.Timeout:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @property
    def auth_headers(self):
        auth_headers = {
            'X-Auth': self._api_key,
            'content-type': 'application/json'
        }
        return auth_headers

    @property
    def get_logger(self):
        # 使用FastAPI项目的logger
        return logging.getLogger('awvs')

if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
    from config import settings
    base = Base(settings.AWVS_API_URL, settings.AWVS_API_KEY)
    print(base.check_connection())
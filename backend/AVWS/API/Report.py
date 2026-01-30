#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
AWVS Report API 类

提供与 AWVS 报告 API 交互的功能,包括获取报告列表和生成报告
"""



from .Base import Base
import requests

class Report(Base):

    """
    AWVS 报告 API 类

    用于获取和生成 AWVS 扫描报告
    """

    def __init__(self, api_base_url, api_key):
        """
        初始化 Report API 类

        Args:
            api_base_url: AWVS API 基础 URL
            api_key: AWVS API 密钥
        """


        super().__init__(api_base_url, api_key)
        self.logger = self.get_logger

    def get_all(self):

        """
        获取所有报告

        Returns:
            dict: 包含所有报告信息的字典,失败返回 None
        """


        try:
            response = requests.get(self.report_api, headers=self.auth_headers, verify=False)
            return response.json()
        except Exception:
            self.logger.error('Get All Reports Failed......', exc_info=True)
            return None

    def generate(self, template_id, list_type, id_list):

        """
        生成报告

        Args:
            template_id: 报告模板 ID
            list_type: 列表类型(如 'scans' 或 'targets')
            id_list: ID 列表

        Returns:
            bool: 成功返回 True,失败返回 False
        """


        data = {
            'template_id': self.report_template_dict.get(template_id),
            'source': {
                'list_type': list_type,
                'id_list': id_list
            }
        }
        try:
            response = requests.post(self.report_api, json=data, headers=self.auth_headers, verify=False)
            return True
        except Exception:
            self.logger.error('Generate Report Failed......', exc_info=True)
            return False

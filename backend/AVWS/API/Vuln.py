#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
AWVS Vulnerability API 类

提供与 AWVS 漏洞 API 交互的功能,包括获取漏洞列表、漏洞详情和搜索漏洞
"""



from .Base import Base
import requests


class Vuln(Base):

    """
    AWVS 漏洞 API 类

    用于获取和管理 AWVS 的漏洞信息
    """

    def __init__(self, api_base_url, api_key):
        """
        初始化 Vuln API 类

        Args:
            api_base_url: AWVS API 基础 URL
            api_key: AWVS API 密钥
        """


        super().__init__(api_base_url, api_key)

        self.logger = self.get_logger

    def get_all(self, status):

        """
        获取所有指定状态的漏洞

        Args:
            status: 漏洞状态

        Returns:
            dict: 包含漏洞信息的字典,失败返回 None
        """


        vuln_get_all_api = f'{self.vuln_api}?q=status:{status}'
        try:
            response = requests.get(vuln_get_all_api, headers=self.auth_headers, verify=False)
            return response.json()
        except Exception:
            self.logger.error('Get All Vuln Failed......', exc_info=True)
            return None

    def get(self, vuln_id):

        """
        获取指定漏洞的详细信息

        Args:
            vuln_id: 漏洞 ID

        Returns:
            dict: 包含漏洞详细信息的字典,失败返回 None
        """


        vuln_get_api = f'{self.vuln_api}/{vuln_id}'
        try:
            response = requests.get(vuln_get_api, headers=self.auth_headers, verify=False)
            return response.json()
        except Exception:
            self.logger.error('Get Vuln Failed......', exc_info=True)
            return None

    def search(self, severity, criticality, status, cvss_score=0.0, target_id=None, group_id=None):
        """
        搜索漏洞

        Args:
            severity: 严重程度
            criticality: 关键性
            status: 状态
            cvss_score: CVSS 评分
            target_id: 目标 ID
            group_id: 组 ID

        Returns:
            str: 搜索结果文本,失败返回 None
        """
        vuln_search_api = f'{self.vuln_api}?q=status:{status};target_id:{target_id}'
        print(vuln_search_api)
        try:
            response = requests.get(vuln_search_api, headers=self.auth_headers, verify=False)


            return response.text
        except Exception:
            self.logger.error('Search Vuln Failed......', exc_info=True)
            return None

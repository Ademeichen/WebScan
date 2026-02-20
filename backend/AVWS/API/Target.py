#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
AWVS Target API 类

提供与 AWVS 目标 API 交互的功能,包括添加、删除、搜索目标
"""



import requests
import requests.packages.urllib3
from .Base import Base


class Target(Base):

    """
    AWVS 目标 API 类

    用于管理 AWVS 的扫描目标,包括创建、删除、查询和搜索目标
    """

    def __init__(self, api_base_url, api_key):
        """
        初始化 Target API 类

        Args:
            api_base_url: AWVS API 基础 URL
            api_key: AWVS API 密钥
        """


        super().__init__(api_base_url, api_key)

        self.logger = self.get_logger


    def get_all(self):

        """
        获取所有目标

        Returns:
            list: 包含所有目标信息的列表,失败返回 None
        """


        try:
            response = requests.get(self.targets_api, headers=self.auth_headers, verify=False, timeout=30)
            result = response.json()
            target_list = result.get('targets')
            return target_list
        except Exception:
            self.logger.error('Get Targets Failed......', exc_info=True)
            return None

    def search(self, threat=None, criticality=None, group_id=None, keyword=None):
        """
        搜索目标

        Args:
            threat: 威胁等级
            criticality: 严重程度
            group_id: 组 ID
            keyword: 搜索关键词

        Returns:
            list: 包含匹配目标的列表,失败返回 None
        """
        search_targets_api = f'{self.targets_api}?q=threat:{threat};criticality:{criticality};group_id:{group_id};text_search:{keyword}'
        try:
            response = requests.get(search_targets_api, headers=self.auth_headers, verify=False, timeout=30)
            result = response.json()
            target_list = result.get('targets')
            return target_list
        except Exception:
            self.logger.error('Search Target Failed......', exc_info=True)
            return None

    def add(self, address, description=None):

        """
        添加新的扫描目标

        Args:
            address: 目标地址(URL 或 IP)
            description: 目标描述,默认为 address + ' 站点测试'

        Returns:
            str: 成功返回目标 ID,失败返回 None
        """


        if not description:
            description = f'{address} 站点测试'
        data = {
            'address': address,
            'description': description,
            'criticality': '10'
        }
        try:
            # Add timeout to prevent hanging
            response = requests.post(self.targets_api, headers=self.auth_headers, json=data, verify=False, timeout=30)
            result = response.json()
            target_id = result.get('target_id')
            return target_id

        except Exception as e:
            self.logger.error(f'Add Target Failed: {str(e)}', exc_info=True)
            return None

    def delete(self, target_id):

        """
        删除目标

        Args:
            target_id: 目标 ID

        Returns:
            bool: 成功返回 True,失败返回 False
        """


        delete_targets_api = f'{self.targets_api}/{target_id}'
        try:
            response = requests.delete(delete_targets_api, headers=self.auth_headers, verify=False, timeout=30)
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f'Delete Target Failed......\n{response.text}')
                return False
        except Exception:
            self.logger.error('Delete Target Failed......', exc_info=True)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

<<<<<<< HEAD
"""
AWVS Target API 类

提供与 AWVS 目标 API 交互的功能，包括添加、删除、搜索目标
"""
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15

import requests
import requests.packages.urllib3
from .Base import Base


class Target(Base):
<<<<<<< HEAD
    """
    AWVS 目标 API 类

    用于管理 AWVS 的扫描目标，包括创建、删除、查询和搜索目标
    """

    def __init__(self, api_base_url, api_key):
        """
        初始化 Target API 类

        Args:
            api_base_url: AWVS API 基础 URL
            api_key: AWVS API 密钥
        """
=======
    def __init__(self, api_base_url, api_key):
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
        super().__init__(api_base_url, api_key)

        self.logger = self.get_logger


    def get_all(self):
<<<<<<< HEAD
        """
        获取所有目标

        Returns:
            list: 包含所有目标信息的列表，失败返回 None
        """
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
        try:
            response = requests.get(self.targets_api, headers=self.auth_headers, verify=False)
            result = response.json()
            target_list = result.get('targets')
            return target_list
        except Exception:
            self.logger.error('Get Targets Failed......', exc_info=True)
            return None

<<<<<<< HEAD
    def search(self, threat=None, criticality=None, group_id=None, keyword=None):
        """
        搜索目标

        Args:
            threat: 威胁等级，高->低: [3,2,1,0]
            criticality: 危险程度，高->低: [30,20,10,0]
            group_id: 分组 ID
            keyword: 筛选内容，支持通配符，如 *baidu.com

        Returns:
            list: 包含匹配目标的列表，失败返回 None
=======
    # https://10.0.0.22:3443/api/v1/targets?q=threat:2;text_search:*pc

    def search(self, threat=None, criticality=None, group_id=None, keyword=None):
        """
        搜索任务
        :param threat: 威胁等级;高->低:[3,2,1,0]
        :param criticality: 危险程度;高->低:[30,20,10,0]
        :param group_id: 分组id
        :param keyword: 筛选内容，支持通配符，*baidu.com
        :return:
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
        """
        search_targets_api = f'{self.targets_api}?q=threat:{threat};criticality:{criticality};group_id:{group_id};text_search:{keyword}'
        try:
            response = requests.get(search_targets_api, headers=self.auth_headers, verify=False)
            result = response.json()
            target_list = result.get('targets')
            return target_list
        except Exception:
            self.logger.error('Search Target Failed......', exc_info=True)
            return None

    def add(self, address, description=None):
<<<<<<< HEAD
        """
        添加新的扫描目标

        Args:
            address: 目标地址（URL 或 IP）
            description: 目标描述，默认为 address + ' 站点测试'

        Returns:
            str: 成功返回目标 ID，失败返回 None
        """
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
        if not description:
            description = f'{address} 站点测试'
        data = {
            'address': address,
            'description': description,
        }
        try:
            response = requests.post(self.targets_api, headers=self.auth_headers, json=data, verify=False)
            result = response.json()
            target_id = result.get('target_id')
            return target_id

        except Exception:
            self.logger.error('Add Target Failed......', exc_info=True)
            return None

    def delete(self, target_id):
<<<<<<< HEAD
        """
        删除目标

        Args:
            target_id: 目标 ID

        Returns:
            bool: 成功返回 True，失败返回 False
        """
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
        delete_targets_api = f'{self.targets_api}/{target_id}'
        try:
            response = requests.delete(delete_targets_api, headers=self.auth_headers, verify=False)
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f'Delete Target Failed......\n{response.text}')
                return False
        except Exception:
            self.logger.error('Delete Target Failed......', exc_info=True)

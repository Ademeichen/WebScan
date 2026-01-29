#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AWVS Group API 类

提供与 AWVS 目标分组 API 交互的功能，包括创建分组、获取分组、添加/删除目标到分组等
"""

from .Base import Base
import requests

class Group(Base):
    """
    AWVS 目标分组 API 类

    用于管理 AWVS 的目标分组，包括创建、查询、添加和删除目标
    """

    def __init__(self, api_base_url, api_key):
        """
        初始化 Group API 类

        Args:
            api_base_url: AWVS API 基础 URL
            api_key: AWVS API 密钥
        """
        super().__init__(api_base_url, api_key)
        self.logger = self.get_logger

    def create_new_group(self, group_name, description = None):
        """
        创建新的目标分组

        Args:
            group_name: 分组名称
            description: 分组描述，默认为 group_name + ' group'

        Returns:
            str: 成功返回分组 ID，失败返回 False
        """
        if not description:
            description = f'{group_name} group'
        
        data = {'name': group_name, 'description':description}
        response = requests.post(self.create_group_api, json=data, headers=self.auth_headers, verify=False)
        if response.status_code != 201:
            self.logger.error("创建分组失败~！", exc_info=True)
            return False
        else: 
            group_id = response.headers['Location'].split('/')[-1]
            group_id = '{0}-{1}-{2}-{3}-{4}'.format(group_id[0:8], group_id[8:12], group_id[12:16], group_id[16:20], group_id[20:len(group_id)])
            return group_id
    
    def get_existed_groups(self):
        """
        获取所有已存在的分组

        Returns:
            dict: 分组名称到分组 ID 的映射字典
        """
        groups = {}
        response = requests.get(self.create_group_api, headers=self.auth_headers, verify=False)
        print(response.status_code)
        if response.status_code != 200:
            self.logger.error("查询已存在组失败~", exc_info=True)
        else:
            response_j = response.json()
            groups_list = response_j.get('groups')
            for group in groups_list:
                groups[group.get('name')] = group.get('group_id')
        return groups


    def add_to_group(self, target_id, group_id):
        """
        将目标添加到分组

        Args:
            target_id: 目标 ID
            group_id: 分组 ID

        Returns:
            bool: 成功返回 True，失败返回 False
        """
        add_to_group_api = self.create_group_api + '/{0}/targets'.format(group_id)
        data = {'add':[target_id],'remove':[]}
        response = requests.patch(add_to_group_api, json=data, headers=self.auth_headers, verify=False)
        if response.status_code != 206:
            self.logger.error("添加失败~！", exc_info=True)
            return False
        else:
            print(response.headers)
            return True
    
    def remove_from_group(self, target_id, group_id):
        """
        从分组中移除目标

        Args:
            target_id: 目标 ID
            group_id: 分组 ID

        Returns:
            bool: 成功返回 True，失败返回 False
        """
        add_to_group_api = self.create_group_api + '/{0}/targets'.format(group_id)
        print(add_to_group_api)
        data = {'add':[],'remove':[target_id]}
        print(data)
        response = requests.patch(add_to_group_api, json=data, headers=self.auth_headers, verify=False)
        if response.status_code != 206:
            self.logger.error("删除失败~！", exc_info=True)
            return False
        else:
            print(response.headers)
            return True

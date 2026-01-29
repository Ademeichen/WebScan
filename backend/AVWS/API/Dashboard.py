#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AWVS Dashboard API 类

提供与 AWVS Dashboard API 交互的功能，获取统计信息
"""

from .Base import Base as AWVSBase
import requests


class Dashboard(AWVSBase):
    """
    AWVS Dashboard API 类

    用于获取 AWVS 的统计信息和仪表板数据
    """

    def __init__(self, api_base_url, api_key):
        """
        初始化 Dashboard API 类

        Args:
            api_base_url: AWVS API 基础 URL
            api_key: AWVS API 密钥
        """
        super().__init__(api_base_url, api_key)

        self.logger = self.get_logger

    def stats(self):
        """
        获取仪表板统计信息

        Returns:
            str: 统计信息的 JSON 字符串
        """
        dashboard_stats_api = f'{self.api_base_url}/api/v1/me/stats'
        print(dashboard_stats_api)
        try:
            response = requests.get(dashboard_stats_api, headers=self.auth_headers, verify=False)
            return response.text
        except Exception:
            self.logger.error('Get Dashboard Stats Failed......', exc_info=True)

if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
    from config import settings
    dashboard = Dashboard(settings.AWVS_API_URL, settings.AWVS_API_KEY)
    print(dashboard.stats())

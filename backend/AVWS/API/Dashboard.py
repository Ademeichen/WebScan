#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .Base import Base as AWVSBase
import requests


class Dashboard(AWVSBase):
    def __init__(self, api_base_url, api_key):
        super().__init__(api_base_url, api_key)

        self.logger = self.get_logger

    def stats(self):
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

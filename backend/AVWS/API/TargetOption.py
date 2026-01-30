#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
AWVS Target Option API 类

提供与 AWVS 目标配置 API 交互的功能,包括设置危险程度、扫描速度、登录信息、代理等
"""



from .Base import Base
import requests
import json


class TargetOption(Base):

    """
    AWVS 目标配置 API 类

    用于配置 AWVS 扫描目标的各种选项,包括危险程度、扫描速度、登录信息、代理等
    """

    def __init__(self, api_base_url, api_key):
        """
        初始化 TargetOption API 类

        Args:
            api_base_url: AWVS API 基础 URL
            api_key: AWVS API 密钥
        """


        super().__init__(api_base_url, api_key)

        self.excluded_hours_dict = {
            'default': '',
            '9am_to_5pm': 'cb869c0f-756e-439f-8895-d2502626a002',
            'except_working_hour': '851d89b6-32f5-4094-94c0-20abf77f7a6a',
            'no_weekends': '6275cc9e-d146-4268-b4b4-4ff747868ecc'
        }

        self.logger = self.get_logger

    def set_criticality(self, target_id, criticality, description=None):


        Args:
            target_id: 目标 ID
            criticality: 危险程度,30->critical, 20->high, 10-normal, 0->low
            description: 目标描述(可选)

        Returns:


        """
        set_criticality_api = f'{self.targets_api}/{target_id}'
        try:
            data = dict()
            if description:
                data['description'] = description
            data['criticality'] = criticality
            response = requests.patch(set_criticality_api, json=data, headers=self.auth_headers, verify=False)
            if not response.text:
                return True
            else:
                self.logger.error(f'Set General Criticality Failed......\n{response.text}')
                return False
        except Exception:
            self.logger.error('Set General Criticality Failed......', exc_info=True)
            return False

    def set_scan_speed(self, target_id, scan_speed):


        Args:
            target_id: 目标 ID
            scan_speed: 扫描速度,可选值为 sequential/slow/moderate/fast

        Returns:


        """
        set_scan_speed_api = f'{self.targets_api}/{target_id}/configuration'
        try:
            data = {'scan_speed': scan_speed}
            response = requests.patch(set_scan_speed_api, json=data, headers=self.auth_headers, verify=False)
            if not response.text:
                return True
            else:
                self.logger.error(f'Set Scan Speed Failed......\n{response.text}')
                return False
        except Exception:
            self.logger.error('Set Scan Speed Failed......', exc_info=True)
            return False

    def set_continuous_scan(self, target_id, enabled=False):


        Args:
            target_id: 目标 ID
            enabled: 启用 True,关闭 False

        Returns:


        """
        set_continuous_scan_api = f'{self.targets_api}/{target_id}/continuous_scan'
        try:
            data = {'enabled': enabled}
            response = requests.post(set_continuous_scan_api, json=data, headers=self.auth_headers, verify=False)
            response_data = response.json()
            if 'enabled' in response_data:
                return True
            else:
                self.logger.error(f'Set Continuous Scan Failed......\n{response.text}')
                return False
        except Exception:
            self.logger.error('Set Continuous Scan Failed......', exc_info=True)
            return False

    def set_site_login(self, target_id, login_kind, login_info):


        Args:
            target_id: 目标 ID
            login_kind: 登录类型,none(无登录)、automatic(用户名和密码登录)
            login_info: 登录信息字典,格式: {'username': 'tudouya', 'password': 'password123'}

        Returns:


        """
        set_site_login_api = f'{self.targets_api}/{target_id}/configuration'
        try:
            data = {
                'login': {
                    'kind': login_kind,
                }
            }
            if login_kind == 'automatic':
                data['login']['credentials'] = {
                    'enabled': True,
                    'username': login_info.get('username'),
                    'password': login_info.get('password')
                }

            response = requests.patch(set_site_login_api, json=data, headers=self.auth_headers, verify=False)
            if not response.text:
                return True
            else:
                self.logger.error(f'Set Scan Speed Failed......\n{response.text}')
                return False
        except Exception:
            self.logger.error('Set Site Login Failed......', exc_info=True)
            return False

    def set_crawler(self, target_id, user_agent, case_sensitive, excluded_paths, limit_crawler_scope):


        Args:
            target_id: 目标 ID
            limit_crawler_scope: 是否仅限爬行到地址和子目录
            case_sensitive: 大小写敏感,auto/no/yes
            excluded_paths: 排除路径列表
            user_agent: User-Agent 头

        Returns:


        """
        set_crawler_api = f'{self.targets_api}/{target_id}/configuration'
        data = {
            'limit_crawler_scope': limit_crawler_scope,
            'case_sensitive': case_sensitive,
            'excluded_paths': excluded_paths,
            'user_agent': user_agent
        }
        try:
            response = requests.patch(set_crawler_api, data=json.dumps(
                data), headers=self.auth_headers, verify=False)
            if not response.text:
                return True
            else:
                self.logger.error(f'Set Crawler Failed......\n{response.text}')
                return False
        except Exception:
            self.logger.error('Set Crawler Failed......', exc_info=True)

    def set_http_auth(self, target_id, enabled, username=None, password=None):


        Args:
            target_id: 目标 ID
            enabled: 启用 True,关闭 False
            username: 用户名(可选)
            password: 密码(可选)

        Returns:


        """
        set_http_auth_api = f'{self.targets_api}/{target_id}/configuration'
        data = {
            'authentication': {
                'enabled': enabled
            }
        }
        if enabled:
            data['authentication']['username'] = username
            data['authentication']['password'] = password
        try:
            response = requests.patch(set_http_auth_api, json=data, headers=self.auth_headers, verify=False)
            if not response.text:
                return True
            else:
                self.logger.error(f'Set HTTP Auth Failed......\n{response.text}')
                return False
        except Exception:
            self.logger.error('Set HTTP Auth Failed......', exc_info=True)
            return False

    def set_http_cert(self, target_id):

        """
        设置 HTTP 证书(未实现)

        Args:
            target_id: 目标 ID
        """


        set_http_cert_api = f'{self.targets_api}/{target_id}/client_certificate'
        pass

    def upload_http_cert(self, upload_url):

        """
        上传 HTTP 证书(未实现)

        Args:
            upload_url: 上传 URL
        """

        pass

    def set_http_cert_password(self, target_id, client_certificate_password):
        """
        设置客户端证书密码

        Args:
            target_id: 目标 ID
            client_certificate_password: 密码

        Returns:


        """
        set_http_cert_password_api = f'{self.targets_api}/{target_id}/configuration'
        data = {
            'client_certificate_password': client_certificate_password
        }
        try:
            response = requests.patch(set_http_cert_password_api, json=data, headers=self.auth_headers, verify=False)
            if not response.text:
                return True
            else:
                self.logger.error(f'Set HTTP Cert Password Failed......\n{response.text}')
                return False
        except Exception:
            self.logger.error(
                'Set HTTP Cert Password Failed......', exc_info=True)
            return False

    def set_proxy(self, target_id, enabled, proxy_info=None):


        Args:
            target_id: 目标 ID
            enabled: 启用 True,关闭 False
            proxy_info: 代理信息字典,格式: {'address': '', 'protocol': '', 'port': '', 'username': '', 'password': ''}

        Returns:


        """
        set_proxy_api = f'{self.targets_api}/{target_id}/configuration'
        data = {
            'proxy': {
                'enabled': enabled
            }
        }
        if enabled:
            data['proxy']['address'] = proxy_info['address']
            data['proxy']['protocol'] = proxy_info['protocol']
            data['proxy']['port'] = proxy_info['port']
            data['proxy']['username'] = proxy_info['username']
            data['proxy']['password'] = proxy_info['password']
        try:
            response = requests.patch(set_proxy_api, json=data, headers=self
                                      .auth_headers, verify=False)
            if not response.text:
                return True
            else:
                self.logger.error(f'Set Proxy Failed......\n{response.text}')
                return False
        except Exception:
            self.logger.error('Set Proxy Failed......', exc_info=True)

    def set_advance(self, target_id, technologies, custom_headers, custom_cookies, excluded_hours_id, debug=False, issue_tracker_id=''):


        Args:
            target_id: 目标 ID
            issue_tracker_id: 问题跟踪器 ID
            technologies: 目标相关技术列表
            custom_headers: 自定义 HTTP 头列表
            custom_cookies: 自定义 Cookie 列表
            debug: 启用 True,关闭 False
            excluded_hours_id: 非扫描时段 ID,如果为空则使用默认值

        Returns:


        """
        set_advance_api = f'{self.targets_api}/{target_id}/configuration'
        data = {
            'issue_tracker_id': issue_tracker_id,
            'technologies': technologies,
            'custom_headers': custom_headers,
            'custom_cookies': custom_cookies,
            'debug': debug,
            'excluded_hours_id': self.excluded_hours_dict.get(excluded_hours_id)
        }
        try:
            response = requests.patch(set_advance_api, json=data, headers=self.auth_headers, verify=False)
            if not response.text:
                return True
            else:
                self.logger.error(f'Set Proxy Failed......\n{response.text}')
                return False
        except Exception:
            self.logger.error('Set Proxy Failed......', exc_info=True)

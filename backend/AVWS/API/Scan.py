#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
AWVS Scan API 类

提供与 AWVS 扫描 API 交互的功能,包括添加、删除、获取扫描任务和漏洞信息
"""



import requests

from .Base import Base


class Scan(Base):

    """
    AWVS 扫描 API 类

    用于管理 AWVS 的扫描任务,包括创建、删除、查询扫描和获取漏洞信息
    """

    def __init__(self, api_base_url, api_key):
        """
        初始化 Scan API 类

        Args:
            api_base_url: AWVS API 基础 URL
            api_key: AWVS API 密钥
        """


        super().__init__(api_base_url, api_key)

        self.profile_dict = {
            'full_scan': '11111111-1111-1111-1111-111111111111',
            'high_risk_vuln': '11111111-1111-1111-1111-111111111112',
            'xss_vuln': '11111111-1111-1111-1111-111111111116',
            'sqli_vuln': '11111111-1111-1111-1111-111111111113',
            'weak_passwords': '11111111-1111-1111-1111-111111111115',
            'crawl_only': '11111111-1111-1111-1111-111111111117'
        }

        self.logger = self.get_logger

    def add(self, target_id, profile_key, report_template_id='', schedule=None, ui_session_id=''):
        """
        添加扫描任务

        Args:
            target_id: 目标 ID
            profile_key: 扫描类型(full_scan, high_risk_vuln, xss_vuln, sqli_vuln, weak_passwords, crawl_only)
            report_template_id: 扫描报告模板 ID(可选)
            schedule: 扫描时间,默认为即时扫描(可选)
            ui_session_id: UI 会话 ID(可选)
        """
        data = {
            'target_id': target_id,
            'profile_id': self.profile_dict.get(profile_key),
        }

        if report_template_id:
            data['report_template_id'] = self.report_template_dict.get(report_template_id)

        if not schedule:
            schedule = {
                'disable': False,
                'start_date': None,
                'time_sensitive': False
            }
        data['schedule'] = schedule
        try:
            response = requests.post(self.scan_api, json=data, headers=self.auth_headers, verify=False)


            status_code = 200
        except Exception:
            self.logger.error('Add Scan Failed......', exc_info=True)
            status_code = 404
        return status_code

    def delete(self, scan_id):

        """
        删除扫描任务

        Args:
            scan_id: 扫描 ID
        """


        scan_delete_api = f'{self.scan_api}/{scan_id}'
        try:
            response = requests.delete(scan_delete_api, headers=self.auth_headers, verify=False)
        except Exception:
            self.logger.error('Delete Scan Failed......', exc_info=True)

    def get_all(self):

        """
        获取所有扫描任务

        Returns:
            list: 包含所有扫描信息的列表
        """


        try:
            response = requests.get(self.scan_api, headers=self.auth_headers, verify=False)
            request_url = response.url
            scan_response = response.json().get('scans')
            scan_list = []
            for scan in scan_response:
                scan['request_url'] = request_url
                scan_list.append(scan)
        except Exception:
            scan_list = []



        return scan_list

    def get(self, scan_id):

        """
        获取指定扫描任务的信息

        Args:
            scan_id: 扫描 ID

        Returns:
            dict: 包含扫描信息的字典,失败返回 None
        """


        scan_get_api = f'{self.scan_api}/{scan_id}'
        try:
            response = requests.get(scan_get_api, headers=self.auth_headers, verify=False)
            return response.json()
        except Exception:
            self.logger.error('Get Scan Failed......', exc_info=True)
            return None

    def get_vulns(self, scan_id, scan_session_id):

        """
        获取扫描任务的漏洞列表

        Args:
            scan_id: 扫描 ID
            scan_session_id: 扫描会话 ID

        Returns:
            list: 包含漏洞信息的列表,失败返回 None
        """


        scan_result_api = f'{self.scan_api}/{scan_id}/results/{scan_session_id}/vulnerabilities'
        try:
            response = requests.get(scan_result_api, headers=self.auth_headers, verify=False)
            vuln_list = response.json().get('vulnerabilities')
            return vuln_list
        except Exception:
            self.logger.error('Get Scan Result Failed......', exc_info=True)
            vuln_list = []
            return None

    def get_vuln_detail(self, scan_id, scan_session_id, vuln_id):

        """
        获取漏洞的详细信息

        Args:
            scan_id: 扫描 ID
            scan_session_id: 扫描会话 ID
            vuln_id: 漏洞 ID

        Returns:
            dict: 包含漏洞详细信息的字典,失败返回 None
        """


        scan_vuln_detail_api = f'{self.scan_api}/{scan_id}/results/{scan_session_id}/vulnerabilities/{vuln_id}'
        try:
            response = requests.get(scan_vuln_detail_api, headers=self.auth_headers, verify=False)
            vuln_detail = response.json()
            return vuln_detail
        except Exception:
            self.logger.error('Get Scan Result Failed......', exc_info=True)
            return None

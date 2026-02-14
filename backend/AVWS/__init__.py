"""
AWVS API 客户端包

提供与 Acunetix Web Vulnerability Scanner (AWVS) API 交互的客户端类。
"""
from .API.Base import Base
from .API.Scan import Scan
from .API.Target import Target
from .API.Vuln import Vuln
from .API.Dashboard import Dashboard
from .API.Group import Group
from .API.Report import Report
from .API.TargetOption import TargetOption

__all__ = [
    'Base',
    'Scan',
    'Target',
    'Vuln',
    'Dashboard',
    'Group',
    'Report',
    'TargetOption'
]

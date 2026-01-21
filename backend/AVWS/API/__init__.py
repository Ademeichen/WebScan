"""
AWVS API 模块

提供与 AWVS API 交互的核心类。
"""
from .Base import Base
from .Scan import Scan
from .Target import Target
from .Vuln import Vuln
from .Dashboard import Dashboard
from .Group import Group
from .Report import Report
from .TargetOption import TargetOption

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

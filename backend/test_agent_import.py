#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试AI Agent导入"""
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

try:
    from backend.ai_agents.tools.adapters import POCAdapter
    print('POCAdapter导入成功')
    pocs = POCAdapter.get_all_pocs()
    print(f'获取POC成功: {list(pocs.keys())}')
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()

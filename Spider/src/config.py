"""
Spider 模块配置文件

定义爬虫的目标 URL、输出目录、爬虫配置、输出配置和过滤规则
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

TARGET_URL = 'https://localhost:3443/Acunetix-API-Documentation.html'
OUTPUT_DIR = BASE_DIR / 'output'

CRAWLER_CONFIG = {
    'headless': False,
    'timeout': 60000,
    'max_requests': 100,
}

OUTPUT_CONFIG = {
    'json_file': 'acunetix-api.json',
    'summary_file': 'summary.json',
}

FILTERS = {
    'include_patterns': [
        'Acunetix-API-Documentation',
        '/api/v1/',
        '#',
    ],
    'base_url': 'https://localhost:3443',
}

def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR

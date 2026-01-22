"""
Spider 模块入口文件

该模块用于爬取 Acunetix API 文档，提取 API 端点、参数、方法等信息
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from advanced_crawler import main


if __name__ == '__main__':
    print('Acunetix API Crawler')
    print('=' * 50)
    print('\n启动高级爬虫...\n')
    asyncio.run(main())

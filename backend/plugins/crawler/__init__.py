# -*- coding:utf-8 -*-
"""
Web爬虫插件

功能：
1. 自动爬取目标网站
2. 提取链接、表单、参数
3. 构建站点地图
4. 发现隐藏页面和接口
"""

from .crawler import WebCrawler, crawl
from .parser import HTMLParser
from .form_extractor import FormExtractor
from .url_filter import URLFilter
from .config import CRAWLER_CONFIG

__all__ = [
    'WebCrawler',
    'crawl',
    'HTMLParser', 
    'FormExtractor',
    'URLFilter',
    'CRAWLER_CONFIG'
]

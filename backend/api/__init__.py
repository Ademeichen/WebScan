"""
API 路由总入口
"""
from fastapi import APIRouter
from . import scan, tasks, reports, poc, awvs, settings, kb, poc_gen

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(scan.router, prefix="/scan", tags=["扫描功能"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务管理"])
api_router.include_router(reports.router, prefix="/reports", tags=["报告管理"])
api_router.include_router(poc.router, tags=["POC扫描"])
api_router.include_router(awvs.router, prefix="/awvs", tags=["AWVS漏洞扫描"])
api_router.include_router(settings.router, prefix="/settings", tags=["系统设置"])
api_router.include_router(kb.router, prefix="/kb", tags=["漏洞知识库"])
api_router.include_router(poc_gen.router, prefix="/poc-gen", tags=["POC智能生成"])


"""
API 路由总入口

统一管理所有 API 路由，包括扫描、任务、报告、POC、AWVS、AI 对话和 Agent 等模块。
"""
from fastapi import APIRouter
from . import scan, tasks, reports, poc, awvs, settings, ai
from .agent import router as agent_router

api_router = APIRouter()

api_router.include_router(scan.router, prefix="/scan", tags=["扫描功能"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务管理"])
api_router.include_router(reports.router, prefix="/reports", tags=["报告管理"])
api_router.include_router(poc.router, tags=["POC扫描"])
api_router.include_router(awvs.router, prefix="/awvs", tags=["AWVS漏洞扫描"])
api_router.include_router(settings.router, prefix="/settings", tags=["系统设置"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI对话"])
api_router.include_router(agent_router)

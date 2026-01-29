"""
API 路由总入口

统一管理所有 API 路由，包括扫描、任务、报告、POC、AWVS、AI 对话、Agent 和 AI Agents 等模块。
"""
from fastapi import APIRouter
from . import scan, tasks, reports, poc, awvs, settings, ai, kb, poc_gen, user, notifications, poc_verification
from .agent import router as agent_router
from backend.plugins.common.common import router as common_router
from backend.plugins.common.common_proxyfliter import router as common_proxy_router
from backend.ai_agents.api import router as ai_agents_router

api_router = APIRouter()

api_router.include_router(scan.router, prefix="/scan", tags=["扫描功能"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务管理"])
api_router.include_router(reports.router, prefix="/reports", tags=["报告管理"])
api_router.include_router(poc.router, tags=["POC扫描"])
api_router.include_router(awvs.router, prefix="/awvs", tags=["AWVS漏洞扫描"])
api_router.include_router(settings.router, prefix="/settings", tags=["系统设置"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI对话"])
api_router.include_router(agent_router, prefix="/agent", tags=["Agent功能"])
api_router.include_router(kb.router, prefix="/kb", tags=["漏洞知识库"])
api_router.include_router(poc_gen.router, prefix="/poc-gen", tags=["POC智能生成"])
api_router.include_router(user.router, tags=["用户管理"])
api_router.include_router(notifications.router, tags=["通知管理"])
api_router.include_router(common_router, prefix="/common", tags=["通用工具"])
api_router.include_router(common_proxy_router, prefix="/common-proxy", tags=["通用工具-代理过滤"])
api_router.include_router(ai_agents_router, tags=["AI Agents"])
api_router.include_router(poc_verification.router, tags=["POC验证"])


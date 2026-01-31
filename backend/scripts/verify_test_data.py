"""
测试数据验证脚本

验证导入的测试数据的完整性和正确性
"""

import asyncio
import sys
from pathlib import Path
from tortoise import Tortoise

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings
from models import (
    Task, Vulnerability, Report,
    VulnerabilityKB, POCScanResult,
    AgentTask, AgentResult, AIChatInstance
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    """初始化数据库连接"""
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["models"]}
    )
    logger.info("✅ 数据库连接成功")


async def verify_tasks():
    """验证任务数据"""
    logger.info("\n📋 验证任务数据...")
    tasks = await Task.all()
    logger.info(f"  任务总数: {len(tasks)}")
    
    if tasks:
        logger.info(f"  任务类型分布:")
        task_types = {}
        for task in tasks:
            task_types[task.task_type] = task_types.get(task.task_type, 0) + 1
        for task_type, count in task_types.items():
            logger.info(f"    - {task_type}: {count}")
        
        logger.info(f"  任务状态分布:")
        status_counts = {}
        for task in tasks:
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
        for status, count in status_counts.items():
            logger.info(f"    - {status}: {count}")
        
        logger.info(f"  示例任务:")
        for task in tasks[:3]:
            logger.info(f"    - {task.task_name} ({task.task_type}) - {task.status}")


async def verify_vulnerabilities():
    """验证漏洞数据"""
    logger.info("\n🔍 验证漏洞数据...")
    vulnerabilities = await Vulnerability.all()
    logger.info(f"  漏洞总数: {len(vulnerabilities)}")
    
    if vulnerabilities:
        logger.info(f"  漏洞类型分布:")
        vuln_types = {}
        for vuln in vulnerabilities:
            vuln_types[vuln.vuln_type] = vuln_types.get(vuln.vuln_type, 0) + 1
        for vuln_type, count in vuln_types.items():
            logger.info(f"    - {vuln_type}: {count}")
        
        logger.info(f"  严重程度分布:")
        severity_counts = {}
        for vuln in vulnerabilities:
            severity_counts[vuln.severity] = severity_counts.get(vuln.severity, 0) + 1
        for severity, count in severity_counts.items():
            logger.info(f"    - {severity}: {count}")
        
        logger.info(f"  状态分布:")
        status_counts = {}
        for vuln in vulnerabilities:
            status_counts[vuln.status] = status_counts.get(vuln.status, 0) + 1
        for status, count in status_counts.items():
            logger.info(f"    - {status}: {count}")


async def verify_reports():
    """验证报告数据"""
    logger.info("\n📄 验证报告数据...")
    reports = await Report.all()
    logger.info(f"  报告总数: {len(reports)}")
    
    if reports:
        logger.info(f"  报告类型分布:")
        report_types = {}
        for report in reports:
            report_types[report.report_type] = report_types.get(report.report_type, 0) + 1
        for report_type, count in report_types.items():
            logger.info(f"    - {report_type}: {count}")


async def verify_knowledge_base():
    """验证知识库数据"""
    logger.info("\n📚 验证知识库数据...")
    kb_items = await VulnerabilityKB.all()
    logger.info(f"  知识库条目总数: {len(kb_items)}")
    
    if kb_items:
        logger.info(f"  严重程度分布:")
        severity_counts = {}
        for kb in kb_items:
            severity_counts[kb.severity] = severity_counts.get(kb.severity, 0) + 1
        for severity, count in severity_counts.items():
            logger.info(f"    - {severity}: {count}")


async def verify_poc_results():
    """验证POC扫描结果数据"""
    logger.info("\n🎯 验证POC扫描结果数据...")
    poc_results = await POCScanResult.all()
    logger.info(f"  POC扫描结果总数: {len(poc_results)}")
    
    if poc_results:
        logger.info(f"  POC类型分布:")
        poc_types = {}
        for poc in poc_results:
            poc_types[poc.poc_type] = poc_types.get(poc.poc_type, 0) + 1
        for poc_type, count in poc_types.items():
            logger.info(f"    - {poc_type}: {count}")
        
        logger.info(f"  漏洞状态:")
        vulnerable_count = sum(1 for poc in poc_results if poc.vulnerable)
        logger.info(f"    - 存在漏洞: {vulnerable_count}")
        logger.info(f"    - 安全: {len(poc_results) - vulnerable_count}")


async def verify_agent_tasks():
    """验证AI Agent任务数据"""
    logger.info("\n🤖 验证AI Agent任务数据...")
    agent_tasks = await AgentTask.all()
    logger.info(f"  Agent任务总数: {len(agent_tasks)}")
    
    if agent_tasks:
        logger.info(f"  任务类型分布:")
        task_types = {}
        for task in agent_tasks:
            task_types[task.task_type] = task_types.get(task.task_type, 0) + 1
        for task_type, count in task_types.items():
            logger.info(f"    - {task_type}: {count}")
        
        logger.info(f"  任务状态分布:")
        status_counts = {}
        for task in agent_tasks:
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
        for status, count in status_counts.items():
            logger.info(f"    - {status}: {count}")


async def verify_agent_results():
    """验证AI Agent结果数据"""
    logger.info("\n✨ 验证AI Agent结果数据...")
    agent_results = await AgentResult.all()
    logger.info(f"  Agent结果总数: {len(agent_results)}")
    
    if agent_results:
        logger.info(f"  执行时间统计:")
        execution_times = [r.execution_time for r in agent_results if r.execution_time]
        if execution_times:
            logger.info(f"    - 最小: {min(execution_times):.1f}秒")
            logger.info(f"    - 最大: {max(execution_times):.1f}秒")
            logger.info(f"    - 平均: {sum(execution_times)/len(execution_times):.1f}秒")


async def verify_ai_chats():
    """验证AI对话数据"""
    logger.info("\n💬 验证AI对话数据...")
    ai_chats = await AIChatInstance.all()
    logger.info(f"  AI对话总数: {len(ai_chats)}")
    
    if ai_chats:
        logger.info(f"  对话类型分布:")
        chat_types = {}
        for chat in ai_chats:
            chat_types[chat.chat_type] = chat_types.get(chat.chat_type, 0) + 1
        for chat_type, count in chat_types.items():
            logger.info(f"    - {chat_type}: {count}")


async def verify_relationships():
    """验证数据关系"""
    logger.info("\n🔗 验证数据关系...")
    
    tasks = await Task.all()
    if tasks:
        for task in tasks[:3]:
            vuln_count = await Vulnerability.filter(task=task).count()
            report_count = await Report.filter(task=task).count()
            logger.info(f"  任务 {task.task_name}: {vuln_count} 个漏洞, {report_count} 个报告")
    
    agent_tasks = await AgentTask.all()
    if agent_tasks:
        for task in agent_tasks[:3]:
            result_count = await AgentResult.filter(task=task).count()
            logger.info(f"  Agent任务 {task.task_type}: {result_count} 个结果")


async def main():
    """主函数：执行所有验证"""
    logger.info("🚀 开始验证测试数据...")
    
    try:
        await init_db()
        
        await verify_tasks()
        await verify_vulnerabilities()
        await verify_reports()
        await verify_knowledge_base()
        await verify_poc_results()
        await verify_agent_tasks()
        await verify_agent_results()
        await verify_ai_chats()
        await verify_relationships()
        
        logger.info("\n✅ 测试数据验证完成！")
        logger.info("\n📊 数据汇总:")
        logger.info(f"  - 任务: {await Task.all().count()}")
        logger.info(f"  - 漏洞: {await Vulnerability.all().count()}")
        logger.info(f"  - 报告: {await Report.all().count()}")
        logger.info(f"  - 知识库: {await VulnerabilityKB.all().count()}")
        logger.info(f"  - POC扫描结果: {await POCScanResult.all().count()}")
        logger.info(f"  - AI Agent任务: {await AgentTask.all().count()}")
        logger.info(f"  - AI Agent结果: {await AgentResult.all().count()}")
        logger.info(f"  - AI对话: {await AIChatInstance.all().count()}")
        
    except Exception as e:
        logger.error(f"❌ 验证测试数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())

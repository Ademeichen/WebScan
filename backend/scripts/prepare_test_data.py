"""
测试数据准备脚本

为 WebScan AI Security Platform 准备测试数据集，包括：
- 用户数据
- 扫描任务数据
- 漏洞数据
- 通知数据
- 报告数据
- 知识库数据
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
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
        modules={"models": ["models"]},
        _create_db=True
    )
    await Tortoise.generate_schemas()
    logger.info("✅ 数据库初始化成功")


async def create_test_tasks():
    """创建测试扫描任务数据"""
    logger.info("📝 创建测试扫描任务数据...")
    
    task_types = ['port_scan', 'info_leak', 'dir_scan', 'web_side', 'baseinfo', 'subdomain', 'comprehensive']
    targets = [
        'https://www.baidu.com',
        'https://www.google.com',
        'https://www.github.com',
        'https://www.example.com',
        'https://test.com'
    ]
    
    tasks = []
    for i in range(20):
        task_data = {
            "task_name": f"测试任务_{i+1}",
            "target": targets[i % len(targets)],
            "task_type": task_types[i % len(task_types)],
            "status": ['pending', 'running', 'completed', 'failed', 'cancelled'][i % 5],
            "progress": [0, 25, 50, 75, 100][i % 5],
            "created_at": datetime.now() - timedelta(days=i),
            "updated_at": datetime.now() - timedelta(days=i) + timedelta(hours=1)
        }
        
        existing = await Task.filter(task_name=task_data["task_name"]).first()
        if not existing:
            task = await Task.create(**task_data)
            tasks.append(task)
            logger.info(f"  ✅ 创建任务: {task.task_name}")
        else:
            tasks.append(existing)
            logger.info(f"  ⚠️  任务已存在: {existing.task_name}")
    
    return tasks


async def create_test_vulnerabilities(tasks):
    """创建测试漏洞数据"""
    logger.info("📝 创建测试漏洞数据...")
    
    vuln_types = [
        'SQL Injection', 'XSS', 'CSRF', 'RCE', 'LFI', 'RFI',
        'XXE', 'SSRF', 'Path Traversal', 'Command Injection'
    ]
    severities = ['critical', 'high', 'medium', 'low']
    sources = ['awvs', 'poc_scan', 'agent_scan', 'manual']
    statuses = ['open', 'fixed', 'ignored', 'false_positive']
    
    vulnerabilities = []
    for i in range(50):
        task = tasks[i % len(tasks)]
        vuln_data = {
            "task": task,
            "vuln_type": vuln_types[i % len(vuln_types)],
            "title": f"{vuln_types[i % len(vuln_types)]} 漏洞",
            "severity": severities[i % len(severities)],
            "source": sources[i % len(sources)],
            "status": statuses[i % len(statuses)],
            "url": task.target,
            "description": f"这是一个{vuln_types[i % len(vuln_types)]}漏洞的测试描述",
            "remediation": f"建议修复方案：更新到最新版本，添加输入验证",
            "created_at": datetime.now() - timedelta(days=i)
        }
        
        existing = await Vulnerability.filter(title=vuln_data["title"], task=task).first()
        if not existing:
            vuln = await Vulnerability.create(**vuln_data)
            vulnerabilities.append(vuln)
            logger.info(f"  ✅ 创建漏洞: {vuln.title}")
        else:
            vulnerabilities.append(existing)
            logger.info(f"  ⚠️  漏洞已存在: {existing.title}")
    
    return vulnerabilities


async def create_test_notifications():
    """创建测试通知数据"""
    logger.info("📝 创建测试通知数据...")
    logger.info("  ⚠️  通知模型不存在，跳过创建通知数据")
    return []


async def create_test_reports(tasks):
    """创建测试报告数据"""
    logger.info("📝 创建测试报告数据...")
    
    report_types = ['pdf', 'html', 'json', 'docx']
    
    reports = []
    for i in range(15):
        task = tasks[i % len(tasks)]
        report_data = {
            "task": task,
            "report_name": f"安全扫描报告_{i+1}",
            "report_type": report_types[i % len(report_types)],
            "content": f"{{\"vulnerability_count\": {10 + i * 2}, \"scan_duration\": \"1h\"}}",
            "file_path": f"/data/reports/report_{i+1}.{report_types[i % len(report_types)]}"
        }
        
        existing = await Report.filter(report_name=report_data["report_name"]).first()
        if not existing:
            report = await Report.create(**report_data)
            reports.append(report)
            logger.info(f"  ✅ 创建报告: {report.report_name}")
        else:
            reports.append(existing)
            logger.info(f"  ⚠️  报告已存在: {existing.report_name}")
    
    return reports


async def create_test_knowledge_base():
    """创建测试知识库数据"""
    logger.info("📝 创建测试知识库数据...")
    
    cve_ids = ['CVE-2024-0001', 'CVE-2024-0002', 'CVE-2024-0003', 'CVE-2024-0004', 'CVE-2024-0005']
    
    knowledge_items = []
    for i in range(25):
        kb_data = {
            "cve_id": cve_ids[i % len(cve_ids)] + f"-{i}",
            "name": f"漏洞_{i+1}",
            "severity": ['critical', 'high', 'medium', 'low'][i % 4],
            "cvss_score": [9.0, 7.5, 5.0, 2.5][i % 4],
            "affected_product": f"测试产品_{i+1}",
            "description": f"这是一个测试漏洞描述，包含漏洞的详细信息",
            "remediation": f"建议修复方案：更新到最新版本",
            "references": f'[\"https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve_ids[i % len(cve_ids)]}\"]'
        }
        
        existing = await VulnerabilityKB.filter(cve_id=kb_data["cve_id"]).first()
        if not existing:
            kb = await VulnerabilityKB.create(**kb_data)
            knowledge_items.append(kb)
            logger.info(f"  ✅ 创建知识库条目: {kb.name}")
        else:
            knowledge_items.append(existing)
            logger.info(f"  ⚠️  知识库条目已存在: {existing.name}")
    
    return knowledge_items


async def create_test_poc_results(tasks):
    """创建测试POC扫描结果数据"""
    logger.info("📝 创建测试POC扫描结果数据...")
    
    poc_types = ['weblogic_cve_2020_2551', 'struts2_009', 'struts2_032', 'thinkphp_99617', 'tomcat_cve_2017_12615']
    
    poc_results = []
    for i in range(15):
        task = tasks[i % len(tasks)]
        poc_data = {
            "task": task,
            "poc_type": poc_types[i % len(poc_types)],
            "target": task.target,
            "vulnerable": i % 3 == 0,
            "message": f"POC扫描结果 - {'存在漏洞' if i % 3 == 0 else '安全'}",
            "severity": ['critical', 'high', 'medium', 'low'][i % 4] if i % 3 == 0 else None,
            "cve_id": f"CVE-2024-{i+1:04d}" if i % 3 == 0 else None
        }
        
        existing = await POCScanResult.filter(poc_type=poc_data["poc_type"], task=task).first()
        if not existing:
            poc = await POCScanResult.create(**poc_data)
            poc_results.append(poc)
            logger.info(f"  ✅ 创建POC扫描结果: {poc.poc_type}")
        else:
            poc_results.append(existing)
            logger.info(f"  ⚠️  POC扫描结果已存在: {existing.poc_type}")
    
    return poc_results


async def create_test_agent_tasks():
    """创建测试AI Agent任务数据"""
    logger.info("📝 创建测试AI Agent任务数据...")
    
    task_types = ['code_generation', 'vuln_analysis', 'report_generation', 'poc_generation']
    
    agent_tasks = []
    for i in range(10):
        from uuid import uuid4
        task_data = {
            "task_id": uuid4(),
            "user_id": f"test_user_{i+1}",
            "input_json": f'{{\"target\": \"https://test{i+1}.com\", \"type\": \"{task_types[i % len(task_types)]}\"}}',
            "task_type": task_types[i % len(task_types)],
            "status": ['pending', 'running', 'completed', 'failed'][i % 4]
        }
        
        existing = await AgentTask.filter(task_id=task_data["task_id"]).first()
        if not existing:
            task = await AgentTask.create(**task_data)
            agent_tasks.append(task)
            logger.info(f"  ✅ 创建Agent任务: {task.task_type}")
        else:
            agent_tasks.append(existing)
            logger.info(f"  ⚠️  Agent任务已存在: {existing.task_type}")
    
    return agent_tasks


async def create_test_agent_results(agent_tasks):
    """创建测试AI Agent结果数据"""
    logger.info("📝 创建测试AI Agent结果数据...")
    
    agent_results = []
    for i, task in enumerate(agent_tasks):
        if task.status == 'completed':
            from uuid import uuid4
            result_data = {
                "id": uuid4(),
                "task": task,
                "final_output": f'{{\"result\": \"success\", \"data\": \"测试结果数据_{i+1}\"}}',
                "error_message": None,
                "execution_time": 60 + i * 10
            }
            
            existing = await AgentResult.filter(task=task).first()
            if not existing:
                result = await AgentResult.create(**result_data)
                agent_results.append(result)
                logger.info(f"  ✅ 创建Agent结果: {result.task.task_type}")
            else:
                agent_results.append(existing)
                logger.info(f"  ⚠️  Agent结果已存在: {existing.task.task_type}")
    
    return agent_results


async def create_test_ai_chats():
    """创建测试AI对话数据"""
    logger.info("📝 创建测试AI对话数据...")
    
    from uuid import uuid4
    chat_types = ['general', 'security', 'code_analysis']
    
    chat_instances = []
    for i in range(5):
        chat_data = {
            "id": uuid4(),
            "user_id": f"test_user_{i+1}",
            "chat_name": f"测试对话_{i+1}",
            "chat_type": chat_types[i % len(chat_types)],
            "status": 'active'
        }
        
        existing = await AIChatInstance.filter(id=chat_data["id"]).first()
        if not existing:
            chat = await AIChatInstance.create(**chat_data)
            chat_instances.append(chat)
            logger.info(f"  ✅ 创建AI对话: {chat.chat_name}")
        else:
            chat_instances.append(existing)
            logger.info(f"  ⚠️  AI对话已存在: {existing.chat_name}")
    
    return chat_instances


async def main():
    """主函数：执行所有测试数据的创建"""
    logger.info("🚀 开始准备测试数据...")
    
    try:
        await init_db()
        
        tasks = await create_test_tasks()
        vulnerabilities = await create_test_vulnerabilities(tasks)
        notifications = await create_test_notifications()
        reports = await create_test_reports(tasks)
        knowledge_items = await create_test_knowledge_base()
        poc_results = await create_test_poc_results(tasks)
        agent_tasks = await create_test_agent_tasks()
        agent_results = await create_test_agent_results(agent_tasks)
        ai_chats = await create_test_ai_chats()
        
        logger.info("✅ 测试数据准备完成！")
        logger.info(f"📊 数据统计:")
        logger.info(f"  - 任务: {len(tasks)}")
        logger.info(f"  - 漏洞: {len(vulnerabilities)}")
        logger.info(f"  - 通知: {len(notifications)}")
        logger.info(f"  - 报告: {len(reports)}")
        logger.info(f"  - 知识库: {len(knowledge_items)}")
        logger.info(f"  - POC扫描结果: {len(poc_results)}")
        logger.info(f"  - AI Agent任务: {len(agent_tasks)}")
        logger.info(f"  - AI Agent结果: {len(agent_results)}")
        logger.info(f"  - AI对话: {len(ai_chats)}")
        
    except Exception as e:
        logger.error(f"❌ 准备测试数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())

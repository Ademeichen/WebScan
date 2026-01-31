import asyncio
from tortoise import Tortoise
from models import Vulnerability, Task

async def check():
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['models']}
    )
    await Tortoise.generate_schemas()
    
    tasks = await Task.all()
    print(f'任务表共有 {len(tasks)} 条记录')
    for task in tasks:
        print(f'任务ID: {task.id}, 任务名称: {task.task_name}')
        vulns = await Vulnerability.filter(task=task)
        print(f'  该任务有 {len(vulns)} 个漏洞')
        for vuln in vulns:
            print(f'    漏洞ID: {vuln.id}, source_id: {vuln.source_id}, title: {vuln.title}')
    
    await Tortoise.close_connections()

asyncio.run(check())
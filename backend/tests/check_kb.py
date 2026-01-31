import asyncio
from tortoise import Tortoise
from models import VulnerabilityKB

async def check():
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['models']}
    )
    await Tortoise.generate_schemas()
    
    items = await VulnerabilityKB.all()
    print(f'漏洞知识库表共有 {len(items)} 条记录')
    for item in items:
        print(f'ID: {item.id}, CVE: {item.cve_id}, Name: {item.name}')
    
    await Tortoise.close_connections()

asyncio.run(check())
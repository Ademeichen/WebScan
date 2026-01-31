import asyncio
from tortoise import Tortoise
from models import Vulnerability

async def check():
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['models']}
    )
    await Tortoise.generate_schemas()
    
    items = await Vulnerability.all()
    print(f'vulnerabilities表共有 {len(items)} 条记录')
    for item in items:
        print(f'ID: {item.id}, Title: {item.title}, Type: {item.vuln_type}, Severity: {item.severity}')
    
    await Tortoise.close_connections()

asyncio.run(check())
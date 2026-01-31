import asyncio
from tortoise import Tortoise
from models import Vulnerability, VulnerabilityKB

async def check():
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['models']}
    )
    await Tortoise.generate_schemas()
    
    print('检查 Vulnerability 表中是否有 ID 3790342569020359700')
    vuln = await Vulnerability.get_or_none(id=3790342569020359700)
    print(f'Vulnerability 表: {vuln}')
    
    print('\n检查 VulnerabilityKB 表中是否有 ID 3790342569020359700')
    kb_vuln = await VulnerabilityKB.get_or_none(id=3790342569020359700)
    print(f'VulnerabilityKB 表: {kb_vuln}')
    
    print('\n检查 Vulnerability 表中是否有 source_id 3790342569020359700')
    vuln_by_source = await Vulnerability.get_or_none(source_id='3790342569020359700')
    print(f'Vulnerability 表 (by source_id): {vuln_by_source}')
    
    print('\n检查 Vulnerability 表中是否有 source_id 3790342569020359723')
    vuln_by_source2 = await Vulnerability.get_or_none(source_id='3790342569020359723')
    print(f'Vulnerability 表 (by source_id 3790342569020359723): {vuln_by_source2}')
    
    await Tortoise.close_connections()

asyncio.run(check())
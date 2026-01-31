import asyncio
from tortoise import Tortoise
from models import VulnerabilityKB

async def add_sample_data():
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['models']}
    )
    await Tortoise.generate_schemas()
    
    sample_vulns = [
        VulnerabilityKB(
            cve_id='CVE-2021-44228',
            name='Log4j 远程代码执行漏洞',
            description='Apache Log4j2 2.0-beta9 到 2.15.0 版本存在 JNDI 注入漏洞，攻击者可以通过构造恶意请求执行任意代码。',
            severity='critical',
            cvss_score=10.0,
            affected_product='Apache Log4j2',
            affected_versions='2.0-beta9 到 2.15.0',
            poc_code=None,
            remediation='升级到 Log4j 2.17.1 或更高版本',
            references='["https://logging.apache.org/log4j/2.x/security.html"]'
        ),
        VulnerabilityKB(
            cve_id='CVE-2022-22965',
            name='Spring Framework 远程代码执行漏洞',
            description='Spring Framework 存在数据绑定漏洞，攻击者可以通过构造恶意请求执行任意代码。',
            severity='critical',
            cvss_score=9.8,
            affected_product='Spring Framework',
            affected_versions='5.3.0 到 5.3.17, 5.2.0 到 5.2.19',
            poc_code=None,
            remediation='升级到 Spring Framework 5.3.18+ 或 5.2.20+',
            references='["https://spring.io/blog/2022/03/31/spring-framework-rce-early-announcements"]'
        ),
        VulnerabilityKB(
            cve_id='CVE-2021-34527',
            name='Windows Print Spooler 远程代码执行漏洞',
            description='Windows Print Spooler 存在远程代码执行漏洞，攻击者可以通过构造恶意请求执行任意代码。',
            severity='critical',
            cvss_score=8.8,
            affected_product='Windows Print Spooler',
            affected_versions='Windows 7, 8.1, 10, Server 2008, 2012, 2016, 2019',
            poc_code=None,
            remediation='安装 Microsoft 安全更新',
            references='["https://msrc.microsoft.com/update-guide/vulnerability/CVE-2021-34527"]'
        )
    ]
    
    for vuln in sample_vulns:
        await vuln.save()
        print(f'已添加漏洞: {vuln.cve_id} - {vuln.name}')
    
    print(f'\n总共添加了 {len(sample_vulns)} 条漏洞记录')
    
    await Tortoise.close_connections()

asyncio.run(add_sample_data())
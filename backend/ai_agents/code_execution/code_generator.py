"""
代码自动生成模块

基于模板和LLM生成扫描脚本。
"""
import logging
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from ..agent_config import agent_config
from .environment import EnvironmentAwareness

logger = logging.getLogger(__name__)


class CodeGenerationRequest(BaseModel):
    """
    代码生成请求模型
    """
    scan_type: str = Field(
        description="扫描类型：port_scan、vuln_scan、dir_scan、subdomain_scan等"
    )
    target: str = Field(description="扫描目标（URL/IP）")
    requirements: str = Field(default="", description="特殊需求或要求")
    language: str = Field(default="python", description="代码语言：python、bash、powershell")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="额外参数")


class CodeGenerationResponse(BaseModel):
    """
    代码生成响应模型
    """
    code: str = Field(description="生成的代码")
    language: str = Field(description="代码语言")
    description: str = Field(description="代码说明")
    estimated_time: int = Field(description="预计执行时间（秒）")
    dependencies: List[str] = Field(default_factory=list, description="依赖列表")


class CodeGenerator:
    """
    代码生成器类
    
    负责基于模板和LLM生成扫描脚本。
    """
    
    def __init__(self):
        self.env_awareness = EnvironmentAwareness()
        self.llm = None
        
        if agent_config.ENABLE_LLM_PLANNING:
            try:
                self.llm = ChatOpenAI(
                    model=agent_config.MODEL_ID,
                    temperature=0.3,
                    openai_api_key=agent_config.OPENAI_API_KEY,
                    base_url=agent_config.OPENAI_BASE_URL
                )
                logger.info("✅ LLM代码生成器初始化完成")
            except Exception as e:
                logger.error(f"LLM初始化失败: {str(e)}")
                self.llm = None
    
    def _get_template(self, scan_type: str) -> str:
        """
        获取扫描模板
        
        Args:
            scan_type: 扫描类型
            
        Returns:
            str: 模板代码
        """
        templates = {
            "port_scan": """
#!/usr/bin/env python3
import socket
import sys
from concurrent.futures import ThreadPoolExecutor

def scan_port(target: str, port: int, timeout: int = 3):
    \"\"\"扫描单个端口\"\"\"
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target, port))
        if result == 0:
            return True
        return False
    except:
        return False

def main():
    target = "{target}"
    ports = [21, 22, 80, 443, 445, 3306, 3389, 8080]
    
    print(f"开始端口扫描: {target}")
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(
            lambda p: scan_port(target, p),
            ports
        ))
    
    open_ports = [p for p, is_open in zip(ports, results) if is_open]
    
    print(f"扫描完成，开放端口: {open_ports}")
""",
            "vuln_scan": """
#!/usr/bin/env python3
import requests
import sys

def check_vulnerability(target: str, vuln_type: str, payload: str):
    \"\"\"检查单个漏洞\"\"\"
    try:
        url = f"{target}/{vuln_type}"
        response = requests.post(url, data=payload, timeout=10, verify=False)
        
        if response.status_code == 200:
            return {{
                "vulnerable": True,
                "status_code": response.status_code,
                "response": response.text[:200]
            }}
        return {{
            "vulnerable": False,
            "status_code": response.status_code,
            "error": str(response.status_code)
        }}
    except Exception as e:
        return {{
            "vulnerable": False,
            "error": str(e)
        }}

def main():
    target = "{target}"
    
    print(f"开始漏洞扫描: {target}")
    
    payloads = {{
        "sqli": "' OR '1'='1",
        "xss": "<script>alert('XSS')</script>",
        "rce": "; cat /etc/passwd"
    }}
    
    for vuln_type, payload in payloads.items():
        result = check_vulnerability(target, vuln_type, payload)
        if result.get("vulnerable"):
            print(f"[+] 发现漏洞: {{vuln_type}}")
        else:
            print(f"[-] 未发现漏洞: {{vuln_type}}")
""",
            "dir_scan": """
#!/usr/bin/env python3
import requests
import sys
from urllib.parse import urljoin

def scan_directory(target: str, wordlist: str = None, extensions: str = None):
    \"\"\"扫描目录\"\"\"
    try:
        if wordlist is None:
            wordlist = "admin,backup,config,db,sql,backup,old,test"
        if extensions is None:
            extensions = ".php,.asp,.aspx,.jsp,.js,.html,.htm,.txt,.bak,.zip,.tar,.gz"
        
        base_url = target if target.endswith("/") else target + "/"
        
        found_dirs = []
        
        for word in wordlist.split(","):
            for ext in extensions.split(","):
                test_url = urljoin(base_url, f"{{word}}{{ext}}")
                
                try:
                    response = requests.get(test_url, timeout=5, verify=False)
                    
                    if response.status_code == 200:
                        found_dirs.append(test_url)
                        print(f"[+] 发现目录: {{test_url}}")
                except:
                    pass
        
        print(f"目录扫描完成，发现: {{len(found_dirs)}} 个目录")
        return found_dirs

def main():
    target = "{target}"
    scan_directory(target)
""",
            "subdomain_scan": """
#!/usr/bin/env python3
import dns.resolver
import sys

def resolve_subdomain(domain: str):
    \"\"\"解析子域名\"\"\"
    try:
        answers = dns.resolver.resolve(domain, 'A')
        return answers
    except Exception as e:
        print(f"DNS解析失败: {{domain}} - {{str(e)}}")
        return []

def brute_subdomain(domain: str, wordlist: str = None):
    \"\"\"暴力破解子域名\"\"\"
    if wordlist is None:
        wordlist = "www,mail,ftp,admin,blog,dev,test,staging,api"
    
    subdomains = []
    
    for word in wordlist.split(","):
        subdomain = f"{{word}}.{{domain}}"
        try:
            ip = resolve_subdomain(subdomain)
            if ip:
                subdomains.append(subdomain)
                print(f"[+] 发现子域名: {{subdomain}}")
        except:
            pass
    
    print(f"子域名扫描完成，发现: {{len(subdomains)}} 个子域名")
    return subdomains

def main():
    domain = "{target}"
    brute_subdomain(domain)
"""
        }
        
        return templates.get(scan_type, templates.get("port_scan", ""))
    
    async def generate_code(
        self,
        scan_type: str,
        target: str,
        requirements: str = "",
        language: str = "python",
        additional_params: Dict[str, Any] = None
    ) -> CodeGenerationResponse:
        """
        生成扫描代码
        
        Args:
            self: 代码生成器实例
            scan_type: 扫描类型
            target: 扫描目标
            requirements: 特殊需求
            language: 代码语言
            additional_params: 额外参数
            
        Returns:
            CodeGenerationResponse: 代码生成响应
        """
        try:
            if self.llm:
                return await self._llm_generate_code(
                    scan_type, target, requirements, language, additional_params
                )
            else:
                return await self._template_generate_code(
                    scan_type, target, requirements, language, additional_params
                )
        except Exception as e:
            logger.error(f"代码生成失败: {str(e)}")
            return CodeGenerationResponse(
                code="",
                language=language,
                description=f"代码生成失败: {str(e)}",
                estimated_time=0,
                dependencies=[]
            )
    
    async def _llm_generate_code(
        self,
        scan_type: str,
        target: str,
        requirements: str,
        language: str,
        additional_params: Dict[str, Any]
    ) -> CodeGenerationResponse:
        """
        使用LLM生成代码
        
        Args:
            self: 代码生成器实例
            scan_type: 扫描类型
            target: 扫描目标
            requirements: 特殊需求
            language: 代码语言
            additional_params: 额外参数
            
        Returns:
            CodeGenerationResponse: 代码生成响应
        """
        env_info = self.env_awareness.get_environment_report()
        
        system_prompt = f"""
你是专业的Web安全扫描脚本编写专家。

环境信息：
- 操作系统: {env_info['os_info'].get('system', 'Unknown')}
- Python版本: {env_info['python_info'].get('version', 'Unknown')}
- 可用工具: {', '.join([f'{{k}}: {{v}}' for k, v in env_info['available_tools'].items() if v.get('available')])}

扫描任务：
- 扫描类型: {scan_type}
- 扫描目标: {target}
- 特殊需求: {requirements}
- 代码语言: {language}

要求：
1. 生成安全、高效的扫描脚本
2. 避免使用危险操作
3. 包含适当的错误处理
4. 添加必要的注释说明
5. 代码应该可以直接执行，无需额外配置

请生成完整的扫描脚本代码，只返回代码内容，不要包含其他说明。
"""
        
        user_prompt = f"生成一个{scan_type}扫描脚本，目标为{target}"
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt)
            ])
            
            chain = prompt | self.llm | JsonOutputParser(pydantic_object=CodeGenerationResponse)
            result = await chain.ainvoke({})
            
            logger.info(f"✅ LLM代码生成完成: {scan_type}")
            
            return CodeGenerationResponse(
                code=result.get("code", ""),
                language=result.get("language", language),
                description=result.get("description", ""),
                estimated_time=result.get("estimated_time", 60),
                dependencies=result.get("dependencies", [])
            )
        except Exception as e:
            logger.error(f"LLM代码生成失败: {str(e)}")
            raise
    
    async def _template_generate_code(
        self,
        scan_type: str,
        target: str,
        requirements: str,
        language: str,
        additional_params: Dict[str, Any]
    ) -> CodeGenerationResponse:
        """
        使用模板生成代码
        
        Args:
            self: 代码生成器实例
            scan_type: 扫描类型
            target: 扫描目标
            requirements: 特殊需求
            language: 代码语言
            additional_params: 额外参数
            
        Returns:
            CodeGenerationResponse: 代码生成响应
        """
        template = self._get_template(scan_type)
        code = template.replace("{target}", target)
        
        if requirements:
            code += f"\n# 特殊需求: {requirements}"
        
        if additional_params:
            code += f"\n# 额外参数: {additional_params}"
        
        logger.info(f"✅ 模板代码生成完成: {scan_type}")
        
        return CodeGenerationResponse(
            code=code,
            language=language,
            description="基于模板生成的扫描脚本",
            estimated_time=60,
            dependencies=[]
        )
    
    def validate_code(self, code: str, language: str) -> Dict[str, Any]:
        """
        验证代码安全性
        
        Args:
            code: 代码内容
            language: 代码语言
            
        Returns:
            Dict: 验证结果
        """
        issues = []
        
        dangerous_patterns = [
            "eval(",
            "exec(",
            "system(",
            "__import__(",
            "subprocess.call(",
            "os.system(",
            "shell=True",
            "rm -rf",
            "format ",
            "pickle.loads",
            "yaml.load"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                issues.append({
                    "type": "security",
                    "severity": "high",
                    "message": f"检测到危险操作: {pattern}",
                    "line": self._find_line_with_pattern(code, pattern)
                })
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def _find_line_with_pattern(self, code: str, pattern: str) -> int:
        """
        查找包含特定模式的行号
        
        Args:
            code: 代码内容
            pattern: 模式
            
        Returns:
            int: 行号（从1开始）
        """
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if pattern in line:
                return i
        return 0

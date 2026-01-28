from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import asyncio
import os
import tempfile
import sys
import subprocess
from backend.models import VulnerabilityKB
# from langchain_community.llms import OpenAI
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain

# TODO: 实际生产环境中，这里应该调用 LongChain API 或集成 LongChain 调用
# 这里使用 OpenAI 作为示例，实际生产中应替换为 LongChain 调用

# 尝试导入 pocsuite3
# TODO: 实际生产环境中，这里应该调用 Pocsuite3 API 或集成 Pocsuite3 调用
try:
    from pocsuite3.api import init_pocsuite
    from pocsuite3.lib.core.data import conf
    HAS_POCSUITE = True
except ImportError:
    HAS_POCSUITE = False

router = APIRouter()
logger = logging.getLogger(__name__)

class POCGenRequest(BaseModel):
    vuln_id: Optional[int] = None
    vuln_description: Optional[str] = None
    target: Optional[str] = None

class POCGenResponse(BaseModel):
    message: str
    poc_code: Optional[str] = None
    status: str

# 模拟的 POC 生成提示模板
POC_PROMPT_TEMPLATE = """
You are a security researcher. Write a Pocsuite3 POC script for the following vulnerability:
Name/Description: {description}

The POC should inherit from `PocTestCase` and implement `_verify` and `_attack` methods.
Return ONLY the python code.
"""

class POCGenerator:
    """POC 生成与执行引擎"""
    
    def __init__(self):
        self.model_id = "ms-5c9c1aaf-f843-4648-8e24-8e0a9e4f2118"
        
    async def generate_from_kb(self, kb_item: VulnerabilityKB) -> str:
        """从知识库条目生成 POC"""
        description = f"{kb_item.name}\n{kb_item.description}"
        return await self.generate_from_description(description)

    async def generate_from_description(self, description: str) -> str:
        """基于描述生成 POC 代码"""
        try:
            # 这里集成 LongChain 调用指定 API
            # model_id = "ms-5c9c1aaf-f843-4648-8e24-8e0a9e4f2118" 
            
            logger.info(f"正在调用 AI 生成 POC，模型: {self.model_id}, 描述长度: {len(description)}")
            
            # TODO: Replace with actual LangChain call
            # llm = OpenAI(model_name=self.model_id, ...)
            # chain = LLMChain(llm=llm, prompt=PromptTemplate.from_template(POC_PROMPT_TEMPLATE))
            # poc_code = chain.run(description)
            
            # 模拟生成过程
            await asyncio.sleep(2) 
            
            # 生成一个基于 Pocsuite3 的模板代码
            # 尝试根据描述提取一些关键信息（模拟）
            vuln_type = "Code Execution"
            if "SQL" in description: vuln_type = "SQL Injection"
            if "XSS" in description: vuln_type = "XSS"
            
            poc_code = f"""
from pocsuite3.api import Output, POCBase, register_poc, requests, logger

class AIGeneratedPOC(POCBase):
    vulID = '0'
    version = '1.0'
    author = ['AI Generator']
    vulDate = '2025-01-01'
    createDate = '2025-01-01'
    updateDate = '2025-01-01'
    references = []
    name = 'AI Generated POC for {vuln_type}'
    appPowerLink = ''
    appName = 'Unknown'
    appVersion = 'Unknown'
    vulType = '{vuln_type}'
    desc = '''
    {description.replace("'''", "'''")}
    '''
    samples = []
    install_requires = ['']

    def _verify(self):
        result = {{}}
        target = self.url
        # AI Generated verification logic placeholder
        # In a real scenario, the LLM would populate this based on the vulnerability description
        try:
            # Simple heuristic: check if target is accessible
            r = requests.get(target, timeout=10)
            
            # 模拟检测逻辑：如果描述里包含特定关键字，我们假设检测成功（仅演示）
            if r.status_code == 200:
                # 这里应该有真实的 Payload 发送逻辑
                pass
                
        except Exception as e:
            pass
            
        return self.parse_output(result)

    def _attack(self):
        return self._verify()

    def parse_output(self, result):
        output = Output(self)
        if result:
            output.success(result)
        else:
            output.fail('Target is not vulnerable')
        return output

register_poc(AIGeneratedPOC)
"""
            return poc_code
        except Exception as e:
            logger.error(f"AI POC Generation failed: {e}")
            raise e

    async def execute_poc(self, poc_code: str, target: str) -> Dict[str, Any]:
        """执行 POC 代码"""
        if not HAS_POCSUITE:
            return {"vulnerable": False, "message": "Pocsuite3 not installed", "status": "error"}

        tmp_path = None
        try:
            # 写入临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(poc_code)
                tmp_path = tmp.name
                
            logger.info(f"Executing POC for target: {target}")
            
            # 使用 subprocess 调用 pocsuite3
            cmd = [sys.executable, "-m", "pocsuite3.cli", "-r", tmp_path, "-u", target, "--verify"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode()
            error = stderr.decode()
            
            is_vulnerable = "success" in output.lower() or "vulnerable" in output.lower()
            
            msg = "Vulnerable" if is_vulnerable else "Not Vulnerable"
            if len(output) > 200:
                msg += f" (Output truncated: {output[:200]}...)"
            else:
                msg += f" ({output.strip()})"
                
            return {
                "status": "completed",
                "vulnerable": is_vulnerable,
                "message": msg,
                "full_output": output
            }
            
        except Exception as e:
            logger.error(f"POC execution failed: {e}")
            return {"vulnerable": False, "message": str(e), "status": "error"}
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

# 全局实例
poc_generator = POCGenerator()

@router.post("/generate", response_model=POCGenResponse)
async def generate_poc(request: POCGenRequest):
    """
    智能生成 POC API
    """
    description = request.vuln_description
    
    # 如果提供了 ID，从 KB 获取描述
    if request.vuln_id:
        kb_item = await VulnerabilityKB.get_or_none(id=request.vuln_id)
        if kb_item:
            description = f"{kb_item.name}\n{kb_item.description}"
    
    if not description:
        raise HTTPException(status_code=400, detail="Description or valid KB ID required")

    try:
        poc_code = await poc_generator.generate_from_description(description)
        return {"message": "POC generated successfully", "poc_code": poc_code, "status": "success"}

    except Exception as e:
        logger.error(f"POC generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_generated_poc(poc_code: str, target: str):
    """
    执行生成的 POC API
    """
    try:
        result = await poc_generator.execute_poc(poc_code, target)
        return result
    except Exception as e:
        logger.error(f"POC execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

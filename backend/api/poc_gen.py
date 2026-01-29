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
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# 初始化 LLM
llm = ChatOpenAI(
    model=settings.MODEL_ID,
    temperature=0.7,
    openai_api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL
)

# 尝试导入 pocsuite3
try:
    from pocsuite3.api import init_pocsuite
    from pocsuite3.lib.core.data import conf
    HAS_POCSUITE = True
except ImportError:
    HAS_POCSUITE = False

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
Return ONLY python code.
"""

class POCGenerator:
    """POC 生成与执行引擎"""
    
    def __init__(self):
        self.llm = llm
        
    async def generate_from_kb(self, kb_item: VulnerabilityKB) -> str:
        """从知识库条目生成 POC"""
        description = f"{kb_item.name}\n{kb_item.description}"
        return await self.generate_from_description(description)

    async def generate_from_description(self, description: str) -> str:
        """基于描述生成 POC 代码"""
        try:
            logger.info(f"正在调用 AI 生成 POC，模型: {self.llm.model_name}, 描述长度: {len(description)}")
            
            # 构建提示模板
            prompt = ChatPromptTemplate.from_template(POC_PROMPT_TEMPLATE)
            
            # 使用 LangChain 0.3.x 的 LCEL 语法
            chain = prompt | self.llm
            
            # 调用 LLM 生成 POC 代码
            response = await chain.ainvoke({"description": description})
            poc_code = response.content
            
            logger.info(f"POC 生成成功，代码长度: {len(poc_code)}")
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
            
            # 解析输出判断是否漏洞存在
            is_vulnerable = self._parse_pocsuite_output(output)
            
            msg = "Vulnerable" if is_vulnerable else "Not Vulnerable"
            if len(output) > 200:
                msg += f" (Output truncated: {output[:200]}...)"
            else:
                msg += f" ({output.strip()})"
                
            return {
                "status": "completed",
                "vulnerable": is_vulnerable,
                "message": msg,
                "full_output": output,
                "error": error if error else None
            }
            
        except Exception as e:
            logger.error(f"POC execution failed: {e}")
            return {"vulnerable": False, "message": str(e), "status": "error"}
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _parse_pocsuite_output(self, output: str) -> bool:
        """
        解析 Pocsuite3 输出，判断是否存在漏洞
        
        Args:
            output: Pocsuite3 的输出内容
            
        Returns:
            bool: 是否存在漏洞
        """
        # Pocsuite3 的成功输出通常包含以下关键词
        success_keywords = [
            "success",
            "vulnerable",
            "vuln",
            "exploit",
            "exists"
        ]
        
        output_lower = output.lower()
        
        # 检查是否包含成功关键词
        for keyword in success_keywords:
            if keyword in output_lower:
                return True
        
        # 检查是否包含 Pocsuite3 的成功标记
        if "[+]" in output and "success" in output_lower:
            return True
            
        return False

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

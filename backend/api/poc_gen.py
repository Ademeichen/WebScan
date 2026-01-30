from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import asyncio
import os
import tempfile
import sys

from backend.models import VulnerabilityKB
from backend.config import settings
import sys
from pathlib import Path
from backend.utils.poc_utils import parse_pocsuite_output

router = APIRouter()
logger = logging.getLogger(__name__)

# 添加Seebug_Agent到Python路径
seebug_agent_path = Path(__file__).parent.parent.parent / "Seebug_Agent"
if str(seebug_agent_path) not in sys.path:
    sys.path.insert(0, str(seebug_agent_path))

try:
    from Seebug_Agent import POCGenerator, Config as SeebugConfig
except ImportError as e:
    logger.error(f"Failed to import Seebug_Agent modules: {e}")
    # 使用备用方案
    POCGenerator = None
    SeebugConfig = None


class POCGenRequest(BaseModel):
    vuln_id: Optional[int] = None
    vuln_description: Optional[str] = None
    target: Optional[str] = None

class POCGenResponse(BaseModel):
    message: str
    poc_code: Optional[str] = None
    status: str


class POCGeneratorWrapper:
    """POC 生成与执行引擎包装类"""
    
    def __init__(self):
        self.seebug_config = SeebugConfig()
        self.poc_generator = POCGenerator(self.seebug_config)
        
    async def generate_from_kb(self, kb_item: VulnerabilityKB) -> str:
        """从知识库条目生成 POC"""
        vul_info = {
            "name": kb_item.name,
            "description": kb_item.description,
            "type": kb_item.severity or "Unknown",
            "component": kb_item.affected_product or "Unknown",
            "solution": kb_item.solution or "Unknown"
        }
        return self.poc_generator.generate_poc(vul_info)

    async def generate_from_description(self, description: str) -> str:
        """基于描述生成 POC 代码"""
        vul_info = {
            "name": "Unknown Vulnerability",
            "description": description,
            "type": "Unknown",
            "component": "Unknown",
            "solution": "Unknown"
        }
        return self.poc_generator.generate_poc(vul_info)

    async def execute_poc(self, poc_code: str, target: str) -> Dict[str, Any]:
        """执行 POC 代码"""
        try:
            # 尝试导入 pocsuite3
            from pocsuite3.api import init_pocsuite
            from pocsuite3.lib.core.data import conf
            
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
                
                # 解析输出
                is_vulnerable = parse_pocsuite_output(output)
                
                msg = "Vulnerable" if is_vulnerable else "Not Vulnerable"
                if len(output) > 200:
                    msg += f" (Output truncated: {output[:200]}...)"
                else:
                    msg += f" ({output.strip()})"
                    
                return {
                    "status": "completed",
                    "vulnerable": is_vulnerable,
                    "message": msg,
                    "output": output,
                    "error": error
                }
                
            except Exception as e:
                logger.error(f"POC execution failed: {e}")
                return {"vulnerable": False, "message": str(e), "status": "error"}
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except ImportError:
            return {"vulnerable": False, "message": "Pocsuite3 not installed", "status": "error"}
    



# 全局实例
poc_generator_wrapper = POCGeneratorWrapper()

@router.post("/generate", response_model=POCGenResponse)
async def generate_poc(request: POCGenRequest):
    """
    智能生成 POC API
    """
    description = request.vuln_description
    
    # 如果提供了 ID,从 KB 获取描述
    if request.vuln_id:
        kb_item = await VulnerabilityKB.get_or_none(id=request.vuln_id)
        if kb_item:
            description = f"{kb_item.name}\n{kb_item.description}"
    
    if not description:
        raise HTTPException(status_code=400, detail="Description or valid KB ID required")

    try:
        poc_code = await poc_generator_wrapper.generate_from_description(description)
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
        result = await poc_generator_wrapper.execute_poc(poc_code, target)
        return result
    except Exception as e:
        logger.error(f"POC execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

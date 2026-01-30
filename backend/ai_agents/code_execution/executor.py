"""
统一执行器

整合环境感知、代码生成和功能补充能力,提供统一的代码执行接口。
"""
import asyncio
import logging
import sys

import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .environment import EnvironmentAwareness
from .code_generator import CodeGenerator
from .capability_enhancer import CapabilityEnhancer
from .process_utils import execute_process, decode_output, handle_process_error

logger = logging.getLogger(__name__)


class ExecutionResult:
    """
    执行结果类
    """
    
    def __init__(
        self,
        status: str,
        output: str = "",
        error: str = "",
        execution_time: float = 0.0,
        exit_code: int = 0
    ):
        self.status = status
        self.output = output
        self.error = error
        self.execution_time = execution_time
        self.exit_code = exit_code
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict: 执行结果
        """
        return {
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "exit_code": self.exit_code
        }


class UnifiedExecutor:
    """
    统一执行器类
    
    整合环境感知、代码生成和功能补充能力,
    提供安全的代码执行环境。
    """
    
    def __init__(
        self,
        timeout: int = 60,
        max_memory: int = 512,
        enable_sandbox: bool = True
    ):
        """
        初始化统一执行器
        
        Args:
            timeout: 执行超时时间(秒)
            max_memory: 最大内存限制(MB)
            enable_sandbox: 是否启用沙箱隔离
        """
        self.timeout = timeout
        self.max_memory = max_memory
        self.enable_sandbox = enable_sandbox
        
        self.env_awareness = EnvironmentAwareness()
        self.code_generator = CodeGenerator()
        self.capability_enhancer = CapabilityEnhancer()
        
        # 使用绝对路径创建工作目录
        self.workspace = Path(__file__).parent / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ 统一执行器初始化完成: timeout={timeout}s, sandbox={enable_sandbox}")
    
    async def execute_code(
        self,
        code: str,
        language: str = "python",
        target: Optional[str] = None,
        **kwargs
    ) -> ExecutionResult:
        """
        执行代码
        
        Args:
            code: 代码内容
            language: 代码语言
            target: 扫描目标(可选)
            **kwargs: 额外参数
            
        Returns:
            ExecutionResult: 执行结果
        """
        try:
            logger.info(f"🔧 开始执行代码: language={language}")
            
            # 验证代码安全性
            validation = self.code_generator.validate_code(code, language)
            if not validation["valid"]:
                logger.warning(f"代码验证失败: {validation['issues']}")
                return ExecutionResult(
                    status="failed",
                    error="代码验证失败",
                    output="",
                    execution_time=0.0
                )
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=f".{self._get_file_extension(language)}",
                delete=False,
                encoding="utf-8"
            ) as f:
                f.write(code)
                temp_file = f.name
            
            # 执行代码
            start_time = datetime.now()
            
            try:
                if language == "python":
                    result = await self._execute(temp_file, language, target, **kwargs)
                elif language == "bash":
                    result = await self._execute(temp_file, language, target, **kwargs)
                elif language == "powershell":
                    result = await self._execute(temp_file, language, target, **kwargs)
                else:
                    result = ExecutionResult(
                        status="failed",
                        error=f"不支持的语言: {language}",
                        output="",
                        execution_time=0.0
                    )
            finally:
                execution_time = (datetime.now() - start_time).total_seconds()
                result.execution_time = execution_time
                
                # 清理临时文件
                try:
                    Path(temp_file).unlink()
                except:
                    pass
            
            logger.info(f"✅ 代码执行完成: status={result.status}, time={execution_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ 代码执行失败: {str(e)}")
            return ExecutionResult(
                status="failed",
                error=str(e),
                output="",
                execution_time=0.0
            )
    
    async def _execute(
        self,
        script_file: str,
        language: str,
        target: Optional[str] = None,
        **kwargs
    ) -> ExecutionResult:
        """
        执行脚本
        
        Args:
            script_file: 脚本文件路径
            language: 代码语言
            target: 扫描目标
            **kwargs: 额外参数
            
        Returns:
            ExecutionResult: 执行结果
        """
        try:
            cmd = self._get_command(language, script_file, target)
            
            stdout, stderr, exit_code = await execute_process(
                cmd=cmd,
                timeout=self.timeout,
                cwd=str(self.workspace)
            )
            
            output = decode_output(stdout)
            error = decode_output(stderr)
            
            return ExecutionResult(
                status="success" if exit_code == 0 else "failed",
                output=output,
                error=error,
                exit_code=exit_code
            )
        except Exception as e:
            return ExecutionResult(
                status="failed",
                error=handle_process_error(e, f"{language}脚本执行"),
                output="",
                exit_code=-1
            )
    
    def _get_command(
        self,
        language: str,
        script_file: str,
        target: Optional[str] = None
    ) -> list:
        """
        获取执行命令
        
        Args:
            language: 代码语言
            script_file: 脚本文件路径
            target: 扫描目标
            
        Returns:
            list: 命令列表
        """
        if language == "python":
            cmd = [sys.executable, script_file]
        elif language == "bash":
            cmd = ["bash", script_file]
        elif language == "powershell":
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_file]
        else:
            cmd = [language, script_file]
        
        if target:
            cmd.append(target)
        
        return cmd
    
    async def generate_and_execute(
        self,
        scan_type: str,
        target: str,
        requirements: str = "",
        language: str = "python",
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成并执行代码
        
        Args:
            scan_type: 扫描类型
            target: 扫描目标
            requirements: 特殊需求
            language: 代码语言
            **kwargs: 额外参数
            
        Returns:
            Dict: 执行结果
        """
        try:
            logger.info(f"🔧 生成并执行代码: scan_type={scan_type}, target={target}")
            
            # 生成代码
            code_response = await self.code_generator.generate_code(
                scan_type=scan_type,
                target=target,
                requirements=requirements,
                language=language,
                additional_params=kwargs
            )
            
            # 执行代码
            result = await self.execute_code(
                code=code_response.code,
                language=language,
                target=target,
                **kwargs
            )
            
            return {
                "code_generation": code_response.to_dict(),
                "execution": result.to_dict(),
                "scan_type": scan_type,
                "target": target
            }
            
        except Exception as e:
            logger.error(f"❌ 生成并执行代码失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "scan_type": scan_type,
                "target": target
            }
    
    async def enhance_and_execute(
        self,
        requirement: str,
        target: str,
        capability_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        增强功能并执行
        
        Args:
            requirement: 功能需求
            target: 扫描目标
            capability_name: 能力名称(可选)
            
        Returns:
            Dict: 执行结果
        """
        try:
            logger.info(f"🔧 增强功能并执行: requirement={requirement}")
            
            # 增强功能
            enhance_result = await self.capability_enhancer.enhance_capability(
                requirement=requirement,
                target=target,
                capability_name=capability_name
            )
            
            if enhance_result.get("status") != "success":
                return {
                    "status": "failed",
                    "error": enhance_result.get("error"),
                    "requirement": requirement
                }
            
            # 执行能力
            capability_name = enhance_result["capability"]["name"]
            result = await self.capability_enhancer.execute_capability(
                name=capability_name,
                target=target
            )
            
            return {
                "enhancement": enhance_result,
                "execution": result,
                "requirement": requirement
            }
            
        except Exception as e:
            logger.error(f"❌ 增强功能并执行失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "requirement": requirement
            }
    
    def get_environment_info(self) -> Dict[str, Any]:
        """
        获取环境信息
        
        Returns:
            Dict: 环境信息
        """
        return self.env_awareness.get_environment_report()
    
    def list_capabilities(self) -> List[Dict[str, Any]]:
        """
        列出所有能力
        
        Returns:
            List[Dict]: 能力列表
        """
        return self.capability_enhancer.list_capabilities()
    

    


"""
Pocsuite3Agent 模块

提供基于 Pocsuite3 的 POC 执行代理功能。
支持自动选择和执行 POC，并返回详细的漏洞检测结果。

主要功能：
- POC 自动发现和加载
- 目标扫描和漏洞验证
- 结果解析和报告生成
- 与 AI Agent 集成
"""

import logging
import os
import tempfile
import sys
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class POCResult:
    """
    POC 执行结果
    
    Attributes:
        poc_name: POC 名称
        target: 扫描目标
        vulnerable: 是否存在漏洞
        message: 结果消息
        output: 完整输出
        error: 错误信息
        execution_time: 执行时间（秒）
    """
    poc_name: str
    target: str
    vulnerable: bool
    message: str
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class ScanResult:
    """
    扫描结果
    
    Attributes:
        target: 扫描目标
        total_pocs: 执行的 POC 总数
        vulnerable_count: 发现的漏洞数量
        results: POC 结果列表
        execution_time: 总执行时间（秒）
    """
    target: str
    total_pocs: int
    vulnerable_count: int
    results: List[POCResult] = field(default_factory=list)
    execution_time: float = 0.0


class Pocsuite3Agent:
    """
    Pocsuite3 代理类
    
    负责管理和执行 Pocsuite3 POC 脚本。
    """
    
    def __init__(self, pocsuite_path: Optional[str] = None):
        """
        初始化 Pocsuite3 代理
        
        Args:
            pocsuite_path: Pocsuite3 安装路径，如果为 None 则使用系统默认路径
        """
        self.pocsuite_path = pocsuite_path
        self.poc_registry: Dict[str, str] = {}
        self._check_pocsuite_installation()
        self._load_pocs()
        
    def _check_pocsuite_installation(self) -> bool:
        """
        检查 Pocsuite3 是否已安装
        
        Returns:
            bool: 是否已安装
        """
        try:
            import pocsuite3
            logger.info("Pocsuite3 已安装")
            return True
        except ImportError:
            logger.warning("Pocsuite3 未安装，部分功能将不可用")
            return False
    
    def _load_pocs(self):
        """
        加载可用的 POC 脚本
        
        从 Pocsuite3 的 POC 目录加载所有可用的 POC 脚本。
        """
        try:
            from pocsuite3.lib.core.data import paths
            
            poc_dir = paths.POCSUITE_ROOT_PATH
            if not poc_dir:
                logger.warning("无法找到 Pocsuite3 POC 目录")
                return
            
            # 扫描 POC 目录
            for root, dirs, files in os.walk(poc_dir):
                for file in files:
                    if file.endswith('.py') and not file.startswith('_'):
                        poc_path = os.path.join(root, file)
                        poc_name = file[:-3]  # 去掉 .py 后缀
                        
                        # 注册 POC
                        self.poc_registry[poc_name] = poc_path
            
            logger.info(f"加载了 {len(self.poc_registry)} 个 POC 脚本")
            
        except Exception as e:
            logger.error(f"加载 POC 脚本失败: {e}")
    
    async def execute_poc(self, poc_name: str, target: str, verify: bool = True) -> POCResult:
        """
        执行单个 POC
        
        Args:
            poc_name: POC 名称
            target: 目标 URL 或 IP
            verify: 是否仅验证（不攻击）
            
        Returns:
            POCResult: 执行结果
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"执行 POC: {poc_name}, 目标: {target}")
            
            # 构建 Pocsuite3 命令
            cmd = [
                sys.executable,
                "-m",
                "pocsuite3.cli",
                "-r",
                self.poc_registry.get(poc_name, poc_name),
                "-u",
                target
            ]
            
            if verify:
                cmd.append("--verify")
            else:
                cmd.append("--attack")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='ignore')
            error = stderr.decode('utf-8', errors='ignore')
            
            execution_time = time.time() - start_time
            
            # 解析结果
            vulnerable = self._parse_output(output)
            message = "Vulnerable" if vulnerable else "Not Vulnerable"
            
            result = POCResult(
                poc_name=poc_name,
                target=target,
                vulnerable=vulnerable,
                message=message,
                output=output,
                error=error if error else None,
                execution_time=execution_time
            )
            
            logger.info(f"POC 执行完成: {poc_name}, 结果: {message}, 耗时: {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"POC 执行失败: {poc_name}, 错误: {e}")
            
            return POCResult(
                poc_name=poc_name,
                target=target,
                vulnerable=False,
                message=f"Execution failed: {str(e)}",
                output="",
                error=str(e),
                execution_time=execution_time
            )
    
    def _parse_output(self, output: str) -> bool:
        """
        解析 Pocsuite3 输出，判断是否存在漏洞
        
        Args:
            output: Pocsuite3 输出内容
            
        Returns:
            bool: 是否存在漏洞
        """
        success_keywords = [
            "success",
            "vulnerable",
            "vuln",
            "exploit",
            "exists",
            "[+]",
            "vulnerable"
        ]
        
        output_lower = output.lower()
        
        for keyword in success_keywords:
            if keyword in output_lower:
                return True
        
        return False
    
    async def scan_target(
        self,
        target: str,
        poc_names: Optional[List[str]] = None,
        max_concurrent: int = 5
    ) -> ScanResult:
        """
        扫描目标，执行多个 POC
        
        Args:
            target: 目标 URL 或 IP
            poc_names: 要执行的 POC 名称列表，如果为 None 则执行所有 POC
            max_concurrent: 最大并发数
            
        Returns:
            ScanResult: 扫描结果
        """
        import time
        start_time = time.time()
        
        # 确定要执行的 POC 列表
        if poc_names is None:
            poc_names = list(self.poc_registry.keys())
        
        if not poc_names:
            logger.warning("没有可执行的 POC")
            return ScanResult(
                target=target,
                total_pocs=0,
                vulnerable_count=0,
                execution_time=0.0
            )
        
        logger.info(f"开始扫描目标: {target}, POC 数量: {len(poc_names)}")
        
        # 限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(poc_name: str) -> POCResult:
            async with semaphore:
                return await self.execute_poc(poc_name, target)
        
        # 并发执行所有 POC
        results = await asyncio.gather(
            *[execute_with_semaphore(poc_name) for poc_name in poc_names],
            return_exceptions=True
        )
        
        # 处理结果
        valid_results = []
        vulnerable_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"POC 执行异常: {result}")
                continue
            
            if isinstance(result, POCResult):
                valid_results.append(result)
                if result.vulnerable:
                    vulnerable_count += 1
        
        execution_time = time.time() - start_time
        
        scan_result = ScanResult(
            target=target,
            total_pocs=len(valid_results),
            vulnerable_count=vulnerable_count,
            results=valid_results,
            execution_time=execution_time
        )
        
        logger.info(
            f"扫描完成: {target}, "
            f"总 POC: {len(valid_results)}, "
            f"发现漏洞: {vulnerable_count}, "
            f"耗时: {execution_time:.2f}s"
        )
        
        return scan_result
    
    async def execute_custom_poc(
        self,
        poc_code: str,
        target: str,
        verify: bool = True
    ) -> POCResult:
        """
        执行自定义 POC 代码
        
        Args:
            poc_code: POC 代码字符串
            target: 目标 URL 或 IP
            verify: 是否仅验证（不攻击）
            
        Returns:
            POCResult: 执行结果
        """
        import time
        start_time = time.time()
        tmp_path = None
        
        try:
            # 写入临时文件
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as tmp:
                tmp.write(poc_code)
                tmp_path = tmp.name
            
            logger.info(f"执行自定义 POC, 目标: {target}")
            
            # 构建命令
            cmd = [
                sys.executable,
                "-m",
                "pocsuite3.cli",
                "-r",
                tmp_path,
                "-u",
                target
            ]
            
            if verify:
                cmd.append("--verify")
            else:
                cmd.append("--attack")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='ignore')
            error = stderr.decode('utf-8', errors='ignore')
            
            execution_time = time.time() - start_time
            
            # 解析结果
            vulnerable = self._parse_output(output)
            message = "Vulnerable" if vulnerable else "Not Vulnerable"
            
            result = POCResult(
                poc_name="custom_poc",
                target=target,
                vulnerable=vulnerable,
                message=message,
                output=output,
                error=error if error else None,
                execution_time=execution_time
            )
            
            logger.info(f"自定义 POC 执行完成, 结果: {message}, 耗时: {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"自定义 POC 执行失败: {e}")
            
            return POCResult(
                poc_name="custom_poc",
                target=target,
                vulnerable=False,
                message=f"Execution failed: {str(e)}",
                output="",
                error=str(e),
                execution_time=execution_time
            )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def get_available_pocs(self) -> List[str]:
        """
        获取所有可用的 POC 列表
        
        Returns:
            List[str]: POC 名称列表
        """
        return list(self.poc_registry.keys())
    
    def search_pocs(self, keyword: str) -> List[str]:
        """
        搜索 POC
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[str]: 匹配的 POC 名称列表
        """
        keyword_lower = keyword.lower()
        return [
            poc_name for poc_name in self.poc_registry.keys()
            if keyword_lower in poc_name.lower()
        ]


# 全局实例
_pocsuite3_agent_instance: Optional[Pocsuite3Agent] = None


def get_pocsuite3_agent() -> Pocsuite3Agent:
    """
    获取 Pocsuite3 代理实例（单例模式）
    
    Returns:
        Pocsuite3Agent: 代理实例
    """
    global _pocsuite3_agent_instance
    
    if _pocsuite3_agent_instance is None:
        _pocsuite3_agent_instance = Pocsuite3Agent()
    
    return _pocsuite3_agent_instance

"""
POC执行机制优化 - Seebug API和pocsuite3集成
"""
import asyncio
import logging
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.Pocsuite3Agent.agent import (
    Pocsuite3Agent,
    POCResult,
    ScanResult,
    get_pocsuite3_agent
)

logger = logging.getLogger(__name__)


@dataclass
class SeebugPOCInfo:
    """Seebug POC信息"""
    cve_id: str
    title: str
    description: str
    severity: str
    poc_download_url: Optional[str] = None
    poc_content: Optional[str] = None
    published_date: Optional[str] = None
    references: List[str] = field(default_factory=list)


@dataclass
class POCExecutionResult:
    """POC执行结果"""
    cve_id: str
    target: str
    success: bool
    vulnerable: bool = False
    poc_name: Optional[str] = None
    execution_time: float = 0.0
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class POCIntegrationManager:
    """
    POC集成管理器
    
    整合Seebug API和pocsuite3工具，提供统一的POC管理和执行接口。
    """
    
    def __init__(self):
        self.pocsuite_agent: Optional[Pocsuite3Agent] = None
        self._seebug_api_key: Optional[str] = None
        self._seebug_api_base: Optional[str] = None
        self._poc_cache_dir: Path = Path(__file__).parent / "poc_cache"
        self._poc_cache_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            from backend.config import settings
            self._seebug_api_key = getattr(settings, 'SEebug_API_KEY', None)
            self._seebug_api_base = getattr(settings, 'SEebug_API_BASE_URL', 'https://www.seebug.org')
        except Exception as e:
            logger.warning(f"无法加载Seebug配置: {str(e)}")
    
    def initialize(self) -> bool:
        """
        初始化POC集成管理器
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.pocsuite_agent = get_pocsuite3_agent()
            logger.info("✅ POC集成管理器初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ POC集成管理器初始化失败: {str(e)}")
            return False
    
    async def search_poc_by_cve(self, cve_id: str) -> List[SeebugPOCInfo]:
        """
        通过CVE编号搜索POC
        
        Args:
            cve_id: CVE编号
            
        Returns:
            List[SeebugPOCInfo]: POC信息列表
        """
        logger.info(f"🔍 搜索CVE: {cve_id}")
        
        try:
            if self._seebug_api_key:
                return await self._search_seebug_api(cve_id)
            else:
                logger.warning("未配置Seebug API，使用本地POC库")
                return await self._search_local_poc(cve_id)
                
        except Exception as e:
            logger.error(f"❌ 搜索POC失败: {str(e)}")
            return []
    
    async def _search_seebug_api(self, cve_id: str) -> List[SeebugPOCInfo]:
        """
        通过Seebug API搜索POC
        
        Args:
            cve_id: CVE编号
            
        Returns:
            List[SeebugPOCInfo]: POC信息列表
        """
        try:
            import httpx
            
            headers = {
                "Authorization": f"Token {self._seebug_api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self._seebug_api_base}/api/v1/vulnerabilities/search",
                    params={"q": cve_id},
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("results", []):
                        poc_info = SeebugPOCInfo(
                            cve_id=cve_id,
                            title=item.get("title", ""),
                            description=item.get("description", ""),
                            severity=item.get("severity", "medium"),
                            poc_download_url=item.get("poc_url"),
                            published_date=item.get("published_date")
                        )
                        results.append(poc_info)
                    
                    logger.info(f"✅ 从Seebug找到 {len(results)} 个POC")
                    return results
                else:
                    logger.warning(f"Seebug API返回错误: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Seebug API调用失败: {str(e)}")
            return []
    
    async def _search_local_poc(self, cve_id: str) -> List[SeebugPOCInfo]:
        """
        搜索本地POC库
        
        Args:
            cve_id: CVE编号
            
        Returns:
            List[SeebugPOCInfo]: POC信息列表
        """
        results = []
        
        try:
            from backend.ai_agents.tools.adapters import POCAdapter
            
            all_pocs = POCAdapter.get_all_pocs()
            
            cve_keywords = cve_id.lower().replace("-", "_")
            
            for poc_name, poc_module in all_pocs.items():
                poc_name_lower = poc_name.lower()
                
                if cve_keywords in poc_name_lower or cve_id.lower() in poc_name_lower:
                    poc_info = SeebugPOCInfo(
                        cve_id=cve_id,
                        title=f"本地POC: {poc_name}",
                        description=f"本地库中的POC - {poc_name}",
                        severity="high",
                        poc_name=poc_name
                    )
                    results.append(poc_info)
            
            logger.info(f"✅ 从本地POC库找到 {len(results)} 个POC")
            
        except Exception as e:
            logger.error(f"搜索本地POC失败: {str(e)}")
        
        return results
    
    async def download_poc(self, poc_info: SeebugPOCInfo) -> Optional[str]:
        """
        下载POC
        
        Args:
            poc_info: POC信息
            
        Returns:
            Optional[str]: 下载的POC文件路径
        """
        try:
            if poc_info.poc_content:
                file_path = self._poc_cache_dir / f"{poc_info.cve_id}_{int(time.time())}.py"
                file_path.write_text(poc_info.poc_content, encoding='utf-8')
                logger.info(f"✅ POC已保存: {file_path}")
                return str(file_path)
            
            elif poc_info.poc_download_url and self._seebug_api_key:
                import httpx
                
                headers = {
                    "Authorization": f"Token {self._seebug_api_key}"
                }
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(
                        poc_info.poc_download_url,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        file_path = self._poc_cache_dir / f"{poc_info.cve_id}_{int(time.time())}.py"
                        file_path.write_text(response.text, encoding='utf-8')
                        logger.info(f"✅ POC已下载: {file_path}")
                        return str(file_path)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 下载POC失败: {str(e)}")
            return None
    
    async def execute_poc(
        self,
        target: str,
        cve_id: Optional[str] = None,
        poc_name: Optional[str] = None,
        poc_file_path: Optional[str] = None,
        timeout: float = 300.0
    ) -> POCExecutionResult:
        """
        执行POC检测
        
        Args:
            target: 目标URL
            cve_id: CVE编号（可选）
            poc_name: 本地POC名称（可选）
            poc_file_path: POC文件路径（可选）
            timeout: 超时时间
            
        Returns:
            POCExecutionResult: 执行结果
        """
        start_time = time.time()
        logger.info(f"🚀 开始POC检测: 目标={target}, CVE={cve_id}, POC={poc_name}")
        
        result = POCExecutionResult(
            cve_id=cve_id or "unknown",
            target=target,
            success=False
        )
        
        try:
            if not self.pocsuite_agent:
                if not self.initialize():
                    result.error = "POC集成管理器初始化失败"
                    return result
            
            if poc_name:
                poc_result = await self._execute_local_poc(target, poc_name, timeout)
            elif poc_file_path:
                poc_result = await self._execute_poc_file(target, poc_file_path, timeout)
            elif cve_id:
                poc_result = await self._execute_cve_poc(target, cve_id, timeout)
            else:
                result.error = "必须提供cve_id、poc_name或poc_file_path之一"
                return result
            
            result.success = poc_result.success if hasattr(poc_result, 'success') else True
            result.vulnerable = poc_result.vulnerable if hasattr(poc_result, 'vulnerable') else False
            result.poc_name = poc_name or cve_id
            result.details = {
                "poc_result": poc_result.__dict__ if hasattr(poc_result, '__dict__') else str(poc_result)
            }
            
            logger.info(
                f"✅ POC检测完成: 目标={target}, "
                f"成功={result.success}, "
                f"有漏洞={result.vulnerable}"
            )
            
        except Exception as e:
            logger.error(f"❌ POC检测异常: {str(e)}")
            result.error = str(e)
        
        result.execution_time = time.time() - start_time
        return result
    
    async def _execute_local_poc(
        self,
        target: str,
        poc_name: str,
        timeout: float
    ) -> Any:
        """
        执行本地POC
        
        Args:
            target: 目标URL
            poc_name: POC名称
            timeout: 超时时间
            
        Returns:
            Any: 执行结果
        """
        try:
            from backend.ai_agents.tools.adapters import POCAdapter
            
            poc_result = await POCAdapter.adapt_poc(
                target=target,
                poc_name=poc_name,
                timeout=timeout
            )
            
            return poc_result
            
        except Exception as e:
            logger.error(f"执行本地POC失败: {str(e)}")
            raise
    
    async def _execute_poc_file(
        self,
        target: str,
        poc_file_path: str,
        timeout: float
    ) -> Any:
        """
        执行POC文件
        
        Args:
            target: 目标URL
            poc_file_path: POC文件路径
            timeout: 超时时间
            
        Returns:
            Any: 执行结果
        """
        try:
            if not self.pocsuite_agent:
                raise RuntimeError("Pocsuite3Agent未初始化")
            
            scan_result = await self.pocsuite_agent.execute_custom_poc(
                target=target,
                poc_file=poc_file_path
            )
            
            return scan_result
            
        except Exception as e:
            logger.error(f"执行POC文件失败: {str(e)}")
            raise
    
    async def _execute_cve_poc(
        self,
        target: str,
        cve_id: str,
        timeout: float
    ) -> Any:
        """
        执行CVE对应的POC
        
        Args:
            target: 目标URL
            cve_id: CVE编号
            timeout: 超时时间
            
        Returns:
            Any: 执行结果
        """
        poc_infos = await self.search_poc_by_cve(cve_id)
        
        if not poc_infos:
            raise RuntimeError(f"未找到CVE {cve_id} 对应的POC")
        
        for poc_info in poc_infos:
            try:
                if poc_info.poc_name:
                    return await self._execute_local_poc(target, poc_info.poc_name, timeout)
                
                poc_file = await self.download_poc(poc_info)
                if poc_file:
                    return await self._execute_poc_file(target, poc_file, timeout)
                    
            except Exception as e:
                logger.warning(f"POC {poc_info.title} 执行失败: {str(e)}")
                continue
        
        raise RuntimeError(f"所有POC都执行失败: {cve_id}")
    
    async def batch_execute_poc(
        self,
        targets: List[str],
        cve_ids: List[str]
    ) -> List[POCExecutionResult]:
        """
        批量执行POC检测
        
        Args:
            targets: 目标列表
            cve_ids: CVE编号列表
            
        Returns:
            List[POCExecutionResult]: 执行结果列表
        """
        results = []
        
        for target in targets:
            for cve_id in cve_ids:
                result = await self.execute_poc(
                    target=target,
                    cve_id=cve_id
                )
                results.append(result)
        
        return results
    
    def get_cached_pocs(self) -> List[str]:
        """
        获取缓存的POC列表
        
        Returns:
            List[str]: POC文件路径列表
        """
        return [str(p) for p in self._poc_cache_dir.glob("*.py")]
    
    def clear_cache(self):
        """清空POC缓存"""
        for poc_file in self._poc_cache_dir.glob("*.py"):
            try:
                poc_file.unlink()
            except Exception as e:
                logger.warning(f"删除缓存文件失败: {poc_file}, 错误: {str(e)}")
        
        logger.info("✅ POC缓存已清空")


_poc_manager = None


def get_poc_integration_manager() -> POCIntegrationManager:
    """
    获取POC集成管理器单例
    
    Returns:
        POCIntegrationManager: POC集成管理器实例
    """
    global _poc_manager
    if _poc_manager is None:
        _poc_manager = POCIntegrationManager()
        _poc_manager.initialize()
    return _poc_manager

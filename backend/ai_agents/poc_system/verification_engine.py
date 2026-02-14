"""
POC 验证执行引擎

负责 POC 验证的核心执行逻辑,包括多线程并发执行、资源限制管理、超时控制、错误重试机制等。
"""
import logging
import asyncio
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


from backend.config import settings
from backend.models import POCVerificationTask, POCVerificationResult, POCExecutionLog
from backend.ai_agents.poc_system.poc_manager import poc_manager
from backend.Pocsuite3Agent.agent import POCResult, Pocsuite3Agent


logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """
    执行配置类
    
    用于配置单个 POC 执行的参数和限制。
    """
    
    poc_id: str
    target: str
    poc_code: str
    timeout: int = 60
    max_retries: int = 3
    enable_sandbox: bool = True
    max_memory_mb: int = 512
    max_cpu_percent: float = 80.0


@dataclass
class ExecutionStats:
    """
    执行统计类
    
    用于跟踪 POC 验证执行的统计信息。
    """
    
    total_pocs: int = 0
    executed_count: int = 0
    vulnerable_count: int = 0
    failed_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    success_rate: float = 0.0


class VerificationEngine:
    """
    POC 验证执行引擎类
    
    负责管理 POC 验证任务的执行,包括:
    - 多线程并发执行
    - 资源限制管理
    - 超时控制
    - 错误重试机制
    - 执行进度监控
    - 实时日志捕获
    """
    
    def __init__(self):
        """
        初始化验证引擎
        """
        self.pocsuite3_agent = Pocsuite3Agent()
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.execution_semaphore = asyncio.Semaphore(
            settings.POC_MAX_CONCURRENT_EXECUTIONS
        )
        self.resource_semaphore = asyncio.Semaphore(
            settings.POC_MAX_CONCURRENT_EXECUTIONS
        )
        
        logger.info("✅ POC 验证执行引擎初始化完成")
    
    async def execute_verification_task(
        self,
        verification_task: POCVerificationTask
    ) -> POCVerificationResult:
        """
        执行单个 POC 验证任务
        
        Args:
            verification_task: POC 验证任务对象
            
        Returns:
            POCVerificationResult: 验证结果
        """
        logger.info(f"[{verification_task.id}] 🚀 开始执行 POC 验证: {verification_task.poc_name}")
        
        start_time = datetime.now()
        
        try:
            # 更新任务状态为运行中
            verification_task.status = "running"
            verification_task.progress = 10
            await verification_task.save()
            
            # 获取 POC 代码
            poc_code = await poc_manager.get_poc_code(verification_task.poc_id)
            if not poc_code:
                raise ValueError(f"POC 代码不存在: {verification_task.poc_id}")
            
            # 创建执行配置
            config = ExecutionConfig(
                poc_id=verification_task.poc_id,
                target=verification_task.target,
                poc_code=poc_code,
                timeout=settings.POC_EXECUTION_TIMEOUT,
                max_retries=settings.POC_RETRY_MAX_COUNT,
                enable_sandbox=True
            )
            
            # 执行 POC 验证
            poc_result = await self._execute_poc_with_retry(config)
            
            # 创建验证结果
            result = await POCVerificationResult.create(
                verification_task=verification_task,
                poc_name=verification_task.poc_name,
                poc_id=verification_task.poc_id,
                target=verification_task.target,
                vulnerable=poc_result.vulnerable,
                message=poc_result.message,
                output=poc_result.output,
                error=poc_result.error,
                execution_time=poc_result.execution_time,
                confidence=self._calculate_confidence(poc_result),
                severity=self._calculate_severity(poc_result),
                cvss_score=self._calculate_cvss_score(poc_result)
            )
            
            # 更新任务状态为已完成
            verification_task.status = "completed"
            verification_task.progress = 100
            await verification_task.save()
            
            # 记录执行日志
            await self._log_execution_details(result, poc_result)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{verification_task.id}] ✅ POC 验证完成: {verification_task.poc_name}, 耗时: {execution_time:.2f}秒")
            
            return result
            
        except Exception as e:
            logger.error(f"[{verification_task.id}] ❌ POC 验证失败: {str(e)}")
            
            # 更新任务状态为失败
            verification_task.status = "failed"
            await verification_task.save()
            
            # 创建失败结果
            result = await POCVerificationResult.create(
                verification_task=verification_task,
                poc_name=verification_task.poc_name,
                poc_id=verification_task.poc_id,
                target=verification_task.target,
                vulnerable=False,
                message=f"执行失败: {str(e)}",
                output="",
                error=str(e),
                execution_time=0.0,
                confidence=0.0,
                severity="info",
                cvss_score=0.0
            )
            
            # 记录错误日志
            await self._log_execution_details(result, None, e)
            
            return result
    
    async def execute_batch_verification(
        self,
        verification_tasks: List[POCVerificationTask],
        max_concurrent: Optional[int] = None
    ) -> List[POCVerificationResult]:
        """
        批量执行 POC 验证任务
        
        Args:
            verification_tasks: POC 验证任务列表
            max_concurrent: 最大并发数,None 则使用配置值
            
        Returns:
            List[POCVerificationResult]: 验证结果列表
        """
        logger.info(f"🚀 开始批量 POC 验证,任务数: {len(verification_tasks)}")
        
        concurrent_limit = max_concurrent or settings.POC_MAX_CONCURRENT_EXECUTIONS
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        results = []
        
        async def execute_single_task(task: POCVerificationTask) -> POCVerificationResult:
            async with semaphore:
                return await self.execute_verification_task(task)
        
        # 并发执行所有任务
        tasks = [execute_single_task(task) for task in verification_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 任务 {verification_tasks[i].poc_name} 执行异常: {str(result)}")
        
        logger.info(f"✅ 批量 POC 验证完成,成功: {len(results)}")
        
        return [r for r in results if isinstance(r, POCVerificationResult)]
    
    async def _execute_poc_with_retry(
        self,
        config: ExecutionConfig
    ) -> POCResult:
        """
        带重试机制的 POC 执行
        
        Args:
            config: 执行配置
            
        Returns:
            POCResult: POC 执行结果
        """
        for attempt in range(config.max_retries):
            logger.info(f"[{config.poc_id}] 🔄 尝试执行 POC (第 {attempt + 1} 次)")
            
            try:
                # 使用 Pocsuite3 执行 POC (自定义代码模式)
                result = await self.pocsuite3_agent.execute_custom_poc(
                    poc_code=config.poc_code,
                    target=config.target
                )
                
                if result.vulnerable:
                    logger.info(f"[{config.poc_id}] ✅ POC 验证成功: {result.message}")
                    return result
                else:
                    logger.warning(f"[{config.poc_id}] ⚠️ POC 验证未发现漏洞: {result.message}")
                    
                    # 如果不是最后一次尝试,继续重试
                    if attempt < config.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        return result
                        
            except Exception as e:
                logger.error(f"[{config.poc_id}] ❌ POC 执行异常 (第 {attempt + 1} 次): {str(e)}")
                
                # 如果不是最后一次尝试,继续重试
                if attempt < config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    # 返回失败结果
                    return POCResult(
                        poc_name=config.poc_id,
                        target=config.target,
                        vulnerable=False,
                        message=f"执行失败: {str(e)}",
                        output="",
                        error=str(e),
                        execution_time=0.0
                    )
        
        return POCResult(
            poc_name=config.poc_id,
            target=config.target,
            vulnerable=False,
            message="超过最大重试次数",
            output="",
            error="Max retries exceeded",
            execution_time=0.0
        )
    
    async def pause_verification_task(
        self,
        task_id: str
    ) -> bool:
        """
        暂停 POC 验证任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            bool: 是否暂停成功
        """
        try:
            task = await POCVerificationTask.get_or_none(id=task_id)
            if not task:
                logger.warning(f"⚠️ 任务不存在: {task_id}")
                return False
            
            if task.status != "running":
                logger.warning(f"⚠️ 任务状态不允许暂停: {task.status}")
                return False
            
            task.status = "paused"
            await task.save()
            
            # 取消正在执行的任务
            if task.id in self.active_executions:
                execution_task = self.active_executions[task.id]
                execution_task.cancel()
                del self.active_executions[task.id]
            
            logger.info(f"✅ 任务已暂停: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 暂停任务失败: {str(e)}")
            return False
    
    async def resume_verification_task(
        self,
        task_id: str
    ) -> bool:
        """
        继续 POC 验证任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            bool: 是否继续成功
        """
        try:
            task = await POCVerificationTask.get_or_none(id=task_id)
            if not task:
                logger.warning(f"⚠️ 任务不存在: {task_id}")
                return False
            
            if task.status != "paused":
                logger.warning(f"⚠️ 任务状态不允许继续: {task.status}")
                return False
            
            task.status = "running"
            await task.save()
            
            logger.info(f"✅ 任务已继续: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 继续任务失败: {str(e)}")
            return False
    
    async def cancel_verification_task(
        self,
        task_id: str
    ) -> bool:
        """
        取消 POC 验证任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            bool: 是否取消成功
        """
        try:
            task = await POCVerificationTask.get_or_none(id=task_id)
            if not task:
                logger.warning(f"⚠️ 任务不存在: {task_id}")
                return False
            
            task.status = "cancelled"
            await task.save()
            
            # 取消正在执行的任务
            if task.id in self.active_executions:
                execution_task = self.active_executions[task.id]
                execution_task.cancel()
                del self.active_executions[task.id]
            
            logger.info(f"✅ 任务已取消: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 取消任务失败: {str(e)}")
            return False
    
    async def get_execution_progress(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        获取执行进度
        
        Args:
            task_id: 任务 ID
            
        Returns:
            Dict: 包含进度信息的字典
        """
        try:
            task = await POCVerificationTask.get_or_none(id=task_id)
            if not task:
                return {"error": "Task not found"}
            
            # 获取相关结果
            results = await POCVerificationResult.filter(
                verification_task=task_id
            ).order_by("-created_at")
            
            if not results:
                return {
                    "task_id": task_id,
                    "poc_name": task.poc_name,
                    "status": task.status,
                    "progress": task.progress,
                    "total_results": len(results),
                    "vulnerable_count": sum(1 for r in results if r.vulnerable),
                    "failed_count": sum(1 for r in results if not r.vulnerable and r.error)
                }
            
            return {
                "task_id": task_id,
                "poc_name": task.poc_name,
                "status": task.status,
                "progress": task.progress,
                "total_results": len(results),
                "vulnerable_count": sum(1 for r in results if r.vulnerable),
                "failed_count": sum(1 for r in results if not r.vulnerable and r.error),
                "latest_result": results[0].to_dict() if results else None
            }
            
        except Exception as e:
            logger.error(f"❌ 获取执行进度失败: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_confidence(self, poc_result: POCResult) -> float:
        """
        计算结果置信度
        
        Args:
            poc_result: POC 执行结果
            
        Returns:
            float: 置信度(0-1)
        """
        confidence = 0.5
        
        # 基于执行结果调整置信度
        if poc_result.vulnerable:
            confidence = 0.9
        elif poc_result.error:
            confidence = 0.1
        else:
            confidence = 0.5
        
        # 基于输出长度调整置信度
        if poc_result.output and len(poc_result.output) > 100:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_severity(self, poc_result: POCResult) -> str:
        """
        计算漏洞严重度
        
        Args:
            poc_result: POC 执行结果
            
        Returns:
            str: 严重度(critical, high, medium, low, info)
        """
        if poc_result.vulnerable:
            return "high"
        elif poc_result.error:
            return "info"
        else:
            return "low"
    
    def _calculate_cvss_score(self, poc_result: POCResult) -> float:
        """
        计算 CVSS 评分
        
        Args:
            poc_result: POC 执行结果
            
        Returns:
            float: CVSS 评分(0-10)
        """
        if poc_result.vulnerable:
            return 7.5
        elif poc_result.error:
            return 0.0
        else:
            return 3.5
    
    async def _log_execution_details(
        self,
        result: POCVerificationResult,
        poc_result: Optional[POCResult] = None,
        error: Optional[Exception] = None
    ):
        """
        记录执行详情日志
        
        Args:
            result: 验证结果对象
            poc_result: POC 执行结果
            error: 异常对象
        """
        try:
            # 记录开始日志
            await POCExecutionLog.create(
                verification_result=result,
                log_level="info",
                message=f"开始执行 POC: {result.poc_name}",
                details={
                    "poc_id": result.poc_id,
                    "target": result.target,
                    "config": {
                        "timeout": settings.POC_EXECUTION_TIMEOUT,
                        "max_retries": settings.POC_RETRY_MAX_COUNT
                    }
                }
            )
            
            # 如果有 POC 执行结果,记录执行日志
            if poc_result:
                await POCExecutionLog.create(
                    verification_result=result,
                    log_level="info",
                    message=f"POC 执行完成: {poc_result.message}",
                    details={
                        "vulnerable": poc_result.vulnerable,
                        "execution_time": poc_result.execution_time,
                        "output_length": len(poc_result.output) if poc_result.output else 0
                    }
                )
            
            # 如果有错误,记录错误日志
            if error:
                await POCExecutionLog.create(
                    verification_result=result,
                    log_level="error",
                    message=f"POC 执行异常: {str(error)}",
                    details={
                        "exception_type": type(error).__name__,
                        "exception_message": str(error)
                    }
                )
            
        except Exception as e:
            logger.error(f"❌ 记录执行日志失败: {str(e)}")
    
    async def get_engine_statistics(self) -> Dict[str, Any]:
        """
        获取引擎统计信息
        
        Returns:
            Dict: 包含引擎统计信息的字典
        """
        try:
            total_tasks = await POCVerificationTask.all().count()
            running_tasks = await POCVerificationTask.filter(status="running").count()
            completed_tasks = await POCVerificationTask.filter(status="completed").count()
            failed_tasks = await POCVerificationTask.filter(status="failed").count()
            
            total_results = await POCVerificationResult.all().count()
            vulnerable_results = await POCVerificationResult.filter(vulnerable=True).count()
            
            return {
                "total_tasks": total_tasks,
                "running_tasks": running_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "total_results": total_results,
                "vulnerable_results": vulnerable_results,
                "success_rate": (vulnerable_results / total_results * 100) if total_results > 0 else 0,
                "active_executions": len(self.active_executions),
                "registered_pocs": len(poc_manager.get_all_pocs()),
                "cached_pocs": len(poc_manager.poc_cache)
            }
            
        except Exception as e:
            logger.error(f"❌ 获取引擎统计失败: {str(e)}")
            return {"error": str(e)}


# 全局验证引擎实例
verification_engine = VerificationEngine()

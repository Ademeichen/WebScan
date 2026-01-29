"""
POC 验证节点

基于 LangGraph 框架的 POC 验证节点，实现 agent 驱动的 POC 验证流程。
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph

from backend.ai_agents.core.state import AgentState
from backend.ai_agents.poc_system import (
    poc_manager,
    target_manager,
    verification_engine,
    result_analyzer,
    report_generator
)
from backend.models import POCVerificationTask, POCVerificationResult
from backend.config import settings

logger = logging.getLogger(__name__)


class POCVerificationNode:
    """
    POC 验证节点类
    
    基于 LangGraph 框架的专用 POC 验证节点，实现：
    - agent 驱动的 POC 验证流程
    - 节点状态管理（创建、执行、暂停、结果返回）
    - 与代码执行节点的无缝集成
    - 标准化数据交互格式
    """
    
    def __init__(self):
        """
        初始化 POC 验证节点
        """
        self.node_name = "poc_verification"
        self.description = "POC 验证节点，负责执行 POC 验证任务"
        
        logger.info("✅ POC 验证节点初始化完成")
    
    async def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        节点调用方法
        
        这是 LangGraph 节点的标准接口，接收 AgentState 并返回更新后的状态。
        
        Args:
            state: 当前智能体状态
            
        Returns:
            Dict[str, Any]: 更新后的状态字段
        """
        logger.info(f"[{self.node_name}] 🚀 开始执行 POC 验证节点")
        
        try:
            # 检查 POC 验证是否启用
            if not settings.POC_VERIFICATION_ENABLED:
                logger.warning(f"[{self.node_name}] ⚠️ POC 验证功能已禁用")
                return {
                    "poc_verification_status": "disabled",
                    "poc_verification_results": [],
                    "poc_execution_stats": {}
                }
            
            # 从状态中获取待验证的 POC 任务
            poc_tasks = state.poc_verification_tasks
            
            if not poc_tasks:
                logger.info(f"[{self.node_name}] ℹ️ 没有待验证的 POC 任务")
                return {
                    "poc_verification_status": "completed",
                    "poc_verification_results": [],
                    "poc_execution_stats": {}
                }
            
            # 更新验证状态为运行中
            logger.info(f"[{self.node_name}] 📋 待验证 POC 任务数: {len(poc_tasks)}")
            
            # 执行 POC 验证
            verification_results = await self._execute_poc_verification(
                poc_tasks,
                state
            )
            
            # 分析验证结果
            analysis_results = await self._analyze_verification_results(
                verification_results
            )
            
            # 更新状态
            updated_state = {
                "poc_verification_status": "completed",
                "poc_verification_results": verification_results,
                "poc_execution_stats": self._calculate_execution_stats(
                    verification_results
                ),
                "vulnerabilities": self._update_vulnerabilities(
                    state.vulnerabilities,
                    verification_results
                ),
                "tool_results": state.tool_results + [
                    {
                        "tool": self.node_name,
                        "result": {
                            "status": "completed",
                            "verified_count": len(verification_results),
                            "vulnerable_count": sum(
                                1 for r in verification_results if r.get("vulnerable")
                            ),
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                ]
            }
            
            logger.info(f"[{self.node_name}] ✅ POC 验证节点执行完成")
            return updated_state
            
        except Exception as e:
            logger.error(f"[{self.node_name}] ❌ POC 验证节点执行失败: {str(e)}")
            
            # 更新状态为失败
            return {
                "poc_verification_status": "failed",
                "poc_verification_results": [],
                "poc_execution_stats": {
                    "error": str(e)
                },
                "errors": state.errors + [
                    {
                        "node": self.node_name,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
    
    async def _execute_poc_verification(
        self,
        poc_tasks: List[Dict[str, Any]],
        state: AgentState
    ) -> List[Dict[str, Any]]:
        """
        执行 POC 验证
        
        Args:
            poc_tasks: POC 任务列表
            state: 当前智能体状态
            
        Returns:
            List[Dict]: 验证结果列表
        """
        logger.info(f"[{self.node_name}] 🔄 开始执行 POC 验证")
        
        verification_results = []
        
        # 从智能体状态获取目标信息
        target = state.target
        
        # 为每个 POC 任务创建验证任务并执行
        for poc_task in poc_tasks:
            try:
                # 创建 POC 验证任务
                verification_task = await poc_manager.create_verification_task(
                    poc_id=poc_task.get("poc_id"),
                    target=target,
                    priority=poc_task.get("priority", 5),
                    task_id=state.task_id
                )
                
                # 执行验证
                result = await verification_engine.execute_verification_task(
                    verification_task
                )
                
                # 转换为字典格式
                result_dict = {
                    "poc_name": result.poc_name,
                    "poc_id": result.poc_id,
                    "target": result.target,
                    "vulnerable": result.vulnerable,
                    "message": result.message,
                    "output": result.output,
                    "error": result.error,
                    "execution_time": result.execution_time,
                    "confidence": result.confidence,
                    "severity": result.severity,
                    "cvss_score": result.cvss_score,
                    "created_at": result.created_at.isoformat()
                }
                
                verification_results.append(result_dict)
                
                logger.info(
                    f"[{self.node_name}] ✅ POC 验证完成: "
                    f"{result.poc_name} -> {result.vulnerable}"
                )
                
            except Exception as e:
                logger.error(
                    f"[{self.node_name}] ❌ POC 验证失败: "
                    f"{poc_task.get('poc_name', 'unknown')} - {str(e)}"
                )
                
                # 添加失败结果
                verification_results.append({
                    "poc_name": poc_task.get("poc_name", "unknown"),
                    "poc_id": poc_task.get("poc_id", ""),
                    "target": target,
                    "vulnerable": False,
                    "message": f"验证失败: {str(e)}",
                    "output": "",
                    "error": str(e),
                    "execution_time": 0.0,
                    "confidence": 0.0,
                    "severity": "info",
                    "cvss_score": 0.0,
                    "created_at": datetime.now().isoformat()
                })
        
        return verification_results
    
    async def _analyze_verification_results(
        self,
        verification_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析验证结果
        
        Args:
            verification_results: 验证结果列表
            
        Returns:
            Dict: 分析结果
        """
        logger.info(f"[{self.node_name}] 🔍 开始分析验证结果")
        
        # 转换为 POCVerificationResult 对象
        result_objects = []
        for result_dict in verification_results:
            result = POCVerificationResult(
                id=result_dict.get("id", 0),
                poc_name=result_dict.get("poc_name", ""),
                poc_id=result_dict.get("poc_id", ""),
                target=result_dict.get("target", ""),
                vulnerable=result_dict.get("vulnerable", False),
                message=result_dict.get("message", ""),
                output=result_dict.get("output"),
                error=result_dict.get("error"),
                execution_time=result_dict.get("execution_time", 0.0),
                confidence=result_dict.get("confidence", 0.0),
                severity=result_dict.get("severity"),
                cvss_score=result_dict.get("cvss_score"),
                created_at=datetime.now()
            )
            result_objects.append(result)
        
        # 批量分析
        analysis_summary = await result_analyzer.analyze_batch_results(
            result_objects
        )
        
        logger.info(
            f"[{self.node_name}] ✅ 验证结果分析完成: "
            f"漏洞 {analysis_summary.vulnerable_count}/{analysis_summary.total_results}"
        )
        
        return {
            "total_results": analysis_summary.total_results,
            "vulnerable_count": analysis_summary.vulnerable_count,
            "not_vulnerable_count": analysis_summary.not_vulnerable_count,
            "false_positive_count": analysis_summary.false_positive_count,
            "true_positive_count": analysis_summary.true_positive_count,
            "severity_distribution": analysis_summary.severity_distribution,
            "average_confidence": analysis_summary.average_confidence,
            "average_cvss_score": analysis_summary.average_cvss_score,
            "high_risk_targets": analysis_summary.high_risk_targets,
            "recommendations": analysis_summary.recommendations
        }
    
    def _calculate_execution_stats(
        self,
        verification_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        计算执行统计信息
        
        Args:
            verification_results: 验证结果列表
            
        Returns:
            Dict: 执行统计信息
        """
        total_pocs = len(verification_results)
        executed_count = total_pocs
        vulnerable_count = sum(
            1 for r in verification_results if r.get("vulnerable")
        )
        failed_count = sum(
            1 for r in verification_results if r.get("error")
        )
        
        total_execution_time = sum(
            r.get("execution_time", 0.0) for r in verification_results
        )
        average_execution_time = (
            total_execution_time / executed_count if executed_count > 0 else 0.0
        )
        success_rate = (
            (executed_count - failed_count) / executed_count * 100
            if executed_count > 0 else 0.0
        )
        
        return {
            "total_pocs": total_pocs,
            "executed_count": executed_count,
            "vulnerable_count": vulnerable_count,
            "failed_count": failed_count,
            "success_rate": success_rate,
            "total_execution_time": total_execution_time,
            "average_execution_time": average_execution_time
        }
    
    def _update_vulnerabilities(
        self,
        existing_vulnerabilities: List[Dict[str, Any]],
        verification_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        更新漏洞列表
        
        Args:
            existing_vulnerabilities: 现有漏洞列表
            verification_results: 验证结果列表
            
        Returns:
            List[Dict]: 更新后的漏洞列表
        """
        updated_vulnerabilities = list(existing_vulnerabilities)
        
        # 添加新发现的漏洞
        for result in verification_results:
            if result.get("vulnerable"):
                vulnerability = {
                    "name": result.get("poc_name", ""),
                    "poc_id": result.get("poc_id", ""),
                    "target": result.get("target", ""),
                    "severity": result.get("severity", "medium"),
                    "cvss_score": result.get("cvss_score", 0.0),
                    "confidence": result.get("confidence", 0.0),
                    "message": result.get("message", ""),
                    "source": "poc_verification",
                    "discovered_at": result.get("created_at", datetime.now().isoformat())
                }
                updated_vulnerabilities.append(vulnerability)
        
        return updated_vulnerabilities
    
    def get_node_info(self) -> Dict[str, Any]:
        """
        获取节点信息
        
        Returns:
            Dict: 节点信息
        """
        return {
            "name": self.node_name,
            "description": self.description,
            "enabled": settings.POC_VERIFICATION_ENABLED,
            "config": {
                "max_concurrent_executions": settings.POC_MAX_CONCURRENT_EXECUTIONS,
                "execution_timeout": settings.POC_EXECUTION_TIMEOUT,
                "max_retries": settings.POC_RETRY_MAX_COUNT,
                "result_accuracy_threshold": settings.POC_RESULT_ACCURACY_THRESHOLD
            }
        }


# 全局 POC 验证节点实例
poc_verification_node = POCVerificationNode()

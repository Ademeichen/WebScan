"""
POC验证子图

负责POC执行和验证状态更新。
执行时间目标: < 1分钟
最大轮次: 3轮
"""
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class POCVerificationState:
    """
    POC验证状态
    
    POCVerificationGraph专用的轻量级状态类。
    """
    target: str
    task_id: str
    poc_tasks: List[Dict[str, Any]] = field(default_factory=list)
    verified_pocs: List[Dict[str, Any]] = field(default_factory=list)
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    current_poc: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    round: int = 0
    max_rounds: int = 3
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "task_id": self.task_id,
            "poc_tasks": self.poc_tasks,
            "verified_pocs": self.verified_pocs,
            "vulnerabilities": self.vulnerabilities,
            "current_poc": self.current_poc,
            "errors": self.errors,
            "round": self.round,
            "execution_time": self.execution_time
        }


class POCExecutionNode:
    """
    POC执行节点
    
    执行单个POC验证任务。
    """
    
    def __init__(self):
        self.timeout = 30.0
    
    async def __call__(self, state: POCVerificationState) -> POCVerificationState:
        if not state.current_poc:
            return state
        
        poc_name = state.current_poc.get("poc_name", "unknown")
        poc_target = state.current_poc.get("target", state.target)
        
        logger.info(f"[{state.task_id}] 🔬 执行POC验证: {poc_name} -> {poc_target}")
        
        try:
            from ..tools.registry import registry
            
            result = await registry.call_tool(poc_name, poc_target)
            
            verified_poc = {
                "poc_name": poc_name,
                "target": poc_target,
                "status": "completed",
                "vulnerable": False,
                "output": "",
                "error": None
            }
            
            if result.get("status") == "success":
                data = result.get("data", {})
                verified_poc["vulnerable"] = data.get("vulnerable", False)
                verified_poc["output"] = data.get("message", "")
                
                if verified_poc["vulnerable"]:
                    vuln_info = {
                        "cve": poc_name.replace("poc_", ""),
                        "target": poc_target,
                        "severity": self._get_severity(poc_name),
                        "details": verified_poc["output"],
                        "poc_name": poc_name
                    }
                    state.vulnerabilities.append(vuln_info)
                    logger.warning(f"[{state.task_id}] 🚨 POC验证发现漏洞: {vuln_info}")
            else:
                verified_poc["status"] = "failed"
                verified_poc["error"] = result.get("error", "未知错误")
                state.errors.append(f"POC执行失败 {poc_name}: {verified_poc['error']}")
            
            state.verified_pocs.append(verified_poc)
            logger.info(f"[{state.task_id}] ✅ POC验证完成: {poc_name}, 结果: {'存在漏洞' if verified_poc['vulnerable'] else '未发现漏洞'}")
            
        except Exception as e:
            error_msg = f"POC执行异常 {poc_name}: {str(e)}"
            state.errors.append(error_msg)
            logger.error(f"[{state.task_id}] ❌ {error_msg}")
            
            state.verified_pocs.append({
                "poc_name": poc_name,
                "target": poc_target,
                "status": "error",
                "vulnerable": False,
                "error": str(e)
            })
        
        return state
    
    def _get_severity(self, poc_name: str) -> str:
        severity_map = {
            "cve_2020_2551": "critical",
            "cve_2017_12615": "high",
            "struts2_009": "critical",
            "struts2_032": "high"
        }
        return severity_map.get(poc_name, "medium")


class POCVerificationGraph:
    """
    POC验证图
    
    执行POC验证任务。
    """
    
    def __init__(self, max_execution_time: float = 60.0, max_rounds: int = 3):
        self.max_execution_time = max_execution_time
        self.max_rounds = max_rounds
        self.execution_node = POCExecutionNode()
        logger.info(f"📊 POCVerificationGraph 初始化, 最大执行时间: {max_execution_time}s, 最大轮次: {max_rounds}")
    
    async def execute(self, state: POCVerificationState) -> POCVerificationState:
        """
        执行POC验证
        
        Args:
            state: POC验证状态
            
        Returns:
            POCVerificationState: 更新后的状态
        """
        start_time = time.time()
        logger.info(f"[{state.task_id}] 🚀 开始POC验证图, 待验证POC: {len(state.poc_tasks)}")
        
        try:
            pending_pocs = [p for p in state.poc_tasks if p.get("status") == "pending"]
            
            while pending_pocs and state.round < self.max_rounds:
                if time.time() - start_time > self.max_execution_time:
                    logger.warning(f"[{state.task_id}] ⚠️ POC验证超时")
                    break
                
                state.round += 1
                state.current_poc = pending_pocs.pop(0)
                
                state = await self.execution_node(state)
            
            total_time = time.time() - start_time
            state.execution_time = total_time
            
            if total_time > self.max_execution_time:
                logger.warning(f"[{state.task_id}] ⚠️ POCVerificationGraph 执行超时: {total_time:.2f}s")
            else:
                logger.info(f"[{state.task_id}] ✅ POCVerificationGraph 执行完成, 耗时: {total_time:.2f}s, 验证POC: {len(state.verified_pocs)}")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ POCVerificationGraph 执行失败: {str(e)}")
            state.errors.append(f"POC验证图失败: {str(e)}")
        
        return state
    
    def get_result_dto(self, state: POCVerificationState) -> 'POCVerificationResultDTO':
        """
        将状态转换为POCVerificationResultDTO
        
        Args:
            state: POC验证状态
            
        Returns:
            POCVerificationResultDTO: POC验证结果DTO
        """
        from .dto import POCVerificationResultDTO, TaskStatus, SeverityLevel
        
        status = TaskStatus.COMPLETED if not state.errors else TaskStatus.FAILED
        
        verified_poc = state.verified_pocs[0] if state.verified_pocs else {}
        vulnerability = state.vulnerabilities[0] if state.vulnerabilities else {}
        
        severity = None
        if vulnerability.get("severity"):
            try:
                severity = SeverityLevel(vulnerability.get("severity"))
            except ValueError:
                severity = SeverityLevel.MEDIUM
        
        return POCVerificationResultDTO(
            task_id=state.task_id,
            target=state.target,
            poc_name=verified_poc.get("poc_name", "unknown"),
            status=status,
            vulnerable=verified_poc.get("vulnerable", False),
            severity=severity,
            cve_id=vulnerability.get("cve"),
            details=vulnerability.get("details"),
            evidence=vulnerability.get("evidence"),
            execution_time=state.execution_time
        )

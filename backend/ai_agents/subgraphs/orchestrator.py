"""
扫描编排器

负责协调各子图的执行，实现去中心化决策。

增强功能：
1. 智能调度 - 根据任务类型和依赖关系优化执行顺序
2. 结果聚合 - 合并多个子图的执行结果，去重和冲突处理
3. 超时控制 - 为每个子图添加独立的超时控制
4. 重试降级 - 子图失败时自动重试，失败后标记需要大图处理
5. 执行统计 - 记录每个子图的执行时间、成功率等
"""
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
from datetime import datetime

from .dto import (
    ScanPlanDTO, ToolExecutionResultDTO, CodeScanResultDTO,
    POCVerificationResultDTO, ReportDTO, OrchestratorResultDTO,
    TaskStatus, ScanDecisionType
)
from .planning import PlanningGraph, PlanningState
from .tool_execution import ToolExecutionGraph, ToolExecutionState
from .code_scan import CodeScanGraph, CodeScanState
from .poc_verification import POCVerificationGraph, POCVerificationState
from .report import ReportGraph, ReportState

logger = logging.getLogger(__name__)


class SubgraphType(Enum):
    """子图类型枚举"""
    PLANNING = "planning"
    TOOL_EXECUTION = "tool_execution"
    CODE_SCAN = "code_scan"
    POC_VERIFICATION = "poc_verification"
    REPORT = "report"


class ExecutionStatus(Enum):
    """执行状态枚举"""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    FAILED = "failed"
    RETRYING = "retrying"
    FALLBACK = "fallback"


@dataclass
class SubgraphExecutionRecord:
    """子图执行记录"""
    subgraph_type: SubgraphType
    start_time: float
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    retry_count: int = 0
    error_message: Optional[str] = None
    needs_main_graph: bool = False


@dataclass
class TaskDependency:
    """任务依赖关系"""
    task_name: str
    depends_on: List[str] = field(default_factory=list)
    priority: int = 0
    can_parallel: bool = True


class ScanOrchestrator:
    """
    扫描编排器
    
    协调各子图的执行，实现全局调度。
    核心原则：
    1. 每个子图只执行特定业务
    2. 子图间通过DTO传递数据
    3. 编排器负责全局决策
    """
    
    def __init__(
        self,
        planning_timeout: float = 10.0,
        tool_execution_timeout: float = 120.0,
        code_scan_timeout: float = 60.0,
        poc_verification_timeout: float = 60.0,
        report_timeout: float = 30.0,
        max_retries: int = 3,
        enable_parallel_execution: bool = True
    ):
        self.planning_graph = PlanningGraph()
        self.planning_graph.max_execution_time = planning_timeout
        self.tool_execution_graph = ToolExecutionGraph(max_execution_time=tool_execution_timeout)
        self.code_scan_graph = CodeScanGraph(max_execution_time=code_scan_timeout)
        self.poc_verification_graph = POCVerificationGraph(max_execution_time=poc_verification_timeout)
        self.report_graph = ReportGraph(max_execution_time=report_timeout)
        
        self._max_retries = max_retries
        self._enable_parallel_execution = enable_parallel_execution
        
        self._execution_stats: Dict[str, List[SubgraphExecutionRecord]] = defaultdict(list)
        self._task_dependencies: Dict[str, TaskDependency] = {}
        self._pending_fallback_tasks: Set[str] = set()
        
        self._subgraph_timeouts = {
            SubgraphType.PLANNING: planning_timeout,
            SubgraphType.TOOL_EXECUTION: tool_execution_timeout,
            SubgraphType.CODE_SCAN: code_scan_timeout,
            SubgraphType.POC_VERIFICATION: poc_verification_timeout,
            SubgraphType.REPORT: report_timeout
        }
        
        self._init_task_dependencies()
        
        logger.info("🎯 ScanOrchestrator 初始化完成")
        logger.info(f"   - PlanningGraph 超时: {planning_timeout}s")
        logger.info(f"   - ToolExecutionGraph 超时: {tool_execution_timeout}s")
        logger.info(f"   - CodeScanGraph 超时: {code_scan_timeout}s")
        logger.info(f"   - POCVerificationGraph 超时: {poc_verification_timeout}s")
        logger.info(f"   - ReportGraph 超时: {report_timeout}s")
        logger.info(f"   - 最大重试次数: {max_retries}")
        logger.info(f"   - 并行执行: {'启用' if enable_parallel_execution else '禁用'}")
    
    def _init_task_dependencies(self):
        """初始化任务依赖关系"""
        self._task_dependencies = {
            "port_scan": TaskDependency(
                task_name="port_scan",
                depends_on=[],
                priority=10,
                can_parallel=True
            ),
            "service_detection": TaskDependency(
                task_name="service_detection",
                depends_on=["port_scan"],
                priority=9,
                can_parallel=True
            ),
            "vuln_scan": TaskDependency(
                task_name="vuln_scan",
                depends_on=["service_detection"],
                priority=8,
                can_parallel=True
            ),
            "dir_brute": TaskDependency(
                task_name="dir_brute",
                depends_on=["port_scan"],
                priority=7,
                can_parallel=True
            ),
            "sqli_test": TaskDependency(
                task_name="sqli_test",
                depends_on=["vuln_scan"],
                priority=6,
                can_parallel=True
            ),
            "xss_test": TaskDependency(
                task_name="xss_test",
                depends_on=["vuln_scan"],
                priority=6,
                can_parallel=True
            ),
            "poc_verify": TaskDependency(
                task_name="poc_verify",
                depends_on=["vuln_scan"],
                priority=5,
                can_parallel=False
            )
        }
    
    async def execute_scan(
        self,
        target: str,
        task_id: str,
        target_context: Dict[str, Any] = None,
        custom_tasks: List[str] = None,
        enable_llm_planning: bool = False
    ) -> OrchestratorResultDTO:
        """
        执行完整扫描流程
        
        Args:
            target: 扫描目标
            task_id: 任务ID
            target_context: 目标上下文
            custom_tasks: 自定义任务列表
            enable_llm_planning: 是否启用LLM规划
            
        Returns:
            OrchestratorResultDTO: 最终结果
        """
        start_time = time.time()
        logger.info(f"[{task_id}] 🚀 开始执行扫描编排, 目标: {target}")
        
        result = OrchestratorResultDTO(
            task_id=task_id,
            target=target,
            status=TaskStatus.RUNNING
        )
        
        try:
            planning_state = PlanningState(
                target=target,
                task_id=task_id,
                target_context=target_context or {}
            )
            
            if custom_tasks:
                planning_state.planned_tasks = custom_tasks
                logger.info(f"[{task_id}] 📋 使用自定义任务列表: {custom_tasks}")
            
            planning_state = await self.planning_graph.run(
                target=target,
                task_id=task_id,
                target_context=target_context or {}
            )
            if custom_tasks:
                planning_state.planned_tasks = custom_tasks
            result.scan_plan = self.planning_graph.get_scan_plan_dto(planning_state)
            
            logger.info(f"[{task_id}] 📊 规划完成, 决策: {planning_state.decision}")
            
            if planning_state.errors:
                logger.warning(f"[{task_id}] ⚠️ 规划阶段有错误: {planning_state.errors}")
            
            all_vulnerabilities = []
            all_tool_results = {}
            
            if planning_state.decision == "fixed_tool":
                tool_result = await self._execute_tool_scan(
                    task_id=task_id,
                    target=target,
                    planned_tasks=planning_state.planned_tasks,
                    target_context=planning_state.target_context
                )
                result.tool_result = tool_result
                all_vulnerabilities.extend(tool_result.findings)
                if tool_result.tool_results:
                    if isinstance(tool_result.tool_results, dict):
                        all_tool_results.update(tool_result.tool_results)
                    else:
                        for tr in tool_result.tool_results:
                            if hasattr(tr, 'to_dict'):
                                all_tool_results[tr.tool_name] = tr.to_dict()
                            elif isinstance(tr, dict):
                                all_tool_results[tr.get('tool_name', 'unknown')] = tr
                
                if tool_result.new_poc_tasks:
                    poc_result = await self._execute_poc_verification(
                        task_id=task_id,
                        target=target,
                        poc_tasks=tool_result.new_poc_tasks
                    )
                    result.poc_results.append(poc_result)
                    all_vulnerabilities.extend(poc_result.vulnerabilities)
            
            elif planning_state.decision == "custom_code":
                code_result = await self._execute_code_scan(
                    task_id=task_id,
                    target=target,
                    need_custom_scan=True,
                    custom_scan_type=planning_state.custom_scan_type,
                    custom_scan_requirements=planning_state.custom_scan_requirements
                )
                result.code_scan_result = code_result
                all_vulnerabilities.extend(code_result.findings)
            
            elif planning_state.decision == "enhance_first":
                code_result = await self._execute_code_scan(
                    task_id=task_id,
                    target=target,
                    need_capability_enhancement=True,
                    capability_requirement=planning_state.capability_requirement
                )
                result.code_scan_result = code_result
            
            elif planning_state.decision == "poc_verification":
                poc_result = await self._execute_poc_verification(
                    task_id=task_id,
                    target=target,
                    poc_tasks=planning_state.poc_tasks
                )
                result.poc_results.append(poc_result)
                if poc_result.vulnerable and poc_result.cve_id:
                    all_vulnerabilities.append({
                        "cve": poc_result.cve_id,
                        "severity": poc_result.severity.value if poc_result.severity else "medium",
                        "details": poc_result.details
                    })
            
            elif planning_state.decision == "awvs_scan":
                logger.info(f"[{task_id}] 🔍 AWVS扫描模式")
            
            report_result = await self._generate_report(
                task_id=task_id,
                target=target,
                tool_results=all_tool_results,
                vulnerabilities=all_vulnerabilities,
                target_context=planning_state.target_context
            )
            result.report = report_result
            
            result.status = TaskStatus.COMPLETED
            result.total_execution_time = time.time() - start_time
            
            logger.info(f"[{task_id}] ✅ 扫描编排完成, 总耗时: {result.total_execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"[{task_id}] ❌ 扫描编排失败: {str(e)}")
            result.status = TaskStatus.FAILED
            result.total_execution_time = time.time() - start_time
        
        return result
    
    async def _execute_tool_scan(
        self,
        task_id: str,
        target: str,
        planned_tasks: List[str],
        target_context: Dict[str, Any]
    ) -> ToolExecutionResultDTO:
        """执行工具扫描"""
        logger.info(f"[{task_id}] 🔧 执行工具扫描")
        
        state = ToolExecutionState(
            target=target,
            task_id=task_id,
            planned_tasks=planned_tasks.copy(),
            current_task=planned_tasks[0] if planned_tasks else None,
            target_context=target_context
        )
        
        state = await self.tool_execution_graph.execute(state)
        return self.tool_execution_graph.get_result_dto(state)
    
    async def _execute_code_scan(
        self,
        task_id: str,
        target: str,
        need_custom_scan: bool = False,
        custom_scan_type: str = None,
        custom_scan_requirements: str = None,
        need_capability_enhancement: bool = False,
        capability_requirement: str = None
    ) -> CodeScanResultDTO:
        """执行代码扫描"""
        logger.info(f"[{task_id}] 💻 执行代码扫描")
        
        state = CodeScanState(
            target=target,
            task_id=task_id,
            need_custom_scan=need_custom_scan,
            custom_scan_type=custom_scan_type,
            custom_scan_requirements=custom_scan_requirements,
            need_capability_enhancement=need_capability_enhancement,
            capability_requirement=capability_requirement
        )
        
        state = await self.code_scan_graph.execute(state)
        return self.code_scan_graph.get_result_dto(state)
    
    async def _execute_poc_verification(
        self,
        task_id: str,
        target: str,
        poc_tasks: List[Dict[str, Any]]
    ) -> POCVerificationResultDTO:
        """执行POC验证"""
        logger.info(f"[{task_id}] 🔬 执行POC验证, 任务数: {len(poc_tasks)}")
        
        state = POCVerificationState(
            target=target,
            task_id=task_id,
            poc_tasks=poc_tasks
        )
        
        state = await self.poc_verification_graph.execute(state)
        return self.poc_verification_graph.get_result_dto(state)
    
    async def _generate_report(
        self,
        task_id: str,
        target: str,
        tool_results: Dict[str, Any],
        vulnerabilities: List[Dict[str, Any]],
        target_context: Dict[str, Any]
    ) -> ReportDTO:
        """生成报告"""
        logger.info(f"[{task_id}] 📝 生成扫描报告")
        
        state = ReportState(
            target=target,
            task_id=task_id,
            tool_results=tool_results,
            vulnerabilities=vulnerabilities,
            target_context=target_context
        )
        
        state = await self.report_graph.execute(state)
        return self.report_graph.get_result_dto(state)
    
    async def execute_planning_only(
        self,
        target: str,
        task_id: str,
        target_context: Dict[str, Any] = None
    ) -> ScanPlanDTO:
        """
        仅执行规划阶段
        
        用于快速获取扫描计划，不执行实际扫描。
        
        Args:
            target: 扫描目标
            task_id: 任务ID
            target_context: 目标上下文
            
        Returns:
            ScanPlanDTO: 扫描计划
        """
        logger.info(f"[{task_id}] 📋 仅执行规划阶段")
        
        planning_state = await self.planning_graph.run(
            target=target,
            task_id=task_id,
            target_context=target_context or {}
        )
        return self.planning_graph.get_scan_plan_dto(planning_state)
    
    async def execute_tool_scan_only(
        self,
        target: str,
        task_id: str,
        planned_tasks: List[str],
        target_context: Dict[str, Any] = None
    ) -> ToolExecutionResultDTO:
        """
        仅执行工具扫描
        
        用于单独执行工具扫描任务。
        
        Args:
            target: 扫描目标
            task_id: 任务ID
            planned_tasks: 计划任务列表
            target_context: 目标上下文
            
        Returns:
            ToolExecutionResultDTO: 工具执行结果
        """
        return await self._execute_tool_scan(
            task_id=task_id,
            target=target,
            planned_tasks=planned_tasks,
            target_context=target_context or {}
        )
    
    async def _execute_with_timeout(
        self,
        coro: Callable,
        timeout: float,
        task_name: str,
        task_id: str,
        subgraph_type: SubgraphType
    ) -> Tuple[Any, SubgraphExecutionRecord]:
        """
        带超时控制的执行
        
        Args:
            coro: 要执行的协程
            timeout: 超时时间（秒）
            task_name: 任务名称
            task_id: 任务ID
            subgraph_type: 子图类型
            
        Returns:
            Tuple[Any, SubgraphExecutionRecord]: 执行结果和执行记录
        """
        record = SubgraphExecutionRecord(
            subgraph_type=subgraph_type,
            start_time=time.time()
        )
        
        try:
            result = await asyncio.wait_for(
                coro,
                timeout=timeout
            )
            record.status = ExecutionStatus.SUCCESS
            logger.info(f"[{task_id}] ✅ {task_name} 执行成功")
            
        except asyncio.TimeoutError:
            record.status = ExecutionStatus.TIMEOUT
            record.error_message = f"任务 {task_name} 执行超时 (>{timeout}s)"
            logger.warning(f"[{task_id}] ⏰ {task_name} 执行超时 (>{timeout}s)")
            result = None
            
        except Exception as e:
            record.status = ExecutionStatus.FAILED
            record.error_message = str(e)
            logger.error(f"[{task_id}] ❌ {task_name} 执行失败: {str(e)}")
            result = None
            
        finally:
            record.end_time = time.time()
            record.execution_time = record.end_time - record.start_time
            
        return result, record
    
    async def _smart_schedule(
        self,
        tasks: List[str],
        task_id: str
    ) -> List[List[str]]:
        """
        智能调度 - 根据任务依赖关系优化执行顺序
        
        分析任务之间的依赖关系，将可以并行执行的任务分组。
        返回的任务组列表中，同一组内的任务可以并行执行，
        不同组之间需要按顺序执行。
        
        Args:
            tasks: 待调度的任务列表
            task_id: 任务ID
            
        Returns:
            List[List[str]]: 可并行执行的任务组列表
        """
        if not tasks:
            return []
        
        logger.info(f"[{task_id}] 🧠 开始智能调度, 任务数: {len(tasks)}")
        
        task_set = set(tasks)
        scheduled: Set[str] = set()
        schedule_groups: List[List[str]] = []
        
        remaining_tasks = task_set.copy()
        max_iterations = len(tasks) + 10
        iteration = 0
        
        while remaining_tasks and iteration < max_iterations:
            iteration += 1
            current_group = []
            
            for task in list(remaining_tasks):
                if task not in self._task_dependencies:
                    current_group.append(task)
                    continue
                
                dependency = self._task_dependencies[task]
                deps_satisfied = all(
                    dep in scheduled or dep not in task_set
                    for dep in dependency.depends_on
                )
                
                if deps_satisfied:
                    current_group.append(task)
            
            if not current_group:
                current_group = list(remaining_tasks)
                logger.warning(f"[{task_id}] ⚠️ 检测到循环依赖或未知依赖，强制调度剩余任务")
            
            current_group.sort(
                key=lambda t: self._task_dependencies.get(t, TaskDependency(t, priority=0)).priority,
                reverse=True
            )
            
            for task in current_group:
                remaining_tasks.discard(task)
                scheduled.add(task)
            
            if current_group:
                schedule_groups.append(current_group)
                logger.debug(f"[{task_id}] 📦 调度组 {len(schedule_groups)}: {current_group}")
        
        if not self._enable_parallel_execution:
            flattened = []
            for group in schedule_groups:
                flattened.extend(group)
            return [[task] for task in flattened]
        
        logger.info(f"[{task_id}] 📊 调度完成, 共 {len(schedule_groups)} 个执行组")
        return schedule_groups
    
    async def _aggregate_results(
        self,
        results: List[Any],
        task_id: str
    ) -> Dict[str, Any]:
        """
        结果智能聚合
        
        合并多个子图的执行结果，处理去重和冲突。
        
        Args:
            results: 多个子图的执行结果列表
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 聚合后的结果
        """
        if not results:
            return {}
        
        logger.info(f"[{task_id}] 🔗 开始结果聚合, 结果数: {len(results)}")
        
        aggregated = {
            "vulnerabilities": [],
            "tool_outputs": {},
            "findings": [],
            "metadata": {
                "total_sources": len(results),
                "aggregation_time": datetime.now().isoformat()
            }
        }
        
        seen_vulns: Set[str] = set()
        seen_findings: Set[str] = set()
        
        for idx, result in enumerate(results):
            if result is None:
                continue
                
            if hasattr(result, 'findings') and result.findings:
                for finding in result.findings:
                    finding_key = self._generate_finding_key(finding)
                    if finding_key not in seen_findings:
                        seen_findings.add(finding_key)
                        aggregated["findings"].append(finding)
                        
                        if isinstance(finding, dict):
                            vuln_key = f"{finding.get('cve', '')}_{finding.get('type', '')}_{finding.get('location', '')}"
                            if vuln_key not in seen_vulns:
                                seen_vulns.add(vuln_key)
                                aggregated["vulnerabilities"].append(finding)
            
            if hasattr(result, 'tool_results') and result.tool_results:
                if isinstance(result.tool_results, dict):
                    for tool_name, tool_output in result.tool_results.items():
                        if tool_name not in aggregated["tool_outputs"]:
                            aggregated["tool_outputs"][tool_name] = tool_output
                        else:
                            aggregated["tool_outputs"][tool_name] = self._merge_tool_outputs(
                                aggregated["tool_outputs"][tool_name],
                                tool_output
                            )
            
            if isinstance(result, dict):
                for key, value in result.items():
                    if key not in ["vulnerabilities", "findings", "tool_outputs"]:
                        if key not in aggregated:
                            aggregated[key] = value
                        elif isinstance(aggregated[key], list) and isinstance(value, list):
                            aggregated[key].extend(value)
                        elif isinstance(aggregated[key], dict) and isinstance(value, dict):
                            aggregated[key].update(value)
        
        aggregated["metadata"]["total_vulnerabilities"] = len(aggregated["vulnerabilities"])
        aggregated["metadata"]["total_findings"] = len(aggregated["findings"])
        aggregated["metadata"]["unique_vulnerabilities"] = len(seen_vulns)
        
        logger.info(f"[{task_id}] ✅ 结果聚合完成, 漏洞数: {len(aggregated['vulnerabilities'])}, 发现数: {len(aggregated['findings'])}")
        
        return aggregated
    
    def _generate_finding_key(self, finding: Any) -> str:
        """
        生成发现项的唯一键，用于去重
        
        Args:
            finding: 发现项
            
        Returns:
            str: 唯一键
        """
        if isinstance(finding, dict):
            parts = [
                str(finding.get("cve", "")),
                str(finding.get("type", "")),
                str(finding.get("name", "")),
                str(finding.get("location", "")),
                str(finding.get("url", ""))
            ]
            return "_".join(filter(None, parts))
        return str(id(finding))
    
    def _merge_tool_outputs(
        self,
        existing: Any,
        new: Any
    ) -> Any:
        """
        合并工具输出，处理冲突
        
        Args:
            existing: 已存在的输出
            new: 新的输出
            
        Returns:
            Any: 合并后的输出
        """
        if isinstance(existing, dict) and isinstance(new, dict):
            merged = existing.copy()
            for key, value in new.items():
                if key in merged:
                    if isinstance(merged[key], list) and isinstance(value, list):
                        merged[key] = merged[key] + value
                    elif isinstance(merged[key], dict) and isinstance(value, dict):
                        merged[key].update(value)
                    else:
                        merged[key] = value
                else:
                    merged[key] = value
            return merged
        elif isinstance(existing, list) and isinstance(new, list):
            return existing + new
        else:
            return new
    
    async def _retry_or_fallback(
        self,
        task_id: str,
        task_name: str,
        error: Exception,
        retry_count: int,
        subgraph_type: SubgraphType
    ) -> Tuple[bool, bool]:
        """
        重试或降级处理
        
        当子图执行失败时，根据重试次数决定是重试还是降级处理。
        
        Args:
            task_id: 任务ID
            task_name: 任务名称
            error: 错误信息
            retry_count: 当前重试次数
            subgraph_type: 子图类型
            
        Returns:
            Tuple[bool, bool]: (是否应该重试, 是否需要大图处理)
        """
        should_retry = retry_count < self._max_retries
        needs_main_graph = False
        
        if should_retry:
            wait_time = min(2 ** retry_count, 10)
            logger.warning(
                f"[{task_id}] 🔄 任务 {task_name} 失败，"
                f"将在 {wait_time}s 后重试 ({retry_count + 1}/{self._max_retries})"
            )
            await asyncio.sleep(wait_time)
        else:
            needs_main_graph = True
            self._pending_fallback_tasks.add(task_id)
            logger.error(
                f"[{task_id}] ❌ 任务 {task_name} 重试次数已达上限，"
                f"标记为需要大图处理"
            )
            
            self._record_fallback(task_id, task_name, str(error), subgraph_type)
        
        return should_retry, needs_main_graph
    
    def _record_fallback(
        self,
        task_id: str,
        task_name: str,
        error_message: str,
        subgraph_type: SubgraphType
    ):
        """
        记录降级信息
        
        Args:
            task_id: 任务ID
            task_name: 任务名称
            error_message: 错误信息
            subgraph_type: 子图类型
        """
        record = SubgraphExecutionRecord(
            subgraph_type=subgraph_type,
            start_time=time.time(),
            end_time=time.time(),
            status=ExecutionStatus.FALLBACK,
            error_message=error_message,
            needs_main_graph=True
        )
        self._execution_stats[task_id].append(record)
    
    def _record_execution(
        self,
        task_id: str,
        record: SubgraphExecutionRecord
    ):
        """
        记录执行统计
        
        Args:
            task_id: 任务ID
            record: 执行记录
        """
        self._execution_stats[task_id].append(record)
    
    def get_execution_stats(self, task_id: str = None) -> Dict[str, Any]:
        """
        获取执行统计
        
        返回指定任务或所有任务的执行统计信息，包括：
        - 各子图的执行时间
        - 成功率
        - 重试次数
        - 降级任务列表
        
        Args:
            task_id: 可选的任务ID，不提供则返回所有统计
            
        Returns:
            Dict[str, Any]: 执行统计信息
        """
        if task_id:
            return self._get_task_stats(task_id)
        
        all_stats = {
            "total_tasks": len(self._execution_stats),
            "tasks_with_failures": 0,
            "tasks_with_timeouts": 0,
            "tasks_needing_main_graph": len(self._pending_fallback_tasks),
            "subgraph_statistics": {},
            "pending_fallback_tasks": list(self._pending_fallback_tasks),
            "generated_at": datetime.now().isoformat()
        }
        
        subgraph_totals: Dict[SubgraphType, Dict] = {
            st: {
                "total_executions": 0,
                "success_count": 0,
                "timeout_count": 0,
                "failure_count": 0,
                "total_time": 0.0,
                "avg_time": 0.0
            }
            for st in SubgraphType
        }
        
        for tid, records in self._execution_stats.items():
            task_has_failure = False
            task_has_timeout = False
            
            for record in records:
                st = record.subgraph_type
                subgraph_totals[st]["total_executions"] += 1
                subgraph_totals[st]["total_time"] += record.execution_time or 0
                
                if record.status == ExecutionStatus.SUCCESS:
                    subgraph_totals[st]["success_count"] += 1
                elif record.status == ExecutionStatus.TIMEOUT:
                    subgraph_totals[st]["timeout_count"] += 1
                    task_has_timeout = True
                elif record.status == ExecutionStatus.FAILED:
                    subgraph_totals[st]["failure_count"] += 1
                    task_has_failure = True
            
            if task_has_failure:
                all_stats["tasks_with_failures"] += 1
            if task_has_timeout:
                all_stats["tasks_with_timeouts"] += 1
        
        for st, stats in subgraph_totals.items():
            if stats["total_executions"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["total_executions"]
                stats["success_rate"] = stats["success_count"] / stats["total_executions"]
            else:
                stats["success_rate"] = 0.0
            
            all_stats["subgraph_statistics"][st.value] = stats
        
        return all_stats
    
    def _get_task_stats(self, task_id: str) -> Dict[str, Any]:
        """
        获取单个任务的执行统计
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 任务执行统计
        """
        records = self._execution_stats.get(task_id, [])
        
        if not records:
            return {
                "task_id": task_id,
                "found": False,
                "message": "未找到该任务的执行记录"
            }
        
        task_stats = {
            "task_id": task_id,
            "found": True,
            "total_executions": len(records),
            "subgraph_executions": [],
            "total_time": 0.0,
            "has_failures": False,
            "needs_main_graph": False,
            "execution_timeline": []
        }
        
        for record in records:
            task_stats["total_time"] += record.execution_time or 0
            
            if record.status in [ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT]:
                task_stats["has_failures"] = True
            if record.needs_main_graph:
                task_stats["needs_main_graph"] = True
            
            task_stats["subgraph_executions"].append({
                "subgraph_type": record.subgraph_type.value,
                "status": record.status.value,
                "execution_time": record.execution_time,
                "retry_count": record.retry_count,
                "error_message": record.error_message,
                "needs_main_graph": record.needs_main_graph
            })
            
            task_stats["execution_timeline"].append({
                "time": record.start_time,
                "event": f"{record.subgraph_type.value} - {record.status.value}"
            })
        
        task_stats["execution_timeline"].sort(key=lambda x: x["time"])
        
        return task_stats
    
    def get_pending_fallback_tasks(self) -> List[str]:
        """
        获取需要大图处理的任务列表
        
        Returns:
            List[str]: 需要降级处理的任务ID列表
        """
        return list(self._pending_fallback_tasks)
    
    def clear_fallback_task(self, task_id: str) -> bool:
        """
        清除已处理的降级任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功清除
        """
        if task_id in self._pending_fallback_tasks:
            self._pending_fallback_tasks.discard(task_id)
            logger.info(f"[{task_id}] 🗑️ 已从降级任务列表中移除")
            return True
        return False
    
    async def execute_parallel_subgraphs(
        self,
        task_id: str,
        subgraph_configs: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        并行执行多个子图
        
        根据配置并行执行多个子图，支持超时控制和结果收集。
        
        Args:
            task_id: 任务ID
            subgraph_configs: 子图配置列表，每个配置包含:
                - subgraph_type: 子图类型
                - coro: 要执行的协程
                - timeout: 超时时间（可选，使用默认值）
                
        Returns:
            List[Any]: 执行结果列表
        """
        if not self._enable_parallel_execution:
            logger.info(f"[{task_id}] 📋 并行执行已禁用，将顺序执行")
            results = []
            for config in subgraph_configs:
                result = await self._execute_single_subgraph(task_id, config)
                results.append(result)
            return results
        
        logger.info(f"[{task_id}] 🚀 开始并行执行 {len(subgraph_configs)} 个子图")
        
        tasks = []
        for config in subgraph_configs:
            task = self._execute_single_subgraph(task_id, config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[{task_id}] ❌ 子图 {idx} 执行异常: {str(result)}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        logger.info(f"[{task_id}] ✅ 并行执行完成")
        return processed_results
    
    async def _execute_single_subgraph(
        self,
        task_id: str,
        config: Dict[str, Any]
    ) -> Any:
        """
        执行单个子图（带超时和重试）
        
        Args:
            task_id: 任务ID
            config: 子图配置
            
        Returns:
            Any: 执行结果
        """
        subgraph_type = config.get("subgraph_type")
        coro = config.get("coro")
        timeout = config.get("timeout", self._subgraph_timeouts.get(subgraph_type, 60.0))
        task_name = config.get("task_name", subgraph_type.value if subgraph_type else "unknown")
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self._max_retries:
            result, record = await self._execute_with_timeout(
                coro=coro,
                timeout=timeout,
                task_name=task_name,
                task_id=task_id,
                subgraph_type=subgraph_type
            )
            
            record.retry_count = retry_count
            self._record_execution(task_id, record)
            
            if record.status == ExecutionStatus.SUCCESS:
                return result
            
            last_error = Exception(record.error_message or "Unknown error")
            should_retry, _ = await self._retry_or_fallback(
                task_id=task_id,
                task_name=task_name,
                error=last_error,
                retry_count=retry_count,
                subgraph_type=subgraph_type
            )
            
            if not should_retry:
                break
            
            retry_count += 1
        
        return None

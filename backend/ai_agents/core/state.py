"""
Agent 状态管理

定义Agent的状态结构,用于LangGraph的状态传递。
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import json
from backend.utils.serializers import sanitize_json_data

logger = logging.getLogger(__name__)


async def persist_task_state(task_id: str, stage_status: Dict, progress: int):
    """Persist task state to database"""
    try:
        from backend.models import Task
        
        try:
            tid = int(task_id)
        except ValueError:
            return
            
        task = await Task.get(id=tid)
        task.progress = progress
        
        try:
            current_result = json.loads(task.result) if task.result else {}
        except:
            current_result = {}
            
        current_result['stages'] = stage_status

        # Ensure default fields exist to prevent frontend errors
        if 'scan_summary' not in current_result:
            current_result['scan_summary'] = {}
        if 'vulnerabilities' not in current_result:
            current_result['vulnerabilities'] = []
        if 'report' not in current_result:
            current_result['report'] = ""
        if 'execution_history' not in current_result:
            current_result['execution_history'] = []

        # Ensure json serialization handles common types if needed, or assume clean data
        current_result = sanitize_json_data(current_result)
        task.result = json.dumps(current_result, default=str)
        
        await task.save()
    except Exception as e:
        logger.error(f"Failed to persist task state for {task_id}: {e}")


@dataclass
class AgentState:
    """
    Agent状态类
    
    管理Agent执行过程中的所有状态信息,包括:
    - 基础信息:目标、任务ID
    - 任务规划:规划任务列表、当前任务、已完成任务
    - 执行结果:工具结果、发现的漏洞
    - 记忆与上下文:目标上下文、执行历史
    - 异常处理:错误列表、重试次数
    - 控制开关:完成标志、继续执行标志
    
    Attributes:
        target: 扫描目标(URL/IP)
        task_id: 任务ID
        planned_tasks: 规划的子任务列表
        current_task: 当前执行的子任务
        completed_tasks: 已完成子任务列表
        tool_results: 工具执行结果字典
        vulnerabilities: 发现的漏洞列表
        target_context: 目标上下文(CMS、端口、WAF等)
        execution_history: 执行历史记录
        errors: 执行错误列表
        retry_count: 重试次数
        is_complete: 任务是否完成
        should_continue: 是否继续执行
    """
    
    # = 基础信息 =
    target: str
    """
    扫描目标
    
    可以是URL、IP地址或域名。
    """
    
    task_id: str
    """
    任务ID
    
    用于标识和跟踪Agent任务。
    """
    
    # = 任务规划 =
    planned_tasks: List[str] = field(default_factory=list)
    """
    规划的子任务列表
    
    包含待执行的任务名称,如["baseinfo", "portscan", "poc_weblogic_2020_2551"]。
    """
    
    current_task: Optional[str] = None
    """
    当前执行的子任务
    
    表示Agent当前正在执行的任务。
    """
    
    completed_tasks: List[str] = field(default_factory=list)
    """
    已完成子任务列表
    
    记录已成功执行的任务。
    """
    
    # = 执行结果 =
    tool_results: Dict[str, Any] = field(default_factory=dict)
    """
    工具执行结果字典
    
    存储每个工具的执行结果,键为工具名称,值为结果数据。
    """
    
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    """
    发现的漏洞列表
    
    每个漏洞包含CVE、严重度、详情等信息。
    """
    
    # = 记忆与上下文 =
    target_context: Dict[str, Any] = field(default_factory=dict)
    """
    目标上下文

    存储目标的关键特征,如:
    - cms: CMS类型(WordPress、Drupal等)
    - open_ports: 开放端口列表
    - waf: WAF类型
    - cdn: 是否使用CDN
    - server: 服务器类型
    - os: 操作系统
    """
    
    user_tools: List[Dict[str, Any]] = field(default_factory=list)
    """
    用户提供的工具列表

    存储用户请求中提供的可用工具。
    """
    
    user_requirement: str = ""
    """
    用户需求描述

    用户的具体需求和目标描述。
    """
    
    memory_info: str = ""
    """
    记忆信息

    用于上下文传递的记忆信息。
    """
    
    plan_data: Optional[str] = None
    """
    规划数据

    存储规划节点的输出数据。
    """
    
    execution_results: List[Dict[str, Any]] = field(default_factory=list)
    """
    执行结果列表

    存储工具执行的结果列表。
    """
    
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    """
    执行历史记录
    
    记录Agent的执行步骤,用于追溯和调试。
    每条记录包含:task、result、timestamp等。
    """
    
    # = 异常处理 =
    errors: List[str] = field(default_factory=list)
    """
    执行错误列表
    
    记录执行过程中发生的错误信息。
    """
    
    retry_count: int = 0
    """
    重试次数
    
    记录当前任务的重试次数。
    """
    
    enhancement_retry_count: int = 0
    """
    功能增强重试次数
    
    记录功能增强的重试次数,防止无限循环。
    """
    
    # = 控制开关 =
    is_complete: bool = False
    """
    任务是否完成
    
    设置为True时,Agent将结束执行。
    """
    
    should_continue: bool = True
    """
    是否继续执行
    
    用于条件分支控制,决定是否继续执行工具还是进入下一阶段。
    """
    
    # = POC 验证 =
    poc_verification_tasks: List[Dict[str, Any]] = field(default_factory=list)
    """
    待验证的 POC 任务列表
    
    包含待执行的 POC 验证任务,每个任务包含:
    - poc_name: POC 名称
    - poc_id: POC ID(SSVID)
    - poc_code: POC 代码
    - target: 验证目标
    - priority: 优先级
    - status: 任务状态(pending/running/completed/failed)
    """
    
    poc_verification_results: List[Dict[str, Any]] = field(default_factory=list)
    """
    POC 验证结果列表
    
    存储 POC 验证的执行结果,每个结果包含:
    - poc_name: POC 名称
    - poc_id: POC ID
    - target: 验证目标
    - vulnerable: 是否存在漏洞
    - message: 结果消息
    - execution_time: 执行时间
    - confidence: 结果置信度
    - severity: 漏洞严重度
    """
    
    poc_execution_stats: Dict[str, Any] = field(default_factory=dict)
    """
    POC 执行统计信息
    
    包含 POC 验证执行的统计数据:
    - total_pocs: 总 POC 数量
    - executed_count: 已执行数量
    - vulnerable_count: 发现漏洞数量
    - failed_count: 失败数量
    - success_rate: 成功率
    - total_execution_time: 总执行时间
    - average_execution_time: 平均执行时间
    """
    
    poc_verification_status: str = "pending"
    """
    POC 验证状态
    
    整体验证流程的状态:
    - pending: 待执行
    - running: 执行中
    - paused: 已暂停
    - completed: 已完成
    - failed: 执行失败
    - cancelled: 已取消
    """
    
    # = Seebug Agent =
    seebug_pocs: List[Dict[str, Any]] = field(default_factory=list)
    """
    Seebug POC 搜索结果列表
    
    存储从Seebug搜索到的POC列表,每个POC包含:
    - ssvid: POC ID
    - name: POC 名称
    - type: POC 类型
    - description: POC 描述
    """
    
    generated_pocs: List[Dict[str, Any]] = field(default_factory=list)
    """
    生成的 POC 列表
    
    存储由Seebug Agent生成的POC代码,每个POC包含:
    - ssvid: POC ID
    - name: POC 名称
    - code: POC 代码
    - source: 来源(seebug_agent)
    """
    
    # = Stage Tracking =
    stage_status: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "openai": {"status": "pending", "sub_status": "pending", "progress": 0, "logs": [], "start_time": None, "end_time": None},
        "plugins": {"status": "pending", "sub_status": "pending", "progress": 0, "logs": [], "start_time": None, "end_time": None},
        "awvs": {"status": "pending", "sub_status": "pending", "progress": 0, "logs": [], "start_time": None, "end_time": None},
        "pocsuite3": {"status": "pending", "sub_status": "pending", "progress": 0, "logs": [], "start_time": None, "end_time": None}
    })
    """
    Stage Tracking
    
    Track the progress of 4 stages: openai, plugins, awvs, pocsuite3.
    """
    
    def update_stage_status(self, stage: str, status: str = None, sub_status: str = None, progress: int = None, log: str = None):
        """
        Update stage status and broadcast via WebSocket
        """
        # Import here to avoid circular dependency
        from backend.api.websocket import manager

        if stage in self.stage_status:
            if status:
                self.stage_status[stage]["status"] = status
            if sub_status:
                self.stage_status[stage]["sub_status"] = sub_status
            if progress is not None:
                self.stage_status[stage]["progress"] = progress
            if log:
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "message": log,
                    "sub_status": sub_status or self.stage_status[stage]["sub_status"]
                }
                self.stage_status[stage]["logs"].append(entry)
            
            # 广播阶段更新
            try:
                # 只有在事件循环中才能执行async操作
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        asyncio.create_task(manager.broadcast({
                            "type": "stage_update",
                            "payload": {
                                "task_id": self.task_id,
                                "stage": stage,
                                "data": self.stage_status[stage]
                            }
                        }))
                        
                        # 持久化到数据库
                        asyncio.create_task(persist_task_state(
                            self.task_id, 
                            self.stage_status, 
                            self.get_progress()
                        ))
                except RuntimeError:
                    # 如果没有运行的事件循环，则忽略（通常在同步测试中）
                    pass
            except Exception as e:
                logger.error(f"Failed to broadcast stage update: {e}")

    def get_progress(self) -> int:
        """
        Get total progress
        """
        total = 0
        count = 0
        for stage in self.stage_status.values():
            total += stage["progress"]
            count += 1
        return int(total / count) if count > 0 else 0

    def add_execution_step(
        self,
        task: str,
        result: Any,
        status: str = "success",
        step_type: str = "tool_execution",
        input_params: Dict[str, Any] = None,
        processing_logic: str = "",
        intermediate_results: List[Dict[str, Any]] = None,
        output_data: Dict[str, Any] = None,
        data_changes: Dict[str, Any] = None,
        state_transitions: List[str] = None,
        execution_time: float = None
    ):
        """
        添加执行步骤到历史记录（增强版）
        
        Args:
            task: 任务名称
            result: 执行结果
            status: 执行状态(success/failed/pending/running)
            step_type: 步骤类型(tool_execution/code_generation/code_execution/capability_enhancement/verification/analysis)
            input_params: 输入参数
            processing_logic: 处理逻辑描述
            intermediate_results: 中间结果列表
            output_data: 输出数据
            data_changes: 关键数据变化
            state_transitions: 状态转换列表
            execution_time: 执行时间（秒）
        """
        import time
        current_time = time.time()
        
        # 自动生成步骤编号
        step_number = len(self.execution_history) + 1
        
        # 记录当前状态快照
        current_state_snapshot = {
            "target": self.target,
            "current_task": self.current_task,
            "progress": self.get_progress(),
            "is_complete": self.is_complete,
            "should_continue": self.should_continue,
            "retry_count": self.retry_count
        }
        
        execution_step = {
            "step_number": step_number,
            "task": task,
            "step_type": step_type,
            "status": status,
            "timestamp": current_time,
            "timestamp_iso": datetime.fromtimestamp(current_time).isoformat(),
            "input_params": input_params or {},
            "processing_logic": processing_logic,
            "result": result,
            "intermediate_results": intermediate_results or [],
            "output_data": output_data or {},
            "data_changes": data_changes or {},
            "state_transitions": state_transitions or [],
            "execution_time": execution_time,
            "state_snapshot": current_state_snapshot
        }
        
        self.execution_history.append(execution_step)
    
    def add_execution_step_start(
        self,
        task: str,
        step_type: str = "tool_execution",
        input_params: Dict[str, Any] = None,
        processing_logic: str = ""
    ):
        """
        记录执行步骤开始
        
        Args:
            task: 任务名称
            step_type: 步骤类型
            input_params: 输入参数
            processing_logic: 处理逻辑描述
        """
        import time
        current_time = time.time()
        
        step_number = len(self.execution_history) + 1
        
        execution_step = {
            "step_number": step_number,
            "task": task,
            "step_type": step_type,
            "status": "running",
            "timestamp": current_time,
            "timestamp_iso": datetime.fromtimestamp(current_time).isoformat(),
            "input_params": input_params or {},
            "processing_logic": processing_logic,
            "start_time": current_time,
            "intermediate_results": [],
            "output_data": {},
            "data_changes": {},
            "state_transitions": ["started"]
        }
        
        self.execution_history.append(execution_step)
        return step_number
    
    def update_execution_step(
        self,
        step_number: int,
        result: Any = None,
        status: str = None,
        intermediate_results: List[Dict[str, Any]] = None,
        output_data: Dict[str, Any] = None,
        data_changes: Dict[str, Any] = None,
        state_transitions: List[str] = None
    ):
        """
        更新执行步骤
        
        Args:
            step_number: 步骤编号
            result: 执行结果
            status: 执行状态
            intermediate_results: 中间结果
            output_data: 输出数据
            data_changes: 数据变化
            state_transitions: 状态转换
        """
        import time
        
        if step_number <= len(self.execution_history):
            step = self.execution_history[step_number - 1]
            
            if result is not None:
                step["result"] = result
            
            if status is not None:
                step["status"] = status
                if status in ["success", "failed"]:
                    if "start_time" in step:
                        step["execution_time"] = time.time() - step["start_time"]
                    step["timestamp"] = time.time()
                    step["timestamp_iso"] = datetime.fromtimestamp(time.time()).isoformat()
            
            if intermediate_results is not None:
                step["intermediate_results"].extend(intermediate_results)
            
            if output_data is not None:
                step["output_data"].update(output_data)
            
            if data_changes is not None:
                step["data_changes"].update(data_changes)
            
            if state_transitions is not None:
                step["state_transitions"].extend(state_transitions)
    
    def update_context(self, key: str, value: Any):
        """
        更新目标上下文
        
        Args:
            key: 上下文键名
            value: 上下文值
        """
        self.target_context[key] = value
    
    def add_vulnerability(self, vuln: Dict[str, Any]):
        """
        添加漏洞到漏洞列表
        
        Args:
            vuln: 漏洞信息字典
        """
        self.vulnerabilities.append(vuln)
    
    def add_error(self, error: str):
        """
        添加错误到错误列表
        
        Args:
            error: 错误信息
        """
        self.errors.append(error)
    
    def increment_retry(self):
        """
        增加重试次数
        """
        self.retry_count += 1
    
    def reset_retry(self):
        """
        重置重试次数
        """
        self.retry_count = 0
    
    def increment_enhancement_retry(self):
        """
        增加功能增强重试次数
        """
        self.enhancement_retry_count += 1
        
    def reset_enhancement_retry(self):
        """
        重置功能增强重试次数
        """
        self.enhancement_retry_count = 0
    
    def mark_complete(self):
        """
        标记任务为完成
        """
        self.is_complete = True
        self.should_continue = False
    
    def get_progress(self) -> float:
        """
        获取任务进度
        
        Returns:
            float: 进度百分比(0-100)
        """
        if not self.planned_tasks:
            return 100.0
        total = len(self.planned_tasks)
        completed = len(self.completed_tasks)
        return (completed / total) * 100 if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict: 包含所有状态信息的字典
        """
        return {
            "target": self.target,
            "task_id": self.task_id,
            "planned_tasks": self.planned_tasks,
            "current_task": self.current_task,
            "completed_tasks": self.completed_tasks,
            "tool_results": self.tool_results,
            "vulnerabilities": self.vulnerabilities,
            "target_context": self.target_context,
            "execution_history": self.execution_history,
            "errors": self.errors,
            "retry_count": self.retry_count,
            "is_complete": self.is_complete,
            "should_continue": self.should_continue,
            "progress": self.get_progress(),
            "poc_verification_tasks": self.poc_verification_tasks,
            "poc_verification_results": self.poc_verification_results,
            "poc_execution_stats": self.poc_execution_stats,
            "poc_verification_status": self.poc_verification_status
        }

"""
Agent 状态管理

定义Agent的状态结构，用于LangGraph的状态传递。
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class AgentState:
    """
    Agent状态类
    
    管理Agent执行过程中的所有状态信息，包括：
    - 基础信息：目标、任务ID
    - 任务规划：规划任务列表、当前任务、已完成任务
    - 执行结果：工具结果、发现的漏洞
    - 记忆与上下文：目标上下文、执行历史
    - 异常处理：错误列表、重试次数
    - 控制开关：完成标志、继续执行标志
    
    Attributes:
        target: 扫描目标（URL/IP）
        task_id: 任务ID
        planned_tasks: 规划的子任务列表
        current_task: 当前执行的子任务
        completed_tasks: 已完成子任务列表
        tool_results: 工具执行结果字典
        vulnerabilities: 发现的漏洞列表
        target_context: 目标上下文（CMS、端口、WAF等）
        execution_history: 执行历史记录
        errors: 执行错误列表
        retry_count: 重试次数
        is_complete: 任务是否完成
        should_continue: 是否继续执行
    """
    
    # ====================== 基础信息 ======================
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
    
    # ====================== 任务规划 ======================
    planned_tasks: List[str] = field(default_factory=list)
    """
    规划的子任务列表
    
    包含待执行的任务名称，如["baseinfo", "portscan", "poc_weblogic_2020_2551"]。
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
    
    # ====================== 执行结果 ======================
    tool_results: Dict[str, Any] = field(default_factory=dict)
    """
    工具执行结果字典
    
    存储每个工具的执行结果，键为工具名称，值为结果数据。
    """
    
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    """
    发现的漏洞列表
    
    每个漏洞包含CVE、严重度、详情等信息。
    """
    
    # ====================== 记忆与上下文 ======================
    target_context: Dict[str, Any] = field(default_factory=dict)
    """
    目标上下文
    
    存储目标的关键特征，如：
    - cms: CMS类型（WordPress、Drupal等）
    - open_ports: 开放端口列表
    - waf: WAF类型
    - cdn: 是否使用CDN
    - server: 服务器类型
    - os: 操作系统
    """
    
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    """
    执行历史记录
    
    记录Agent的执行步骤，用于追溯和调试。
    每条记录包含：task、result、timestamp等。
    """
    
    # ====================== 异常处理 ======================
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
    
    # ====================== 控制开关 ======================
    is_complete: bool = False
    """
    任务是否完成
    
    设置为True时，Agent将结束执行。
    """
    
    should_continue: bool = True
    """
    是否继续执行
    
    用于条件分支控制，决定是否继续执行工具还是进入下一阶段。
    """
    
    def add_execution_step(self, task: str, result: Any, status: str = "success"):
        """
        添加执行步骤到历史记录
        
        Args:
            task: 任务名称
            result: 执行结果
            status: 执行状态（success/failed）
        """
        import time
        self.execution_history.append({
            "task": task,
            "result": result,
            "status": status,
            "timestamp": time.time()
        })
    
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
            float: 进度百分比（0-100）
        """
        if not self.planned_tasks:
            return 100.0
        total = len(self.planned_tasks) + len(self.completed_tasks)
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
            "progress": self.get_progress()
        }

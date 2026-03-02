"""
子图数据传输对象(DTO)

定义各子图之间传递数据的标准化格式，确保数据流清晰可追踪。
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class ScanDecisionType(Enum):
    """扫描决策类型"""
    FIXED_TOOL = "fixed_tool"
    CUSTOM_CODE = "custom_code"
    ENHANCE_FIRST = "enhance_first"
    POC_VERIFICATION = "poc_verification"
    SEEBUG_AGENT = "seebug_agent"
    AWVS_SCAN = "awvs_scan"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SeverityLevel(Enum):
    """漏洞严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ScanPlanDTO:
    """
    扫描计划DTO
    
    PlanningGraph的输出，作为后续子图的输入。
    """
    target: str
    task_id: str
    decision: ScanDecisionType
    tool_tasks: List[str] = field(default_factory=list)
    poc_tasks: List[Dict[str, Any]] = field(default_factory=list)
    need_custom_scan: bool = False
    custom_scan_type: Optional[str] = None
    custom_scan_requirements: Optional[str] = None
    need_capability_enhancement: bool = False
    capability_requirement: Optional[str] = None
    need_seebug: bool = False
    use_awvs: bool = False
    target_context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['decision'] = self.decision.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanPlanDTO':
        if 'decision' in data and isinstance(data['decision'], str):
            data['decision'] = ScanDecisionType(data['decision'])
        return cls(**data)


@dataclass
class ToolResultDTO:
    """单个工具执行结果"""
    tool_name: str
    status: TaskStatus
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass
class ToolExecutionResultDTO:
    """
    工具执行结果DTO
    
    ToolExecutionGraph的输出。
    """
    task_id: str
    target: str
    status: TaskStatus
    tool_results: List[ToolResultDTO] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    new_poc_tasks: List[Dict[str, Any]] = field(default_factory=list)
    awvs_required: bool = False
    target_context: Dict[str, Any] = field(default_factory=dict)
    total_execution_time: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        result['tool_results'] = [r.to_dict() for r in self.tool_results]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolExecutionResultDTO':
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = TaskStatus(data['status'])
        if 'tool_results' in data:
            data['tool_results'] = [
                ToolResultDTO(**r) if isinstance(r, dict) else r 
                for r in data['tool_results']
            ]
        return cls(**data)


@dataclass
class CodeScanResultDTO:
    """
    代码扫描结果DTO
    
    CodeScanGraph的输出。
    """
    task_id: str
    target: str
    status: TaskStatus
    generated_code: Optional[str] = None
    code_language: str = "python"
    execution_output: Optional[str] = None
    installed_packages: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    execution_logs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    execution_time: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass
class POCVerificationResultDTO:
    """
    POC验证结果DTO
    
    POCVerificationGraph的输出。
    """
    task_id: str
    target: str
    poc_name: str
    status: TaskStatus
    vulnerable: bool = False
    severity: Optional[SeverityLevel] = None
    cve_id: Optional[str] = None
    details: Optional[str] = None
    evidence: Optional[str] = None
    execution_time: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        if self.severity:
            result['severity'] = self.severity.value
        return result


@dataclass
class VulnerabilityDTO:
    """漏洞信息DTO"""
    vuln_id: str
    vuln_type: str
    severity: SeverityLevel
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    payload: Optional[str] = None
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    cve_id: Optional[str] = None
    poc_name: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['severity'] = self.severity.value
        return result


@dataclass
class ReportDTO:
    """
    扫描报告DTO
    
    ReportGraph的输出。
    """
    task_id: str
    target: str
    status: TaskStatus
    vulnerabilities: List[VulnerabilityDTO] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    tool_findings: Dict[str, Any] = field(default_factory=dict)
    report_content: Optional[str] = None
    report_format: str = "json"
    total_execution_time: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        result['vulnerabilities'] = [v.to_dict() for v in self.vulnerabilities]
        return result


@dataclass
class OrchestratorResultDTO:
    """
    编排器最终结果DTO
    
    ScanOrchestrator的最终输出。
    """
    task_id: str
    target: str
    status: TaskStatus
    scan_plan: Optional[ScanPlanDTO] = None
    tool_result: Optional[ToolExecutionResultDTO] = None
    code_scan_result: Optional[CodeScanResultDTO] = None
    poc_results: List[POCVerificationResultDTO] = field(default_factory=list)
    report: Optional[ReportDTO] = None
    total_execution_time: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        if self.scan_plan:
            result['scan_plan'] = self.scan_plan.to_dict()
        if self.tool_result:
            result['tool_result'] = self.tool_result.to_dict()
        if self.code_scan_result:
            result['code_scan_result'] = self.code_scan_result.to_dict()
        if self.poc_results:
            result['poc_results'] = [p.to_dict() for p in self.poc_results]
        if self.report:
            result['report'] = self.report.to_dict()
        return result

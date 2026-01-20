"""
数据库模型定义 - 使用 Tortoise-ORM
"""
from tortoise import fields
from tortoise.models import Model
from datetime import datetime
from typing import Optional


class Task(Model):
    """
    扫描任务表
    
    用于记录和管理各类安全扫描任务，包括端口扫描、漏洞扫描、子域名扫描等。
    任务状态流转：pending -> running -> completed/failed/cancelled
    
    Attributes:
        id: 任务唯一标识
        task_name: 任务名称，便于识别和管理
        task_type: 任务类型，如 scan（扫描）、vulnerability（漏洞检测）、poc（POC验证）等
        target: 扫描目标，可以是域名、IP地址或URL
        status: 任务状态，pending（待执行）、running（执行中）、completed（已完成）、failed（失败）、cancelled（已取消）
        progress: 任务进度，0-100的整数
        config: 任务配置信息，JSON格式存储扫描参数
        result: 任务执行结果，JSON格式存储扫描输出
        error_message: 错误信息，记录任务失败原因
        created_at: 任务创建时间
        updated_at: 任务最后更新时间
    """
    
    id = fields.IntField(pk=True, description="任务ID")
    task_name = fields.CharField(max_length=255, description="任务名称")
    task_type = fields.CharField(max_length=50, description="任务类型：scan, vulnerability, poc, etc.")
    target = fields.CharField(max_length=500, description="扫描目标（域名/IP/URL）")
    status = fields.CharField(max_length=50, default="pending", description="状态：pending, running, completed, failed, cancelled")
    progress = fields.IntField(default=0, description="任务进度 0-100")
    config = fields.TextField(null=True, description="任务配置信息（JSON格式）")
    result = fields.TextField(null=True, description="任务执行结果（JSON格式）")
    error_message = fields.TextField(null=True, description="错误信息")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    # 关系定义
    reports: fields.ReverseRelation["Report"]
    vulnerabilities: fields.ReverseRelation["Vulnerability"]
    scan_results: fields.ReverseRelation["ScanResult"]
    poc_results: fields.ReverseRelation["POCScanResult"]
    
    class Meta:
        table = "tasks"
        table_description = "扫描任务表"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.task_name} ({self.status})"
    
    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self.status == "running"
    
    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.status == "completed"
    
    def is_failed(self) -> bool:
        """检查任务是否失败"""
        return self.status == "failed"


class Report(Model):
    """
    扫描报告表
    
    用于存储和管理扫描任务生成的报告，支持多种格式（PDF、HTML、JSON等）。
    报告与任务是一对多关系，一个任务可以生成多个报告。
    
    Attributes:
        id: 报告唯一标识
        task: 关联的任务对象，外键关联到Task表
        report_name: 报告名称，便于识别和管理
        report_type: 报告类型，如pdf（PDF文档）、html（HTML网页）、json（JSON数据）等
        content: 报告内容，JSON格式存储结构化数据
        file_path: 报告文件存储路径，如果报告导出为文件
        created_at: 报告创建时间
        updated_at: 报告最后更新时间
    """
    
    id = fields.IntField(pk=True, description="报告ID")
    task: fields.ForeignKeyRelation[Task] = fields.ForeignKeyField(
        "models.Task", related_name="reports", description="关联任务"
    )
    report_name = fields.CharField(max_length=255, description="报告名称")
    report_type = fields.CharField(max_length=50, description="报告类型：pdf, html, json, docx, etc.")
    content = fields.TextField(null=True, description="报告内容（JSON格式）")
    file_path = fields.CharField(max_length=500, null=True, description="报告文件存储路径")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    class Meta:
        table = "reports"
        table_description = "扫描报告表"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.report_name} ({self.report_type})"
    
    def has_file(self) -> bool:
        """检查报告是否有文件"""
        return self.file_path is not None and len(self.file_path) > 0


class Vulnerability(Model):
    """
    漏洞信息表
    
    用于记录和管理安全扫描发现的漏洞信息，包括漏洞详情、严重程度、修复建议等。
    漏洞与任务是一对多关系，一个任务可以发现多个漏洞。
    
    Attributes:
        id: 漏洞唯一标识
        task: 关联的任务对象，外键关联到Task表
        vuln_type: 漏洞类型，如XSS（跨站脚本）、SQLInjection（SQL注入）、CSRF（跨站请求伪造）等
        severity: 严重程度，high（高危）、medium（中危）、low（低危）、info（信息）
        title: 漏洞标题，简洁描述漏洞
        description: 漏洞详细描述，说明漏洞原理和影响
        url: 漏洞所在的URL地址
        payload: 测试使用的Payload，用于复现漏洞
        evidence: 漏洞证据，如截图、响应数据等
        remediation: 修复建议，提供漏洞修复方案
        status: 漏洞状态，open（未修复）、fixed（已修复）、ignored（已忽略）
        created_at: 漏洞发现时间
        updated_at: 漏洞最后更新时间
    """
    
    id = fields.IntField(pk=True, description="漏洞ID")
    task: fields.ForeignKeyRelation[Task] = fields.ForeignKeyField(
        "models.Task", related_name="vulnerabilities", description="关联任务"
    )
    vuln_type = fields.CharField(max_length=100, description="漏洞类型：XSS, SQLInjection, CSRF, RCE, SSRF, etc.")
    severity = fields.CharField(max_length=20, description="严重程度：critical, high, medium, low, info")
    title = fields.CharField(max_length=255, description="漏洞标题")
    description = fields.TextField(null=True, description="漏洞详细描述")
    url = fields.CharField(max_length=500, null=True, description="漏洞URL地址")
    payload = fields.TextField(null=True, description="测试Payload")
    evidence = fields.TextField(null=True, description="漏洞证据（截图/响应数据等）")
    remediation = fields.TextField(null=True, description="修复建议")
    status = fields.CharField(max_length=50, default="open", description="状态：open, fixed, ignored, false_positive")
    source_id = fields.CharField(max_length=100, null=True, description="来源ID (如AWVS vuln_id)")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    class Meta:
        table = "vulnerabilities"
        table_description = "漏洞信息表"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.title} ({self.severity})"
    
    def is_critical(self) -> bool:
        """检查是否为高危漏洞"""
        return self.severity in ["critical", "high"]
    
    def is_open(self) -> bool:
        """检查漏洞是否未修复"""
        return self.status == "open"
    
    def is_fixed(self) -> bool:
        """检查漏洞是否已修复"""
        return self.status == "fixed"


class ScanResult(Model):
    """
    扫描结果表
    
    用于存储各类扫描任务的执行结果，如端口扫描、子域名扫描、目录扫描等。
    扫描结果与任务是一对多关系，一个任务可以产生多个扫描结果。
    
    Attributes:
        id: 结果唯一标识
        task: 关联的任务对象，外键关联到Task表
        scan_type: 扫描类型，如port_scan（端口扫描）、subdomain（子域名）、directory（目录扫描）等
        target: 扫描目标，域名、IP或URL
        result: 扫描结果，JSON格式存储结构化数据
        status: 扫描状态，success（成功）、failed（失败）
        error_message: 错误信息，记录扫描失败原因
        created_at: 扫描时间
    """
    
    id = fields.IntField(pk=True, description="结果ID")
    task: fields.ForeignKeyRelation[Task] = fields.ForeignKeyField(
        "models.Task", related_name="scan_results", description="关联任务"
    )
    scan_type = fields.CharField(max_length=50, description="扫描类型：port_scan, subdomain, directory, etc.")
    target = fields.CharField(max_length=500, description="扫描目标（域名/IP/URL）")
    result = fields.TextField(null=True, description="扫描结果（JSON格式）")
    status = fields.CharField(max_length=50, default="success", description="状态：success, failed")
    error_message = fields.TextField(null=True, description="错误信息")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "scan_results"
        table_description = "扫描结果表"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.scan_type} - {self.target}"
    
    def is_success(self) -> bool:
        """检查扫描是否成功"""
        return self.status == "success"


class SystemLog(Model):
    """
    系统日志表
    
    用于记录系统运行日志，包括操作日志、错误日志、访问日志等。
    支持按级别、模块、IP地址等维度查询和分析。
    
    Attributes:
        id: 日志唯一标识
        level: 日志级别，INFO（信息）、WARNING（警告）、ERROR（错误）
        module: 模块名称，标识日志来源模块
        message: 日志消息，具体的日志内容
        ip_address: 客户端IP地址，用于访问日志
        user_agent: 用户代理，记录客户端浏览器信息
        created_at: 日志记录时间
    """
    
    id = fields.IntField(pk=True, description="日志ID")
    level = fields.CharField(max_length=20, description="日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL")
    module = fields.CharField(max_length=100, null=True, description="模块名称")
    message = fields.TextField(description="日志消息内容")
    ip_address = fields.CharField(max_length=50, null=True, description="客户端IP地址")
    user_agent = fields.CharField(max_length=500, null=True, description="用户代理（User-Agent）")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "system_logs"
        table_description = "系统日志表"
        ordering = ["-created_at"]
        indexes = [
            ("level",),
            ("created_at",),
        ]
    
    def __str__(self):
        return f"[{self.level}] {self.message[:50]}..."
    
    def is_error(self) -> bool:
        """检查是否为错误日志"""
        return self.level in ["ERROR", "CRITICAL"]
    
    def is_warning(self) -> bool:
        """检查是否为警告日志"""
        return self.level == "WARNING"


class POCScanResult(Model):
    """
    POC（Proof of Concept）扫描结果表
    
    用于存储POC漏洞验证扫描的结果，验证目标是否存在已知漏洞。
    POC扫描结果与任务是一对多关系，一个任务可以扫描多个POC。
    
    Attributes:
        id: 结果唯一标识
        task: 关联的任务对象，外键关联到Task表
        poc_type: POC类型，如weblogic_cve_2020_2551、struts2_009等
        target: 扫描目标，域名、IP或URL
        vulnerable: 是否存在漏洞，True表示存在漏洞，False表示安全
        message: 扫描结果消息，详细说明扫描情况
        severity: 漏洞严重程度，high（高危）、medium（中危）、low（低危）
        cve_id: CVE编号，如CVE-2020-2551
        created_at: 扫描时间
    """
    
    id = fields.IntField(pk=True, description="结果ID")
    task: fields.ForeignKeyRelation[Task] = fields.ForeignKeyField(
        "models.Task", related_name="poc_results", description="关联任务"
    )
    poc_type = fields.CharField(max_length=100, description="POC类型：weblogic_cve_2020_2551, struts2_009, etc.")
    target = fields.CharField(max_length=500, description="扫描目标（域名/IP/URL）")
    vulnerable = fields.BooleanField(default=False, description="是否存在漏洞")
    message = fields.TextField(null=True, description="扫描结果消息")
    severity = fields.CharField(max_length=20, null=True, description="严重程度：critical, high, medium, low")
    cve_id = fields.CharField(max_length=50, null=True, description="CVE编号（如CVE-2020-2551）")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "poc_scan_results"
        table_description = "POC扫描结果表"
        ordering = ["-created_at"]
        indexes = [
            ("poc_type",),
            ("vulnerable",),
        ]
    
    def __str__(self):
        return f"{self.poc_type} - {self.target} ({'存在漏洞' if self.vulnerable else '安全'})"
    
    def is_vulnerable(self) -> bool:
        """检查是否存在漏洞"""
        return self.vulnerable
    
    def is_critical(self) -> bool:
        """检查是否为高危漏洞"""
        return self.vulnerable and self.severity in ["critical", "high"]


class AIChatInstance(Model):
    """
    AI对话实例表
    
    用于管理AI对话会话，支持多轮对话、对话历史记录等功能。
    对话实例与消息是一对多关系，一个对话实例包含多条消息。
    
    Attributes:
        id: 对话实例唯一标识（UUID）
        user_id: 用户ID，标识对话所属用户
        chat_name: 对话名称，便于用户识别和管理
        chat_type: 对话类型，如general（通用对话）、security（安全咨询）等
        status: 对话状态，active（活跃）、closed（已关闭）
        created_at: 对话创建时间
        updated_at: 对话最后更新时间
    """
    
    id = fields.UUIDField(pk=True, description="对话实例ID（UUID）")
    user_id = fields.CharField(max_length=100, null=True, description="用户ID")
    chat_name = fields.CharField(max_length=255, default="新对话", description="对话名称")
    chat_type = fields.CharField(max_length=50, default="general", description="对话类型：general, security, code_analysis, etc.")
    status = fields.CharField(max_length=50, default="active", description="状态：active, closed, archived")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    # 关系定义
    messages: fields.ReverseRelation["AIChatMessage"]
    
    class Meta:
        table = "ai_chat_instances"
        table_description = "AI对话实例表"
        ordering = ["-updated_at"]
        indexes = [
            ("user_id",),
            ("status",),
        ]
    
    def __str__(self):
        return f"{self.chat_name} ({self.status})"
    
    def is_active(self) -> bool:
        """检查对话是否活跃"""
        return self.status == "active"
    
    def is_closed(self) -> bool:
        """检查对话是否已关闭"""
        return self.status == "closed"
    
    def get_message_count(self) -> int:
        """获取对话消息数量（需要异步调用）"""
        return len(self.messages) if hasattr(self, 'messages') else 0


class AIChatMessage(Model):
    """
    AI对话消息表
    
    用于存储AI对话中的每条消息，包括用户消息和AI回复。
    消息与对话实例是多对一关系，一条消息属于一个对话实例。
    
    Attributes:
        id: 消息唯一标识（自增整数）
        chat_instance: 关联的对话实例对象，外键关联到AIChatInstance表
        role: 消息角色，user（用户消息）、assistant（AI回复）、system（系统消息）
        content: 消息内容，文本或JSON格式
        message_type: 消息类型，text（文本）、image（图片）、code（代码）等
        created_at: 消息创建时间
    """
    
    id = fields.BigIntField(pk=True, description="消息ID（自增）")
    chat_instance: fields.ForeignKeyRelation[AIChatInstance] = fields.ForeignKeyField(
        "models.AIChatInstance", related_name="messages", description="关联对话实例"
    )
    role = fields.CharField(max_length=20, description="角色：user, assistant, system")
    content = fields.TextField(description="消息内容")
    message_type = fields.CharField(max_length=50, default="text", description="消息类型：text, image, code, file, etc.")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "ai_chat_messages"
        table_description = "AI对话消息表"
        ordering = ["created_at"]
        indexes = [
            ("chat_instance",),
            ("role",),
        ]
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
    
    def is_user_message(self) -> bool:
        """检查是否为用户消息"""
        return self.role == "user"
    
    def is_assistant_message(self) -> bool:
        """检查是否为AI回复"""
        return self.role == "assistant"


class AgentTask(Model):
    """
    AI Agent 任务记录表
    
    用于记录AI Agent的自动化任务，如代码生成、漏洞分析、报告生成等。
    Agent任务与结果是一对一关系，一个任务对应一个执行结果。
    
    Attributes:
        task_id: 任务唯一标识（UUID）
        user_id: 用户ID，标识任务所属用户
        input_json: 用户输入的内容，JSON格式存储任务参数
        task_type: 任务类型，如code_generation（代码生成）、vuln_analysis（漏洞分析）等
        status: 任务状态，pending（待执行）、running（执行中）、completed（已完成）、failed（失败）
        created_at: 任务创建时间
        updated_at: 任务最后更新时间
    """
    
    task_id = fields.UUIDField(pk=True, description="任务ID（UUID）")
    user_id = fields.CharField(max_length=100, null=True, description="用户ID")
    input_json = fields.TextField(description="用户输入内容（JSON格式）")
    task_type = fields.CharField(max_length=50, null=True, description="任务类型：code_generation, vuln_analysis, report_generation, etc.")
    status = fields.CharField(max_length=50, default="pending", description="状态：pending, running, completed, failed, cancelled")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    # 关系定义
    result: fields.ReverseRelation["AgentResult"]
    
    class Meta:
        table = "agent_tasks"
        table_description = "AI Agent 任务记录表"
        ordering = ["-created_at"]
        indexes = [
            ("user_id",),
            ("status",),
            ("task_type",),
        ]
    
    def __str__(self):
        return f"AgentTask {self.task_id} ({self.status})"
    
    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self.status == "running"
    
    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.status == "completed"
    
    def is_failed(self) -> bool:
        """检查任务是否失败"""
        return self.status == "failed"


class AgentResult(Model):
    """
    AI Agent 执行结果表
    
    用于存储AI Agent任务的执行结果，包括输出内容、执行时间、错误信息等。
    结果与任务是多对一关系，一个结果对应一个任务。
    
    Attributes:
        id: 结果唯一标识（UUID）
        task: 关联的任务对象，外键关联到AgentTask表
        final_output: AI输出的结果，JSON格式存储结构化数据
        execution_time: 执行时间，单位为秒
        error_message: 错误信息，记录任务执行失败原因
        created_at: 结果创建时间
    """
    
    id = fields.UUIDField(pk=True, description="结果ID（UUID）")
    task: fields.ForeignKeyRelation[AgentTask] = fields.ForeignKeyField(
        "models.AgentTask", related_name="result", description="关联任务"
    )
    final_output = fields.TextField(description="AI输出结果（JSON格式）")
    execution_time = fields.FloatField(null=True, description="执行时间（秒）")
    error_message = fields.TextField(null=True, description="错误信息")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "agent_results"
        table_description = "AI Agent 执行结果表"
        ordering = ["-created_at"]
        indexes = [
            ("task",),
        ]
    
    def __str__(self):
        return f"AgentResult {self.id} for Task {self.task.task_id}"
    
    def is_success(self) -> bool:
        """检查执行是否成功"""
        return self.error_message is None
    
    def has_error(self) -> bool:
        """检查是否有错误"""
        return self.error_message is not None


class VulnerabilityKB(Model):
    """漏洞知识库表"""
    
    id = fields.IntField(pk=True, description="知识库ID")
    cve_id = fields.CharField(max_length=50, unique=True, null=True, description="CVE 编号")
    name = fields.CharField(max_length=500, description="漏洞名称")
    description = fields.TextField(null=True, description="漏洞描述")
    severity = fields.CharField(max_length=20, null=True, description="严重程度")
    cvss_score = fields.FloatField(null=True, description="CVSS 评分")
    affected_product = fields.TextField(null=True, description="影响组件/产品")
    solution = fields.TextField(null=True, description="修复建议")
    references = fields.TextField(null=True, description="参考链接（JSON/List）")
    poc_code = fields.TextField(null=True, description="POC 代码")
    has_poc = fields.BooleanField(default=False, description="是否有 POC")
    source = fields.CharField(max_length=50, default="manual", description="来源：seebug, exploit-db, manual")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    class Meta:
        table = "vulnerability_kb"
        table_description = "漏洞知识库表"
        ordering = ["-updated_at"]
    
    def __str__(self):
        return f"{self.cve_id or 'No CVE'} - {self.name}"

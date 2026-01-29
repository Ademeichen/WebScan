"""
POC 验证数据模型

定义 POC 验证系统所需的数据模型，包括验证任务、验证结果和执行日志。
"""
from tortoise import fields
from tortoise.models import Model
from datetime import datetime
from typing import Optional
from uuid import uuid4


class POCVerificationTask(Model):
    """
    POC 验证任务表
    
    用于记录和管理 POC 验证任务，支持批量验证和单个验证。
    任务状态流转：pending -> running -> completed/failed/cancelled
    
    Attributes:
        id: 任务唯一标识（UUID）
        task_id: 关联的任务ID
        poc_name: POC 名称
        poc_id: POC ID（SSVID）
        poc_code: POC 代码
        target: 验证目标
        priority: 优先级
        status: 任务状态
        progress: 任务进度
        config: 任务配置信息
        created_at: 任务创建时间
        updated_at: 任务最后更新时间
    """
    
    id = fields.UUIDField(pk=True, default=uuid4, description="任务ID（UUID）")
    task_id = fields.CharField(max_length=100, null=True, description="关联任务ID")
    poc_name = fields.CharField(max_length=255, description="POC 名称")
    poc_id = fields.CharField(max_length=100, null=True, description="POC ID（SSVID）")
    poc_code = fields.TextField(null=True, description="POC 代码")
    target = fields.CharField(max_length=500, description="验证目标")
    priority = fields.IntField(default=5, description="优先级（1-10，数字越小优先级越高）")
    status = fields.CharField(max_length=50, default="pending", description="状态：pending, running, completed, failed, cancelled")
    progress = fields.IntField(default=0, description="任务进度 0-100")
    config = fields.TextField(null=True, description="任务配置信息（JSON格式）")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    # 关系定义
    results: fields.ReverseRelation["POCVerificationResult"]
    execution_logs: fields.ReverseRelation["POCExecutionLog"]
    
    class Meta:
        table = "poc_verification_tasks"
        table_description = "POC 验证任务表"
        ordering = ["-created_at"]
        indexes = [
            ("task_id",),
            ("status",),
            ("priority",),
        ]
    
    def __str__(self):
        return f"{self.poc_name} ({self.status})"
    
    def is_pending(self) -> bool:
        """检查任务是否待执行"""
        return self.status == "pending"
    
    def is_running(self) -> bool:
        """检查任务是否正在执行"""
        return self.status == "running"
    
    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.status == "completed"
    
    def is_failed(self) -> bool:
        """检查任务是否失败"""
        return self.status == "failed"
    
    def is_cancelled(self) -> bool:
        """检查任务是否已取消"""
        return self.status == "cancelled"


class POCVerificationResult(Model):
    """
    POC 验证结果表
    
    用于存储 POC 验证的执行结果，包括漏洞状态、严重度、置信度等。
    与验证任务是一对多关系，一个任务可以有多个验证结果。
    
    Attributes:
        id: 结果唯一标识
        verification_task: 关联的验证任务对象
        poc_name: POC 名称
        poc_id: POC ID
        target: 验证目标
        vulnerable: 是否存在漏洞
        message: 结果消息
        output: 完整输出
        error: 错误信息
        execution_time: 执行时间（秒）
        confidence: 结果置信度（0-1）
        severity: 漏洞严重度
        cvss_score: CVSS 评分
        created_at: 结果创建时间
    """
    
    id = fields.BigIntField(pk=True, description="结果ID（自增）")
    verification_task: fields.ForeignKeyRelation[POCVerificationTask] = fields.ForeignKeyField(
        "models.POCVerificationTask", related_name="results", description="关联验证任务"
    )
    poc_name = fields.CharField(max_length=255, description="POC 名称")
    poc_id = fields.CharField(max_length=100, null=True, description="POC ID")
    target = fields.CharField(max_length=500, description="验证目标")
    vulnerable = fields.BooleanField(default=False, description="是否存在漏洞")
    message = fields.TextField(description="结果消息")
    output = fields.TextField(null=True, description="完整输出")
    error = fields.TextField(null=True, description="错误信息")
    execution_time = fields.FloatField(default=0.0, description="执行时间（秒）")
    confidence = fields.FloatField(default=0.0, description="结果置信度（0-1）")
    severity = fields.CharField(max_length=50, null=True, description="漏洞严重度：critical, high, medium, low, info")
    cvss_score = fields.FloatField(null=True, description="CVSS 评分（0-10）")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "poc_verification_results"
        table_description = "POC 验证结果表"
        ordering = ["-created_at"]
        indexes = [
            ("verification_task",),
            ("vulnerable",),
            ("severity",),
        ]
    
    def __str__(self):
        return f"{self.poc_name} - {self.target} ({'Vulnerable' if self.vulnerable else 'Not Vulnerable'})"


class POCExecutionLog(Model):
    """
    POC 执行日志表
    
    用于记录 POC 执行过程中的详细日志，包括执行步骤、输出、错误等。
    与验证结果是一对多关系，一个结果可以有多条执行日志。
    
    Attributes:
        id: 日志唯一标识
        verification_result: 关联的验证结果对象
        log_level: 日志级别
        message: 日志消息
        details: 详细信息
        timestamp: 日志时间戳
    """
    
    id = fields.BigIntField(pk=True, description="日志ID（自增）")
    verification_result: fields.ForeignKeyRelation[POCVerificationResult] = fields.ForeignKeyField(
        "models.POCVerificationResult", related_name="execution_logs", description="关联验证结果"
    )
    log_level = fields.CharField(max_length=20, default="info", description="日志级别：debug, info, warning, error, critical")
    message = fields.TextField(description="日志消息")
    details = fields.TextField(null=True, description="详细信息（JSON格式）")
    timestamp = fields.DatetimeField(auto_now_add=True, description="日志时间戳")
    
    class Meta:
        table = "poc_execution_logs"
        table_description = "POC 执行日志表"
        ordering = ["timestamp"]
        indexes = [
            ("verification_result",),
            ("log_level",),
            ("timestamp",),
        ]
    
    def __str__(self):
        return f"[{self.log_level.upper()}] {self.message[:50]}..."

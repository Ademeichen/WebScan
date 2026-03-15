"""
增强版报告生成器

实现完整的子图/节点执行信息保留、AI分析集成、多格式报告导出。
"""
import json
import logging
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    """报告格式枚举"""
    JSON = "json"
    HTML = "html"
    PDF = "pdf"


SEVERITY_CONFIG = {
    "critical": {"score": 10.0, "color": "#c0392b", "label": "严重", "order": 0},
    "high": {"score": 8.0, "color": "#e74c3c", "label": "高危", "order": 1},
    "medium": {"score": 5.0, "color": "#f39c12", "label": "中危", "order": 2},
    "low": {"score": 3.0, "color": "#3498db", "label": "低危", "order": 3},
    "info": {"score": 1.0, "color": "#95a5a6", "label": "信息", "order": 4}
}


@dataclass
class EnvironmentInfo:
    """环境信息"""
    os: str = ""
    python_version: str = ""
    dependencies: Dict[str, str] = field(default_factory=dict)


@dataclass
class TargetInfo:
    """目标信息"""
    url: str = ""
    ip: str = ""
    domain: str = ""
    ports: List[int] = field(default_factory=list)


@dataclass
class ExecutionTiming:
    """执行时序信息"""
    start_time: str = ""
    end_time: str = ""
    total_duration_ms: float = 0.0
    module_durations: Dict[str, float] = field(default_factory=dict)


@dataclass
class NodeExecutionInfo:
    """节点执行信息"""
    node_id: str = ""
    node_name: str = ""
    subgraph_name: str = ""
    input_params: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: str = ""
    error_log: str = ""
    execution_time_ms: float = 0.0
    timestamp: str = ""


@dataclass
class SubgraphExecutionInfo:
    """子图执行信息"""
    subgraph_id: str = ""
    subgraph_name: str = ""
    nodes: List[NodeExecutionInfo] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""
    status: str = ""


@dataclass
class GraphFlowVisualization:
    """图流程可视化数据"""
    subgraphs: List[SubgraphExecutionInfo] = field(default_factory=list)
    dependencies: List[Dict[str, str]] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)


@dataclass
class InfoCollectionResult:
    """信息收集结果"""
    crawler_links_count: int = 0
    dirscan_count: int = 0
    cms_identified: str = ""
    middleware_version: str = ""
    open_ports: List[int] = field(default_factory=list)
    waf_detected: str = ""
    cdn_detected: bool = False
    subdomains_found: List[str] = field(default_factory=list)


@dataclass
class VulnerabilityItem:
    """漏洞项"""
    vuln_name: str = ""
    cve_id: str = ""
    affected_url: str = ""
    severity: str = ""
    poc_result: str = ""
    remediation: str = ""
    description: str = ""


@dataclass
class AIModelInfo:
    """AI模型信息"""
    model_name: str = ""
    model_version: str = ""
    deployment_type: str = ""
    temperature: float = 0.7
    context_length: int = 4096
    call_count: int = 0
    total_time_ms: float = 0.0


@dataclass
class AIResultAnalysis:
    """AI结果分析"""
    vulnerability_causes: List[str] = field(default_factory=list)
    exploitation_risks: List[str] = field(default_factory=list)
    remediation_priorities: List[Dict[str, Any]] = field(default_factory=list)
    business_impact: str = ""
    analysis_evidence: List[str] = field(default_factory=list)


@dataclass
class ToolExecutionStep:
    """工具执行步骤"""
    step_number: int = 0
    tool_name: str = ""
    trigger_condition: str = ""
    output_result: str = ""
    timestamp: str = ""


@dataclass
class EnhancedReportData:
    """增强版报告数据结构"""
    task_name: str = ""
    task_id: str = ""
    
    environment: EnvironmentInfo = field(default_factory=EnvironmentInfo)
    target: TargetInfo = field(default_factory=TargetInfo)
    timing: ExecutionTiming = field(default_factory=ExecutionTiming)
    
    tool_execution_flow: List[ToolExecutionStep] = field(default_factory=list)
    graph_flow: GraphFlowVisualization = field(default_factory=GraphFlowVisualization)
    
    info_collection: InfoCollectionResult = field(default_factory=InfoCollectionResult)
    vulnerabilities: List[VulnerabilityItem] = field(default_factory=list)
    
    ai_model: AIModelInfo = field(default_factory=AIModelInfo)
    ai_analysis: AIResultAnalysis = field(default_factory=AIResultAnalysis)
    
    raw_data: Dict[str, Any] = field(default_factory=dict)


class EnhancedReportGenerator:
    """
    增强版报告生成器
    
    支持完整的子图/节点执行信息保留、AI分析集成、多格式报告导出。
    """
    
    def __init__(self, output_dir: str = "reports", auto_ai_analysis: bool = True):
        """
        初始化报告生成器
        
        Args:
            output_dir: 输出目录
            auto_ai_analysis: 是否自动进行AI分析
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.auto_ai_analysis = auto_ai_analysis
        self.ai_analyzer = None
        
        if self.auto_ai_analysis:
            try:
                from .ai_analyzer import AIAnalyzer
                self.ai_analyzer = AIAnalyzer()
                logger.info("🧠 AI分析器已集成到报告生成器")
            except Exception as e:
                logger.warning(f"AI分析器集成失败: {e}，将需要手动提供AI分析数据")
        
        logger.info("📄 增强版报告生成器初始化完成")
    
    def collect_environment_info(self) -> EnvironmentInfo:
        """收集环境信息"""
        try:
            from importlib.metadata import distributions
            dependencies = {
                dist.metadata['Name']: dist.version
                for dist in distributions()
            }
        except:
            try:
                import pkg_resources
                dependencies = {
                    d.key: d.version
                    for d in pkg_resources.working_set
                }
            except:
                dependencies = {}
        
        return EnvironmentInfo(
            os=platform.system() + " " + platform.release(),
            python_version=sys.version,
            dependencies=dependencies
        )
    
    async def generate_from_state(
        self,
        state: Any,
        task_name: str = "Security Scan Task",
        ai_analysis_data: Optional[Dict[str, Any]] = None
    ) -> EnhancedReportData:
        """
        从Agent状态生成增强版报告数据
        
        Args:
            state: Agent状态对象
            task_name: 任务名称
            ai_analysis_data: 可选的AI分析数据，如果不提供且启用了auto_ai_analysis则自动分析
            
        Returns:
            EnhancedReportData: 增强版报告数据
        """
        report_data = EnhancedReportData(
            task_name=task_name,
            task_id=getattr(state, "task_id", "unknown")
        )
        
        report_data.environment = self.collect_environment_info()
        report_data.target = self._extract_target_info(state)
        report_data.timing = self._extract_timing_info(state)
        report_data.tool_execution_flow = self._extract_tool_flow(state)
        report_data.graph_flow = self._extract_graph_flow(state)
        report_data.info_collection = self._extract_info_collection(state)
        report_data.vulnerabilities = self._extract_vulnerabilities(state)
        report_data.ai_model = self._extract_ai_model_info(state)
        
        if ai_analysis_data:
            report_data.ai_analysis = self._parse_ai_analysis(ai_analysis_data)
        elif self.ai_analyzer:
            vulnerabilities = getattr(state, "vulnerabilities", [])
            tool_results = getattr(state, "tool_results", {})
            target_context = getattr(state, "target_context", {})
            
            try:
                import time
                start_time = time.time()
                
                ai_result = await self.ai_analyzer.analyze_scan_results(
                    vulnerabilities, tool_results, target_context
                )
                
                end_time = time.time()
                elapsed_ms = (end_time - start_time) * 1000
                
                report_data.ai_analysis = self._parse_ai_analysis(ai_result.to_dict())
                report_data.ai_model.call_count += 1
                report_data.ai_model.total_time_ms += elapsed_ms
                logger.info("✅ 自动AI分析完成并集成到报告")
            except Exception as e:
                logger.warning(f"自动AI分析失败: {e}")
        
        report_data.raw_data = self._get_raw_state_data(state)
        
        return report_data
    
    def generate_from_state_sync(
        self,
        state: Any,
        task_name: str = "Security Scan Task",
        ai_analysis_data: Optional[Dict[str, Any]] = None
    ) -> EnhancedReportData:
        """
        从Agent状态生成增强版报告数据（同步版本）
        
        Args:
            state: Agent状态对象
            task_name: 任务名称
            ai_analysis_data: 可选的AI分析数据
            
        Returns:
            EnhancedReportData: 增强版报告数据
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_from_state(state, task_name, ai_analysis_data)
        )
    
    def _extract_target_info(self, state: Any) -> TargetInfo:
        """从状态提取目标信息"""
        target_info = TargetInfo()
        target_info.url = getattr(state, "target", "")
        
        target_context = getattr(state, "target_context", {})
        if isinstance(target_context, dict):
            target_info.ip = target_context.get("ip", "")
            target_info.domain = target_context.get("domain", "")
            target_info.ports = target_context.get("open_ports", [])
        
        return target_info
    
    def _extract_timing_info(self, state: Any) -> ExecutionTiming:
        """从状态提取执行时序信息"""
        timing = ExecutionTiming()
        
        execution_history = getattr(state, "execution_history", [])
        
        if execution_history:
            first_step = execution_history[0]
            last_step = execution_history[-1]
            
            timing.start_time = first_step.get("timestamp_iso", "")
            timing.end_time = last_step.get("timestamp_iso", "")
            
            start_ts = first_step.get("timestamp", 0)
            end_ts = last_step.get("timestamp", 0)
            timing.total_duration_ms = (end_ts - start_ts) * 1000 if start_ts and end_ts else 0
            
            timing.module_durations = self._calculate_module_durations(execution_history)
        
        return timing
    
    def _calculate_module_durations(self, execution_history: List[Dict]) -> Dict[str, float]:
        """计算各模块耗时"""
        module_times = {}
        
        for step in execution_history:
            task = step.get("task", "")
            exec_time = step.get("execution_time", 0)
            
            if task:
                if task not in module_times:
                    module_times[task] = 0
                module_times[task] += (exec_time or 0) * 1000
        
        return module_times
    
    def _extract_tool_flow(self, state: Any) -> List[ToolExecutionStep]:
        """提取工具执行流程"""
        tool_flow = []
        execution_history = getattr(state, "execution_history", [])
        
        for i, step in enumerate(execution_history):
            tool_step = ToolExecutionStep(
                step_number=i + 1,
                tool_name=step.get("task", ""),
                trigger_condition="sequential",
                output_result=str(step.get("result", "")),
                timestamp=step.get("timestamp_iso", "")
            )
            tool_flow.append(tool_step)
        
        return tool_flow
    
    def _extract_graph_flow(self, state: Any) -> GraphFlowVisualization:
        """提取图流程可视化数据"""
        graph_flow = GraphFlowVisualization()
        
        execution_history = getattr(state, "execution_history", [])
        
        current_subgraph = SubgraphExecutionInfo(
            subgraph_id="main",
            subgraph_name="Main Workflow",
            status="completed"
        )
        
        if execution_history:
            current_subgraph.start_time = execution_history[0].get("timestamp_iso", "")
            current_subgraph.end_time = execution_history[-1].get("timestamp_iso", "")
        
        for step in execution_history:
            node_info = NodeExecutionInfo(
                node_id=step.get("task", ""),
                node_name=step.get("task", ""),
                subgraph_name="Main Workflow",
                input_params=step.get("input_params", {}),
                output_data=step.get("output_data", {}),
                status=step.get("status", ""),
                error_log=step.get("error", ""),
                execution_time_ms=(step.get("execution_time", 0) or 0) * 1000,
                timestamp=step.get("timestamp_iso", "")
            )
            current_subgraph.nodes.append(node_info)
            graph_flow.execution_order.append(step.get("task", ""))
        
        graph_flow.subgraphs.append(current_subgraph)
        
        return graph_flow
    
    def _extract_info_collection(self, state: Any) -> InfoCollectionResult:
        """提取信息收集结果"""
        info_result = InfoCollectionResult()
        
        tool_results = getattr(state, "tool_results", {})
        
        for tool_name, result in tool_results.items():
            if tool_name == "crawler":
                data = result.get("data", {})
                info_result.crawler_links_count = len(data.get("links", []))
            elif tool_name == "dirscan":
                data = result.get("data", {})
                info_result.dirscan_count = len(data.get("directories", []))
            elif tool_name == "cms_identify":
                data = result.get("data", {})
                apps = data.get("apps", [])
                if apps:
                    info_result.cms_identified = apps[0].get("name", "")
        
        target_context = getattr(state, "target_context", {})
        if isinstance(target_context, dict):
            info_result.open_ports = target_context.get("open_ports", [])
            info_result.waf_detected = target_context.get("waf", "")
            info_result.cdn_detected = target_context.get("cdn", False)
        
        return info_result
    
    def _extract_vulnerabilities(self, state: Any) -> List[VulnerabilityItem]:
        """提取漏洞列表"""
        vuln_items = []
        
        vulnerabilities = getattr(state, "vulnerabilities", [])
        
        for vuln in vulnerabilities:
            item = VulnerabilityItem(
                vuln_name=vuln.get("title", vuln.get("vuln_type", "Unknown")),
                cve_id=vuln.get("cve", ""),
                affected_url=vuln.get("url", ""),
                severity=vuln.get("severity", "info"),
                poc_result=vuln.get("details", ""),
                remediation=vuln.get("remediation", ""),
                description=vuln.get("description", "")
            )
            vuln_items.append(item)
        
        severity_order = {s: c["order"] for s, c in SEVERITY_CONFIG.items()}
        vuln_items.sort(key=lambda x: severity_order.get(x.severity, 4))
        
        return vuln_items
    
    def _extract_ai_model_info(self, state: Any) -> AIModelInfo:
        """提取AI模型信息"""
        from backend.ai_agents.agent_config import agent_config
        
        model_info = AIModelInfo(
            model_name=getattr(agent_config, "MODEL_ID", "unknown"),
            model_version="1.0",
            deployment_type="API",
            temperature=0.7,
            context_length=4096
        )
        
        return model_info
    
    def _parse_ai_analysis(self, ai_analysis_data: Dict[str, Any]) -> AIResultAnalysis:
        """解析AI分析数据"""
        analysis = AIResultAnalysis()
        
        causes = ai_analysis_data.get("causes", [])
        analysis.vulnerability_causes = []
        for cause in causes:
            if isinstance(cause, dict) and "description" in cause:
                analysis.vulnerability_causes.append(cause["description"])
            elif isinstance(cause, str):
                analysis.vulnerability_causes.append(cause)
        
        risks = ai_analysis_data.get("risks", [])
        analysis.exploitation_risks = []
        for risk in risks:
            if isinstance(risk, dict) and "description" in risk:
                analysis.exploitation_risks.append(risk["description"])
            elif isinstance(risk, str):
                analysis.exploitation_risks.append(risk)
        
        analysis.remediation_priorities = ai_analysis_data.get("priorities", [])
        
        business_impact = ai_analysis_data.get("business_impact", "")
        if isinstance(business_impact, dict):
            analysis.business_impact = str(business_impact)
        else:
            analysis.business_impact = business_impact
        
        analysis.analysis_evidence = ai_analysis_data.get("evidence", [])
        
        return analysis
    
    def _get_raw_state_data(self, state: Any) -> Dict[str, Any]:
        """获取原始状态数据"""
        if hasattr(state, "to_dict"):
            return state.to_dict()
        
        return {
            "target": getattr(state, "target", ""),
            "task_id": getattr(state, "task_id", ""),
            "tool_results": getattr(state, "tool_results", {}),
            "vulnerabilities": getattr(state, "vulnerabilities", []),
            "target_context": getattr(state, "target_context", {}),
            "execution_history": getattr(state, "execution_history", []),
            "errors": getattr(state, "errors", []),
            "is_complete": getattr(state, "is_complete", False)
        }
    
    def generate_json_report(self, report_data: EnhancedReportData) -> str:
        """生成JSON格式报告"""
        report_dict = asdict(report_data)
        return json.dumps(report_dict, ensure_ascii=False, indent=2)
    
    def generate_html_report(self, report_data: EnhancedReportData) -> str:
        """生成HTML格式报告"""
        html_content = self._render_html_template(report_data)
        return html_content
    
    def _render_html_template(self, report_data: EnhancedReportData) -> str:
        """渲染HTML模板"""
        vulnerabilities_html = self._render_vulnerabilities_html(report_data.vulnerabilities)
        graph_flow_html = self._render_graph_flow_html(report_data.graph_flow)
        ai_analysis_html = self._render_ai_analysis_html(report_data.ai_analysis)
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_data.task_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .section {{ background: white; border-radius: 10px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .info-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
        .info-card h3 {{ color: #667eea; margin-bottom: 10px; font-size: 14px; }}
        .info-card .value {{ font-size: 18px; font-weight: bold; }}
        .vuln-item {{ border: 1px solid #eee; border-radius: 8px; padding: 20px; margin-bottom: 15px; }}
        .vuln-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 10px; }}
        .vuln-title {{ font-size: 18px; font-weight: bold; }}
        .vuln-severity {{ padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; }}
        .severity-critical {{ background: #c0392b; }}
        .severity-high {{ background: #e74c3c; }}
        .severity-medium {{ background: #f39c12; }}
        .severity-low {{ background: #3498db; }}
        .severity-info {{ background: #95a5a6; }}
        .timeline {{ position: relative; padding-left: 30px; }}
        .timeline::before {{ content: ''; position: absolute; left: 10px; top: 0; bottom: 0; width: 2px; background: #667eea; }}
        .timeline-item {{ position: relative; margin-bottom: 20px; }}
        .timeline-item::before {{ content: ''; position: absolute; left: -24px; top: 5px; width: 12px; height: 12px; border-radius: 50%; background: #667eea; }}
        .timeline-time {{ color: #666; font-size: 12px; }}
        .node-list {{ max-height: 400px; overflow-y: auto; }}
        .node-item {{ background: #f8f9fa; padding: 15px; margin-bottom: 10px; border-radius: 6px; font-family: monospace; font-size: 12px; }}
        .ai-analysis {{ background: #e8f4fd; border-left: 4px solid #3498db; padding: 20px; border-radius: 8px; }}
        .ai-analysis h3 {{ color: #3498db; margin-bottom: 15px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 {report_data.task_name}</h1>
            <p>任务ID: {report_data.task_id}</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="section">
            <h2>📋 基础元信息</h2>
            <div class="info-grid">
                <div class="info-card">
                    <h3>操作系统</h3>
                    <div class="value">{report_data.environment.os}</div>
                </div>
                <div class="info-card">
                    <h3>Python版本</h3>
                    <div class="value">{report_data.environment.python_version.split()[0]}</div>
                </div>
                <div class="info-card">
                    <h3>目标URL</h3>
                    <div class="value">{report_data.target.url}</div>
                </div>
                <div class="info-card">
                    <h3>总耗时</h3>
                    <div class="value">{report_data.timing.total_duration_ms:.0f}ms</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>⏱️ 执行时序信息</h2>
            <div class="info-grid">
                <div class="info-card">
                    <h3>开始时间</h3>
                    <div class="value">{report_data.timing.start_time}</div>
                </div>
                <div class="info-card">
                    <h3>结束时间</h3>
                    <div class="value">{report_data.timing.end_time}</div>
                </div>
            </div>
            <h3 style="margin-top: 20px;">模块耗时</h3>
            <div class="info-grid">
                {self._render_module_durations_html(report_data.timing.module_durations)}
            </div>
        </div>

        <div class="section">
            <h2>🔧 工具执行流程</h2>
            <div class="timeline">
                {self._render_tool_timeline_html(report_data.tool_execution_flow)}
            </div>
        </div>

        <div class="section">
            <h2>📊 图流程可视化</h2>
            {graph_flow_html}
        </div>

        <div class="section">
            <h2>📈 信息收集结果</h2>
            <div class="info-grid">
                <div class="info-card">
                    <h3>爬取链接数</h3>
                    <div class="value">{report_data.info_collection.crawler_links_count}</div>
                </div>
                <div class="info-card">
                    <h3>发现目录数</h3>
                    <div class="value">{report_data.info_collection.dirscan_count}</div>
                </div>
                <div class="info-card">
                    <h3>CMS识别</h3>
                    <div class="value">{report_data.info_collection.cms_identified or '未识别'}</div>
                </div>
                <div class="info-card">
                    <h3>WAF检测</h3>
                    <div class="value">{report_data.info_collection.waf_detected or '未检测到'}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🔍 扫描结果</h2>
            <p style="margin-bottom: 20px;">共发现 <strong>{len(report_data.vulnerabilities)}</strong> 个漏洞</p>
            {vulnerabilities_html}
        </div>

        <div class="section">
            <h2>🤖 AI模型信息</h2>
            <div class="info-grid">
                <div class="info-card">
                    <h3>模型名称</h3>
                    <div class="value">{report_data.ai_model.model_name}</div>
                </div>
                <div class="info-card">
                    <h3>部署方式</h3>
                    <div class="value">{report_data.ai_model.deployment_type}</div>
                </div>
                <div class="info-card">
                    <h3>温度参数</h3>
                    <div class="value">{report_data.ai_model.temperature}</div>
                </div>
                <div class="info-card">
                    <h3>调用次数</h3>
                    <div class="value">{report_data.ai_model.call_count}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🧠 AI结果分析</h2>
            {ai_analysis_html}
        </div>

        <div class="footer">
            <p>报告由 AI_WebSecurity 自动生成 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
    
    def _render_vulnerabilities_html(self, vulnerabilities: List[VulnerabilityItem]) -> str:
        """渲染漏洞列表HTML"""
        if not vulnerabilities:
            return "<p>未发现漏洞</p>"
        
        html = ""
        for vuln in vulnerabilities:
            severity_class = f"severity-{vuln.severity}"
            html += f"""
            <div class="vuln-item">
                <div class="vuln-header">
                    <span class="vuln-title">{vuln.vuln_name}</span>
                    <span class="vuln-severity {severity_class}">{SEVERITY_CONFIG.get(vuln.severity, {}).get('label', vuln.severity)}</span>
                </div>
                <p><strong>CVE:</strong> {vuln.cve_id or 'N/A'}</p>
                <p><strong>影响URL:</strong> {vuln.affected_url or 'N/A'}</p>
                <p><strong>描述:</strong> {vuln.description}</p>
                <p style="margin-top: 10px; padding: 10px; background: #e8f5e9; border-radius: 4px;">
                    <strong>修复建议:</strong> {vuln.remediation}
                </p>
            </div>
            """
        
        return html
    
    def _render_graph_flow_html(self, graph_flow: GraphFlowVisualization) -> str:
        """渲染图流程HTML"""
        html = ""
        
        for subgraph in graph_flow.subgraphs:
            html += f"""
            <div style="margin-bottom: 30px;">
                <h3 style="margin-bottom: 15px;">📦 子图: {subgraph.subgraph_name}</h3>
                <p style="margin-bottom: 10px; color: #666;">
                    状态: {subgraph.status} | 开始: {subgraph.start_time} | 结束: {subgraph.end_time}
                </p>
                <div class="node-list">
            """
            
            for node in subgraph.nodes:
                status_color = "#27ae60" if node.status == "success" else "#e74c3c"
                html += f"""
                <div class="node-item">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <strong>{node.node_name}</strong>
                        <span style="color: {status_color}; font-weight: bold;">{node.status}</span>
                    </div>
                    <div>执行时间: {node.execution_time_ms:.0f}ms</div>
                    <details style="margin-top: 8px;">
                        <summary>查看详情</summary>
                        <div style="margin-top: 8px;">
                            <div><strong>输入参数:</strong> {json.dumps(node.input_params, ensure_ascii=False)}</div>
                            <div style="margin-top: 5px;"><strong>输出数据:</strong> {json.dumps(node.output_data, ensure_ascii=False)}</div>
                            {f'<div style="margin-top: 5px; color: #e74c3c;"><strong>错误日志:</strong> {node.error_log}</div>' if node.error_log else ''}
                        </div>
                    </details>
                </div>
                """
            
            html += "</div></div>"
        
        return html
    
    def _render_ai_analysis_html(self, ai_analysis: AIResultAnalysis) -> str:
        """渲染AI分析HTML"""
        if not ai_analysis.vulnerability_causes and not ai_analysis.exploitation_risks:
            return "<p>暂无AI分析结果</p>"
        
        html = '<div class="ai-analysis">'
        
        if ai_analysis.vulnerability_causes:
            html += "<h3>🔍 漏洞成因分析</h3><ul>"
            for cause in ai_analysis.vulnerability_causes:
                html += f"<li>{cause}</li>"
            html += "</ul>"
        
        if ai_analysis.exploitation_risks:
            html += "<h3 style='margin-top: 20px;'>⚠️ 利用风险</h3><ul>"
            for risk in ai_analysis.exploitation_risks:
                html += f"<li>{risk}</li>"
            html += "</ul>"
        
        if ai_analysis.remediation_priorities:
            html += "<h3 style='margin-top: 20px;'>🎯 修复优先级</h3><ul>"
            for priority in ai_analysis.remediation_priorities:
                html += f"<li>{priority.get('vulnerability', '')}: 优先级 {priority.get('priority', '')}</li>"
            html += "</ul>"
        
        if ai_analysis.business_impact:
            html += f"<h3 style='margin-top: 20px;'>💼 业务影响评估</h3><p>{ai_analysis.business_impact}</p>"
        
        html += "</div>"
        return html
    
    def _render_tool_timeline_html(self, tool_flow: List[ToolExecutionStep]) -> str:
        """渲染工具时间线HTML"""
        html = ""
        for step in tool_flow:
            html += f"""
            <div class="timeline-item">
                <div class="timeline-time">{step.timestamp}</div>
                <div><strong>步骤 {step.step_number}:</strong> {step.tool_name}</div>
                <div style="color: #666; font-size: 13px; margin-top: 5px;">
                    触发条件: {step.trigger_condition}
                </div>
            </div>
            """
        return html
    
    def _render_module_durations_html(self, module_durations: Dict[str, float]) -> str:
        """渲染模块耗时HTML"""
        html = ""
        for module, duration in module_durations.items():
            html += f"""
            <div class="info-card">
                <h3>{module}</h3>
                <div class="value">{duration:.0f}ms</div>
            </div>
            """
        return html
    
    def save_report(
        self,
        report_data: EnhancedReportData,
        format: ReportFormat = ReportFormat.JSON,
        filename: Optional[str] = None
    ) -> str:
        """
        保存报告到文件
        
        Args:
            report_data: 报告数据
            format: 报告格式
            filename: 文件名（可选）
            
        Returns:
            str: 文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{report_data.task_id}_{timestamp}.{format.value}"
        
        filepath = self.output_dir / filename
        
        if format == ReportFormat.JSON:
            content = self.generate_json_report(report_data)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        elif format == ReportFormat.HTML:
            content = self.generate_html_report(report_data)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        elif format == ReportFormat.PDF:
            content = self.generate_html_report(report_data)
            try:
                import weasyprint
                weasyprint.HTML(string=content).write_pdf(filepath)
            except ImportError:
                logger.warning("WeasyPrint not available, saving as HTML instead")
                html_path = filepath.with_suffix(".html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return str(html_path)
        
        logger.info(f"📄 报告已保存: {filepath}")
        return str(filepath)


class ReportGenerator:
    """
    向后兼容的报告生成器适配器
    
    模拟旧版ReportGenerator API，内部使用新版EnhancedReportGenerator。
    用于确保现有代码无需修改即可继续工作。
    """
    
    def __init__(self, auto_ai_analysis: bool = False):
        """初始化兼容适配器"""
        self.enhanced_generator = EnhancedReportGenerator(auto_ai_analysis=auto_ai_analysis)
        logger.info("📄 兼容报告生成器初始化完成(使用新版增强版)")
    
    def generate_report(self, state: Any) -> Dict[str, Any]:
        """
        生成扫描报告(兼容旧版API)
        
        Args:
            state: Agent状态
            
        Returns:
            Dict: 扫描报告(旧版格式)
        """
        vulnerabilities = getattr(state, "vulnerabilities", [])
        tool_results = getattr(state, "tool_results", {})
        target_context = getattr(state, "target_context", {})
        execution_history = getattr(state, "execution_history", [])
        
        severity_counts = {}
        for vuln in vulnerabilities:
            sev = vuln.get("severity", vuln.get("risk_level", "unknown"))
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        target_url = getattr(state, "target", "")
        target_ip = target_context.get("ip", "") if target_context else ""
        target_domain = target_context.get("domain", "") if target_context else ""
        target_ports = target_context.get("open_ports", []) if target_context else []
        
        legacy_report = {
            "meta": {
                "version": "2.0",
                "generator": "AI_WebSecurity Report Engine",
                "generated_at": datetime.now().isoformat()
            },
            "task_id": getattr(state, "task_id", "unknown"),
            "target": target_url,
            "scan_time": datetime.now().isoformat(),
            "duration": 0,
            "status": "completed",
            "progress": 100,
            
            "tasks": {
                "planned": getattr(state, "planned_tasks", []),
                "completed": getattr(state, "completed_tasks", []),
                "total": len(getattr(state, "planned_tasks", []))
            },
            
            "target_context": {
                "ip": target_ip,
                "domain": target_domain,
                "open_ports": target_ports
            },
            
            "vulnerabilities": {
                "list": [
                    {
                        "title": vuln.get("title", vuln.get("name", "Unknown")),
                        "vuln_type": vuln.get("vuln_type", vuln.get("type", "unknown")),
                        "severity": vuln.get("severity", vuln.get("risk_level", "unknown")),
                        "cve": vuln.get("cve", ""),
                        "url": vuln.get("url", vuln.get("affected_url", "")),
                        "description": vuln.get("description", ""),
                        "remediation": vuln.get("remediation", vuln.get("solution", ""))
                    }
                    for vuln in vulnerabilities
                ],
                "total": len(vulnerabilities),
                "summary": self._generate_vuln_summary_legacy(vulnerabilities) if vulnerabilities else "未发现漏洞",
                "by_severity": severity_counts,
                "deduplication_policy": "Disabled (All findings reported)"
            },
            
            "risk_assessment": self._calculate_risk_assessment(state),
            "tool_results": self._summarize_tool_results_legacy(tool_results),
            "errors": getattr(state, "errors", []),
            "execution_history": execution_history,
            "recommendations": self._generate_recommendations_legacy(vulnerabilities) if vulnerabilities else [],
            "ai_analysis": self._extract_ai_analysis_from_state(state)
        }
        
        logger.info(f"📄 兼容扫描报告生成完成: {getattr(state, 'task_id', 'unknown')}")
        return legacy_report
    
    def _generate_vuln_summary_legacy(self, vulnerabilities: List[Any]) -> str:
        """生成漏洞摘要(兼容旧版)"""
        if not vulnerabilities:
            return "未发现漏洞"
        
        severity_count = {}
        for vuln in vulnerabilities:
            if hasattr(vuln, 'severity'):
                severity = vuln.severity
            else:
                severity = vuln.get("severity", vuln.get("risk_level", "unknown"))
            severity_count[severity] = severity_count.get(severity, 0) + 1
        
        parts = []
        for severity in ["critical", "high", "medium", "low"]:
            count = severity_count.get(severity, 0)
            if count > 0:
                config = SEVERITY_CONFIG.get(severity, {})
                parts.append(f"{config.get('label', severity)}: {count}")
        
        return "共发现 {} 个漏洞: {}".format(
            len(vulnerabilities),
            ", ".join(parts)
        )
    
    def _calculate_risk_assessment(self, state: Any) -> Dict[str, Any]:
        """计算风险评估"""
        vulnerabilities = getattr(state, "vulnerabilities", [])
        
        if not vulnerabilities:
            return {
                "score": 0.0,
                "level": "info",
                "label": "无风险",
                "color": "#95a5a6",
                "factors": []
            }
        
        base_score = 0.0
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for vuln in vulnerabilities:
            if isinstance(vuln, dict):
                severity = vuln.get("severity", vuln.get("risk_level", "info"))
            else:
                severity = getattr(vuln, "severity", "info")
            config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["info"])
            base_score += config["score"]
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        max_score = len(vulnerabilities) * 10.0
        normalized_score = (base_score / max_score * 10) if max_score > 0 else 0.0
        
        if normalized_score >= 8.0:
            level = "critical"
        elif normalized_score >= 6.0:
            level = "high"
        elif normalized_score >= 4.0:
            level = "medium"
        elif normalized_score >= 2.0:
            level = "low"
        else:
            level = "info"
        
        config = SEVERITY_CONFIG[level]
        factors = []
        
        if severity_counts["critical"] > 0:
            factors.append(f"发现{severity_counts['critical']}个严重漏洞")
        if severity_counts["high"] > 0:
            factors.append(f"发现{severity_counts['high']}个高危漏洞")
        
        return {
            "score": round(normalized_score, 1),
            "level": level,
            "label": config["label"],
            "color": config["color"],
            "factors": factors,
            "severity_counts": severity_counts
        }
    
    def _summarize_tool_results_legacy(self, tool_results: Dict[str, Any]) -> Dict[str, Any]:
        """汇总工具结果(兼容旧版)"""
        return {
            "info_collection": {
                "crawler_links_count": len(tool_results.get("crawler_links", [])),
                "dirscan_count": len(tool_results.get("dirscan_results", [])),
                "cms_identified": tool_results.get("cms", ""),
                "open_ports": tool_results.get("open_ports", []),
                "waf_detected": tool_results.get("waf", "")
            }
        }
    
    def _extract_ai_analysis_from_state(self, state: Any) -> Dict[str, Any]:
        """从状态中提取AI分析结果"""
        ai_analysis = getattr(state, "ai_analysis", None)
        
        if ai_analysis and isinstance(ai_analysis, dict):
            return {
                "vulnerability_causes": ai_analysis.get("vulnerability_causes", ""),
                "exploitation_risks": ai_analysis.get("exploitation_risks", ""),
                "remediation_priorities": ai_analysis.get("remediation_priorities", []),
                "business_impact": ai_analysis.get("business_impact", ""),
                "analysis_evidence": ai_analysis.get("analysis_evidence", [])
            }
        
        vulnerabilities = getattr(state, "vulnerabilities", [])
        tool_results = getattr(state, "tool_results", {})
        target_context = getattr(state, "target_context", {})
        
        causes = []
        risks = []
        priorities = []
        
        for vuln in vulnerabilities:
            if isinstance(vuln, dict):
                vuln_type = vuln.get("vuln_type", vuln.get("type", "unknown"))
                severity = vuln.get("severity", vuln.get("risk_level", "unknown"))
                title = vuln.get("title", vuln.get("name", "Unknown"))
                
                causes.append(f"{title}: 可能存在{vuln_type}漏洞")
                
                if severity in ["critical", "high"]:
                    risks.append(f"{title}: 高风险漏洞，可能被攻击者利用")
                    priorities.append({"vulnerability": title, "priority": "高", "severity": severity})
                elif severity == "medium":
                    risks.append(f"{title}: 中等风险，建议及时修复")
                    priorities.append({"vulnerability": title, "priority": "中", "severity": severity})
        
        return {
            "vulnerability_causes": "; ".join(causes) if causes else "未发现明显漏洞原因",
            "exploitation_risks": "; ".join(risks) if risks else "当前未发现高风险漏洞",
            "remediation_priorities": priorities,
            "business_impact": "建议根据漏洞严重程度制定修复计划，优先处理高危漏洞" if priorities else "当前安全状况良好",
            "analysis_evidence": ["基于漏洞扫描结果的规则分析"]
        }
    

    
    def _generate_recommendations_legacy(self, vulnerabilities: List[Any]) -> List[Dict[str, str]]:
        """生成修复建议列表(兼容旧版)"""
        recommendations = []
        
        severity_order = {s: c["order"] for s, c in SEVERITY_CONFIG.items()}
        
        def get_severity(vuln):
            if hasattr(vuln, 'severity'):
                return vuln.severity
            return vuln.get("severity", vuln.get("risk_level", "info"))
        
        def get_remediation(vuln):
            if hasattr(vuln, 'remediation'):
                return vuln.remediation
            return vuln.get("remediation", vuln.get("solution", ""))
        
        def get_vuln_name(vuln):
            if hasattr(vuln, 'vuln_name'):
                return vuln.vuln_name
            return vuln.get("title", vuln.get("name", "Unknown"))
        
        sorted_vulns = sorted(vulnerabilities, key=lambda v: severity_order.get(get_severity(v), 4))
        
        for vuln in sorted_vulns[:10]:
            remediation = get_remediation(vuln)
            if remediation:
                recommendations.append({
                    "vulnerability": get_vuln_name(vuln),
                    "severity": get_severity(vuln),
                    "recommendation": remediation
                })
        
        return recommendations
    
    def generate_html_report(self, state: Any) -> str:
        """
        生成HTML格式报告(兼容旧版API)
        
        Args:
            state: Agent状态
            
        Returns:
            str: HTML报告
        """
        report_data = self.enhanced_generator.generate_from_state_sync(
            state,
            task_name=f"安全扫描 - {state.target}"
        )
        return self.enhanced_generator.generate_html_report(report_data)
    
    def generate_json_report(self, state: Any) -> str:
        """
        生成JSON格式报告(兼容旧版API)
        
        Args:
            state: Agent状态
            
        Returns:
            str: JSON报告
        """
        report_data = self.enhanced_generator.generate_from_state_sync(
            state,
            task_name=f"安全扫描 - {state.target}"
        )
        return self.enhanced_generator.generate_json_report(report_data)
    
    def generate_report_by_format(self, state: Any, format: str = "json") -> str:
        """
        根据格式生成报告(兼容旧版API)
        
        Args:
            state: Agent状态
            format: 报告格式 (json, html, markdown, pdf)
            
        Returns:
            str: 报告内容
        """
        format = format.lower()
        
        generators = {
            "json": self.generate_json_report,
            "html": self.generate_html_report,
            "markdown": self.generate_json_report,
            "pdf": self.generate_html_report
        }
        
        generator = generators.get(format, self.generate_json_report)
        return generator(state)
    
    def generate_execution_trace_report(self, state: Any) -> Dict[str, Any]:
        """
        生成执行轨迹报告(兼容旧版API)
        
        Args:
            state: Agent状态
            
        Returns:
            Dict: 执行轨迹报告
        """
        report_data = self.enhanced_generator.generate_from_state_sync(
            state,
            task_name=f"安全扫描 - {state.target}"
        )
        
        return {
            "task_id": report_data.task_id,
            "execution_history": report_data.raw_data.get("execution_history", []),
            "tool_flow": [
                {
                    "step_number": step.step_number,
                    "tool_name": step.tool_name,
                    "timestamp": step.timestamp
                }
                for step in report_data.tool_execution_flow
            ],
            "graph_flow": {
                "subgraphs": [
                    {
                        "subgraph_id": sg.subgraph_id,
                        "subgraph_name": sg.subgraph_name,
                        "nodes": [
                            {
                                "node_id": n.node_id,
                                "node_name": n.node_name,
                                "status": n.status
                            }
                            for n in sg.nodes
                        ]
                    }
                    for sg in report_data.graph_flow.subgraphs
                ]
            }
        }
    
    def generate_html_execution_trace(self, state: Any) -> str:
        """
        生成HTML执行轨迹(兼容旧版API)
        
        Args:
            state: Agent状态
            
        Returns:
            str: HTML执行轨迹
        """
        return self.generate_html_report(state)
    
    def generate_markdown_report(self, state: Any) -> str:
        """
        生成Markdown格式报告(兼容旧版API)
        
        Args:
            state: Agent状态
            
        Returns:
            str: Markdown报告
        """
        return self.generate_json_report(state)

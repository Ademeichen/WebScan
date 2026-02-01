"""
报告生成器

生成标准化的扫描报告。
"""
import logging
from datetime import datetime
from typing import Any, Dict, List


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    报告生成器
    
    负责生成标准化的扫描报告。
    """
    
    def __init__(self):
        logger.info("📄 报告生成器初始化完成")
    
    def generate_report(self, state: Any) -> Dict[str, Any]:
        """
        生成扫描报告
        
        Args:
            state: Agent状态
            
        Returns:
            Dict: 扫描报告
        """
        report = {
            "task_id": state.task_id,
            "target": state.target,
            "scan_time": datetime.now().isoformat(),
            "duration": self._calculate_duration(state),
            "status": "completed" if state.is_complete else "failed",
            "progress": state.get_progress(),
            
            # 任务信息
            "tasks": {
                "planned": state.planned_tasks,
                "completed": state.completed_tasks,
                "total": len(state.planned_tasks) + len(state.completed_tasks)
            },
            
            # 目标上下文
            "target_context": state.target_context,
            
            # 漏洞信息
            "vulnerabilities": {
                "list": state.vulnerabilities,
                "total": len(state.vulnerabilities),
                "summary": self._generate_vuln_summary(state.vulnerabilities)
            },
            
            # 工具结果
            "tool_results": self._summarize_tool_results(state.tool_results),
            
            # 错误信息
            "errors": state.errors,
            
            # 执行历史
            "execution_history": state.execution_history
        }
        
        logger.info(f"📄 扫描报告生成完成: {report['task_id']}")
        return report
    
    def generate_html_report(self, state: Any) -> str:
        """
        生成HTML格式报告
        
        Args:
            state: Agent状态
            
        Returns:
            str: HTML报告
        """
        report_data = self.generate_report(state)
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web安全扫描报告 - {state.target}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .vulnerability {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .vulnerability.critical {{ border-left: 5px solid #dc3545; }}
        .vulnerability.high {{ border-left: 5px solid #fd7e14; }}
        .vulnerability.medium {{ border-left: 5px solid #ffc107; }}
        .vulnerability.low {{ border-left: 5px solid #28a745; }}
        .severity {{ font-weight: bold; text-transform: uppercase; }}
        .summary {{ background: #e9ecef; padding: 15px; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        table th, table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        table th {{ background: #007bff; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Web安全扫描报告</h1>
        <p><strong>目标:</strong> {state.target}</p>
        <p><strong>扫描时间:</strong> {report_data['scan_time']}</p>
        <p><strong>任务ID:</strong> {state.task_id}</p>
        <p><strong>状态:</strong> {report_data['status']}</p>
    </div>
    
    <div class="section">
        <h2>扫描摘要</h2>
        <div class="summary">
            <p>{report_data['vulnerabilities']['summary']}</p>
            <p><strong>任务进度:</strong> {report_data['progress']:.1f}%</p>
            <p><strong>已完成任务:</strong> {len(report_data['tasks']['completed'])}/{report_data['tasks']['total']}</p>
        </div>
    </div>
    
    <div class="section">
        <h2>目标信息</h2>
        <table>
            <tr><th>项目</th><th>信息</th></tr>
            {self._generate_context_rows(state.target_context)}
        </table>
    </div>
    
    <div class="section">
        <h2>漏洞详情</h2>
        {self._generate_vuln_rows(state.vulnerabilities)}
    </div>
    
    <div class="section">
        <h2>工具执行结果</h2>
        {self._generate_tool_rows(state.tool_results)}
    </div>
    
    {self._generate_error_section(state.errors)}
</body>
</html>
        """
        
        return html
    
    def _calculate_duration(self, state: Any) -> float:
        """
        计算扫描持续时间
        
        Args:
            state: Agent状态
            
        Returns:
            float: 持续时间(秒)
        """
        if not state.execution_history:
            return 0.0
        
        start_time = state.execution_history[0].get("timestamp", 0)
        end_time = state.execution_history[-1].get("timestamp", 0)
        
        if start_time is None or end_time is None:
            return 0.0
        
        try:
            return float(end_time) - float(start_time)
        except (TypeError, ValueError):
            return 0.0
    
    def _generate_vuln_summary(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """
        生成漏洞摘要
        
        Args:
            vulnerabilities: 漏洞列表
            
        Returns:
            str: 摘要文本
        """
        if not vulnerabilities:
            return "未发现漏洞"
        
        severity_count = {}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info")
            severity_count[severity] = severity_count.get(severity, 0) + 1
        
        parts = []
        for severity in ["critical", "high", "medium", "low"]:
            count = severity_count.get(severity, 0)
            if count > 0:
                parts.append(f"{severity.capitalize()}: {count}")
        
        return "共发现 {} 个漏洞: {}".format(
            len(vulnerabilities),
            ", ".join(parts)
        )
    
    def _summarize_tool_results(self, tool_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        汇总工具结果
        
        Args:
            tool_results: 工具结果字典
            
        Returns:
            Dict: 汇总结果
        """
        summary = {
            "total": len(tool_results),
            "success": 0,
            "failed": 0,
            "timeout": 0,
            "details": {}
        }
        
        for tool_name, result in tool_results.items():
            status = result.get("status", "unknown")
            if status == "success":
                summary["success"] += 1
            elif status == "failed":
                summary["failed"] += 1
            elif status == "timeout":
                summary["timeout"] += 1
            
            summary["details"][tool_name] = {
                "status": status,
                "has_data": "data" in result
            }
        
        return summary
    
    def _generate_context_rows(self, context: Dict[str, Any]) -> str:
        """
        生成上下文表格行
        
        Args:
            context: 上下文字典
            
        Returns:
            str: HTML表格行
        """
        rows = []
        for key, value in context.items():
            if value:
                display_value = str(value)
                if isinstance(value, list):
                    display_value = ", ".join(str(v) for v in value)
                rows.append(f"<tr><td>{key}</td><td>{display_value}</td></tr>")
        
        return "\n".join(rows)
    
    def _generate_vuln_rows(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """
        生成漏洞HTML行
        
        Args:
            vulnerabilities: 漏洞列表
            
        Returns:
            str: HTML漏洞行
        """
        if not vulnerabilities:
            return "<p>未发现漏洞</p>"
        
        rows = []
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info")
            rows.append(f"""
    <div class="vulnerability {severity}">
        <p><strong>CVE:</strong> {vuln.get('cve', 'N/A')}</p>
        <p><strong>严重度:</strong> <span class="severity">{severity}</span></p>
        <p><strong>详情:</strong> {vuln.get('details', 'N/A')}</p>
        {f"<p><strong>修复建议:</strong> {vuln.get('fix_suggestion', 'N/A')}</p>" if vuln.get('fix_suggestion') else ''}
    </div>
            """)
        
        return "\n".join(rows)
    
    def _generate_tool_rows(self, tool_results: Dict[str, Any]) -> str:
        """
        生成工具结果HTML行
        
        Args:
            tool_results: 工具结果字典
            
        Returns:
            str: HTML工具行
        """
        rows = []
        for tool_name, result in tool_results.items():
            status = result.get("status", "unknown")
            status_color = {
                "success": "#28a745",
                "failed": "#dc3545",
                "timeout": "#ffc107"
            }.get(status, "#6c757d")
            
            rows.append(f"""
    <tr>
        <td>{tool_name}</td>
        <td style="color: {status_color}; font-weight: bold;">{status.upper()}</td>
        <td>{'是' if result.get('data') else '否'}</td>
    </tr>
            """)
        
        return "\n".join(rows)
    
    def _generate_error_section(self, errors: List[str]) -> str:
        """
        生成错误部分
        
        Args:
            errors: 错误列表
            
        Returns:
            str: HTML错误部分
        """
        if not errors:
            return ""
        
        error_rows = "\n".join([f"<li>{error}</li>" for error in errors])
        return f"""
    <div class="section">
        <h2>执行错误</h2>
        <ul style="color: #dc3545;">
            {error_rows}
        </ul>
    </div>
        """
    
    def generate_execution_trace_report(self, state: Any) -> Dict[str, Any]:
        """
        生成详细的执行轨迹报告
        
        Args:
            state: Agent状态
            
        Returns:
            Dict: 执行轨迹报告
        """
        try:
            trace_report = {
                "task_id": state.task_id,
                "target": state.target,
                "scan_time": datetime.now().isoformat(),
                "total_steps": len(state.execution_history),
                "total_duration": self._calculate_duration(state),
                "execution_trace": self._generate_detailed_trace(state.execution_history) if state.execution_history else [],
                "trace_summary": self._generate_trace_summary(state.execution_history) if state.execution_history else {
                    "total_steps": 0,
                    "successful_steps": 0,
                    "failed_steps": 0,
                    "running_steps": 0,
                    "pending_steps": 0,
                    "total_execution_time": 0.0,
                    "average_execution_time": 0.0
                },
                "state_changes": self._generate_state_changes(state.execution_history) if state.execution_history else [],
                "performance_metrics": self._generate_performance_metrics(state.execution_history) if state.execution_history else {
                    "throughput": 0.0,
                    "success_rate": 0.0,
                    "failure_rate": 0.0,
                    "steps_per_second": 0.0,
                    "average_step_duration": 0.0
                }
            }
            
            logger.info(f"📄 执行轨迹报告生成完成: {trace_report['task_id']}")
            return trace_report
        except Exception as e:
            logger.error(f"生成执行轨迹报告失败: {str(e)}")
            return {
                "task_id": getattr(state, 'task_id', 'unknown'),
                "target": getattr(state, 'target', 'unknown'),
                "scan_time": datetime.now().isoformat(),
                "total_steps": 0,
                "total_duration": 0.0,
                "execution_trace": [],
                "trace_summary": {
                    "total_steps": 0,
                    "successful_steps": 0,
                    "failed_steps": 0,
                    "running_steps": 0,
                    "pending_steps": 0,
                    "total_execution_time": 0.0,
                    "average_execution_time": 0.0
                },
                "state_changes": [],
                "performance_metrics": {
                    "throughput": 0.0,
                    "success_rate": 0.0,
                    "failure_rate": 0.0,
                    "steps_per_second": 0.0,
                    "average_step_duration": 0.0
                }
            }
    
    def _generate_detailed_trace(self, execution_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        生成详细的执行轨迹
        
        Args:
            execution_history: 执行历史记录
            
        Returns:
            List[Dict]: 详细轨迹列表
        """
        detailed_trace = []
        
        for step in execution_history:
            trace_entry = {
                "step_number": step.get("step_number", 0),
                "timestamp": step.get("timestamp_iso", ""),
                "task": step.get("task", ""),
                "step_type": step.get("step_type", "unknown"),
                "status": step.get("status", "unknown"),
                "execution_time": step.get("execution_time", 0),
                
                # 输入参数
                "input_parameters": step.get("input_params", {}),
                
                # 处理逻辑
                "processing_logic": step.get("processing_logic", ""),
                
                # 中间结果
                "intermediate_results": step.get("intermediate_results", []),
                
                # 输出数据
                "output_data": step.get("output_data", {}),
                
                # 最终结果
                "final_result": step.get("result", {}),
                
                # 数据变化
                "data_changes": step.get("data_changes", {}),
                
                # 状态转换
                "state_transitions": step.get("state_transitions", []),
                
                # 状态快照
                "state_snapshot": step.get("state_snapshot", {})
            }
            
            detailed_trace.append(trace_entry)
        
        return detailed_trace
    
    def _generate_trace_summary(self, execution_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成轨迹摘要
        
        Args:
            execution_history: 执行历史记录
            
        Returns:
            Dict: 轨迹摘要
        """
        summary = {
            "total_steps": len(execution_history),
            "successful_steps": 0,
            "failed_steps": 0,
            "running_steps": 0,
            "pending_steps": 0,
            "step_types": {},
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "min_execution_time": float('inf'),
            "max_execution_time": 0.0
        }
        
        execution_times = []
        
        for step in execution_history:
            status = step.get("status", "unknown")
            
            # 统计状态
            if status == "success":
                summary["successful_steps"] += 1
            elif status == "failed":
                summary["failed_steps"] += 1
            elif status == "running":
                summary["running_steps"] += 1
            elif status == "pending":
                summary["pending_steps"] += 1
            
            # 统计步骤类型
            step_type = step.get("step_type", "unknown")
            summary["step_types"][step_type] = summary["step_types"].get(step_type, 0) + 1
            
            # 统计执行时间
            execution_time = step.get("execution_time")
            if execution_time is not None and execution_time > 0:
                execution_times.append(execution_time)
                summary["total_execution_time"] += execution_time
                summary["min_execution_time"] = min(summary["min_execution_time"], execution_time)
                summary["max_execution_time"] = max(summary["max_execution_time"], execution_time)
        
        # 计算平均执行时间
        if execution_times:
            summary["average_execution_time"] = summary["total_execution_time"] / len(execution_times)
        else:
            summary["min_execution_time"] = 0.0
        
        return summary
    
    def _generate_state_changes(self, execution_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        生成状态变化记录
        
        Args:
            execution_history: 执行历史记录
            
        Returns:
            List[Dict]: 状态变化列表
        """
        state_changes = []
        
        for step in execution_history:
            step_number = step.get("step_number", 0)
            task = step.get("task", "")
            timestamp = step.get("timestamp_iso", "")
            data_changes = step.get("data_changes", {})
            state_transitions = step.get("state_transitions", [])
            state_snapshot = step.get("state_snapshot", {})
            
            if data_changes or state_transitions:
                change_entry = {
                    "step_number": step_number,
                    "task": task,
                    "timestamp": timestamp,
                    "data_changes": data_changes,
                    "state_transitions": state_transitions,
                    "state_snapshot": state_snapshot
                }
                state_changes.append(change_entry)
        
        return state_changes
    
    def _generate_performance_metrics(self, execution_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成性能指标
        
        Args:
            execution_history: 执行历史记录
            
        Returns:
            Dict: 性能指标
        """
        metrics = {
            "throughput": 0.0,
            "success_rate": 0.0,
            "failure_rate": 0.0,
            "steps_per_second": 0.0,
            "average_step_duration": 0.0
        }
        
        if not execution_history:
            return metrics
        
        total_steps = len(execution_history)
        successful_steps = sum(1 for step in execution_history if step.get("status") == "success")
        
        # 计算成功率
        metrics["success_rate"] = (successful_steps / total_steps * 100) if total_steps > 0 else 0.0
        metrics["failure_rate"] = 100.0 - metrics["success_rate"]
        
        # 计算总执行时间
        total_time = self._calculate_total_time(execution_history)
        
        if total_time > 0:
            metrics["steps_per_second"] = total_steps / total_time
            metrics["throughput"] = successful_steps / total_time
        
        # 计算平均步骤持续时间
        execution_times = [step.get("execution_time", 0) for step in execution_history if step.get("execution_time") is not None and step.get("execution_time", 0) > 0]
        if execution_times:
            metrics["average_step_duration"] = sum(execution_times) / len(execution_times)
        
        return metrics
    
    def _calculate_total_time(self, execution_history: List[Dict[str, Any]]) -> float:
        """
        计算总执行时间
        
        Args:
            execution_history: 执行历史记录
            
        Returns:
            float: 总执行时间（秒）
        """
        if not execution_history:
            return 0.0
        
        start_time = execution_history[0].get("timestamp", 0)
        end_time = execution_history[-1].get("timestamp", 0)
        
        if start_time is None or end_time is None:
            return 0.0
        
        try:
            return float(end_time) - float(start_time)
        except (TypeError, ValueError):
            return 0.0
    
    def generate_html_execution_trace(self, state: Any) -> str:
        """
        生成HTML格式的执行轨迹报告
        
        Args:
            state: Agent状态
            
        Returns:
            str: HTML执行轨迹报告
        """
        try:
            trace_report = self.generate_execution_trace_report(state)
        except Exception as e:
            logger.error(f"生成执行轨迹报告失败: {str(e)}")
            trace_report = {
                "task_id": state.task_id,
                "target": state.target,
                "scan_time": datetime.now().isoformat(),
                "total_steps": 0,
                "total_duration": 0.0,
                "execution_trace": [],
                "trace_summary": {
                    "total_steps": 0,
                    "successful_steps": 0,
                    "failed_steps": 0,
                    "running_steps": 0,
                    "pending_steps": 0,
                    "total_execution_time": 0.0,
                    "average_execution_time": 0.0
                },
                "state_changes": [],
                "performance_metrics": {
                    "throughput": 0.0,
                    "success_rate": 0.0,
                    "failure_rate": 0.0,
                    "steps_per_second": 0.0,
                    "average_step_duration": 0.0
                }
            }
        
        total_duration = trace_report.get('total_duration', 0.0) or 0.0
        total_steps = trace_report.get('total_steps', 0) or 0
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent执行轨迹报告 - {state.target}</title>
    <style>
        body {{ font-family: 'Courier New', monospace; line-height: 1.6; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0 0 10px 0; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{ color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
        .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
        .card h3 {{ margin: 0 0 10px 0; color: #667eea; font-size: 14px; }}
        .card .value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .trace-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 12px; }}
        .trace-table th {{ background: #667eea; color: white; padding: 12px; text-align: left; font-weight: bold; }}
        .trace-table td {{ padding: 10px; border-bottom: 1px solid #ddd; vertical-align: top; }}
        .trace-table tr:hover {{ background: #f5f5f5; }}
        .status-success {{ color: #28a745; font-weight: bold; }}
        .status-failed {{ color: #dc3545; font-weight: bold; }}
        .status-running {{ color: #ffc107; font-weight: bold; }}
        .step-type {{ padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        .type-tool {{ background: #e3f2fd; color: #1976d2; }}
        .type-code {{ background: #fce4ec; color: #c2185b; }}
        .type-execution {{ background: #fff3e0; color: #f57c00; }}
        .type-enhancement {{ background: #e8f5e9; color: #388e3c; }}
        .type-verification {{ background: #f3e5f5; color: #7b1fa2; }}
        .type-analysis {{ background: #ffebee; color: #d32f2f; }}
        .data-changes {{ background: #fff9c4; padding: 10px; border-radius: 4px; margin-top: 10px; }}
        .state-transitions {{ background: #e1f5fe; padding: 10px; border-radius: 4px; margin-top: 10px; }}
        .json-display {{ background: #f5f5f5; padding: 10px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 11px; max-height: 200px; overflow-y: auto; }}
        .timestamp {{ color: #666; font-size: 11px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Agent执行轨迹报告</h1>
            <p><strong>目标:</strong> {state.target}</p>
            <p><strong>任务ID:</strong> {state.task_id}</p>
            <p><strong>扫描时间:</strong> {trace_report['scan_time']}</p>
            <p><strong>总步骤:</strong> {total_steps}</p>
            <p><strong>总耗时:</strong> {total_duration:.2f}秒</p>
        </div>
        
        <div class="section">
            <h2>📊 执行摘要</h2>
            <div class="summary-cards">
                <div class="card">
                    <h3>总步骤</h3>
                    <div class="value">{trace_report['trace_summary']['total_steps']}</div>
                </div>
                <div class="card">
                    <h3>成功步骤</h3>
                    <div class="value status-success">{trace_report['trace_summary']['successful_steps']}</div>
                </div>
                <div class="card">
                    <h3>失败步骤</h3>
                    <div class="value status-failed">{trace_report['trace_summary']['failed_steps']}</div>
                </div>
                <div class="card">
                    <h3>总耗时</h3>
                    <div class="value">{trace_report['trace_summary']['total_execution_time'] or 0:.2f}s</div>
                </div>
                <div class="card">
                    <h3>平均耗时</h3>
                    <div class="value">{trace_report['trace_summary']['average_execution_time'] or 0:.2f}s</div>
                </div>
                <div class="card">
                    <h3>成功率</h3>
                    <div class="value">{trace_report['trace_summary']['successful_steps']}/{trace_report['trace_summary']['total_steps']}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 性能指标</h2>
            <table class="trace-table">
                <tr>
                    <th>指标</th>
                    <th>值</th>
                </tr>
                <tr>
                    <td>成功率</td>
                    <td>{trace_report['performance_metrics']['success_rate'] or 0:.2f}%</td>
                </tr>
                <tr>
                    <td>失败率</td>
                    <td>{trace_report['performance_metrics']['failure_rate'] or 0:.2f}%</td>
                </tr>
                <tr>
                    <td>吞吐量（成功步骤/秒）</td>
                    <td>{trace_report['performance_metrics']['throughput'] or 0:.4f}</td>
                </tr>
                <tr>
                    <td>步骤/秒</td>
                    <td>{trace_report['performance_metrics']['steps_per_second'] or 0:.4f}</td>
                </tr>
                <tr>
                    <td>平均步骤持续时间</td>
                    <td>{trace_report['performance_metrics']['average_step_duration'] or 0:.2f}s</td>
                </tr>
            </table>
        </div>
        
        <div class="section">
            <h2>📋 详细执行轨迹</h2>
            <table class="trace-table">
                <thead>
                    <tr>
                        <th>步骤</th>
                        <th>时间戳</th>
                        <th>任务</th>
                        <th>类型</th>
                        <th>状态</th>
                        <th>耗时</th>
                        <th>输入参数</th>
                        <th>输出数据</th>
                        <th>数据变化</th>
                        <th>状态转换</th>
                    </tr>
                </thead>
                <tbody>
                    {self._generate_trace_rows(trace_report['execution_trace'])}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>🔄 状态变化记录</h2>
            {self._generate_state_changes_rows(trace_report['state_changes'])}
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def _generate_trace_rows(self, execution_trace: List[Dict[str, Any]]) -> str:
        """
        生成轨迹表格行
        
        Args:
            execution_trace: 执行轨迹
            
        Returns:
            str: HTML表格行
        """
        rows = []
        
        for step in execution_trace:
            step_number = step.get("step_number", 0)
            timestamp = step.get("timestamp", "")
            task = step.get("task", "")
            step_type = step.get("step_type", "unknown")
            status = step.get("status", "unknown")
            execution_time = step.get("execution_time") or 0
            input_params = step.get("input_parameters", {})
            output_data = step.get("output_data", {})
            data_changes = step.get("data_changes", {})
            state_transitions = step.get("state_transitions", [])
            
            # 状态样式
            status_class = {
                "success": "status-success",
                "failed": "status-failed",
                "running": "status-running"
            }.get(status, "")
            
            # 步骤类型样式
            type_class = {
                "tool_execution": "type-tool",
                "code_generation": "type-code",
                "code_execution": "type-execution",
                "capability_enhancement": "type-enhancement",
                "verification": "type-verification",
                "analysis": "type-analysis"
            }.get(step_type, "")
            
            # 格式化输入参数
            input_html = self._format_json(input_params)
            
            # 格式化输出数据
            output_html = self._format_json(output_data)
            
            # 格式化数据变化
            changes_html = self._format_json(data_changes) if data_changes else "-"
            
            # 格式化状态转换
            transitions_html = ", ".join(state_transitions) if state_transitions else "-"
            
            rows.append(f"""
                <tr>
                    <td>{step_number}</td>
                    <td class="timestamp">{timestamp}</td>
                    <td>{task}</td>
                    <td><span class="step-type {type_class}">{step_type}</span></td>
                    <td class="{status_class}">{status.upper()}</td>
                    <td>{execution_time:.2f}s</td>
                    <td><div class="json-display">{input_html}</div></td>
                    <td><div class="json-display">{output_html}</div></td>
                    <td><div class="json-display">{changes_html}</div></td>
                    <td>{transitions_html}</td>
                </tr>
            """)
        
        return "\n".join(rows)
    
    def _generate_state_changes_rows(self, state_changes: List[Dict[str, Any]]) -> str:
        """
        生成状态变化表格行
        
        Args:
            state_changes: 状态变化列表
            
        Returns:
            str: HTML表格行
        """
        if not state_changes:
            return "<p>无状态变化记录</p>"
        
        rows = []
        for change in state_changes:
            step_number = change.get("step_number", 0)
            task = change.get("task", "")
            timestamp = change.get("timestamp", "")
            data_changes = change.get("data_changes", {})
            state_transitions = change.get("state_transitions", [])
            state_snapshot = change.get("state_snapshot", {})
            
            rows.append(f"""
                <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <h4 style="margin: 0 0 10px 0; color: #667eea;">步骤 {step_number}: {task}</h4>
                    <p class="timestamp">时间: {timestamp}</p>
                    
                    {f'<div class="data-changes"><strong>数据变化:</strong><br>{self._format_json(data_changes)}</div>' if data_changes else ''}
                    
                    {f'<div class="state-transitions"><strong>状态转换:</strong> {", ".join(state_transitions)}</div>' if state_transitions else ''}
                    
                    {f'<div class="json-display"><strong>状态快照:</strong><br>{self._format_json(state_snapshot)}</div>' if state_snapshot else ''}
                </div>
            """)
        
        return "\n".join(rows)
    
    def _format_json(self, data: Any) -> str:
        """
        格式化JSON数据
        
        Args:
            data: 要格式化的数据
            
        Returns:
            str: 格式化的HTML
        """
        import json
        try:
            if not data:
                return "-"
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            return f"<pre>{json_str}</pre>"
        except:
            return str(data)

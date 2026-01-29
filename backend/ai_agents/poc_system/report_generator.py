"""
报告生成器

负责生成 POC 验证报告，支持 HTML、JSON、PDF 等多种格式。
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from backend.models import POCVerificationTask, POCVerificationResult
from backend.ai_agents.poc_system.result_analyzer import BatchAnalysisSummary

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    报告生成器类
    
    负责生成 POC 验证报告，包括：
    - HTML 格式报告（带图表）
    - JSON 格式报告（结构化数据）
    - PDF 格式报告（可打印）
    - 执行摘要生成
    - 漏洞详情列表
    - 统计信息
    """
    
    def __init__(self):
        """
        初始化报告生成器
        """
        self.report_templates = {
            "html": self._generate_html_report,
            "json": self._generate_json_report,
            "pdf": self._generate_pdf_report
        }
        
        logger.info("✅ 报告生成器初始化完成")
    
    async def generate_report(
        self,
        verification_task: POCVerificationTask,
        format: str = "html",
        output_path: Optional[str] = None
    ) -> str:
        """
        生成 POC 验证报告
        
        Args:
            verification_task: POC 验证任务对象
            format: 报告格式（html, json, pdf）
            output_path: 输出文件路径，None 则返回内容
            
        Returns:
            str: 报告内容或文件路径
        """
        logger.info(f"📄 开始生成报告，格式: {format}, 任务: {verification_task.poc_name}")
        
        # 获取验证结果
        results = await POCVerificationResult.filter(
            verification_task=verification_task.id
        ).order_by("-created_at")
        
        # 生成报告
        if format not in self.report_templates:
            raise ValueError(f"不支持的报告格式: {format}")
        
        report_content = await self.report_templates[format](
            verification_task,
            results
        )
        
        # 保存到文件或返回内容
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"✅ 报告已保存: {output_path}")
            return output_path
        else:
            return report_content
    
    async def generate_batch_report(
        self,
        verification_tasks: List[POCVerificationTask],
        format: str = "html",
        output_path: Optional[str] = None
    ) -> str:
        """
        生成批量 POC 验证报告
        
        Args:
            verification_tasks: POC 验证任务列表
            format: 报告格式（html, json, pdf）
            output_path: 输出文件路径，None 则返回内容
            
        Returns:
            str: 报告内容或文件路径
        """
        logger.info(f"📄 开始生成批量报告，格式: {format}, 任务数: {len(verification_tasks)}")
        
        # 获取所有验证结果
        all_results = []
        for task in verification_tasks:
            results = await POCVerificationResult.filter(
                verification_task=task.id
            ).order_by("-created_at")
            all_results.extend(results)
        
        # 生成报告
        if format not in self.report_templates:
            raise ValueError(f"不支持的报告格式: {format}")
        
        report_content = await self.report_templates[format](
            verification_tasks,
            all_results,
            is_batch=True
        )
        
        # 保存到文件或返回内容
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"✅ 批量报告已保存: {output_path}")
            return output_path
        else:
            return report_content
    
    async def _generate_html_report(
        self,
        task_or_tasks: Any,
        results: List[POCVerificationResult],
        is_batch: bool = False
    ) -> str:
        """
        生成 HTML 格式报告
        
        Args:
            task_or_tasks: 单个任务或任务列表
            results: 验证结果列表
            is_batch: 是否为批量报告
            
        Returns:
            str: HTML 报告内容
        """
        if is_batch:
            tasks = task_or_tasks
            task = None
        else:
            task = task_or_tasks
            tasks = [task]
        
        # 计算统计信息
        total_results = len(results)
        vulnerable_count = sum(1 for r in results if r.vulnerable)
        not_vulnerable_count = total_results - vulnerable_count
        
        # 严重度分布
        severity_distribution = {}
        for result in results:
            severity = result.severity or "info"
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # 生成 HTML 报告
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>POC 验证报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
        }}
        .header p {{
            color: #666;
            margin: 10px 0 0 0;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .summary h2 {{
            margin-top: 0;
            color: #007bff;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .stat-card {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #007bff;
        }}
        .results {{
            margin-top: 30px;
        }}
        .results h2 {{
            color: #007bff;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .result-card {{
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-bottom: 20px;
            padding: 20px;
        }}
        .result-card.vulnerable {{
            border-left: 5px solid #dc3545;
        }}
        .result-card.not-vulnerable {{
            border-left: 5px solid #28a745;
        }}
        .result-card h3 {{
            margin-top: 0;
            color: #333;
        }}
        .result-card .meta {{
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        .result-card .severity {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
        }}
        .severity-critical {{
            background-color: #dc3545;
            color: white;
        }}
        .severity-high {{
            background-color: #fd7e14;
            color: white;
        }}
        .severity-medium {{
            background-color: #ffc107;
            color: black;
        }}
        .severity-low {{
            background-color: #20c997;
            color: white;
        }}
        .severity-info {{
            background-color: #6c757d;
            color: white;
        }}
        .result-card .message {{
            margin-top: 15px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 3px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>POC 验证报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <h2>执行摘要</h2>
            <div class="stats">
                <div class="stat-card">
                    <h3>总结果数</h3>
                    <div class="value">{total_results}</div>
                </div>
                <div class="stat-card">
                    <h3>发现漏洞</h3>
                    <div class="value" style="color: #dc3545;">{vulnerable_count}</div>
                </div>
                <div class="stat-card">
                    <h3>未发现漏洞</h3>
                    <div class="value" style="color: #28a745;">{not_vulnerable_count}</div>
                </div>
                <div class="stat-card">
                    <h3>漏洞率</h3>
                    <div class="value">{(vulnerable_count / total_results * 100) if total_results > 0 else 0:.1f}%</div>
                </div>
            </div>
        </div>
        
        <div class="results">
            <h2>验证结果详情</h2>
            {self._generate_results_html(results)}
        </div>
        
        <div class="footer">
            <p>报告由 WebScan AI 安全平台生成</p>
        </div>
    </div>
</body>
</html>
"""
        return html_content
    
    def _generate_results_html(self, results: List[POCVerificationResult]) -> str:
        """
        生成结果 HTML 片段
        
        Args:
            results: 验证结果列表
            
        Returns:
            str: HTML 片段
        """
        html_parts = []
        
        for result in results:
            vulnerable_class = "vulnerable" if result.vulnerable else "not-vulnerable"
            severity_class = f"severity-{result.severity or 'info'}"
            
            html_parts.append(f"""
            <div class="result-card {vulnerable_class}">
                <h3>{result.poc_name}</h3>
                <div class="meta">
                    <span class="severity {severity_class}">{result.severity or 'info'}</span>
                    <span>目标: {result.target}</span>
                    <span>置信度: {result.confidence:.2f}</span>
                    <span>CVSS: {result.cvss_score or 0:.1f}</span>
                </div>
                <div class="message">
                    <strong>结果:</strong> {result.message}
                </div>
            </div>
""")
        
        return "\n".join(html_parts)
    
    async def _generate_json_report(
        self,
        task_or_tasks: Any,
        results: List[POCVerificationResult],
        is_batch: bool = False
    ) -> str:
        """
        生成 JSON 格式报告
        
        Args:
            task_or_tasks: 单个任务或任务列表
            results: 验证结果列表
            is_batch: 是否为批量报告
            
        Returns:
            str: JSON 报告内容
        """
        # 计算统计信息
        total_results = len(results)
        vulnerable_count = sum(1 for r in results if r.vulnerable)
        
        # 严重度分布
        severity_distribution = {}
        for result in results:
            severity = result.severity or "info"
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # 构建 JSON 数据
        report_data = {
            "report_type": "batch" if is_batch else "single",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_results": total_results,
                "vulnerable_count": vulnerable_count,
                "not_vulnerable_count": total_results - vulnerable_count,
                "vulnerability_rate": (vulnerable_count / total_results * 100) if total_results > 0 else 0,
                "severity_distribution": severity_distribution
            },
            "results": [
                {
                    "id": result.id,
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
                for result in results
            ]
        }
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    async def _generate_pdf_report(
        self,
        task_or_tasks: Any,
        results: List[POCVerificationResult],
        is_batch: bool = False
    ) -> str:
        """
        生成 PDF 格式报告
        
        Args:
            task_or_tasks: 单个任务或任务列表
            results: 验证结果列表
            is_batch: 是否为批量报告
            
        Returns:
            str: PDF 报告内容
        """
        # 先生成 HTML 报告
        html_content = await self._generate_html_report(
            task_or_tasks,
            results,
            is_batch
        )
        
        # 尝试转换为 PDF
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes.decode('latin-1')
        except ImportError:
            logger.warning("⚠️ weasyprint 未安装，返回 HTML 格式")
            return html_content
        except Exception as e:
            logger.error(f"❌ 生成 PDF 失败: {str(e)}")
            return html_content
    
    async def generate_execution_summary(
        self,
        verification_task: POCVerificationTask
    ) -> Dict[str, Any]:
        """
        生成执行摘要
        
        Args:
            verification_task: POC 验证任务对象
            
        Returns:
            Dict: 执行摘要字典
        """
        # 获取验证结果
        results = await POCVerificationResult.filter(
            verification_task=verification_task.id
        ).order_by("-created_at")
        
        # 计算统计信息
        total_results = len(results)
        vulnerable_count = sum(1 for r in results if r.vulnerable)
        
        # 平均执行时间
        total_execution_time = sum(r.execution_time for r in results)
        average_execution_time = total_execution_time / total_results if total_results > 0 else 0
        
        # 严重度分布
        severity_distribution = {}
        for result in results:
            severity = result.severity or "info"
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # 目标列表
        targets = list(set(r.target for r in results))
        
        return {
            "task_id": str(verification_task.id),
            "poc_name": verification_task.poc_name,
            "poc_id": verification_task.poc_id,
            "target": verification_task.target,
            "status": verification_task.status,
            "progress": verification_task.progress,
            "created_at": verification_task.created_at.isoformat(),
            "updated_at": verification_task.updated_at.isoformat(),
            "summary": {
                "total_results": total_results,
                "vulnerable_count": vulnerable_count,
                "not_vulnerable_count": total_results - vulnerable_count,
                "vulnerability_rate": (vulnerable_count / total_results * 100) if total_results > 0 else 0,
                "total_execution_time": total_execution_time,
                "average_execution_time": average_execution_time,
                "severity_distribution": severity_distribution
            },
            "targets": targets,
            "result_count": total_results
        }
    
    async def generate_vulnerability_details(
        self,
        results: List[POCVerificationResult]
    ) -> List[Dict[str, Any]]:
        """
        生成漏洞详情列表
        
        Args:
            results: 验证结果列表
            
        Returns:
            List[Dict]: 漏洞详情列表
        """
        details = []
        
        for result in results:
            if result.vulnerable:
                details.append({
                    "poc_name": result.poc_name,
                    "poc_id": result.poc_id,
                    "target": result.target,
                    "severity": result.severity,
                    "cvss_score": result.cvss_score,
                    "confidence": result.confidence,
                    "message": result.message,
                    "output": result.output,
                    "execution_time": result.execution_time,
                    "created_at": result.created_at.isoformat()
                })
        
        return details
    
    async def generate_statistics(
        self,
        results: List[POCVerificationResult]
    ) -> Dict[str, Any]:
        """
        生成统计信息
        
        Args:
            results: 验证结果列表
            
        Returns:
            Dict: 统计信息字典
        """
        if not results:
            return {
                "total": 0,
                "vulnerable": 0,
                "not_vulnerable": 0,
                "vulnerability_rate": 0,
                "average_confidence": 0,
                "average_cvss_score": 0,
                "severity_distribution": {}
            }
        
        total = len(results)
        vulnerable_count = sum(1 for r in results if r.vulnerable)
        
        # 严重度分布
        severity_distribution = {}
        for result in results:
            severity = result.severity or "info"
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # 平均值
        average_confidence = sum(r.confidence for r in results) / total
        average_cvss_score = sum(r.cvss_score or 0 for r in results) / total
        
        return {
            "total": total,
            "vulnerable": vulnerable_count,
            "not_vulnerable": total - vulnerable_count,
            "vulnerability_rate": (vulnerable_count / total * 100) if total > 0 else 0,
            "average_confidence": average_confidence,
            "average_cvss_score": average_cvss_score,
            "severity_distribution": severity_distribution
        }


# 全局报告生成器实例
report_generator = ReportGenerator()

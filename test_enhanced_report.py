"""
测试增强版报告生成器和AI分析器
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

import asyncio
from datetime import datetime
from ai_agents.analyzers.enhanced_report_gen import (
    EnhancedReportGenerator,
    EnhancedReportData,
    ReportFormat
)
from ai_agents.analyzers.ai_analyzer import AIAnalyzer
from ai_agents.core.state import AgentState


def create_mock_state() -> AgentState:
    """创建模拟的Agent状态"""
    state = AgentState(
        target="https://example.com",
        task_id="test_task_123"
    )
    
    state.tool_results = {
        "crawler": {
            "status": "success",
            "data": {"links": ["https://example.com/page1", "https://example.com/page2"]}
        },
        "dirscan": {
            "status": "success",
            "data": {"directories": ["/admin", "/backup", "/config"]}
        },
        "cms_identify": {
            "status": "success",
            "data": {"apps": [{"name": "WordPress"}]}
        }
    }
    
    state.vulnerabilities = [
        {
            "title": "SQL注入漏洞",
            "vuln_type": "sqli",
            "severity": "critical",
            "cve": "CVE-2024-0001",
            "url": "https://example.com/login",
            "description": "登录页面存在SQL注入漏洞",
            "remediation": "使用参数化查询"
        },
        {
            "title": "XSS跨站脚本漏洞",
            "vuln_type": "xss",
            "severity": "high",
            "url": "https://example.com/comment",
            "description": "评论功能存在XSS漏洞",
            "remediation": "对用户输入进行HTML编码"
        }
    ]
    
    state.target_context = {
        "domain": "example.com",
        "ip": "192.168.1.1",
        "open_ports": [80, 443, 22],
        "waf": "Cloudflare",
        "cdn": True
    }
    
    state.execution_history = [
        {
            "step_number": 1,
            "task": "baseinfo",
            "status": "success",
            "timestamp": 1710000000.0,
            "timestamp_iso": "2024-03-14T10:00:00",
            "execution_time": 2.5,
            "input_params": {"target": "https://example.com"},
            "output_data": {"domain": "example.com"},
            "result": {"status": "success"}
        },
        {
            "step_number": 2,
            "task": "crawler",
            "status": "success",
            "timestamp": 1710000003.0,
            "timestamp_iso": "2024-03-14T10:00:03",
            "execution_time": 5.0,
            "input_params": {"depth": 2},
            "output_data": {"links_count": 2},
            "result": {"status": "success"}
        }
    ]
    
    return state


async def test_enhanced_report_generator():
    """测试增强版报告生成器"""
    print("=" * 60)
    print("测试增强版报告生成器（含自动AI分析集成）")
    print("=" * 60)
    
    print("\n[方式1] 使用自动AI分析集成:")
    generator = EnhancedReportGenerator(output_dir="test_reports", auto_ai_analysis=True)
    
    state = create_mock_state()
    
    report_data = await generator.generate_from_state(
        state,
        task_name="示例安全扫描任务（自动AI分析）"
    )
    
    print("\n[1] 报告数据生成完成")
    print(f"   任务名称: {report_data.task_name}")
    print(f"   任务ID: {report_data.task_id}")
    print(f"   漏洞数量: {len(report_data.vulnerabilities)}")
    print(f"   子图数量: {len(report_data.graph_flow.subgraphs)}")
    
    json_path = generator.save_report(report_data, format=ReportFormat.JSON)
    print(f"\n[2] JSON报告已保存: {json_path}")
    
    html_path = generator.save_report(report_data, format=ReportFormat.HTML)
    print(f"[3] HTML报告已保存: {html_path}")
    
    try:
        pdf_path = generator.save_report(report_data, format=ReportFormat.PDF)
        print(f"[4] PDF报告已保存: {pdf_path}")
    except Exception as e:
        print(f"[4] PDF生成跳过 (需要weasyprint库): {e}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    
    return report_data


if __name__ == "__main__":
    asyncio.run(test_enhanced_report_generator())

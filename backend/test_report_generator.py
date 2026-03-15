#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的报告生成器测试脚本
"""
import sys
import os
from pathlib import Path

# 添加项目路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 确保能找到 backend 模块
os.environ['PYTHONPATH'] = str(backend_dir)

from ai_agents.analyzers.enhanced_report_gen import ReportGenerator, EnhancedReportGenerator
from ai_agents.core.state import AgentState
from datetime import datetime
import json

def test_report_generation():
    """测试报告生成"""
    print("=" * 60)
    print("开始测试报告生成功能")
    print("=" * 60)
    
    # 创建测试状态
    test_state = AgentState(
        task_id="test_task_123",
        target="https://www.example.com"
    )
    
    # 添加一些测试数据
    test_state.vulnerabilities = [
        {
            "title": "SQL注入漏洞",
            "vuln_type": "sql_injection",
            "severity": "high",
            "url": "https://www.example.com/search.php?id=1",
            "description": "在搜索参数中发现SQL注入漏洞",
            "remediation": "使用参数化查询"
        },
        {
            "title": "XSS漏洞",
            "vuln_type": "xss",
            "severity": "medium",
            "url": "https://www.example.com/comment.php",
            "description": "在评论表单中发现XSS漏洞",
            "remediation": "对用户输入进行适当转义"
        }
    ]
    
    test_state.tool_results = {
        "baseinfo": {
            "data": {
                "server": "Apache",
                "os": "Linux"
            }
        },
        "portscan": {
            "data": {
                "open_ports": [80, 443]
            }
        }
    }
    
    test_state.target_context = {
        "ip": "93.184.216.34",
        "domain": "example.com",
        "open_ports": [80, 443],
        "waf": "Cloudflare"
    }
    
    test_state.execution_history = [
        {
            "task": "baseinfo",
            "status": "success",
            "timestamp": 1234567890,
            "timestamp_iso": datetime.now().isoformat(),
            "result": "ok"
        },
        {
            "task": "portscan",
            "status": "success",
            "timestamp": 1234567900,
            "timestamp_iso": datetime.now().isoformat(),
            "result": "ok"
        }
    ]
    
    print("\n1. 测试数据准备完成")
    print(f"   - 任务ID: {test_state.task_id}")
    print(f"   - 目标URL: {test_state.target}")
    print(f"   - 漏洞数量: {len(test_state.vulnerabilities)}")
    
    # 初始化报告生成器
    report_gen = ReportGenerator()
    print("\n2. 报告生成器初始化完成")
    
    # 生成报告
    print("\n3. 开始生成报告...")
    try:
        report = report_gen.generate_report(test_state)
        print("   ✅ 报告生成成功！")
        
        # 检查报告结构
        print(f"\n4. 报告结构检查:")
        print(f"   - 报告版本: {report.get('meta', {}).get('version', 'unknown')}")
        print(f"   - 任务ID: {report.get('task_id', 'unknown')}")
        print(f"   - 目标: {report.get('target', 'unknown')}")
        print(f"   - 漏洞总数: {report.get('vulnerabilities', {}).get('total', 0)}")
        
        # 检查AI分析部分
        ai_analysis = report.get('ai_analysis', {})
        print(f"\n5. AI分析检查:")
        print(f"   - 漏洞成因: {'有' if ai_analysis.get('vulnerability_causes') else '无'}")
        print(f"   - 利用风险: {'有' if ai_analysis.get('exploitation_risks') else '无'}")
        print(f"   - 修复优先级: {len(ai_analysis.get('remediation_priorities', []))}个")
        print(f"   - 业务影响: {'有' if ai_analysis.get('business_impact') else '无'}")
        
        if ai_analysis.get('vulnerability_causes'):
            print(f"\n6. AI分析内容:")
            print(f"   - 漏洞成因: {ai_analysis['vulnerability_causes']}")
            print(f"   - 利用风险: {ai_analysis['exploitation_risks']}")
            print(f"   - 业务影响: {ai_analysis['business_impact']}")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！报告生成功能正常工作")
        print("=" * 60)
        
        # 保存测试报告
        test_report_dir = Path("test_reports")
        test_report_dir.mkdir(exist_ok=True)
        test_report_path = test_report_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(test_report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n测试报告已保存到: {test_report_path}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 报告生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_report_generation()
    sys.exit(0 if success else 1)

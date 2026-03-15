#!/usr/bin/env python
"""
测试 PDF 生成功能的脚本
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib.util
spec = importlib.util.spec_from_file_location("reports", os.path.join(os.path.dirname(os.path.abspath(__file__)), "api", "reports.py"))
reports = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reports)
generate_pdf_report = reports.generate_pdf_report

def test_pdf_generation():
    """测试 PDF 生成功能"""
    print("=== 开始测试 PDF 生成功能 ===")
    
    # 准备测试数据
    test_data = {
        "report_name": "测试安全扫描报告",
        "task_name": "测试任务",
        "target": "https://www.example.com",
        "scan_time": "2026-03-15 10:30:00",
        "summary": {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4,
            "info": 5
        },
        "vulnerabilities": [
            {
                "title": "SQL注入漏洞",
                "severity": "critical",
                "url": "https://www.example.com/login",
                "description": "用户登录表单存在 SQL 注入漏洞，攻击者可以通过构造恶意输入获取数据库信息。",
                "remediation": "使用参数化查询或 ORM 框架来防止 SQL 注入攻击。"
            },
            {
                "title": "XSS跨站脚本攻击",
                "severity": "high",
                "url": "https://www.example.com/comment",
                "description": "评论功能未对用户输入进行充分过滤，存在 XSS 攻击风险。",
                "remediation": "对所有用户输入进行 HTML 编码，使用 Content Security Policy (CSP)。"
            },
            {
                "title": "敏感信息泄露",
                "severity": "medium",
                "url": "https://www.example.com/error",
                "description": "错误页面显示了详细的堆栈信息，可能泄露系统敏感信息。",
                "remediation": "在生产环境中禁用详细的错误信息显示。"
            }
        ],
        "ai_analysis": {
            "summary": "本次扫描发现多个高危和严重漏洞，建议立即修复。",
            "risk_level": "high",
            "priorities": [
                {
                    "vulnerability": "SQL注入漏洞",
                    "priority": "紧急",
                    "reason": "可导致数据库完全泄露"
                }
            ],
            "recommendations": [
                "立即修复 SQL 注入漏洞",
                "实施输入验证和输出编码",
                "加强安全配置"
            ]
        }
    }
    
    try:
        print("\n1. 正在生成 PDF...")
        pdf_content = generate_pdf_report(test_data)
        
        print(f"2. PDF 生成成功！大小: {len(pdf_content)} 字节")
        
        # 保存 PDF 文件
        output_file = "test_report.pdf"
        with open(output_file, "wb") as f:
            f.write(pdf_content)
        
        print(f"3. PDF 文件已保存为: {os.path.abspath(output_file)}")
        print("\n=== PDF 生成测试完成！===")
        
        return True
        
    except Exception as e:
        print(f"\n错误: PDF 生成失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    sys.exit(0 if success else 1)

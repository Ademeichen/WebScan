#!/usr/bin/env python
"""
简化的 PDF 生成测试脚本
"""
import sys
import os
from io import BytesIO
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError as e:
    print(f"错误: 缺少依赖 - {e}")
    print("请运行: pip install reportlab")
    sys.exit(1)

SEVERITY_CONFIG = {
    "critical": {"color": "#c0392b", "label": "严重"},
    "high": {"color": "#e74c3c", "label": "高危"},
    "medium": {"color": "#f39c12", "label": "中危"},
    "low": {"color": "#3498db", "label": "低危"},
    "info": {"color": "#95a5a6", "label": "信息"}
}

def calculate_risk_score(vulnerabilities):
    """计算风险评分"""
    if not vulnerabilities:
        return {"score": 0.0, "level": "info", "label": "无风险", "color": "#95a5a6"}
    
    severity_scores = {"critical": 10.0, "high": 8.0, "medium": 5.0, "low": 3.0, "info": 1.0}
    base_score = 0.0
    
    for vuln in vulnerabilities:
        severity = vuln.get("severity", "info").lower()
        base_score += severity_scores.get(severity, 1.0)
    
    max_possible = len(vulnerabilities) * 10.0
    normalized_score = min(100.0, (base_score / max_possible) * 100) if max_possible > 0 else 0.0
    
    if normalized_score >= 80:
        level, label, color = "critical", "极高风险", "#c0392b"
    elif normalized_score >= 60:
        level, label, color = "high", "高风险", "#e74c3c"
    elif normalized_score >= 40:
        level, label, color = "medium", "中等风险", "#f39c12"
    elif normalized_score >= 20:
        level, label, color = "low", "低风险", "#3498db"
    else:
        level, label, color = "info", "信息", "#95a5a6"
    
    return {
        "score": round(normalized_score, 2),
        "level": level,
        "label": label,
        "color": color
    }

def generate_pdf_report(report_data):
    """生成PDF格式报告"""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        
        styles = getSampleStyleSheet()
        
        chinese_font_name = 'ChineseFont'
        font_registered = False
        
        try:
            if sys.platform.startswith('win'):
                font_paths = [
                    r'C:\Windows\Fonts\msyh.ttc',
                    r'C:\Windows\Fonts\simhei.ttf',
                    r'C:\Windows\Fonts\simsun.ttc',
                ]
            elif sys.platform.startswith('darwin'):
                font_paths = [
                    '/System/Library/Fonts/PingFang.ttc',
                    '/System/Library/Fonts/STHeiti Light.ttc',
                ]
            else:
                font_paths = [
                    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
                ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(chinese_font_name, font_path))
                        font_registered = True
                        print(f"已注册中文字体: {font_path}")
                        break
                    except Exception as e:
                        print(f"尝试注册字体失败: {font_path} - {e}")
                        continue
        except Exception as e:
            print(f"字体注册异常: {e}")
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,
            fontName=chinese_font_name if font_registered else 'Helvetica'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            fontName=chinese_font_name if font_registered else 'Helvetica'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceBefore=6,
            spaceAfter=6,
            fontName=chinese_font_name if font_registered else 'Helvetica'
        )
        
        story = []
        
        story.append(Paragraph("🔒 安全扫描报告", title_style))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("基本信息", heading_style))
        info_data = [
            ["报告名称", report_data.get('report_name', 'N/A')],
            ["任务名称", report_data.get('task_name', 'N/A')],
            ["目标", report_data.get('target', 'N/A')],
            ["扫描时间", report_data.get('scan_time', 'N/A')]
        ]
        info_table = Table(info_data, colWidths=[4*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), chinese_font_name if font_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        risk = calculate_risk_score(report_data.get('vulnerabilities', []))
        story.append(Paragraph("风险评估", heading_style))
        risk_data = [
            ["风险评分", f"{risk['score']}"],
            ["风险等级", risk['label']],
            ["风险颜色", risk['color']]
        ]
        risk_table = Table(risk_data, colWidths=[4*cm, 10*cm])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), chinese_font_name if font_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 20))
        
        summary = report_data.get('summary', {})
        story.append(Paragraph("漏洞统计", heading_style))
        summary_data = [
            ["严重程度", "数量"],
            ["严重", str(summary.get('critical', 0))],
            ["高危", str(summary.get('high', 0))],
            ["中危", str(summary.get('medium', 0))],
            ["低危", str(summary.get('low', 0))],
            ["信息", str(summary.get('info', 0))]
        ]
        summary_table = Table(summary_data, colWidths=[6*cm, 6*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), chinese_font_name if font_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, 1), colors.Color(0.75, 0.22, 0.17)),
            ('BACKGROUND', (0, 2), (-1, 2), colors.Color(0.91, 0.30, 0.24)),
            ('BACKGROUND', (0, 3), (-1, 3), colors.Color(0.95, 0.61, 0.07)),
            ('BACKGROUND', (0, 4), (-1, 4), colors.Color(0.20, 0.60, 0.69)),
            ('BACKGROUND', (0, 5), (-1, 5), colors.Color(0.58, 0.65, 0.69))
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        vulnerabilities = report_data.get('vulnerabilities', [])
        if vulnerabilities:
            story.append(Paragraph("漏洞详情", heading_style))
            
            for i, vuln in enumerate(vulnerabilities[:20], 1):
                severity = vuln.get('severity', 'info').lower()
                config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG['info'])
                
                story.append(Paragraph(f"{i}. {vuln.get('title', 'Unknown')}", normal_style))
                
                vuln_info = [
                    ["等级", config['label']],
                    ["URL", str(vuln.get('url', 'N/A'))[:100]],
                    ["描述", str(vuln.get('description', 'N/A'))[:200]]
                ]
                vuln_table = Table(vuln_info, colWidths=[2*cm, 12*cm])
                vuln_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font_name if font_registered else 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                story.append(vuln_table)
                story.append(Spacer(1, 10))
        
        ai_analysis = report_data.get('ai_analysis')
        if ai_analysis:
            story.append(PageBreak())
            story.append(Paragraph("AI智能分析", heading_style))
            
            if ai_analysis.get('summary'):
                story.append(Paragraph("风险总结", normal_style))
                story.append(Paragraph(ai_analysis['summary'], normal_style))
            
            if ai_analysis.get('risk_level'):
                story.append(Paragraph(f"AI评估风险等级: {ai_analysis['risk_level'].upper()}", normal_style))
            
            priorities = ai_analysis.get('priorities', [])
            if priorities:
                story.append(Paragraph("修复优先级建议", normal_style))
                for p in priorities[:5]:
                    story.append(Paragraph(f"- {p.get('vulnerability', 'Unknown')}: 优先级 {p.get('priority', 'N/A')}", normal_style))
        
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        story.append(Paragraph("报告由 AI_WebSecurity 自动生成", normal_style))
        
        doc.build(story)
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        print(f"PDF生成失败: {e}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """主测试函数"""
    print("=== 开始测试 PDF 生成功能 ===")
    
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
        
        output_file = "test_report.pdf"
        with open(output_file, "wb") as f:
            f.write(pdf_content)
        
        print(f"3. PDF 文件已保存为: {os.path.abspath(output_file)}")
        print("\n=== PDF 生成测试完成！===")
        
        return True
        
    except Exception as e:
        print(f"\n错误: PDF 生成失败 - {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

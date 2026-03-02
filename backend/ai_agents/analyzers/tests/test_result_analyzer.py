"""测试智能结果分析器"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from backend.ai_agents.analyzers.result_analyzer import ResultAnalyzer


async def test():
    analyzer = ResultAnalyzer()
    
    test_vulns = [
        {'id': '1', 'cve': 'CVE-2024-1234', 'name': 'SQL注入', 'type': 'sql_injection', 'target': 'example.com', 'severity': 'high', 'confidence': 0.9},
        {'id': '2', 'cve': 'CVE-2024-1234', 'name': 'SQL注入', 'type': 'sql_injection', 'target': 'example.com', 'severity': 'high', 'confidence': 0.7},
        {'id': '3', 'cve': 'CVE-2024-5678', 'name': 'XSS', 'type': 'xss', 'target': 'test.com', 'severity': 'medium', 'confidence': 0.15},
        {'id': '4', 'cve': 'CVE-2024-9999', 'name': 'RCE', 'type': 'rce', 'target': 'prod.com', 'severity': 'critical', 'confidence': 0.95},
    ]
    
    print("=" * 50)
    print("智能结果分析器测试")
    print("=" * 50)
    
    deduped, stats = analyzer.deduplicate_vulnerabilities(test_vulns)
    print(f'\n[去重测试] {stats["original_count"]} -> {stats["deduplicated_count"]} (移除 {stats["duplicates_removed"]} 个重复)')
    
    true_vulns, fps, fp_stats = await analyzer.identify_false_positives(deduped)
    print(f'\n[误报识别] {len(true_vulns)} 个真实漏洞, {len(fps)} 个误报')
    for fp in fps:
        print(f'  - 误报: {fp.get("name")} (分数: {fp.get("false_positive_score", 0):.2f})')
    
    score, details = analyzer.calculate_risk_score(true_vulns)
    print(f'\n[风险评分] {score} 分 ({details["risk_level"]})')
    print(f'  因素: {details["summary"]}')
    
    suggestions, sug_stats = analyzer.generate_follow_up_suggestions(true_vulns)
    print(f'\n[补充扫描建议] 共 {len(suggestions)} 条:')
    for s in suggestions[:5]:
        print(f'  - [{s.priority}] {s.title}')
    
    result = await analyzer.analyze(test_vulns)
    print(f'\n[完整分析结果]')
    print(f'  风险评分: {result.risk_score}')
    print(f'  置信度: {result.confidence:.2%}')
    print(f'  漏洞数: {len(result.vulnerabilities)}')
    print(f'  误报数: {len(result.false_positives)}')
    print(f'  摘要: {result.summary}')
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test())

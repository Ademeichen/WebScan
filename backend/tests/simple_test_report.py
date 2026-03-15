#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的报告生成器测试脚本
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

# 直接导入需要的模块，避免复杂依赖
try:
    # 直接导入，不使用包导入
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "enhanced_report_gen", 
        str(Path(__file__).parent / "ai_agents" / "analyzers" / "enhanced_report_gen.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ReportGenerator = module.ReportGenerator
    print("✅ ReportGenerator 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 模拟一个简单的状态对象
class MockState:
    def __init__(self):
        self.task_id = "test_task_123"
        self.target = "https://www.example.com"
        self.vulnerabilities = [
            {
                "title": "SQL注入漏洞",
                "vuln_type": "sql_injection",
                "severity": "high",
                "url": "https://www.example.com/search.php?id=1",
                "description": "在搜索参数中发现SQL注入漏洞",
                "remediation": "使用参数化查询"
            }
        ]
        self.tool_results = {}
        self.target_context = {}
        self.execution_history = []
        self.errors = []
        self.planned_tasks = []
        self.completed_tasks = []

def main():
    print("=" * 60)
    print("测试报告生成")
    print("=" * 60)
    
    # 创建测试状态
    state = MockState()
    
    # 初始化报告生成器
    try:
        report_gen = ReportGenerator()
        print("\n✅ 报告生成器初始化成功")
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 生成报告
    print("\n生成报告...")
    try:
        report = report_gen.generate_report(state)
        print("✅ 报告生成成功！")
        
        # 检查AI分析部分
        ai_analysis = report.get('ai_analysis', {})
        print(f"\nAI分析检查:")
        print(f"  - 漏洞成因: {ai_analysis.get('vulnerability_causes', 'N/A')}")
        print(f"  - 利用风险: {ai_analysis.get('exploitation_risks', 'N/A')}")
        print(f"  - 业务影响: {ai_analysis.get('business_impact', 'N/A')}")
        print(f"  - 修复优先级: {len(ai_analysis.get('remediation_priorities', []))}个")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成！报告生成功能正常工作")
        print("=" * 60)
        
        # 保存报告
        test_report_dir = Path("test_reports")
        test_report_dir.mkdir(exist_ok=True)
        
        report_path = test_report_dir / f"test_report_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n报告已保存到: {report_path}")
        return True
        
    except Exception as e:
        print(f"\n❌ 报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

"""
WebScan AI Security Platform - 主测试运行脚本

运行所有API测试，包括：
1. 准备测试数据
2. 运行全面API测试
3. 验证测试数据
4. 生成测试报告
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def prepare_test_data():
    """准备测试数据"""
    logger.info("\n" + "="*80)
    logger.info("步骤 1: 准备测试数据")
    logger.info("="*80)
    
    try:
        from tests.prepare_test_data import main as prepare_main
        await prepare_main()
        logger.info("✅ 测试数据准备完成")
        return True
    except Exception as e:
        logger.error(f"❌ 测试数据准备失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def verify_test_data():
    """验证测试数据"""
    logger.info("\n" + "="*80)
    logger.info("步骤 2: 验证测试数据")
    logger.info("="*80)
    
    try:
        from tests.verify_test_data import main as verify_main
        await verify_main()
        logger.info("✅ 测试数据验证完成")
        return True
    except Exception as e:
        logger.error(f"❌ 测试数据验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_api_tests():
    """运行API测试"""
    logger.info("\n" + "="*80)
    logger.info("步骤 3: 运行全面API测试")
    logger.info("="*80)
    
    try:
        from tests.test_all_apis import run_all_tests
        passed, failed, total = await run_all_tests()
        logger.info(f"✅ API测试完成: {passed}/{total} 通过")
        return passed, failed, total
    except Exception as e:
        logger.error(f"❌ API测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0, 0, 0


async def generate_test_report(passed: int, failed: int, total: int):
    """生成测试报告"""
    logger.info("\n" + "="*80)
    logger.info("步骤 4: 生成测试报告")
    logger.info("="*80)
    
    try:
        report = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{(passed/total*100):.2f}%" if total > 0 else "0%"
            },
            "test_phases": [
                {
                    "phase": "准备测试数据",
                    "status": "completed",
                    "description": "创建测试所需的数据库记录"
                },
                {
                    "phase": "验证测试数据",
                    "status": "completed",
                    "description": "验证测试数据的完整性"
                },
                {
                    "phase": "运行API测试",
                    "status": "completed",
                    "description": "测试所有后端API接口"
                },
                {
                    "phase": "生成测试报告",
                    "status": "completed",
                    "description": "生成详细的测试报告"
                }
            ],
            "tested_apis": [
                "扫描功能API - 端口扫描、信息泄露、旁站扫描、网站信息、子域名扫描、目录扫描、综合扫描",
                "任务管理API - 创建、查询、更新、删除任务",
                "报告管理API - 创建、查询、导出报告",
                "AWVS扫描API - 扫描管理、漏洞查询、统计",
                "POC扫描API - POC类型、扫描执行、结果查询",
                "知识库API - 漏洞查询、同步、搜索",
                "AI对话API - 对话管理、消息发送",
                "系统设置API - 配置管理、系统信息、统计",
                "用户管理API - 用户信息、权限管理",
                "通知管理API - 通知查询、创建、标记已读",
                "Agent API - 任务管理、执行",
                "AI Agents API - 扫描任务、代码生成、工具管理",
                "Seebug Agent API - 漏洞搜索、POC生成、连接测试"
            ],
            "recommendations": []
        }
        
        if failed > 0:
            report["recommendations"].append(f"有 {failed} 个测试失败，请检查失败原因并修复")
        if total > 0 and (passed/total) < 0.9:
            report["recommendations"].append("测试通过率低于90%，建议检查API实现")
        if total > 0 and (passed/total) >= 0.9:
            report["recommendations"].append("测试通过率良好，系统功能基本正常")
        
        report_file = "test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 测试报告已生成: {report_file}")
        
        logger.info("\n" + "="*80)
        logger.info("测试摘要")
        logger.info("="*80)
        logger.info(f"总测试数: {total}")
        logger.info(f"通过: {passed}")
        logger.info(f"失败: {failed}")
        logger.info(f"通过率: {(passed/total*100):.2f}%" if total > 0 else "通过率: 0%")
        logger.info("="*80)
        
        return True
    except Exception as e:
        logger.error(f"❌ 生成测试报告失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    logger.info("\n" + "="*80)
    logger.info("WebScan AI Security Platform - 全面测试套件")
    logger.info("="*80)
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    success_count = 0
    
    if await prepare_test_data():
        success_count += 1
    
    if await verify_test_data():
        success_count += 1
    
    passed, failed, total = await run_api_tests()
    
    if await generate_test_report(passed, failed, total):
        success_count += 1
    
    logger.info(f"\n测试阶段完成: {success_count}/4")
    
    if success_count == 4 and failed == 0:
        logger.info("\n✅ 所有测试通过！系统功能正常。")
        return 0
    elif failed > 0:
        logger.warning(f"\n⚠️  有 {failed} 个测试失败，请检查详细日志。")
        return 1
    else:
        logger.error("\n❌ 测试执行失败，请检查错误日志。")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

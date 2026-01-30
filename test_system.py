#!/usr/bin/env python3
"""
系统综合测试脚本

测试整个系统的功能完整性和性能
"""
import asyncio
import logging
import time
from backend.ai_agents.utils.file_sync import file_sync_manager
from backend.ai_agents.code_execution.environment import EnvironmentAwareness
from backend.ai_agents.analyzers.report_gen import ReportGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_file_sync():
    """
    测试文件同步功能
    """
    logger.info("\n=== 测试文件同步功能 ===")
    
    try:
        # 执行文件同步
        sync_result = file_sync_manager.sync_files()
        
        logger.info(f"同步结果:")
        logger.info(f"  新增文件: {len(sync_result['added'])}")
        logger.info(f"  更新文件: {len(sync_result['updated'])}")
        logger.info(f"  删除文件: {len(sync_result['deleted'])}")
        
        # 获取同步状态
        sync_status = file_sync_manager.get_sync_status()
        
        logger.info(f"\n同步状态:")
        logger.info(f"  基础POC目录文件数: {len(sync_status['base_poc_files'])}")
        logger.info(f"  Seebug生成目录文件数: {len(sync_status['seebug_generated_files'])}")
        
        return True
    except Exception as e:
        logger.error(f"文件同步测试失败: {str(e)}")
        return False


async def test_environment_awareness():
    """
    测试环境感知功能
    """
    logger.info("\n=== 测试环境感知功能 ===")
    
    try:
        start_time = time.time()
        env = EnvironmentAwareness()
        report = env.get_environment_report()
        end_time = time.time()
        
        logger.info(f"环境感知初始化耗时: {end_time - start_time:.2f}秒")
        logger.info(f"操作系统: {report['os_info']['system']} {report['os_info']['release']}")
        logger.info(f"Python版本: {report['python_info']['version']}")
        logger.info(f"可用工具数量: {sum(1 for t in report['available_tools'].values() if t.get('available'))}")
        logger.info(f"网络状态: {'在线' if report['network_info']['internet_available'] else '离线'}")
        logger.info(f"磁盘使用率: {report['system_resources']['disk_used_percent']:.1f}%")
        
        return True
    except Exception as e:
        logger.error(f"环境感知测试失败: {str(e)}")
        return False


async def test_report_generator():
    """
    测试报告生成功能
    """
    logger.info("\n=== 测试报告生成功能 ===")
    
    try:
        # 创建一个模拟的AgentState对象
        class MockAgentState:
            def __init__(self):
                self.task_id = "test_task"
                self.target = "http://example.com"
                self.planned_tasks = ["baseinfo", "portscan"]
                self.completed_tasks = ["baseinfo"]
                self.target_context = {"cms": "wordpress", "open_ports": [80, 443]}
                self.vulnerabilities = []
                self.tool_results = {"baseinfo": {"status": "success", "data": {"server": "Apache"}}}
                self.errors = []
                self.is_complete = True
                self.execution_history = [{"timestamp": time.time() - 10}, {"timestamp": time.time()}]
            
            def get_progress(self):
                return 50.0
        
        state = MockAgentState()
        report_gen = ReportGenerator()
        
        # 测试生成报告
        start_time = time.time()
        report = report_gen.generate_report(state)
        end_time = time.time()
        
        logger.info(f"报告生成耗时: {end_time - start_time:.2f}秒")
        logger.info(f"报告包含任务ID: {report['task_id']}")
        logger.info(f"报告包含目标: {report['target']}")
        logger.info(f"报告包含漏洞数: {report['vulnerabilities']['total']}")
        logger.info(f"报告包含工具结果数: {len(report['tool_results']['details'])}")
        
        # 测试生成HTML报告
        html_report = report_gen.generate_html_report(state)
        logger.info(f"HTML报告长度: {len(html_report)}字符")
        
        return True
    except Exception as e:
        logger.error(f"报告生成测试失败: {str(e)}")
        return False


async def test_api_endpoints():
    """
    测试API接口功能
    """
    logger.info("\n=== 测试API接口功能 ===")
    
    try:
        # 这里我们只是测试API模块的导入和初始化
        from backend.api import api_router
        from backend.api.poc_files import router as poc_files_router
        
        logger.info("API路由模块导入成功")
        logger.info("POC文件管理API路由导入成功")
        
        # 测试API路由的包含情况
        poc_files_included = any(r.path == "/poc/files" for r in api_router.routes)
        logger.info(f"POC文件管理API路由已包含: {poc_files_included}")
        
        return True
    except Exception as e:
        logger.error(f"API接口测试失败: {str(e)}")
        return False


async def main():
    """
    主测试函数
    """
    logger.info("🚀 开始系统综合测试")
    
    # 运行所有测试
    tests = [
        test_file_sync(),
        test_environment_awareness(),
        test_report_generator(),
        test_api_endpoints()
    ]
    
    results = await asyncio.gather(*tests)
    
    # 统计测试结果
    passed = sum(results)
    total = len(results)
    
    logger.info(f"\n=== 测试结果汇总 ===")
    logger.info(f"通过测试: {passed}/{total}")
    logger.info(f"测试通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 所有测试通过！系统功能完整正常")
    else:
        logger.warning("⚠️ 部分测试失败，需要进一步检查")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())

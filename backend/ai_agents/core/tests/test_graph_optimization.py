"""
图结构优化测试文件

测试优化后的图结构、插件集成、POC工具调用和性能测试。
"""
import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
import sys
import os
backend_dir = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_dir)

from ai_agents.core.graph import create_agent_graph, initialize_tools
from ai_agents.core.state import AgentState
from ai_agents.tools.registry import registry


class TestData:
    """测试数据类"""
    
    TEST_TARGETS = [
        "https://example.com",
        "https://test-site.local",
        "http://192.168.1.100"
    ]
    
    @staticmethod
    def create_test_state(target: str = "https://example.com", task_id: str = None) -> AgentState:
        """创建测试状态
        
        Args:
            target: 测试目标
            task_id: 任务ID
            
        Returns:
            AgentState: 测试状态
        """
        if task_id is None:
            task_id = f"test_{int(time.time())}"
        
        return AgentState(
            task_id=task_id,
            target=target,
            target_context={},
            planned_tasks=[],
            completed_tasks=[],
            current_task=None,
            tool_results={},
            vulnerabilities=[],
            errors=[],
            execution_steps=[],
            stage_status={},
            is_complete=False,
            should_continue=True,
            retry_count=0,
            enhancement_retry_count=0
        )


class GraphOptimizationTest:
    """图结构优化测试类"""
    
    def __init__(self):
        """初始化测试"""
        self.test_results = []
        self.graph = None
        
    def initialize(self):
        """初始化测试环境"""
        logger.info("=" * 60)
        logger.info("初始化测试环境")
        logger.info("=" * 60)
        
        # 初始化工具
        initialize_tools()
        logger.info(f"✅ 工具初始化完成，共 {len(registry.tools)} 个工具")
        
        # 创建图实例
        self.graph = create_agent_graph()
        logger.info("✅ 图实例创建完成")
        
        logger.info("=" * 60)
        
    async def test_all_plugins_registered(self):
        """测试所有插件都已注册"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 1: 验证所有插件是否已注册")
        logger.info("=" * 60)
        
        expected_plugins = [
            "baseinfo", "portscan", "waf_detect", "cdn_detect", 
            "cms_identify", "infoleak_scan", "subdomain_scan", 
            "webside_scan", "webweight_scan", "iplocating", 
            "loginfo", "randheader", "awvs"
        ]
        
        all_tools = registry.list_tools()
        registered_plugins = [t["name"] for t in all_tools if t.get("category") == "plugin"]
        
        logger.info(f"期望插件数量: {len(expected_plugins)}")
        logger.info(f"实际注册插件数量: {len(registered_plugins)}")
        logger.info(f"注册的插件: {registered_plugins}")
        
        # 检查缺失的插件
        missing_plugins = [p for p in expected_plugins if p not in registered_plugins]
        extra_plugins = [p for p in registered_plugins if p not in expected_plugins]
        
        passed = len(missing_plugins) == 0
        
        result = {
            "test_name": "test_all_plugins_registered",
            "passed": passed,
            "expected_count": len(expected_plugins),
            "actual_count": len(registered_plugins),
            "missing_plugins": missing_plugins,
            "extra_plugins": extra_plugins,
            "registered_plugins": registered_plugins
        }
        
        self.test_results.append(result)
        
        if passed:
            logger.info("✅ 所有插件已正确注册")
        else:
            logger.error(f"❌ 插件注册测试失败，缺失: {missing_plugins}")
        
        return passed
        
    async def test_poc_tools_available(self):
        """测试POC工具可用"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 2: 验证POC工具是否可用")
        logger.info("=" * 60)
        
        all_tools = registry.list_tools()
        poc_tools = [t["name"] for t in all_tools if t.get("category") == "poc"]
        
        logger.info(f"POC工具数量: {len(poc_tools)}")
        logger.info(f"POC工具列表: {poc_tools}")
        
        passed = len(poc_tools) > 0
        
        result = {
            "test_name": "test_poc_tools_available",
            "passed": passed,
            "poc_count": len(poc_tools),
            "poc_tools": poc_tools
        }
        
        self.test_results.append(result)
        
        if passed:
            logger.info(f"✅ POC工具测试通过，共 {len(poc_tools)} 个POC")
        else:
            logger.error("❌ POC工具测试失败")
        
        return passed
        
    async def test_graph_structure(self):
        """测试图结构"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 3: 验证图结构")
        logger.info("=" * 60)
        
        # 测试完整图
        try:
            compiled_graph = self.graph.compile()
            logger.info("✅ 完整图编译成功")
        except Exception as e:
            logger.error(f"❌ 完整图编译失败: {str(e)}")
            return False
            
        # 测试子图
        try:
            info_graph = self.graph.compile_info_collection()
            logger.info("✅ 信息收集子图编译成功")
            
            scan_graph = self.graph.compile_vulnerability_scan()
            logger.info("✅ 漏洞扫描子图编译成功")
            
            analysis_graph = self.graph.compile_result_analysis()
            logger.info("✅ 结果分析子图编译成功")
        except Exception as e:
            logger.error(f"❌ 子图编译失败: {str(e)}")
            return False
            
        result = {
            "test_name": "test_graph_structure",
            "passed": True,
            "subgraphs": ["info_collection", "vulnerability_scan", "result_analysis"]
        }
        
        self.test_results.append(result)
        return True
        
    async def test_performance(self, test_target: str = "https://example.com", iterations: int = 3):
        """性能测试"""
        logger.info("\n" + "=" * 60)
        logger.info(f"测试 4: 性能测试 (迭代次数: {iterations})")
        logger.info("=" * 60)
        
        execution_times = []
        
        for i in range(iterations):
            logger.info(f"\n--- 迭代 {i+1}/{iterations} ---")
            
            test_state = TestData.create_test_state(
                target=test_target,
                task_id=f"perf_test_{int(time.time())}_{i}"
            )
            
            start_time = time.time()
            
            try:
                # 只测试信息收集子图以节省时间
                result_state = await self.graph.invoke_info_collection(test_state)
                execution_time = time.time() - start_time
                
                execution_times.append(execution_time)
                logger.info(f"✅ 执行完成，耗时: {execution_time:.2f}秒")
                logger.info(f"   规划任务数: {len(getattr(result_state, 'planned_tasks', []))}")
                
            except Exception as e:
                logger.error(f"❌ 执行失败: {str(e)}")
                execution_times.append(None)
        
        # 计算统计数据
        valid_times = [t for t in execution_times if t is not None]
        
        if valid_times:
            avg_time = sum(valid_times) / len(valid_times)
            min_time = min(valid_times)
            max_time = max(valid_times)
            
            logger.info(f"\n--- 性能统计 ---")
            logger.info(f"平均执行时间: {avg_time:.2f}秒")
            logger.info(f"最小执行时间: {min_time:.2f}秒")
            logger.info(f"最大执行时间: {max_time:.2f}秒")
            logger.info(f"成功执行次数: {len(valid_times)}/{iterations}")
        else:
            avg_time = None
            min_time = None
            max_time = None
            logger.error("❌ 没有成功的执行记录")
        
        result = {
            "test_name": "test_performance",
            "passed": len(valid_times) > 0,
            "iterations": iterations,
            "execution_times": execution_times,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "success_count": len(valid_times)
        }
        
        self.test_results.append(result)
        return len(valid_times) > 0
        
    def generate_report(self, output_file: str = None):
        """生成测试报告
        
        Args:
            output_file: 输出文件路径
        """
        report = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for r in self.test_results if r.get("passed", False)),
            "failed_tests": sum(1 for r in self.test_results if not r.get("passed", False)),
            "test_results": self.test_results
        }
        
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"\n✅ 测试报告已保存到: {output_file}")
        
        # 打印摘要
        logger.info("\n" + "=" * 60)
        logger.info("测试摘要")
        logger.info("=" * 60)
        logger.info(f"总测试数: {report['total_tests']}")
        logger.info(f"通过: {report['passed_tests']}")
        logger.info(f"失败: {report['failed_tests']}")
        logger.info("=" * 60)
        
        return report


async def main():
    """主测试函数"""
    test = GraphOptimizationTest()
    
    try:
        # 初始化
        test.initialize()
        
        # 运行测试
        await test.test_all_plugins_registered()
        await test.test_poc_tools_available()
        await test.test_graph_structure()
        await test.test_performance(iterations=1)  # 减少迭代次数以快速测试
        
        # 生成报告
        report_file = Path(__file__).parent / "test_report.json"
        test.generate_report(str(report_file))
        
    except Exception as e:
        logger.error(f"测试执行失败: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())

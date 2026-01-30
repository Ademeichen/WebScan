#!/usr/bin/env python3
"""
简单的工作流测试脚本
验证SeebugAgentNode和POCVerificationNode的集成
"""
import asyncio
import logging
from backend.ai_agents.core.graph import ScanAgentGraph
from backend.ai_agents.core.state import AgentState

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_seebug_poc_workflow():
    """
    测试Seebug POC工作流
    """
    logger.info("🚀 开始测试Seebug POC工作流")
    
    try:
        # 创建初始状态
        initial_state = AgentState(
            task_id="test_seebug_poc",
            target="http://example.com",
            target_context={
                "need_seebug_agent": True,
                "cms": "thinkphp"
            }
        )
        
        # 创建并执行图
        graph = ScanAgentGraph()
        final_state = await graph.invoke(initial_state)
        
        # 打印结果
        logger.info("✅ 工作流执行完成")
        logger.info(f"  完成任务: {len(final_state.completed_tasks)}")
        logger.info(f"  发现漏洞: {len(final_state.vulnerabilities)}")
        logger.info(f"  执行步骤: {len(final_state.execution_history)}")
        logger.info(f"  错误数: {len(final_state.errors)}")
        
        # 检查是否执行了Seebug Agent和POC验证
        seebug_executed = any(step['task'] == 'seebug_agent' for step in final_state.execution_history)
        poc_executed = any(step['task'] == 'poc_verification' for step in final_state.execution_history)
        
        logger.info(f"  Seebug Agent执行: {seebug_executed}")
        logger.info(f"  POC验证执行: {poc_executed}")
        
        if seebug_executed and poc_executed:
            logger.info("🎉 测试通过: Seebug Agent和POC验证节点都已执行")
        else:
            logger.error("❌ 测试失败: Seebug Agent或POC验证节点未执行")
        
    except Exception as e:
        logger.error(f"❌ 工作流执行失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_seebug_poc_workflow())

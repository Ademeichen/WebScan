"""
子图执行测试脚本

测试AI Agent各个子图是否能够正确执行并返回结果。
使用真实AI模型服务进行测试。
"""
import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.config import settings
from backend.ai_agents.core.state import AgentState
from backend.ai_agents.core.graph import ScanAgentGraph


class SubGraphTester:
    """子图测试器"""
    
    def __init__(self):
        self.test_results = []
        self.test_target = "https://www.baidu.com"
        
    def print_header(self, title: str):
        """打印标题"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    
    def print_result(self, test_name: str, success: bool, duration: float, details: str = ""):
        """打印测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        print(f"\n{status} | {test_name} | 耗时: {duration:.2f}秒")
        if details:
            print(f"   详情: {details}")
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "duration": duration,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_graph_initialization(self):
        """测试图初始化"""
        self.print_header("测试1: 图初始化")
        start_time = time.time()
        
        try:
            graph = ScanAgentGraph()
            assert graph is not None, "图对象创建失败"
            assert graph.graph is not None, "图结构创建失败"
            
            compiled = graph.graph.compile()
            assert compiled is not None, "图编译失败"
            
            duration = time.time() - start_time
            self.print_result("图初始化测试", True, duration, "图创建和编译成功")
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("图初始化测试", False, duration, str(e))
            return False
    
    async def test_state_creation(self):
        """测试状态创建"""
        self.print_header("测试2: AgentState创建")
        start_time = time.time()
        
        try:
            state = AgentState(
                target=self.test_target,
                task_id="test_subgraph_001",
                target_context={"test": "value"},
                user_tools=["port_scan", "baseinfo"],
                user_requirement="测试子图执行",
                memory_info="子图测试记忆信息"
            )
            
            assert state.target == self.test_target, "目标设置失败"
            assert state.task_id == "test_subgraph_001", "任务ID设置失败"
            assert state.user_tools == ["port_scan", "baseinfo"], "工具列表设置失败"
            assert state.is_complete == False, "初始完成状态错误"
            assert state.should_continue == True, "初始继续状态错误"
            
            duration = time.time() - start_time
            self.print_result("AgentState创建测试", True, duration, "状态对象创建成功")
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("AgentState创建测试", False, duration, str(e))
            return False
    
    async def test_state_methods(self):
        """测试状态方法"""
        self.print_header("测试3: AgentState方法")
        start_time = time.time()
        
        try:
            state = AgentState(
                target=self.test_target,
                task_id="test_methods_001"
            )
            
            # 测试update_context
            state.update_context("cms", "WordPress")
            assert state.target_context["cms"] == "WordPress", "update_context失败"
            
            # 测试add_vulnerability
            state.add_vulnerability({
                "type": "XSS",
                "severity": "Medium",
                "title": "Test XSS"
            })
            assert len(state.vulnerabilities) == 1, "add_vulnerability失败"
            
            # 测试add_error
            state.add_error("Test error")
            assert "Test error" in state.errors, "add_error失败"
            
            # 测试mark_complete
            state.mark_complete()
            assert state.is_complete == True, "mark_complete失败"
            assert state.should_continue == False, "mark_complete后should_continue错误"
            
            # 测试to_dict
            state_dict = state.to_dict()
            assert "target" in state_dict, "to_dict缺少target"
            assert "task_id" in state_dict, "to_dict缺少task_id"
            
            duration = time.time() - start_time
            self.print_result("AgentState方法测试", True, duration, "所有方法测试通过")
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("AgentState方法测试", False, duration, str(e))
            return False
    
    async def test_graph_execution_basic(self):
        """测试基本图执行"""
        self.print_header("测试4: 基本图执行")
        start_time = time.time()
        
        try:
            state = AgentState(
                target=self.test_target,
                task_id="test_exec_001",
                target_context={"task_type": "ai_agent_scan"},
                user_tools=["port_scan"],
                user_requirement="执行基本扫描测试",
                memory_info="基本执行测试"
            )
            
            graph = ScanAgentGraph()
            app = graph.graph.compile()
            
            print(f"\n开始执行图，目标: {self.test_target}")
            
            final_state = await asyncio.wait_for(
                app.ainvoke(state),
                timeout=120
            )
            
            # 检查执行结果
            if isinstance(final_state, dict):
                is_complete = final_state.get('is_complete', False)
                errors = final_state.get('errors', [])
            else:
                is_complete = getattr(final_state, 'is_complete', False)
                errors = getattr(final_state, 'errors', [])
            
            duration = time.time() - start_time
            
            if errors:
                self.print_result("基本图执行测试", False, duration, f"执行有错误: {errors[:3]}")
            else:
                self.print_result("基本图执行测试", True, duration, f"执行完成, is_complete={is_complete}")
            
            return True
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self.print_result("基本图执行测试", False, duration, "执行超时(120秒)")
            return False
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("基本图执行测试", False, duration, str(e))
            return False
    
    async def test_ai_model_connection(self):
        """测试AI模型连接"""
        self.print_header("测试5: AI模型连接")
        start_time = time.time()
        
        try:
            from backend.ai_agents.core.llm import get_llm
            
            llm = get_llm()
            assert llm is not None, "LLM对象创建失败"
            
            # 测试简单调用
            response = await asyncio.wait_for(
                llm.ainvoke("请回复'连接成功'"),
                timeout=30
            )
            
            assert response is not None, "AI模型响应为空"
            
            duration = time.time() - start_time
            response_text = str(response.content) if hasattr(response, 'content') else str(response)
            self.print_result("AI模型连接测试", True, duration, f"响应: {response_text[:50]}...")
            return True
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self.print_result("AI模型连接测试", False, duration, "连接超时")
            return False
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("AI模型连接测试", False, duration, str(e))
            return False
    
    async def test_stage_status_tracking(self):
        """测试阶段状态跟踪"""
        self.print_header("测试6: 阶段状态跟踪")
        start_time = time.time()
        
        try:
            state = AgentState(
                target=self.test_target,
                task_id="test_stage_001"
            )
            
            # 测试阶段状态更新
            state.update_stage_status("openai", status="running", progress=50, log="开始AI处理")
            
            assert state.stage_status["openai"]["status"] == "running", "阶段状态更新失败"
            assert state.stage_status["openai"]["progress"] == 50, "阶段进度更新失败"
            assert len(state.stage_status["openai"]["logs"]) > 0, "阶段日志未记录"
            
            # 测试进度计算
            progress = state.get_progress()
            assert isinstance(progress, (int, float)), "进度返回类型错误"
            
            duration = time.time() - start_time
            self.print_result("阶段状态跟踪测试", True, duration, f"进度: {progress}%")
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("阶段状态跟踪测试", False, duration, str(e))
            return False
    
    async def test_execution_history(self):
        """测试执行历史记录"""
        self.print_header("测试7: 执行历史记录")
        start_time = time.time()
        
        try:
            state = AgentState(
                target=self.test_target,
                task_id="test_history_001"
            )
            
            # 添加执行步骤
            state.add_execution_step(
                task="test_task",
                result={"status": "success"},
                status="success",
                step_type="tool_execution"
            )
            
            assert len(state.execution_history) == 1, "执行历史未记录"
            assert state.execution_history[0]["task"] == "test_task", "任务名称错误"
            assert state.execution_history[0]["status"] == "success", "状态错误"
            
            # 测试步骤编号
            step_num = state.add_execution_step_start(
                task="test_task_2",
                step_type="code_generation"
            )
            assert step_num == 2, "步骤编号错误"
            
            duration = time.time() - start_time
            self.print_result("执行历史记录测试", True, duration, f"记录了{len(state.execution_history)}条历史")
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("执行历史记录测试", False, duration, str(e))
            return False
    
    def print_summary(self):
        """打印测试摘要"""
        self.print_header("测试摘要")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        print(f"\n总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n失败的测试:")
            for r in self.test_results:
                if not r["success"]:
                    print(f"  - {r['test_name']}: {r['details']}")
        
        print("\n" + "=" * 60)


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("  AI Agent 子图执行测试")
    print("  使用真实AI模型服务")
    print("=" * 60)
    
    tester = SubGraphTester()
    
    # 执行所有测试
    await tester.test_graph_initialization()
    await tester.test_state_creation()
    await tester.test_state_methods()
    await tester.test_ai_model_connection()
    await tester.test_stage_status_tracking()
    await tester.test_execution_history()
    await tester.test_graph_execution_basic()
    
    # 打印摘要
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())

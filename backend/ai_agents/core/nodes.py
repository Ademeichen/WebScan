"""
LangGraph 节点定义

定义Agent工作流中的各个节点函数。
"""
import logging
import asyncio
import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

from ..core.state import AgentState
from ..tools.registry import registry
from ..tools.adapters import PluginAdapter, POCAdapter
from ..agent_config import agent_config
from ..utils.priority import TaskPriorityManager

logger = logging.getLogger(__name__)


class PlanningResponse(BaseModel):
    """
    规划响应模型
    
    用于LLM规划器的输出解析。
    """
    plan: List[str]
    reasoning: str


class TaskPlanningNode:
    """
    任务规划节点
    
    根据用户需求和目标特征,生成扫描任务计划。
    支持规则化规划和LLM增强规划两种模式。
    """
    
    def __init__(self):
        self.priority_manager = TaskPriorityManager()
        
        if agent_config.ENABLE_LLM_PLANNING:
            self.llm = ChatOpenAI(
                model=agent_config.MODEL_ID,
                temperature=0,
                api_key=agent_config.OPENAI_API_KEY,
                base_url=agent_config.OPENAI_BASE_URL
            )
            self.use_llm = True
            logger.info("🤖 启用LLM增强任务规划")
        else:
            self.use_llm = False
            logger.info("📋 使用规则化任务规划")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        执行任务规划
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{state.task_id}] 📋 开始任务规划,目标: {state.target}")
        
        # 更新阶段状态
        state.update_stage_status("openai", "running", "planning", 10, "开始任务规划")
        
        try:
            if self.use_llm:
                state.update_stage_status("openai", "running", "analyzing", 30, "正在使用LLM分析目标")
                planned_tasks = await self._llm_planning(state)
            else:
                state.update_stage_status("openai", "running", "analyzing", 30, "正在使用规则分析目标")
                planned_tasks = await self._rule_based_planning(state)
            
            state.planned_tasks = planned_tasks
            state.current_task = planned_tasks[0] if planned_tasks else None
            
            logger.info(f"[{state.task_id}] ✅ 任务规划完成: {planned_tasks}")
            state.add_execution_step("task_planning", {"tasks": planned_tasks}, "success")
            
            # 更新阶段状态
            state.update_stage_status("openai", "completed", "finished", 100, f"任务规划完成, 生成 {len(planned_tasks)} 个任务")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 任务规划失败: {str(e)}")
            state.add_error(f"任务规划失败: {str(e)}")
            state.planned_tasks = agent_config.DEFAULT_SCAN_TASKS
            state.current_task = state.planned_tasks[0] if state.planned_tasks else None
            
            # 更新阶段状态
            state.update_stage_status("openai", "failed", "error", 0, f"任务规划失败: {str(e)}")
        
        return state
    
    async def _rule_based_planning(self, state: AgentState) -> List[str]:
        """
        规则化任务规划
        
        根据预设规则生成任务列表。
        
        Args:
            state: Agent当前状态
            
        Returns:
            List[str]: 任务列表
        """
        tasks = agent_config.DEFAULT_SCAN_TASKS.copy()
        
        # 根据目标上下文补充POC任务
        if state.target_context:
            cms = state.target_context.get("cms", "").lower()
            open_ports = state.target_context.get("open_ports", [])
            
            # 根据CMS添加POC
            if "weblogic" in cms:
                tasks.extend(POCAdapter.get_poc_by_cms("weblogic"))
            elif "struts2" in cms:
                tasks.extend(POCAdapter.get_poc_by_cms("struts2"))
            elif "tomcat" in cms:
                tasks.extend(POCAdapter.get_poc_by_cms("tomcat"))
            
            # 根据端口添加POC
            for port in open_ports:
                port_pocs = POCAdapter.get_poc_by_port(port)
                for poc in port_pocs:
                    if poc not in tasks:
                        tasks.append(poc)
        
        return tasks
    
    async def _llm_planning(self, state: AgentState) -> List[str]:
        """
        LLM增强任务规划
        
        使用LLM根据目标特征智能生成任务列表。
        
        Args:
            state: Agent当前状态
            
        Returns:
            List[str]: 任务列表
        """
        available_tools = registry.list_tools()
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}" 
            for t in available_tools
        ])
        
        context_info = ""
        if state.target_context:
            # 使用双花括号来转义花括号，避免被ChatPromptTemplate错误解析
            context_info = f"\n目标上下文: {str(state.target_context).replace('{', '{{').replace('}', '}}')}"
        
        system_prompt = """
        你是Web安全扫描专家,需要为目标规划扫描任务。
        
        可用工具列表:
        {tools}
        
        规划规则:
        1. 先执行基础信息收集类任务(baseinfo、portscan、waf_detect、cdn_detect、cms_identify)
        2. 根据基础信息结果选择POC验证任务(如CMS为WordPress则跳过WebLogic POC)
        3. 避免无意义的POC扫描
        4. 为了确保全面性，请默认包含 'awvs' 任务，除非用户明确要求"快速扫描"或"轻量级扫描"
        5. 返回格式为JSON数组,仅包含任务名称
        6. 任务优先级:AWVS > POC验证 > 端口扫描 > 基础信息收集
        """
        
        user_prompt = f"目标: {state.target}{context_info}"
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt)
            ])
            
            chain = prompt | self.llm | JsonOutputParser(pydantic_object=PlanningResponse)
            result = await chain.ainvoke({"tools": tools_desc})
            
            # 检查result的类型并提取任务列表
            tasks = self._extract_tasks_from_result(result)
            
            if tasks:
                logger.info(f"LLM规划结果: {tasks}")
                return tasks
            else:
                raise ValueError("无法从LLM规划结果中提取有效任务列表")
                
        except Exception as e:
            logger.error(f"LLM规划失败,使用规则化规划: {str(e)}")
            return await self._rule_based_planning(state)
    
    def _extract_tasks_from_result(self, result: Any) -> List[str]:
        """
        从LLM结果中提取任务列表
        
        Args:
            result: LLM返回的结果
            
        Returns:
            List[str]: 任务列表
        """
        if result is None:
            return []
        
        # 情况1: result 是 PlanningResponse 对象
        if isinstance(result, PlanningResponse):
            if isinstance(result.plan, list):
                return result.plan
            return []
        
        # 情况2: result 是字典类型
        if isinstance(result, dict):
            if 'plan' in result and isinstance(result['plan'], list):
                return result['plan']
            # 如果字典本身就是任务列表（兼容性处理）
            if all(isinstance(v, str) for v in result.values()):
                return list(result.values())
            return []
        
        # 情况3: result 是列表类型
        if isinstance(result, list):
            if all(isinstance(item, str) for item in result):
                return result
            return []
        
        # 情况4: result 是字符串类型（JSON字符串）
        if isinstance(result, str):
            try:
                import json
                parsed = json.loads(result)
                return self._extract_tasks_from_result(parsed)
            except json.JSONDecodeError:
                return []
        
        logger.warning(f"无法识别的LLM结果类型: {type(result)}, 值: {result}")
        return []


class ToolExecutionNode:
    """
    工具执行节点
    
    执行当前规划的任务,调用相应的工具并更新状态。
    """
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(agent_config.MAX_CONCURRENT_TOOLS)
        logger.info(f"🔧 工具执行节点初始化,最大并发: {agent_config.MAX_CONCURRENT_TOOLS}")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        执行工具
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        # 计算总体进度
        total = len(state.completed_tasks) + len(state.planned_tasks)
        if state.current_task and state.current_task not in state.completed_tasks:
             total += 1 if state.current_task not in state.planned_tasks else 0
        current = len(state.completed_tasks)
        progress = int((current / total) * 100) if total > 0 else 0
        
        state.update_stage_status("plugins", "running", "scanning", progress, "正在执行工具扫描")

        if not state.current_task:
            logger.info(f"[{state.task_id}] ⏹️ 没有待执行任务")
            state.update_stage_status("plugins", "completed", "finished", 100, "所有工具执行完成")
            # 不要立即标记为完成，让工作流继续执行到result_verification节点
            return state
        
        tool_name = state.current_task
        logger.info(f"[{state.task_id}] 🔧 执行工具: {tool_name}")
        
        log_msg = f"正在执行插件扫描: {tool_name}"
        state.update_stage_status("plugins", "running", "scanning", progress, log_msg)
        
        step_number = state.add_execution_step_start(
            tool_name,
            step_type="tool_execution",
            input_params={
                "target": state.target,
                "tool_name": tool_name,
                "tool_type": "plugin" if not tool_name.startswith("poc_") else "poc"
            },
            processing_logic=f"执行{tool_name}工具进行安全扫描"
        )
        
        try:
            async with self.semaphore:
                logger.info(f"[{state.task_id}] 🚀 开始执行插件: {tool_name}")
                result = await registry.call_tool(tool_name, state.target)
                
                # 检查工具执行状态
                if result.get("status") == "success":
                    state.update_stage_status("plugins", "running", "scanning", progress, f"插件 {tool_name} 执行完成")
                    state.tool_results[tool_name] = result
                    
                    # 更新目标上下文
                    self._update_context(state, tool_name, result)
                    
                    # 处理POC结果
                    if tool_name.startswith("poc_") and result.get("status") == "success":
                        self._process_poc_result(state, tool_name, result)
                    
                    # 标记任务完成
                    state.completed_tasks.append(tool_name)
                    if tool_name in state.planned_tasks:
                        state.planned_tasks.remove(tool_name)
                    
                    # 更新下一个任务
                    state.current_task = state.planned_tasks[0] if state.planned_tasks else None
                    
                    logger.info(f"[{state.task_id}] ✅ 工具 {tool_name} 执行完成")
                    
                    state.update_execution_step(
                        step_number,
                        result=result,
                        status="success",
                        output_data={
                            "tool_status": result.get("status"),
                            "has_data": "data" in result,
                            "data_keys": list(result.get("data", {}).keys()) if "data" in result and isinstance(result.get("data"), dict) else []
                        },
                        data_changes={
                            "completed_task": tool_name,
                            "remaining_tasks": len(state.planned_tasks)
                        },
                        state_transitions=["completed", "next_task"]
                    )
                else:
                    # 工具执行失败或超时
                    error_msg = result.get("error", "未知错误")
                    logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 执行失败: {error_msg}")
                    state.update_stage_status("plugins", "running", "scanning", progress, f"插件 {tool_name} 执行失败: {error_msg}")
                    state.add_error(f"工具执行失败 {tool_name}: {error_msg}")
                    state.increment_retry()
                    
                    state.update_execution_step(
                        step_number,
                        result=result,
                        status="failed",
                        output_data={
                            "error": error_msg,
                            "tool_status": result.get("status")
                        },
                        state_transitions=["failed", "retrying"]
                    )
                    
                    # 使用统一的重试逻辑
                    self._handle_retry(state, tool_name, step_number, error_msg)
                
        except ValueError as e:
            # 工具不存在的错误
            logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 不存在: {str(e)}")
            state.add_error(f"工具不存在: {tool_name}")
            
            state.update_execution_step(
                step_number,
                result={"error": f"工具不存在: {tool_name}"},
                status="failed",
                state_transitions=["failed", "tool_not_found"]
            )
            
            # 标记任务完成（跳过不存在的工具）
            state.completed_tasks.append(tool_name)
            if tool_name in state.planned_tasks:
                state.planned_tasks.remove(tool_name)
            state.current_task = state.planned_tasks[0] if state.planned_tasks else None
            
        except Exception as e:
            # 其他异常
            logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 执行异常: {str(e)}")
            state.update_stage_status("plugins", "running", "scanning", progress, f"插件 {tool_name} 执行异常: {str(e)}")
            state.add_error(f"工具执行异常 {tool_name}: {str(e)}")
            state.increment_retry()
            
            state.update_execution_step(
                step_number,
                result={"error": str(e)},
                status="failed",
                state_transitions=["failed", "retrying"]
            )
            
            # 使用统一的重试逻辑
            self._handle_retry(state, tool_name, step_number, str(e))
        
        return state
    
    def _handle_retry(self, state: AgentState, tool_name: str, step_number: int, error_msg: str):
        """
        处理工具重试逻辑
        
        Args:
            state: Agent状态
            tool_name: 工具名称
            step_number: 步骤编号
            error_msg: 错误消息
        """
        if state.retry_count < agent_config.MAX_RETRIES:
            logger.warning(f"[{state.task_id}] 🔄 工具 {tool_name} 重试 {state.retry_count}/{agent_config.MAX_RETRIES}")
        else:
            logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 达到最大重试次数")
            state.completed_tasks.append(tool_name)
            if tool_name in state.planned_tasks:
                state.planned_tasks.remove(tool_name)
            state.current_task = state.planned_tasks[0] if state.planned_tasks else None
            state.reset_retry()
            
            state.update_execution_step(
                step_number,
                status="failed",
                state_transitions=["failed", "max_retries_reached"]
            )
    
    def _update_context(self, state: AgentState, tool_name: str, result: Dict[str, Any]):
        """
        更新目标上下文
        
        Args:
            state: Agent状态
            tool_name: 工具名称
            result: 工具结果
        """
        if not result:
            logger.warning(f"工具 {tool_name} 返回结果为None")
            return
            
        if result.get("status") != "success":
            return
        
        data = result.get("data", {})
        if not isinstance(data, dict):
            logger.warning(f"工具 {tool_name} 返回的data不是字典类型: {type(data)}")
            data = {}
        
        # 使用字典映射来减少重复代码
        context_mapping = {
            "baseinfo": {
                "server": data.get("server"),
                "os": data.get("os"),
                "ip": data.get("ip"),
                "domain": data.get("domain")
            },
            "cms_identify": {
                "cms": data.get("cms", "unknown")
            },
            "portscan": {
                "open_ports": data.get("open_ports", [])
            },
            "waf_detect": {
                "waf": data.get("waf")
            },
            "cdn_detect": {
                "cdn": data.get("has_cdn")
            }
        }
        
        if tool_name in context_mapping:
            for key, value in context_mapping[tool_name].items():
                state.update_context(key, value)
    
    def _process_poc_result(self, state: AgentState, tool_name: str, result: Dict[str, Any]):
        """
        处理POC执行结果
        
        Args:
            state: Agent状态
            tool_name: POC名称
            result: POC执行结果
        """
        data = result.get("data", {})
        if data.get("vulnerable"):
            vuln_info = {
                "cve": tool_name.replace("poc_", ""),
                "target": state.target,
                "severity": self._get_severity(tool_name),
                "details": data.get("message", ""),
                "poc_name": tool_name
            }
            state.add_vulnerability(vuln_info)
            logger.warning(f"[{state.task_id}] 🚨 发现漏洞: {vuln_info}")
    
    def _get_severity(self, poc_name: str) -> str:
        """
        获取POC的严重度
        
        Args:
            poc_name: POC名称
            
        Returns:
            str: 严重度(critical/high/medium/low)
        """
        poc_lower = poc_name.lower()
        if "cve_2020_2551" in poc_lower or "cve_2023_21839" in poc_lower:
            return "critical"
        elif "cve" in poc_lower:
            return "high"
        else:
            return "medium"


class ResultVerificationNode:
    """
    结果验证节点
    
    验证扫描结果,根据上下文补充任务,决定是否继续执行。
    """
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        验证结果并补充任务
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{state.task_id}] 🔍 验证扫描结果")
        
        # 基于上下文补充POC任务
        self._supplement_poc_tasks(state)
        
        # 检查是否需要继续执行
        if not state.planned_tasks:
            logger.info(f"[{state.task_id}] ✅ 所有任务已完成")
            state.should_continue = False
            state.is_complete = True
        else:
            state.current_task = state.planned_tasks[0]
            logger.info(f"[{state.task_id}] 📋 待执行任务: {state.planned_tasks}")
        
        # 添加执行步骤
        state.add_execution_step(
            "result_verification",
            {"planned_tasks": state.planned_tasks},
            "success",
            step_type="result_verification"
        )
        logger.info(f"[{state.task_id}] ✅ 结果验证完成")
        return state
    
    def _supplement_poc_tasks(self, state: AgentState):
        """
        基于上下文补充POC任务
        
        Args:
            state: Agent状态
        """
        cms = state.target_context.get("cms", "").lower()
        open_ports = state.target_context.get("open_ports", [])
        
        # 使用集合来避免重复
        supplement_tasks = set()
        
        # 根据CMS补充POC
        if cms:
            cms_pocs = POCAdapter.get_poc_by_cms(cms)
            for poc in cms_pocs:
                if poc not in state.completed_tasks and poc not in state.planned_tasks:
                    supplement_tasks.add(poc)
        
        # 根据端口补充POC
        for port in open_ports:
            port_pocs = POCAdapter.get_poc_by_port(port)
            for poc in port_pocs:
                if poc not in state.completed_tasks and poc not in state.planned_tasks:
                    supplement_tasks.add(poc)
        
        # 添加到计划任务列表
        for task in supplement_tasks:
            if task not in state.planned_tasks:
                state.planned_tasks.append(task)
                logger.info(f"[{state.task_id}] ➕ 补充POC任务: {task}")


class VulnerabilityAnalysisNode:
    """
    漏洞分析节点
    
    分析发现的漏洞,进行去重、排序和严重度评估。
    """
    
    def __init__(self):
        from ..analyzers.vuln_analyzer import VulnerabilityAnalyzer
        self.analyzer = VulnerabilityAnalyzer()
        logger.info("🔍 漏洞分析节点初始化")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        分析漏洞
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{state.task_id}] 🔍 分析漏洞结果,共发现 {len(state.vulnerabilities)} 个漏洞")
        
        if not state.vulnerabilities:
            logger.info(f"[{state.task_id}] ✅ 未发现漏洞")
            state.add_execution_step(
                "vulnerability_analysis",
                {
                    "total": 0,
                    "vulnerabilities": []
                },
                "success",
                step_type="analysis"
            )
            return state
        
        try:
            # 去重
            unique_vulns = self.analyzer.deduplicate(state.vulnerabilities)
            
            # 排序
            sorted_vulns = self.analyzer.sort_by_severity(unique_vulns)
            
            # 更新状态
            state.vulnerabilities = sorted_vulns
            
            logger.info(f"[{state.task_id}] ✅ 漏洞分析完成,去重后: {len(sorted_vulns)} 个")
            state.add_execution_step(
                "vulnerability_analysis",
                {
                    "total": len(sorted_vulns),
                    "vulnerabilities": sorted_vulns
                },
                "success",
                step_type="analysis"
            )
            
        except AttributeError as e:
            logger.error(f"[{state.task_id}] ❌ 漏洞分析器方法不存在: {str(e)}")
            state.add_error(f"漏洞分析器方法不存在: {str(e)}")
            # 保持原始漏洞数据不变
            state.add_execution_step(
                "vulnerability_analysis",
                {
                    "total": len(state.vulnerabilities),
                    "vulnerabilities": state.vulnerabilities,
                    "error": str(e)
                },
                "failed",
                step_type="analysis"
            )
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 漏洞分析失败: {str(e)}")
            state.add_error(f"漏洞分析失败: {str(e)}")
            # 保持原始漏洞数据不变
            state.add_execution_step(
                "vulnerability_analysis",
                {
                    "total": len(state.vulnerabilities),
                    "vulnerabilities": state.vulnerabilities,
                    "error": str(e)
                },
                "failed",
                step_type="analysis"
            )
        
        return state


class ReportGenerationNode:
    """
    报告生成节点
    
    生成最终的扫描报告,包含所有结果和漏洞信息。
    """
    
    def __init__(self):
        from ..analyzers.report_gen import ReportGenerator
        self.report_gen = ReportGenerator()
        logger.info("📄 报告生成节点初始化")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        生成报告
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{state.task_id}] 📄 生成扫描报告")
        
        try:
            # 生成标准扫描报告
            report = self.report_gen.generate_report(state)
            state.tool_results["final_report"] = report
            
            # 生成详细的执行轨迹报告
            trace_report = self.report_gen.generate_execution_trace_report(state)
            state.tool_results["execution_trace_report"] = trace_report
            
            # 生成HTML格式的执行轨迹报告
            html_trace = self.report_gen.generate_html_execution_trace(state)
            state.tool_results["html_execution_trace"] = html_trace
            
            state.mark_complete()
            
            logger.info(f"[{state.task_id}] ✅ 报告生成完成")
            state.add_execution_step(
                "report_generation",
                {
                    "standard_report": report,
                    "trace_report": trace_report,
                    "html_trace": html_trace
                },
                "success",
                step_type="report_generation",
                processing_logic="生成标准扫描报告和详细执行轨迹报告",
                output_data={
                    "report_sections": [
                        "task_info",
                        "scan_summary",
                        "target_context",
                        "vulnerabilities",
                        "tool_results",
                        "errors",
                        "execution_trace",
                        "trace_summary",
                        "state_changes",
                        "performance_metrics"
                    ]
                }
            )
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 报告生成失败: {str(e)}")
            state.add_error(f"报告生成失败: {str(e)}")
            state.mark_complete()
        
        return state


# = 新增节点(从new_nodes.py合并)=

class EnvironmentAwarenessNode:
    """
    环境感知节点
    
    使用EnvironmentAwareness的单例模式避免重复初始化。
    """
    
    def __init__(self):
        from ..code_execution.environment import EnvironmentAwareness
        self.env_awareness = EnvironmentAwareness()
        logger.info("🔍 环境感知节点初始化完成")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        执行环境感知
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{state.task_id}] 🔍 开始环境感知")
        
        try:
            env_report = self.env_awareness.get_environment_report()
            
            state.update_context("environment_info", env_report)
            state.update_context("os_system", env_report["os_info"]["system"])
            state.update_context("python_version", env_report["python_info"]["version"])
            state.update_context("available_tools", env_report["available_tools"])
            
            logger.info(f"[{state.task_id}] ✅ 环境感知完成")
            state.add_execution_step("environment_awareness", env_report, "success")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 环境感知失败: {str(e)}")
            state.add_error(f"环境感知失败: {str(e)}")
        
        return state


class CodeGenerationNode:
    """
    代码生成节点
    
    根据扫描需求自动生成扫描脚本。
    """
    
    def __init__(self):
        from ..code_execution.code_generator import CodeGenerator
        self.code_generator = CodeGenerator()
        
        # 创建代码文件存储目录
        self.code_dir = Path(__file__).parent.parent / "code_execution" / "workspace" / "generated_code"
        self.code_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🔧 代码生成节点初始化完成")
    
    def _save_generated_code(
        self,
        code: str,
        language: str,
        scan_type: str,
        target: str,
        task_id: str
    ) -> str:
        """
        保存生成的代码到文件
        
        Args:
            code: 代码内容
            language: 代码语言
            scan_type: 扫描类型
            target: 扫描目标
            task_id: 任务ID
            
        Returns:
            str: 代码文件路径
        """
        try:
            # 生成唯一标识符
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_id = f"{task_id}_{scan_type}_{timestamp}"
            
            # 获取文件扩展名
            extensions = {
                "python": "py",
                "bash": "sh",
                "powershell": "ps1",
                "shell": "sh"
            }
            extension = extensions.get(language, "txt")
            
            # 创建代码文件
            code_file = self.code_dir / f"{file_id}.{extension}"
            
            # 写入代码文件
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            logger.info(f"代码文件已保存: {code_file}")
            return str(code_file)
            
        except Exception as e:
            logger.error(f"保存代码文件失败: {str(e)}")
            return ""
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        执行代码生成
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{state.task_id}] 🔧 开始代码生成")
        
        step_number = state.add_execution_step_start(
            "code_generation",
            step_type="code_generation",
            input_params={
                "target": state.target,
                "scan_type": state.target_context.get("custom_scan_type", "vuln_scan"),
                "requirements": state.target_context.get("custom_scan_requirements", ""),
                "language": state.target_context.get("custom_scan_language", "python")
            },
            processing_logic="根据扫描需求和目标特征生成自定义扫描代码"
        )
        
        try:
            target = state.target
            
            if not state.target_context.get("need_custom_scan"):
                logger.info(f"[{state.task_id}] ⏭️ 无需自定义扫描,跳过代码生成")
                state.update_execution_step(
                    step_number,
                    status="skipped",
                    output_data={"message": "无需自定义扫描"},
                    state_transitions=["skipped"]
                )
                return state
            
            scan_type = state.target_context.get("custom_scan_type", "vuln_scan")
            requirements = state.target_context.get("custom_scan_requirements", "")
            language = state.target_context.get("custom_scan_language", "python")
            
            code_response = await self.code_generator.generate_code(
                scan_type=scan_type,
                target=target,
                requirements=requirements,
                language=language
            )
            
            code_dict = code_response.to_dict()
            state.tool_results["generated_code"] = code_dict
            state.update_context("generated_code", code_dict)
            
            # 保存生成的代码到文件
            code_file_path = self._save_generated_code(
                code=code_response.code,
                language=language,
                scan_type=scan_type,
                target=target,
                task_id=state.task_id
            )
            
            if code_file_path:
                code_dict["file_path"] = code_file_path
                logger.info(f"[{state.task_id}] 📝 代码已保存到文件: {code_file_path}")
            
            logger.info(f"[{state.task_id}] ✅ 代码生成完成")
            
            state.update_execution_step(
                step_number,
                result=code_dict,
                status="success",
                output_data={
                    "code_length": len(code_response.code),
                    "language": code_response.language,
                    "dependencies": code_response.dependencies,
                    "file_path": code_file_path
                },
                data_changes={
                    "generated_code": True,
                    "scan_type": scan_type
                },
                state_transitions=["completed", "ready_for_execution"]
            )
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 代码生成失败: {str(e)}")
            state.add_error(f"代码生成失败: {str(e)}")
            
            state.update_execution_step(
                step_number,
                result={"error": str(e)},
                status="failed",
                state_transitions=["failed"]
            )
        
        return state


class CapabilityEnhancementNode:
    """
    功能补充节点
    
    根据需求动态增强AI Agent能力。
    """
    
    def __init__(self):
        from ..code_execution.capability_enhancer import CapabilityEnhancer
        self.capability_enhancer = CapabilityEnhancer()
        logger.info("🚀 功能补充节点初始化完成")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        执行功能补充
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{state.task_id}] 🚀 开始功能补充")
        
        step_number = state.add_execution_step_start(
            "capability_enhancement",
            step_type="capability_enhancement",
            input_params={
                "target": state.target,
                "requirement": state.target_context.get("capability_requirement", ""),
                "capability_name": state.target_context.get("capability_name")
            },
            processing_logic="根据需求动态增强AI Agent能力"
        )
        
        try:
            if not state.target_context.get("need_capability_enhancement"):
                logger.info(f"[{state.task_id}] ⏭️ 无需功能补充,跳过")
                state.update_execution_step(
                    step_number,
                    status="skipped",
                    output_data={"message": "无需功能补充"},
                    state_transitions=["skipped"]
                )
                return state
            
            requirement = state.target_context.get("capability_requirement", "")
            target = state.target
            capability_name = state.target_context.get("capability_name")
            
            if not requirement:
                logger.warning(f"[{state.task_id}] ⚠️ 未指定功能需求,跳过功能补充")
                state.update_execution_step(
                    step_number,
                    status="skipped",
                    output_data={"message": "未指定功能需求"},
                    state_transitions=["skipped"]
                )
                return state
            
            enhance_result = await self.capability_enhancer.enhance_capability(
                requirement=requirement,
                target=target,
                capability_name=capability_name
            )
            
            state.tool_results["capability_enhancement"] = enhance_result
            state.update_context("enhanced_capability", enhance_result)
            
            # 清除功能增强需求标志，避免无限循环
            state.target_context["need_capability_enhancement"] = False
            
            logger.info(f"[{state.task_id}] ✅ 功能补充完成")
            
            state.update_execution_step(
                step_number,
                result=enhance_result,
                status="success" if enhance_result.get("status") == "success" else "failed",
                output_data={
                    "capability_name": enhance_result.get("capability", {}).get("name"),
                    "capability_version": enhance_result.get("capability", {}).get("version"),
                    "code_file": enhance_result.get("code_file")
                },
                data_changes={
                    "enhanced_capability": True,
                    "capability_name": enhance_result.get("capability", {}).get("name")
                },
                state_transitions=["completed", "capability_available"]
            )
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 功能补充失败: {str(e)}")
            state.add_error(f"功能补充失败: {str(e)}")
            
            state.update_execution_step(
                step_number,
                result={"error": str(e)},
                status="failed",
                state_transitions=["failed"]
            )
        
        return state


class CodeExecutionNode:
    """
    代码执行节点
    
    执行生成的代码或自定义脚本。
    """
    
    def __init__(self):
        from ..code_execution.executor import UnifiedExecutor
        from ..agent_config import agent_config
        self.executor = UnifiedExecutor(
            timeout=agent_config.TOOL_TIMEOUT,
            enable_sandbox=True
        )
        logger.info("⚡ 代码执行节点初始化完成")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        执行代码
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{state.task_id}] ⚡ 开始执行代码")
        
        try:
            if not state.target_context.get("generated_code"):
                logger.info(f"[{state.task_id}] ⏭️ 无代码可执行,跳过")
                return state
            
            generated_code = state.target_context["generated_code"]
            target = state.target
            
            execution_result = await self.executor.execute_code(
                code=generated_code["code"],
                language=generated_code["language"],
                target=target
            )
            
            state.tool_results["code_execution"] = execution_result.to_dict()
            state.update_context("code_execution_result", execution_result.to_dict())
            
            if execution_result.status == "success":
                logger.info(f"[{state.task_id}] ✅ 代码执行成功")
            else:
                logger.warning(f"[{state.task_id}] ⚠️ 代码执行失败: {execution_result.error}")
                # 设置需要功能增强标志
                state.target_context["need_capability_enhancement"] = True
                state.target_context["capability_requirement"] = "自动安装代码执行所需依赖"
            
            state.add_execution_step(
                "code_execution",
                execution_result.to_dict(),
                execution_result.status,
                step_type="code_execution"
            )
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 代码执行失败: {str(e)}")
            state.add_error(f"代码执行失败: {str(e)}")
        
        return state


class IntelligentDecisionNode:
    """
    智能决策节点
    
    基于环境信息和扫描结果,智能决定下一步操作。
    使用EnvironmentAwareness的单例模式避免重复初始化。
    """
    
    def __init__(self):
        from ..code_execution.environment import EnvironmentAwareness
        self.env_awareness = EnvironmentAwareness()
        logger.info("🧠 智能决策节点初始化完成")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        执行智能决策
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{state.task_id}] 🧠 开始智能决策")
        
        try:
            env_info = self.env_awareness.get_environment_report()
            target_context = state.target_context
            
            decisions = []
            
            # 基于环境信息决策
            os_system = env_info["os_info"]["system"]
            if os_system == "Windows":
                decisions.append("使用PowerShell执行脚本")
            else:
                decisions.append("使用Bash执行脚本")
            
            # 基于可用工具决策
            available_tools = [
                name for name, info in env_info["available_tools"].items()
                if info.get("available", False)
            ]
            
            if "nmap" in available_tools:
                decisions.append("使用nmap进行端口扫描")
            else:
                decisions.append("使用Python进行端口扫描")
            
            # 基于目标特征决策
            cms = target_context.get("cms", "").lower()
            if "weblogic" in cms:
                decisions.append("执行WebLogic相关POC")
            elif "tomcat" in cms:
                decisions.append("执行Tomcat相关POC")
            elif "struts2" in cms:
                decisions.append("执行Struts2相关POC")
            
            # 基于网络状态决策
            network_info = env_info["network_info"]
            if network_info.get("proxy_detected"):
                decisions.append("检测到代理,调整扫描策略")
            if network_info.get("firewall_detected"):
                decisions.append("检测到防火墙,降低扫描速度")
            
            state.update_context("intelligent_decisions", decisions)
            
            logger.info(f"[{state.task_id}] ✅ 智能决策完成: {decisions}")
            state.add_execution_step("intelligent_decision", {"decisions": decisions}, "success")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 智能决策失败: {str(e)}")
            state.add_error(f"智能决策失败: {str(e)}")
        
        return state

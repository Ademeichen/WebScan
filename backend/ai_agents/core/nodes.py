"""
LangGraph 节点定义

定义Agent工作流中的各个节点函数。
"""
import logging
import asyncio
from typing import Dict, Any, List
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
    
    根据用户需求和目标特征，生成扫描任务计划。
    支持规则化规划和LLM增强规划两种模式。
    """
    
    def __init__(self):
        self.priority_manager = TaskPriorityManager()
        
        if agent_config.ENABLE_LLM_PLANNING:
            self.llm = ChatOpenAI(
                model=agent_config.MODEL_ID,
                temperature=0,
                openai_api_key=agent_config.OPENAI_API_KEY,
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
        logger.info(f"[{state.task_id}] 📋 开始任务规划，目标: {state.target}")
        
        try:
            if self.use_llm:
                planned_tasks = await self._llm_planning(state)
            else:
                planned_tasks = await self._rule_based_planning(state)
            
            state.planned_tasks = planned_tasks
            state.current_task = planned_tasks[0] if planned_tasks else None
            
            logger.info(f"[{state.task_id}] ✅ 任务规划完成: {planned_tasks}")
            state.add_execution_step("task_planning", {"tasks": planned_tasks}, "success")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 任务规划失败: {str(e)}")
            state.add_error(f"任务规划失败: {str(e)}")
            state.planned_tasks = agent_config.DEFAULT_SCAN_TASKS
            state.current_task = state.planned_tasks[0] if state.planned_tasks else None
        
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
            context_info = f"\n目标上下文: {state.target_context}"
        
        system_prompt = """
        你是Web安全扫描专家，需要为目标规划扫描任务。
        
        可用工具列表：
        {tools}
        
        规划规则：
        1. 先执行基础信息收集类任务（baseinfo、portscan、waf_detect、cdn_detect、cms_identify）
        2. 根据基础信息结果选择POC验证任务（如CMS为WordPress则跳过WebLogic POC）
        3. 避免无意义的POC扫描
        4. 返回格式为JSON数组，仅包含任务名称
        5. 任务优先级：POC验证 > 端口扫描 > 基础信息收集
        """
        
        user_prompt = f"目标: {state.target}{context_info}"
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt)
            ])
            
            chain = prompt | self.llm | JsonOutputParser(pydantic_object=PlanningResponse)
            result = await chain.ainvoke({})
            
            logger.info(f"LLM规划结果: {result.plan}")
            return result.plan
        except Exception as e:
            logger.error(f"LLM规划失败，使用规则化规划: {str(e)}")
            return await self._rule_based_planning(state)


class ToolExecutionNode:
    """
    工具执行节点
    
    执行当前规划的任务，调用相应的工具并更新状态。
    """
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(agent_config.MAX_CONCURRENT_TOOLS)
        logger.info(f"🔧 工具执行节点初始化，最大并发: {agent_config.MAX_CONCURRENT_TOOLS}")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        执行工具
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        if not state.current_task:
            logger.info(f"[{state.task_id}] ⏹️ 没有待执行任务")
            state.is_complete = True
            return state
        
        tool_name = state.current_task
        logger.info(f"[{state.task_id}] 🔧 执行工具: {tool_name}")
        
        try:
            async with self.semaphore:
                result = await registry.call_tool(tool_name, state.target)
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
                
                state.add_execution_step(tool_name, result, "success")
                logger.info(f"[{state.task_id}] ✅ 工具 {tool_name} 执行完成")
                
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 执行失败: {str(e)}")
            state.add_error(f"工具执行失败 {tool_name}: {str(e)}")
            state.increment_retry()
            
            # 重试逻辑
            if state.retry_count < agent_config.MAX_RETRIES:
                logger.warning(f"[{state.task_id}] 🔄 工具 {tool_name} 重试 {state.retry_count}/{agent_config.MAX_RETRIES}")
            else:
                logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 达到最大重试次数")
                state.completed_tasks.append(tool_name)
                if tool_name in state.planned_tasks:
                    state.planned_tasks.remove(tool_name)
                state.current_task = state.planned_tasks[0] if state.planned_tasks else None
                state.reset_retry()
        
        return state
    
    def _update_context(self, state: AgentState, tool_name: str, result: Dict[str, Any]):
        """
        更新目标上下文
        
        Args:
            state: Agent状态
            tool_name: 工具名称
            result: 工具结果
        """
        if result.get("status") != "success":
            return
        
        data = result.get("data", {})
        
        if tool_name == "baseinfo":
            state.update_context("server", data.get("server"))
            state.update_context("os", data.get("os"))
            state.update_context("ip", data.get("ip"))
        elif tool_name == "cms_identify":
            state.update_context("cms", data.get("cms", "unknown"))
        elif tool_name == "portscan":
            state.update_context("open_ports", data.get("open_ports", []))
        elif tool_name == "waf_detect":
            state.update_context("waf", data.get("waf"))
        elif tool_name == "cdn_detect":
            state.update_context("cdn", data.get("has_cdn"))
    
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
            str: 严重度（critical/high/medium/low）
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
    
    验证扫描结果，根据上下文补充任务，决定是否继续执行。
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
        else:
            state.current_task = state.planned_tasks[0]
            logger.info(f"[{state.task_id}] 📋 待执行任务: {state.planned_tasks}")
        
        state.add_execution_step("result_verification", {"planned_tasks": state.planned_tasks}, "success")
        return state
    
    def _supplement_poc_tasks(self, state: AgentState):
        """
        基于上下文补充POC任务
        
        Args:
            state: Agent状态
        """
        cms = state.target_context.get("cms", "").lower()
        open_ports = state.target_context.get("open_ports", [])
        
        supplement_tasks = []
        
        # 根据CMS补充POC
        if cms:
            cms_pocs = POCAdapter.get_poc_by_cms(cms)
            for poc in cms_pocs:
                if poc not in state.completed_tasks and poc not in state.planned_tasks:
                    supplement_tasks.append(poc)
        
        # 根据端口补充POC
        for port in open_ports:
            port_pocs = POCAdapter.get_poc_by_port(port)
            for poc in port_pocs:
                if poc not in state.completed_tasks and poc not in state.planned_tasks:
                    supplement_tasks.append(poc)
        
        # 去重并添加
        for task in supplement_tasks:
            if task not in state.planned_tasks:
                state.planned_tasks.append(task)
                logger.info(f"[{state.task_id}] ➕ 补充POC任务: {task}")


class VulnerabilityAnalysisNode:
    """
    漏洞分析节点
    
    分析发现的漏洞，进行去重、排序和严重度评估。
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
        logger.info(f"[{state.task_id}] 🔍 分析漏洞结果，共发现 {len(state.vulnerabilities)} 个漏洞")
        
        if not state.vulnerabilities:
            logger.info(f"[{state.task_id}] ✅ 未发现漏洞")
            return state
        
        try:
            # 去重
            unique_vulns = self.analyzer.deduplicate(state.vulnerabilities)
            
            # 排序
            sorted_vulns = self.analyzer.sort_by_severity(unique_vulns)
            
            # 更新状态
            state.vulnerabilities = sorted_vulns
            
            logger.info(f"[{state.task_id}] ✅ 漏洞分析完成，去重后: {len(sorted_vulns)} 个")
            state.add_execution_step("vulnerability_analysis", {
                "total": len(sorted_vulns),
                "vulnerabilities": sorted_vulns
            }, "success")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 漏洞分析失败: {str(e)}")
            state.add_error(f"漏洞分析失败: {str(e)}")
        
        return state


class ReportGenerationNode:
    """
    报告生成节点
    
    生成最终的扫描报告，包含所有结果和漏洞信息。
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
            report = self.report_gen.generate_report(state)
            state.tool_results["final_report"] = report
            state.mark_complete()
            
            logger.info(f"[{state.task_id}] ✅ 报告生成完成")
            state.add_execution_step("report_generation", report, "success")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 报告生成失败: {str(e)}")
            state.add_error(f"报告生成失败: {str(e)}")
            state.mark_complete()
        
        return state

"""
LangGraph 节点定义

定义Agent工作流中的各个节点函数。
"""
import logging
import asyncio
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
        4. 返回格式为JSON数组,仅包含任务名称
        5. 任务优先级:POC验证 > 端口扫描 > 基础信息收集
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
        if not state.current_task:
            logger.info(f"[{state.task_id}] ⏹️ 没有待执行任务")
            # 不要立即标记为完成，让工作流继续执行到result_verification节点
            return state
        
        tool_name = state.current_task
        logger.info(f"[{state.task_id}] 🔧 执行工具: {tool_name}")
        
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
                result = await registry.call_tool(tool_name, state.target)
                
                # 检查工具执行状态
                if result.get("status") == "success":
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
                "ip": data.get("ip")
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


class SeebugAgentNode:
    """
    Seebug Agent 节点
    
    负责集成Seebug_Agent功能,包括:
    - 搜索Seebug POC
    - 生成POC代码
    - 下载POC
    """
    
    def __init__(self):
        """
        初始化Seebug Agent节点
        """
        try:
            from backend.utils.seebug_utils import seebug_utils
            self.seebug_agent = seebug_utils.get_agent()
            logger.info("✅ Seebug Agent节点初始化完成")
        except ImportError as e:
            logger.warning(f"⚠️ Seebug Agent节点初始化失败: {str(e)}")
            self.seebug_agent = None
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        执行Seebug Agent节点
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{state.task_id}] 🔍 开始执行Seebug Agent节点,目标: {state.target}")
        
        try:
            # 检查Seebug Agent是否可用
            if not self.seebug_agent:
                logger.warning(f"[{state.task_id}] ⚠️ Seebug Agent不可用")
                state.add_error("Seebug Agent不可用")
                state.add_execution_step("seebug_agent", {}, "failed")
                return state
            
            # 从目标中提取关键词用于搜索
            keyword = self._extract_keyword_from_target(state.target)
            
            # 如果没有提取到关键词，使用默认关键词
            if not keyword:
                keyword = "web vulnerability"
                logger.info(f"[{state.task_id}] ℹ️ 未提取到关键词，使用默认关键词: {keyword}")
            
            # 搜索Seebug POC
            logger.info(f"[{state.task_id}] 🔍 搜索Seebug POC,关键词: {keyword}")
            search_result = self.seebug_agent.search_vulnerabilities(
                keyword=keyword,
                page=1,
                page_size=10
            )
            
            if search_result.get("status") == "success":
                poc_list = search_result.get("data", {}).get("list", [])
                logger.info(f"[{state.task_id}] ✅ Seebug搜索成功,找到 {len(poc_list)} 个POC")
                
                # 将搜索结果添加到状态
                state.seebug_pocs = poc_list
                
                # 如果找到POC,处理前几个进行详细分析
                if poc_list:
                    # 处理前3个POC以提高覆盖率
                    for i, selected_poc in enumerate(poc_list[:3]):
                        ssvid = selected_poc.get("ssvid")
                        poc_name = selected_poc.get("name")
                        
                        if ssvid:
                            logger.info(f"[{state.task_id}] 🔍 处理第 {i+1} 个POC: {poc_name} (SSVID: {ssvid})")
                            
                            # 获取POC详情
                            detail_result = self.seebug_agent.get_vulnerability_detail(ssvid)
                            
                            if detail_result.get("status") == "success":
                                vul_data = detail_result.get("data", {})
                                logger.info(f"[{state.task_id}] ✅ 获取POC详情成功: {poc_name}")
                                
                                # 生成POC代码
                                poc_code = self.seebug_agent.generate_poc(vul_data)
                                
                                if poc_code:
                                    logger.info(f"[{state.task_id}] ✅ POC生成成功,代码长度: {len(poc_code)}")
                                    
                                    # 将生成的POC添加到状态
                                    state.generated_pocs = state.generated_pocs or []
                                    state.generated_pocs.append({
                                        "ssvid": ssvid,
                                        "name": poc_name,
                                        "code": poc_code,
                                        "source": "seebug_agent",
                                        "priority": 1 if i == 0 else 2
                                    })
                                    
                                    # 添加到POC验证任务列表
                                    state.poc_verification_tasks = state.poc_verification_tasks or []
                                    state.poc_verification_tasks.append({
                                        "poc_id": f"seebug_{ssvid}",
                                        "poc_name": poc_name,
                                        "poc_code": poc_code,
                                        "target": state.target,
                                        "priority": 1 if i == 0 else 2
                                    })
                                else:
                                    logger.warning(f"[{state.task_id}] ⚠️ POC生成失败: {poc_name}")
                            else:
                                logger.warning(f"[{state.task_id}] ⚠️ 获取POC详情失败: {poc_name}")
                else:
                    logger.warning(f"[{state.task_id}] ⚠️ 未找到相关POC")
            else:
                error_msg = search_result.get('msg', '未知错误')
                logger.warning(f"[{state.task_id}] ⚠️ Seebug搜索失败: {error_msg}")
                state.add_error(f"Seebug搜索失败: {error_msg}")
            
            # 统计信息
            poc_count = len(state.seebug_pocs) if state.seebug_pocs else 0
            generated_count = len(state.generated_pocs) if state.generated_pocs else 0
            
            state.add_execution_step("seebug_agent", {
                "keyword": keyword,
                "poc_count": poc_count,
                "generated_count": generated_count
            }, "success" if generated_count > 0 else "partial")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ Seebug Agent节点执行失败: {str(e)}")
            state.add_error(f"Seebug Agent节点执行失败: {str(e)}")
            state.add_execution_step("seebug_agent", {}, "failed")
        
        return state
    
    def _extract_keyword_from_target(self, target: str) -> str:
        """
        从目标中提取搜索关键词
        
        Args:
            target: 目标URL或域名
            
        Returns:
            str: 搜索关键词
        """
        # 简单实现:从URL中提取域名作为关键词
        # 实际应用中可以使用更复杂的逻辑
        if "://" in target:
            target = target.split("://")[1]
        
        # 移除端口号和路径
        if "/" in target:
            target = target.split("/")[0]
        if ":" in target:
            target = target.split(":")[0]
        
        # 如果是IP地址,返回空字符串
        if target.replace(".", "").isdigit():
            return ""
        
        # 提取主域名
        parts = target.split(".")
        if len(parts) >= 2:
            return parts[-2]
        
        return target


class POCVerificationNode:
    """
    POC 验证节点
    
    基于 LangGraph 框架的 POC 验证节点,实现 agent 驱动的 POC 验证流程。
    """
    
    def __init__(self):
        """
        初始化 POC 验证节点
        """
        self.node_name = "poc_verification"
        self.description = "POC 验证节点,负责执行 POC 验证任务"
        
        logger.info("✅ POC 验证节点初始化完成")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        节点调用方法
        
        这是 LangGraph 节点的标准接口,接收 AgentState 并返回更新后的状态。
        
        Args:
            state: 当前智能体状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{self.node_name}] 🚀 开始执行 POC 验证节点")
        
        try:
            # 检查 POC 验证是否启用
            try:
                from config import settings
                if not settings.POC_VERIFICATION_ENABLED:
                    logger.warning(f"[{self.node_name}] ⚠️ POC 验证功能已禁用")
                    state.add_execution_step("poc_verification", {}, "disabled")
                    return state
            except ImportError:
                logger.warning(f"[{self.node_name}] ⚠️ 无法导入配置，默认启用POC验证")
            
            # 从状态中获取待验证的 POC 任务
            poc_tasks = state.poc_verification_tasks
            
            if not poc_tasks:
                logger.info(f"[{self.node_name}] ℹ️ 没有待验证的 POC 任务")
                state.add_execution_step("poc_verification", {}, "completed")
                return state
            
            # 更新验证状态为运行中
            logger.info(f"[{self.node_name}] 📋 待验证 POC 任务数: {len(poc_tasks)}")
            
            # 执行 POC 验证
            verification_results = await self._execute_poc_verification(
                poc_tasks,
                state
            )
            
            # 分析验证结果
            analysis_results = await self._analyze_verification_results(
                verification_results
            )
            
            # 更新漏洞列表
            state.vulnerabilities = self._update_vulnerabilities(
                state.vulnerabilities,
                verification_results
            )
            
            # 计算执行统计信息
            execution_stats = self._calculate_execution_stats(verification_results)
            
            # 记录POC验证结果到工具结果
            state.tool_results["poc_verification"] = {
                "verification_results": verification_results,
                "analysis_results": analysis_results,
                "execution_stats": execution_stats
            }
            
            # 添加执行步骤
            state.add_execution_step("poc_verification", {
                "verification_results": verification_results,
                "analysis_results": analysis_results,
                "execution_stats": execution_stats
            }, "success")
            
            logger.info(f"[{self.node_name}] ✅ POC 验证节点执行完成")
            
        except Exception as e:
            logger.error(f"[{self.node_name}] ❌ POC 验证节点执行失败: {str(e)}")
            state.add_error(f"POC 验证节点执行失败: {str(e)}")
            state.add_execution_step("poc_verification", {}, "failed")
        
        return state
    
    async def _execute_poc_verification(
        self,
        poc_tasks: List[Dict[str, Any]],
        state: AgentState
    ) -> List[Dict[str, Any]]:
        """
        执行 POC 验证
        
        Args:
            poc_tasks: POC 任务列表
            state: 当前智能体状态
            
        Returns:
            List[Dict]: 验证结果列表
        """
        logger.info(f"[{self.node_name}] 🔄 开始执行 POC 验证")
        
        verification_results = []
        
        # 从智能体状态获取目标信息
        target = state.target
        
        # 导入必要的模块
        try:
            try:
                from ai_agents.poc_system import poc_manager, verification_engine
            except ImportError:
                from poc_system import poc_manager, verification_engine
            from datetime import datetime
        except ImportError:
            logger.warning(f"[{self.node_name}] ⚠️ 无法导入poc_system模块，跳过POC验证")
            return []
        
        # 为每个 POC 任务创建验证任务并执行
        for poc_task in poc_tasks:
            try:
                # 验证POC脚本格式
                poc_code = poc_task.get("poc_code")
                if poc_code:
                    validation_result = poc_manager.validate_poc_script(poc_code)
                    if not validation_result["is_valid"]:
                        logger.warning(f"[{self.node_name}] ⚠️ POC脚本格式验证失败: {validation_result['errors']}")
                        # 跳过格式不正确的POC
                        continue
                
                # 创建 POC 验证任务
                verification_task = await poc_manager.create_verification_task(
                    poc_id=poc_task.get("poc_id"),
                    target=target,
                    priority=poc_task.get("priority", 5),
                    task_id=state.task_id
                )
                
                # 执行验证
                result = await verification_engine.execute_verification_task(
                    verification_task
                )
                
                # 转换为字典格式
                result_dict = {
                    "poc_name": result.poc_name,
                    "poc_id": result.poc_id,
                    "target": result.target,
                    "vulnerable": result.vulnerable,
                    "message": result.message,
                    "output": result.output,
                    "error": result.error,
                    "execution_time": result.execution_time,
                    "confidence": result.confidence,
                    "severity": result.severity,
                    "cvss_score": result.cvss_score,
                    "created_at": result.created_at.isoformat()
                }
                
                verification_results.append(result_dict)
                
                logger.info(
                    f"[{self.node_name}] ✅ POC 验证完成: "
                    f"{result.poc_name} -> {result.vulnerable}"
                )
                
            except Exception as e:
                logger.error(
                    f"[{self.node_name}] ❌ POC 验证失败: "
                    f"{poc_task.get('poc_name', 'unknown')} - {str(e)}"
                )
                
                # 添加失败结果
                verification_results.append({
                    "poc_name": poc_task.get("poc_name", "unknown"),
                    "poc_id": poc_task.get("poc_id", ""),
                    "target": target,
                    "vulnerable": False,
                    "message": f"验证失败: {str(e)}",
                    "output": "",
                    "error": str(e),
                    "execution_time": 0.0,
                    "confidence": 0.0,
                    "severity": "info",
                    "cvss_score": 0.0,
                    "created_at": datetime.now().isoformat()
                })
        
        return verification_results
    
    async def _analyze_verification_results(
        self,
        verification_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析验证结果
        
        Args:
            verification_results: 验证结果列表
            
        Returns:
            Dict: 分析结果
        """
        logger.info(f"[{self.node_name}] 🔍 开始分析验证结果")
        
        # 导入必要的模块
        try:
            from ai_agents.poc_system import result_analyzer
        except ImportError:
            from poc_system import result_analyzer
        from datetime import datetime
        
        # 转换为 POCVerificationResult 对象
        result_objects = []
        for result_dict in verification_results:
            # 这里简化处理，直接使用字典进行分析
            result_objects.append(result_dict)
        
        # 批量分析
        # 由于 result_analyzer.analyze_batch_results 可能需要特定的对象格式
        # 这里我们使用简化的分析方法
        total_results = len(verification_results)
        vulnerable_count = sum(1 for r in verification_results if r.get("vulnerable"))
        not_vulnerable_count = total_results - vulnerable_count
        
        analysis_summary = {
            "total_results": total_results,
            "vulnerable_count": vulnerable_count,
            "not_vulnerable_count": not_vulnerable_count,
            "average_confidence": sum(r.get("confidence", 0.0) for r in verification_results) / total_results if total_results > 0 else 0.0,
            "average_cvss_score": sum(r.get("cvss_score", 0.0) for r in verification_results) / total_results if total_results > 0 else 0.0
        }
        
        logger.info(
            f"[{self.node_name}] ✅ 验证结果分析完成: "
            f"漏洞 {analysis_summary['vulnerable_count']}/{analysis_summary['total_results']}"
        )
        
        return analysis_summary
    
    def _calculate_execution_stats(
        self,
        verification_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        计算执行统计信息
        
        Args:
            verification_results: 验证结果列表
            
        Returns:
            Dict: 执行统计信息
        """
        total_pocs = len(verification_results)
        executed_count = total_pocs
        vulnerable_count = sum(
            1 for r in verification_results if r.get("vulnerable")
        )
        failed_count = sum(
            1 for r in verification_results if r.get("error")
        )
        
        total_execution_time = sum(
            r.get("execution_time", 0.0) for r in verification_results
        )
        average_execution_time = (
            total_execution_time / executed_count if executed_count > 0 else 0.0
        )
        success_rate = (
            (executed_count - failed_count) / executed_count * 100
            if executed_count > 0 else 0.0
        )
        
        return {
            "total_pocs": total_pocs,
            "executed_count": executed_count,
            "vulnerable_count": vulnerable_count,
            "failed_count": failed_count,
            "success_rate": success_rate,
            "total_execution_time": total_execution_time,
            "average_execution_time": average_execution_time
        }
    
    def _update_vulnerabilities(
        self,
        existing_vulnerabilities: List[Dict[str, Any]],
        verification_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        更新漏洞列表
        
        Args:
            existing_vulnerabilities: 现有漏洞列表
            verification_results: 验证结果列表
            
        Returns:
            List[Dict]: 更新后的漏洞列表
        """
        updated_vulnerabilities = list(existing_vulnerabilities)
        
        # 添加新发现的漏洞
        from datetime import datetime
        for result in verification_results:
            if result.get("vulnerable"):
                vulnerability = {
                    "name": result.get("poc_name", ""),
                    "poc_id": result.get("poc_id", ""),
                    "target": result.get("target", ""),
                    "severity": result.get("severity", "medium"),
                    "cvss_score": result.get("cvss_score", 0.0),
                    "confidence": result.get("confidence", 0.0),
                    "message": result.get("message", ""),
                    "source": "poc_verification",
                    "discovered_at": result.get("created_at", datetime.now().isoformat())
                }
                updated_vulnerabilities.append(vulnerability)
        
        return updated_vulnerabilities

"""
新增节点定义

添加环境感知、代码生成和功能补充节点到AI Agent系统。
"""
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..core.state import AgentState
from ..code_execution.environment import EnvironmentAwareness
from ..code_execution.code_generator import CodeGenerator
from ..code_execution.capability_enhancer import CapabilityEnhancer
from ..code_execution.executor import UnifiedExecutor
from ..config import agent_config

logger = logging.getLogger(__name__)


class EnvironmentAwarenessNode:
    """
    环境感知节点
    
    负责收集和分析环境信息，为后续决策提供依据。
    """
    
    def __init__(self):
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
        self.code_generator = CodeGenerator()
        logger.info("🔧 代码生成节点初始化完成")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        执行代码生成
        
        Args:
            state: Agent当前状态
            
        Returns:
            AgentState: 更新后的状态
        """
        logger.info(f"[{state.task_id}] 🔧 开始代码生成")
        
        try:
            target = state.target
            
            if not state.target_context.get("need_custom_scan"):
                logger.info(f"[{state.task_id}] ⏭️ 无需自定义扫描，跳过代码生成")
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
            
            state.tool_results["generated_code"] = code_response.to_dict()
            state.update_context("generated_code", code_response.to_dict())
            
            logger.info(f"[{state.task_id}] ✅ 代码生成完成")
            state.add_execution_step("code_generation", code_response.to_dict(), "success")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 代码生成失败: {str(e)}")
            state.add_error(f"代码生成失败: {str(e)}")
        
        return state


class CapabilityEnhancementNode:
    """
    功能补充节点
    
    根据需求动态增强AI Agent能力。
    """
    
    def __init__(self):
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
        
        try:
            if not state.target_context.get("need_capability_enhancement"):
                logger.info(f"[{state.task_id}] ⏭️ 无需功能补充，跳过")
                return state
            
            requirement = state.target_context.get("capability_requirement", "")
            target = state.target
            
            if not requirement:
                logger.warning(f"[{state.task_id}] ⚠️ 未指定功能需求，跳过功能补充")
                return state
            
            enhance_result = await self.capability_enhancer.enhance_capability(
                requirement=requirement,
                target=target
            )
            
            state.tool_results["capability_enhancement"] = enhance_result
            state.update_context("enhanced_capability", enhance_result)
            
            logger.info(f"[{state.task_id}] ✅ 功能补充完成")
            state.add_execution_step("capability_enhancement", enhance_result, "success")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 功能补充失败: {str(e)}")
            state.add_error(f"功能补充失败: {str(e)}")
        
        return state


class CodeExecutionNode:
    """
    代码执行节点
    
    执行生成的代码或自定义脚本。
    """
    
    def __init__(self):
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
                logger.info(f"[{state.task_id}] ⏭️ 无代码可执行，跳过")
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
            
            state.add_execution_step("code_execution", execution_result.to_dict(), execution_result.status)
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 代码执行失败: {str(e)}")
            state.add_error(f"代码执行失败: {str(e)}")
        
        return state


class IntelligentDecisionNode:
    """
    智能决策节点
    
    基于环境信息和扫描结果，智能决定下一步操作。
    """
    
    def __init__(self):
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
                decisions.append("检测到代理，调整扫描策略")
            if network_info.get("firewall_detected"):
                decisions.append("检测到防火墙，降低扫描速度")
            
            state.update_context("intelligent_decisions", decisions)
            
            logger.info(f"[{state.task_id}] ✅ 智能决策完成: {decisions}")
            state.add_execution_step("intelligent_decision", {"decisions": decisions}, "success")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ 智能决策失败: {str(e)}")
            state.add_error(f"智能决策失败: {str(e)}")
        
        return state

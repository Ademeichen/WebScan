"""
LangGraph 节点定义

定义Agent工作流中的各个节点函数。
优化版本：使用基类减少重复代码，统一错误处理和上下文更新逻辑。
"""
import logging
import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, TypeVar
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

from .state import AgentState
from ..tools.registry import registry
from ..tools.adapters import PluginAdapter, POCAdapter
from ..agent_config import agent_config
from ..utils.priority import TaskPriorityManager

logger = logging.getLogger(__name__)


class PlanningResponse(BaseModel):
    """规划响应模型，用于LLM规划器的输出解析"""
    plan: List[str]
    reasoning: str


class NodeStage(Enum):
    """节点阶段枚举"""
    INFO_COLLECTION = "info_collection"
    VULN_SCAN = "vuln_scan"
    POC_VERIFICATION = "poc_verification"
    RESULT_ANALYSIS = "result_analysis"


@dataclass
class ExecutionContext:
    """执行上下文，用于跟踪执行状态"""
    task_id: str
    target: str
    stage: NodeStage
    start_time: datetime = field(default_factory=datetime.now)
    completed_count: int = 0
    total_count: int = 0
    
    @property
    def progress(self) -> int:
        if self.total_count == 0:
            return 0
        return int((self.completed_count / self.total_count) * 100)


class TargetContextUpdater:
    """
    目标上下文更新器
    
    统一管理目标上下文的更新逻辑，避免在多个节点中重复代码。
    """
    
    CONTEXT_MAPPINGS = {
        "baseinfo": {
            "server": "server",
            "os": "os", 
            "ip": "ip",
            "domain": "domain",
            "title": "title",
            "headers": "headers"
        },
        "cms_identify": {
            "cms": "cms"
        },
        "portscan": {
            "open_ports": "open_ports"
        },
        "waf_detect": {
            "waf": "waf"
        },
        "cdn_detect": {
            "cdn": "is_cdn",
            "has_cdn": "has_cdn"
        },
        "subdomain_scan": {
            "subdomains": "subdomains"
        },
        "webside_scan": {
            "side_domains": "side_domains"
        },
        "iplocating": {
            "location": "location"
        },
        "infoleak_scan": {
            "leaks": "leaks"
        },
        "dirscan": {
            "directories": "directories"
        }
    }
    
    @classmethod
    def update_context(cls, state: AgentState, tool_name: str, data: Dict[str, Any]) -> None:
        """
        根据工具名称更新目标上下文
        
        Args:
            state: Agent状态
            tool_name: 工具名称
            data: 工具返回的数据
        """
        if not data or not isinstance(data, dict):
            logger.warning(f"工具 {tool_name} 返回数据无效")
            return
        
        if tool_name not in cls.CONTEXT_MAPPINGS:
            logger.debug(f"工具 {tool_name} 无上下文映射配置")
            return
        
        mapping = cls.CONTEXT_MAPPINGS[tool_name]
        for state_key, data_key in mapping.items():
            value = data.get(data_key)
            if value is not None:
                state.update_context(state_key, value)
                logger.debug(f"更新上下文: {state_key} = {value}")


class ProgressCalculator:
    """
    进度计算器
    
    统一管理进度计算逻辑。
    """
    
    @staticmethod
    def calculate_progress(completed: int, total: int) -> int:
        """计算百分比进度"""
        if total <= 0:
            return 0
        return min(100, int((completed / total) * 100))
    
    @staticmethod
    def calculate_stage_progress(
        completed_tasks: List[str],
        planned_tasks: List[str],
        current_task: Optional[str] = None
    ) -> int:
        """计算阶段进度"""
        completed = len(completed_tasks)
        remaining = len(planned_tasks)
        total = completed + remaining
        return ProgressCalculator.calculate_progress(completed, total)


class ErrorHandler:
    """
    错误处理器
    
    统一管理错误处理逻辑。
    """
    
    @staticmethod
    def handle_tool_error(
        state: AgentState,
        tool_name: str,
        error: Exception,
        step_number: Optional[int] = None
    ) -> None:
        """
        处理工具执行错误
        
        Args:
            state: Agent状态
            tool_name: 工具名称
            error: 错误对象
            step_number: 步骤编号
        """
        error_msg = str(error)
        logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 执行错误: {error_msg}")
        state.add_error(f"工具执行错误 {tool_name}: {error_msg}")
        
        if step_number is not None:
            state.update_execution_step(
                step_number,
                result={"error": error_msg},
                status="failed",
                state_transitions=["failed", "error"]
            )
    
    @staticmethod
    def handle_tool_not_found(state: AgentState, tool_name: str) -> None:
        """处理工具未找到错误"""
        logger.warning(f"[{state.task_id}] ⚠️ 工具未注册: {tool_name}")
        state.add_error(f"工具未注册: {tool_name}")


class BasePlanningNode(ABC):
    """
    规划节点基类
    
    提供统一的规划逻辑框架，子类只需实现具体的规划策略。
    """
    
    def __init__(self, stage: NodeStage = NodeStage.INFO_COLLECTION):
        self.priority_manager = TaskPriorityManager()
        self.stage = stage
        self._init_llm()
        logger.info(f"📋 {self.__class__.__name__} 初始化完成 | 阶段: {stage.value}")
    
    def _init_llm(self) -> None:
        """初始化LLM（如果启用）"""
        self.llm = None
        self.use_llm = False
        
        if agent_config.ENABLE_LLM_PLANNING:
            self.llm = ChatOpenAI(
                model=agent_config.MODEL_ID,
                temperature=0,
                api_key=agent_config.OPENAI_API_KEY,
                base_url=agent_config.OPENAI_BASE_URL
            )
            self.use_llm = True
    
    async def __call__(self, state: AgentState) -> AgentState:
        """执行规划"""
        logger.info(
            f"[{state.task_id}] 📋 开始{self.stage.value}任务规划 | "
            f"目标: {state.target} | 当前上下文: {len(state.target_context)} 项"
        )
        
        state.update_stage_status(
            self.stage.value, 
            "running", 
            "planning", 
            10, 
            f"规划{self.stage.value}任务"
        )
        
        try:
            logger.debug(f"[{state.task_id}] 📝 开始调用 _plan_tasks 方法")
            tasks = await self._plan_tasks(state)
            logger.debug(f"[{state.task_id}] 📝 原始规划任务: {tasks}")
            
            tasks = self._filter_valid_tasks(tasks)
            logger.debug(f"[{state.task_id}] 📝 过滤后有效任务: {tasks}")
            
            state.planned_tasks = tasks
            state.current_task = tasks[0] if tasks else None
            
            logger.info(
                f"[{state.task_id}] ✅ 任务规划完成 | 任务数: {len(tasks)} | "
                f"任务列表: {tasks}"
            )
            state.update_stage_status(
                self.stage.value,
                "running",
                "executing",
                30,
                f"规划了 {len(tasks)} 个任务"
            )
            
            state.add_execution_step(
                f"{self.stage.value}_planning",
                {"tasks": tasks},
                "success",
                step_type="planning"
            )
            
        except Exception as e:
            logger.error(
                f"[{state.task_id}] ❌ 任务规划失败 | 错误类型: {type(e).__name__} | "
                f"错误信息: {str(e)}",
                exc_info=True
            )
            state.add_error(f"任务规划失败: {str(e)}")
            
            fallback_tasks = self._get_fallback_tasks()
            state.planned_tasks = fallback_tasks
            state.current_task = fallback_tasks[0] if fallback_tasks else None
            
            logger.warning(
                f"[{state.task_id}] ⚠️ 使用备用任务列表 | 任务数: {len(fallback_tasks)} | "
                f"任务列表: {fallback_tasks}"
            )
            
            state.update_stage_status(
                self.stage.value,
                "failed",
                "error",
                0,
                f"规划失败，使用默认任务"
            )
        
        return state
    
    @abstractmethod
    async def _plan_tasks(self, state: AgentState) -> List[str]:
        """
        规划任务列表（子类实现）
        
        Args:
            state: Agent状态
            
        Returns:
            List[str]: 任务列表
        """
        pass
    
    @abstractmethod
    def _get_fallback_tasks(self) -> List[str]:
        """获取备用任务列表（子类实现）"""
        pass
    
    @abstractmethod
    def _get_valid_tools(self) -> List[str]:
        """获取有效工具列表（子类实现）"""
        pass
    
    def _filter_valid_tasks(self, tasks: List[str]) -> List[str]:
        """过滤出有效的任务"""
        valid_tools = set(self._get_valid_tools())
        return [t for t in tasks if t in valid_tools]


class BaseToolExecutionNode(ABC):
    """
    工具执行节点基类
    
    提供统一的工具执行逻辑框架，包括错误处理、进度更新等。
    """
    
    def __init__(
        self,
        stage: NodeStage = NodeStage.INFO_COLLECTION,
        max_concurrent: int = None
    ):
        self.stage = stage
        self.semaphore = asyncio.Semaphore(
            max_concurrent or agent_config.MAX_CONCURRENT_TOOLS
        )
        logger.info(
            f"🔧 {self.__class__.__name__} 初始化完成 | "
            f"阶段: {stage.value} | 最大并发: {max_concurrent or agent_config.MAX_CONCURRENT_TOOLS}"
        )
    
    async def __call__(self, state: AgentState) -> AgentState:
        """执行工具"""
        if not state.current_task:
            logger.info(
                f"[{state.task_id}] ⏹️ 没有待执行任务 | "
                f"已完成: {len(state.completed_tasks)} | 待执行: {len(state.planned_tasks)}"
            )
            return state
        
        task = state.current_task
        logger.info(
            f"[{state.task_id}] 🔧 开始执行工具 | 工具: {task} | "
            f"目标: {state.target} | 阶段: {self.stage.value}"
        )
        
        progress = ProgressCalculator.calculate_stage_progress(
            state.completed_tasks,
            state.planned_tasks,
            state.current_task
        )
        logger.debug(f"[{state.task_id}] 📊 当前进度: {progress}%")
        
        step_number = state.add_execution_step_start(
            task,
            step_type="tool_execution",
            input_params={
                "target": state.target,
                "tool_name": task,
                "stage": self.stage.value
            },
            processing_logic=f"执行{task}工具"
        )
        logger.debug(f"[{state.task_id}] 📝 创建执行步骤 | 步骤号: {step_number}")
        
        try:
            logger.debug(f"[{state.task_id}] 🔄 获取信号量锁，准备执行工具")
            async with self.semaphore:
                logger.debug(f"[{state.task_id}] 🔒 获取信号量锁成功，开始执行工具: {task}")
                result = await self._execute_tool(state, task)
                logger.debug(
                    f"[{state.task_id}] 📦 工具执行返回 | 工具: {task} | "
                    f"成功: {result.success if hasattr(result, 'success') else 'N/A'}"
                )
                
                if result.success:
                    await self._handle_success(state, task, result, step_number)
                else:
                    await self._handle_failure(state, task, result, step_number)
                    
        except ValueError as e:
            logger.warning(
                f"[{state.task_id}] ⚠️ 工具未注册 | 工具: {task} | 错误: {str(e)}"
            )
            ErrorHandler.handle_tool_not_found(state, task)
            self._mark_task_completed(state, task)
            
        except Exception as e:
            logger.error(
                f"[{state.task_id}] ❌ 工具执行异常 | 工具: {task} | "
                f"错误类型: {type(e).__name__} | 错误: {str(e)}",
                exc_info=True
            )
            ErrorHandler.handle_tool_error(state, task, e, step_number)
            self._mark_task_completed(state, task)
        
        return state
    
    @abstractmethod
    async def _execute_tool(self, state: AgentState, tool_name: str):
        """
        执行具体工具（子类实现）
        
        Args:
            state: Agent状态
            tool_name: 工具名称
            
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    async def _handle_success(self, state: AgentState, tool_name: str, result, step_number: int):
        """处理执行成功"""
        pass
    
    @abstractmethod
    async def _handle_failure(self, state: AgentState, tool_name: str, result, step_number: int):
        """处理执行失败"""
        pass
    
    def _mark_task_completed(self, state: AgentState, task: str) -> None:
        """标记任务完成"""
        if task in state.planned_tasks:
            state.planned_tasks.remove(task)
        state.completed_tasks.append(task)
        state.current_task = state.planned_tasks[0] if state.planned_tasks else None
    
    def _update_progress(self, state: AgentState, message: str = None) -> None:
        """更新进度"""
        progress = ProgressCalculator.calculate_stage_progress(
            state.completed_tasks,
            state.planned_tasks
        )
        msg = message or f"执行任务中"
        state.update_stage_status(
            self.stage.value,
            "running",
            "executing",
            progress,
            msg
        )


class BaseResultVerificationNode(ABC):
    """
    结果验证节点基类
    
    提供统一的结果验证逻辑框架。
    """
    
    def __init__(self, stage: NodeStage = NodeStage.INFO_COLLECTION):
        self.stage = stage
        logger.info(f"🔍 {self.__class__.__name__} 初始化完成 | 阶段: {stage.value}")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """验证结果"""
        logger.info(
            f"[{state.task_id}] 🔍 开始验证{self.stage.value}结果 | "
            f"已完成任务: {len(state.completed_tasks)} | 待执行任务: {len(state.planned_tasks)}"
        )
        
        await self._verify_results(state)
        
        if not state.planned_tasks:
            logger.info(
                f"[{state.task_id}] ✅ 所有{self.stage.value}任务已完成 | "
                f"总计完成: {len(state.completed_tasks)} 个任务"
            )
            state.update_stage_status(
                self.stage.value,
                "completed",
                "完成",
                100,
                f"完成 {len(state.completed_tasks)} 个任务"
            )
        else:
            state.current_task = state.planned_tasks[0]
            logger.info(
                f"[{state.task_id}] 📋 待执行任务 | 数量: {len(state.planned_tasks)} | "
                f"下一个任务: {state.current_task}"
            )
        
        return state
    
    @abstractmethod
    async def _verify_results(self, state: AgentState) -> None:
        """验证结果（子类实现）"""
        pass


# ============================================================================
# 任务规划节点
# ============================================================================

class TaskPlanningNode(BasePlanningNode):
    """
    任务规划节点
    
    根据用户需求和目标特征，生成扫描任务计划。
    支持规则化规划和LLM增强规划两种模式。
    """
    
    def __init__(self):
        super().__init__(stage=NodeStage.INFO_COLLECTION)
        if self.use_llm:
            logger.info("🤖 启用LLM增强任务规划")
        else:
            logger.info("📋 使用规则化任务规划")
    
    async def _plan_tasks(self, state: AgentState) -> List[str]:
        """规划任务"""
        if self.use_llm:
            return await self._llm_planning(state)
        return await self._rule_based_planning(state)
    
    def _get_fallback_tasks(self) -> List[str]:
        return agent_config.DEFAULT_SCAN_TASKS.copy()
    
    def _get_valid_tools(self) -> List[str]:
        return [t["name"] for t in registry.list_tools()]
    
    async def _rule_based_planning(self, state: AgentState) -> List[str]:
        """规则化任务规划"""
        tasks = agent_config.DEFAULT_SCAN_TASKS.copy()
        
        if state.target_context:
            self._add_poc_tasks_by_context(state, tasks)
        
        return tasks
    
    def _add_poc_tasks_by_context(self, state: AgentState, tasks: List[str]) -> None:
        """根据上下文添加POC任务"""
        cms = state.target_context.get("cms", "").lower()
        open_ports = state.target_context.get("open_ports", [])
        
        cms_poc_map = {
            "weblogic": POCAdapter.get_poc_by_cms("weblogic"),
            "struts2": POCAdapter.get_poc_by_cms("struts2"),
            "tomcat": POCAdapter.get_poc_by_cms("tomcat")
        }
        
        if cms in cms_poc_map:
            tasks.extend(cms_poc_map[cms])
        
        for port in open_ports:
            port_pocs = POCAdapter.get_poc_by_port(port)
            for poc in port_pocs:
                if poc not in tasks:
                    tasks.append(poc)
    
    async def _llm_planning(self, state: AgentState) -> List[str]:
        """LLM增强任务规划"""
        available_tools = registry.list_tools()
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}" 
            for t in available_tools
        ])
        
        context_info = ""
        if state.target_context:
            context_info = f"\n目标上下文: {json.dumps(state.target_context, ensure_ascii=False)}"
        
        system_prompt = self._build_llm_prompt()
        user_prompt = f"目标: {state.target}{context_info}"
        
        try:
            logger.info(f"[{state.task_id}] 📝 LLM规划输入 - 目标: {state.target}")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt)
            ])
            
            chain = prompt | self.llm | JsonOutputParser(pydantic_object=PlanningResponse)
            result = await chain.ainvoke({"tools": tools_desc, "target": state.target})
            
            logger.info(f"[{state.task_id}] 📝 LLM规划结果: {result}")
            
            tasks = self._extract_tasks_from_result(result)
            
            if tasks:
                if isinstance(result, dict) and 'reasoning' in result:
                    logger.info(f"[{state.task_id}] 📝 规划理由: {result['reasoning']}")
                return tasks
            
            raise ValueError("无法从LLM结果中提取有效任务列表")
                
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ LLM规划失败: {str(e)}，切换到规则化规划")
            return await self._rule_based_planning(state)
    
    def _build_llm_prompt(self) -> str:
        """构建LLM规划提示词"""
        return """你是Web安全扫描专家，负责为目标规划最优扫描任务序列。

## 可用工具
{tools}

## 重要规则 - 必须遵守

### 1. 必须使用所有可用工具
- 你**必须**在计划中包含所有可用的工具，不能遗漏任何工具
- 每个工具都有其独特的安全检测价值，必须全部执行
- 如果某个工具不适用，也应在计划中列出，执行时会自动跳过

### 2. 执行顺序原则

**第一阶段：基础信息收集（必须全部执行）**
- baseinfo: 获取基础HTTP信息（必须）
- portscan: 端口扫描（必须）
- cms_identify: CMS识别（必须）
- waf_detect: WAF检测（必须）
- cdn_detect: CDN检测（必须）
- iplocating: IP地址定位（必须）

**第二阶段：深度信息收集（必须全部执行）**
- subdomain_scan: 子域名枚举（必须）
- webside_scan: 站点信息收集（必须）
- webweight_scan: 网站权重查询（必须）
- infoleak_scan: 信息泄露检测（必须）
- dirscan: 目录扫描（必须）
- crawler: Web爬虫（必须）

**第三阶段：漏洞扫描（必须全部执行）**
- sqli_scan: SQL注入扫描（必须）
- xss_scan: XSS漏洞扫描（必须）
- csrf_scan: CSRF漏洞扫描（必须）
- vuln_infoleak_scan: 敏感信息泄露扫描（必须）
- fileupload_scan: 文件上传漏洞扫描（必须）
- cmdi_scan: 命令注入扫描（必须）
- weakpass_scan: 弱口令扫描（必须）
- lfi_scan: 文件包含漏洞扫描（必须）
- ssrf_scan: SSRF漏洞扫描（必须）

**第四阶段：POC验证（根据端口和CMS选择）**
- 根据开放端口选择对应POC
- 根据识别的CMS选择对应POC

### 3. 输出格式
返回JSON格式:
{{
  "plan": ["task1", "task2", ...],
  "reasoning": "规划理由说明"
}}

### 4. 示例输出
{{
  "plan": ["baseinfo", "portscan", "cms_identify", "waf_detect", "cdn_detect", "iplocating", "subdomain_scan", "webside_scan", "webweight_scan", "infoleak_scan", "dirscan", "crawler", "sqli_scan", "xss_scan", "csrf_scan", "vuln_infoleak_scan", "fileupload_scan", "cmdi_scan", "weakpass_scan", "lfi_scan", "ssrf_scan"],
  "reasoning": "执行完整的安全扫描流程，包含所有信息收集和漏洞检测工具"
}}

## 注意事项
- 计划必须包含所有可用工具
- 按照阶段顺序排列任务
- 不要遗漏任何安全检测工具
- 完整性比效率更重要"""
    
    def _extract_tasks_from_result(self, result: Any) -> List[str]:
        """从LLM结果中提取任务列表"""
        if result is None:
            return []
        
        if isinstance(result, PlanningResponse):
            return result.plan if isinstance(result.plan, list) else []
        
        if isinstance(result, dict):
            if 'plan' in result and isinstance(result['plan'], list):
                return result['plan']
            if all(isinstance(v, str) for v in result.values()):
                return list(result.values())
            return []
        
        if isinstance(result, list):
            return result if all(isinstance(item, str) for item in result) else []
        
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                return self._extract_tasks_from_result(parsed)
            except json.JSONDecodeError:
                return []
        
        logger.warning(f"无法识别的LLM结果类型: {type(result)}")
        return []


# ============================================================================
# 工具执行节点
# ============================================================================

class ToolExecutionNode(BaseToolExecutionNode):
    """
    工具执行节点
    
    执行当前规划的任务，调用相应的工具并更新状态。
    """
    
    def __init__(self):
        super().__init__(stage=NodeStage.INFO_COLLECTION)
    
    async def _execute_tool(self, state: AgentState, tool_name: str):
        """执行工具"""
        return await registry.call_tool(tool_name, state.target)
    
    async def _handle_success(self, state: AgentState, tool_name: str, result, step_number: int):
        """处理执行成功"""
        state.tool_results[tool_name] = result
        
        TargetContextUpdater.update_context(state, tool_name, result.get("data", {}))
        
        if tool_name.startswith("poc_"):
            self._process_poc_result(state, tool_name, result)
        
        self._mark_task_completed(state, tool_name)
        
        logger.info(f"[{state.task_id}] ✅ 工具 {tool_name} 执行完成")
        
        state.update_execution_step(
            step_number,
            result=result,
            status="success",
            output_data={
                "tool_status": result.get("status"),
                "has_data": "data" in result
            },
            state_transitions=["completed", "next_task"]
        )
        
        self._update_progress(state, f"完成 {tool_name}")
    
    async def _handle_failure(self, state: AgentState, tool_name: str, result, step_number: int):
        """处理执行失败"""
        error_msg = result.get("error", "未知错误")
        logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 执行失败: {error_msg}")
        state.add_error(f"工具执行失败 {tool_name}: {error_msg}")
        
        state.update_execution_step(
            step_number,
            result=result,
            status="failed",
            output_data={"error": error_msg},
            state_transitions=["failed"]
        )
        
        self._handle_retry(state, tool_name, step_number, error_msg)
    
    def _handle_retry(self, state: AgentState, tool_name: str, step_number: int, error_msg: str):
        """处理重试逻辑"""
        state.increment_retry()
        
        if state.retry_count < agent_config.MAX_RETRIES:
            logger.warning(f"[{state.task_id}] 🔄 工具 {tool_name} 重试 {state.retry_count}/{agent_config.MAX_RETRIES}")
        else:
            logger.error(f"[{state.task_id}] ❌ 工具 {tool_name} 达到最大重试次数")
            self._mark_task_completed(state, tool_name)
            state.reset_retry()
            
            state.update_execution_step(
                step_number,
                status="failed",
                state_transitions=["failed", "max_retries_reached"]
            )
    
    def _process_poc_result(self, state: AgentState, tool_name: str, result: Dict[str, Any]):
        """处理POC执行结果"""
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
        """获取POC的严重度"""
        poc_lower = poc_name.lower()
        severity_map = {
            "cve_2020_2551": "critical",
            "cve_2023_21839": "critical",
            "cve_2022_22965": "critical"
        }
        
        for key, severity in severity_map.items():
            if key in poc_lower:
                return severity
        
        return "high" if "cve" in poc_lower else "medium"


# ============================================================================
# 结果验证节点
# ============================================================================

class ResultVerificationNode(BaseResultVerificationNode):
    """
    结果验证节点
    
    验证扫描结果，根据上下文补充任务，决定是否继续执行。
    """
    
    def __init__(self):
        super().__init__(stage=NodeStage.INFO_COLLECTION)
    
    async def _verify_results(self, state: AgentState) -> None:
        """验证结果并补充任务"""
        self._supplement_poc_tasks(state)
        
        state.add_execution_step(
            "result_verification",
            {"planned_tasks": state.planned_tasks},
            "success",
            step_type="result_verification"
        )
    
    def _supplement_poc_tasks(self, state: AgentState) -> None:
        """基于上下文补充POC任务"""
        cms = state.target_context.get("cms", "").lower()
        open_ports = state.target_context.get("open_ports", [])
        
        supplement_tasks = set()
        
        if cms:
            cms_pocs = POCAdapter.get_poc_by_cms(cms)
            for poc in cms_pocs:
                if poc not in state.completed_tasks and poc not in state.planned_tasks:
                    supplement_tasks.add(poc)
        
        for port in open_ports:
            port_pocs = POCAdapter.get_poc_by_port(port)
            for poc in port_pocs:
                if poc not in state.completed_tasks and poc not in state.planned_tasks:
                    supplement_tasks.add(poc)
        
        for task in supplement_tasks:
            state.planned_tasks.append(task)
            logger.info(f"[{state.task_id}] ➕ 补充POC任务: {task}")


# ============================================================================
# 漏洞分析节点
# ============================================================================

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
        """分析漏洞"""
        logger.info(
            f"[{state.task_id}] 🔍 开始漏洞分析 | "
            f"发现漏洞数: {len(state.vulnerabilities)} | 目标: {state.target}"
        )
        
        if not state.vulnerabilities:
            self._log_no_vulnerabilities(state)
            return state
        
        try:
            logger.debug(f"[{state.task_id}] 📊 开始漏洞去重处理")
            unique_vulns = self.analyzer.deduplicate(state.vulnerabilities)
            logger.debug(
                f"[{state.task_id}] 📊 去重完成 | 原始: {len(state.vulnerabilities)} | "
                f"去重后: {len(unique_vulns)}"
            )
            
            logger.debug(f"[{state.task_id}] 📊 开始按严重度排序")
            sorted_vulns = self.analyzer.sort_by_severity(unique_vulns)
            state.vulnerabilities = sorted_vulns
            
            severity_counts = {}
            for vuln in sorted_vulns:
                sev = vuln.get('severity', 'unknown')
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            logger.info(
                f"[{state.task_id}] ✅ 漏洞分析完成 | 总数: {len(sorted_vulns)} | "
                f"严重度分布: {severity_counts}"
            )
            state.add_execution_step(
                "vulnerability_analysis",
                {"total": len(sorted_vulns), "vulnerabilities": sorted_vulns},
                "success",
                step_type="analysis"
            )
        except Exception as e:
            self._handle_analysis_error(state, e)
        
        return state
    
    def _log_no_vulnerabilities(self, state: AgentState) -> None:
        """记录无漏洞情况"""
        logger.info(f"[{state.task_id}] ✅ 未发现漏洞")
        state.add_execution_step(
            "vulnerability_analysis",
            {"total": 0, "vulnerabilities": []},
            "success",
            step_type="analysis"
        )
    
    def _handle_analysis_error(self, state: AgentState, error: Exception) -> None:
        """处理分析错误"""
        logger.error(
            f"[{state.task_id}] ❌ 漏洞分析失败 | "
            f"错误类型: {type(error).__name__} | 错误: {str(error)}",
            exc_info=True
        )
        state.add_error(f"漏洞分析失败: {str(error)}")
        state.add_execution_step(
            "vulnerability_analysis",
            {"total": len(state.vulnerabilities), "vulnerabilities": state.vulnerabilities, "error": str(error)},
            "failed",
            step_type="analysis"
        )


# ============================================================================
# 报告生成节点
# ============================================================================

class ReportGenerationNode:
    """
    报告生成节点
    
    生成最终的扫描报告，包含所有结果和漏洞信息。
    """
    
    def __init__(self):
        from ..analyzers.enhanced_report_gen import ReportGenerator
        self.report_gen = ReportGenerator()
        logger.info("📄 报告生成节点初始化（使用增强版报告生成器）")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """生成报告"""
        logger.info(
            f"[{state.task_id}] 📄 开始生成扫描报告 | "
            f"目标: {state.target} | 漏洞数: {len(state.vulnerabilities)} | "
            f"已完成任务: {len(state.completed_tasks)}"
        )
        
        try:
            logger.debug(f"[{state.task_id}] 📝 调用报告生成器生成所有报告")
            reports = await self._generate_all_reports_async(state)
            logger.debug(
                f"[{state.task_id}] 📝 报告生成完成 | 报告类型: {list(reports.keys())}"
            )
            
            state.tool_results.update(reports)
            
            state.scan_summary = {
                "target": state.target,
                "vulnerabilities_count": len(state.vulnerabilities),
                "completed_tasks": len(state.completed_tasks),
                "errors_count": len(state.errors)
            }
            
            if "final_report" in reports:
                state.report = reports["final_report"].get("summary", "")
            
            state.mark_complete()
            
            logger.info(
                f"[{state.task_id}] ✅ 报告生成完成 | "
                f"漏洞数: {len(state.vulnerabilities)} | 任务数: {len(state.completed_tasks)} | "
                f"错误数: {len(state.errors)}"
            )
            state.add_execution_step(
                "report_generation",
                reports,
                "success",
                step_type="report_generation",
                processing_logic="生成标准扫描报告和详细执行轨迹报告"
            )
        except Exception as e:
            logger.error(
                f"[{state.task_id}] ❌ 报告生成失败 | "
                f"错误类型: {type(e).__name__} | 错误: {str(e)}",
                exc_info=True
            )
            state.add_error(f"报告生成失败: {str(e)}")
            state.mark_complete()
        
        return state
    
    async def _generate_all_reports_async(self, state: AgentState) -> Dict[str, Any]:
        """异步生成所有报告 - 使用同步版本避免事件循环问题"""
        try:
            return self._generate_all_reports(state)
        except Exception as e:
            logger.warning(f"报告生成失败: {e}，使用简化报告")
            return {
                "final_report": {},
                "execution_trace_report": {},
                "html_execution_trace": "",
                "enhanced_report": {
                    "task_id": state.task_id,
                    "target": state.target,
                    "vulnerabilities_count": len(state.vulnerabilities),
                    "timing": {}
                }
            }
    
    def _generate_all_reports(self, state: AgentState) -> Dict[str, Any]:
        """生成所有报告（同步版本，保留向后兼容）"""
        return {
            "final_report": self.report_gen.generate_report(state),
            "execution_trace_report": self.report_gen.generate_execution_trace_report(state),
            "html_execution_trace": self.report_gen.generate_html_execution_trace(state)
        }
    
    def _handle_report_error(self, state: AgentState, error: Exception) -> None:
        """处理报告生成错误"""
        logger.error(f"[{state.task_id}] ❌ 报告生成失败: {str(error)}")
        state.add_error(f"报告生成失败: {str(error)}")
        state.mark_complete()


# ============================================================================
# 环境感知节点
# ============================================================================

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
        """执行环境感知"""
        logger.info(
            f"[{state.task_id}] 🔍 开始环境感知 | 目标: {state.target}"
        )
        
        try:
            logger.debug(f"[{state.task_id}] 🌐 获取环境报告")
            env_report = self.env_awareness.get_environment_report()
            logger.debug(
                f"[{state.task_id}] 🌐 环境报告获取成功 | "
                f"操作系统: {env_report['os_info']['system']} | "
                f"Python版本: {env_report['python_info']['version']}"
            )
            
            state.update_context("environment_info", env_report)
            state.update_context("os_system", env_report["os_info"]["system"])
            state.update_context("python_version", env_report["python_info"]["version"])
            state.update_context("available_tools", env_report["available_tools"])
            
            logger.info(
                f"[{state.task_id}] ✅ 环境感知完成 | "
                f"操作系统: {env_report['os_info']['system']} | "
                f"可用工具数: {len(env_report['available_tools'])}"
            )
            state.add_execution_step("environment_awareness", env_report, "success")
            
        except Exception as e:
            logger.error(
                f"[{state.task_id}] ❌ 环境感知失败 | "
                f"错误类型: {type(e).__name__} | 错误: {str(e)}",
                exc_info=True
            )
            state.add_error(f"环境感知失败: {str(e)}")
        
        return state


# ============================================================================
# 代码生成节点
# ============================================================================

class CodeGenerationNode:
    """
    代码生成节点
    
    根据扫描需求自动生成扫描脚本。
    """
    
    def __init__(self):
        from ..code_execution.code_generator import CodeGenerator
        self.code_generator = CodeGenerator()
        
        self.code_dir = Path(__file__).parent.parent / "code_execution" / "workspace" / "generated_code"
        self.code_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🔧 代码生成节点初始化完成")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """执行代码生成"""
        logger.info(
            f"[{state.task_id}] 🔧 开始代码生成 | 目标: {state.target}"
        )
        
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
        logger.debug(f"[{state.task_id}] 📝 创建代码生成步骤 | 步骤号: {step_number}")
        
        try:
            if not state.target_context.get("need_custom_scan"):
                return self._skip_code_generation(state, step_number)
            
            logger.debug(
                f"[{state.task_id}] 📝 开始生成代码 | "
                f"扫描类型: {state.target_context.get('custom_scan_type', 'vuln_scan')} | "
                f"语言: {state.target_context.get('custom_scan_language', 'python')}"
            )
            code_response = await self._generate_code(state)
            self._save_and_update_state(state, code_response, step_number)
            
        except Exception as e:
            self._handle_generation_error(state, e, step_number)
        
        return state
    
    async def _generate_code(self, state: AgentState):
        """生成代码"""
        return await self.code_generator.generate_code(
            scan_type=state.target_context.get("custom_scan_type", "vuln_scan"),
            target=state.target,
            requirements=state.target_context.get("custom_scan_requirements", ""),
            language=state.target_context.get("custom_scan_language", "python")
        )
    
    def _skip_code_generation(self, state: AgentState, step_number: int) -> AgentState:
        """跳过代码生成"""
        logger.info(f"[{state.task_id}] ⏭️ 无需自定义扫描,跳过代码生成")
        state.update_execution_step(
            step_number,
            status="skipped",
            output_data={"message": "无需自定义扫描"},
            state_transitions=["skipped"]
        )
        return state
    
    def _save_and_update_state(self, state: AgentState, code_response, step_number: int) -> None:
        """保存代码并更新状态"""
        code_dict = code_response.to_dict()
        state.tool_results["generated_code"] = code_dict
        state.update_context("generated_code", code_dict)
        
        code_file_path = self._save_generated_code(
            code=code_response.code,
            language=code_response.language,
            scan_type=state.target_context.get("custom_scan_type", "vuln_scan"),
            target=state.target,
            task_id=state.task_id
        )
        
        if code_file_path:
            code_dict["file_path"] = code_file_path
        
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
            state_transitions=["completed", "ready_for_execution"]
        )
    
    def _save_generated_code(
        self,
        code: str,
        language: str,
        scan_type: str,
        target: str,
        task_id: str
    ) -> str:
        """保存生成的代码到文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_id = f"{task_id}_{scan_type}_{timestamp}"
            
            extensions = {
                "python": "py",
                "bash": "sh",
                "powershell": "ps1",
                "shell": "sh"
            }
            extension = extensions.get(language, "txt")
            
            code_file = self.code_dir / f"{file_id}.{extension}"
            
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            logger.info(f"代码文件已保存: {code_file}")
            return str(code_file)
            
        except Exception as e:
            logger.error(f"保存代码文件失败: {str(e)}")
            return ""
    
    def _handle_generation_error(self, state: AgentState, error: Exception, step_number: int) -> None:
        """处理代码生成错误"""
        logger.error(
            f"[{state.task_id}] ❌ 代码生成失败 | "
            f"错误类型: {type(error).__name__} | 错误: {str(error)}",
            exc_info=True
        )
        state.add_error(f"代码生成失败: {str(error)}")
        
        state.update_execution_step(
            step_number,
            result={"error": str(error)},
            status="failed",
            state_transitions=["failed"]
        )


# ============================================================================
# 功能增强节点
# ============================================================================

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
        """执行功能补充"""
        logger.info(
            f"[{state.task_id}] 🚀 开始功能补充 | 目标: {state.target}"
        )
        
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
        logger.debug(f"[{state.task_id}] 📝 创建功能补充步骤 | 步骤号: {step_number}")
        
        try:
            if not state.target_context.get("need_capability_enhancement"):
                return self._skip_enhancement(state, step_number)
            
            requirement = state.target_context.get("capability_requirement", "")
            if not requirement:
                return self._skip_enhancement(state, step_number, "未指定功能需求")
            
            logger.debug(
                f"[{state.task_id}] 📝 开始功能增强 | 需求: {requirement} | "
                f"功能名称: {state.target_context.get('capability_name')}"
            )
            await self._enhance_capability(state, requirement, step_number)
            
        except Exception as e:
            self._handle_enhancement_error(state, e, step_number)
        
        return state
    
    async def _enhance_capability(self, state: AgentState, requirement: str, step_number: int) -> None:
        """执行功能增强"""
        enhance_result = await self.capability_enhancer.enhance_capability(
            requirement=requirement,
            target=state.target,
            capability_name=state.target_context.get("capability_name")
        )
        
        state.tool_results["capability_enhancement"] = enhance_result
        state.update_context("enhanced_capability", enhance_result)
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
            state_transitions=["completed", "capability_available"]
        )
    
    def _skip_enhancement(self, state: AgentState, step_number: int, reason: str = "无需功能补充") -> AgentState:
        """跳过功能增强"""
        logger.info(f"[{state.task_id}] ⏭️ {reason},跳过")
        state.update_execution_step(
            step_number,
            status="skipped",
            output_data={"message": reason},
            state_transitions=["skipped"]
        )
        return state
    
    def _handle_enhancement_error(self, state: AgentState, error: Exception, step_number: int) -> None:
        """处理功能增强错误"""
        logger.error(
            f"[{state.task_id}] ❌ 功能补充失败 | "
            f"错误类型: {type(error).__name__} | 错误: {str(error)}",
            exc_info=True
        )
        state.add_error(f"功能补充失败: {str(error)}")
        
        state.update_execution_step(
            step_number,
            result={"error": str(error)},
            status="failed",
            state_transitions=["failed"]
        )


# ============================================================================
# 代码执行节点
# ============================================================================

class CodeExecutionNode:
    """
    代码执行节点
    
    执行生成的代码或自定义脚本。
    """
    
    def __init__(self):
        from ..code_execution.executor import UnifiedExecutor
        self.executor = UnifiedExecutor(
            timeout=agent_config.TOOL_TIMEOUT,
            enable_sandbox=True
        )
        logger.info("⚡ 代码执行节点初始化完成")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """执行代码"""
        logger.info(
            f"[{state.task_id}] ⚡ 开始执行代码 | 目标: {state.target}"
        )
        
        try:
            if not state.target_context.get("generated_code"):
                logger.info(
                    f"[{state.task_id}] ⏭️ 无代码可执行,跳过 | "
                    f"目标: {state.target}"
                )
                return state
            
            generated_code = state.target_context["generated_code"]
            logger.debug(
                f"[{state.task_id}] 📝 准备执行代码 | "
                f"语言: {generated_code.get('language', 'unknown')} | "
                f"代码长度: {len(generated_code.get('code', ''))} 字符"
            )
            
            execution_result = await self.executor.execute_code(
                code=generated_code["code"],
                language=generated_code["language"],
                target=state.target
            )
            
            state.tool_results["code_execution"] = execution_result.to_dict()
            state.update_context("code_execution_result", execution_result.to_dict())
            
            if execution_result.status == "success":
                logger.info(
                    f"[{state.task_id}] ✅ 代码执行成功 | "
                    f"输出长度: {len(execution_result.output) if execution_result.output else 0}"
                )
            else:
                logger.warning(
                    f"[{state.task_id}] ⚠️ 代码执行失败 | "
                    f"错误: {execution_result.error}"
                )
                state.target_context["need_capability_enhancement"] = True
                state.target_context["capability_requirement"] = "自动安装代码执行所需依赖"
            
            state.add_execution_step(
                "code_execution",
                execution_result.to_dict(),
                execution_result.status,
                step_type="code_execution"
            )
            
        except Exception as e:
            logger.error(
                f"[{state.task_id}] ❌ 代码执行失败 | "
                f"错误类型: {type(e).__name__} | 错误: {str(e)}",
                exc_info=True
            )
            state.add_error(f"代码执行失败: {str(e)}")
        
        return state


# ============================================================================
# 智能决策节点
# ============================================================================

class IntelligentDecisionNode:
    """
    智能决策节点
    
    基于环境信息和扫描结果，智能决定下一步操作。
    """
    
    def __init__(self):
        from ..code_execution.environment import EnvironmentAwareness
        self.env_awareness = EnvironmentAwareness()
        logger.info("🧠 智能决策节点初始化完成")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """执行智能决策"""
        logger.info(
            f"[{state.task_id}] 🧠 开始智能决策 | 目标: {state.target}"
        )
        
        try:
            logger.debug(f"[{state.task_id}] 🌐 获取环境信息")
            env_info = self.env_awareness.get_environment_report()
            logger.debug(
                f"[{state.task_id}] 🌐 环境信息获取成功 | "
                f"操作系统: {env_info['os_info']['system']}"
            )
            
            logger.debug(f"[{state.task_id}] 🧠 开始制定决策")
            decisions = self._make_decisions(state, env_info)
            
            state.update_context("intelligent_decisions", decisions)
            
            logger.info(
                f"[{state.task_id}] ✅ 智能决策完成 | 决策数: {len(decisions)} | "
                f"决策列表: {decisions}"
            )
            state.add_execution_step("intelligent_decision", {"decisions": decisions}, "success")
            
        except Exception as e:
            logger.error(
                f"[{state.task_id}] ❌ 智能决策失败 | "
                f"错误类型: {type(e).__name__} | 错误: {str(e)}",
                exc_info=True
            )
            state.add_error(f"智能决策失败: {str(e)}")
        
        return state
    
    def _make_decisions(self, state: AgentState, env_info: Dict) -> List[str]:
        """制定决策"""
        decisions = []
        
        os_system = env_info["os_info"]["system"]
        decisions.append("使用PowerShell执行脚本" if os_system == "Windows" else "使用Bash执行脚本")
        
        available_tools = [
            name for name, info in env_info["available_tools"].items()
            if info.get("available", False)
        ]
        
        if "nmap" in available_tools:
            decisions.append("使用nmap进行端口扫描")
        else:
            decisions.append("使用Python进行端口扫描")
        
        cms = state.target_context.get("cms", "").lower()
        cms_poc_map = {
            "weblogic": "执行WebLogic相关POC",
            "tomcat": "执行Tomcat相关POC",
            "struts2": "执行Struts2相关POC"
        }
        if cms in cms_poc_map:
            decisions.append(cms_poc_map[cms])
        
        network_info = env_info["network_info"]
        if network_info.get("proxy_detected"):
            decisions.append("检测到代理,调整扫描策略")
        if network_info.get("firewall_detected"):
            decisions.append("检测到防火墙,降低扫描速度")
        
        return decisions


# ============================================================================
# 漏洞扫描节点
# ============================================================================

class VulnerabilityScanNode:
    """
    漏洞扫描节点
    
    执行漏洞扫描插件，检测SQL注入、XSS、CSRF等漏洞。
    """
    
    def __init__(self):
        from backend.vulnerability_scan_plugins.manager import plugin_manager
        self.plugin_manager = plugin_manager
        logger.info("🔍 漏洞扫描节点初始化完成")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """执行漏洞扫描"""
        logger.info(
            f"[{state.task_id}] 🔍 开始漏洞扫描 | 目标: {state.target}"
        )
        state.update_stage_status("tool_execution", "running", "初始化", 10, "加载漏洞扫描插件")
        
        try:
            logger.debug(f"[{state.task_id}] 📦 加载漏洞扫描插件")
            self.plugin_manager.load_plugins_from_directory()
            
            loaded_plugins = self.plugin_manager.list_plugins(enabled_only=True)
            state.vuln_scan_plugins_loaded = [p.name for p in loaded_plugins]
            
            logger.info(
                f"[{state.task_id}] 📦 已加载 {len(loaded_plugins)} 个漏洞扫描插件 | "
                f"插件列表: {state.vuln_scan_plugins_loaded}"
            )
            state.update_stage_status("tool_execution", "running", "扫描中", 30, f"使用 {len(loaded_plugins)} 个插件扫描")
            
            logger.debug(f"[{state.task_id}] 🔬 开始执行所有插件扫描")
            results = await self.plugin_manager.scan_all_async(
                target=state.target,
                plugin_names=state.vuln_scan_plugins_loaded,
                max_concurrent=2
            )
            logger.debug(f"[{state.task_id}] 🔬 扫描完成，开始聚合结果")
            
            aggregated = self.plugin_manager.aggregate_results(results)
            
            self._update_scan_results(state, aggregated)
            
            logger.info(
                f"[{state.task_id}] ✅ 漏洞扫描完成 | "
                f"发现漏洞: {aggregated['total_vulnerabilities']} 个 | "
                f"扫描耗时: {aggregated['scan_summary']['total_duration']:.2f}s"
            )
            
        except Exception as e:
            self._handle_scan_error(state, e)
        
        return state
    
    def _update_scan_results(self, state: AgentState, aggregated: Dict) -> None:
        """更新扫描结果"""
        state.vuln_scan_results = aggregated
        state.vuln_scan_progress = 100
        state.vuln_scan_metadata = {
            "plugins_used": len(state.vuln_scan_plugins_loaded),
            "total_vulnerabilities": aggregated["total_vulnerabilities"],
            "scan_duration": aggregated["scan_summary"]["total_duration"]
        }
        
        for vuln in aggregated["vulnerabilities"]:
            state.add_vulnerability(vuln)
        
        state.update_stage_status(
            "tool_execution", 
            "completed", 
            "完成", 
            100, 
            f"发现 {aggregated['total_vulnerabilities']} 个漏洞"
        )
        
        state.add_execution_step(
            "vulnerability_scan",
            {
                "plugins_used": state.vuln_scan_plugins_loaded,
                "vulnerabilities_found": aggregated["total_vulnerabilities"],
                "scan_duration": aggregated["scan_summary"]["total_duration"]
            },
            "success"
        )
    
    def _handle_scan_error(self, state: AgentState, error: Exception) -> None:
        """处理扫描错误"""
        logger.error(
            f"[{state.task_id}] ❌ 漏洞扫描失败 | "
            f"错误类型: {type(error).__name__} | 错误: {str(error)}",
            exc_info=True
        )
        state.add_error(f"漏洞扫描失败: {str(error)}")
        state.update_stage_status("tool_execution", "failed", "失败", 0, str(error))


# ============================================================================
# 信息收集子图节点
# ============================================================================

INFO_COLLECTION_TOOLS = [
    "baseinfo", "portscan", "waf_detect", "cdn_detect", "cms_identify",
    "subdomain_scan", "webside_scan", "webweight_scan", "iplocating",
    "infoleak_scan", "dirscan", "loginfo", "randheader",
    "crawler"
]


class InfoTaskPlanningNode(BasePlanningNode):
    """信息收集任务规划节点"""
    
    def __init__(self):
        super().__init__(stage=NodeStage.INFO_COLLECTION)
    
    async def _plan_tasks(self, state: AgentState) -> List[str]:
        """规划信息收集任务"""
        tasks = ["baseinfo", "portscan", "cms_identify", "waf_detect", "cdn_detect"]
        
        if state.target_context:
            cms = state.target_context.get("cms", "").lower()
            if cms:
                tasks.append("subdomain_scan")
        
        return tasks
    
    def _get_fallback_tasks(self) -> List[str]:
        return ["baseinfo", "portscan", "cms_identify"]
    
    def _get_valid_tools(self) -> List[str]:
        return INFO_COLLECTION_TOOLS


class InfoToolExecutionNode(BaseToolExecutionNode):
    """信息收集工具执行节点"""
    
    def __init__(self):
        super().__init__(stage=NodeStage.INFO_COLLECTION)
    
    async def _execute_tool(self, state: AgentState, tool_name: str):
        """执行信息收集工具"""
        tool_wrapper = registry.get_tool(tool_name)
        if tool_wrapper is None:
            raise ValueError(f"工具未注册: {tool_name}")
        
        return await tool_wrapper.execute(state.target)
    
    async def _handle_success(self, state: AgentState, tool_name: str, result, step_number: int):
        """处理执行成功"""
        state.tool_results[tool_name] = result.data
        
        if result.data:
            TargetContextUpdater.update_context(state, tool_name, result.data)
        
        self._mark_task_completed(state, tool_name)
        
        logger.info(f"[{state.task_id}] ✅ 工具执行成功: {tool_name}")
        
        state.update_execution_step(
            step_number,
            result=result.data,
            status="success",
            state_transitions=["completed"]
        )
        
        self._update_progress(state, f"完成 {tool_name}")
    
    async def _handle_failure(self, state: AgentState, tool_name: str, result, step_number: int):
        """处理执行失败"""
        logger.warning(f"[{state.task_id}] ⚠️ 工具执行失败: {tool_name} - {result.error}")
        state.add_error(f"工具执行失败: {tool_name} - {result.error}")
        
        state.update_execution_step(
            step_number,
            result={"error": result.error},
            status="failed",
            state_transitions=["failed"]
        )
        
        self._mark_task_completed(state, tool_name)


class InfoResultVerificationNode(BaseResultVerificationNode):
    """信息收集结果验证节点"""
    
    def __init__(self):
        super().__init__(stage=NodeStage.INFO_COLLECTION)
    
    async def _verify_results(self, state: AgentState) -> None:
        """验证信息收集结果"""
        pass


# ============================================================================
# 漏洞扫描子图节点
# ============================================================================

VULN_SCAN_TOOLS = [
    "sqli_scan", "xss_scan", "csrf_scan", "vuln_infoleak_scan",
    "fileupload_scan", "cmdi_scan", "weakpass_scan", "lfi_scan", "ssrf_scan"
]


class VulnScanPlanningNode(BasePlanningNode):
    """漏洞扫描任务规划节点"""
    
    def __init__(self):
        super().__init__(stage=NodeStage.VULN_SCAN)
    
    async def _plan_tasks(self, state: AgentState) -> List[str]:
        """规划漏洞扫描任务"""
        tasks = ["sqli_scan", "xss_scan", "csrf_scan", "vuln_infoleak_scan"]
        
        cms = state.target_context.get("cms", "").lower()
        cms_task_map = {
            "wordpress": ["sqli_scan", "xss_scan"],
            "drupal": ["sqli_scan", "xss_scan"],
            "joomla": ["sqli_scan", "xss_scan"]
        }
        
        if cms in cms_task_map:
            tasks = cms_task_map[cms]
        
        return tasks
    
    def _get_fallback_tasks(self) -> List[str]:
        return VULN_SCAN_TOOLS
    
    def _get_valid_tools(self) -> List[str]:
        return VULN_SCAN_TOOLS


class VulnToolExecutionNode(BaseToolExecutionNode):
    """漏洞扫描工具执行节点"""
    
    def __init__(self):
        super().__init__(stage=NodeStage.VULN_SCAN)
    
    async def _execute_tool(self, state: AgentState, tool_name: str):
        """执行漏洞扫描工具"""
        if tool_name not in registry.tools:
            raise ValueError(f"工具未注册: {tool_name}")
        
        tool_wrapper = registry.tools[tool_name]
        return await tool_wrapper.execute(state.target)
    
    async def _handle_success(self, state: AgentState, tool_name: str, result, step_number: int):
        """处理执行成功"""
        state.tool_results[tool_name] = result.data
        
        vuln_data = result.data
        
        if isinstance(vuln_data, dict):
            for key in ["vulnerabilities", "fileupload_results", "cmdi_results", 
                          "weakpass_results", "lfi_results", "ssrf_results"]:
                if key in vuln_data and vuln_data[key]:
                    vulns = vuln_data[key]
                    if isinstance(vulns, list):
                        for vuln in vulns:
                            state.add_vulnerability(vuln)
                    elif isinstance(vulns, dict):
                        state.add_vulnerability(vulns)
        
        self._mark_task_completed(state, tool_name)
        
        logger.info(f"[{state.task_id}] ✅ 漏洞扫描工具执行成功: {tool_name}")
        
        state.update_execution_step(
            step_number,
            result=result.data,
            status="success",
            state_transitions=["completed"]
        )
        
        self._update_progress(state, f"完成 {tool_name}")
    
    async def _handle_failure(self, state: AgentState, tool_name: str, result, step_number: int):
        """处理执行失败"""
        logger.warning(f"[{state.task_id}] ⚠️ 漏洞扫描工具执行失败: {tool_name}")
        state.add_error(f"漏洞扫描工具执行失败: {tool_name}")
        
        state.update_execution_step(
            step_number,
            result={"error": result.error if hasattr(result, 'error') else "未知错误"},
            status="failed",
            state_transitions=["failed"]
        )
        
        self._mark_task_completed(state, tool_name)


class VulnResultAggregationNode:
    """漏洞扫描结果汇总节点"""
    
    def __init__(self):
        logger.info("📊 漏洞扫描结果汇总节点初始化")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """汇总漏洞扫描结果"""
        logger.info(f"[{state.task_id}] 📊 汇总漏洞扫描结果")
        
        total_vulns = len(state.vulnerabilities)
        
        state.vuln_scan_results = {
            "total_vulnerabilities": total_vulns,
            "vulnerabilities": state.vulnerabilities,
            "tools_used": [t for t in state.completed_tasks if t in VULN_SCAN_TOOLS]
        }
        
        state.update_stage_status("tool_execution", "completed", "完成", 100, f"发现 {total_vulns} 个漏洞")
        
        logger.info(f"[{state.task_id}] ✅ 漏洞扫描结果汇总完成: 发现 {total_vulns} 个漏洞")
        
        return state


# ============================================================================
# POC验证子图节点
# ============================================================================

class PocTaskPlanningNode(BasePlanningNode):
    """POC任务规划节点"""
    
    def __init__(self):
        super().__init__(stage=NodeStage.POC_VERIFICATION)
    
    async def _plan_tasks(self, state: AgentState) -> List[str]:
        """规划POC验证任务"""
        poc_tasks = []
        
        cms = state.target_context.get("cms", "").lower()
        if cms:
            cms_pocs = POCAdapter.get_poc_by_cms(cms)
            poc_tasks.extend(cms_pocs)
        
        open_ports = state.target_context.get("open_ports", [])
        for port in open_ports:
            port_pocs = POCAdapter.get_poc_by_port(port)
            poc_tasks.extend(port_pocs)
        
        poc_tasks = list(set(poc_tasks))
        
        return [t for t in poc_tasks if t not in state.completed_tasks]
    
    def _get_fallback_tasks(self) -> List[str]:
        return []
    
    def _get_valid_tools(self) -> List[str]:
        return [t["name"] for t in registry.list_tools() if t["name"].startswith("poc_")]


class PocExecutionNode(BaseToolExecutionNode):
    """POC执行节点"""
    
    def __init__(self):
        super().__init__(stage=NodeStage.POC_VERIFICATION)
    
    async def _execute_tool(self, state: AgentState, tool_name: str):
        """执行POC验证"""
        if tool_name not in registry.tools:
            raise ValueError(f"POC未注册: {tool_name}")
        
        tool_wrapper = registry.tools[tool_name]
        return await tool_wrapper.execute(state.target)
    
    async def _handle_success(self, state: AgentState, tool_name: str, result, step_number: int):
        """处理执行成功"""
        state.tool_results[tool_name] = result.data
        
        if result.data and result.data.get("vulnerabilities"):
            for vuln in result.data["vulnerabilities"]:
                state.add_vulnerability(vuln)
        
        self._mark_task_completed(state, tool_name)
        
        logger.info(f"[{state.task_id}] ✅ POC验证成功: {tool_name}")
        
        state.update_execution_step(
            step_number,
            result=result.data,
            status="success",
            state_transitions=["completed"]
        )
        
        self._update_progress(state, f"完成 {tool_name}")
    
    async def _handle_failure(self, state: AgentState, tool_name: str, result, step_number: int):
        """处理执行失败"""
        logger.warning(f"[{state.task_id}] ⚠️ POC验证失败: {tool_name}")
        state.add_error(f"POC验证失败: {tool_name}")
        
        state.update_execution_step(
            step_number,
            result={"error": result.error if hasattr(result, 'error') else "未知错误"},
            status="failed",
            state_transitions=["failed"]
        )
        
        self._mark_task_completed(state, tool_name)


class PocResultVerificationNode(BaseResultVerificationNode):
    """POC结果验证节点"""
    
    def __init__(self):
        super().__init__(stage=NodeStage.POC_VERIFICATION)
    
    async def _verify_results(self, state: AgentState) -> None:
        """验证POC结果"""
        pass

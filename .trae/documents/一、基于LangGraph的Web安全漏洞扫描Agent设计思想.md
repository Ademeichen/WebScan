## 一、基于LangGraph的Web安全漏洞扫描Agent设计思想

### 核心目标
构建一个具备**自主任务规划、工具调用、结果迭代验证、漏洞分析与报告生成**的智能Agent，替代人工完成端到端的Web安全扫描流程，适配项目现有插件/POC体系，补齐AI部分业务逻辑短板。

### 核心架构设计
#### 1. 分层架构
| 层级         | 职责                                                                 |
|--------------|----------------------------------------------------------------------|
| 状态层       | 管理扫描全生命周期状态（目标、任务、结果、记忆、错误），基于LangGraph State定义 |
| 决策层       | 基于当前状态和扫描结果，决定下一步执行的子任务/工具（核心控制逻辑）|
| 工具层       | 封装项目现有扫描插件、POC验证、AWVS集成等能力，提供标准化调用接口       |
| 执行层       | 异步执行工具调用，处理超时、异常，返回结构化结果                       |
| 汇总层       | 整合所有扫描结果，分析漏洞严重程度，生成标准化报告                     |

#### 2. 核心工作流程（LangGraph有向图）
```
初始化 → 任务规划 → 工具执行（循环） → 结果验证 → 漏洞分析 → 报告生成 → 结束
          ↑                              ↓
          └────────── 结果不满足 → 重新规划 ────────┘
```

#### 3. 关键设计点
- **任务拆解**：将「综合扫描」拆解为基础信息收集→端口扫描→WAF/CDN检测→CMS识别→POC验证→漏洞分析等子任务；
- **工具路由**：根据子任务类型自动匹配工具（如CMS识别→whatcms插件、POC验证→对应CVE脚本）；
- **记忆机制**：记录已执行步骤、已发现漏洞、目标特征（如CMS类型），避免重复扫描；
- **迭代验证**：若POC扫描无结果，自动调整扫描策略（如更换端口、调整请求头）；
- **异步兼容**：适配项目asyncio+FastAPI的异步架构，所有工具调用异步化；
- **可扩展**：预留插件注册接口，新增扫描能力无需修改核心逻辑。

## 二、代码实现（适配项目现有结构）

### 1. 核心Agent实现（`agent/core.py` 完善版）
```python
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from langgraph.graph import StateGraph, END
from langgraph.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from loguru import logger

# 导入项目现有工具/插件
from plugins.portscan.portscan import ScanPort
from plugins.infoleak.infoleak import get_infoleak
from plugins.waf.waf import getwaf
from plugins.cdnexist.cdnexist import iscdn
from plugins.whatcms.whatcms import getwhatcms
from plugins.baseinfo.baseinfo import getbaseinfo
from poc.weblogic.cve_2020_2551_poc import poc as weblogic_2020_2551
from poc.struts2.struts2_009_poc import poc as struts2_009
from poc.tomcat.cve_2017_12615_poc import poc as tomcat_2017_12615
from task_executor import standardize_vuln_severity

# -------------------------- 1. 定义Agent状态（核心） --------------------------
@dataclass
class ScanState:
    """扫描Agent的状态管理类"""
    # 基础信息
    target: str  # 扫描目标（URL/IP）
    task_id: str  # 任务ID
    # 任务规划
    planned_tasks: List[str] = field(default_factory=list)  # 规划的子任务列表
    current_task: Optional[str] = None  # 当前执行的子任务
    completed_tasks: List[str] = field(default_factory=list)  # 已完成子任务
    # 执行结果
    tool_results: Dict[str, Any] = field(default_factory=dict)  # 工具执行结果
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)  # 发现的漏洞
    # 记忆与上下文
    target_context: Dict[str, Any] = field(default_factory=dict)  # 目标上下文（如CMS、端口、WAF等）
    # 异常处理
    errors: List[str] = field(default_factory=list)  # 执行错误
    retry_count: int = 0  # 重试次数
    # 控制开关
    is_complete: bool = False  # 任务是否完成

# -------------------------- 2. 工具注册与封装 --------------------------
class ScanToolRegistry:
    """扫描工具注册表，封装现有插件/POC，提供统一调用接口"""
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """注册项目现有工具"""
        # 基础信息收集类
        self.tools["baseinfo"] = self._wrap_async(getbaseinfo)
        self.tools["portscan"] = self._wrap_portscan()
        self.tools["waf_detect"] = self._wrap_async(getwaf)
        self.tools["cdn_detect"] = self._wrap_async(iscdn)
        self.tools["cms_identify"] = self._wrap_async(getwhatcms)
        self.tools["infoleak_scan"] = self._wrap_async(get_infoleak)
        
        # POC验证类（按CMS/中间件分类）
        self.tools["poc_weblogic_2020_2551"] = self._wrap_async(weblogic_2020_2551)
        self.tools["poc_struts2_009"] = self._wrap_async(struts2_009)
        self.tools["poc_tomcat_2017_12615"] = self._wrap_async(tomcat_2017_12615)

    def _wrap_async(self, func: Callable) -> Callable:
        """同步工具封装为异步调用"""
        async def async_wrapper(target: str, **kwargs) -> Any:
            try:
                # 适配无参数/有参数的工具
                if kwargs:
                    return await asyncio.to_thread(func, target, **kwargs)
                return await asyncio.to_thread(func, target)
            except Exception as e:
                logger.error(f"工具执行失败 {func.__name__}: {str(e)}")
                return {"status": "failed", "error": str(e)}
        return async_wrapper

    def _wrap_portscan(self) -> Callable:
        """端口扫描工具封装"""
        async def async_portscan(target: str) -> Dict[str, Any]:
            try:
                scanner = ScanPort(target)
                result = await asyncio.to_thread(scanner.run_scan)
                if result:
                    return {
                        "status": "success",
                        "open_ports": scanner.get_results(),
                        "target": target
                    }
                return {"status": "success", "open_ports": [], "target": target}
            except Exception as e:
                logger.error(f"端口扫描失败: {str(e)}")
                return {"status": "failed", "error": str(e)}
        return async_portscan

    async def call_tool(self, tool_name: str, target: str, **kwargs) -> Any:
        """统一工具调用入口"""
        if tool_name not in self.tools:
            raise ValueError(f"未知工具: {tool_name}")
        return await self.tools[tool_name](target, **kwargs)

# -------------------------- 3. Agent节点实现 --------------------------
class ScanAgentNodes:
    """Agent节点函数（对应工作流程的各个步骤）"""
    def __init__(self):
        self.tool_registry = ScanToolRegistry()
        # 任务规划提示词（可根据实际需求优化）
        self.plan_prompt = PromptTemplate(
            template="""
            你是Web安全扫描专家，需要为目标 {target} 规划扫描任务。
            可用子任务：baseinfo(基础信息), portscan(端口扫描), waf_detect(WAF检测), cdn_detect(CDN检测), 
            cms_identify(CMS识别), infoleak_scan(信息泄露), poc_{中间件}_{CVE}(POC验证)。
            规划规则：
            1. 先执行基础信息收集类任务，再执行POC验证；
            2. 根据基础信息结果选择POC（如CMS为WordPress则跳过WebLogic POC）；
            3. 避免无意义的POC扫描；
            4. 返回格式为JSON数组，仅包含子任务名称。
            """,
            input_variables=["target"]
        )

    async def task_planning(self, state: ScanState) -> ScanState:
        """节点1：任务规划"""
        logger.info(f"[{state.task_id}] 开始任务规划，目标: {state.target}")
        # 基础规划（可替换为LLM生成，此处先实现规则化版本）
        base_tasks = ["baseinfo", "portscan", "waf_detect", "cdn_detect", "cms_identify", "infoleak_scan"]
        state.planned_tasks = base_tasks
        state.current_task = state.planned_tasks[0] if state.planned_tasks else None
        logger.info(f"[{state.task_id}] 规划任务: {state.planned_tasks}")
        return state

    async def tool_execution(self, state: ScanState) -> ScanState:
        """节点2：工具执行"""
        if not state.current_task:
            state.is_complete = True
            return state
        
        tool_name = state.current_task
        logger.info(f"[{state.task_id}] 执行工具: {tool_name}")
        
        try:
            # 调用工具
            result = await self.tool_registry.call_tool(tool_name, state.target)
            state.tool_results[tool_name] = result

            # 更新目标上下文（关键：为后续任务提供依据）
            if tool_name == "baseinfo" and result["status"] == "success":
                state.target_context.update(result)
            elif tool_name == "cms_identify" and result["status"] == "success":
                state.target_context["cms"] = result.get("cms", "unknown")
            elif tool_name == "portscan" and result["status"] == "success":
                state.target_context["open_ports"] = result.get("open_ports", [])

            # 若为POC工具，解析漏洞结果
            if tool_name.startswith("poc_") and result["status"] == "success":
                if result.get("vulnerable", False):
                    vuln_info = {
                        "cve": tool_name.replace("poc_", ""),
                        "target": state.target,
                        "severity": standardize_vuln_severity(tool_name),
                        "details": result.get("details", {})
                    }
                    state.vulnerabilities.append(vuln_info)
                    logger.warning(f"[{state.task_id}] 发现漏洞: {vuln_info}")

            # 标记任务完成
            state.completed_tasks.append(state.current_task)
            state.planned_tasks.remove(state.current_task)
            # 更新下一个任务
            state.current_task = state.planned_tasks[0] if state.planned_tasks else None

        except Exception as e:
            state.errors.append(f"工具执行失败 {tool_name}: {str(e)}")
            state.retry_count += 1
            # 重试逻辑（最多3次）
            if state.retry_count < 3:
                logger.warning(f"[{state.task_id}] 工具 {tool_name} 执行失败，重试 {state.retry_count}/3")
            else:
                state.completed_tasks.append(state.current_task)
                state.planned_tasks.remove(state.current_task)
                state.current_task = state.planned_tasks[0] if state.planned_tasks else None
                state.retry_count = 0

        return state

    async def result_verification(self, state: ScanState) -> ScanState:
        """节点3：结果验证与补充任务"""
        logger.info(f"[{state.task_id}] 验证扫描结果，已完成任务: {state.completed_tasks}")
        
        # 基于上下文补充POC任务（核心逻辑：根据CMS/中间件自动选择POC）
        cms = state.target_context.get("cms", "unknown")
        open_ports = state.target_context.get("open_ports", [])
        supplement_tasks = []

        # 示例规则：根据CMS/端口补充POC
        if "weblogic" in cms.lower() or 7001 in open_ports:
            supplement_tasks.append("poc_weblogic_2020_2551")
        if "struts2" in cms.lower():
            supplement_tasks.append("poc_struts2_009")
        if "tomcat" in cms.lower() or 8080 in open_ports:
            supplement_tasks.append("poc_tomcat_2017_12615")

        # 去重并添加到规划任务
        for task in supplement_tasks:
            if task not in state.completed_tasks and task not in state.planned_tasks:
                state.planned_tasks.append(task)
                logger.info(f"[{state.task_id}] 补充POC任务: {task}")

        # 更新当前任务
        state.current_task = state.planned_tasks[0] if state.planned_tasks else None
        # 验证是否需要继续执行
        if not state.planned_tasks:
            state.is_complete = True

        return state

    async def vulnerability_analysis(self, state: ScanState) -> ScanState:
        """节点4：漏洞分析（严重度排序、去重）"""
        logger.info(f"[{state.task_id}] 分析漏洞结果，共发现 {len(state.vulnerabilities)} 个漏洞")
        
        # 漏洞去重 + 严重度排序
        unique_vulns = {}
        for vuln in state.vulnerabilities:
            key = f"{vuln['cve']}_{vuln['target']}"
            if key not in unique_vulns:
                unique_vulns[key] = vuln

        # 按严重度排序（critical > high > medium > low）
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        sorted_vulns = sorted(
            unique_vulns.values(),
            key=lambda x: severity_order.get(x["severity"], 0),
            reverse=True
        )

        state.vulnerabilities = sorted_vulns
        return state

    async def report_generation(self, state: ScanState) -> ScanState:
        """节点5：报告生成"""
        logger.info(f"[{state.task_id}] 生成扫描报告")
        
        report = {
            "task_id": state.task_id,
            "target": state.target,
            "scan_time": asyncio.get_event_loop().time(),
            "completed_tasks": state.completed_tasks,
            "target_context": state.target_context,
            "vulnerabilities": state.vulnerabilities,
            "errors": state.errors,
            "summary": {
                "total_vulnerabilities": len(state.vulnerabilities),
                "critical_count": len([v for v in state.vulnerabilities if v["severity"] == "critical"]),
                "high_count": len([v for v in state.vulnerabilities if v["severity"] == "high"]),
            }
        }

        state.tool_results["final_report"] = report
        state.is_complete = True
        logger.info(f"[{state.task_id}] 报告生成完成，漏洞总数: {report['summary']['total_vulnerabilities']}")
        return state

# -------------------------- 4. 构建LangGraph图 --------------------------
def build_scan_agent_graph() -> StateGraph:
    """构建扫描Agent的LangGraph图"""
    nodes = ScanAgentNodes()
    graph = StateGraph(ScanState)

    # 注册节点
    graph.add_node("task_planning", nodes.task_planning)
    graph.add_node("tool_execution", nodes.tool_execution)
    graph.add_node("result_verification", nodes.result_verification)
    graph.add_node("vulnerability_analysis", nodes.vulnerability_analysis)
    graph.add_node("report_generation", nodes.report_generation)

    # 定义边（核心流程）
    graph.set_entry_point("task_planning")
    graph.add_edge("task_planning", "tool_execution")
    graph.add_edge("tool_execution", "result_verification")

    # 条件边：验证后判断是否继续执行工具
    def should_continue(state: ScanState) -> str:
        if state.is_complete:
            return "vulnerability_analysis"
        return "tool_execution"
    graph.add_conditional_edges("result_verification", should_continue)

    # 后续流程
    graph.add_edge("vulnerability_analysis", "report_generation")
    graph.add_edge("report_generation", END)

    # 编译图
    return graph.compile()

# -------------------------- 5. Agent调用入口（适配现有API） --------------------------
async def run_scan_agent(target: str, task_id: str) -> Dict[str, Any]:
    """
    扫描Agent调用入口（供api/agent.py调用）
    :param target: 扫描目标（URL/IP）
    :param task_id: 任务ID
    :return: 扫描报告
    """
    # 初始化状态
    initial_state = ScanState(
        target=target,
        task_id=task_id
    )

    # 构建并运行图
    graph = build_scan_agent_graph()
    final_state = await graph.ainvoke(initial_state)

    # 返回最终报告
    return final_state.tool_results.get("final_report", {})
```

### 2. 适配现有API（`api/agent.py` 补充）
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agent.core import run_scan_agent
from loguru import logger
import uuid

router = APIRouter(prefix="/agent", tags=["agent"])

# 请求模型
class AgentScanRequest(BaseModel):
    target: str  # 扫描目标（URL/IP）

# 内存级任务存储（可替换为数据库）
agent_tasks = {}

@router.post("/execute")
async def execute_agent_task(request: AgentScanRequest):
    """执行AI Agent扫描任务（适配现有API）"""
    try:
        task_id = str(uuid.uuid4())
        # 异步执行扫描（避免阻塞API）
        asyncio.create_task(_run_agent_task(task_id, request.target))
        agent_tasks[task_id] = {
            "task_id": task_id,
            "target": request.target,
            "status": "running",
            "created_at": asyncio.get_event_loop().time()
        }
        return {"code": 200, "data": {"task_id": task_id}, "msg": "任务已启动"}
    except Exception as e:
        logger.error(f"Agent任务启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"任务启动失败: {str(e)}")

async def _run_agent_task(task_id: str, target: str):
    """后台执行Agent任务"""
    try:
        result = await run_scan_agent(target, task_id)
        agent_tasks[task_id].update({
            "status": "completed",
            "result": result,
            "completed_at": asyncio.get_event_loop().time()
        })
    except Exception as e:
        agent_tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": asyncio.get_event_loop().time()
        })
        logger.error(f"Agent任务执行失败 {task_id}: {str(e)}")

@router.get("/tasks/{task_id}")
async def get_agent_task(task_id: str):
    """获取Agent任务详情（适配现有API）"""
    if task_id not in agent_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"code": 200, "data": agent_tasks[task_id]}
```

## 三、AI部分业务逻辑完善建议
### 1. LLM增强任务规划
当前任务规划为规则化实现，可接入项目现有OpenAI/通义千问能力，通过LLM生成更智能的扫描任务：
```python
# 在ScanAgentNodes中替换task_planning的规则化逻辑
from langchain.chat_models import ChatOpenAI
from config import settings

async def task_planning(self, state: ScanState) -> ScanState:
    llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        model_name=settings.MODEL_ID
    )
    plan_chain = self.plan_prompt | llm | RunnableLambda(lambda x: eval(x.content))
    state.planned_tasks = await plan_chain.ainvoke({"target": state.target})
    # 后续逻辑不变...
```

### 2. 记忆机制持久化
将Agent状态（尤其是target_context、vulnerabilities）持久化到数据库（models.py中新增AgentState模型），支持断点续扫、历史扫描对比。

### 3. 工具扩展能力
新增工具注册装饰器，简化新增扫描插件的流程：
```python
def register_scan_tool(tool_name: str):
    def decorator(func: Callable):
        ScanToolRegistry().tools[tool_name] = ScanToolRegistry()._wrap_async(func)
        return func
    return decorator

# 新增插件时只需添加装饰器
@register_scan_tool("new_scan_tool")
def new_scan_tool(target: str) -> Dict:
    # 扫描逻辑
    pass
```

### 4. 漏洞知识库联动
集成项目`kb.py`的知识库能力，在漏洞分析阶段自动匹配知识库中的漏洞修复建议：
```python
# 在vulnerability_analysis节点中补充
from api.kb import get_kb_entry_by_cve
for vuln in state.vulnerabilities:
    kb_entry = await get_kb_entry_by_cve(vuln["cve"])
    if kb_entry:
        vuln["fix_suggestion"] = kb_entry.get("fix_suggestion")
```

### 5. 异常重试策略优化
为不同工具定制重试策略（如端口扫描超时重试、POC验证失败换端口重试），提升扫描成功率。

## 四、使用示例
```bash
# 1. 启动服务
python main.py

# 2. 调用Agent扫描API
curl -X POST "http://127.0.0.1:3000/agent/execute" \
-H "Content-Type: application/json" \
-d '{"target": "http://example.com"}'

# 3. 查询任务结果
curl "http://127.0.0.1:3000/agent/tasks/{task_id}"
```

该设计完全适配项目现有目录结构和技术栈，补齐了AI Agent的核心业务逻辑，同时具备良好的可扩展性和异步兼容性，可直接集成到现有项目中。
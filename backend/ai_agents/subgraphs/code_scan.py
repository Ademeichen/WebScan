"""
代码扫描子图

负责代码生成、代码执行和功能增强。
执行时间目标: < 1分钟
最大重试次数: 3次
"""
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CodeScanState:
    """
    代码扫描状态
    
    CodeScanGraph专用的轻量级状态类。
    """
    target: str
    task_id: str
    need_custom_scan: bool = False
    custom_scan_type: Optional[str] = None
    custom_scan_requirements: Optional[str] = None
    need_capability_enhancement: bool = False
    capability_requirement: Optional[str] = None
    generated_code: Optional[str] = None
    code_language: str = "python"
    execution_result: Dict[str, Any] = field(default_factory=dict)
    enhancement_result: Dict[str, Any] = field(default_factory=dict)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    execution_logs: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "task_id": self.task_id,
            "need_custom_scan": self.need_custom_scan,
            "custom_scan_type": self.custom_scan_type,
            "custom_scan_requirements": self.custom_scan_requirements,
            "need_capability_enhancement": self.need_capability_enhancement,
            "capability_requirement": self.capability_requirement,
            "generated_code": self.generated_code,
            "code_language": self.code_language,
            "execution_result": self.execution_result,
            "enhancement_result": self.enhancement_result,
            "findings": self.findings,
            "execution_logs": self.execution_logs,
            "errors": self.errors,
            "retry_count": self.retry_count,
            "execution_time": self.execution_time
        }


class CodeGenerationNode:
    """
    代码生成节点
    
    根据扫描需求生成自定义扫描代码。
    """
    
    def __init__(self):
        self.timeout = 10.0
    
    async def __call__(self, state: CodeScanState) -> CodeScanState:
        logger.info(f"[{state.task_id}] 📝 开始代码生成, 类型: {state.custom_scan_type}")
        
        if not state.need_custom_scan:
            logger.info(f"[{state.task_id}] ⏭️ 无需自定义扫描, 跳过代码生成")
            return state
        
        try:
            from ..code_execution.code_generator import CodeGenerator
            
            generator = CodeGenerator()
            result = await generator.generate_code(
                scan_type=state.custom_scan_type or "port_scan",
                target=state.target,
                requirements=state.custom_scan_requirements or "",
                language=state.code_language
            )
            
            if result:
                state.generated_code = result.code if hasattr(result, 'code') else str(result)
                state.execution_logs.append(f"代码生成成功: {len(state.generated_code)} 字符")
                logger.info(f"[{state.task_id}] ✅ 代码生成成功")
            else:
                state.errors.append("代码生成返回空结果")
                logger.error(f"[{state.task_id}] ❌ 代码生成返回空结果")
                
        except Exception as e:
            error_msg = f"代码生成失败: {str(e)}"
            state.errors.append(error_msg)
            logger.error(f"[{state.task_id}] ❌ {error_msg}")
        
        return state


class CodeExecutionNode:
    """
    代码执行节点
    
    执行生成的自定义扫描代码。
    """
    
    def __init__(self):
        self.timeout = 30.0
    
    async def __call__(self, state: CodeScanState) -> CodeScanState:
        logger.info(f"[{state.task_id}] 🚀 开始代码执行")
        
        if not state.generated_code:
            logger.info(f"[{state.task_id}] ⏭️ 无生成代码, 跳过执行")
            return state
        
        try:
            from ..code_execution.executor import UnifiedExecutor
            
            executor = UnifiedExecutor()
            result = await executor.execute(
                code=state.generated_code,
                language=state.code_language,
                target=state.target
            )
            
            state.execution_result = result
            
            if result.get("status") == "success":
                state.findings.append({
                    "type": "custom_scan",
                    "output": result.get("output", ""),
                    "execution_time": result.get("execution_time", 0)
                })
                state.execution_logs.append(f"代码执行成功: {result.get('output', '')[:100]}")
                logger.info(f"[{state.task_id}] ✅ 代码执行成功")
            else:
                error_msg = result.get("error", "未知错误")
                state.errors.append(f"代码执行失败: {error_msg}")
                state.need_capability_enhancement = True
                state.capability_requirement = "安装缺失的依赖包"
                logger.warning(f"[{state.task_id}] ⚠️ 代码执行失败: {error_msg}")
                
        except Exception as e:
            error_msg = f"代码执行异常: {str(e)}"
            state.errors.append(error_msg)
            logger.error(f"[{state.task_id}] ❌ {error_msg}")
        
        return state


class CapabilityEnhancementNode:
    """
    功能增强节点
    
    安装缺失的依赖包以支持代码执行。
    """
    
    def __init__(self):
        self.timeout = 30.0
    
    async def __call__(self, state: CodeScanState) -> CodeScanState:
        logger.info(f"[{state.task_id}] 🔧 开始功能增强")
        
        if not state.need_capability_enhancement:
            logger.info(f"[{state.task_id}] ⏭️ 无需功能增强, 跳过")
            return state
        
        if state.retry_count >= state.max_retries:
            logger.warning(f"[{state.task_id}] ⚠️ 达到最大重试次数, 跳过功能增强")
            return state
        
        try:
            from ..code_execution.capability_enhancer import CapabilityEnhancer
            
            enhancer = CapabilityEnhancer()
            result = await enhancer.enhance_capability(
                requirement=state.capability_requirement or "安装依赖",
                target=state.target
            )
            
            state.enhancement_result = result
            state.retry_count += 1
            
            if result.get("status") == "success":
                state.need_capability_enhancement = False
                state.execution_logs.append(f"功能增强成功: {result.get('installed_packages', [])}")
                logger.info(f"[{state.task_id}] ✅ 功能增强成功")
            else:
                error_msg = result.get("error", "未知错误")
                state.errors.append(f"功能增强失败: {error_msg}")
                logger.error(f"[{state.task_id}] ❌ 功能增强失败: {error_msg}")
                
        except Exception as e:
            error_msg = f"功能增强异常: {str(e)}"
            state.errors.append(error_msg)
            logger.error(f"[{state.task_id}] ❌ {error_msg}")
        
        return state


class CodeScanGraph:
    """
    代码扫描图
    
    执行自定义代码扫描任务。
    """
    
    def __init__(self, max_execution_time: float = 60.0, max_retries: int = 3):
        self.max_execution_time = max_execution_time
        self.max_retries = max_retries
        self.code_generation_node = CodeGenerationNode()
        self.code_execution_node = CodeExecutionNode()
        self.capability_enhancement_node = CapabilityEnhancementNode()
        logger.info(f"📊 CodeScanGraph 初始化, 最大执行时间: {max_execution_time}s, 最大重试: {max_retries}")
    
    async def execute(self, state: CodeScanState) -> CodeScanState:
        """
        执行代码扫描
        
        Args:
            state: 代码扫描状态
            
        Returns:
            CodeScanState: 更新后的状态
        """
        start_time = time.time()
        logger.info(f"[{state.task_id}] 🚀 开始代码扫描图")
        
        try:
            while state.retry_count < self.max_retries:
                if time.time() - start_time > self.max_execution_time:
                    logger.warning(f"[{state.task_id}] ⚠️ 代码扫描超时")
                    break
                
                if not state.generated_code:
                    state = await self.code_generation_node(state)
                
                if state.generated_code:
                    state = await self.code_execution_node(state)
                    
                    if state.execution_result.get("status") == "success":
                        break
                    
                    if state.need_capability_enhancement:
                        state = await self.capability_enhancement_node(state)
                else:
                    break
            
            total_time = time.time() - start_time
            state.execution_time = total_time
            
            if total_time > self.max_execution_time:
                logger.warning(f"[{state.task_id}] ⚠️ CodeScanGraph 执行超时: {total_time:.2f}s")
            else:
                logger.info(f"[{state.task_id}] ✅ CodeScanGraph 执行完成, 耗时: {total_time:.2f}s")
            
        except Exception as e:
            logger.error(f"[{state.task_id}] ❌ CodeScanGraph 执行失败: {str(e)}")
            state.errors.append(f"代码扫描图失败: {str(e)}")
        
        return state
    
    def get_result_dto(self, state: CodeScanState) -> 'CodeScanResultDTO':
        """
        将状态转换为CodeScanResultDTO
        
        Args:
            state: 代码扫描状态
            
        Returns:
            CodeScanResultDTO: 代码扫描结果DTO
        """
        from .dto import CodeScanResultDTO, TaskStatus
        
        status = TaskStatus.COMPLETED if not state.errors else TaskStatus.FAILED
        
        return CodeScanResultDTO(
            task_id=state.task_id,
            target=state.target,
            status=status,
            generated_code=state.generated_code,
            execution_result=state.execution_result,
            findings=state.findings,
            execution_logs=state.execution_logs,
            errors=state.errors,
            execution_time=state.execution_time
        )

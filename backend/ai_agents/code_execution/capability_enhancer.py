"""
功能补充模块

支持动态功能补充，允许AI根据需求执行代码以增强自身能力。
"""
import logging
import importlib.util
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime

from .environment import EnvironmentAwareness
from .code_generator import CodeGenerator

logger = logging.getLogger(__name__)


class Capability:
    """
    能力类
    
    表示一个可用的扫描能力。
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        dependencies: List[str] = None,
        execute_func: Callable = None
    ):
        self.name = name
        self.description = description
        self.version = version
        self.dependencies = dependencies or []
        self.execute_func = execute_func
        self.created_at = datetime.now()
        self.execution_count = 0
    
    async def execute(self, target: str, **kwargs) -> Dict[str, Any]:
        """
        执行能力
        
        Args:
            target: 扫描目标
            **kwargs: 额外参数
            
        Returns:
            Dict: 执行结果
        """
        if not self.execute_func:
            return {
                "status": "failed",
                "error": "未定义执行函数"
            }
        
        try:
            self.execution_count += 1
            result = await self.execute_func(target, **kwargs)
            return {
                "status": "success",
                "data": result,
                "capability": self.name,
                "version": self.version
            }
        except Exception as e:
            logger.error(f"能力执行失败 {self.name}: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "capability": self.name
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict: 能力信息
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "execution_count": self.execution_count
        }


class CapabilityEnhancer:
    """
    功能补充器类
    
    负责动态生成和注册新的扫描能力。
    """
    
    def __init__(self):
        self.env_awareness = EnvironmentAwareness()
        self.code_generator = CodeGenerator()
        self.capabilities: Dict[str, Capability] = {}
        self.workspace = Path("ai_agents/code_execution/workspace")
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ 功能补充器初始化完成")
    
    async def enhance_capability(
        self,
        requirement: str,
        target: str,
        capability_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        增强功能
        
        根据需求动态生成并注册新的能力。
        
        Args:
            requirement: 功能需求描述
            target: 扫描目标
            capability_name: 能力名称（可选）
            
        Returns:
            Dict: 增强结果
        """
        try:
            logger.info(f"🔧 开始增强功能: {requirement}")
            
            # 生成能力名称
            if not capability_name:
                capability_name = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 生成代码
            code_response = await self.code_generator.generate_code(
                scan_type="custom",
                target=target,
                requirements=requirement,
                language="python"
            )
            
            # 验证代码
            validation = self.code_generator.validate_code(
                code_response.code,
                code_response.language
            )
            
            if not validation["valid"]:
                logger.warning(f"代码验证失败: {validation['issues']}")
                return {
                    "status": "failed",
                    "error": "代码验证失败",
                    "issues": validation["issues"]
                }
            
            # 保存代码
            code_file = self.workspace / f"{capability_name}.py"
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(code_response.code)
            
            # 创建能力
            capability = await self._create_capability_from_code(
                capability_name,
                requirement,
                code_file
            )
            
            # 注册能力
            self.capabilities[capability_name] = capability
            
            logger.info(f"✅ 功能增强完成: {capability_name}")
            
            return {
                "status": "success",
                "capability": capability.to_dict(),
                "code_file": str(code_file),
                "validation": validation
            }
            
        except Exception as e:
            logger.error(f"功能增强失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _create_capability_from_code(
        self,
        name: str,
        description: str,
        code_file: Path
    ) -> Capability:
        """
        从代码文件创建能力
        
        Args:
            name: 能力名称
            description: 描述
            code_file: 代码文件路径
            
        Returns:
            Capability: 能力对象
        """
        spec = importlib.util.spec_from_file_location(name, code_file)
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
            
            if hasattr(module, "execute"):
                execute_func = module.execute
            else:
                execute_func = None
            
            return Capability(
                name=name,
                description=description,
                version="1.0.0",
                execute_func=execute_func
            )
        except Exception as e:
            logger.error(f"加载能力失败 {name}: {str(e)}")
            return Capability(
                name=name,
                description=description,
                version="1.0.0",
                execute_func=None
            )
    
    def register_capability(
        self,
        name: str,
        description: str,
        execute_func: Callable,
        version: str = "1.0.0",
        dependencies: List[str] = None
    ):
        """
        注册能力
        
        Args:
            name: 能力名称
            description: 描述
            execute_func: 执行函数
            version: 版本
            dependencies: 依赖列表
        """
        capability = Capability(
            name=name,
            description=description,
            version=version,
            dependencies=dependencies,
            execute_func=execute_func
        )
        
        self.capabilities[name] = capability
        logger.info(f"✅ 注册能力: {name}")
    
    def get_capability(self, name: str) -> Optional[Capability]:
        """
        获取能力
        
        Args:
            name: 能力名称
            
        Returns:
            Optional[Capability]: 能力对象
        """
        return self.capabilities.get(name)
    
    def list_capabilities(self) -> List[Dict[str, Any]]:
        """
        列出所有能力
        
        Returns:
            List[Dict]: 能力列表
        """
        return [
            capability.to_dict()
            for capability in self.capabilities.values()
        ]
    
    async def execute_capability(
        self,
        name: str,
        target: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行能力
        
        Args:
            name: 能力名称
            target: 扫描目标
            **kwargs: 额外参数
            
        Returns:
            Dict: 执行结果
        """
        capability = self.get_capability(name)
        if not capability:
            return {
                "status": "failed",
                "error": f"能力不存在: {name}"
            }
        
        return await capability.execute(target, **kwargs)
    
    def remove_capability(self, name: str) -> bool:
        """
        移除能力
        
        Args:
            name: 能力名称
            
        Returns:
            bool: 是否成功移除
        """
        if name in self.capabilities:
            del self.capabilities[name]
            
            # 删除代码文件
            code_file = self.workspace / f"{name}.py"
            if code_file.exists():
                code_file.unlink()
            
            logger.info(f"✅ 移除能力: {name}")
            return True
        
        return False
    
    def get_capability_dependencies(self, name: str) -> List[str]:
        """
        获取能力的依赖
        
        Args:
            name: 能力名称
            
        Returns:
            List[str]: 依赖列表
        """
        capability = self.get_capability(name)
        if capability:
            return capability.dependencies
        return []
    
    def check_capability_dependencies(self, name: str) -> Dict[str, Any]:
        """
        检查能力依赖是否满足
        
        Args:
            name: 能力名称
            
        Returns:
            Dict: 依赖检查结果
        """
        dependencies = self.get_capability_dependencies(name)
        missing = []
        satisfied = []
        
        for dep in dependencies:
            if self.env_awareness.is_tool_available(dep):
                satisfied.append(dep)
            else:
                missing.append(dep)
        
        return {
            "capability": name,
            "dependencies": dependencies,
            "satisfied": satisfied,
            "missing": missing,
            "all_satisfied": len(missing) == 0
        }

"""
功能补充模块(优化版)

支持动态功能补充,允许AI根据需求执行代码以增强自身能力。

优化内容:
1. 实现单例模式,避免重复初始化
2. 增强错误处理和恢复机制
3. 添加能力版本管理和冲突检测
4. 实现异步依赖安装
5. 添加执行超时控制和结果缓存
6. 完善日志记录和监控
7. 添加资源清理机制
8. 增强代码验证逻辑
9. 实现能力持久化
10. 添加并发安全保护
"""
import logging
import importlib.util
import subprocess
import sys
import asyncio
import threading
import hashlib
import json
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from .environment import EnvironmentAwareness
from .code_generator import CodeGenerator

logger = logging.getLogger(__name__)


class CapabilityError(Exception):
    """能力异常基类"""
    pass


class CapabilityNotFoundError(CapabilityError):
    """能力不存在异常"""
    pass


class CapabilityExecutionError(CapabilityError):
    """能力执行异常"""
    pass


class DependencyInstallError(CapabilityError):
    """依赖安装异常"""
    pass


class CodeValidationError(CapabilityError):
    """代码验证异常"""
    pass


class Capability:
    """
    能力类(优化版)
    
    表示一个可用的扫描能力。
    
    优化内容:
    - 支持同步和异步执行函数
    - 添加执行超时控制
    - 添加执行结果缓存
    - 添加执行统计信息
    - 添加能力状态管理
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        dependencies: List[str] = None,
        execute_func: Callable = None,
        timeout: int = 60,
        enable_cache: bool = True
    ):
        self.name = name
        self.description = description
        self.version = version
        self.dependencies = dependencies or []
        self.execute_func = execute_func
        self.timeout = timeout
        self.enable_cache = enable_cache
        self.created_at = datetime.now()
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_execution_time = None
        self.last_execution_status = None
        self.cache: Dict[str, Any] = {}
        self.max_cache_size = 100
        self.status = "ready"  # ready, running, error, disabled
        self._lock = threading.Lock()
    
    async def execute(self, target: str, **kwargs) -> Dict[str, Any]:
        """
        执行能力(优化版)
        
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
        
        # 检查缓存
        cache_key = self._generate_cache_key(target, kwargs)
        if self.enable_cache and cache_key in self.cache:
            logger.debug(f"使用缓存结果: {self.name}")
            return self.cache[cache_key]
        
        # 检查状态
        if self.status == "disabled":
            return {
                "status": "failed",
                "error": "能力已禁用"
            }
        
        # 更新状态
        with self._lock:
            self.status = "running"
            self.execution_count += 1
        
        try:
            # 执行函数(支持同步和异步)
            if asyncio.iscoroutinefunction(self.execute_func):
                result = await asyncio.wait_for(
                    self.execute_func(target, **kwargs),
                    timeout=self.timeout
                )
            else:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, self.execute_func, target, **kwargs),
                    timeout=self.timeout
                )
            
            # 更新统计信息
            with self._lock:
                self.success_count += 1
                self.last_execution_time = datetime.now()
                self.last_execution_status = "success"
                self.status = "ready"
            
            response = {
                "status": "success",
                "data": result,
                "capability": self.name,
                "version": self.version
            }
            
            # 缓存结果
            if self.enable_cache:
                self._update_cache(cache_key, response)
            
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"能力执行超时 {self.name}")
            with self._lock:
                self.failure_count += 1
                self.last_execution_time = datetime.now()
                self.last_execution_status = "timeout"
                self.status = "ready"
            
            return {
                "status": "failed",
                "error": f"执行超时({self.timeout}s)",
                "capability": self.name
            }
            
        except Exception as e:
            logger.error(f"能力执行失败 {self.name}: {str(e)}")
            with self._lock:
                self.failure_count += 1
                self.last_execution_time = datetime.now()
                self.last_execution_status = "error"
                self.status = "ready"
            
            return {
                "status": "failed",
                "error": str(e),
                "capability": self.name
            }
    
    def _generate_cache_key(self, target: str, kwargs: Dict[str, Any]) -> str:
        """
        生成缓存键
        
        Args:
            target: 扫描目标
            kwargs: 额外参数
            
        Returns:
            str: 缓存键
        """
        key_str = f"{target}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _update_cache(self, key: str, value: Any):
        """
        更新缓存
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        with self._lock:
            if len(self.cache) >= self.max_cache_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            self.cache[key] = value
    
    def clear_cache(self):
        """清空缓存"""
        with self._lock:
            self.cache.clear()
    
    def disable(self):
        """禁用能力"""
        with self._lock:
            self.status = "disabled"
    
    def enable(self):
        """启用能力"""
        with self._lock:
            self.status = "ready"
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        with self._lock:
            return {
                "name": self.name,
                "execution_count": self.execution_count,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "success_rate": self.success_count / self.execution_count if self.execution_count > 0 else 0,
                "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
                "last_execution_status": self.last_execution_status,
                "status": self.status,
                "cache_size": len(self.cache)
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
            "timeout": self.timeout,
            "status": self.status,
            "statistics": self.get_statistics()
        }


class CapabilityEnhancer:
    """
    功能补充器类(优化版)
    
    负责动态生成和注册新的扫描能力。
    
    优化内容:
    - 实现单例模式
    - 添加能力版本管理
    - 添加能力冲突检测
    - 实现异步依赖安装
    - 添加能力持久化
    - 添加并发安全保护
    - 完善错误处理和恢复
    - 添加资源清理机制
    """
    
    # 单例实例
    _instance = None
    _instance_lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """
        实现单例模式
        
        确保全局只有一个CapabilityEnhancer实例
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化功能补充器(单例模式)
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._lock = threading.Lock()
        self._initialized = False
        
        try:
            logger.info("🚀 开始初始化功能补充器...")
            
            self.env_awareness = EnvironmentAwareness()
            self.code_generator = CodeGenerator()
            self.capabilities: Dict[str, Capability] = {}
            
            # 使用绝对路径创建工作目录
            self.workspace = Path(__file__).parent / "workspace"
            self.workspace.mkdir(parents=True, exist_ok=True)
            
            # 创建能力代码存储目录
            self.capabilities_dir = self.workspace / "capabilities"
            self.capabilities_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建持久化存储目录
            self.persistence_dir = self.workspace / "persistence"
            self.persistence_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建日志目录
            self.log_dir = self.workspace / "logs"
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # 线程池用于异步操作
            self.executor = ThreadPoolExecutor(max_workers=4)
            
            # 加载持久化的能力
            self._load_capabilities()
            
            self._initialized = True
            logger.info("✅ 功能补充器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 功能补充器初始化失败: {str(e)}")
            raise
    
    async def enhance_capability(
        self,
        requirement: str,
        target: str,
        capability_name: Optional[str] = None,
        timeout: int = 60,
        enable_cache: bool = True
    ) -> Dict[str, Any]:
        """
        增强功能(优化版)
        
        根据需求动态生成并注册新的能力。
        
        Args:
            requirement: 功能需求描述
            target: 扫描目标
            capability_name: 能力名称(可选)
            timeout: 执行超时时间(秒)
            enable_cache: 是否启用缓存
            
        Returns:
            Dict: 增强结果
        """
        try:
            logger.info(f"🔧 开始增强功能: {requirement}")
            
            # 生成能力名称
            if not capability_name:
                capability_name = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 检查能力是否已存在
            if capability_name in self.capabilities:
                logger.warning(f"能力已存在: {capability_name}")
                return {
                    "status": "failed",
                    "error": f"能力已存在: {capability_name}"
                }
            
            # 生成代码
            code_response = await self.code_generator.generate_code(
                scan_type="custom",
                target=target,
                requirements=requirement,
                language="python"
            )
            
            # 验证代码(增强版)
            validation = self._validate_code_enhanced(
                code_response.code,
                code_response.language
            )
            
            if not validation["valid"]:
                logger.warning(f"代码验证失败: {validation['issues']}")
                raise CodeValidationError(f"代码验证失败: {validation['issues']}")
            
            # 检查并安装依赖(异步)
            dependencies = code_response.dependencies
            if dependencies:
                logger.info(f"📦 检测到依赖: {dependencies}")
                install_result = await self._install_dependencies_async(dependencies)
                
                if install_result["status"] != "success":
                    logger.warning(f"依赖安装失败: {install_result['error']}")
                    raise DependencyInstallError(f"依赖安装失败: {install_result['error']}")
                
                logger.info(f"✅ 依赖安装完成: {install_result['installed_packages']}")
            
            # 保存代码
            code_file = self.capabilities_dir / f"{capability_name}.py"
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(code_response.code)
            
            # 创建能力
            capability = await self._create_capability_from_code(
                capability_name,
                requirement,
                code_file,
                timeout=timeout,
                enable_cache=enable_cache
            )
            
            # 验证能力
            if not capability.execute_func:
                logger.warning(f"能力未定义执行函数: {capability_name}")
                raise CodeValidationError(f"能力未定义执行函数: {capability_name}")
            
            # 注册能力
            with self._lock:
                self.capabilities[capability_name] = capability
            
            # 持久化能力
            self._save_capability(capability)
            
            logger.info(f"✅ 功能增强完成: {capability_name}")
            
            return {
                "status": "success",
                "capability": capability.to_dict(),
                "code_file": str(code_file),
                "validation": validation
            }
            
        except CodeValidationError as e:
            logger.error(f"代码验证失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "error_type": "validation_error"
            }
        except DependencyInstallError as e:
            logger.error(f"依赖安装失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "error_type": "dependency_error",
                "dependencies": dependencies if 'dependencies' in locals() else []
            }
        except Exception as e:
            logger.error(f"功能增强失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "error_type": "unknown_error"
            }
    
    def _validate_code_enhanced(
        self,
        code: str,
        language: str
    ) -> Dict[str, Any]:
        """
        增强的代码验证
        
        Args:
            code: 代码内容
            language: 代码语言
            
        Returns:
            Dict: 验证结果
        """
        issues = []
        
        # 基础验证
        basic_validation = self.code_generator.validate_code(code, language)
        if not basic_validation["valid"]:
            issues.extend(basic_validation["issues"])
        
        # 检查是否包含execute函数
        if "def execute(" not in code and "async def execute(" not in code:
            issues.append("代码必须包含execute函数")
        
        # 检查危险操作
        dangerous_patterns = [
            "os.system",
            "subprocess.call",
            "eval(",
            "exec(",
            "__import__",
            "open(",
            "file("
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                issues.append(f"代码包含潜在危险操作: {pattern}")
        
        # 检查导入限制
        restricted_imports = [
            "import os",
            "import subprocess",
            "import sys"
        ]
        
        for imp in restricted_imports:
            if imp in code:
                issues.append(f"代码包含受限导入: {imp}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    async def _install_dependencies_async(
        self,
        dependencies: List[str],
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        异步安装依赖包
        
        Args:
            dependencies: 依赖包列表
            timeout: 超时时间(秒)
            
        Returns:
            Dict: 安装结果
        """
        try:
            logger.info(f"📦 开始安装依赖: {dependencies}")
            
            # 构建安装命令
            cmd = [sys.executable, "-m", "pip", "install"]
            cmd.extend(dependencies)
            
            # 在线程池中执行安装
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            )
            
            # 解析输出
            output = result.stdout
            error = result.stderr
            
            # 检查是否成功
            success = result.returncode == 0
            
            # 提取安装的包信息
            installed_packages = []
            if success:
                for line in output.split('\n'):
                    if 'Successfully installed' in line:
                        packages_str = line.replace('Successfully installed', '').strip()
                        installed_packages = packages_str.split()
            
            logger.info(f"✅ 依赖安装完成: {len(installed_packages)} 个包")
            
            return {
                "status": "success" if success else "failed",
                "dependencies": dependencies,
                "installed_packages": installed_packages,
                "output": output,
                "error": error,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 依赖安装超时")
            return {
                "status": "timeout",
                "dependencies": dependencies,
                "installed_packages": [],
                "error": "安装超时",
                "return_code": -1
            }
        except Exception as e:
            logger.error(f"❌ 依赖安装失败: {str(e)}")
            return {
                "status": "failed",
                "dependencies": dependencies,
                "installed_packages": [],
                "error": str(e),
                "return_code": -1
            }
    
    async def _create_capability_from_code(
        self,
        name: str,
        description: str,
        code_file: Path,
        timeout: int = 60,
        enable_cache: bool = True
    ) -> Capability:
        """
        从代码文件创建能力(优化版)
        
        Args:
            name: 能力名称
            description: 描述
            code_file: 代码文件路径
            timeout: 执行超时时间
            enable_cache: 是否启用缓存
            
        Returns:
            Capability: 能力对象
        """
        spec = importlib.util.spec_from_file_location(name, code_file)
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
            
            # 查找execute函数
            execute_func = None
            if hasattr(module, "execute"):
                execute_func = module.execute
            elif hasattr(module, "run"):
                execute_func = module.run
                logger.warning(f"能力使用run函数而非execute函数: {name}")
            
            # 提取版本信息
            version = "1.0.0"
            if hasattr(module, "__version__"):
                version = module.__version__
            
            # 提取依赖信息
            dependencies = []
            if hasattr(module, "__dependencies__"):
                dependencies = module.__dependencies__
            
            return Capability(
                name=name,
                description=description,
                version=version,
                dependencies=dependencies,
                execute_func=execute_func,
                timeout=timeout,
                enable_cache=enable_cache
            )
            
        except Exception as e:
            logger.error(f"加载能力失败 {name}: {str(e)}")
            return Capability(
                name=name,
                description=description,
                version="1.0.0",
                execute_func=None,
                timeout=timeout,
                enable_cache=enable_cache
            )
    
    def _save_capability(self, capability: Capability):
        """
        持久化能力信息
        
        Args:
            capability: 能力对象
        """
        try:
            capability_file = self.persistence_dir / f"{capability.name}.json"
            with open(capability_file, "w", encoding="utf-8") as f:
                json.dump(capability.to_dict(), f, indent=2, ensure_ascii=False)
            logger.debug(f"保存能力信息: {capability.name}")
        except Exception as e:
            logger.error(f"保存能力信息失败 {capability.name}: {str(e)}")
    
    def _load_capabilities(self):
        """
        加载持久化的能力
        """
        try:
            for capability_file in self.persistence_dir.glob("*.json"):
                try:
                    with open(capability_file, "r", encoding="utf-8") as f:
                        capability_data = json.load(f)
                    
                    capability_name = capability_data.get("name")
                    if capability_name and capability_name not in self.capabilities:
                        # 重新加载代码文件
                        code_file = self.capabilities_dir / f"{capability_name}.py"
                        if code_file.exists():
                            capability = asyncio.run(self._create_capability_from_code(
                                capability_name,
                                capability_data.get("description", ""),
                                code_file,
                                timeout=capability_data.get("timeout", 60),
                                enable_cache=True
                            ))
                            self.capabilities[capability_name] = capability
                            logger.info(f"加载持久化能力: {capability_name}")
                except Exception as e:
                    logger.error(f"加载能力失败 {capability_file}: {str(e)}")
        except Exception as e:
            logger.error(f"加载持久化能力失败: {str(e)}")
    
    def register_capability(
        self,
        name: str,
        description: str,
        execute_func: Callable,
        version: str = "1.0.0",
        dependencies: List[str] = None,
        timeout: int = 60,
        enable_cache: bool = True
    ):
        """
        注册能力(优化版)
        
        Args:
            name: 能力名称
            description: 描述
            execute_func: 执行函数
            version: 版本
            dependencies: 依赖列表
            timeout: 执行超时时间
            enable_cache: 是否启用缓存
        """
        with self._lock:
            if name in self.capabilities:
                logger.warning(f"能力已存在,将被覆盖: {name}")
            
            capability = Capability(
                name=name,
                description=description,
                version=version,
                dependencies=dependencies,
                execute_func=execute_func,
                timeout=timeout,
                enable_cache=enable_cache
            )
            
            self.capabilities[name] = capability
            self._save_capability(capability)
            logger.info(f"✅ 注册能力: {name}")
    
    def get_capability(self, name: str) -> Optional[Capability]:
        """
        获取能力
        
        Args:
            name: 能力名称
            
        Returns:
            Optional[Capability]: 能力对象
        """
        with self._lock:
            return self.capabilities.get(name)
    
    def list_capabilities(self) -> List[Dict[str, Any]]:
        """
        列出所有能力
        
        Returns:
            List[Dict]: 能力列表
        """
        with self._lock:
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
        执行能力(优化版)
        
        Args:
            name: 能力名称
            target: 扫描目标
            **kwargs: 额外参数
            
        Returns:
            Dict: 执行结果
        """
        capability = self.get_capability(name)
        if not capability:
            raise CapabilityNotFoundError(f"能力不存在: {name}")
        
        return await capability.execute(target, **kwargs)
    
    def remove_capability(self, name: str) -> bool:
        """
        移除能力(优化版)
        
        Args:
            name: 能力名称
            
        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            if name in self.capabilities:
                del self.capabilities[name]
                
                # 删除代码文件
                code_file = self.capabilities_dir / f"{name}.py"
                if code_file.exists():
                    code_file.unlink()
                
                # 删除持久化文件
                persistence_file = self.persistence_dir / f"{name}.json"
                if persistence_file.exists():
                    persistence_file.unlink()
                
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
    
    def get_capability_statistics(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取能力统计信息
        
        Args:
            name: 能力名称
            
        Returns:
            Optional[Dict]: 统计信息
        """
        capability = self.get_capability(name)
        if capability:
            return capability.get_statistics()
        return None
    
    def clear_capability_cache(self, name: str):
        """
        清空能力缓存
        
        Args:
            name: 能力名称
        """
        capability = self.get_capability(name)
        if capability:
            capability.clear_cache()
            logger.info(f"清空能力缓存: {name}")
    
    def disable_capability(self, name: str):
        """
        禁用能力
        
        Args:
            name: 能力名称
        """
        capability = self.get_capability(name)
        if capability:
            capability.disable()
            logger.info(f"禁用能力: {name}")
    
    def enable_capability(self, name: str):
        """
        启用能力
        
        Args:
            name: 能力名称
        """
        capability = self.get_capability(name)
        if capability:
            capability.enable()
            logger.info(f"启用能力: {name}")
    
    def cleanup(self):
        """
        清理资源
        """
        try:
            # 关闭线程池
            self.executor.shutdown(wait=True)
            logger.info("✅ 资源清理完成")
        except Exception as e:
            logger.error(f"资源清理失败: {str(e)}")
    
    def __del__(self):
        """析构函数"""
        if hasattr(self, 'executor'):
            self.cleanup()

"""
工具注册表

管理所有扫描工具的注册和调用,提供统一的工具接口。
"""
import asyncio
import logging
from typing import Dict, Callable, Any, List, Optional

from .wrappers import AsyncToolWrapper

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册表类
    
    负责注册、管理和调用所有扫描工具。
    支持装饰器注册和直接注册两种方式。
    
    Attributes:
        tools: 工具字典,键为工具名称,值为工具对象
        tool_metadata: 工具元数据字典
    """
    
    def __init__(self):
        self.tools: Dict[str, AsyncToolWrapper] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        logger.info("工具注册表初始化完成")
    
    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        category: str = "general",
        timeout: int = 60,
        priority: int = 5
    ):
        """
        注册工具
        
        Args:
            name: 工具名称
            func: 工具函数
            description: 工具描述
            category: 工具分类(plugin/poc/general)
            timeout: 超时时间(秒)
            priority: 工具优先级(1-10,数字越大优先级越高)
        """
        if name in self.tools:
            logger.warning(f"工具 {name} 已存在,将被覆盖")
        
        # 检查是否已经是AsyncToolWrapper，避免双重包装
        if isinstance(func, AsyncToolWrapper):
            wrapper = func
        else:
            wrapper = AsyncToolWrapper(func, timeout=timeout)
        
        self.tools[name] = wrapper
        self.tool_metadata[name] = {
            "description": description,
            "category": category,
            "timeout": timeout,
            "priority": priority
        }
        logger.info(f"✅ 注册工具: {name} (分类: {category}, 优先级: {priority})")
    
    async def call_tool(
        self,
        tool_name: str,
        target: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            target: 扫描目标
            **kwargs: 工具参数
            
        Returns:
            Dict: 工具执行结果,包含status、data、error等字段
            
        Raises:
            ValueError: 工具不存在
        """
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
        
        tool = self.tools[tool_name]
        logger.info(f"🔧 调用工具: {tool_name} -> {target}")
        
        try:
            result = await tool.execute(target, **kwargs)
            logger.info(f"✅ 工具 {tool_name} 执行成功")
            return {
                "status": "success",
                "data": result,
                "tool_name": tool_name
            }
        except asyncio.TimeoutError:
            logger.error(f"⏱️ 工具 {tool_name} 执行超时")
            return {
                "status": "timeout",
                "error": f"工具执行超时({tool.timeout}秒)",
                "tool_name": tool_name
            }
        except Exception as e:
            logger.error(f"❌ 工具 {tool_name} 执行失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "tool_name": tool_name
            }
    
    def get_tool(self, tool_name: str) -> Optional[AsyncToolWrapper]:
        """
        获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[AsyncToolWrapper]: 工具对象,不存在则返回None
        """
        return self.tools.get(tool_name)
    
    def list_tools(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出所有工具
        
        Args:
            category: 按分类过滤
            
        Returns:
            List[Dict]: 工具列表,包含名称和元数据
        """
        tools_list = []
        for name, wrapper in self.tools.items():
            metadata = self.tool_metadata.get(name, {})
            if category is None or metadata.get("category") == category:
                tools_list.append({
                    "name": name,
                    **metadata
                })
        
        return sorted(tools_list, key=lambda x: x.get("priority", 0), reverse=True)
    
    def get_tools_by_category(self, category: str) -> List[str]:
        """
        按分类获取工具名称列表
        
        Args:
            category: 工具分类
            
        Returns:
            List[str]: 工具名称列表
        """
        return [
            name for name, metadata in self.tool_metadata.items()
            if metadata.get("category") == category
        ]
    
    def has_tool(self, tool_name: str) -> bool:
        """
        检查工具是否存在
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 工具是否存在
        """
        return tool_name in self.tools


def register_tool(
    name: str,
    description: str = "",
    category: str = "general",
    timeout: int = 60,
    priority: int = 5
):
    """
    工具注册装饰器
    
    用于简化工具注册,使用装饰器语法:
    
    Examples:
        >>> @register_tool(
        ...     name="my_tool",
        ...     description="我的工具",
        ...     category="plugin",
        ...     timeout=30
        ... )
        ... async def my_tool_func(target: str):
        ...     return {"result": "success"}
    """
    def decorator(func: Callable):
        registry.register(
            name=name,
            func=func,
            description=description,
            category=category,
            timeout=timeout,
            priority=priority
        )
        return func
    return decorator


# 全局工具注册表实例
registry = ToolRegistry()
"""
全局工具注册表

在应用中导入此实例来注册和调用工具:
    from ai_agents.tools import registry, register_tool
    
    @register_tool(name="my_tool", description="我的工具")
    async def my_tool(target: str):
        return {"result": "success"}
    
    result = await registry.call_tool("my_tool", "https://www.baidu.com")
"""

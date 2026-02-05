"""
工具注册表

管理所有扫描工具的注册和调用,提供统一的工具接口。
"""
import asyncio
import logging
from typing import Dict, Callable, Any, List, Optional

logger = logging.getLogger(__name__)


class AsyncToolWrapper:
    """
    异步工具包装器

    将同步函数封装为异步调用,并提供超时控制。

    Attributes:
        func: 原始函数
        timeout: 超时时间(秒)
    """

    def __init__(self, func: Callable, timeout: int = 60):
        """
        初始化工具包装器

        Args:
            func: 要封装的函数
            timeout: 超时时间(秒)
        """
        self.func = func
        self.timeout = timeout
        self.is_async = asyncio.iscoroutinefunction(func)
        func_name = getattr(func, '__name__', str(func))
        logger.debug(f"创建工具包装器: {func_name}, 异步: {self.is_async}, 超时: {timeout}s")

    async def execute(self, target: str, **kwargs) -> Any:
        """
        执行工具

        Args:
            target: 扫描目标
            **kwargs: 工具参数

        Returns:
            Any: 工具执行结果

        Raises:
            asyncio.TimeoutError: 执行超时
            Exception: 执行失败
        """
        func_name = getattr(self.func, '__name__', str(self.func))
        try:
            if self.is_async:
                result = await asyncio.wait_for(
                    self.func(target, **kwargs),
                    timeout=self.timeout
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self.func, target, **kwargs),
                    timeout=self.timeout
                )
            return result
        except asyncio.TimeoutError:
            logger.error(f"工具 {func_name} 执行超时({self.timeout}秒)")
            raise
        except Exception as e:
            logger.error(f"工具 {func_name} 执行失败: {str(e)}")
            raise

    def get_timeout(self) -> int:
        """
        获取超时时间

        Returns:
            int: 超时时间(秒)
        """
        return self.timeout

    def get_func_name(self) -> str:
        """
        获取函数名称

        Returns:
            str: 函数名称
        """
        return self.func.__name__


def wrap_async(
    func: Callable,
    timeout: int = 60
) -> AsyncToolWrapper:
    """
    工具异步封装函数

    便捷函数,用于快速创建工具包装器。

    Args:
        func: 要封装的函数
        timeout: 超时时间(秒)

    Returns:
        AsyncToolWrapper: 工具包装器实例

    Examples:
        >>> from plugins.baseinfo.baseinfo import getbaseinfo
        >>> wrapper = wrap_async(getbaseinfo, timeout=10)
        >>> result = await wrapper.execute("https://www.baidu.com")
    """
    return AsyncToolWrapper(func, timeout=timeout)


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
                "error": f"工具执行超时({tool.get_timeout()}秒)",
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

    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """
        列出所有工具

        Args:
            category: 工具分类过滤,不指定则返回所有

        Returns:
            List[str]: 工具名称列表
        """
        if category:
            return [
                name for name, meta in self.tool_metadata.items()
                if meta.get("category") == category
            ]
        return list(self.tools.keys())

    def get_tool_metadata(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具元数据

        Args:
            tool_name: 工具名称

        Returns:
            Optional[Dict]: 工具元数据,不存在则返回None
        """
        return self.tool_metadata.get(tool_name)

    def unregister(self, tool_name: str) -> bool:
        """
        注销工具

        Args:
            tool_name: 工具名称

        Returns:
            bool: 是否成功注销
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            del self.tool_metadata[tool_name]
            logger.info(f"🗑️ 注销工具: {tool_name}")
            return True
        return False

    def clear(self):
        """清空所有工具"""
        self.tools.clear()
        self.tool_metadata.clear()
        logger.info("🗑️ 清空工具注册表")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        total_tools = len(self.tools)
        by_category = {}

        for meta in self.tool_metadata.values():
            category = meta.get("category", "unknown")
            by_category[category] = by_category.get(category, 0) + 1

        return {
            "total_tools": total_tools,
            "by_category": by_category
        }


def register_tool(
    name: str,
    description: str = "",
    category: str = "general",
    timeout: int = 60,
    priority: int = 5
):
    """
    工具注册装饰器

    Args:
        name: 工具名称
        description: 工具描述
        category: 工具分类(plugin/poc/general)
        timeout: 超时时间(秒)
        priority: 工具优先级(1-10,数字越大优先级越高)

    Returns:
        Callable: 装饰器函数

    Examples:
        >>> @register_tool("my_tool", description="我的工具", category="general")
        >>> async def my_scan(target: str):
        >>>     return {"result": "success"}
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

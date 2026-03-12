"""
工具适配器

适配现有插件和POC,提供统一的调用接口。
包含统一返回格式、超时控制、异常捕获、进度回调功能。
"""
import asyncio
import functools
import logging
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union

from .wrappers import wrap_async

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """插件执行状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class PluginResult:
    """
    插件执行结果数据类
    
    统一所有插件的返回格式,包含执行状态、数据、错误信息、执行时间和元数据。
    
    Attributes:
        status: 执行状态 (success/failed/timeout)
        data: 返回的数据
        error: 错误信息,成功时为None
        execution_time: 执行时间(秒)
        metadata: 额外的元数据信息
    """
    status: str
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def success(cls, data: Any = None, execution_time: float = 0.0, **metadata) -> 'PluginResult':
        """创建成功结果"""
        return cls(
            status=PluginStatus.SUCCESS.value,
            data=data,
            execution_time=execution_time,
            metadata=metadata
        )
    
    @classmethod
    def failed(cls, error: str, execution_time: float = 0.0, **metadata) -> 'PluginResult':
        """创建失败结果"""
        return cls(
            status=PluginStatus.FAILED.value,
            error=error,
            execution_time=execution_time,
            metadata=metadata
        )
    
    @classmethod
    def timeout(cls, timeout_seconds: float, execution_time: float = 0.0, **metadata) -> 'PluginResult':
        """创建超时结果"""
        return cls(
            status=PluginStatus.TIMEOUT.value,
            error=f"执行超时,超过{timeout_seconds}秒",
            execution_time=execution_time,
            metadata=metadata
        )


class ProgressReporter:
    """
    进度报告器
    
    用于在插件执行过程中报告进度,支持回调函数和日志记录。
    
    Attributes:
        plugin_name: 插件名称
        target: 目标地址
        callback: 进度回调函数
    """
    
    def __init__(
        self,
        plugin_name: str,
        target: str,
        callback: Optional[Callable[[str, str, int, Dict], None]] = None
    ):
        self.plugin_name = plugin_name
        self.target = target
        self.callback = callback
        self.start_time = time.time()
    
    def report(
        self,
        stage: str,
        progress: int,
        message: str = "",
        extra_data: Optional[Dict] = None
    ) -> None:
        """
        报告执行进度
        
        Args:
            stage: 当前阶段名称
            progress: 进度百分比 (0-100)
            message: 进度消息
            extra_data: 额外数据
        """
        elapsed = time.time() - self.start_time
        progress_info = {
            "plugin": self.plugin_name,
            "target": self.target,
            "stage": stage,
            "progress": progress,
            "message": message,
            "elapsed_time": elapsed,
            **(extra_data or {})
        }
        
        logger.info(f"[{self.plugin_name}] {self.target} - {stage}: {progress}% - {message}")
        
        if self.callback:
            try:
                self.callback(
                    self.plugin_name,
                    stage,
                    progress,
                    progress_info
                )
            except Exception as e:
                logger.warning(f"进度回调执行失败: {str(e)}")


def with_timeout_and_error_handling(
    default_timeout: float = 60.0,
    plugin_name: str = "unknown"
):
    """
    超时控制和异常捕获装饰器
    
    为插件适配器添加统一的超时控制和异常处理。
    
    Args:
        default_timeout: 默认超时时间(秒)
        plugin_name: 插件名称,用于日志记录
    
    Returns:
        装饰器函数
    
    Example:
        @with_timeout_and_error_handling(default_timeout=30, plugin_name="portscan")
        async def scan_port(target: str, timeout: float = None, progress_callback=None):
            # 插件实现
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(
            *args,
            timeout: Optional[float] = None,
            progress_callback: Optional[Callable] = None,
            **kwargs
        ) -> PluginResult:
            actual_timeout = timeout if timeout is not None else default_timeout
            start_time = time.time()
            
            try:
                result = await asyncio.wait_for(
                    func(*args, timeout=actual_timeout, progress_callback=progress_callback, **kwargs),
                    timeout=actual_timeout
                )
                execution_time = time.time() - start_time
                
                if isinstance(result, PluginResult):
                    result.execution_time = execution_time
                    return result
                
                return PluginResult.success(
                    data=result,
                    execution_time=execution_time,
                    plugin=plugin_name
                )
                
            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                logger.error(f"[{plugin_name}] 执行超时,耗时{execution_time:.2f}秒")
                return PluginResult.timeout(
                    timeout_seconds=actual_timeout,
                    execution_time=execution_time,
                    plugin=plugin_name
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"[{plugin_name}] 执行异常: {error_msg}", exc_info=True)
                return PluginResult.failed(
                    error=error_msg,
                    execution_time=execution_time,
                    plugin=plugin_name
                )
        
        @functools.wraps(func)
        def sync_wrapper(
            *args,
            timeout: Optional[float] = None,
            progress_callback: Optional[Callable] = None,
            **kwargs
        ) -> PluginResult:
            actual_timeout = timeout if timeout is not None else default_timeout
            start_time = time.time()
            
            try:
                if asyncio.iscoroutinefunction(func):
                    loop = asyncio.get_event_loop()
                    result = loop.run_until_complete(
                        asyncio.wait_for(
                            func(*args, timeout=actual_timeout, progress_callback=progress_callback, **kwargs),
                            timeout=actual_timeout
                        )
                    )
                else:
                    result = func(*args, timeout=actual_timeout, progress_callback=progress_callback, **kwargs)
                
                execution_time = time.time() - start_time
                
                if isinstance(result, PluginResult):
                    result.execution_time = execution_time
                    return result
                
                return PluginResult.success(
                    data=result,
                    execution_time=execution_time,
                    plugin=plugin_name
                )
                
            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                logger.error(f"[{plugin_name}] 执行超时,耗时{execution_time:.2f}秒")
                return PluginResult.timeout(
                    timeout_seconds=actual_timeout,
                    execution_time=execution_time,
                    plugin=plugin_name
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"[{plugin_name}] 执行异常: {error_msg}", exc_info=True)
                return PluginResult.failed(
                    error=error_msg,
                    execution_time=execution_time,
                    plugin=plugin_name
                )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def create_progress_callback(
    plugin_name: str,
    target: str,
    callback: Optional[Callable] = None
) -> Optional[ProgressReporter]:
    """
    创建进度报告器
    
    Args:
        plugin_name: 插件名称
        target: 目标地址
        callback: 用户提供的回调函数
    
    Returns:
        ProgressReporter实例或None
    """
    if callback is None:
        return None
    return ProgressReporter(plugin_name, target, callback)


class PluginAdapter:
    """
    插件适配器
    
    适配现有的扫描插件,提供统一的调用接口。
    所有适配器支持超时控制、异常捕获和进度回调。
    """
    
    PLUGIN_NAME = "base_plugin"
    DEFAULT_TIMEOUT = 60.0
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=30.0, plugin_name="baseinfo")
    async def adapt_baseinfo(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        适配基础信息收集插件
        
        Args:
            target: 目标地址
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("baseinfo", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "开始基础信息收集")
        
        from backend.plugins.baseinfo.baseinfo import getbaseinfo
        
        if reporter:
            reporter.report("执行中", 50, "正在收集基础信息")
        
        result = await asyncio.to_thread(getbaseinfo, target)
        
        if reporter:
            reporter.report("完成", 100, "基础信息收集完成")
        
        return PluginResult.success(data=result, plugin="baseinfo", target=target)
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=120.0, plugin_name="portscan")
    async def adapt_portscan(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None,
        ports: Optional[str] = None
    ) -> PluginResult:
        """
        适配端口扫描插件
        
        Args:
            target: 目标地址
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
            ports: 指定扫描的端口范围
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("portscan", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "初始化端口扫描器")
        
        from backend.plugins.portscan.portscan import ScanPort
        
        def run_scan():
            scanner = ScanPort(target)
            if ports:
                scanner.ports = ports
            success = scanner.run_scan()
            if success:
                return scanner.get_results()
            return []
        
        if reporter:
            reporter.report("扫描中", 30, "开始端口扫描")
        
        open_ports = await asyncio.to_thread(run_scan)
        
        if reporter:
            reporter.report("完成", 100, f"扫描完成,发现{len(open_ports)}个开放端口")
        
        return PluginResult.success(
            data={"open_ports": open_ports, "target": target},
            plugin="portscan",
            target=target,
            open_port_count=len(open_ports)
        )
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=30.0, plugin_name="waf_detect")
    async def adapt_waf_detect(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        适配WAF检测插件
        
        Args:
            target: 目标地址
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("waf_detect", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "开始WAF检测")
        
        from backend.plugins.waf.waf import get_waf
        
        if reporter:
            reporter.report("检测中", 50, "正在检测WAF")
        
        result = await asyncio.to_thread(get_waf, target)
        
        if reporter:
            reporter.report("完成", 100, "WAF检测完成")
        
        return PluginResult.success(
            data={"waf_info": result, "target": target},
            plugin="waf_detect",
            target=target
        )
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=30.0, plugin_name="cdn_detect")
    async def adapt_cdn_detect(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        适配CDN检测插件
        
        Args:
            target: 目标地址
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("cdn_detect", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "开始CDN检测")
        
        from backend.plugins.cdnexist.cdnexist import iscdn
        
        if reporter:
            reporter.report("检测中", 50, "正在检测CDN")
        
        result = await asyncio.to_thread(iscdn, target)
        
        if reporter:
            reporter.report("完成", 100, "CDN检测完成")
        
        return PluginResult.success(
            data={"has_cdn": bool(result), "cdn_info": str(result) if result else None, "target": target},
            plugin="cdn_detect",
            target=target
        )
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=60.0, plugin_name="cms_identify")
    async def adapt_cms_identify(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        适配CMS识别插件
        
        Args:
            target: 目标地址
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("cms_identify", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "开始CMS识别")
        
        from backend.plugins.whatcms.whatcms import getwhatcms
        
        if reporter:
            reporter.report("识别中", 50, "正在识别CMS类型")
        
        result = await asyncio.to_thread(getwhatcms, target)
        
        if reporter:
            reporter.report("完成", 100, "CMS识别完成")
        
        return PluginResult.success(
            data={"cms_info": result, "target": target},
            plugin="cms_identify",
            target=target
        )
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=60.0, plugin_name="infoleak_scan")
    async def adapt_infoleak_scan(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        适配信息泄露扫描插件
        
        Args:
            target: 目标地址
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("infoleak_scan", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "开始信息泄露扫描")
        
        from backend.plugins.infoleak.infoleak import get_infoleak
        
        if reporter:
            reporter.report("扫描中", 50, "正在扫描信息泄露")
        
        result = await asyncio.to_thread(get_infoleak, target)
        
        if reporter:
            reporter.report("完成", 100, "信息泄露扫描完成")
        
        return PluginResult.success(
            data={"leak_info": result, "target": target},
            plugin="infoleak_scan",
            target=target
        )
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=120.0, plugin_name="subdomain_scan")
    async def adapt_subdomain_scan(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        适配子域名扫描插件
        
        Args:
            target: 目标地址
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("subdomain_scan", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "开始子域名扫描")
        
        from backend.plugins.subdomain.subdomain import get_subdomain
        
        if reporter:
            reporter.report("扫描中", 50, "正在扫描子域名")
        
        result = await asyncio.to_thread(get_subdomain, target)
        
        subdomain_count = len(result) if isinstance(result, (list, dict)) else 0
        if reporter:
            reporter.report("完成", 100, f"子域名扫描完成,发现{subdomain_count}个子域名")
        
        return PluginResult.success(
            data={"subdomains": result, "target": target},
            plugin="subdomain_scan",
            target=target,
            subdomain_count=subdomain_count
        )
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=60.0, plugin_name="webside_scan")
    async def adapt_webside_scan(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        适配站点信息扫描插件
        
        Args:
            target: 目标地址
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("webside_scan", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "开始站点信息扫描")
        
        from backend.plugins.webside.webside import get_side_info
        
        if reporter:
            reporter.report("扫描中", 50, "正在获取站点信息")
        
        result = await asyncio.to_thread(get_side_info, target)
        
        if reporter:
            reporter.report("完成", 100, "站点信息扫描完成")
        
        return PluginResult.success(
            data={"side_info": result, "target": target},
            plugin="webside_scan",
            target=target
        )
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=30.0, plugin_name="webweight_scan")
    async def adapt_webweight_scan(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        适配网站权重扫描插件
        
        Args:
            target: 目标地址
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("webweight_scan", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "开始网站权重查询")
        
        from backend.plugins.webweight.webweight import get_web_weight
        
        if reporter:
            reporter.report("查询中", 50, "正在查询网站权重")
        
        result = await asyncio.to_thread(get_web_weight, target)
        
        if reporter:
            reporter.report("完成", 100, "网站权重查询完成")
        
        return PluginResult.success(
            data={"weight_info": result, "target": target},
            plugin="webweight_scan",
            target=target
        )
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=30.0, plugin_name="iplocating")
    async def adapt_iplocating(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        适配IP定位插件
        
        Args:
            target: 目标地址
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("iplocating", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "开始IP定位")
        
        from backend.plugins.iplocating.iplocating import get_locating
        
        if reporter:
            reporter.report("定位中", 50, "正在定位IP地址")
        
        result = await asyncio.to_thread(get_locating, target)
        
        if reporter:
            reporter.report("完成", 100, "IP定位完成")
        
        return PluginResult.success(
            data={"location_info": result, "target": target},
            plugin="iplocating",
            target=target
        )

    @staticmethod
    @with_timeout_and_error_handling(default_timeout=30.0, plugin_name="loginfo")
    async def adapt_loginfo(
        target: str,
        log_name: str = "default",
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        适配日志处理插件
        
        Args:
            target: 目标地址(用于日志标识)
            log_name: 日志名称
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("loginfo", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "初始化日志处理器")
        
        from backend.plugins.loginfo.loginfo import LogHandler
        
        if reporter:
            reporter.report("配置中", 50, "正在配置日志处理器")
        
        return PluginResult.success(
            data={"log_name": log_name, "target": target, "status": "ready"},
            plugin="loginfo",
            target=target
        )

    @staticmethod
    @with_timeout_and_error_handling(default_timeout=30.0, plugin_name="randheader")
    async def adapt_randheader(
        target: str,
        conn_type: str = "keep-alive",
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        适配随机请求头生成插件
        
        Args:
            target: 目标地址
            conn_type: 连接类型(keep-alive/close)
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("randheader", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "开始生成随机请求头")
        
        from backend.plugins.randheader.randheader import get_random_headers
        
        if reporter:
            reporter.report("生成中", 50, "正在生成随机请求头")
        
        result = await asyncio.to_thread(get_random_headers, conn_type)
        
        if reporter:
            reporter.report("完成", 100, "随机请求头生成完成")
        
        return PluginResult.success(
            data={"headers": result, "target": target},
            plugin="randheader",
            target=target
        )

    @staticmethod
    @with_timeout_and_error_handling(default_timeout=300.0, plugin_name="awvs")
    async def adapt_awvs(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None,
        scan_type: str = "full_scan"
    ) -> PluginResult:
        """
        适配AWVS扫描
        
        Args:
            target: 目标地址
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
            scan_type: 扫描类型 (full_scan, high_risk_vulnerabilities等)
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("awvs", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "检查AWVS配置")
        
        from backend.config import settings
        from backend.AVWS.API.Target import Target
        from backend.AVWS.API.Scan import Scan
        
        api_url = settings.AWVS_API_URL
        api_key = settings.AWVS_API_KEY
        
        if not api_url or not api_key:
            return PluginResult.failed(
                error="AWVS配置缺失(API_URL或API_KEY)",
                plugin="awvs",
                target=target
            )
        
        if reporter:
            reporter.report("添加目标", 30, "正在添加扫描目标")
        
        def run_awvs():
            target_api = Target(api_url, api_key)
            scan_api = Scan(api_url, api_key)
            
            target_id = target_api.add(target)
            if not target_id:
                raise Exception("添加目标失败")
            
            return target_api, scan_api, target_id
        
        target_api, scan_api, target_id = await asyncio.to_thread(run_awvs)
        
        if reporter:
            reporter.report("启动扫描", 60, "正在启动AWVS扫描")
        
        scan_id = await asyncio.to_thread(scan_api.add, target_id, scan_type)
        if not scan_id:
            return PluginResult.failed(
                error="启动扫描失败",
                plugin="awvs",
                target=target,
                target_id=target_id
            )
        
        if reporter:
            reporter.report("完成", 100, "AWVS扫描任务已启动")
        
        return PluginResult.success(
            data={
                "message": "AWVS扫描任务已启动",
                "scan_id": scan_id,
                "target_id": target_id,
                "target": target
            },
            plugin="awvs",
            target=target,
            scan_type=scan_type
        )
    
    @staticmethod
    def get_adapters() -> Dict[str, Callable]:
        """
        获取所有插件适配器
        
        Returns:
            Dict[str, Callable]: 适配器名称到函数的映射
        """
        return {
            "baseinfo": PluginAdapter.adapt_baseinfo,
            "portscan": PluginAdapter.adapt_portscan,
            "waf_detect": PluginAdapter.adapt_waf_detect,
            "cdn_detect": PluginAdapter.adapt_cdn_detect,
            "cms_identify": PluginAdapter.adapt_cms_identify,
            "infoleak_scan": PluginAdapter.adapt_infoleak_scan,
            "subdomain_scan": PluginAdapter.adapt_subdomain_scan,
            "webside_scan": PluginAdapter.adapt_webside_scan,
            "webweight_scan": PluginAdapter.adapt_webweight_scan,
            "iplocating": PluginAdapter.adapt_iplocating,
            "loginfo": PluginAdapter.adapt_loginfo,
            "randheader": PluginAdapter.adapt_randheader,
            "awvs": PluginAdapter.adapt_awvs,
        }


class POCAdapter:
    """
    POC适配器
    
    适配现有的POC脚本,提供统一的调用接口。
    支持超时控制、异常捕获和进度回调。
    """
    
    DEFAULT_POC_TIMEOUT = 30.0
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=30.0, plugin_name="poc")
    async def adapt_poc(
        target: str,
        poc_name: str,
        poc_module: Any,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> PluginResult:
        """
        执行单个POC检测
        
        Args:
            target: 目标地址
            poc_name: POC名称
            poc_module: POC模块
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback(f"poc_{poc_name}", target, progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, f"开始执行POC: {poc_name}")
        
        if hasattr(poc_module, 'poc'):
            poc_func = poc_module.poc
        else:
            poc_func = poc_module
        
        if reporter:
            reporter.report("执行中", 50, "正在执行漏洞检测")
        
        actual_timeout = timeout if timeout is not None else POCAdapter.DEFAULT_POC_TIMEOUT
        is_vulnerable, message = await asyncio.to_thread(poc_func, target, actual_timeout)
        
        if reporter:
            status = "存在漏洞" if is_vulnerable else "未发现漏洞"
            reporter.report("完成", 100, f"检测完成: {status}")
        
        return PluginResult.success(
            data={
                "vulnerable": is_vulnerable,
                "message": message,
                "poc_name": poc_name,
                "target": target
            },
            plugin=f"poc_{poc_name}",
            target=target,
            is_vulnerable=is_vulnerable
        )
    
    @staticmethod
    async def run_poc_batch(
        target: str,
        poc_names: List[str],
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> List[PluginResult]:
        """
        批量执行多个POC
        
        Args:
            target: 目标地址
            poc_names: POC名称列表
            timeout: 单个POC超时时间(秒)
            progress_callback: 进度回调函数
        
        Returns:
            List[PluginResult]: 所有POC的执行结果列表
        """
        results = []
        pocs = POCAdapter.get_all_pocs()
        total = len(poc_names)
        
        reporter = create_progress_callback("poc_batch", target, progress_callback)
        
        for idx, poc_name in enumerate(poc_names):
            if poc_name not in pocs:
                results.append(PluginResult.failed(
                    error=f"POC {poc_name} 不存在",
                    plugin=f"poc_{poc_name}",
                    target=target
                ))
                continue
            
            if reporter:
                progress = int((idx / total) * 100)
                reporter.report("批量检测", progress, f"执行 {poc_name} ({idx+1}/{total})")
            
            result = await POCAdapter.adapt_poc(
                target=target,
                poc_name=poc_name,
                poc_module=pocs[poc_name],
                timeout=timeout,
                progress_callback=None
            )
            results.append(result)
        
        if reporter:
            reporter.report("完成", 100, f"批量检测完成,共检测{total}个POC")
        
        return results
    
    @staticmethod
    def get_all_pocs() -> Dict[str, Any]:
        """
        获取所有POC模块
        
        Returns:
            Dict[str, Any]: POC名称到模块的映射
        """
        from backend.poc import (
            cve_2020_2551_poc, cve_2018_2628_poc, cve_2018_2894_poc,
            cve_2020_14756_poc, cve_2023_21839_poc,
            struts2_009_poc, struts2_032_poc,
            cve_2017_12615_poc, cve_2022_22965_poc, cve_2022_47986_poc,
            cve_2017_12149_poc, cve_2020_10199_poc, cve_2018_7600_poc,
            poc_99617_ai_poc, poc_manual_thinkphp_ai_poc
        )
        
        return {
            "poc_weblogic_2020_2551": cve_2020_2551_poc,
            "poc_weblogic_2018_2628": cve_2018_2628_poc,
            "poc_weblogic_2018_2894": cve_2018_2894_poc,
            "poc_weblogic_2020_14756": cve_2020_14756_poc,
            "poc_weblogic_2023_21839": cve_2023_21839_poc,
            "poc_struts2_009": struts2_009_poc,
            "poc_struts2_032": struts2_032_poc,
            "poc_tomcat_2017_12615": cve_2017_12615_poc,
            "poc_tomcat_2022_22965": cve_2022_22965_poc,
            "poc_tomcat_2022_47986": cve_2022_47986_poc,
            "poc_jboss_2017_12149": cve_2017_12149_poc,
            "poc_nexus_2020_10199": cve_2020_10199_poc,
            "poc_drupal_2018_7600": cve_2018_7600_poc,
            "poc_thinkphp_99617": poc_99617_ai_poc,
            "poc_thinkphp_manual": poc_manual_thinkphp_ai_poc,
        }
    
    @staticmethod
    def get_poc_by_cms(cms: str) -> List[str]:
        """
        根据CMS类型获取相关POC
        
        Args:
            cms: CMS类型
            
        Returns:
            List[str]: 相关POC名称列表
        """
        cms_lower = cms.lower()
        poc_mapping = {
            "weblogic": ["poc_weblogic_2020_2551", "poc_weblogic_2018_2628", 
                       "poc_weblogic_2018_2894", "poc_weblogic_2020_14756", "poc_weblogic_2023_21839"],
            "struts2": ["poc_struts2_009", "poc_struts2_032"],
            "tomcat": ["poc_tomcat_2017_12615", "poc_tomcat_2022_22965", "poc_tomcat_2022_47986"],
            "jboss": ["poc_jboss_2017_12149"],
            "nexus": ["poc_nexus_2020_10199"],
            "drupal": ["poc_drupal_2018_7600"],
            "thinkphp": ["poc_thinkphp_99617", "poc_thinkphp_manual"],
        }
        
        for key, pocs in poc_mapping.items():
            if key in cms_lower:
                return pocs
        
        return []
    
    @staticmethod
    def get_poc_by_port(port: int) -> List[str]:
        """
        根据端口获取相关POC
        
        Args:
            port: 端口号
            
        Returns:
            List[str]: 相关POC名称列表
        """
        port_mapping = {
            7001: ["poc_weblogic_2020_2551", "poc_weblogic_2018_2628", 
                    "poc_weblogic_2018_2894", "poc_weblogic_2020_14756", "poc_weblogic_2023_21839"],
            8080: ["poc_tomcat_2017_12615", "poc_tomcat_2022_22965", "poc_tomcat_2022_47986"],
        }
        
        return port_mapping.get(port, [])


class DependencyAdapter:
    """
    依赖安装适配器
    
    适配依赖安装功能,提供统一的调用接口。
    支持超时控制、异常捕获和进度回调。
    """
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=300.0, plugin_name="dependency_install")
    async def adapt_install_dependencies(
        target: str,
        packages: Optional[str] = None,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> PluginResult:
        """
        适配依赖安装功能
        
        Args:
            target: 目标地址(用于兼容性,实际不使用)
            packages: 要安装的包列表,逗号分隔
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
            **kwargs: 其他参数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("dependency_install", target or "system", progress_callback)
        
        if reporter:
            reporter.report("初始化", 10, "准备安装依赖")
        
        from backend.ai_agents.tools.dependency_installer import install_dependencies
        
        if packages:
            package_list = [p.strip() for p in packages.split(',')]
        else:
            package_list = []
        
        if reporter:
            reporter.report("安装中", 30, f"正在安装 {len(package_list)} 个包")
        
        result = await asyncio.to_thread(install_dependencies, package_list, **kwargs)
        
        if reporter:
            installed_count = len(result.get("installed_packages", []))
            reporter.report("完成", 100, f"安装完成,成功安装 {installed_count} 个包")
        
        if result["status"] == "success":
            return PluginResult.success(
                data={
                    "installed_packages": result["installed_packages"],
                    "output": result["output"],
                    "target": target
                },
                plugin="dependency_install",
                target=target
            )
        else:
            return PluginResult.failed(
                error=result.get("error", "安装失败"),
                plugin="dependency_install",
                target=target,
                output=result.get("output")
            )
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=30.0, plugin_name="check_package")
    async def adapt_check_package(
        target: str,
        package: Optional[str] = None,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> PluginResult:
        """
        适配包检查功能
        
        Args:
            target: 目标地址(用于兼容性)
            package: 要检查的包名
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
            **kwargs: 其他参数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("check_package", target or "system", progress_callback)
        
        if not package:
            return PluginResult.failed(
                error="未指定包名",
                plugin="check_package",
                target=target
            )
        
        if reporter:
            reporter.report("检查中", 50, f"正在检查包: {package}")
        
        from .dependency_installer import check_package_installed
        
        installed = await asyncio.to_thread(check_package_installed, package)
        
        if reporter:
            status = "已安装" if installed else "未安装"
            reporter.report("完成", 100, f"检查完成: {package} {status}")
        
        return PluginResult.success(
            data={"installed": installed, "package": package, "target": target},
            plugin="check_package",
            target=target
        )
    
    @staticmethod
    @with_timeout_and_error_handling(default_timeout=30.0, plugin_name="list_packages")
    async def adapt_get_packages(
        target: str,
        timeout: Optional[float] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> PluginResult:
        """
        适配获取已安装包列表功能
        
        Args:
            target: 目标地址(用于兼容性)
            timeout: 超时时间(秒)
            progress_callback: 进度回调函数
            **kwargs: 其他参数
        
        Returns:
            PluginResult: 统一格式的执行结果
        """
        reporter = create_progress_callback("list_packages", target or "system", progress_callback)
        
        if reporter:
            reporter.report("获取中", 50, "正在获取已安装包列表")
        
        from .dependency_installer import get_installed_packages
        
        packages = await asyncio.to_thread(get_installed_packages)
        
        if reporter:
            reporter.report("完成", 100, f"获取完成,共 {len(packages)} 个包")
        
        return PluginResult.success(
            data={"packages": packages, "count": len(packages), "target": target},
            plugin="list_packages",
            target=target
        )


async def run_plugin(
    plugin_name: str,
    target: str,
    timeout: Optional[float] = None,
    progress_callback: Optional[Callable] = None,
    **kwargs
) -> PluginResult:
    """
    统一的插件运行入口
    
    提供统一的插件调用接口,自动选择对应的适配器执行。
    
    Args:
        plugin_name: 插件名称
        target: 目标地址
        timeout: 超时时间(秒)
        progress_callback: 进度回调函数
        **kwargs: 传递给插件的其他参数
    
    Returns:
        PluginResult: 统一格式的执行结果
    
    Example:
        result = await run_plugin("portscan", "example.com", timeout=60)
        if result.status == "success":
            print(result.data)
    """
    adapters = PluginAdapter.get_adapters()
    
    if plugin_name not in adapters:
        return PluginResult.failed(
            error=f"未知的插件: {plugin_name}",
            plugin=plugin_name,
            target=target,
            available_plugins=list(adapters.keys())
        )
    
    adapter_func = adapters[plugin_name]
    return await adapter_func(
        target=target,
        timeout=timeout,
        progress_callback=progress_callback,
        **kwargs
    )


async def run_multiple_plugins(
    plugin_names: List[str],
    target: str,
    timeout: Optional[float] = None,
    progress_callback: Optional[Callable] = None
) -> Dict[str, PluginResult]:
    """
    批量运行多个插件
    
    Args:
        plugin_names: 插件名称列表
        target: 目标地址
        timeout: 单个插件超时时间(秒)
        progress_callback: 进度回调函数
    
    Returns:
        Dict[str, PluginResult]: 插件名称到执行结果的映射
    """
    results = {}
    total = len(plugin_names)
    
    for idx, plugin_name in enumerate(plugin_names):
        if progress_callback:
            def plugin_progress(name, stage, progress, info):
                overall_progress = int((idx / total) * 100 + (progress / total))
                progress_callback(name, stage, overall_progress, info)
        else:
            plugin_progress = None
        
        results[plugin_name] = await run_plugin(
            plugin_name=plugin_name,
            target=target,
            timeout=timeout,
            progress_callback=plugin_progress
        )
    
    return results

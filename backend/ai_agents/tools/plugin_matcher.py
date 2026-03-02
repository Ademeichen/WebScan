"""
插件智能匹配器

基于目标特征智能匹配插件,处理依赖关系和并行执行调度。
"""
import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .tool_recommender import (
    ToolRecommender,
    TargetProfile,
    ToolRecommendation,
    create_target_profile
)
from .registry import ToolRegistry, registry

logger = logging.getLogger(__name__)


class PluginCategory(Enum):
    """插件分类枚举"""
    INFO_GATHER = "info_gather"
    VULNERABILITY_SCAN = "vulnerability_scan"
    EXPLOIT = "exploit"
    POC = "poc"
    AUXILIARY = "auxiliary"


class DependencyType(Enum):
    """依赖类型枚举"""
    REQUIRED = "required"
    OPTIONAL = "optional"
    CONFLICT = "conflict"


@dataclass
class PluginInfo:
    """
    插件信息数据类
    
    Attributes:
        name: 插件名称
        category: 插件分类
        description: 插件描述
        dependencies: 依赖插件列表
        conflicts: 冲突插件列表
        estimated_time: 预估执行时间(秒)
        resource_usage: 资源使用等级(1-10)
        tags: 标签列表
        applicable_ports: 适用端口列表
        applicable_cms: 适用CMS列表
        applicable_techs: 适用技术栈列表
    """
    name: str
    category: PluginCategory = PluginCategory.AUXILIARY
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    estimated_time: float = 30.0
    resource_usage: int = 5
    tags: List[str] = field(default_factory=list)
    applicable_ports: List[int] = field(default_factory=list)
    applicable_cms: List[str] = field(default_factory=list)
    applicable_techs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "dependencies": self.dependencies,
            "conflicts": self.conflicts,
            "estimated_time": self.estimated_time,
            "resource_usage": self.resource_usage,
            "tags": self.tags,
            "applicable_ports": self.applicable_ports,
            "applicable_cms": self.applicable_cms,
            "applicable_techs": self.applicable_techs
        }


@dataclass
class PluginMatch:
    """
    插件匹配结果数据类
    
    Attributes:
        plugin_name: 插件名称
        match_score: 匹配度分数(0.0-1.0)
        match_reasons: 匹配原因列表
        dependencies: 依赖插件列表
        estimated_time: 预估执行时间(秒)
        category: 插件分类
        priority: 执行优先级
    """
    plugin_name: str
    match_score: float
    match_reasons: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    estimated_time: float = 30.0
    category: PluginCategory = PluginCategory.AUXILIARY
    priority: int = 50
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "plugin_name": self.plugin_name,
            "match_score": self.match_score,
            "match_reasons": self.match_reasons,
            "dependencies": self.dependencies,
            "estimated_time": self.estimated_time,
            "category": self.category.value,
            "priority": self.priority
        }


@dataclass
class ExecutionPlan:
    """
    执行计划数据类
    
    Attributes:
        parallel_groups: 可并行执行的插件组列表
        total_estimated_time: 总预估执行时间(秒)
        dependency_graph: 依赖关系图
        execution_order: 执行顺序列表
        resource_conflicts: 资源冲突列表
    """
    parallel_groups: List[List[str]] = field(default_factory=list)
    total_estimated_time: float = 0.0
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    resource_conflicts: List[Tuple[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "parallel_groups": self.parallel_groups,
            "total_estimated_time": self.total_estimated_time,
            "dependency_graph": self.dependency_graph,
            "execution_order": self.execution_order,
            "resource_conflicts": self.resource_conflicts
        }


@dataclass
class DependencyNode:
    """
    依赖节点数据类
    
    用于构建依赖图,支持拓扑排序。
    
    Attributes:
        name: 节点名称
        dependencies: 依赖节点名称集合
        dependents: 被依赖节点名称集合
        visited: 访问标记(用于循环检测)
        in_stack: 栈中标记(用于循环检测)
    """
    name: str
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    visited: bool = False
    in_stack: bool = False


class PluginMatcher:
    """
    插件智能匹配器
    
    基于目标特征智能匹配插件,处理依赖关系,生成最优执行计划。
    
    功能:
    - 基于端口、CMS、技术栈、WAF等特征匹配插件
    - 解析和处理插件依赖关系
    - 检测和处理循环依赖
    - 生成并行执行计划
    - 整合ToolRecommender的推荐结果
    
    Attributes:
        registry: 工具注册表实例
        recommender: 工具推荐器实例
        plugins_info: 插件信息字典
        max_parallel: 最大并行数
        max_resource_usage: 最大资源使用等级
    """
    
    PLUGIN_DEFINITIONS: Dict[str, PluginInfo] = {
        "baseinfo": PluginInfo(
            name="baseinfo",
            category=PluginCategory.INFO_GATHER,
            description="基础信息收集插件",
            dependencies=[],
            estimated_time=15.0,
            resource_usage=2,
            tags=["info", "basic"],
            applicable_ports=[],
            applicable_cms=[],
            applicable_techs=[]
        ),
        "portscan": PluginInfo(
            name="portscan",
            category=PluginCategory.INFO_GATHER,
            description="端口扫描插件",
            dependencies=[],
            estimated_time=60.0,
            resource_usage=6,
            tags=["port", "scan", "network"],
            applicable_ports=[],
            applicable_cms=[],
            applicable_techs=[]
        ),
        "waf_detect": PluginInfo(
            name="waf_detect",
            category=PluginCategory.INFO_GATHER,
            description="WAF检测插件",
            dependencies=["baseinfo"],
            estimated_time=20.0,
            resource_usage=3,
            tags=["waf", "security"],
            applicable_ports=[80, 443, 8080],
            applicable_cms=[],
            applicable_techs=[]
        ),
        "cdn_detect": PluginInfo(
            name="cdn_detect",
            category=PluginCategory.INFO_GATHER,
            description="CDN检测插件",
            dependencies=["baseinfo"],
            estimated_time=15.0,
            resource_usage=2,
            tags=["cdn", "network"],
            applicable_ports=[],
            applicable_cms=[],
            applicable_techs=[]
        ),
        "cms_identify": PluginInfo(
            name="cms_identify",
            category=PluginCategory.INFO_GATHER,
            description="CMS识别插件",
            dependencies=["baseinfo"],
            estimated_time=25.0,
            resource_usage=4,
            tags=["cms", "fingerprint"],
            applicable_ports=[80, 443, 8080],
            applicable_cms=[],
            applicable_techs=[]
        ),
        "infoleak_scan": PluginInfo(
            name="infoleak_scan",
            category=PluginCategory.VULNERABILITY_SCAN,
            description="信息泄露扫描插件",
            dependencies=["baseinfo"],
            estimated_time=45.0,
            resource_usage=5,
            tags=["infoleak", "security"],
            applicable_ports=[80, 443, 8080],
            applicable_cms=[],
            applicable_techs=[]
        ),
        "subdomain_scan": PluginInfo(
            name="subdomain_scan",
            category=PluginCategory.INFO_GATHER,
            description="子域名扫描插件",
            dependencies=[],
            estimated_time=120.0,
            resource_usage=7,
            tags=["subdomain", "dns"],
            applicable_ports=[],
            applicable_cms=[],
            applicable_techs=[]
        ),
        "webside_scan": PluginInfo(
            name="webside_scan",
            category=PluginCategory.INFO_GATHER,
            description="站点信息扫描插件",
            dependencies=["baseinfo"],
            estimated_time=30.0,
            resource_usage=4,
            tags=["webside", "info"],
            applicable_ports=[80, 443, 8080],
            applicable_cms=[],
            applicable_techs=[]
        ),
        "webweight_scan": PluginInfo(
            name="webweight_scan",
            category=PluginCategory.INFO_GATHER,
            description="网站权重扫描插件",
            dependencies=[],
            estimated_time=20.0,
            resource_usage=2,
            tags=["weight", "seo"],
            applicable_ports=[],
            applicable_cms=[],
            applicable_techs=[]
        ),
        "iplocating": PluginInfo(
            name="iplocating",
            category=PluginCategory.INFO_GATHER,
            description="IP定位插件",
            dependencies=["baseinfo"],
            estimated_time=10.0,
            resource_usage=1,
            tags=["ip", "location"],
            applicable_ports=[],
            applicable_cms=[],
            applicable_techs=[]
        ),
        "poc_weblogic_2020_2551": PluginInfo(
            name="poc_weblogic_2020_2551",
            category=PluginCategory.POC,
            description="Weblogic CVE-2020-2551 POC",
            dependencies=["portscan"],
            estimated_time=30.0,
            resource_usage=4,
            tags=["poc", "weblogic", "rce"],
            applicable_ports=[7001, 7002, 7003],
            applicable_cms=["weblogic"],
            applicable_techs=["weblogic"]
        ),
        "poc_weblogic_2018_2628": PluginInfo(
            name="poc_weblogic_2018_2628",
            category=PluginCategory.POC,
            description="Weblogic CVE-2018-2628 POC",
            dependencies=["portscan"],
            estimated_time=30.0,
            resource_usage=4,
            tags=["poc", "weblogic", "rce"],
            applicable_ports=[7001, 7002, 7003],
            applicable_cms=["weblogic"],
            applicable_techs=["weblogic"]
        ),
        "poc_struts2_009": PluginInfo(
            name="poc_struts2_009",
            category=PluginCategory.POC,
            description="Struts2 S2-009 POC",
            dependencies=["cms_identify"],
            estimated_time=25.0,
            resource_usage=3,
            tags=["poc", "struts2", "rce"],
            applicable_ports=[80, 443, 8080],
            applicable_cms=["struts2"],
            applicable_techs=["struts2"]
        ),
        "poc_tomcat_2017_12615": PluginInfo(
            name="poc_tomcat_2017_12615",
            category=PluginCategory.POC,
            description="Tomcat CVE-2017-12615 POC",
            dependencies=["cms_identify"],
            estimated_time=25.0,
            resource_usage=3,
            tags=["poc", "tomcat", "file_upload"],
            applicable_ports=[8080, 8443],
            applicable_cms=["tomcat"],
            applicable_techs=["tomcat"]
        ),
        "poc_jboss_2017_12149": PluginInfo(
            name="poc_jboss_2017_12149",
            category=PluginCategory.POC,
            description="JBoss CVE-2017-12149 POC",
            dependencies=["portscan"],
            estimated_time=30.0,
            resource_usage=4,
            tags=["poc", "jboss", "deserialization"],
            applicable_ports=[8080, 8081, 8082],
            applicable_cms=["jboss"],
            applicable_techs=["jboss"]
        ),
    }
    
    PORT_PLUGIN_MAPPING: Dict[int, List[str]] = {
        7001: ["poc_weblogic_2020_2551", "poc_weblogic_2018_2628"],
        8080: ["poc_tomcat_2017_12615", "poc_jboss_2017_12149"],
        8081: ["poc_jboss_2017_12149"],
        8082: ["poc_jboss_2017_12149"],
    }
    
    CMS_PLUGIN_MAPPING: Dict[str, List[str]] = {
        "weblogic": ["poc_weblogic_2020_2551", "poc_weblogic_2018_2628"],
        "struts2": ["poc_struts2_009"],
        "tomcat": ["poc_tomcat_2017_12615"],
        "jboss": ["poc_jboss_2017_12149"],
    }
    
    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        recommender: Optional[ToolRecommender] = None,
        max_parallel: int = 5,
        max_resource_usage: int = 8
    ):
        """
        初始化插件匹配器
        
        Args:
            registry: 工具注册表实例
            recommender: 工具推荐器实例
            max_parallel: 最大并行执行数
            max_resource_usage: 最大资源使用等级
        """
        self.registry = registry or globals().get('registry')
        self.recommender = recommender or ToolRecommender(registry=self.registry)
        self.plugins_info: Dict[str, PluginInfo] = dict(self.PLUGIN_DEFINITIONS)
        self.max_parallel = max_parallel
        self.max_resource_usage = max_resource_usage
        self._dependency_cache: Dict[str, List[str]] = {}
        logger.info(f"插件匹配器初始化完成, 已加载 {len(self.plugins_info)} 个插件定义")
    
    def register_plugin(self, plugin_info: PluginInfo) -> None:
        """
        注册插件信息
        
        Args:
            plugin_info: 插件信息对象
        """
        self.plugins_info[plugin_info.name] = plugin_info
        self._dependency_cache.clear()
        logger.info(f"注册插件: {plugin_info.name}")
    
    def match_by_target(
        self,
        target: str,
        ports: Optional[List[int]] = None,
        cms: Optional[str] = None,
        technologies: Optional[List[str]] = None,
        waf: Optional[str] = None,
        include_dependencies: bool = True
    ) -> List[PluginMatch]:
        """
        根据目标特征匹配插件
        
        综合分析目标的各种特征,返回匹配度排序的插件列表。
        
        Args:
            target: 目标地址
            ports: 开放端口列表
            cms: CMS类型
            technologies: 技术栈列表
            waf: WAF类型
            include_dependencies: 是否包含依赖插件
            
        Returns:
            List[PluginMatch]: 匹配度排序的插件列表
        """
        matches: Dict[str, PluginMatch] = {}
        
        base_plugins = ["baseinfo", "portscan"]
        for plugin_name in base_plugins:
            if plugin_name in self.plugins_info:
                plugin_info = self.plugins_info[plugin_name]
                matches[plugin_name] = PluginMatch(
                    plugin_name=plugin_name,
                    match_score=1.0,
                    match_reasons=["基础信息收集插件"],
                    dependencies=plugin_info.dependencies.copy(),
                    estimated_time=plugin_info.estimated_time,
                    category=plugin_info.category,
                    priority=100
                )
        
        if ports:
            port_matches = self._match_by_ports(ports)
            for plugin_name, match in port_matches.items():
                if plugin_name in matches:
                    matches[plugin_name].match_score = min(1.0, matches[plugin_name].match_score + 0.2)
                    matches[plugin_name].match_reasons.extend(match.match_reasons)
                else:
                    matches[plugin_name] = match
        
        if cms:
            cms_matches = self._match_by_cms(cms)
            for plugin_name, match in cms_matches.items():
                if plugin_name in matches:
                    matches[plugin_name].match_score = min(1.0, matches[plugin_name].match_score + 0.3)
                    matches[plugin_name].match_reasons.extend(match.match_reasons)
                else:
                    matches[plugin_name] = match
        
        if technologies:
            tech_matches = self._match_by_technologies(technologies)
            for plugin_name, match in tech_matches.items():
                if plugin_name in matches:
                    matches[plugin_name].match_score = min(1.0, matches[plugin_name].match_score + 0.1)
                    matches[plugin_name].match_reasons.extend(match.match_reasons)
                else:
                    matches[plugin_name] = match
        
        if waf:
            waf_matches = self._match_by_waf(waf)
            for plugin_name, match in waf_matches.items():
                if plugin_name in matches:
                    matches[plugin_name].match_reasons.extend(match.match_reasons)
                else:
                    matches[plugin_name] = match
        
        if include_dependencies:
            matches = self._add_dependencies(matches)
        
        sorted_matches = sorted(
            matches.values(),
            key=lambda x: (x.priority, x.match_score),
            reverse=True
        )
        
        logger.info(f"目标 {target} 匹配到 {len(sorted_matches)} 个插件")
        return sorted_matches
    
    def _match_by_ports(self, ports: List[int]) -> Dict[str, PluginMatch]:
        """
        根据端口匹配插件
        
        Args:
            ports: 端口列表
            
        Returns:
            Dict[str, PluginMatch]: 插件匹配结果字典
        """
        matches: Dict[str, PluginMatch] = {}
        
        for port in ports:
            plugin_names = self.PORT_PLUGIN_MAPPING.get(port, [])
            for plugin_name in plugin_names:
                if plugin_name in self.plugins_info:
                    plugin_info = self.plugins_info[plugin_name]
                    if plugin_name in matches:
                        matches[plugin_name].match_reasons.append(f"端口 {port} 匹配")
                    else:
                        matches[plugin_name] = PluginMatch(
                            plugin_name=plugin_name,
                            match_score=0.8,
                            match_reasons=[f"端口 {port} 匹配"],
                            dependencies=plugin_info.dependencies.copy(),
                            estimated_time=plugin_info.estimated_time,
                            category=plugin_info.category,
                            priority=80
                        )
        
        return matches
    
    def _match_by_cms(self, cms: str) -> Dict[str, PluginMatch]:
        """
        根据CMS匹配插件
        
        Args:
            cms: CMS类型
            
        Returns:
            Dict[str, PluginMatch]: 插件匹配结果字典
        """
        matches: Dict[str, PluginMatch] = {}
        cms_lower = cms.lower()
        
        for cms_key, plugin_names in self.CMS_PLUGIN_MAPPING.items():
            if cms_key in cms_lower:
                for plugin_name in plugin_names:
                    if plugin_name in self.plugins_info:
                        plugin_info = self.plugins_info[plugin_name]
                        matches[plugin_name] = PluginMatch(
                            plugin_name=plugin_name,
                            match_score=0.95,
                            match_reasons=[f"CMS {cms} 匹配"],
                            dependencies=plugin_info.dependencies.copy(),
                            estimated_time=plugin_info.estimated_time,
                            category=plugin_info.category,
                            priority=90
                        )
        
        return matches
    
    def _match_by_technologies(self, technologies: List[str]) -> Dict[str, PluginMatch]:
        """
        根据技术栈匹配插件
        
        Args:
            technologies: 技术栈列表
            
        Returns:
            Dict[str, PluginMatch]: 插件匹配结果字典
        """
        matches: Dict[str, PluginMatch] = {}
        
        for tech in technologies:
            tech_lower = tech.lower()
            for plugin_name, plugin_info in self.plugins_info.items():
                if tech_lower in [t.lower() for t in plugin_info.applicable_techs]:
                    if plugin_name in matches:
                        matches[plugin_name].match_reasons.append(f"技术栈 {tech} 匹配")
                    else:
                        matches[plugin_name] = PluginMatch(
                            plugin_name=plugin_name,
                            match_score=0.7,
                            match_reasons=[f"技术栈 {tech} 匹配"],
                            dependencies=plugin_info.dependencies.copy(),
                            estimated_time=plugin_info.estimated_time,
                            category=plugin_info.category,
                            priority=70
                        )
        
        return matches
    
    def _match_by_waf(self, waf: str) -> Dict[str, PluginMatch]:
        """
        根据WAF匹配插件
        
        Args:
            waf: WAF类型
            
        Returns:
            Dict[str, PluginMatch]: 插件匹配结果字典
        """
        matches: Dict[str, PluginMatch] = {}
        
        waf_lower = waf.lower()
        if waf_lower != "none" and waf_lower != "unknown":
            if "waf_detect" in self.plugins_info:
                plugin_info = self.plugins_info["waf_detect"]
                matches["waf_detect"] = PluginMatch(
                    plugin_name="waf_detect",
                    match_score=0.6,
                    match_reasons=[f"WAF {waf} 已检测,建议绕过测试"],
                    dependencies=plugin_info.dependencies.copy(),
                    estimated_time=plugin_info.estimated_time,
                    category=plugin_info.category,
                    priority=60
                )
        
        return matches
    
    def _add_dependencies(self, matches: Dict[str, PluginMatch]) -> Dict[str, PluginMatch]:
        """
        添加依赖插件到匹配结果
        
        Args:
            matches: 原始匹配结果
            
        Returns:
            Dict[str, PluginMatch]: 包含依赖的匹配结果
        """
        all_plugins = set(matches.keys())
        added = True
        
        while added:
            added = False
            for plugin_name in list(all_plugins):
                if plugin_name in self.plugins_info:
                    for dep in self.plugins_info[plugin_name].dependencies:
                        if dep not in all_plugins and dep in self.plugins_info:
                            dep_info = self.plugins_info[dep]
                            matches[dep] = PluginMatch(
                                plugin_name=dep,
                                match_score=0.5,
                                match_reasons=[f"插件 {plugin_name} 的依赖"],
                                dependencies=dep_info.dependencies.copy(),
                                estimated_time=dep_info.estimated_time,
                                category=dep_info.category,
                                priority=95
                            )
                            all_plugins.add(dep)
                            added = True
        
        return matches
    
    def resolve_dependencies(
        self,
        plugin_names: List[str]
    ) -> Dict[str, List[str]]:
        """
        解析插件依赖关系
        
        递归解析所有插件的依赖关系,返回完整的依赖图。
        
        Args:
            plugin_names: 插件名称列表
            
        Returns:
            Dict[str, List[str]]: 依赖关系图,键为插件名,值为依赖列表
        """
        dependency_graph: Dict[str, List[str]] = {}
        visited: Set[str] = set()
        
        def resolve_recursive(plugin_name: str) -> None:
            if plugin_name in visited:
                return
            
            visited.add(plugin_name)
            
            if plugin_name not in self.plugins_info:
                dependency_graph[plugin_name] = []
                return
            
            plugin_info = self.plugins_info[plugin_name]
            dependencies = plugin_info.dependencies.copy()
            
            for dep in dependencies:
                resolve_recursive(dep)
            
            dependency_graph[plugin_name] = dependencies
        
        for plugin_name in plugin_names:
            resolve_recursive(plugin_name)
        
        logger.debug(f"解析依赖关系完成, 共 {len(dependency_graph)} 个插件")
        return dependency_graph
    
    def detect_circular_dependency(
        self,
        dependency_graph: Dict[str, List[str]]
    ) -> Optional[List[str]]:
        """
        检测循环依赖
        
        使用深度优先搜索检测依赖图中是否存在循环依赖。
        
        Args:
            dependency_graph: 依赖关系图
            
        Returns:
            Optional[List[str]]: 如果存在循环依赖,返回循环路径;否则返回None
        """
        nodes: Dict[str, DependencyNode] = {}
        
        for plugin_name in dependency_graph:
            nodes[plugin_name] = DependencyNode(
                name=plugin_name,
                dependencies=set(dependency_graph[plugin_name])
            )
        
        for plugin_name, deps in dependency_graph.items():
            for dep in deps:
                if dep in nodes:
                    nodes[dep].dependents.add(plugin_name)
        
        def dfs(node: DependencyNode, path: List[str]) -> Optional[List[str]]:
            node.visited = True
            node.in_stack = True
            path.append(node.name)
            
            for dep_name in node.dependencies:
                if dep_name not in nodes:
                    continue
                
                dep_node = nodes[dep_name]
                
                if dep_node.in_stack:
                    cycle_start = path.index(dep_name)
                    return path[cycle_start:] + [dep_name]
                
                if not dep_node.visited:
                    result = dfs(dep_node, path)
                    if result:
                        return result
            
            path.pop()
            node.in_stack = False
            return None
        
        for node in nodes.values():
            if not node.visited:
                result = dfs(node, [])
                if result:
                    logger.warning(f"检测到循环依赖: {' -> '.join(result)}")
                    return result
        
        return None
    
    def get_execution_order(
        self,
        plugin_names: List[str]
    ) -> List[str]:
        """
        计算最优执行顺序
        
        使用拓扑排序计算满足依赖关系的最优执行顺序。
        
        Args:
            plugin_names: 插件名称列表
            
        Returns:
            List[str]: 排序后的插件执行顺序
            
        Raises:
            ValueError: 存在循环依赖时抛出
        """
        dependency_graph = self.resolve_dependencies(plugin_names)
        
        cycle = self.detect_circular_dependency(dependency_graph)
        if cycle:
            raise ValueError(f"存在循环依赖,无法确定执行顺序: {' -> '.join(cycle)}")
        
        in_degree: Dict[str, int] = defaultdict(int)
        for plugin_name in dependency_graph:
            if plugin_name not in in_degree:
                in_degree[plugin_name] = 0
            for dep in dependency_graph[plugin_name]:
                in_degree[plugin_name] += 1
        
        queue: deque = deque()
        for plugin_name in dependency_graph:
            if in_degree[plugin_name] == 0:
                queue.append(plugin_name)
        
        execution_order: List[str] = []
        
        while queue:
            current = queue.popleft()
            execution_order.append(current)
            
            for plugin_name, deps in dependency_graph.items():
                if current in deps:
                    in_degree[plugin_name] -= 1
                    if in_degree[plugin_name] == 0:
                        queue.append(plugin_name)
        
        if len(execution_order) != len(dependency_graph):
            missing = set(dependency_graph.keys()) - set(execution_order)
            raise ValueError(f"依赖解析不完整,缺失插件: {missing}")
        
        logger.info(f"执行顺序计算完成: {execution_order}")
        return execution_order
    
    def get_parallel_groups(
        self,
        plugin_names: List[str],
        consider_resources: bool = True
    ) -> List[List[str]]:
        """
        获取可并行执行的插件组
        
        根据依赖关系和资源限制,将插件分组为可并行执行的批次。
        
        Args:
            plugin_names: 插件名称列表
            consider_resources: 是否考虑资源限制
            
        Returns:
            List[List[str]]: 并行执行组列表,每组内的插件可并行执行
        """
        dependency_graph = self.resolve_dependencies(plugin_names)
        
        cycle = self.detect_circular_dependency(dependency_graph)
        if cycle:
            logger.warning(f"存在循环依赖,将尝试解除: {' -> '.join(cycle)}")
            for plugin in cycle[:-1]:
                if plugin in dependency_graph:
                    dependency_graph[plugin] = [
                        d for d in dependency_graph[plugin] if d != cycle[-1]
                    ]
        
        completed: Set[str] = set()
        parallel_groups: List[List[str]] = []
        
        while len(completed) < len(dependency_graph):
            ready: List[str] = []
            
            for plugin_name in dependency_graph:
                if plugin_name in completed:
                    continue
                
                deps = dependency_graph[plugin_name]
                if all(dep in completed for dep in deps):
                    ready.append(plugin_name)
            
            if not ready:
                remaining = set(dependency_graph.keys()) - completed
                logger.warning(f"无法继续分组,剩余插件: {remaining}")
                break
            
            if consider_resources:
                group = self._group_by_resources(ready)
            else:
                group = ready[:self.max_parallel]
            
            parallel_groups.append(group)
            completed.update(group)
        
        logger.info(f"并行分组完成, 共 {len(parallel_groups)} 组")
        return parallel_groups
    
    def _group_by_resources(self, ready_plugins: List[str]) -> List[str]:
        """
        根据资源限制分组插件
        
        Args:
            ready_plugins: 就绪插件列表
            
        Returns:
            List[str]: 当前批次可执行的插件列表
        """
        group: List[str] = []
        total_resource = 0
        
        sorted_plugins = sorted(
            ready_plugins,
            key=lambda x: self.plugins_info.get(x, PluginInfo(name=x)).resource_usage
        )
        
        for plugin_name in sorted_plugins:
            if len(group) >= self.max_parallel:
                break
            
            plugin_info = self.plugins_info.get(plugin_name, PluginInfo(name=plugin_name))
            if total_resource + plugin_info.resource_usage <= self.max_resource_usage:
                group.append(plugin_name)
                total_resource += plugin_info.resource_usage
        
        return group
    
    def create_execution_plan(
        self,
        plugin_names: List[str],
        consider_resources: bool = True
    ) -> ExecutionPlan:
        """
        创建完整的执行计划
        
        综合依赖关系、并行分组和资源限制,生成完整的执行计划。
        
        Args:
            plugin_names: 插件名称列表
            consider_resources: 是否考虑资源限制
            
        Returns:
            ExecutionPlan: 执行计划对象
        """
        dependency_graph = self.resolve_dependencies(plugin_names)
        
        try:
            execution_order = self.get_execution_order(plugin_names)
        except ValueError as e:
            logger.warning(f"执行顺序计算失败: {e}, 使用原始顺序")
            execution_order = list(dependency_graph.keys())
        
        parallel_groups = self.get_parallel_groups(plugin_names, consider_resources)
        
        total_time = sum(
            self.plugins_info.get(name, PluginInfo(name=name)).estimated_time
            for name in dependency_graph
        )
        
        if parallel_groups:
            parallel_time = sum(
                max(
                    self.plugins_info.get(name, PluginInfo(name=name)).estimated_time
                    for name in group
                ) if group else 0
                for group in parallel_groups
            )
            total_time = min(total_time, parallel_time)
        
        resource_conflicts = self._detect_resource_conflicts(plugin_names)
        
        plan = ExecutionPlan(
            parallel_groups=parallel_groups,
            total_estimated_time=total_time,
            dependency_graph=dependency_graph,
            execution_order=execution_order,
            resource_conflicts=resource_conflicts
        )
        
        logger.info(f"执行计划创建完成, 预估时间: {total_time:.1f}秒")
        return plan
    
    def _detect_resource_conflicts(
        self,
        plugin_names: List[str]
    ) -> List[Tuple[str, str]]:
        """
        检测资源冲突
        
        检测插件之间是否存在资源冲突(如互斥访问同一资源)。
        
        Args:
            plugin_names: 插件名称列表
            
        Returns:
            List[Tuple[str, str]]: 冲突插件对列表
        """
        conflicts: List[Tuple[str, str]] = []
        
        for i, plugin1 in enumerate(plugin_names):
            if plugin1 not in self.plugins_info:
                continue
            
            info1 = self.plugins_info[plugin1]
            
            for plugin2 in plugin_names[i + 1:]:
                if plugin2 not in self.plugins_info:
                    continue
                
                info2 = self.plugins_info[plugin2]
                
                if plugin2 in info1.conflicts or plugin1 in info2.conflicts:
                    conflicts.append((plugin1, plugin2))
                
                if info1.resource_usage + info2.resource_usage > self.max_resource_usage:
                    if info1.resource_usage > 5 and info2.resource_usage > 5:
                        conflicts.append((plugin1, plugin2))
        
        return conflicts
    
    def recommend_plugins(
        self,
        target: str,
        ports: Optional[List[int]] = None,
        cms: Optional[str] = None,
        technologies: Optional[List[str]] = None,
        vulnerabilities: Optional[List[str]] = None,
        use_llm: bool = False,
        top_n: int = 10
    ) -> List[PluginMatch]:
        """
        综合推荐插件
        
        整合ToolRecommender的结果和插件匹配结果,生成综合推荐列表。
        
        Args:
            target: 目标地址
            ports: 开放端口列表
            cms: CMS类型
            technologies: 技术栈列表
            vulnerabilities: 已知漏洞列表
            use_llm: 是否使用LLM增强
            top_n: 返回数量限制
            
        Returns:
            List[PluginMatch]: 推荐插件列表
        """
        profile = create_target_profile(
            target=target,
            ports=ports or [],
            cms=cms,
            technologies=technologies or [],
            vulnerabilities=vulnerabilities or []
        )
        
        tool_recommendations = self.recommender.recommend_for_target(profile, use_llm)
        
        plugin_matches = self.match_by_target(
            target=target,
            ports=ports,
            cms=cms,
            technologies=technologies,
            include_dependencies=True
        )
        
        combined: Dict[str, PluginMatch] = {}
        
        for match in plugin_matches:
            combined[match.plugin_name] = match
        
        for rec in tool_recommendations:
            plugin_name = rec.tool_name
            if plugin_name in combined:
                existing = combined[plugin_name]
                existing.match_score = min(1.0, existing.match_score + rec.confidence * 0.3)
                existing.priority = min(100, existing.priority + int(rec.priority * 0.2))
                existing.match_reasons.append(f"推荐器: {rec.reason}")
            else:
                plugin_info = self.plugins_info.get(
                    plugin_name,
                    PluginInfo(name=plugin_name, category=PluginCategory.POC)
                )
                combined[plugin_name] = PluginMatch(
                    plugin_name=plugin_name,
                    match_score=rec.confidence,
                    match_reasons=[rec.reason],
                    dependencies=plugin_info.dependencies.copy(),
                    estimated_time=plugin_info.estimated_time,
                    category=plugin_info.category,
                    priority=rec.priority
                )
        
        sorted_recommendations = sorted(
            combined.values(),
            key=lambda x: (x.priority, x.match_score),
            reverse=True
        )[:top_n]
        
        logger.info(f"综合推荐完成, 返回 {len(sorted_recommendations)} 个插件")
        return sorted_recommendations
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        获取插件信息
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[PluginInfo]: 插件信息,不存在则返回None
        """
        return self.plugins_info.get(plugin_name)
    
    def list_plugins(
        self,
        category: Optional[PluginCategory] = None
    ) -> List[PluginInfo]:
        """
        列出所有插件
        
        Args:
            category: 按分类过滤
            
        Returns:
            List[PluginInfo]: 插件信息列表
        """
        plugins = list(self.plugins_info.values())
        
        if category:
            plugins = [p for p in plugins if p.category == category]
        
        return sorted(plugins, key=lambda x: x.name)
    
    def validate_plugins(self, plugin_names: List[str]) -> Dict[str, bool]:
        """
        验证插件是否可用
        
        Args:
            plugin_names: 插件名称列表
            
        Returns:
            Dict[str, bool]: 插件可用性字典
        """
        result = {}
        for name in plugin_names:
            in_definitions = name in self.plugins_info
            in_registry = self.registry.has_tool(name) if self.registry else True
            result[name] = in_definitions or in_registry
        
        return result


async def match_plugins_for_target(
    target: str,
    ports: Optional[List[int]] = None,
    cms: Optional[str] = None,
    technologies: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    为目标匹配插件的异步便捷函数
    
    Args:
        target: 目标地址
        ports: 开放端口列表
        cms: CMS类型
        technologies: 技术栈列表
        
    Returns:
        List[Dict[str, Any]]: 匹配的插件列表(字典格式)
    """
    matcher = PluginMatcher()
    matches = matcher.match_by_target(
        target=target,
        ports=ports,
        cms=cms,
        technologies=technologies
    )
    return [match.to_dict() for match in matches]


async def get_execution_plan_for_plugins(
    plugin_names: List[str],
    consider_resources: bool = True
) -> Dict[str, Any]:
    """
    获取插件执行计划的异步便捷函数
    
    Args:
        plugin_names: 插件名称列表
        consider_resources: 是否考虑资源限制
        
    Returns:
        Dict[str, Any]: 执行计划(字典格式)
    """
    matcher = PluginMatcher()
    plan = matcher.create_execution_plan(plugin_names, consider_resources)
    return plan.to_dict()

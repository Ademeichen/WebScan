"""
工具推荐系统

基于目标特征智能推荐安全扫描工具,支持端口映射、CMS识别、漏洞类型匹配等。
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from .registry import ToolRegistry, registry

logger = logging.getLogger(__name__)


class RecommendationSource(Enum):
    """推荐来源枚举"""
    PORT_BASED = "port_based"
    CMS_BASED = "cms_based"
    VULNERABILITY_BASED = "vulnerability_based"
    LLM_ENHANCED = "llm_enhanced"
    HEURISTIC = "heuristic"


@dataclass
class ToolRecommendation:
    """
    工具推荐结果数据类
    
    Attributes:
        tool_name: 工具名称
        priority: 推荐优先级(1-100)
        confidence: 推荐置信度(0.0-1.0)
        source: 推荐来源
        reason: 推荐原因
        metadata: 额外元数据
    """
    tool_name: str
    priority: int
    confidence: float
    source: RecommendationSource
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "tool_name": self.tool_name,
            "priority": self.priority,
            "confidence": self.confidence,
            "source": self.source.value,
            "reason": self.reason,
            "metadata": self.metadata
        }


@dataclass
class TargetProfile:
    """
    目标画像数据类
    
    Attributes:
        target: 目标地址
        ports: 开放端口列表
        cms: 识别到的CMS类型
        technologies: 技术栈列表
        vulnerabilities: 已知漏洞列表
        services: 服务信息字典
        metadata: 额外元数据
    """
    target: str
    ports: List[int] = field(default_factory=list)
    cms: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    vulnerabilities: List[str] = field(default_factory=list)
    services: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolRecommender:
    """
    工具推荐器
    
    基于目标特征智能推荐安全扫描工具,支持多种推荐策略:
    - 端口映射: 根据开放端口推荐相关POC
    - CMS映射: 根据CMS类型推荐相关漏洞检测工具
    - 漏洞类型映射: 根据已知漏洞类型推荐验证工具
    - LLM增强: 使用大语言模型辅助决策
    
    Attributes:
        registry: 工具注册表实例
        llm_client: LLM客户端(可选)
    """
    
    PORT_POC_MAPPING: Dict[int, List[Dict[str, Any]]] = {
        7001: [
            {"name": "poc_weblogic_2020_2551", "priority": 90, "reason": "Weblogic默认端口,检测CVE-2020-2551反序列化漏洞"},
            {"name": "poc_weblogic_2018_2628", "priority": 85, "reason": "Weblogic默认端口,检测CVE-2018-2628反序列化漏洞"},
            {"name": "poc_weblogic_2018_2894", "priority": 80, "reason": "Weblogic默认端口,检测CVE-2018-2894未授权访问漏洞"},
            {"name": "poc_weblogic_2020_14756", "priority": 75, "reason": "Weblogic默认端口,检测CVE-2020-14756漏洞"},
            {"name": "poc_weblogic_2023_21839", "priority": 70, "reason": "Weblogic默认端口,检测CVE-2023-21839漏洞"},
        ],
        8080: [
            {"name": "poc_tomcat_2017_12615", "priority": 85, "reason": "Tomcat常用端口,检测CVE-2017-12615 PUT漏洞"},
            {"name": "poc_tomcat_2022_22965", "priority": 80, "reason": "Tomcat常用端口,检测Spring4Shell漏洞"},
            {"name": "poc_tomcat_2022_47986", "priority": 75, "reason": "Tomcat常用端口,检测CVE-2022-47986漏洞"},
        ],
        8081: [
            {"name": "poc_jboss_2017_12149", "priority": 85, "reason": "JBoss常用端口,检测CVE-2017-12149反序列化漏洞"},
        ],
        8082: [
            {"name": "poc_jboss_2017_12149", "priority": 80, "reason": "JBoss备用端口,检测CVE-2017-12149反序列化漏洞"},
        ],
        8071: [
            {"name": "poc_weblogic_2020_2551", "priority": 85, "reason": "Weblogic备用端口,检测CVE-2020-2551漏洞"},
        ],
        443: [
            {"name": "ssl_scan", "priority": 70, "reason": "HTTPS端口,建议进行SSL/TLS安全检测"},
        ],
        21: [
            {"name": "ftp_anonymous_check", "priority": 75, "reason": "FTP端口,检测匿名访问漏洞"},
        ],
        22: [
            {"name": "ssh_brute_check", "priority": 60, "reason": "SSH端口,注意弱口令风险"},
        ],
        3306: [
            {"name": "mysql_weak_password", "priority": 65, "reason": "MySQL端口,检测弱口令和未授权访问"},
        ],
        6379: [
            {"name": "redis_unauthorized", "priority": 85, "reason": "Redis端口,检测未授权访问漏洞"},
        ],
        27017: [
            {"name": "mongodb_unauthorized", "priority": 85, "reason": "MongoDB端口,检测未授权访问漏洞"},
        ],
        9200: [
            {"name": "elasticsearch_unauthorized", "priority": 85, "reason": "Elasticsearch端口,检测未授权访问漏洞"},
        ],
    }
    
    CMS_POC_MAPPING: Dict[str, List[Dict[str, Any]]] = {
        "weblogic": [
            {"name": "poc_weblogic_2020_2551", "priority": 95, "reason": "Weblogic核心漏洞CVE-2020-2551"},
            {"name": "poc_weblogic_2018_2628", "priority": 90, "reason": "Weblogic核心漏洞CVE-2018-2628"},
            {"name": "poc_weblogic_2018_2894", "priority": 85, "reason": "Weblogic核心漏洞CVE-2018-2894"},
            {"name": "poc_weblogic_2020_14756", "priority": 80, "reason": "Weblogic核心漏洞CVE-2020-14756"},
            {"name": "poc_weblogic_2023_21839", "priority": 75, "reason": "Weblogic核心漏洞CVE-2023-21839"},
        ],
        "struts2": [
            {"name": "poc_struts2_009", "priority": 95, "reason": "Struts2 OGNL代码执行漏洞S2-009"},
            {"name": "poc_struts2_032", "priority": 90, "reason": "Struts2远程代码执行漏洞S2-032"},
        ],
        "tomcat": [
            {"name": "poc_tomcat_2017_12615", "priority": 90, "reason": "Tomcat PUT方法任意文件写入漏洞"},
            {"name": "poc_tomcat_2022_22965", "priority": 85, "reason": "Tomcat Spring4Shell漏洞"},
            {"name": "poc_tomcat_2022_47986", "priority": 80, "reason": "Tomcat CVE-2022-47986漏洞"},
        ],
        "jboss": [
            {"name": "poc_jboss_2017_12149", "priority": 95, "reason": "JBoss JMXInvokerServlet反序列化漏洞"},
        ],
        "nexus": [
            {"name": "poc_nexus_2020_10199", "priority": 95, "reason": "Nexus Repository Manager远程代码执行漏洞"},
        ],
        "drupal": [
            {"name": "poc_drupal_2018_7600", "priority": 95, "reason": "Drupal远程代码执行漏洞CVE-2018-7600"},
        ],
        "spring": [
            {"name": "poc_spring_spel", "priority": 85, "reason": "Spring SpEL注入漏洞"},
            {"name": "poc_spring_actuator", "priority": 80, "reason": "Spring Actuator未授权访问"},
        ],
        "shiro": [
            {"name": "poc_shiro_deserialize", "priority": 95, "reason": "Shiro反序列化漏洞(CVE-2016-4437)"},
        ],
        "fastjson": [
            {"name": "poc_fastjson_rce", "priority": 95, "reason": "Fastjson反序列化远程代码执行漏洞"},
        ],
        "thinkphp": [
            {"name": "poc_thinkphp_rce", "priority": 90, "reason": "ThinkPHP远程代码执行漏洞"},
        ],
        "weblogic": [
            {"name": "poc_weblogic_2020_2551", "priority": 95, "reason": "Weblogic T3协议反序列化漏洞"},
        ],
    }
    
    VULNERABILITY_POC_MAPPING: Dict[str, List[Dict[str, Any]]] = {
        "deserialization": [
            {"name": "poc_weblogic_2020_2551", "priority": 85, "reason": "反序列化漏洞检测"},
            {"name": "poc_weblogic_2018_2628", "priority": 80, "reason": "反序列化漏洞检测"},
            {"name": "poc_jboss_2017_12149", "priority": 75, "reason": "反序列化漏洞检测"},
        ],
        "rce": [
            {"name": "poc_struts2_009", "priority": 85, "reason": "远程代码执行漏洞检测"},
            {"name": "poc_struts2_032", "priority": 80, "reason": "远程代码执行漏洞检测"},
        ],
        "unauthorized": [
            {"name": "redis_unauthorized", "priority": 85, "reason": "未授权访问漏洞检测"},
            {"name": "mongodb_unauthorized", "priority": 80, "reason": "未授权访问漏洞检测"},
            {"name": "elasticsearch_unauthorized", "priority": 75, "reason": "未授权访问漏洞检测"},
        ],
        "file_upload": [
            {"name": "poc_tomcat_2017_12615", "priority": 85, "reason": "文件上传漏洞检测"},
        ],
        "ssrf": [
            {"name": "ssrf_detector", "priority": 80, "reason": "SSRF漏洞检测"},
        ],
        "sqli": [
            {"name": "sql_injection_scanner", "priority": 85, "reason": "SQL注入漏洞检测"},
        ],
        "xss": [
            {"name": "xss_scanner", "priority": 75, "reason": "XSS跨站脚本漏洞检测"},
        ],
    }
    
    TOOL_CATEGORY_PRIORITY: Dict[str, int] = {
        "poc": 100,
        "exploit": 90,
        "vulnerability_scan": 80,
        "info_gather": 70,
        "plugin": 60,
        "general": 50,
    }
    
    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        llm_client: Optional[Any] = None
    ):
        """
        初始化工具推荐器
        
        Args:
            registry: 工具注册表实例,默认使用全局注册表
            llm_client: LLM客户端实例,用于增强决策
        """
        self.registry = registry or globals().get('registry')
        self.llm_client = llm_client
        self._recommendation_cache: Dict[str, List[ToolRecommendation]] = {}
        logger.info("工具推荐器初始化完成")
    
    def recommend_by_port(
        self,
        port: int,
        base_priority: int = 50
    ) -> List[ToolRecommendation]:
        """
        根据端口推荐工具
        
        Args:
            port: 端口号
            base_priority: 基础优先级
            
        Returns:
            List[ToolRecommendation]: 推荐工具列表
        """
        recommendations = []
        
        port_tools = self.PORT_POC_MAPPING.get(port, [])
        for tool_info in port_tools:
            recommendation = ToolRecommendation(
                tool_name=tool_info["name"],
                priority=tool_info["priority"] + base_priority,
                confidence=min(0.9, tool_info["priority"] / 100),
                source=RecommendationSource.PORT_BASED,
                reason=tool_info["reason"],
                metadata={"port": port}
            )
            recommendations.append(recommendation)
        
        logger.debug(f"端口 {port} 推荐 {len(recommendations)} 个工具")
        return recommendations
    
    def recommend_by_cms(
        self,
        cms: str,
        base_priority: int = 50
    ) -> List[ToolRecommendation]:
        """
        根据CMS类型推荐工具
        
        Args:
            cms: CMS类型名称
            base_priority: 基础优先级
            
        Returns:
            List[ToolRecommendation]: 推荐工具列表
        """
        recommendations = []
        cms_lower = cms.lower()
        
        for cms_key, tools in self.CMS_POC_MAPPING.items():
            if cms_key in cms_lower:
                for tool_info in tools:
                    recommendation = ToolRecommendation(
                        tool_name=tool_info["name"],
                        priority=tool_info["priority"] + base_priority,
                        confidence=min(0.95, tool_info["priority"] / 100),
                        source=RecommendationSource.CMS_BASED,
                        reason=tool_info["reason"],
                        metadata={"cms": cms, "matched_key": cms_key}
                    )
                    recommendations.append(recommendation)
                break
        
        logger.debug(f"CMS {cms} 推荐 {len(recommendations)} 个工具")
        return recommendations
    
    def recommend_by_vulnerability(
        self,
        vulnerability_type: str,
        base_priority: int = 50
    ) -> List[ToolRecommendation]:
        """
        根据漏洞类型推荐工具
        
        Args:
            vulnerability_type: 漏洞类型
            base_priority: 基础优先级
            
        Returns:
            List[ToolRecommendation]: 推荐工具列表
        """
        recommendations = []
        vuln_lower = vulnerability_type.lower()
        
        for vuln_key, tools in self.VULNERABILITY_POC_MAPPING.items():
            if vuln_key in vuln_lower:
                for tool_info in tools:
                    recommendation = ToolRecommendation(
                        tool_name=tool_info["name"],
                        priority=tool_info["priority"] + base_priority,
                        confidence=min(0.85, tool_info["priority"] / 100),
                        source=RecommendationSource.VULNERABILITY_BASED,
                        reason=tool_info["reason"],
                        metadata={"vulnerability_type": vulnerability_type, "matched_key": vuln_key}
                    )
                    recommendations.append(recommendation)
                break
        
        logger.debug(f"漏洞类型 {vulnerability_type} 推荐 {len(recommendations)} 个工具")
        return recommendations
    
    def recommend_for_target(
        self,
        profile: TargetProfile,
        use_llm: bool = False
    ) -> List[ToolRecommendation]:
        """
        为目标生成综合工具推荐
        
        根据目标画像综合分析,生成最优工具推荐列表。
        
        Args:
            profile: 目标画像
            use_llm: 是否使用LLM增强决策
            
        Returns:
            List[ToolRecommendation]: 排序后的推荐工具列表
        """
        all_recommendations: Dict[str, ToolRecommendation] = {}
        
        for port in profile.ports:
            port_recs = self.recommend_by_port(port)
            for rec in port_recs:
                if rec.tool_name in all_recommendations:
                    existing = all_recommendations[rec.tool_name]
                    existing.priority = max(existing.priority, rec.priority)
                    existing.confidence = max(existing.confidence, rec.confidence)
                else:
                    all_recommendations[rec.tool_name] = rec
        
        if profile.cms:
            cms_recs = self.recommend_by_cms(profile.cms)
            for rec in cms_recs:
                if rec.tool_name in all_recommendations:
                    existing = all_recommendations[rec.tool_name]
                    existing.priority = min(100, existing.priority + 10)
                    existing.confidence = min(1.0, existing.confidence + 0.1)
                    existing.reason = f"{existing.reason}; CMS匹配增强"
                else:
                    all_recommendations[rec.tool_name] = rec
        
        for vuln in profile.vulnerabilities:
            vuln_recs = self.recommend_by_vulnerability(vuln)
            for rec in vuln_recs:
                if rec.tool_name in all_recommendations:
                    existing = all_recommendations[rec.tool_name]
                    existing.priority = min(100, existing.priority + 5)
                    existing.confidence = min(1.0, existing.confidence + 0.05)
                else:
                    all_recommendations[rec.tool_name] = rec
        
        for tech in profile.technologies:
            tech_recs = self.recommend_by_cms(tech)
            for rec in tech_recs:
                if rec.tool_name in all_recommendations:
                    existing = all_recommendations[rec.tool_name]
                    existing.priority = min(100, existing.priority + 3)
                else:
                    rec.priority = max(50, rec.priority - 20)
                    all_recommendations[rec.tool_name] = rec
        
        if use_llm and self.llm_client:
            llm_recs = self._llm_enhanced_recommendation(profile, all_recommendations)
            for rec in llm_recs:
                if rec.tool_name in all_recommendations:
                    existing = all_recommendations[rec.tool_name]
                    existing.priority = min(100, existing.priority + 15)
                    existing.source = RecommendationSource.LLM_ENHANCED
                else:
                    all_recommendations[rec.tool_name] = rec
        
        sorted_recommendations = sorted(
            all_recommendations.values(),
            key=lambda x: (x.priority, x.confidence),
            reverse=True
        )
        
        self._recommendation_cache[profile.target] = sorted_recommendations
        
        logger.info(f"目标 {profile.target} 共推荐 {len(sorted_recommendations)} 个工具")
        return sorted_recommendations
    
    def _llm_enhanced_recommendation(
        self,
        profile: TargetProfile,
        existing_recommendations: Dict[str, ToolRecommendation]
    ) -> List[ToolRecommendation]:
        """
        LLM增强推荐
        
        使用大语言模型分析目标特征,提供更智能的工具推荐。
        
        Args:
            profile: 目标画像
            existing_recommendations: 现有推荐结果
            
        Returns:
            List[ToolRecommendation]: LLM增强后的推荐列表
        """
        if not self.llm_client:
            return []
        
        try:
            prompt = self._build_llm_prompt(profile, existing_recommendations)
            
            llm_recommendations = []
            
            logger.debug(f"LLM增强推荐完成,新增 {len(llm_recommendations)} 个推荐")
            return llm_recommendations
            
        except Exception as e:
            logger.error(f"LLM增强推荐失败: {str(e)}")
            return []
    
    def _build_llm_prompt(
        self,
        profile: TargetProfile,
        existing_recommendations: Dict[str, ToolRecommendation]
    ) -> str:
        """
        构建LLM提示词
        
        Args:
            profile: 目标画像
            existing_recommendations: 现有推荐结果
            
        Returns:
            str: 构建的提示词
        """
        existing_tools = [name for name in existing_recommendations.keys()]
        
        prompt = f"""
请分析以下目标特征,推荐最适合的安全扫描工具:

目标信息:
- 地址: {profile.target}
- 开放端口: {profile.ports}
- CMS类型: {profile.cms or '未知'}
- 技术栈: {profile.technologies}
- 已知漏洞: {profile.vulnerabilities}

已推荐工具: {existing_tools}

请根据以上信息,推荐额外的安全检测工具,并说明推荐理由。
"""
        return prompt.strip()
    
    def get_top_recommendations(
        self,
        profile: TargetProfile,
        top_n: int = 5,
        use_llm: bool = False
    ) -> List[ToolRecommendation]:
        """
        获取Top N推荐工具
        
        Args:
            profile: 目标画像
            top_n: 返回数量
            use_llm: 是否使用LLM增强
            
        Returns:
            List[ToolRecommendation]: Top N推荐工具列表
        """
        all_recommendations = self.recommend_for_target(profile, use_llm)
        return all_recommendations[:top_n]
    
    def filter_by_registry(
        self,
        recommendations: List[ToolRecommendation]
    ) -> List[ToolRecommendation]:
        """
        过滤掉注册表中不存在的工具
        
        Args:
            recommendations: 原始推荐列表
            
        Returns:
            List[ToolRecommendation]: 过滤后的推荐列表
        """
        if not self.registry:
            logger.warning("工具注册表未设置,跳过过滤")
            return recommendations
        
        filtered = [
            rec for rec in recommendations
            if self.registry.has_tool(rec.tool_name)
        ]
        
        if len(filtered) < len(recommendations):
            missing = [rec.tool_name for rec in recommendations if rec not in filtered]
            logger.debug(f"过滤掉 {len(recommendations) - len(filtered)} 个未注册工具: {missing}")
        
        return filtered
    
    def get_recommendation_summary(
        self,
        recommendations: List[ToolRecommendation]
    ) -> Dict[str, Any]:
        """
        获取推荐结果摘要
        
        Args:
            recommendations: 推荐列表
            
        Returns:
            Dict[str, Any]: 摘要信息
        """
        if not recommendations:
            return {
                "total": 0,
                "by_source": {},
                "avg_priority": 0,
                "avg_confidence": 0.0
            }
        
        by_source: Dict[str, int] = {}
        total_priority = 0
        total_confidence = 0.0
        
        for rec in recommendations:
            source_key = rec.source.value
            by_source[source_key] = by_source.get(source_key, 0) + 1
            total_priority += rec.priority
            total_confidence += rec.confidence
        
        return {
            "total": len(recommendations),
            "by_source": by_source,
            "avg_priority": round(total_priority / len(recommendations), 2),
            "avg_confidence": round(total_confidence / len(recommendations), 3),
            "top_tools": [rec.tool_name for rec in recommendations[:5]]
        }
    
    def add_custom_port_mapping(
        self,
        port: int,
        tools: List[Dict[str, Any]]
    ) -> None:
        """
        添加自定义端口映射
        
        Args:
            port: 端口号
            tools: 工具列表,每个元素包含name、priority、reason字段
        """
        if port in self.PORT_POC_MAPPING:
            self.PORT_POC_MAPPING[port].extend(tools)
            logger.info(f"扩展端口 {port} 的工具映射,新增 {len(tools)} 个工具")
        else:
            self.PORT_POC_MAPPING[port] = tools
            logger.info(f"添加端口 {port} 的工具映射,共 {len(tools)} 个工具")
    
    def add_custom_cms_mapping(
        self,
        cms: str,
        tools: List[Dict[str, Any]]
    ) -> None:
        """
        添加自定义CMS映射
        
        Args:
            cms: CMS名称
            tools: 工具列表
        """
        cms_lower = cms.lower()
        if cms_lower in self.CMS_POC_MAPPING:
            self.CMS_POC_MAPPING[cms_lower].extend(tools)
            logger.info(f"扩展CMS {cms} 的工具映射,新增 {len(tools)} 个工具")
        else:
            self.CMS_POC_MAPPING[cms_lower] = tools
            logger.info(f"添加CMS {cms} 的工具映射,共 {len(tools)} 个工具")
    
    def clear_cache(self) -> None:
        """清空推荐缓存"""
        self._recommendation_cache.clear()
        logger.info("推荐缓存已清空")


def create_target_profile(
    target: str,
    ports: Optional[List[int]] = None,
    cms: Optional[str] = None,
    technologies: Optional[List[str]] = None,
    vulnerabilities: Optional[List[str]] = None,
    services: Optional[Dict[int, Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> TargetProfile:
    """
    创建目标画像的便捷函数
    
    Args:
        target: 目标地址
        ports: 开放端口列表
        cms: CMS类型
        technologies: 技术栈列表
        vulnerabilities: 已知漏洞列表
        services: 服务信息
        metadata: 额外元数据
        
    Returns:
        TargetProfile: 目标画像实例
    """
    return TargetProfile(
        target=target,
        ports=ports or [],
        cms=cms,
        technologies=technologies or [],
        vulnerabilities=vulnerabilities or [],
        services=services or {},
        metadata=metadata or {}
    )


async def get_recommended_tools(
    target: str,
    ports: Optional[List[int]] = None,
    cms: Optional[str] = None,
    top_n: int = 5,
    use_llm: bool = False
) -> List[Dict[str, Any]]:
    """
    获取推荐工具的异步便捷函数
    
    Args:
        target: 目标地址
        ports: 开放端口列表
        cms: CMS类型
        top_n: 返回数量
        use_llm: 是否使用LLM增强
        
    Returns:
        List[Dict[str, Any]]: 推荐工具列表(字典格式)
    """
    recommender = ToolRecommender()
    profile = create_target_profile(
        target=target,
        ports=ports,
        cms=cms
    )
    
    recommendations = recommender.get_top_recommendations(
        profile,
        top_n=top_n,
        use_llm=use_llm
    )
    
    return [rec.to_dict() for rec in recommendations]

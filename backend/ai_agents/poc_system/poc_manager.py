"""
POC 脚本管理器

负责 POC 脚本的管理,包括从 Seebug 同步、本地加载、版本控制等。
使用Seebug_Agent的SeebugClient和SeebugAgent实现。
"""
import logging
from pathlib import Path

from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.config import settings
from backend.models import POCVerificationTask
from backend.utils.seebug_utils import seebug_utils
from backend.ai_agents.utils.cache import CacheManager
from backend.utils.poc_utils import validate_poc_script_code
from backend.Pocsuite3Agent.agent import get_pocsuite3_agent

logger = logging.getLogger(__name__)


class POCMetadata:
    """
    POC 元数据类
    
    用于存储 POC 的元信息,包括名称、类型、严重度等。
    """
    
    def __init__(
        self,
        poc_name: str,
        poc_id: str,
        poc_type: str = "web",
        severity: str = "medium",
        cvss_score: Optional[float] = None,
        description: Optional[str] = None,
        author: Optional[str] = None,
        source: str = "seebug",
        version: str = "1.0",
        tags: List[str] = None
    ):
        self.poc_name = poc_name
        self.poc_id = poc_id
        self.poc_type = poc_type
        self.severity = severity
        self.cvss_score = cvss_score
        self.description = description
        self.author = author
        self.source = source
        self.version = version
        self.tags = tags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict: 包含所有元信息的字典
        """
        return {
            "poc_name": self.poc_name,
            "poc_id": self.poc_id,
            "poc_type": self.poc_type,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "description": self.description,
            "author": self.author,
            "source": self.source,
            "version": self.version,
            "tags": self.tags
        }


class POCManager:
    """
    POC 管理器类
    
    负责管理 POC 脚本的生命周期,包括:
    - 从 Seebug 同步 POC
    - 本地自定义 POC 脚本加载
    - POC 版本控制
    - POC 缓存管理
    - POC 元数据管理
    """
    
    def __init__(self):
        """
        初始化 POC 管理器
        """
        self.poc_registry: Dict[str, POCMetadata] = {}
        self.generated_poc_codes: Dict[str, str] = {}  # Store generated POC codes
        self.poc_cache = CacheManager(ttl=settings.POC_CACHE_TTL)
        
        # 使用统一的Seebug工具
        self.seebug_client = seebug_utils.get_client()
        self.seebug_agent = seebug_utils.get_agent()
        
        # 使用 Pocsuite3 Agent
        self.pocsuite3_agent = get_pocsuite3_agent()
        
        logger.info("✅ POC 管理器初始化完成")

    def register_dynamic_poc(self, poc_id: str, code: str):
        """Register a dynamically generated POC code"""
        self.generated_poc_codes[poc_id] = code
        # Also create metadata
        self.poc_registry[poc_id] = POCMetadata(
            poc_name="Dynamic POC",
            poc_id=poc_id,
            source="generated",
            description="Dynamically generated POC"
        )
    
    async def get_poc_code(self, poc_id: str) -> Optional[str]:
        """Get POC code by ID (checks dynamic first, then seebug)"""
        if poc_id in self.generated_poc_codes:
            return self.generated_poc_codes[poc_id]
        
        return await self.download_poc_from_seebug(poc_id)

    async def sync_from_seebug(
        self,
        keyword: str = "",
        limit: int = 100,
        force_refresh: bool = False
    ) -> List[POCMetadata]:
        """
        从 Seebug 同步 POC
        
        Args:
            keyword: 搜索关键词,为空时同步所有 POC
            limit: 同步数量限制
            force_refresh: 是否强制刷新缓存
            
        Returns:
            List[POCMetadata]: POC 元数据列表
        """
        try:
            logger.info(f"🔍 开始从 Seebug 同步 POC,关键词: {keyword}, 限制: {limit}")
            
            # 检查缓存
            cache_key = f"seebug_{keyword}_{limit}"
            cached_pocs = self.poc_cache.get(cache_key)
            if cached_pocs:
                logger.info(f"✅ 使用缓存数据,缓存年龄: {self.poc_cache.get_age(cache_key):.2f}秒")
                return cached_pocs
            
            # 使用Seebug_Agent的客户端搜索POC
            search_result = self.seebug_client.search_poc(keyword, page=1, page_size=limit)
            
            if search_result.get("status") != "success":
                return []
            
            poc_list = search_result.get("data", {}).get("list", [])
            
            if not poc_list:
                return []
            
            # 转换为 POC 元数据
            poc_metadata_list = []
            for poc_item in poc_list:
                metadata = POCMetadata(
                    poc_name=poc_item.get("name", ""),
                    poc_id=str(poc_item.get("ssvid", "")),
                    poc_type=poc_item.get("type", "web"),
                    severity=poc_item.get("severity", "medium"),
                    cvss_score=poc_item.get("cvss_score"),
                    description=poc_item.get("description"),
                    author=poc_item.get("author"),
                    source="seebug",
                    version="1.0",
                    tags=poc_item.get("tags", [])
                )
                poc_metadata_list.append(metadata)
                
                # 注册到 POC 注册表
                self.poc_registry[metadata.poc_id] = metadata
            
            # 更新缓存
            self.poc_cache.set(cache_key, poc_metadata_list)
            
            logger.info(f"✅ 从 Seebug 同步完成,获取 {len(poc_metadata_list)} 个 POC")
            return poc_metadata_list
            
        except Exception as e:
            logger.error(f"❌ 从 Seebug 同步 POC 失败: {str(e)}")
            return []
    
    async def download_poc_from_seebug(self, ssvid: int) -> Optional[str]:
        """
        从 Seebug 下载 POC 代码
        
        Args:
            ssvid: POC 的 SSVID
            
        Returns:
            Optional[str]: POC 代码,失败返回 None
        """
        try:
            logger.info(f"📥 开始从 Seebug 下载 POC,SSVID: {ssvid}")
            
            # 检查缓存
            cache_key = f"poc_code_{ssvid}"
            cached_code = self.poc_cache.get(cache_key)
            if cached_code:
                return cached_code["code"] if isinstance(cached_code, dict) else cached_code
            
            # 使用Seebug_Agent的客户端下载POC
            download_result = self.seebug_client.download_poc(ssvid)
            
            if download_result.get("status") != "success":
                logger.warning(f"⚠️ 从 Seebug 下载 POC 失败,SSVID: {ssvid}")
                return None
            
            poc_code = download_result.get("data", {}).get("poc", "")
            
            if not poc_code:
                logger.warning(f"⚠️ 从 Seebug 下载 POC 失败,SSVID: {ssvid}")
                return None
            
            # 更新缓存
            self.poc_cache.set(cache_key, poc_code)
            
            logger.info(f"✅ 从 Seebug 下载 POC 完成,代码长度: {len(poc_code)}")
            return poc_code
            
        except Exception as e:
            logger.error(f"❌ 从 Seebug 下载 POC 失败: {str(e)}")
            return None
    
    async def load_local_poc(self, poc_path: str) -> Optional[POCMetadata]:
        """
        加载本地自定义 POC 脚本
        
        Args:
            poc_path: POC 文件路径
            
        Returns:
            Optional[POCMetadata]: POC 元数据,失败返回 None
        """
        try:
            logger.info(f"📂 开始加载本地 POC,路径: {poc_path}")
            
            path = Path(poc_path)
            if not path.exists():
                logger.warning(f"⚠️ POC 文件不存在: {poc_path}")
                return None
            
            # 读取 POC 文件
            with open(path, 'r', encoding='utf-8') as f:
                poc_code = f.read()
            
            # 解析 POC 元数据(从注释中提取)
            poc_name = path.stem
            poc_id = f"local_{poc_name}"
            
            metadata = POCMetadata(
                poc_name=poc_name,
                poc_id=poc_id,
                poc_type="local",
                severity="medium",
                description=f"本地自定义 POC: {poc_name}",
                source="local",
                version="1.0",
                tags=["custom"]
            )
            
            # 注册到 POC 注册表
            self.poc_registry[metadata.poc_id] = metadata
            
            logger.info(f"✅ 加载本地 POC 完成: {poc_name}")
            return metadata
            
        except Exception as e:
            logger.error(f"❌ 加载本地 POC 失败: {str(e)}")
            return None
    
    async def load_local_pocs_from_directory(
        self,
        directory: str = None,
        pattern: str = "*.py"
    ) -> List[POCMetadata]:
        """
        从目录批量加载本地 POC 脚本
        
        Args:
            directory: POC 目录路径，默认为 backend/poc
            pattern: 文件匹配模式
            
        Returns:
            List[POCMetadata]: POC 元数据列表
        """
        try:
            # 如果未指定目录，使用 backend/poc
            if not directory:
                import os
                directory = str(Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))/"poc")
            
            logger.info(f"📂 开始从目录加载 POC,路径: {directory}, 模式: {pattern}")
            
            dir_path = Path(directory)
            if not dir_path.exists():
                logger.warning(f"⚠️ 目录不存在: {directory}")
                return []
            
            # 遍历目录加载 POC
            poc_metadata_list = []
            for poc_file in dir_path.glob(pattern):
                metadata = await self.load_local_poc(str(poc_file))
                if metadata:
                    poc_metadata_list.append(metadata)
            
            # 遍历子目录
            for subdir in dir_path.iterdir():
                if subdir.is_dir() and not subdir.name.startswith('.') and subdir.name not in ['__pycache__']:
                    for poc_file in subdir.glob(pattern):
                        metadata = await self.load_local_poc(str(poc_file))
                        if metadata:
                            poc_metadata_list.append(metadata)
            
            logger.info(f"✅ 从目录加载 POC 完成,获取 {len(poc_metadata_list)} 个 POC")
            return poc_metadata_list
            
        except Exception as e:
            logger.error(f"❌ 从目录加载 POC 失败: {str(e)}")
            return []
    
    def get_poc_metadata(self, poc_id: str) -> Optional[POCMetadata]:
        """
        获取 POC 元数据
        
        Args:
            poc_id: POC ID
            
        Returns:
            Optional[POCMetadata]: POC 元数据,不存在返回 None
        """
        return self.poc_registry.get(poc_id)
    
    def get_all_pocs(self) -> List[POCMetadata]:
        """
        获取所有已注册的 POC
        
        Returns:
            List[POCMetadata]: 所有 POC 元数据列表
        """
        return list(self.poc_registry.values())
    
    def get_pocs_by_type(self, poc_type: str) -> List[POCMetadata]:
        """
        按类型获取 POC
        
        Args:
            poc_type: POC 类型
            
        Returns:
            List[POCMetadata]: 指定类型的 POC 列表
        """
        return [
            poc for poc in self.poc_registry.values()
            if poc.poc_type == poc_type
        ]
    
    def get_pocs_by_severity(self, severity: str) -> List[POCMetadata]:
        """
        按严重度获取 POC
        
        Args:
            severity: 严重度(critical, high, medium, low, info)
            
        Returns:
            List[POCMetadata]: 指定严重度的 POC 列表
        """
        return [
            poc for poc in self.poc_registry.values()
            if poc.severity == severity
        ]
    
    def update_poc_version(self, poc_id: str, new_version: str):
        """
        更新 POC 版本
        
        Args:
            poc_id: POC ID
            new_version: 新版本号
        """
        if poc_id in self.poc_registry:
            self.poc_registry[poc_id].version = new_version
            logger.info(f"✅ 更新 POC 版本: {poc_id} -> {new_version}")
        else:
            logger.warning(f"⚠️ POC 不存在: {poc_id}")
    
    def clear_cache(self):
        """
        清除 POC 缓存
        """
        self.poc_cache.clear()
        logger.info("✅ POC 缓存已清除")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 包含缓存统计信息的字典
        """
        return {
            "poc_count": len(self.poc_registry),
            "cache_entries": len(self.poc_cache),
            "cache_size_mb": sum(
                len(str(poc)) for poc in self.poc_cache.values()
            ) / (1024 * 1024)
        }
    
    def validate_poc_script(self, poc_code: str) -> Dict[str, Any]:
        """
        验证POC脚本是否符合pocsuite3标准格式
        
        Args:
            poc_code: POC脚本代码
            
        Returns:
            Dict[str, Any]: 验证结果，包含is_valid和错误信息
        """
        try:
            logger.info("🔍 开始验证POC脚本格式")
            
            # 使用统一的验证函数
            validation_result = validate_poc_script_code(poc_code)
            
            if validation_result["is_valid"]:
                logger.info("✅ POC脚本格式验证通过")
            else:
                logger.warning(f"⚠️ POC脚本格式验证失败: {validation_result['errors']}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ POC脚本验证失败: {str(e)}")
            return {
                "is_valid": False,
                "errors": [f"验证过程出错: {str(e)}"]
            }
    
    async def create_verification_task(
        self,
        poc_id: str,
        target: str,
        priority: int = 5,
        task_id: Optional[str] = None
    ) -> POCVerificationTask:
        """
        创建 POC 验证任务
        
        Args:
            poc_id: POC ID
            target: 验证目标
            priority: 优先级
            task_id: 关联的任务 ID
            
        Returns:
            POCVerificationTask: 创建的验证任务
        """
        try:
            # 获取 POC 元数据
            poc_metadata = self.get_poc_metadata(poc_id)
            if not poc_metadata:
                raise ValueError(f"POC 不存在: {poc_id}")
            
            # 创建验证任务
            verification_task = await POCVerificationTask.create(
                task_id=task_id,
                poc_name=poc_metadata.poc_name,
                poc_id=poc_id,
                target=target,
                priority=priority,
                status="pending",
                progress=0,
                config={
                    "poc_metadata": poc_metadata.to_dict(),
                    "source": poc_metadata.source
                }
            )
            
            logger.info(f"✅ 创建 POC 验证任务: {poc_metadata.poc_name} -> {target}")
            return verification_task
            
        except Exception as e:
            logger.error(f"❌ 创建 POC 验证任务失败: {str(e)}")
            raise
    
    def register_generated_poc(self, poc_id: str, code: str, metadata: POCMetadata):
        """
        注册生成的 POC
        
        Args:
            poc_id: POC ID
            code: POC 代码
            metadata: POC 元数据
        """
        self.poc_registry[poc_id] = metadata
        self.generated_poc_codes[poc_id] = code
        logger.info(f"✅ 注册生成的 POC: {poc_id}")

    async def get_poc_code(self, poc_id: str) -> Optional[str]:
        """
        获取 POC 代码
        
        Args:
            poc_id: POC ID
            
        Returns:
            Optional[str]: POC 代码
        """
        # Check generated POCs first
        if poc_id in self.generated_poc_codes:
            return self.generated_poc_codes[poc_id]

        # 检查缓存
        cache_key = f"poc_code_{poc_id}"
        cached_code = self.poc_cache.get(cache_key)
        if cached_code:
            return cached_code
        
        # 如果是本地 POC,从文件读取
        if poc_id.startswith("local_"):
            poc_name = poc_id.replace("local_", "")
            # 从 backend/poc 目录读取
            import os
            local_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))/"poc"/f"{poc_name}.py"
            if local_path.exists():
                with open(local_path, 'r', encoding='utf-8') as f:
                    return f.read()

        # 如果是 Pocsuite3 POC,从注册表获取路径并读取
        if poc_id.startswith("pocsuite3_"):
            poc_name = poc_id.replace("pocsuite3_", "")
            poc_path = self.pocsuite3_agent.poc_registry.get(poc_name)
            if poc_path and Path(poc_path).exists():
                try:
                    with open(poc_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"读取 Pocsuite3 POC 失败: {str(e)}")
                    return None
        
        # 如果是 Seebug POC,从缓存或重新下载
        ssvid = poc_id.replace("seebug_", "")
        try:
            return await self.download_poc_from_seebug(int(ssvid))
        except (ValueError, TypeError):
            return None
    
    async def search_pocsuite_pocs(
        self,
        keyword: str,
        limit: int = 10
    ) -> List[POCMetadata]:
        """
        搜索 Pocsuite3 内置 POC
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            List[POCMetadata]: POC 元数据列表
        """
        try:
            logger.info(f"🔍 开始搜索 Pocsuite3 POC,关键词: {keyword}")
            
            # 使用 Pocsuite3 Agent 搜索
            poc_names = self.pocsuite3_agent.search_pocs(keyword)
            
            if not poc_names:
                return []
                
            # 限制返回数量
            poc_names = poc_names[:limit]
            
            # 转换为 POC 元数据
            poc_metadata_list = []
            for name in poc_names:
                # 尝试从文件内容或名称推断信息
                # 这里简化处理，主要使用名称
                poc_id = f"pocsuite3_{name}"
                
                metadata = POCMetadata(
                    poc_name=name,
                    poc_id=poc_id,
                    poc_type="web", # 默认为web
                    severity="high", # 默认设为高危，因为通常内置POC针对已知漏洞
                    source="pocsuite3",
                    version="1.0",
                    tags=["pocsuite3"]
                )
                poc_metadata_list.append(metadata)
                
                # 注册到 POC 注册表
                self.poc_registry[poc_id] = metadata
                
            logger.info(f"✅ Pocsuite3 POC搜索成功,找到 {len(poc_metadata_list)} 个POC")
            return poc_metadata_list
            
        except Exception as e:
            logger.error(f"❌ Pocsuite3 POC搜索失败: {str(e)}")
            return []

    async def search_seebug_pocs(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 10
    ) -> List[POCMetadata]:
        """
        基于关键词搜索Seebug POC
        
        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            List[POCMetadata]: POC 元数据列表
        """
        try:
            logger.info(f"🔍 开始搜索Seebug POC,关键词: {keyword}, 页码: {page}, 每页: {page_size}")
            
            # 检查缓存
            cache_key = f"search_{keyword}_{page}_{page_size}"
            if cache_key in self.poc_cache:
                cache_time = self.poc_cache[cache_key]["timestamp"]
                cache_age = (datetime.now() - cache_time).total_seconds()
                
                if cache_age < settings.POC_CACHE_TTL:
                    logger.info(f"✅ 使用缓存数据,缓存年龄: {cache_age}秒")
                    return self.poc_cache[cache_key]["pocs"]
            
            # 使用Seebug_Agent搜索POC
            search_result = self.seebug_client.search_poc(keyword, page, page_size)
            
            if search_result.get("status") != "success":
                return []
            
            poc_list = search_result.get("data", {}).get("list", [])
            
            if not poc_list:
                return []
            
            # 转换为 POC 元数据
            poc_metadata_list = []
            for poc_item in poc_list:
                metadata = POCMetadata(
                    poc_name=poc_item.get("name", ""),
                    poc_id=f"seebug_{poc_item.get('ssvid', '')}",
                    poc_type=poc_item.get("type", "web"),
                    severity=poc_item.get("severity", "medium"),
                    cvss_score=poc_item.get("cvss_score"),
                    description=poc_item.get("description"),
                    author=poc_item.get("author"),
                    source="seebug",
                    version="1.0",
                    tags=poc_item.get("tags", [])
                )
                poc_metadata_list.append(metadata)
                
                # 注册到 POC 注册表
                self.poc_registry[metadata.poc_id] = metadata
            
            # 更新缓存
            self.poc_cache.set(cache_key, poc_metadata_list)
            
            logger.info(f"✅ Seebug POC搜索成功,找到 {len(poc_metadata_list)} 个POC")
            return poc_metadata_list
            
        except Exception as e:
            logger.error(f"❌ Seebug POC搜索失败: {str(e)}")
            return []
    
    async def generate_poc_from_seebug(
        self,
        ssvid: str,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        从Seebug生成POC代码
        
        Args:
            ssvid: 漏洞的SSVID
            save: 是否保存到本地
            
        Returns:
            Dict[str, Any]: 包含POC代码和信息的字典
        """
        try:
            logger.info(f"🤖 开始从Seebug生成POC,SSVID: {ssvid}")
            
            # 生成并保存POC
            result = self.seebug_agent.generate_and_save_poc(ssvid)
            
            if result.get("success"):
                poc_path = result.get("poc_path")
                vulnerability = result.get("vulnerability", {})
                
                # 读取生成的POC代码
                with open(poc_path, 'r', encoding='utf-8') as f:
                    poc_code = f.read()
                
                # 创建POC元数据
                metadata = POCMetadata(
                    poc_name=vulnerability.get("name", f"SSVID-{ssvid}"),
                    poc_id=f"seebug_{ssvid}",
                    poc_type=vulnerability.get("type", "web"),
                    severity=vulnerability.get("severity", "medium"),
                    cvss_score=vulnerability.get("cvss_score"),
                    description=vulnerability.get("description"),
                    author="AI Generated",
                    source="seebug_ai",
                    version="1.0",
                    tags=["ai_generated", "seebug"]
                )
                
                # 注册到 POC 注册表
                self.poc_registry[metadata.poc_id] = metadata
                
                # 更新缓存
                cache_key = f"poc_code_seebug_{ssvid}"
                self.poc_cache[cache_key] = {
                    "timestamp": datetime.now(),
                    "code": poc_code
                }
                
                logger.info(f"✅ POC生成成功,保存路径: {poc_path}")
                return {
                    "success": True,
                    "poc_code": poc_code,
                    "poc_path": poc_path,
                    "metadata": metadata.to_dict()
                }
            else:
                logger.warning(f"⚠️ POC生成失败: {result.get('message')}")
                return {
                    "success": False,
                    "message": result.get("message", "生成失败")
                }
                
        except Exception as e:
            logger.error(f"❌ 从Seebug生成POC失败: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }
    
    async def batch_sync_from_seebug(
        self,
        keywords: List[str],
        limit_per_keyword: int = 10
    ) -> List[POCMetadata]:
        """
        批量从Seebug同步POC
        
        Args:
            keywords: 关键词列表
            limit_per_keyword: 每个关键词的同步数量限制
            
        Returns:
            List[POCMetadata]: POC 元数据列表
        """
        try:
            logger.info(f"🔍 开始批量同步Seebug POC,关键词数量: {len(keywords)}")
            
            all_pocs = []
            
            for keyword in keywords:
                pocs = await self.sync_from_seebug(keyword, limit_per_keyword)
                all_pocs.extend(pocs)
            
            logger.info(f"✅ 批量同步完成,共获取 {len(all_pocs)} 个POC")
            return all_pocs
            
        except Exception as e:
            logger.error(f"❌ 批量同步Seebug POC失败: {str(e)}")
            return []


# 全局 POC 管理器实例
poc_manager = POCManager()

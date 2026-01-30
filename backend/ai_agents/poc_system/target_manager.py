"""
目标信息管理器

负责目标信息的管理,包括批量导入、单个输入、去重验证、分组管理等功能。
"""
import logging
from typing import Optional, Dict, Any, List


logger = logging.getLogger(__name__)


class TargetInfo:
    """
    目标信息类
    
    用于存储单个目标的详细信息。
    """
    
    def __init__(
        self,
        url: str,
        target_type: str = "web",
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.url = url
        self.target_type = target_type
        self.priority = priority
        self.metadata = metadata or {}
    
    def is_valid(self) -> bool:
        """
        验证目标是否有效
        
        Returns:
            bool: 目标是否有效
        """
        if not self.url:
            return False
        
        try:
            result = urlparse(self.url)
            return bool(result.scheme and result.netloc)
        except Exception:
            return False
    
    def get_domain(self) -> Optional[str]:
        """
        获取目标域名
        
        Returns:
            Optional[str]: 域名,无法解析返回 None
        """
        try:
            result = urlparse(self.url)
            return result.netloc
        except Exception:
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict: 包含所有目标信息的字典
        """
        return {
            "url": self.url,
            "target_type": self.target_type,
            "priority": self.priority,
            "metadata": self.metadata,
            "domain": self.get_domain(),
            "is_valid": self.is_valid()
        }


class TargetManager:
    """
    目标管理器类
    
    负责管理目标信息,包括:
    - 批量导入目标
    - 单个目标输入
    - 目标去重和验证
    - 目标分组管理
    """
    
    def __init__(self):
        """
        初始化目标管理器
        """
        self.targets: Dict[str, TargetInfo] = {}
        self.target_groups: Dict[str, List[str]] = {}
        
        logger.info("✅ 目标管理器初始化完成")
    
    async def import_targets_from_csv(
        self,
        file_path: str,
        encoding: str = "utf-8"
    ) -> List[TargetInfo]:
        """
        从 CSV 文件批量导入目标
        
        Args:
            file_path: CSV 文件路径
            encoding: 文件编码
            
        Returns:
            List[TargetInfo]: 目标信息列表
        """
        try:
            logger.info(f"📥 开始从 CSV 导入目标,路径: {file_path}")
            
            targets = []
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    url = row.get("url", "").strip()
                    if not url:
                        continue
                    
                    target_type = row.get("type", "web").strip()
                    priority = int(row.get("priority", "5").strip() or "5")
                    
                    metadata = {
                        "name": row.get("name", ""),
                        "description": row.get("description", ""),
                        "tags": row.get("tags", "").split(",") if row.get("tags") else []
                    }
                    
                    target_info = TargetInfo(
                        url=url,
                        target_type=target_type,
                        priority=priority,
                        metadata=metadata
                    )
                    
                    targets.append(target_info)
            
            logger.info(f"✅ 从 CSV 导入完成,获取 {len(targets)} 个目标")
            return targets
            
        except Exception as e:
            logger.error(f"❌ 从 CSV 导入目标失败: {str(e)}")
            return []
    
    async def import_targets_from_json(
        self,
        file_path: str,
        encoding: str = "utf-8"
    ) -> List[TargetInfo]:
        """
        从 JSON 文件批量导入目标
        
        Args:
            file_path: JSON 文件路径
            encoding: 文件编码
            
        Returns:
            List[TargetInfo]: 目标信息列表
        """
        try:
            logger.info(f"📥 开始从 JSON 导入目标,路径: {file_path}")
            
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
                
            targets = []
            for item in data:
                url = item.get("url", "").strip()
                if not url:
                    continue
                    
                target_type = item.get("type", "web").strip()
                priority = int(item.get("priority", "5").strip() or "5")
                metadata = item.get("metadata", {})
                
                target_info = TargetInfo(
                    url=url,
                    target_type=target_type,
                    priority=priority,
                    metadata=metadata
                )
                
                targets.append(target_info)
            
            logger.info(f"✅ 从 JSON 导入完成,获取 {len(targets)} 个目标")
            return targets
            
        except Exception as e:
            logger.error(f"❌ 从 JSON 导入目标失败: {str(e)}")
            return []
    
    async def import_targets_from_excel(
        self,
        file_path: str
    ) -> List[TargetInfo]:
        """
        从 Excel 文件批量导入目标
        
        Args:
            file_path: Excel 文件路径
            
        Returns:
            List[TargetInfo]: 目标信息列表
        """
        try:
            logger.info(f"📥 开始从 Excel 导入目标,路径: {file_path}")
            
            try:
                import openpyxl
            except ImportError:
                logger.warning("⚠️ openpyxl 未安装,尝试使用 pandas")
                return await self._import_targets_from_excel_pandas(file_path)
            
            workbook = openpyxl.load_workbook(file_path)
            sheet = workbook.active
            
            targets = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                url = str(row[0]).strip() if row[0] else ""
                if not url:
                    continue
                    
                target_type = str(row[1]).strip() if row[1] else "web"
                priority = int(str(row[2]).strip() or "5") if row[2] else 5
                
                target_info = TargetInfo(
                    url=url,
                    target_type=target_type,
                    priority=priority
                )
                
                targets.append(target_info)
            
            logger.info(f"✅ 从 Excel 导入完成,获取 {len(targets)} 个目标")
            return targets
            
        except Exception as e:
            logger.error(f"❌ 从 Excel 导入目标失败: {str(e)}")
            return []
    
    async def _import_targets_from_excel_pandas(
        self,
        file_path: str
    ) -> List[TargetInfo]:
        """
        使用 pandas 从 Excel 导入目标
        
        Args:
            file_path: Excel 文件路径
            
        Returns:
            List[TargetInfo]: 目标信息列表
        """
        try:
            import pandas as pd
            
            df = pd.read_excel(file_path)
            
            targets = []
            for _, row in df.iterrows():
                url = str(row.get("url", "")).strip()
                if not url:
                    continue
                    
                target_type = str(row.get("type", "web")).strip()
                priority = int(str(row.get("priority", "5")).strip() or "5")
                
                target_info = TargetInfo(
                    url=url,
                    target_type=target_type,
                    priority=priority
                )
                
                targets.append(target_info)
            
            logger.info(f"✅ 使用 pandas 从 Excel 导入完成,获取 {len(targets)} 个目标")
            return targets
            
        except ImportError:
            logger.error("❌ pandas 未安装")
            return []
        except Exception as e:
            logger.error(f"❌ 使用 pandas 导入 Excel 失败: {str(e)}")
            return []
    
    async def add_single_target(
        self,
        url: str,
        target_type: str = "web",
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TargetInfo:
        """
        添加单个目标
        
        Args:
            url: 目标 URL
            target_type: 目标类型
            priority: 优先级
            metadata: 元数据
            
        Returns:
            TargetInfo: 目标信息对象
        """
        target_info = TargetInfo(
            url=url,
            target_type=target_type,
            priority=priority,
            metadata=metadata
        )
        
        self.targets[url] = target_info
        logger.info(f"✅ 添加单个目标: {url}")
        
        return target_info
    
    async def add_targets_from_agent_workflow(
        self,
        agent_state: Dict[str, Any]
    ) -> List[TargetInfo]:
        """
        从智能体工作流接收目标数据
        
        Args:
            agent_state: 智能体状态
            
        Returns:
            List[TargetInfo]: 目标信息列表
        """
        try:
            logger.info("🤖 开始从智能体工作流接收目标数据")
            
            targets = []
            
            # 从目标上下文提取目标
            target_context = agent_state.get("target_context", {})
            target = agent_state.get("target", "")
            
            if target:
                target_info = TargetInfo(
                    url=target,
                    target_type=target_context.get("target_type", "web"),
                    priority=target_context.get("priority", 5),
                    metadata={
                        "source": "agent_workflow",
                        "context": target_context
                    }
                )
                
                targets.append(target_info)
                self.targets[target] = target_info
            
            # 从漏洞列表提取目标
            vulnerabilities = agent_state.get("vulnerabilities", [])
            for vuln in vulnerabilities:
                if "target" in vuln:
                    target_url = vuln["target"]
                    if target_url and target_url not in self.targets:
                        target_info = TargetInfo(
                            url=target_url,
                            target_type="web",
                            priority=5,
                            metadata={
                                "source": "vulnerability_scan",
                                "vulnerability": vuln
                            }
                        )
                        
                        targets.append(target_info)
                        self.targets[target_url] = target_info
            
            logger.info(f"✅ 从智能体工作流接收目标完成,获取 {len(targets)} 个目标")
            return targets
            
        except Exception as e:
            logger.error(f"❌ 从智能体工作流接收目标失败: {str(e)}")
            return []
    
    async def deduplicate_targets(self) -> List[TargetInfo]:
        """
        目标去重
        
        Returns:
            List[TargetInfo]: 去重后的目标列表
        """
        logger.info(f"🔄 开始目标去重,当前目标数: {len(self.targets)}")
        
        seen_urls = set()
        unique_targets = []
        
        for target_info in self.targets.values():
            if target_info.url not in seen_urls:
                seen_urls.add(target_info.url)
                unique_targets.append(target_info)
        
        self.targets = {target.url: target for target in unique_targets}
        
        logger.info(f"✅ 目标去重完成,去重后: {len(unique_targets)} 个目标")
        return unique_targets
    
    async def validate_targets(self) -> Dict[str, Any]:
        """
        验证所有目标
        
        Returns:
            Dict: 包含验证结果的字典
        """
        logger.info(f"🔍 开始验证目标,目标数: {len(self.targets)}")
        
        valid_targets = []
        invalid_targets = []
        
        for target_info in self.targets.values():
            if target_info.is_valid():
                valid_targets.append(target_info)
            else:
                invalid_targets.append(target_info)
        
        result = {
            "total": len(self.targets),
            "valid": len(valid_targets),
            "invalid": len(invalid_targets),
            "valid_targets": [t.to_dict() for t in valid_targets],
            "invalid_targets": [t.to_dict() for t in invalid_targets]
        }
        
        logger.info(f"✅ 目标验证完成,有效: {result['valid']}, 无效: {result['invalid']}")
        return result
    
    async def create_target_group(
        self,
        group_name: str,
        target_urls: List[str]
    ) -> bool:
        """
        创建目标分组
        
        Args:
            group_name: 分组名称
            target_urls: 目标 URL 列表
            
        Returns:
            bool: 是否创建成功
        """
        try:
            logger.info(f"📁 创建目标分组: {group_name}, 目标数: {len(target_urls)}")
            
            valid_urls = []
            for url in target_urls:
                if url in self.targets:
                    valid_urls.append(url)
                else:
                    logger.warning(f"⚠️ 目标不存在: {url}")
            
            if not valid_urls:

                return False
            
            self.target_groups[group_name] = valid_urls
            
            logger.info(f"✅ 目标分组创建成功: {group_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建目标分组失败: {str(e)}")
            return False
    
    async def get_targets_by_priority(
        self,
        min_priority: int = 1,
        max_priority: int = 10
    ) -> List[TargetInfo]:
        """
        按优先级获取目标
        
        Args:
            min_priority: 最小优先级
            max_priority: 最大优先级
            
        Returns:
            List[TargetInfo]: 指定优先级的目标列表
        """
        return [
            target for target in self.targets.values()
            if min_priority <= target.priority <= max_priority
        ]
    
    async def get_targets_by_type(
        self,
        target_type: str
    ) -> List[TargetInfo]:
        """
        按类型获取目标
        
        Args:
            target_type: 目标类型
            
        Returns:
            List[TargetInfo]: 指定类型的目标列表
        """
        return [
            target for target in self.targets.values()
            if target.target_type == target_type
        ]
    
    async def get_all_targets(self) -> List[TargetInfo]:
        """
        获取所有目标
        
        Returns:
            List[TargetInfo]: 所有目标列表
        """
        return list(self.targets.values())
    
    async def remove_target(self, url: str) -> bool:
        """
        移除目标
        
        Args:
            url: 目标 URL
            
        Returns:
            bool: 是否移除成功
        """
        if url in self.targets:
            del self.targets[url]
            logger.info(f"✅ 移除目标: {url}")
            return True
        else:
            logger.warning(f"⚠️ 目标不存在: {url}")
            return False
    
    async def clear_all_targets(self):
        """
        清除所有目标
        """
        self.targets.clear()
        self.target_groups.clear()
        logger.info("✅ 清除所有目标")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取目标统计信息
        
        Returns:
            Dict: 包含统计信息的字典
        """
        targets = list(self.targets.values())
        
        type_counts = {}
        for target in targets:
            ttype = target.target_type
            type_counts[ttype] = type_counts.get(ttype, 0) + 1
        
        return {
            "total": len(targets),
            "by_type": type_counts,
            "groups": len(self.target_groups),
            "valid_count": sum(1 for t in targets if t.is_valid()),
            "invalid_count": sum(1 for t in targets if not t.is_valid())
        }


# 全局目标管理器实例
target_manager = TargetManager()

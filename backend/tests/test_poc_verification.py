"""
POC 验证系统单元测试

测试 POC 验证系统的各个模块,包括 POC 管理器、目标管理器、验证引擎、结果分析器和报告生成器。
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_agents.poc_system.poc_manager import POCManager, POCMetadata
from ai_agents.poc_system.target_manager import TargetManager, TargetInfo
from ai_agents.poc_system.result_analyzer import ResultAnalyzer
from ai_agents.poc_system.report_generator import ReportGenerator
from models import POCVerificationTask, POCVerificationResult


class TestPOCMetadata:
    """测试 POC 元数据类"""
    
    def test_poc_metadata_creation(self):
        """测试 POC 元数据创建"""
        metadata = POCMetadata(
            poc_name="Test POC",
            poc_id="test_poc_1",
            poc_type="web",
            severity="high",
            cvss_score=7.5,
            description="Test POC description",
            author="Test Author",
            source="seebug",
            version="1.0",
            tags=["sql", "injection"]
        )
        
        assert metadata.poc_name == "Test POC"
        assert metadata.poc_id == "test_poc_1"
        assert metadata.poc_type == "web"
        assert metadata.severity == "high"
        assert metadata.cvss_score == 7.5
        assert metadata.author == "Test Author"
        assert metadata.source == "seebug"
        assert metadata.version == "1.0"
        assert "sql" in metadata.tags
        assert "injection" in metadata.tags
    
    def test_poc_metadata_to_dict(self):
        """测试 POC 元数据转换为字典"""
        metadata = POCMetadata(
            poc_name="Test POC",
            poc_id="test_poc_1",
            poc_type="web",
            severity="medium"
        )
        
        metadata_dict = metadata.to_dict()
        
        assert isinstance(metadata_dict, dict)
        assert metadata_dict["poc_name"] == "Test POC"
        assert metadata_dict["poc_id"] == "test_poc_1"
        assert metadata_dict["poc_type"] == "web"
        assert metadata_dict["severity"] == "medium"


class TestPOCManager:
    """测试 POC 管理器"""
    
    @pytest.fixture
    async def poc_manager(self):
        """创建 POC 管理器实例"""
        return POCManager()
    
    async def test_poc_manager_initialization(self, poc_manager):
        """测试 POC 管理器初始化"""
        assert poc_manager is not None
        assert isinstance(poc_manager.poc_registry, dict)
        assert isinstance(poc_manager.poc_cache, dict)
        assert isinstance(poc_manager.poc_versions, dict)
    
    async def test_register_poc(self, poc_manager):
        """测试注册 POC"""
        metadata = POCMetadata(
            poc_name="Test POC",
            poc_id="test_poc_1",
            poc_type="web",
            severity="high"
        )
        
        poc_manager.poc_registry[metadata.poc_id] = metadata
        
        assert "test_poc_1" in poc_manager.poc_registry
        assert poc_manager.poc_registry["test_poc_1"] == metadata
    
    async def test_get_poc_metadata(self, poc_manager):
        """测试获取 POC 元数据"""
        metadata = POCMetadata(
            poc_name="Test POC",
            poc_id="test_poc_1",
            poc_type="web",
            severity="high"
        )
        
        poc_manager.poc_registry[metadata.poc_id] = metadata
        
        retrieved_metadata = poc_manager.get_poc_metadata("test_poc_1")
        
        assert retrieved_metadata is not None
        assert retrieved_metadata.poc_name == "Test POC"
    
    async def test_get_poc_by_type(self, poc_manager):
        """测试按类型获取 POC"""
        poc_manager.poc_registry["poc1"] = POCMetadata(
            poc_name="POC 1",
            poc_id="poc1",
            poc_type="web",
            severity="high"
        )
        poc_manager.poc_registry["poc2"] = POCMetadata(
            poc_name="POC 2",
            poc_id="poc2",
            poc_type="local",
            severity="medium"
        )
        
        web_pocs = poc_manager.get_pocs_by_type("web")
        
        assert len(web_pocs) == 1
        assert web_pocs[0].poc_id == "poc1"
    
    async def test_get_poc_by_severity(self, poc_manager):
        """测试按严重度获取 POC"""
        poc_manager.poc_registry["poc1"] = POCMetadata(
            poc_name="POC 1",
            poc_id="poc1",
            poc_type="web",
            severity="high"
        )
        poc_manager.poc_registry["poc2"] = POCMetadata(
            poc_name="POC 2",
            poc_id="poc2",
            poc_type="web",
            severity="medium"
        )
        
        high_pocs = poc_manager.get_pocs_by_severity("high")
        
        assert len(high_pocs) == 1
        assert high_pocs[0].poc_id == "poc1"
    
    async def test_clear_cache(self, poc_manager):
        """测试清除缓存"""
        poc_manager.poc_cache["test_key"] = {"data": "test"}
        
        assert len(poc_manager.poc_cache) > 0
        
        poc_manager.clear_cache()
        
        assert len(poc_manager.poc_cache) == 0
    
    async def test_get_cache_stats(self, poc_manager):
        """测试获取缓存统计"""
        poc_manager.poc_registry["poc1"] = POCMetadata(
            poc_name="POC 1",
            poc_id="poc1",
            poc_type="web",
            severity="high"
        )
        poc_manager.poc_cache["poc_code_poc1"] = {"code": "test code"}
        
        stats = poc_manager.get_cache_stats()
        
        assert "poc_count" in stats
        assert "cache_entries" in stats
        assert "cache_size_mb" in stats
        assert stats["poc_count"] == 1
        assert stats["cache_entries"] == 1


class TestTargetInfo:
    """测试目标信息类"""
    
    def test_target_info_creation(self):
        """测试目标信息创建"""
        target = TargetInfo(
            url="https://example.com",
            target_type="web",
            priority=5,
            metadata={"name": "Example Site"}
        )
        
        assert target.url == "https://example.com"
        assert target.target_type == "web"
        assert target.priority == 5
        assert target.metadata["name"] == "Example Site"
    
    def test_target_info_is_valid(self):
        """测试目标信息验证"""
        valid_target = TargetInfo(url="https://example.com")
        invalid_target = TargetInfo(url="not-a-url")
        
        assert valid_target.is_valid() == True
        assert invalid_target.is_valid() == False
    
    def test_target_info_get_domain(self):
        """测试获取域名"""
        target = TargetInfo(url="https://example.com/path")
        
        domain = target.get_domain()
        
        assert domain == "example.com"
    
    def test_target_info_to_dict(self):
        """测试目标信息转换为字典"""
        target = TargetInfo(
            url="https://example.com",
            target_type="web",
            priority=5
        )
        
        target_dict = target.to_dict()
        
        assert isinstance(target_dict, dict)
        assert target_dict["url"] == "https://example.com"
        assert target_dict["target_type"] == "web"
        assert target_dict["priority"] == 5
        assert "domain" in target_dict
        assert "is_valid" in target_dict


class TestTargetManager:
    """测试目标管理器"""
    
    @pytest.fixture
    async def target_manager(self):
        """创建目标管理器实例"""
        return TargetManager()
    
    async def test_target_manager_initialization(self, target_manager):
        """测试目标管理器初始化"""
        assert target_manager is not None
        assert isinstance(target_manager.targets, dict)
        assert isinstance(target_manager.target_groups, dict)
    
    async def test_add_single_target(self, target_manager):
        """测试添加单个目标"""
        target = await target_manager.add_single_target(
            url="https://example.com",
            target_type="web",
            priority=5
        )
        
        assert "https://example.com" in target_manager.targets
        assert target_manager.targets["https://example.com"].url == "https://example.com"
    
    async def test_remove_target(self, target_manager):
        """测试移除目标"""
        await target_manager.add_single_target(url="https://example.com")
        
        assert "https://example.com" in target_manager.targets
        
        result = await target_manager.remove_target("https://example.com")
        
        assert result == True
        assert "https://example.com" not in target_manager.targets
    
    async def test_clear_all_targets(self, target_manager):
        """测试清除所有目标"""
        await target_manager.add_single_target(url="https://example.com")
        await target_manager.add_single_target(url="https://test.com")
        
        assert len(target_manager.targets) == 2
        
        await target_manager.clear_all_targets()
        
        assert len(target_manager.targets) == 0
        assert len(target_manager.target_groups) == 0
    
    async def test_get_targets_by_priority(self, target_manager):
        """测试按优先级获取目标"""
        await target_manager.add_single_target(
            url="https://high.com",
            target_type="web",
            priority=2
        )
        await target_manager.add_single_target(
            url="https://medium.com",
            target_type="web",
            priority=5
        )
        
        high_priority_targets = await target_manager.get_targets_by_priority(
            min_priority=1,
            max_priority=3
        )
        
        assert len(high_priority_targets) == 1
        assert high_priority_targets[0].url == "https://high.com"
    
    async def test_get_targets_by_type(self, target_manager):
        """测试按类型获取目标"""
        await target_manager.add_single_target(
            url="https://web1.com",
            target_type="web",
            priority=5
        )
        await target_manager.add_single_target(
            url="https://api1.com",
            target_type="api",
            priority=5
        )
        
        web_targets = await target_manager.get_targets_by_type("web")
        
        assert len(web_targets) == 1
        assert web_targets[0].url == "https://web1.com"
    
    async def test_get_statistics(self, target_manager):
        """测试获取统计信息"""
        await target_manager.add_single_target(
            url="https://web1.com",
            target_type="web",
            priority=5
        )
        await target_manager.add_single_target(
            url="https://api1.com",
            target_type="api",
            priority=5
        )
        
        stats = target_manager.get_statistics()
        
        assert "total" in stats
        assert "by_type" in stats
        assert stats["total"] == 2
        assert stats["by_type"]["web"] == 1
        assert stats["by_type"]["api"] == 1


class TestResultAnalyzer:
    """测试结果分析器"""
    
    @pytest.fixture
    async def result_analyzer(self):
        """创建结果分析器实例"""
        return ResultAnalyzer()
    
    async def test_result_analyzer_initialization(self, result_analyzer):
        """测试结果分析器初始化"""
        assert result_analyzer is not None
        assert isinstance(result_analyzer.false_positive_keywords, list)
        assert isinstance(result_analyzer.success_keywords, list)
    
    async def test_detect_false_positive(self, result_analyzer):
        """测试误报检测"""
        result = POCVerificationResult(
            id=1,
            poc_name="Test POC",
            poc_id="test_poc",
            target="https://example.com",
            vulnerable=False,
            message="Connection timeout",
            output="",
            error="timeout",
            execution_time=0.0,
            confidence=0.1,
            severity="info",
            cvss_score=0.0,
            created_at=datetime.now()
        )
        
        is_false_positive = result_analyzer._detect_false_positive(result, [])
        
        assert is_false_positive == True
    
    async def test_calculate_risk_level(self, result_analyzer):
        """测试风险等级计算"""
        vulnerable_result = POCVerificationResult(
            id=1,
            poc_name="Test POC",
            poc_id="test_poc",
            target="https://example.com",
            vulnerable=True,
            message="Vulnerable",
            output="Exploit successful",
            error="",
            execution_time=5.0,
            confidence=0.9,
            severity="high",
            cvss_score=7.5,
            created_at=datetime.now()
        )
        
        risk_level = result_analyzer._calculate_risk_level(
            vulnerable_result,
            is_false_positive=False
        )
        
        assert risk_level == "high"
    
    async def test_generate_recommendations(self, result_analyzer):
        """测试生成修复建议"""
        vulnerable_result = POCVerificationResult(
            id=1,
            poc_name="Test POC",
            poc_id="test_poc",
            target="https://example.com",
            vulnerable=True,
            message="Vulnerable",
            output="Exploit successful",
            error="",
            execution_time=5.0,
            confidence=0.9,
            severity="high",
            cvss_score=7.5,
            created_at=datetime.now()
        )
        
        recommendations = result_analyzer._generate_recommendations(
            vulnerable_result,
            is_false_positive=False
        )
        
        assert len(recommendations) > 0
        assert any("漏洞存在" in r for r in recommendations)
        assert any("修复" in r for r in recommendations)


class TestReportGenerator:
    """测试报告生成器"""
    
    @pytest.fixture
    async def report_generator(self):
        """创建报告生成器实例"""
        return ReportGenerator()
    
    async def test_report_generator_initialization(self, report_generator):
        """测试报告生成器初始化"""
        assert report_generator is not None
        assert isinstance(report_generator.report_templates, dict)
        assert "html" in report_generator.report_templates
        assert "json" in report_generator.report_templates
        assert "pdf" in report_generator.report_templates
    
    async def test_generate_html_report(self, report_generator):
        """测试生成 HTML 报告"""
        verification_task = Mock()
        verification_task.poc_name = "Test POC"
        verification_task.id = "test-task-id"
        
        results = []
        
        html_content = await report_generator._generate_html_report(
            verification_task,
            results,
            is_batch=False
        )
        
        assert isinstance(html_content, str)
        assert "<!DOCTYPE html>" in html_content
        assert "POC 验证报告" in html_content
        assert verification_task.poc_name in html_content
    
    async def test_generate_json_report(self, report_generator):
        """测试生成 JSON 报告"""
        verification_task = Mock()
        verification_task.poc_name = "Test POC"
        verification_task.id = "test-task-id"
        
        results = []
        
        json_content = await report_generator._generate_json_report(
            verification_task,
            results,
            is_batch=False
        )
        
        assert isinstance(json_content, str)
        assert '"report_type"' in json_content
        assert '"summary"' in json_content
        assert '"results"' in json_content
    
    async def test_generate_execution_summary(self, report_generator):
        """测试生成执行摘要"""
        verification_task = Mock()
        verification_task.poc_name = "Test POC"
        verification_task.poc_id = "test_poc"
        verification_task.target = "https://example.com"
        verification_task.status = "completed"
        verification_task.progress = 100
        verification_task.created_at = datetime.now()
        verification_task.updated_at = datetime.now()
        
        summary = await report_generator.generate_execution_summary(
            verification_task
        )
        
        assert "task_id" in summary
        assert "poc_name" in summary
        assert "status" in summary
        assert "summary" in summary
    
    async def test_generate_statistics(self, report_generator):
        """测试生成统计信息"""
        results = []
        
        stats = await report_generator.generate_statistics(results)
        
        assert "total" in stats
        assert "vulnerable" in stats
        assert "not_vulnerable" in stats
        assert "average_confidence" in stats
        assert "severity_distribution" in stats


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_poc_verification_flow(self):
        """测试端到端 POC 验证流程"""
        from backend.ai_agents.poc_system import (
            poc_manager,
            target_manager,
            verification_engine,
            result_analyzer,
            report_generator
        )
        
        # 1. 添加目标
        target = await target_manager.add_single_target(
            url="https://example.com",
            target_type="web",
            priority=5
        )
        
        # 2. 注册 POC
        poc_metadata = POCMetadata(
            poc_name="Test POC",
            poc_id="test_poc_1",
            poc_type="web",
            severity="high",
            cvss_score=7.5,
            description="Test POC for integration testing",
            source="test"
        )
        poc_manager.poc_registry[poc_metadata.poc_id] = poc_metadata
        
        # 3. 创建验证任务(模拟)
        assert len(poc_manager.poc_registry) > 0
        assert len(target_manager.targets) > 0
        
        # 4. 验证流程完整性
        assert poc_manager.get_poc_metadata("test_poc_1") is not None
        assert target_manager.targets["https://example.com"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

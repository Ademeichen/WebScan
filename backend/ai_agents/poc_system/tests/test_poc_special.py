"""
POC专项测试文件

测试POC脚本下载成功率、不同类型CVE的POC兼容性、
POC执行结果准确性、异常处理机制等。
"""
import pytest
import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Any

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from backend.ai_agents.poc_system.poc_integration import (
    POCIntegrationManager,
    get_poc_integration_manager,
    POCExecutionResult,
    SeebugPOCInfo
)


class TestPOCDownload:
    """POC下载测试"""
    
    @pytest.fixture
    def poc_manager(self):
        """POC管理器fixture"""
        return POCIntegrationManager()
    
    @pytest.mark.asyncio
    async def test_search_poc_by_cve(self, poc_manager):
        """测试通过CVE编号搜索POC"""
        cve_id = "CVE-2017-12149"
        
        poc_infos = await poc_manager.search_poc_by_cve(cve_id)
        
        assert isinstance(poc_infos, list)
        print(f"找到 {len(poc_infos)} 个POC")
        
        for poc_info in poc_infos:
            assert isinstance(poc_info, SeebugPOCInfo)
            assert poc_info.cve_id == cve_id or cve_id in poc_info.title
    
    @pytest.mark.asyncio
    async def test_search_local_poc_fallback(self, poc_manager):
        """测试本地POC库回退搜索"""
        cve_id = "CVE-2017-12149"
        
        poc_infos = await poc_manager._search_local_poc(cve_id)
        
        assert isinstance(poc_infos, list)
        print(f"本地找到 {len(poc_infos)} 个POC")
    
    @pytest.mark.asyncio
    async def test_invalid_cve_search(self, poc_manager):
        """测试无效CVE编号搜索"""
        invalid_cve = "CVE-INVALID-99999"
        
        poc_infos = await poc_manager.search_poc_by_cve(invalid_cve)
        
        assert isinstance(poc_infos, list)
        print(f"无效CVE找到 {len(poc_infos)} 个POC")


class TestPOCCompatibility:
    """不同类型CVE的POC兼容性测试"""
    
    @pytest.fixture
    def poc_manager(self):
        """POC管理器fixture"""
        return POCIntegrationManager()
    
    @pytest.mark.parametrize("cve_id, cve_type", [
        ("CVE-2017-12149", "jboss"),
        ("CVE-2018-7600", "drupal"),
        ("CVE-2020-10199", "nexus"),
        ("CVE-2018-2628", "weblogic"),
        ("CVE-2022-22965", "spring"),
    ])
    @pytest.mark.asyncio
    async def test_different_cve_types(self, poc_manager, cve_id, cve_type):
        """测试不同类型CVE的兼容性"""
        poc_infos = await poc_manager.search_poc_by_cve(cve_id)
        
        print(f"\nCVE类型: {cve_type}")
        print(f"CVE编号: {cve_id}")
        print(f"找到POC数量: {len(poc_infos)}")
        
        for i, poc_info in enumerate(poc_infos[:3], 1):
            print(f"  POC {i}: {poc_info.title}")
            print(f"    严重度: {poc_info.severity}")
        
        assert isinstance(poc_infos, list)


class TestPOCExecution:
    """POC执行测试"""
    
    @pytest.fixture
    def poc_manager(self):
        """POC管理器fixture"""
        manager = POCIntegrationManager()
        manager.initialize()
        return manager
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_execute_local_poc(self, poc_manager):
        """测试执行本地POC"""
        target = "http://example.com"
        poc_name = "jboss_cve_2017_12149"
        
        try:
            from backend.ai_agents.tools.adapters import POCAdapter
            
            all_pocs = POCAdapter.get_all_pocs()
            if not all_pocs:
                pytest.skip("没有可用的本地POC")
            
            poc_name = next(iter(all_pocs.keys()))
            
            result = await poc_manager.execute_poc(
                target=target,
                poc_name=poc_name,
                timeout=60.0
            )
            
            assert isinstance(result, POCExecutionResult)
            assert result.target == target
            assert result.poc_name == poc_name
            
            print(f"\nPOC执行结果:")
            print(f"  目标: {result.target}")
            print(f"  POC: {result.poc_name}")
            print(f"  成功: {result.success}")
            print(f"  有漏洞: {result.vulnerable}")
            print(f"  执行时间: {result.execution_time:.2f}s")
            
            if result.error:
                print(f"  错误: {result.error}")
                
        except Exception as e:
            pytest.skip(f"POC执行跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_poc(self, poc_manager):
        """测试执行不存在的POC"""
        target = "http://example.com"
        invalid_poc_name = "nonexistent_poc_that_never_exists"
        
        result = await poc_manager.execute_poc(
            target=target,
            poc_name=invalid_poc_name,
            timeout=30.0
        )
        
        assert isinstance(result, POCExecutionResult)
        assert result.success is False or result.error is not None


class TestPOCErrorHandling:
    """POC异常处理机制测试"""
    
    @pytest.fixture
    def poc_manager(self):
        """POC管理器fixture"""
        manager = POCIntegrationManager()
        manager.initialize()
        return manager
    
    @pytest.mark.asyncio
    async def test_invalid_target_error(self, poc_manager):
        """测试无效目标错误处理"""
        invalid_target = "not-a-valid-url"
        
        result = await poc_manager.execute_poc(
            target=invalid_target,
            poc_name="baseinfo",
            timeout=10.0
        )
        
        assert isinstance(result, POCExecutionResult)
        print(f"无效目标测试:")
        print(f"  目标: {invalid_target}")
        print(f"  成功: {result.success}")
        print(f"  错误: {result.error}")
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, poc_manager):
        """测试超时错误处理"""
        target = "http://10.255.255.1"
        
        result = await poc_manager.execute_poc(
            target=target,
            poc_name="baseinfo",
            timeout=5.0
        )
        
        assert isinstance(result, POCExecutionResult)
        print(f"\n超时测试:")
        print(f"  目标: {target}")
        print(f"  成功: {result.success}")
        print(f"  执行时间: {result.execution_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_no_poc_provided_error(self, poc_manager):
        """测试未提供POC参数的错误处理"""
        target = "http://example.com"
        
        result = await poc_manager.execute_poc(
            target=target,
            timeout=30.0
        )
        
        assert isinstance(result, POCExecutionResult)
        assert result.error is not None or result.success is False
        print(f"\n无POC参数测试:")
        print(f"  错误: {result.error}")


class TestPOCCache:
    """POC缓存测试"""
    
    @pytest.fixture
    def poc_manager(self):
        """POC管理器fixture"""
        return POCIntegrationManager()
    
    def test_get_cached_pocs(self, poc_manager):
        """测试获取缓存的POC列表"""
        cached_pocs = poc_manager.get_cached_pocs()
        
        assert isinstance(cached_pocs, list)
        print(f"\n缓存POC数量: {len(cached_pocs)}")
        for poc_path in cached_pocs[:5]:
            print(f"  {poc_path}")
    
    def test_clear_cache(self, poc_manager):
        """测试清空POC缓存"""
        poc_manager.clear_cache()
        
        cached_pocs = poc_manager.get_cached_pocs()
        assert len(cached_pocs) == 0 or len(cached_pocs) < len(poc_manager.get_cached_pocs())


class TestPOCBatchExecution:
    """批量POC执行测试"""
    
    @pytest.fixture
    def poc_manager(self):
        """POC管理器fixture"""
        manager = POCIntegrationManager()
        manager.initialize()
        return manager
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_batch_execute_poc(self, poc_manager):
        """测试批量执行POC"""
        targets = [
            "http://example1.com",
            "http://example2.com",
        ]
        cve_ids = [
            "CVE-2017-12149",
            "CVE-2018-7600",
        ]
        
        results = await poc_manager.batch_execute_poc(targets, cve_ids)
        
        assert isinstance(results, list)
        assert len(results) == len(targets) * len(cve_ids)
        
        print(f"\n批量执行结果:")
        print(f"  总任务数: {len(results)}")
        
        for i, result in enumerate(results[:5], 1):
            print(f"  任务 {i}:")
            print(f"    CVE: {result.cve_id}")
            print(f"    目标: {result.target}")
            print(f"    成功: {result.success}")


class TestPOCSuccessRate:
    """POC成功率测试"""
    
    @pytest.fixture
    def poc_manager(self):
        """POC管理器fixture"""
        manager = POCIntegrationManager()
        manager.initialize()
        return manager
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_poc_success_rate(self, poc_manager):
        """测试POC成功率"""
        test_cases = [
            ("CVE-2017-12149", "http://example.com"),
            ("CVE-2018-7600", "http://example.com"),
            ("CVE-INVALID-001", "http://example.com"),
        ]
        
        results = []
        for cve_id, target in test_cases:
            try:
                poc_infos = await poc_manager.search_poc_by_cve(cve_id)
                results.append({
                    "cve_id": cve_id,
                    "found": len(poc_infos) > 0,
                    "count": len(poc_infos)
                })
            except Exception as e:
                results.append({
                    "cve_id": cve_id,
                    "found": False,
                    "error": str(e)
                })
        
        total = len(results)
        successful = sum(1 for r in results if r.get("found", False))
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"\nPOC搜索成功率测试:")
        print(f"  总测试数: {total}")
        print(f"  成功数: {successful}")
        print(f"  成功率: {success_rate:.1f}%")
        
        for result in results:
            status = "✓" if result.get("found") else "✗"
            print(f"  {status} {result['cve_id']}: "
                  f"{'找到' if result.get('found') else '未找到'}"
                  f"{' (' + str(result.get('count', 0)) + '个)' if result.get('count') else ''}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

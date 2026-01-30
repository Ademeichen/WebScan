"""
POC 文件管理 API 测试

测试 POC 文件管理 API 的功能正确性和可靠性
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import os
from typing import Dict, List, Any

from backend.main import app
from backend.ai_agents.utils.file_sync import FileSyncManager


class TestPOCFilesAPI(unittest.TestCase):
    """
    POC 文件管理 API 测试类
    """
    
    def setUp(self):
        """
        设置测试环境
        """
        # 创建测试客户端
        self.client = TestClient(app)
        
        # 创建临时目录作为测试目录
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_poc_dir = Path(self.temp_dir.name) / "base_poc"
        self.seebug_generated_dir = Path(self.temp_dir.name) / "seebug_generated"
        
        # 创建测试目录
        self.base_poc_dir.mkdir(exist_ok=True)
        self.seebug_generated_dir.mkdir(exist_ok=True)
        
        # 创建测试子目录
        (self.base_poc_dir / "test1").mkdir(exist_ok=True)
        (self.base_poc_dir / "test2").mkdir(exist_ok=True)
        (self.seebug_generated_dir / "test1").mkdir(exist_ok=True)
        (self.seebug_generated_dir / "test3").mkdir(exist_ok=True)
        
        # 创建测试文件
        # 在base_poc目录中创建文件
        with open(self.base_poc_dir / "test1" / "file1.py", "w") as f:
            f.write("# Test file 1\n")
        with open(self.base_poc_dir / "test2" / "file2.py", "w") as f:
            f.write("# Test file 2\n")
        
        # 在seebug_generated目录中创建文件
        with open(self.seebug_generated_dir / "test1" / "file1.py", "w") as f:
            f.write("# Test file 1\n")
        with open(self.seebug_generated_dir / "test3" / "file3.py", "w") as f:
            f.write("# Test file 3\n")
        
        # 保存原始目录路径
        from backend.ai_agents.utils.file_sync import file_sync_manager
        self.original_base_poc_dir = file_sync_manager.base_poc_dir
        self.original_seebug_generated_dir = file_sync_manager.seebug_generated_dir
        
        # 替换为测试目录
        file_sync_manager.base_poc_dir = self.base_poc_dir
        file_sync_manager.seebug_generated_dir = self.seebug_generated_dir
        
        # 重新导入file_access_layer以使用新的目录
        from backend.api import poc_files
        poc_files.file_access_layer = poc_files.FileAccessLayer()
    
    def tearDown(self):
        """
        清理测试环境
        """
        # 恢复原始目录路径
        from backend.ai_agents.utils.file_sync import file_sync_manager
        file_sync_manager.base_poc_dir = self.original_base_poc_dir
        file_sync_manager.seebug_generated_dir = self.original_seebug_generated_dir
        
        # 清理临时目录
        self.temp_dir.cleanup()
    
    def test_get_poc_files(self):
        """
        测试获取POC文件列表
        """
        response = self.client.get("/api/poc/files/list")
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应内容
        data = response.json()
        self.assertIn('total', data)
        self.assertIn('files', data)
        self.assertGreaterEqual(data['total'], 3)  # 至少有3个文件
        
        # 检查文件信息
        file_names = [f['file_name'] for f in data['files']]
        self.assertIn('file1.py', file_names)
        self.assertIn('file2.py', file_names)
        self.assertIn('file3.py', file_names)
    
    def test_get_poc_files_with_filter(self):
        """
        测试带过滤器的POC文件列表获取
        """
        # 按文件名过滤
        response = self.client.get("/api/poc/files/list?name=file1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        file_names = [f['file_name'] for f in data['files']]
        self.assertIn('file1.py', file_names)
        self.assertNotIn('file2.py', file_names)
        self.assertNotIn('file3.py', file_names)
        
        # 按目录过滤
        response = self.client.get("/api/poc/files/list?directory=test2")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        file_names = [f['file_name'] for f in data['files']]
        self.assertIn('file2.py', file_names)
        self.assertNotIn('file1.py', file_names)
        self.assertNotIn('file3.py', file_names)
    
    def test_get_poc_file_content(self):
        """
        测试获取单个POC文件内容
        """
        response = self.client.get("/api/poc/files/content/test1/file1.py")
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应内容
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['message'], "获取文件内容成功")
        self.assertIn('file_path', data['data'])
        self.assertIn('content', data['data'])
        self.assertEqual(data['data']['file_path'], "test1/file1.py")
        self.assertEqual(data['data']['content'], "# Test file 1\n")
    
    def test_get_poc_file_content_not_found(self):
        """
        测试获取不存在的POC文件内容
        """
        response = self.client.get("/api/poc/files/content/nonexistent/file.py")
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 404)
        
        # 检查响应内容
        data = response.json()
        self.assertEqual(data['detail'], "文件不存在: nonexistent/file.py")
    
    def test_get_poc_file_info(self):
        """
        测试获取单个POC文件信息
        """
        # 先获取文件列表，确保文件路径正确
        list_response = self.client.get("/api/poc/files/list")
        files = list_response.json()['files']
        
        # 确保有文件
        self.assertGreater(len(files), 0)
        
        # 使用第一个文件的路径进行测试
        test_file_path = files[0]['file_path']
        response = self.client.get(f"/api/poc/files/info/{test_file_path}")
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应内容
        data = response.json()
        self.assertIn('file_path', data)
        self.assertIn('file_name', data)
        self.assertIn('directory', data)
        self.assertIn('size', data)
        self.assertIn('created_at', data)
        self.assertIn('modified_at', data)
        self.assertEqual(data['file_path'], test_file_path)
    
    def test_get_poc_file_info_not_found(self):
        """
        测试获取不存在的POC文件信息
        """
        response = self.client.get("/api/poc/files/info/nonexistent/file.py")
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 404)
        
        # 检查响应内容
        data = response.json()
        self.assertEqual(data['detail'], "文件不存在: nonexistent/file.py")
    
    def test_get_poc_directories(self):
        """
        测试获取POC目录列表
        """
        response = self.client.get("/api/poc/files/directories")
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应内容
        directories = response.json()
        self.assertIsInstance(directories, list)
        self.assertIn("test1", directories)
        self.assertIn("test2", directories)
        self.assertIn("test3", directories)
    
    def test_sync_poc_files(self):
        """
        测试同步POC文件
        """
        # 修改seebug_generated目录中的文件
        with open(self.seebug_generated_dir / "test3" / "file3.py", "w") as f:
            f.write("# Updated test file 3\n")
        
        response = self.client.post("/api/poc/files/sync")
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应内容
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['message'], "文件同步成功")
        self.assertIn('data', data)
        self.assertIn('added', data['data'])
        self.assertIn('updated', data['data'])
        self.assertIn('deleted', data['data'])
    
    def test_get_sync_status(self):
        """
        测试获取同步状态
        """
        response = self.client.get("/api/poc/files/sync/status")
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应内容
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['message'], "获取同步状态成功")
        self.assertIn('data', data)
        self.assertIn('sync_time', data['data'])
        self.assertIn('base_poc_files', data['data'])
        self.assertIn('seebug_generated_files', data['data'])
        self.assertIn('base_poc_dir', data['data'])
        self.assertIn('seebug_generated_dir', data['data'])
    
    def test_search_files_by_name(self):
        """
        测试按文件名搜索文件
        """
        response = self.client.get("/api/poc/files/list?name=file1")
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应内容
        data = response.json()
        self.assertGreater(data['total'], 0)
        for file_info in data['files']:
            self.assertIn('file1', file_info['file_name'])
    
    def test_search_files_by_directory(self):
        """
        测试按目录搜索文件
        """
        response = self.client.get("/api/poc/files/list?directory=test2")
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应内容
        data = response.json()
        self.assertGreater(data['total'], 0)
        for file_info in data['files']:
            self.assertIn('test2', file_info['directory'])


if __name__ == '__main__':
    unittest.main()

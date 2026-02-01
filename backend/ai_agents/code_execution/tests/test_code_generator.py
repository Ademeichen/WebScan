"""
测试代码生成模块

测试 CodeGenerator 类的各项功能。
"""
import pytest
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.ai_agents.code_execution.code_generator import (
    CodeGenerator,

    CodeGenerationResponse
)


class TestCodeGenerator:
    """
    测试代码生成器类
    """

    @pytest.fixture
    def code_generator(self):
        """
        创建代码生成器实例
        """
        return CodeGenerator()

    def test_initialization(self, code_generator):
        """
        测试初始化
        """
        assert code_generator is not None
        assert hasattr(code_generator, 'env_awareness')
        assert hasattr(code_generator, 'llm')

    def test_get_template(self, code_generator):
        """
        测试获取扫描模板
        """
        template = code_generator._get_template('port_scan')
        assert isinstance(template, str)
        assert len(template) > 0
        assert 'socket' in template
        assert 'scan_port' in template

        template = code_generator._get_template('vuln_scan')
        assert isinstance(template, str)
        assert len(template) > 0
        assert 'requests' in template

        template = code_generator._get_template('dir_scan')
        assert isinstance(template, str)
        assert len(template) > 0
        assert 'urljoin' in template

        template = code_generator._get_template('subdomain_scan')
        assert isinstance(template, str)
        assert len(template) > 0
        assert 'dns.resolver' in template

    def test_get_template_invalid_type(self, code_generator):
        """
        测试获取不存在的扫描类型模板
        """
        template = code_generator._get_template('invalid_type')
        assert isinstance(template, str)
        assert len(template) > 0

    @pytest.mark.asyncio
    async def test_template_generate_code(self, code_generator):
        """
        测试使用模板生成代码
        """
        response = await code_generator._template_generate_code(
            scan_type='port_scan',
            target='www.baidu.com',
            requirements='',
            language='python',
            additional_params={}
        )
        
        assert isinstance(response, CodeGenerationResponse)
        assert response.code != ''
        assert response.language == 'python'
        assert response.description != ''
        assert response.estimated_time > 0
        assert 'www.baidu.com' in response.code

    @pytest.mark.asyncio
    async def test_generate_code_port_scan(self, code_generator):
        """
        测试生成端口扫描代码
        """
        response = await code_generator.generate_code(
            scan_type='port_scan',
            target='www.baidu.com',
            requirements='',
            language='python'
        )
        
        assert isinstance(response, CodeGenerationResponse)
        assert response.code != ''
        assert 'www.baidu.com' in response.code
        assert 'socket' in response.code

    @pytest.mark.asyncio
    async def test_generate_code_vuln_scan(self, code_generator):
        """
        测试生成漏洞扫描代码
        """
        response = await code_generator.generate_code(
            scan_type='vuln_scan',
            target='https://www.baidu.com',
            requirements='',
            language='python'
        )
        
        assert isinstance(response, CodeGenerationResponse)
        assert response.code != ''
        assert 'https://www.baidu.com' in response.code
        assert 'requests' in response.code

    @pytest.mark.asyncio
    async def test_generate_code_dir_scan(self, code_generator):
        """
        测试生成目录扫描代码
        """
        response = await code_generator.generate_code(
            scan_type='dir_scan',
            target='https://www.baidu.com',
            requirements='',
            language='python'
        )
        
        assert isinstance(response, CodeGenerationResponse)
        assert response.code != ''
        assert 'https://www.baidu.com' in response.code
        assert 'urljoin' in response.code

    @pytest.mark.asyncio
    async def test_generate_code_subdomain_scan(self, code_generator):
        """
        测试生成子域名扫描代码
        """
        response = await code_generator.generate_code(
            scan_type='subdomain_scan',
            target='www.baidu.com',
            requirements='',
            language='python'
        )
        
        assert isinstance(response, CodeGenerationResponse)
        assert response.code != ''
        assert 'www.baidu.com' in response.code
        assert 'dns.resolver' in response.code

    def test_validate_code_safe(self, code_generator):
        """
        测试验证安全代码
        """
        safe_code = """
import socket

def scan_port(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    return result == 0
"""
        validation = code_generator.validate_code(safe_code, 'python')
        assert validation['valid'] is True
        assert len(validation['issues']) == 0

    def test_validate_code_dangerous(self, code_generator):
        """
        测试验证危险代码
        """
        dangerous_code = """
import os

def execute_command(cmd):
    os.system(cmd)
"""
        validation = code_generator.validate_code(dangerous_code, 'python')
        assert validation['valid'] is False
        assert len(validation['issues']) > 0
        
        issues = validation['issues']
        dangerous_patterns = [issue['message'] for issue in issues]
        assert any('os.system' in pattern for pattern in dangerous_patterns)

    def test_validate_code_eval(self, code_generator):
        """
        测试验证包含eval的代码
        """
        dangerous_code = """
def execute_eval(code):
    return eval(code)
"""
        validation = code_generator.validate_code(dangerous_code, 'python')
        assert validation['valid'] is False
        assert len(validation['issues']) > 0

    def test_validate_code_exec(self, code_generator):
        """
        测试验证包含exec的代码
        """
        dangerous_code = """
def execute_exec(code):
    exec(code)
"""
        validation = code_generator.validate_code(dangerous_code, 'python')
        assert validation['valid'] is False
        assert len(validation['issues']) > 0

    def test_validate_code_shell_true(self, code_generator):
        """
        测试验证包含shell=True的代码
        """
        dangerous_code = """
import subprocess

def run_command(cmd):
    subprocess.run(cmd, shell=True)
"""
        validation = code_generator.validate_code(dangerous_code, 'python')
        assert validation['valid'] is False
        assert len(validation['issues']) > 0

    def test_find_line_with_pattern(self, code_generator):
        """
        测试查找包含特定模式的行号
        """
        code = """line 1
line 2 with pattern
line 3
"""
        line_num = code_generator._find_line_with_pattern(code, 'pattern')
        assert line_num == 2

    def test_find_line_with_pattern_not_found(self, code_generator):
        """
        测试查找不存在的模式
        """
        code = """line 1
line 2
line 3
"""
        line_num = code_generator._find_line_with_pattern(code, 'nonexistent')
        assert line_num == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

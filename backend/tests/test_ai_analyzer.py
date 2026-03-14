"""
AI分析器测试文件

测试AI分析器的提示词生成和结果解析功能
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.ai_agents.analyzers.ai_analyzer import AIAnalyzer


class TestAIAnalyzer:
    """AI分析器测试类"""
    
    @pytest.fixture
    def analyzer():
        """创建分析器实例"""
        return AIAnalyzer()
    
    @pytest.fixture
    def sample_vulnerabilities():
        """示例漏洞数据"""
        return [
            {
                "id": "1",
                "type": "SQL注入",
                "vuln_type": "SQL注入",
                "severity": "high",
                "url": "http://example.com/search?id=1",
                "description": "存在SQL注入漏洞"
            },
            {
                "id": "2",
                "type": "XSS",
                "vuln_type": "存储型XSS",
                "severity": "medium",
                "url": "http://example.com/comment",
                "description": "存储型XSS漏洞"
            },
            {
                "id": "3",
                "type": "CSRF",
                "vuln_type": "CSRF",
                "severity": "medium",
                "url": "http://example.com/transfer",
                "description": "跨站请求伪造漏洞"
            }
        ]
    @pytest.fixture
    def sample_tool_results():
        """示例工具结果"""
        return {
            "sqlmap": {"found": True, "databases": 2},
            "nmap": {"open_ports": [80, 443, 3306]}
        }
    
    @pytest.fixture
    def sample_target_context():
        """示例目标上下文"""
        return {
            "target": "http://example.com",
            "scan_type": "web",
            "depth": "standard"
        }
    
    def test_build_analysis_prompt_length(self, analyzer, sample_vulnerabilities, sample_tool_results, sample_target_context):
        """测试提示词生成 - 验证精简"""
        prompt = analyzer._build_analysis_prompt(
            vulnerabilities=sample_vulnerabilities,
            tool_results=sample_tool_results,
            target_context=sample_target_context
        )
        
        assert len(prompt) < 1500, f"提示词过长: {len(prompt)} 字符"
        assert "输出格式" in prompt, "缺少输出格式说明"
        assert "JSON" in prompt, "缺少JSON格式要求"
        assert "summary" in prompt, "缺少summary字段说明"
        assert "recommendations" in prompt, "缺少recommendations字段说明"
    
    def test_build_analysis_prompt_content(self, analyzer, sample_vulnerabilities, sample_tool_results, sample_target_context):
        """测试提示词内容"""
        prompt = analyzer._build_analysis_prompt(
            vulnerabilities=sample_vulnerabilities,
            tool_results=sample_tool_results,
            target_context=sample_target_context
        )
        
        assert "目标:" in prompt, "缺少目标信息"
        assert "漏洞数量:" in prompt, "缺少漏洞数量信息"
        assert "主要漏洞:" in prompt, "缺少主要漏洞信息"
    
    def test_parse_llm_response_valid(self, analyzer):
        """测试解析有效的LLM响应"""
        response_text = '''
        {
          "summary": "发现SQL注入和XSS漏洞，风险等级高",
          "risk_level": "high",
          "top_vulnerabilities": [
            {"id": "1", "type": "SQL注入", "severity": "high", "fix_priority": 1}
          ],
          "recommendations": ["使用参数化查询", "输入验证"]
        }
        '''
        
        result = analyzer._parse_llm_response(response_text)
        
        assert result.summary == "发现SQL注入和XSS漏洞，风险等级高"
        assert result.risk_level == "high"
        assert len(result.remediation_priorities) > 0
    
    def test_parse_llm_response_with_extra_text(self, analyzer):
        """测试解析包含额外文本的响应"""
        response_text = '''
        根据分析结果:
        {
          "summary": "存在多个安全漏洞",
          "risk_level": "medium",
          "top_vulnerabilities": [],
          "recommendations": []
        }
        其他建议...
        '''
        
        result = analyzer._parse_llm_response(response_text)
        
        assert result.summary == "存在多个安全漏洞"
        assert result.risk_level == "medium"
    
    def test_parse_llm_response_invalid_json(self, analyzer):
        """测试解析无效JSON响应"""
        response_text = "这不是JSON格式"
        
        result = analyzer._parse_llm_response(response_text)
        
        assert result.summary == "分析结果解析失败"
    
    def test_parse_llm_response_empty(self, analyzer):
        """测试解析空响应"""
        response_text = ""
        
        result = analyzer._parse_llm_response(response_text)
        
        assert result.summary == "分析结果解析失败"


if __name__ == "__main__":
    pytest.main(["-v", "test_ai_analyzer.py"])

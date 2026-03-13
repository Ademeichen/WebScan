"""
独立的 AgentState 测试 - 使用 pytest 框架
"""
import pytest
from ai_agents.core.state import AgentState


class TestAgentStateCreation:
    """测试 AgentState 对象的创建"""
    
    def test_agent_state_creation_basic(self):
        """测试 AgentState 基础创建"""
        state = AgentState(
            target="https://www.baidu.com",
            task_id="test_task_001"
        )
        
        assert state.target == "https://www.baidu.com"
        assert state.task_id == "test_task_001"
        assert state.planned_tasks == []
        assert state.vulnerabilities == []
        assert state.errors == []
        assert state.is_complete == False
        assert state.should_continue == True
    
    def test_agent_state_creation_with_params(self):
        """测试 AgentState 带参数创建"""
        state = AgentState(
            target="https://www.baidu.com",
            task_id="test_task_001",
            target_context={"test": "value"},
            user_tools=["port_scan"],
            user_requirement="Test requirement",
            memory_info="Test memory"
        )
        
        assert state.target == "https://www.baidu.com"
        assert state.task_id == "test_task_001"
        assert state.target_context == {"test": "value"}
        assert state.user_tools == ["port_scan"]
        assert state.user_requirement == "Test requirement"
        assert state.memory_info == "Test memory"


class TestAgentStateUpdate:
    """测试 AgentState 的更新操作"""
    
    def test_update_context(self):
        """测试 update_context() 方法"""
        state = AgentState(
            target="https://www.baidu.com",
            task_id="test_task_002"
        )
        
        state.update_context("cms", "WordPress")
        assert state.target_context["cms"] == "WordPress"
    
    def test_add_vulnerability(self):
        """测试 add_vulnerability() 方法"""
        state = AgentState(
            target="https://www.baidu.com",
            task_id="test_task_002"
        )
        
        vuln = {
            "type": "XSS",
            "severity": "Medium",
            "title": "Test XSS"
        }
        state.add_vulnerability(vuln)
        assert len(state.vulnerabilities) == 1
        assert state.vulnerabilities[0]["type"] == "XSS"
    
    def test_add_error(self):
        """测试 add_error() 方法"""
        state = AgentState(
            target="https://www.baidu.com",
            task_id="test_task_002"
        )
        
        state.add_error("Test error")
        assert "Test error" in state.errors
    
    def test_mark_complete(self):
        """测试 mark_complete() 方法"""
        state = AgentState(
            target="https://www.baidu.com",
            task_id="test_task_002"
        )
        
        state.mark_complete()
        assert state.is_complete == True
        assert state.should_continue == False
    
    def test_to_dict(self):
        """测试 to_dict() 方法"""
        state = AgentState(
            target="https://www.baidu.com",
            task_id="test_task_002"
        )
        
        state_dict = state.to_dict()
        assert isinstance(state_dict, dict)
        assert state_dict["target"] == state.target
        assert state_dict["task_id"] == state.task_id
        assert "vulnerabilities" in state_dict
        assert "errors" in state_dict

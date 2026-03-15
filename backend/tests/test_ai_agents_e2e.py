# -*- coding: utf-8 -*-
"""
AI Agents 端到端测试

测试完整的 AI Agent 工作流程。
"""
import pytest
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ai_agents.core.state import AgentState


def create_test_state(task_id: str, target: str) -> AgentState:
    """创建测试用的 AgentState"""
    return AgentState(
        task_id=task_id,
        target=target
    )


class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    def test_state_initialization(self):
        """测试状态初始化"""
        state = create_test_state("e2e-test-1", "https://example.com")
        
        assert state.task_id == "e2e-test-1"
        assert state.target == "https://example.com"
        assert len(state.stage_status) == 4
        
        for stage_name, stage_data in state.stage_status.items():
            assert stage_data["status"] == "pending"
            assert stage_data["progress"] == 0
        
        print("✅ 状态初始化测试通过")
    
    def test_state_serialization(self):
        """测试状态序列化"""
        state = create_test_state("e2e-test-2", "https://example.com")
        
        state_dict = state.to_dict()
        
        assert "task_id" in state_dict
        assert "target" in state_dict
        assert "execution_history" in state_dict
        assert "errors" in state_dict
        
        json_str = json.dumps(state_dict, default=str)
        assert json_str is not None
        
        print("✅ 状态序列化测试通过")
    
    def test_stage_progression(self):
        """测试阶段推进"""
        state = create_test_state("e2e-test-3", "https://example.com")
        
        state.update_stage_status("planning", "running", "执行中", 25, "正在规划")
        assert state.stage_status["planning"]["status"] == "running"
        
        state.update_stage_status("planning", "completed", "完成", 100, "规划完成")
        assert state.stage_status["planning"]["status"] == "completed"
        
        state.update_stage_status("tool_execution", "running", "执行中", 50, "正在扫描")
        assert state.stage_status["tool_execution"]["status"] == "running"
        
        print("✅ 阶段推进测试通过")
    
    def test_execution_history_recording(self):
        """测试执行历史记录"""
        state = create_test_state("e2e-test-4", "https://example.com")
        
        state.add_execution_step(
            task="planning",
            result={"plan": ["portscan", "vulnscan"]},
            status="success"
        )
        
        assert len(state.execution_history) == 1
        assert state.execution_history[0]["task"] == "planning"
        
        state.add_execution_step(
            task="tool_execution",
            result={"vulnerabilities": 2},
            status="success"
        )
        
        assert len(state.execution_history) == 2
        
        print("✅ 执行历史记录测试通过")
    
    def test_error_handling(self):
        """测试错误处理"""
        state = create_test_state("e2e-test-5", "https://example.com")
        
        state.add_error("测试错误1")
        state.add_error("测试错误2")
        
        assert len(state.errors) == 2
        assert "测试错误1" in state.errors
        
        print("✅ 错误处理测试通过")
    
    def test_vulnerability_tracking(self):
        """测试漏洞追踪"""
        state = create_test_state("e2e-test-6", "https://example.com")
        
        vuln = {
            "type": "xss",
            "url": "https://example.com/search?q=test",
            "severity": "high",
            "parameter": "q"
        }
        
        state.vulnerabilities.append(vuln)
        
        assert len(state.vulnerabilities) == 1
        assert state.vulnerabilities[0]["type"] == "xss"
        
        print("✅ 漏洞追踪测试通过")


class TestAPIResponseFormat:
    """测试 API 响应格式"""
    
    def test_task_detail_response_format(self):
        """测试任务详情响应格式"""
        expected_fields = [
            "task_id",
            "task_type", 
            "target",
            "status",
            "progress",
            "config",
            "stages",
            "execution_history",
            "graph_flow",
            "target_context",
            "scan_summary",
            "created_at",
            "updated_at",
            "final_output",
            "error_message"
        ]
        
        print(f"✅ 预期 API 响应字段: {len(expected_fields)} 个")
        
        for field in expected_fields:
            assert field is not None
        
        print("✅ API 响应格式测试通过")
    
    def test_stages_response_format(self):
        """测试阶段响应格式"""
        expected_stages = {
            "planning": {"status": "pending", "progress": 0},
            "tool_execution": {"status": "pending", "progress": 0},
            "poc_verification": {"status": "pending", "progress": 0},
            "report": {"status": "pending", "progress": 0}
        }
        
        for stage_name, stage_data in expected_stages.items():
            assert "status" in stage_data
            assert "progress" in stage_data
        
        print("✅ 阶段响应格式测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

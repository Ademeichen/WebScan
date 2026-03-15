# -*- coding: utf-8 -*-
"""
AI Agents 子图测试

测试 AI Agents 的各个子图功能是否正常。
使用真实配置进行测试，不使用 Mock 模拟。
"""
import pytest
import asyncio
import sys
import os
from pathlib import Path

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


class TestAgentState:
    """测试 AgentState"""
    
    def test_agent_state_creation(self):
        """测试 AgentState 创建"""
        state = create_test_state("test-task-1", "https://example.com")
        
        assert state.task_id == "test-task-1"
        assert state.target == "https://example.com"
        assert len(state.stage_status) == 4
        print(f"✅ AgentState 创建成功")
    
    def test_stage_status_structure(self):
        """测试阶段状态结构"""
        state = create_test_state("test-task-6", "https://example.com")
        
        expected_stages = ["planning", "tool_execution", "poc_verification", "report"]
        for stage in expected_stages:
            assert stage in state.stage_status
            assert "status" in state.stage_status[stage]
            assert "progress" in state.stage_status[stage]
        
        print(f"✅ 阶段状态结构正确")
    
    def test_update_stage_status(self):
        """测试更新阶段状态"""
        state = create_test_state("test-task-7", "https://example.com")
        
        state.update_stage_status("planning", "running", "执行中", 50, "正在规划")
        
        assert state.stage_status["planning"]["status"] == "running"
        assert state.stage_status["planning"]["progress"] == 50
        print(f"✅ 阶段状态更新成功")


class TestPlanningNode:
    """测试规划节点 - 使用真实 AI 配置"""
    
    def test_planning_node_initialization(self):
        """测试规划节点初始化"""
        from backend.ai_agents.core.nodes import TaskPlanningNode
        node = TaskPlanningNode()
        assert node is not None
        print("✅ TaskPlanningNode 初始化成功")
    
    @pytest.mark.asyncio
    async def test_planning_node_execution_real(self):
        """测试规划节点执行 - 使用真实 AI"""
        from backend.ai_agents.core.nodes import TaskPlanningNode
        node = TaskPlanningNode()
        state = create_test_state("real-planning-test", "https://www.example.com")
        
        result = await node(state)
        
        assert result is not None
        assert result.task_id == "real-planning-test"
        assert len(result.execution_history) > 0
        print(f"✅ TaskPlanningNode 真实执行成功，执行历史: {len(result.execution_history)} 条")


class TestVulnerabilityScanNode:
    """测试漏洞扫描节点 - 使用真实配置"""
    
    def test_vulnerability_scan_node_initialization(self):
        """测试漏洞扫描节点初始化"""
        from backend.ai_agents.core.nodes import VulnerabilityScanNode
        node = VulnerabilityScanNode()
        assert node is not None
        print("✅ VulnerabilityScanNode 初始化成功")
    
    @pytest.mark.asyncio
    async def test_vulnerability_scan_node_execution_real(self):
        """测试漏洞扫描节点执行 - 使用真实配置"""
        from backend.ai_agents.core.nodes import VulnerabilityScanNode
        node = VulnerabilityScanNode()
        state = create_test_state("real-vulnscan-test", "https://www.example.com")
        
        result = await node(state)
        
        assert result is not None
        assert result.task_id == "real-vulnscan-test"
        print(f"✅ VulnerabilityScanNode 真实执行成功")


class TestReportGenerationNode:
    """测试报告生成节点 - 使用真实配置"""
    
    def test_report_generation_node_initialization(self):
        """测试报告生成节点初始化"""
        from backend.ai_agents.core.nodes import ReportGenerationNode
        node = ReportGenerationNode()
        assert node is not None
        print("✅ ReportGenerationNode 初始化成功")
    
    @pytest.mark.asyncio
    async def test_report_generation_node_execution_real(self):
        """测试报告生成节点执行 - 使用真实配置"""
        from backend.ai_agents.core.nodes import ReportGenerationNode
        node = ReportGenerationNode()
        state = create_test_state("real-report-test", "https://www.example.com")
        
        result = await node(state)
        
        assert result is not None
        assert result.task_id == "real-report-test"
        assert result.is_complete == True
        print(f"✅ ReportGenerationNode 真实执行成功")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

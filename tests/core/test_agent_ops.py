import pytest
import asyncio
from unittest.mock import MagicMock
from msc.core.tools.agent_ops import CreateAgentTool
from msc.core.tools.base import ToolContext

@pytest.mark.asyncio
async def test_create_agent_returns_valid_id():
    # Setup context
    mock_oracle = MagicMock()
    mock_gateway = MagicMock()
    context = ToolContext(
        agent_id="main-agent",
        workspace_root=".",
        oracle=mock_oracle,
        gateway=mock_gateway
    )
    tool = CreateAgentTool(context)
    
    # Execute
    agent_id = await tool.execute(task_description="Test sub-task")
    
    # Verify
    assert agent_id.startswith("agent-")
    assert len(agent_id) > 6

@pytest.mark.asyncio
async def test_create_agent_identity_binding():
    # This test will verify that the agent_id is correctly bound in the context
    # and cannot be spoofed via parameters (if we decide to enforce it at tool level)
    mock_oracle = MagicMock()
    context = ToolContext(
        agent_id="main-agent",
        workspace_root=".",
        oracle=mock_oracle
    )
    tool = CreateAgentTool(context)
    
    # Even if we pass a different agent_id in kwargs (if the tool supported it), 
    # it should use the one from context.
    # Currently CreateAgentTool doesn't take agent_id as arg, which is good.
    assert tool.context.agent_id == "main-agent"

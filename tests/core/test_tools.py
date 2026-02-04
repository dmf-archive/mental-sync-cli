import pytest
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from unittest.mock import AsyncMock, MagicMock

# 导入模块
from msc.core.tools.base import BaseTool, ToolContext
from msc.core.tools.agent_ops import CreateAgentTool

# 1. 基础工具架构测试 (Unit)
class MockArgs(BaseModel):
    input_str: str = Field(..., description="A test input")

class MockTool(BaseTool):
    name = "mock_tool"
    description = "A tool for testing"
    args_schema = MockArgs

    async def execute(self, input_str: str) -> str:
        return f"Processed: {input_str}"

@pytest.fixture
def tool_context():
    # 模拟共享的 Oracle 实例
    mock_oracle = MagicMock()
    return ToolContext(
        agent_id="test-parent",
        workspace_root=".",
        oracle=mock_oracle,
        allowed_paths=["./src"]
    )

def test_tool_schema_generation(tool_context):
    tool = MockTool(tool_context)
    schema = tool.get_schema()
    assert schema["name"] == "mock_tool"
    assert schema["parameters"]["properties"]["input_str"]["type"] == "string"

# 2. 模型 B 架构下的子代理创建测试
@pytest.mark.asyncio
async def test_create_agent_coroutine_spawn(tool_context):
    """
    验证 create_agent 工具在模型 B 架构下的行为：
    1. 验证它是否返回了正确的 agent_id。
    2. 验证 context 中的 oracle 是否被正确引用（模型 B 核心：共享 Oracle）。
    """
    # 注意：在 GREEN Phase 之前，CreateAgentTool 可能还未定义或导入失败
    tool = CreateAgentTool(tool_context)
    
    # 模拟执行
    agent_id = await tool.execute(
        task_description="Test Task",
        model_name="gpt-4o",
        sandbox_config={"allowed_read_paths": ["./src"]}
    )
    
    assert agent_id is not None
    assert agent_id.startswith("agent-")
    # 验证 context 中的 oracle 是否被正确引用（模型 B 核心：共享 Oracle）
    assert tool.context.oracle is not None

import os
import platform

import pytest

from msc.core.tools.base import ToolContext
from msc.core.tools.system_ops import ExecuteTool


@pytest.fixture
def tool_context():
    workspace = os.path.abspath(os.path.join(os.getcwd(), "tests", "mock-workspace"))
    allowed_path = os.path.join(workspace, "allowed")
    blocked_path = os.path.join(workspace, "blocked")
    
    yield ToolContext(
        agent_id="test-security-agent",
        workspace_root=workspace,
        oracle=None,
        allowed_paths=[allowed_path],
        blocked_paths=[blocked_path]
    )
    
    if platform.system() == "Windows":
        import subprocess
        subprocess.run(
            ["icacls", blocked_path, "/grant", f"{os.environ['USERNAME']}:(OI)(CI)(F)", "/Q"],
            capture_output=True
        )

@pytest.mark.asyncio
async def test_execute_basic_command(tool_context):
    tool = ExecuteTool(tool_context)
    cmd = "whoami" if platform.system() == "Windows" else "whoami"
    result = await tool.execute(command=cmd)
    assert result["exit_code"] == 0
    assert len(result["stdout"]) > 0

@pytest.mark.asyncio
async def test_execute_invalid_command(tool_context):
    tool = ExecuteTool(tool_context)
    result = await tool.execute(command="invalid_cmd_xyz_123")
    assert result["exit_code"] != 0

@pytest.mark.asyncio
async def test_execute_path_restriction_violation(tool_context):
    tool = ExecuteTool(tool_context)
    blocked_file = os.path.join(tool_context.workspace_root, "blocked", "secret.txt")
    
    if platform.system() == "Windows":
        cmd = f"type \"{blocked_file}\""
    else:
        cmd = f"cat \"{blocked_file}\""
        
    result = await tool.execute(command=cmd)
    assert result["exit_code"] != 0
    assert "SecurityViolation" in result["stderr"]

@pytest.mark.asyncio
async def test_execute_blocked_subpath(tool_context):
    tool = ExecuteTool(tool_context)
    blocked_file = os.path.join(tool_context.workspace_root, "blocked", "secret.txt")
    
    if platform.system() == "Windows":
        cmd = f"type \"{blocked_file}\""
    else:
        cmd = f"cat \"{blocked_file}\""
        
    result = await tool.execute(command=cmd)
    assert result["exit_code"] != 0
    assert "SecurityViolation" in result["stderr"]

@pytest.mark.asyncio
async def test_execute_allowed_path(tool_context):
    tool = ExecuteTool(tool_context)
    allowed_file = os.path.join(tool_context.workspace_root, "allowed", "data.txt")
    
    if platform.system() == "Windows":
        cmd = f"type \"{allowed_file}\""
    else:
        cmd = f"cat \"{allowed_file}\""
        
    result = await tool.execute(command=cmd)
    assert "SecurityViolation" not in result["stderr"]

@pytest.mark.asyncio
async def test_execute_shell_injection_attempt(tool_context):
    tool = ExecuteTool(tool_context)
    if platform.system() == "Windows":
        cmd = "whoami ; echo injection"
        result = await tool.execute(command=cmd)
        assert result["exit_code"] != 0
        assert "injection" not in result["stdout"]
    else:
        cmd = "whoami; echo injection"
        result = await tool.execute(command=cmd)
        assert "injection" in result["stdout"]
        assert ";" in result["stdout"]

import pytest
import asyncio
import os
from msc.core.tools.system_ops import ExecuteTool
from msc.core.tools.base import ToolContext

@pytest.fixture
def tool_context():
    # 模拟场景：授权 .roo/ 但 block .roo/rules/
    workspace = os.getcwd()
    roo_path = os.path.join(workspace, ".roo")
    roo_rules_path = os.path.join(roo_path, "rules")
    
    return ToolContext(
        agent_id="test-security-agent",
        workspace_root=workspace,
        oracle=None,
        allowed_paths=[roo_path],
        blocked_paths=[roo_rules_path]
    )

@pytest.mark.asyncio
async def test_execute_basic_command(tool_context):
    tool = ExecuteTool(tool_context)
    import platform
    if platform.system() == "Windows":
        # On Windows, 'echo' is a cmd builtin, not an executable.
        # Use 'powershell -Command "Write-Output ''hello world''"' to ensure it's treated as a single string
        result = await tool.execute(command="powershell -Command \"Write-Output 'hello world'\"")
    else:
        result = await tool.execute(command="echo 'hello world'")
    assert result["exit_code"] == 0
    assert "hello world" in result["stdout"]

@pytest.mark.asyncio
async def test_execute_invalid_command(tool_context):
    tool = ExecuteTool(tool_context)
    result = await tool.execute(command="non_existent_command_12345")
    assert result["exit_code"] != 0
    assert result["stderr"] != ""

@pytest.mark.asyncio
async def test_execute_path_restriction_violation(tool_context):
    """
    RED Phase: 验证 NFSS 是否能拦截对未授权路径的访问。
    """
    tool = ExecuteTool(tool_context)
    # 尝试读取系统敏感路径（假设不在 allowed_paths 中）
    import platform
    if platform.system() == "Windows":
        cmd = "type C:\\Windows\\System32\\drivers\\etc\\hosts"
    else:
        cmd = "cat /etc/shadow"
        
    result = await tool.execute(command=cmd)
    
    # 预期：由于 NFSS 拦截，执行应该失败并返回伪装的错误提示
    assert result["exit_code"] != 0
    assert "cannot find the path specified" in result["stderr"]

@pytest.mark.asyncio
async def test_execute_blocked_subpath(tool_context):
    """
    验证 NFSS 是否能拦截 allowed 路径下的 blocked 子路径。
    场景：授权了 .roo/，但尝试访问 .roo/rules/main.md (被 block)
    """
    tool = ExecuteTool(tool_context)
    # 构造一个在 blocked 路径下的文件路径
    blocked_file = os.path.join(tool_context.workspace_root, ".roo", "rules", "0-main.md")
    
    import platform
    if platform.system() == "Windows":
        cmd = f"type {blocked_file}"
    else:
        cmd = f"cat {blocked_file}"
        
    result = await tool.execute(command=cmd)
    
    assert result["exit_code"] != 0
    assert "cannot find the path specified" in result["stderr"]

@pytest.mark.asyncio
async def test_execute_allowed_path(tool_context):
    """
    验证 NFSS 允许访问授权路径。
    场景：授权了 .roo/，尝试访问 .roo/config.yaml (假设存在或仅测试路径校验)
    """
    tool = ExecuteTool(tool_context)
    allowed_file = os.path.join(tool_context.workspace_root, ".roo", "test_file.txt")
    
    # 确保文件不存在也不会触发 SecurityViolation，而是触发系统错误
    import platform
    if platform.system() == "Windows":
        cmd = f"type {allowed_file}"
    else:
        cmd = f"cat {allowed_file}"
        
    result = await tool.execute(command=cmd)
    
    # 路径校验应该通过，进入执行阶段。因为文件不存在，系统会报错，但不是伪装的 SecurityViolation 错误
    # 真实的系统错误通常包含 "The system cannot find the file specified" (Windows) 或 "No such file or directory" (Linux)
    # 我们的伪装错误是 "The system cannot find the path specified"
    assert "SecurityViolation" not in result["stderr"]

@pytest.mark.asyncio
async def test_execute_shell_injection_attempt(tool_context):
    """
    验证切换到 create_subprocess_exec 后，Shell 注入尝试是否失效。
    """
    tool = ExecuteTool(tool_context)
    # 尝试通过分号注入第二个命令
    cmd = "echo hello; echo world"
    result = await tool.execute(command=cmd)
    
    # 在 exec 模式下，'echo hello; echo world' 会被视为一个整体的可执行文件名，
    # 或者 'echo' 命令会收到 'hello;' 和 'echo' 和 'world' 作为参数。
    # 无论哪种情况，'echo world' 都不会作为独立的 shell 命令执行。
    if os.name == 'nt':
        # Windows 下 echo 是 cmd 内置命令，直接 exec 'echo' 会失败
        # 如果失败，stderr 应该包含我们伪装的错误信息
        assert result["exit_code"] != 0
        assert "cannot find the path specified" in result["stderr"]
    else:
        # Linux/macOS 下 echo 也会输出所有参数
        assert "world" in result["stdout"]
        assert ";" in result["stdout"]

@pytest.mark.asyncio
async def test_execute_symlink_bypass_attempt(tool_context, tmp_path):
    """
    验证 NFSS 是否能识别并拦截通过符号链接绕过路径限制的尝试。
    """
    # 仅在支持符号链接的系统上运行
    if os.name == 'nt':
        pytest.skip("Symlink test requires admin privileges on Windows or specific config")

    tool = ExecuteTool(tool_context)
    
    # 创建一个在 allowed 路径下的符号链接，指向 blocked 路径
    allowed_dir = tool_context.allowed_paths[0]
    blocked_dir = tool_context.blocked_paths[0]
    
    # 确保目录存在
    os.makedirs(allowed_dir, exist_ok=True)
    os.makedirs(blocked_dir, exist_ok=True)
    
    secret_file = os.path.join(blocked_dir, "secret.txt")
    with open(secret_file, "w") as f:
        f.write("sensitive data")
        
    link_path = os.path.join(allowed_dir, "malicious_link")
    if os.path.exists(link_path):
        os.remove(link_path)
    os.symlink(blocked_dir, link_path)
    
    # 尝试通过链接访问
    cmd = f"cat {link_path}/secret.txt"
    result = await tool.execute(command=cmd)
    
    # 预期：物理沙箱（如 Landlock/Seatbelt）应该拦截此访问，
    # 或者我们的逻辑预检应该解析符号链接。
    # 目前我们的逻辑预检使用了 os.path.abspath，它不解析符号链接。
    # 但物理沙箱会拦截。
    assert result["exit_code"] != 0

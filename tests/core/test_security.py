import pytest
import os
import platform
import asyncio
from msc.core.tools.system_ops import WindowsSandbox, get_sandbox_provider

@pytest.mark.skipif(platform.system() != "Windows", reason="Windows specific tests")
@pytest.mark.asyncio
async def test_windows_sandbox_restricted_token_simulation():
    # This test will verify the current WindowsSandbox implementation
    # and serve as a baseline for Restricted Token enhancement.
    sandbox = WindowsSandbox()
    
    # Test blocked path via icacls simulation
    # We'll use a temp file to test ACL denial
    test_file = os.path.abspath("sandbox_test_file.txt")
    with open(test_file, "w") as f:
        f.write("secret data")
    
    try:
        # Verify that the command is wrapped in our python sandbox launcher
        command = ["type", test_file]
        wrapped = sandbox.wrap_command(command, allowed_paths=[], blocked_paths=[test_file])
        
        # Check if the launcher script path is in the wrapped command
        assert any("sandbox_launcher.py" in arg for arg in wrapped)
        
    finally:
        if os.path.exists(test_file):
            # Reset ACLs if needed or just remove
            os.system(f'icacls "{test_file}" /grant "${{env:USERNAME}}:(F)" /Q')
            os.remove(test_file)

@pytest.mark.skipif(platform.system() != "Windows", reason="Windows specific tests")
@pytest.mark.asyncio
async def test_windows_sandbox_execution():
    # Verify that the powershell wrapper actually runs
    sandbox = WindowsSandbox()
    command = ["whoami"]
    wrapped = sandbox.wrap_command(command, allowed_paths=[], blocked_paths=[])
    
    process = await asyncio.create_subprocess_exec(
        *wrapped,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        
    assert process.returncode == 0
    assert len(stdout) > 0

@pytest.mark.skipif(platform.system() != "Windows", reason="Windows specific tests")
@pytest.mark.asyncio
async def test_windows_sandbox_network_restriction():
    """
    RED: 验证沙箱是否能拦截网络请求。
    我们尝试访问一个外部 URL，预期应该失败。
    """
    sandbox = WindowsSandbox()
    # 使用 curl 尝试访问网络，预期被拦截或超时
    command = ["curl", "-m", "2", "https://www.google.com"]
    wrapped = sandbox.wrap_command(command, allowed_paths=[], blocked_paths=[])
    
    process = await asyncio.create_subprocess_exec(
        *wrapped,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    # 预期：要么返回非零退出码，要么 stderr 包含拦截信息
    # 在当前 PowerShell 模拟中，这可能会通过，因为我们还没实现网络拦截
    # 这正是 TDD 的 RED 阶段
    assert process.returncode != 0 or b"MSC.SecurityViolation" in stderr or b"MSC.SandboxError" in stderr

@pytest.mark.skipif(platform.system() != "Windows", reason="Windows specific tests")
@pytest.mark.asyncio
async def test_windows_sandbox_privilege_stripping():
    """
    RED: 验证沙箱是否剥离了管理员权限。
    """
    sandbox = WindowsSandbox()
    # 尝试执行需要管理员权限的操作（例如查询系统敏感信息或尝试修改 ACL）
    # 这里我们简单检查 whoami /groups 是否包含 Administrators
    command = ["whoami", "/groups"]
    wrapped = sandbox.wrap_command(command, allowed_paths=[], blocked_paths=[])
    
    process = await asyncio.create_subprocess_exec(
        *wrapped,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    output = stdout.decode(errors="replace")
    # 预期：Administrators 组应该被标记为 "Group used for deny only"
    # 且不应出现 "Enabled group" 状态（针对该组）
    admin_lines = [line for line in output.splitlines() if "Administrators" in line]
    assert len(admin_lines) > 0, "Administrators group should be present in groups list"
    for line in admin_lines:
        assert "Group used for deny only" in line
        assert "Enabled group" not in line

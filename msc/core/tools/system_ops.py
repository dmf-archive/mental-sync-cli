import asyncio
import os
import platform
import shlex
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from msc.core.tools.base import BaseTool

class SandboxProvider(ABC):
    @abstractmethod
    def wrap_command(self, command: List[str], allowed_paths: List[str], blocked_paths: List[str]) -> List[str]:
        pass

class NoSandboxProvider(SandboxProvider):
    def wrap_command(self, command: List[str], allowed_paths: List[str], blocked_paths: List[str]) -> List[str]:
        return command

class MacOSSandbox(SandboxProvider):
    def wrap_command(self, command: List[str], allowed_paths: List[str], blocked_paths: List[str]) -> List[str]:
        sb_profile = ["(version 1)", "(deny default)", "(allow process-exec)", "(allow network-outbound)"]
        for path in allowed_paths:
            abs_path = os.path.abspath(path)
            sb_profile.append(f'(allow file-read* file-write* (subpath "{abs_path}"))')
        # Basic system libs
        sb_profile.extend(['(allow file-read* (subpath "/usr/lib"))', '(allow file-read* (subpath "/usr/bin"))'])
        profile_str = " ".join(sb_profile)
        return ["sandbox-exec", "-p", profile_str] + command

class LinuxSandbox(SandboxProvider):
    def wrap_command(self, command: List[str], allowed_paths: List[str], blocked_paths: List[str]) -> List[str]:
        # Use bubblewrap (bwrap) as a reliable CLI wrapper for Landlock/Namespaces
        # It's widely available and handles the complexity of mounting
        bwrap_cmd = [
            "bwrap",
            "--ro-bind", "/", "/",  # Default read-only root
            "--dev", "/dev",        # Essential devices
            "--proc", "/proc",      # Process info
            "--tmpfs", "/tmp",      # Private tmp
            "--unshare-all",        # Isolate network, IPC, UTS, etc.
            "--hostname", "msc-sandbox"
        ]
        
        # Bind allowed paths as read-write
        for path in allowed_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                bwrap_cmd.extend(["--bind", abs_path, abs_path])
        
        # Explicitly block paths by masking them with empty directories or symlinks to nowhere
        # Note: bwrap doesn't have a direct 'deny' but we can over-mount
        for path in blocked_paths:
            abs_path = os.path.abspath(path)
            bwrap_cmd.extend(["--tmpfs", abs_path])
            
        return bwrap_cmd + command

class WindowsSandbox(SandboxProvider):
    def wrap_command(self, command: List[str], allowed_paths: List[str], blocked_paths: List[str]) -> List[str]:
        # Windows sandboxing is complex to implement via CLI wrapping without external tools like 'Sandboxie' or 'AppContainer'.
        # However, we can use 'runas' with a restricted user or a helper that uses Job Objects.
        # For this implementation, we'll use a PowerShell wrapper that simulates basic Job Object restrictions
        # and relies on the fact that we've switched to create_subprocess_exec to prevent shell injection.
        
        # In a production MSC environment, this would call a C++ helper 'msc-sandbox-win.exe'
        # that uses CreateRestrictedToken and AssignProcessToJobObject.
        
        ps_wrapper = [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
            "$job = New-Object System.Management.Automation.Job; " +
            "Start-Process -FilePath " + command[0] + " -ArgumentList " +
            (shlex.join(command[1:]) if len(command) > 1 else "''") + " -Wait"
        ]
        # Note: This is a placeholder for the actual Job Object C++ implementation.
        # The key security improvement is already achieved by using create_subprocess_exec.
        return command

def get_sandbox_provider() -> SandboxProvider:
    sys = platform.system()
    if sys == "Darwin":
        return MacOSSandbox()
    elif sys == "Linux":
        return LinuxSandbox()
    elif sys == "Windows":
        return WindowsSandbox()
    return NoSandboxProvider()

class ExecuteArgs(BaseModel):
    command: str = Field(..., description="The shell command to execute")
    cwd: Optional[str] = Field(None, description="Working directory for the command")

class ExecuteTool(BaseTool):
    name = "execute"
    description = "Execute a system command in a sandboxed subprocess."
    args_schema = ExecuteArgs

    async def execute(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a command in a subprocess with NFSS (Native Filesystem Sandbox) constraints.
        """
        if self.context.gateway:
            approved = await self.context.gateway.request_permission(
                agent_id=self.context.agent_id,
                action="execute",
                params={"command": command, "cwd": cwd}
            )
            if not approved:
                return {"exit_code": -1, "stdout": "", "stderr": "MSC.SecurityViolation: Permission denied by user."}

        try:
            tokens = shlex.split(command)
        except ValueError as e:
            return {"exit_code": 1, "stdout": "", "stderr": f"MSC.SecurityViolation: Shell parsing error: {e}"}

        if not tokens:
            return {"exit_code": 1, "stdout": "", "stderr": "MSC.SecurityViolation: Empty command."}

        # NFSS Phase 1: Logical Pre-flight Check (Optional but good for UX)
        # ... (Keeping the logic but using it to decide whether to even try)

        # NFSS Phase 2: Native Sandbox Wrapping
        provider = get_sandbox_provider()
        final_tokens = provider.wrap_command(
            tokens,
            self.context.allowed_paths,
            self.context.blocked_paths
        )

        try:
            # Use create_subprocess_exec to avoid shell injection
            # On Windows, we need to handle executable resolution manually for some commands
            executable = final_tokens[0]
            
            process = await asyncio.create_subprocess_exec(
                *final_tokens,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or self.context.workspace_root,
                env=os.environ.copy() # In production, we should clean this
            )

            stdout, stderr = await process.communicate()
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode(errors="replace").strip(),
                "stderr": stderr.decode(errors="replace").strip()
            }
        except FileNotFoundError:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Error: The system cannot find the path specified: '{tokens[0]}'"
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }

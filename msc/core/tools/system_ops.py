import asyncio
import os
import platform
import shlex
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from msc.core.tools.base import BaseTool


class SandboxProvider(ABC):
    @abstractmethod
    def wrap_command(self, command: list[str], allowed_paths: list[str], blocked_paths: list[str]) -> list[str]:
        pass

class NoSandboxProvider(SandboxProvider):
    def wrap_command(self, command: list[str], allowed_paths: list[str], blocked_paths: list[str]) -> list[str]:
        _ = allowed_paths
        _ = blocked_paths
        return command

class MacOSSandbox(SandboxProvider):
    def wrap_command(self, command: list[str], allowed_paths: list[str], blocked_paths: list[str]) -> list[str]:
        sb_profile = ["(version 1)", "(deny default)", "(allow process-exec)", "(allow network-outbound)"]
        for path in allowed_paths:
            abs_path = os.path.abspath(path)
            sb_profile.append(f'(allow file-read* file-write* (subpath "{abs_path}"))')
        sb_profile.extend(['(allow file-read* (subpath "/usr/lib"))', '(allow file-read* (subpath "/usr/bin"))'])
        profile_str = " ".join(sb_profile)
        return ["sandbox-exec", "-p", profile_str] + command

class LinuxSandbox(SandboxProvider):
    def wrap_command(self, command: list[str], allowed_paths: list[str], blocked_paths: list[str]) -> list[str]:
        bwrap_cmd = [
            "bwrap",
            "--ro-bind", "/", "/",
            "--dev", "/dev",
            "--proc", "/proc",
            "--tmpfs", "/tmp",
            "--unshare-all",
            "--hostname", "msc-sandbox"
        ]
        for path in allowed_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                bwrap_cmd.extend(["--bind", abs_path, abs_path])
        for path in blocked_paths:
            abs_path = os.path.abspath(path)
            bwrap_cmd.extend(["--tmpfs", abs_path])
        return bwrap_cmd + command

class WindowsSandbox(SandboxProvider):
    def wrap_command(self, command: list[str], allowed_paths: list[str], blocked_paths: list[str]) -> list[str]:
        _ = allowed_paths
        acl_commands = []
        for path in blocked_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                acl_commands.append(f'icacls "{abs_path}" /deny "${{env:USERNAME}}:(OI)(CI)(R,W,D)" /Q')

        cmd_exe = command[0]
        cmd_args = shlex.join(command[1:]) if len(command) > 1 else ""
        cmd_args_escaped = cmd_args.replace('"', '`"')
        
        ps_wrapper = [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
            f"""
            $OutputEncoding = [System.Text.Encoding]::UTF8;
            {"; ".join(acl_commands) if acl_commands else " # No ACLs"};
            $pinfo = New-Object System.Diagnostics.ProcessStartInfo;
            $pinfo.FileName = "{cmd_exe}";
            $pinfo.Arguments = "{cmd_args_escaped}";
            $pinfo.UseShellExecute = $false;
            $pinfo.CreateNoWindow = $true;
            $pinfo.RedirectStandardOutput = $true;
            $pinfo.RedirectStandardError = $true;
            try {{
                $process = [System.Diagnostics.Process]::Start($pinfo);
                $stdout = $process.StandardOutput.ReadToEnd();
                $stderr = $process.StandardError.ReadToEnd();
                $process.WaitForExit();
                Write-Host $stdout -NoNewline;
                [Console]::Error.Write($stderr);
                exit $process.ExitCode;
            }} catch {{
                exit 1;
            }}
            """
        ]
        return ps_wrapper

def get_sandbox_provider() -> SandboxProvider:
    sys = platform.system()
    if sys == "Darwin":
        return MacOSSandbox()
    if sys == "Linux":
        return LinuxSandbox()
    if sys == "Windows":
        return WindowsSandbox()
    return NoSandboxProvider()

class ExecuteArgs(BaseModel):
    command: str = Field(..., description="The shell command to execute")
    cwd: str | None = Field(None, description="Working directory for the command")

class ExecuteTool(BaseTool):
    name = "execute"
    description = "Execute a system command in a sandboxed subprocess."
    args_schema = ExecuteArgs

    async def execute(self, **kwargs: Any) -> Any:
        command: str = kwargs["command"]
        cwd: str | None = kwargs.get("cwd")
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

        def normalize_path(p: str) -> str:
            return os.path.normpath(os.path.abspath(p)).lower()

        cmd_full_norm = " ".join(tokens).lower()
        for blocked in self.context.blocked_paths:
            blocked_norm = normalize_path(blocked)
            if blocked_norm in cmd_full_norm or blocked.lower() in cmd_full_norm:
                return {
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": f"MSC.SecurityViolation: Access to blocked path '{blocked}' is forbidden."
                }

        provider = get_sandbox_provider()
        final_tokens = provider.wrap_command(
            tokens,
            self.context.allowed_paths,
            self.context.blocked_paths
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *final_tokens,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or self.context.workspace_root,
                env=os.environ.copy()
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

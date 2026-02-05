import os
import shlex
import sys
import uuid

try:
    import win32api
    import win32con
    import win32event
    import win32job
    import win32process
    import win32security
    import win32com.client
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False

def apply_network_block(exe_path: str) -> str | None:
    """尝试通过 Windows 防火墙拦截特定路径的出站流量"""
    try:
        fw_policy = win32com.client.Dispatch("HNetCfg.FwPolicy2")
        rule = win32com.client.Dispatch("HNetCfg.FWRule")
        rule_name = f"MSC_Block_{uuid.uuid4().hex[:8]}"
        rule.Name = rule_name
        rule.Description = "MSC Sandbox Outbound Block"
        rule.ApplicationName = exe_path
        rule.Direction = 2 # NET_FW_RULE_DIR_OUT
        rule.Action = 0    # NET_FW_ACTION_BLOCK
        rule.Enabled = True
        fw_policy.Rules.Add(rule)
        return rule_name
    except Exception:
        return None

def remove_network_block(rule_name: str):
    try:
        fw_policy = win32com.client.Dispatch("HNetCfg.FwPolicy2")
        fw_policy.Rules.Remove(rule_name)
    except Exception:
        pass

def run_sandboxed(cmd_line: str, blocked_paths: list[str]):
    if not HAS_PYWIN32:
        sys.stderr.write("MSC.SandboxError: pywin32 not found in launcher context.\n")
        sys.exit(1)
    
    rule_name = None
    try:
        # 1. Create Restricted Token
        h_token = win32security.OpenProcessToken(win32process.GetCurrentProcess(), win32security.TOKEN_ALL_ACCESS)
        
        # Disable Administrators group
        sid_admin = win32security.CreateWellKnownSid(win32security.WinBuiltinAdministratorsSid)
        sids_to_disable = [(sid_admin, 0)]
        
        # Create the restricted token
        # DISABLE_MAX_PRIVILEGE (0x1) removes all privileges except those specifically needed
        token_r = win32security.CreateRestrictedToken(h_token, win32security.DISABLE_MAX_PRIVILEGE, sids_to_disable, None, None)
        
        # 2. Create Job Object for resource and UI isolation
        h_job = win32job.CreateJobObject(None, "")
        info = win32job.QueryInformationJobObject(h_job, win32job.JobObjectExtendedLimitInformation)
        info['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        win32job.SetInformationJobObject(h_job, win32job.JobObjectExtendedLimitInformation, info)
        
        # UI Restrictions
        win32job.SetInformationJobObject(h_job, win32job.JobObjectBasicUIRestrictions, {'UIRestrictionsClass': win32job.JOB_OBJECT_UILIMIT_ALL})

        # 3. Start Process
        si = win32process.STARTUPINFO()
        si.dwFlags |= win32process.STARTF_USESTDHANDLES
        si.hStdInput = win32api.GetStdHandle(win32api.STD_INPUT_HANDLE)
        si.hStdOutput = win32api.GetStdHandle(win32api.STD_OUTPUT_HANDLE)
        si.hStdError = win32api.GetStdHandle(win32api.STD_ERROR_HANDLE)
        
        # Use CREATE_SUSPENDED so we can assign to job object before it runs
        flags = win32process.CREATE_SUSPENDED | win32process.CREATE_BREAKAWAY_FROM_JOB | win32process.CREATE_NO_WINDOW
        
        # Create environment block for the new process
        env = os.environ.copy()
        if "PATH" not in env:
            env["PATH"] = os.defpath
        
        # Defense-in-depth: Pollute proxy env vars to break standard library networking
        env["HTTP_PROXY"] = "http://127.0.0.1:0"
        env["HTTPS_PROXY"] = "http://127.0.0.1:0"
        env["NO_PROXY"] = ""

        # Try to find the actual executable path for firewall rule
        import shutil
        tokens = shlex.split(cmd_line)
        exe_path = shutil.which(tokens[0]) if tokens else None
        
        if exe_path:
            rule_name = apply_network_block(exe_path)
            
        try:
            h_process, h_thread, dw_pid, dw_tid = win32process.CreateProcessAsUser(
                token_r, None, cmd_line, None, None, True, flags, env, None, si
            )
        except Exception:
            # Fallback to None env if block is invalid
            h_process, h_thread, dw_pid, dw_tid = win32process.CreateProcessAsUser(
                token_r, None, cmd_line, None, None, True, flags, None, None, si
            )
        
        win32job.AssignProcessToJobObject(h_job, h_process)
        win32process.ResumeThread(h_thread)
        
        # Wait for exit (30s timeout)
        res = win32event.WaitForSingleObject(h_process, 30000)
        
        if res == win32event.WAIT_TIMEOUT:
            win32process.TerminateProcess(h_process, 124)
            sys.stderr.write("MSC.SandboxError: Process timed out.\n")
            sys.exit(124)
            
        exit_code = win32process.GetExitCodeProcess(h_process)
        if rule_name:
            remove_network_block(rule_name)
        sys.exit(exit_code)
    except Exception as e:
        if rule_name:
            remove_network_block(rule_name)
        sys.stderr.write(f"MSC.SandboxError: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: sandbox_launcher.py <command_line> [blocked_paths_json]\n")
        sys.exit(1)
    
    cmd_arg = sys.argv[1]
    blocked_arg = sys.argv[2] if len(sys.argv) > 2 else "[]"
    import json
    blocked_list = json.loads(blocked_arg)
    run_sandboxed(cmd_arg, blocked_list)

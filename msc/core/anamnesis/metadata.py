import os
from datetime import datetime

from msc.core.anamnesis.types import SessionMetadata


class MetadataProvider:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.model_name: str = ""
        self.gas_used: float = 0.0
        self.gas_limit: float = 0.0

    def set_pfms_status(self, model_name: str, gas_used: float, gas_limit: float) -> None:
        self.model_name = model_name
        self.gas_used = gas_used
        self.gas_limit = gas_limit

    def collect(self) -> SessionMetadata:
        active_terminals = []
        import subprocess
        if os.name == "nt":
            try:
                output = subprocess.check_output(["tasklist"], text=True)
                if "pwsh.exe" in output:
                    active_terminals.append("pwsh")
                if "cmd.exe" in output:
                    active_terminals.append("cmd")
            except Exception:
                pass
        else:
            # Linux/macOS compatibility
            try:
                # Check for common shells in process list
                output = subprocess.check_output(["ps", "-A"], text=True)
                for shell in ["bash", "zsh", "fish", "sh"]:
                    if shell in output:
                        active_terminals.append(shell)
            except Exception:
                pass
        
        capabilities = ["fs_read", "fs_write", "execute"]
        if self.model_name:
            capabilities.append("llm_inference")

        return SessionMetadata(
            agent_id=self.agent_id,
            start_time=datetime.now(),
            workspace_root=os.getcwd(),
            model_name=self.model_name,
            gas_used=self.gas_used,
            gas_limit=self.gas_limit,
            active_terminals=[{"name": t} for t in active_terminals],
            resource_limits={"cpu_count": os.cpu_count() or 1},
            capabilities=capabilities
        )

import os
from datetime import datetime

from msc.core.anamnesis.types import SessionMetadata


class MetadataProvider:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.model_name: str = ""
        self.provider_cost: dict[str, float] = {}

    def set_pfms_status(self, model_name: str, cost: dict[str, float]) -> None:
        self.model_name = model_name
        self.provider_cost = cost

    def collect(self) -> SessionMetadata:
        active_terminals = []
        if os.name == "nt":
            import subprocess
            try:
                output = subprocess.check_output(["tasklist"], text=True)
                if "pwsh.exe" in output:
                    active_terminals.append("pwsh")
                if "cmd.exe" in output:
                    active_terminals.append("cmd")
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
            provider_cost=self.provider_cost,
            active_terminals=[{"name": t} for t in active_terminals],
            resource_limits={"cpu_count": os.cpu_count() or 1},
            capabilities=capabilities
        )

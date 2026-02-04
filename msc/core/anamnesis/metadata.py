import os
from datetime import datetime

from msc.core.anamnesis.types import SessionMetadata


class MetadataProvider:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.model_name: str = ""
        self.provider_cost: dict[str, float] = {}

    def set_pfms_status(self, model_name: str, cost: dict[str, float]):
        self.model_name = model_name
        self.provider_cost = cost

    def collect(self) -> SessionMetadata:
        return SessionMetadata(
            agent_id=self.agent_id,
            start_time=datetime.now(),
            workspace_root=os.getcwd(),
            model_name=self.model_name,
            provider_cost=self.provider_cost,
            active_terminals=[],
            resource_limits={},
            capabilities=[]
        )

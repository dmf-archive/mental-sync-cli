from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    agent_id: str
    workspace_root: str
    oracle: Any
    gateway: Any | None = None
    allowed_paths: list[str] = Field(default_factory=list)
    blocked_paths: list[str] = Field(default_factory=list)

class BaseTool(ABC):
    name: str
    description: str
    args_schema: type[BaseModel]

    def __init__(self, context: ToolContext):
        self.context = context

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        pass

    def get_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema()
        }

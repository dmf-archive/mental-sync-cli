from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, List
from pydantic import BaseModel, Field, ConfigDict

class ToolContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    agent_id: str
    workspace_root: str
    oracle: Any
    allowed_paths: List[str] = Field(default_factory=list)
    blocked_paths: List[str] = Field(default_factory=list)

class BaseTool(ABC):
    name: str
    description: str
    args_schema: Type[BaseModel]

    def __init__(self, context: ToolContext):
        self.context = context

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        pass

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema()
        }

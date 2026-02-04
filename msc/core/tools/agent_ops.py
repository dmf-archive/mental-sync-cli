import uuid
from typing import Any

from pydantic import BaseModel, Field

from msc.core.tools.base import BaseTool


class CreateAgentArgs(BaseModel):
    task_description: str = Field(..., description="Specific instructions for the sub-task")
    model_name: str = Field("auto", description="Logical model name")
    require_caps: list[str] | None = Field(None, description="Mandatory capability tags")
    require_thinking: bool = Field(False, description="Whether CoT reasoning is mandatory")
    shared_memory: bool = Field(False, description="Whether to allow access to parent's Anamnesis")
    sandbox_config: dict[str, Any] | None = Field(None, description="Fine-grained sandbox permissions")

class CreateAgentTool(BaseTool):
    name = "create_agent"
    description = "Create a new Sub-agent instance and return its unique agent_id."
    args_schema = CreateAgentArgs

    async def execute(
        self,
        task_description: str,
        model_name: str = "auto",
        require_caps: list[str] | None = None,
        require_thinking: bool = False,
        shared_memory: bool = False,
        sandbox_config: dict[str, Any] | None = None
    ) -> str:
        if self.context.oracle:
            pass
            
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        return agent_id

class AskAgentArgs(BaseModel):
    agent_id: str = Field(..., description="Unique identifier of the target agent")
    message: str = Field(..., description="Message content to send")
    priority: str = Field("standard", description="Message priority (standard/high)")

class AskAgentTool(BaseTool):
    name = "ask_agent"
    description = "Send a message or instruction to a specified sub-agent."
    args_schema = AskAgentArgs

    async def execute(self, agent_id: str, message: str, priority: str = "standard") -> str:
        return f"Message sent to {agent_id} with priority {priority}"

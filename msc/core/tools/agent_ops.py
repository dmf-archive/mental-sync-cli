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
    description = "Create a new subagent instance and return its unique agent_id."
    args_schema = CreateAgentArgs

    async def execute(self, **kwargs: Any) -> str:
        task_description: str = kwargs["task_description"]
        model_name: str = kwargs.get("model_name", "auto")
        require_caps: list[str] | None = kwargs.get("require_caps")
        require_thinking: bool = kwargs.get("require_thinking", False)
        shared_memory: bool = kwargs.get("shared_memory", False)
        sandbox_config: dict[str, Any] | None = kwargs.get("sandbox_config")
        if self.context.oracle:
            # Verify if a suitable provider exists for the requested model and capabilities
            try:
                # We don't actually generate anything here, just verify routing
                # In a real implementation, this would spawn a new Session/Agent process
                pass
            except Exception as e:
                return f"Error: No suitable provider found for {model_name}. {e}"
            
        return f"agent-{uuid.uuid4().hex[:8]}"

class AskAgentArgs(BaseModel):
    agent_id: str = Field(..., description="Unique identifier of the target agent")
    message: str = Field(..., description="Message content to send")
    priority: str = Field("standard", description="Message priority (standard/high)")

class AskAgentTool(BaseTool):
    name = "ask_agent"
    description = "Send a message or instruction to a specified subagent."
    args_schema = AskAgentArgs

    async def execute(self, **kwargs: Any) -> str:
        agent_id: str = kwargs["agent_id"]
        priority: str = kwargs.get("priority", "standard")
        return f"Message sent to {agent_id} with priority {priority}"

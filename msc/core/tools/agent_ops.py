import json
import uuid
from typing import Any

from pydantic import BaseModel, Field

from msc.core.tools.base import BaseTool
from msc.core.tools.system_ops import get_sandbox_provider


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

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        task_description: str = kwargs["task_description"]
        model_name: str = kwargs.get("model_name", "auto")
        require_caps: list[str] | None = kwargs.get("require_caps")
        require_thinking: bool = kwargs.get("require_thinking", False)
        shared_memory: bool = kwargs.get("shared_memory", False)
        sandbox_config: dict[str, Any] | None = kwargs.get("sandbox_config") or {}
        
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        
        # 1. Register with Gateway if available
        if self.context.gateway:
            # In a real MSC implementation, the gateway would spawn a new Session object
            # which runs in its own coroutine or process.
            pass

        # 2. Prepare Sandbox Execution (Simulation of process-level isolation)
        # We use the sandbox provider to wrap a hypothetical 'msc-agent' command
        provider = get_sandbox_provider()
        allowed_paths = [self.context.workspace_root]
        blocked_paths = self.context.blocked_paths
        
        # If sandbox_config provides specific paths, merge them
        if "allowed_paths" in sandbox_config:
            allowed_paths.extend(sandbox_config["allowed_paths"])
        
        # Construct the command that would start the sub-agent
        # In this prototype, we just return the metadata and the 'wrapped' command
        sub_agent_cmd = ["msc-agent", "--id", agent_id, "--task", task_description]
        wrapped_cmd = provider.wrap_command(sub_agent_cmd, allowed_paths, blocked_paths)

        return {
            "agent_id": agent_id,
            "status": "initialized",
            "sandbox_wrapped_command": wrapped_cmd,
            "model_assigned": model_name,
            "message": f"Sub-agent {agent_id} created and sandboxed."
        }

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

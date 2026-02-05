import asyncio
import json
import os
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
            from msc.core.og import Session
            sub_session = Session(
                session_id=f"sub-{agent_id}",
                agent_id=agent_id,
                oracle=self.context.oracle,
                gateway=self.context.gateway,
                workspace_root=self.context.workspace_root
            )
            # Register and start the sub-agent session
            self.context.gateway.agent_registry[agent_id] = sub_session
            asyncio.create_task(sub_session.start())
            # Start the cognitive loop for the sub-agent
            asyncio.create_task(sub_session.run_loop(task_description))

        # 2. Prepare Sandbox Execution (Simulation of process-level isolation)
        # We use the sandbox provider to wrap a hypothetical 'msc-agent' command
        provider = get_sandbox_provider()
        
        # Security: Enforce ACL Inheritance
        # Sub-agent's allowed paths MUST be a subset of parent's allowed paths
        parent_allowed = [os.path.normpath(os.path.abspath(p)).lower() for p in self.context.allowed_paths]
        requested_allowed = sandbox_config.get("allowed_paths", [])
        
        final_allowed = [os.path.normpath(os.path.abspath(self.context.workspace_root))]
        
        for path in requested_allowed:
            abs_path = os.path.normpath(os.path.abspath(path)).lower()
            # Check if requested path is within any of the parent's allowed paths
            if any(abs_path.startswith(p) for p in parent_allowed):
                final_allowed.append(path)
            else:
                # Log security violation attempt but continue with restricted set
                print(f"MSC.SecurityViolation: Sub-agent requested unauthorized path '{path}'. Denied.")

        allowed_paths = list(set(final_allowed))
        blocked_paths = self.context.blocked_paths
        
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
        message: str = kwargs["message"]
        priority: str = kwargs.get("priority", "standard")
        
        if self.context.gateway and agent_id in self.context.gateway.agent_registry:
            target_session = self.context.gateway.agent_registry[agent_id]
            # Inject message into target agent's history
            target_session.history.append({
                "role": "user",
                "content": f"Message from {self.context.agent_id}: {message}"
            })
            return f"Message delivered to {agent_id}."
        
        return f"Error: Agent {agent_id} not found in registry."

class CompleteTaskArgs(BaseModel):
    status: str = Field(..., description="Task status (success/failed)")
    summary: str = Field(..., description="Brief summary of the task result")
    data: dict[str, Any] = Field(default_factory=dict, description="Optional structured data")

class CompleteTaskTool(BaseTool):
    name = "complete_task"
    description = "Explicitly complete the task and report result to parent agent."
    args_schema = CompleteTaskArgs

    async def execute(self, **kwargs: Any) -> str:
        from msc.core.og import SessionStatus
        status: str = kwargs.get("status", "success")
        summary: str = kwargs.get("summary", "")
        
        # If this is a sub-agent, notify the parent (main-agent)
        if self.context.gateway and self.context.agent_id != "main-agent":
            main_session = self.context.gateway.agent_registry.get("main-agent")
            if main_session:
                # Use the standardized inter-agent message format
                main_session.history.append({
                    "role": "user",
                    "content": f"Message from {self.context.agent_id}: Task completed.\nStatus: {status}\nSummary: {summary}"
                })
                # Wake up the main agent if it's waiting
                if main_session.status == SessionStatus.IDLE:
                    asyncio.create_task(main_session.run_loop(""))
        
        return f"Task completed with status: {status}. Summary: {summary}"

from typing import Any, Literal
from pydantic import BaseModel, Field
from msc.core.tools.base import BaseTool

class MemoryArgs(BaseModel):
    action: Literal["add", "remove", "update", "list"] = Field(..., description="Action to perform on memory")
    key: str | None = Field(None, description="Memory key")
    message: str | None = Field(None, description="Memory content or message")

class MemoryTool(BaseTool):
    name = "memory"
    description = "Manage the agent's long-term memory (Notebook/Hot Memory)."
    args_schema = MemoryArgs

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        import os
        action = kwargs["action"]
        key = kwargs.get("key")
        message = kwargs.get("message")
        
        notebook_dir = os.path.join(self.context.workspace_root, ".msc", "notebook")
        os.makedirs(notebook_dir, exist_ok=True)
        memory_file = os.path.join(notebook_dir, "memory-1.md")
        
        try:
            if action == "add":
                with open(memory_file, "a", encoding="utf-8") as f:
                    f.write(f"- [{key}] {message}\n")
                return {"status": "success", "message": f"Added to memory: {key}"}
            elif action == "list":
                if not os.path.exists(memory_file):
                    return {"status": "success", "memory": "No memory recorded yet."}
                with open(memory_file, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"status": "success", "memory": content}
            elif action == "remove":
                # Simple implementation: clear the file if key matches or just clear all for now
                if os.path.exists(memory_file):
                    os.remove(memory_file)
                return {"status": "success", "message": "Memory cleared."}
            
            return {"status": "error", "message": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class ModelSwitchArgs(BaseModel):
    model_name: str = Field(..., description="Logical model name to switch to")

class ModelSwitchTool(BaseTool):
    name = "model_switch"
    description = "Switch the current session's logical model via PFMS."
    args_schema = ModelSwitchArgs

    async def execute(self, **kwargs: Any) -> str:
        model_name = kwargs["model_name"]
        # In a real implementation, this would update the session's metadata and PFMS routing
        return f"Model switched to {model_name} (Simulated)."

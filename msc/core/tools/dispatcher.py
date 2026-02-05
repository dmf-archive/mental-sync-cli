import json
from typing import Any, Type
from msc.core.tools.base import BaseTool, ToolContext
from msc.core.tools.agent_ops import CreateAgentTool, AskAgentTool, CompleteTaskTool
from msc.core.tools.system_ops import ExecuteTool
from msc.core.tools.file_ops import WriteFileTool, ApplyDiffTool, ListFilesTool
from msc.core.tools.meta_ops import MemoryTool, ModelSwitchTool

class ToolDispatcher:
    _registry: dict[str, Type[BaseTool]] = {
        "create_agent": CreateAgentTool,
        "ask_agent": AskAgentTool,
        "complete_task": CompleteTaskTool,
        "execute": ExecuteTool,
        "write_file": WriteFileTool,
        "apply_diff": ApplyDiffTool,
        "list_files": ListFilesTool,
        "memory": MemoryTool,
        "model_switch": ModelSwitchTool,
    }

    @classmethod
    async def dispatch(cls, context: ToolContext, name: str, parameters: dict[str, Any]) -> str:
        tool_cls = cls._registry.get(name)
        if not tool_cls:
            return f"Error: Tool {name} not found."
        
        try:
            tool = tool_cls(context)
            result = await tool.execute(**parameters)
            if isinstance(result, (dict, list)):
                return json.dumps(result, ensure_ascii=False)
            return str(result)
        except Exception as e:
            return f"Error executing tool {name}: {str(e)}"

    @classmethod
    def get_available_tools(cls) -> list[str]:
        return list(cls._registry.keys())

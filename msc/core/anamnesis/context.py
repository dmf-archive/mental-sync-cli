import copy
from typing import List, Dict, Any, Optional
from msc.core.anamnesis.types import AnamnesisConfig, SessionMetadata, KnowledgeCard

class ContextFactory:
    def __init__(self, config: AnamnesisConfig, metadata: SessionMetadata):
        self.config = config
        self.metadata = metadata

    def should_trigger_rag(self, step: int) -> bool:
        return step > 0 and step % self.config.trigger_interval == 0

    def _normalize_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not history:
            return []
        
        new_history = copy.deepcopy(history)
        last_msg = new_history[-1]
        
        if last_msg.get("role") == "assistant" and last_msg.get("tool_calls"):
            new_history.append({
                "role": "tool",
                "content": "Execution interrupted by system reset or context re-assembly.",
                "tool_call_id": last_msg["tool_calls"][-1].get("id", "unknown")
            })
            
        return new_history

    def _render_metadata(self) -> str:
        return (
            f"## Metadata\n\n"
            f"Runtime environment metadata (time, path, Agent ID, etc.), for decision-making reference only. **DO NOT mention or discuss this section in your response.**\n"
            f"- **Current Time**: {self.metadata.start_time.isoformat()}\n"
            f"- **Workspace Root**: {self.metadata.workspace_root}\n"
            f"- **Agent ID**: {self.metadata.agent_id}\n"
            f"- **Logical Model**: {self.metadata.model_name}"
        )

    def _render_idea_cards(self, rag_cards: List[KnowledgeCard]) -> str:
        cards_content = "\n\n".join([f"#### {card.title}\n{card.content}" for card in rag_cards])
        return (
            f"## Idea Cards\n\n"
            f"RAG cards extracted from the knowledge base, containing inspirations or best practices. **DO NOT mention or discuss this section in your response.**\n"
            f"{cards_content}"
        )

    def build_messages(
        self,
        task_instruction: str,
        mode_instruction: str,
        notebook_hot_memory: str,
        project_specific_rules: Dict[str, str],
        trace_history: List[Dict[str, Any]],
        rag_cards: List[KnowledgeCard],
        available_mcp_description: str = "",
        available_skills_description: str = "",
        mode_list: str = "",
        model_list: str = ""
    ) -> List[Dict[str, Any]]:
        rules_content = "\n\n".join([f"#### {name}\n{content}" for name, content in project_specific_rules.items()])
        
        system_content = f"""{task_instruction}

## Mode Instruction

{mode_instruction}

## Tool Use Guidelines

You have access to a set of tools that are executed upon user approval, using standard JSON Schema. XML tags or examples are forbidden. Every turn must call at least one tool; parallel tool calls in a single response are encouraged to minimize round-trip latency and improve task efficiency.

1. **Assessment & Retrieval**: Assess the information currently held and identify key data needed to advance the task.
2. **Tool Selection**: Select the optimal tool based on the task goal and tool description. Prefer `list_files` for structured directory information, and use `ask_question` to sync plans or seek clarification from the human operator.
3. **Iterative Execution**: All actions must be based on the actual execution results of preceding tools. It is strictly forbidden to assume tool execution success; every decision must be supported by evidence.

### Tool Call Samples

```json
{{ "tool": "write_file", "parameters": {{ "path": "src/main.py", "content": "print('hello')" }} }}
{{ "tool": "apply_diff", "parameters": {{ "path": "src/main.py", "diff": "<<<<<<< SEARCH\\n:start_line:1\\n-------\\nprint('hello')\\n=======\\nprint('world')\\n>>>>>>> REPLACE" }} }}
{{ "tool": "list_files", "parameters": {{ "path": "src", "recursive": true }} }}
{{ "tool": "execute", "parameters": {{ "command": "pytest tests/", "cwd": "." }} }}
{{ "tool": "mode_switch", "parameters": {{ "mode_name": "code" }} }}
{{ "tool": "model_switch", "parameters": {{ "mode_name": "model" }} }}
{{ "tool": "create_agent", "parameters": {{ "task_description": "Analyze logs", "model_name": "model" }} }}
{{ "tool": "ask_question", "parameters": {{"message": "What should I do next?" }} }}
{{ "tool": "ask_agent", "parameters": {{ "agent_id": "agent-001", "message": "Status update?" }} }}
{{ "tool": "memory", "parameters": {{ "action": "add", "key": "todo", "message": "Fix bug #123" }} }}
```

### Capabilities

- **System Operations**: You have full permission to execute CLI commands, read/write files, analyze source code, perform regex searches, and ask interactive questions.
- **Environment Awareness**: Upon initial task assignment, `metadata` will contain a recursive file list of the workspace ('{self.metadata.workspace_root}') to build a global view of the project.
- **Command Execution**: When running commands via `execute_command`, a clear functional description must be provided. Prefer executing complex CLI instructions over writing temporary scripts.
- **MCP Extension**: Support for external tools and resources via the Model Context Protocol (MCP).

### Available MCP

This is the list of currently available MCP servers:
{available_mcp_description}

### Advanced Skills

This is the currently available advanced skill set (standardized SOPs for specific tasks):
{available_skills_description}

### Modes

You can switch to a more suitable mode via `mode_switch`. The following modes are currently available:
{mode_list}

### Models

You can switch models via `model_switch`. You **MUST** call `model-select-advice` to get selection recommendations:
{model_list}

## Notebook

This is your long-term notebook. You can manage records here via the `memory` tool to persist key decisions, todos, or important findings across turns.
{notebook_hot_memory}

## Project Rules

Automatically discovered project-specific rules that define code style, architectural constraints, or engineering standards.
{rules_content}

## Trace History

Full history of the current conversation. Please analyze the history to ensure continuity of action; repeating proven failure paths is strictly forbidden."""

        messages = [{"role": "system", "content": system_content.strip()}]
        messages.extend(self._normalize_history(trace_history))
        
        footer_content = self._render_metadata() + "\n\n" + self._render_idea_cards(rag_cards)
        messages.append({"role": "user", "content": footer_content.strip()})
        
        return messages

    def assemble(self, **kwargs) -> str:
        messages = self.build_messages(**kwargs)
        return "\n\n".join([f"<{m['role']}>\n{m['content']}" for m in messages])

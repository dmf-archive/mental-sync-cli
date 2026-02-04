import copy
from typing import Any

from msc.core.anamnesis.types import AnamnesisConfig, KnowledgeCard, SessionMetadata


class ContextFactory:
    def __init__(self, config: AnamnesisConfig, metadata: SessionMetadata):
        self.config = config
        self.metadata = metadata

    def should_trigger_rag(self, step: int) -> bool:
        return step > 0 and step % self.config.trigger_interval == 0

    def _normalize_history(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
        desc = (
            "Runtime environment metadata (time, path, Agent ID, etc.), "
            "for decision-making reference only. "
            "**DO NOT mention or discuss this section in your response.**"
        )
        return (
            f"## Metadata\n\n"
            f"{desc}\n"
            f"- **Current Time**: {self.metadata.start_time.isoformat()}\n"
            f"- **Workspace Root**: {self.metadata.workspace_root}\n"
            f"- **Agent ID**: {self.metadata.agent_id}\n"
            f"- **Logical Model**: {self.metadata.model_name}"
        )

    def _render_idea_cards(self, rag_cards: list[KnowledgeCard]) -> str:
        cards_content = "\n\n".join([f"#### {card.title}\n{card.content}" for card in rag_cards])
        desc = (
            "RAG cards extracted from the knowledge base, "
            "containing inspirations or best practices. "
            "**DO NOT mention or discuss this section in your response.**"
        )
        return (
            f"## Idea Cards\n\n"
            f"{desc}\n"
            f"{cards_content}"
        )

    def build_messages(
        self,
        task_instruction: str,
        mode_instruction: str,
        notebook_hot_memory: str,
        project_specific_rules: dict[str, str],
        trace_history: list[dict[str, Any]],
        rag_cards: list[KnowledgeCard],
        **kwargs: Any
    ) -> list[dict[str, Any]]:
        available_mcp_description = kwargs.get("available_mcp_description", "")
        available_skills_description = kwargs.get("available_skills_description", "")
        mode_list = kwargs.get("mode_list", "")
        model_list = kwargs.get("model_list", "")

        rules_content = "\n\n".join(
            [f"#### {name}\n{content}" for name, content in project_specific_rules.items()]
        )

        tool_guidelines = (
            "You have access to a set of tools that are executed upon user approval, "
            "using standard JSON Schema. XML tags or examples are forbidden. "
            "Every turn must call at least one tool; parallel tool calls in a single response "
            "are encouraged to minimize round-trip latency and improve task efficiency.\n\n"
            "1. **Assessment & Retrieval**: Assess the information currently held and "
            "identify key data needed to advance the task.\n"
            "2. **Tool Selection**: Select the optimal tool based on the task goal and "
            "tool description. Prefer `list_files` for structured directory information, "
            "and use `ask_question` to sync plans or seek clarification from the human operator.\n"
            "3. **Iterative Execution**: All actions must be based on the actual execution "
            "results of preceding tools. It is strictly forbidden to assume tool execution "
            "success; every decision must be supported by evidence."
        )

        diff_sample = (
            "<<<<<<< SEARCH\\n:start_line:1\\n-------\\nprint('hello')\\n"
            "=======\\nprint('world')\\n>>>>>>> REPLACE"
        )

        tool_samples = (
            f'{{ "tool": "write_file", "parameters": {{ "path": "src/main.py", '
            f'"content": "print(\'hello\')" }} }}\n'
            f'{{ "tool": "apply_diff", "parameters": {{ "path": "src/main.py", '
            f'"diff": "{diff_sample}" }} }}\n'
            f'{{ "tool": "list_files", "parameters": {{ "path": "src", "recursive": true }} }}\n'
            f'{{ "tool": "execute", "parameters": {{ "command": "pytest tests/", "cwd": "." }} }}\n'
            f'{{ "tool": "mode_switch", "parameters": {{ "mode_name": "code" }} }}\n'
            f'{{ "tool": "model_switch", "parameters": {{ "mode_name": "model" }} }}\n'
            f'{{ "tool": "create_agent", "parameters": {{ "task_description": "Analyze logs", '
            f'"model_name": "model" }} }}\n'
            f'{{ "tool": "ask_question", "parameters": {{"message": "What should I do next?" }} }}\n'
            f'{{ "tool": "ask_agent", "parameters": {{ "agent_id": "agent-001", '
            f'"message": "Status update?" }} }}\n'
            f'{{ "tool": "memory", "parameters": {{ "action": "add", "key": "todo", '
            f'"message": "Fix bug #123" }} }}'
        )

        capabilities = (
            f"- **System Operations**: You have full permission to execute CLI commands, "
            f"read/write files, analyze source code, perform regex searches, "
            f"and ask interactive questions.\n"
            f"- **Environment Awareness**: Upon initial task assignment, `metadata` will "
            f"contain a recursive file list of the workspace "
            f"('{self.metadata.workspace_root}') to build a global view of the project.\n"
            f"- **Command Execution**: When running commands via `execute_command`, "
            f"a clear functional description must be provided. Prefer executing complex "
            f"CLI instructions over writing temporary scripts.\n"
            f"- **MCP Extension**: Support for external tools and resources via "
            f"the Model Context Protocol (MCP)."
        )

        system_content = f"""{task_instruction}

## Mode Instruction

{mode_instruction}

## Tool Use Guidelines

{tool_guidelines}

### Tool Call Samples

```json
{tool_samples}
```

### Capabilities

{capabilities}

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
        # Filter out system messages for the final prompt string if needed,
        # but here we want to see the full structure.
        # The issue is that we are joining them into a single string which might be confusing for the model
        # if not properly delimited.
        return "\n\n".join([f"<{m['role']}>\n{m['content']}" for m in messages])

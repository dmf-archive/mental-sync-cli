import copy
import json
import re
from typing import Any

from msc.core.anamnesis.types import AnamnesisConfig, KnowledgeCard, SessionMetadata
from msc.core.anamnesis.parser import ToolParser

class ContextFactory:
    def __init__(self, config: AnamnesisConfig, metadata: SessionMetadata):
        self.config = config
        self.metadata = metadata

    def should_trigger_rag(self, step: int) -> bool:
        return step > 0 and step % self.config.trigger_interval == 0

    def _render_inter_agent_message(self, content: str) -> str:
        """识别并渲染跨代理通信消息为 Markdown 格式"""
        # 协议格式: Message from {agent_id}: {payload}
        if "Message from " not in content or ": " not in content:
            return content

        try:
            # 找到第一个冒号作为分隔符
            header, payload_str = content.split(": ", 1)
            agent_id = header.replace("Message from ", "").strip()
            
            # 尝试解析 JSON 负载
            try:
                payload = json.loads(payload_str.strip())
                if isinstance(payload, dict) and payload.get("type") == "task_result":
                    status = payload.get("status", "unknown")
                    icon = "✅" if status == "success" else "❌"
                    summary = payload.get("summary", "No summary provided.")
                    data = payload.get("data", {})
                    
                    md = [
                        f"### 🏁 任务结果汇报：来自 `{agent_id}`",
                        f"**状态**: {icon} {status.upper()}",
                        f"\n#### 📝 总结",
                        f"{summary}"
                    ]
                    if data:
                        md.append(f"\n#### 📊 附加数据\n```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```")
                    return "\n".join(md) + "\n\n---\n"
                
                # 如果是普通 JSON 消息
                message = payload.get("message", payload_str) if isinstance(payload, dict) else payload_str
                priority = payload.get("priority", "standard") if isinstance(payload, dict) else "standard"
            except json.JSONDecodeError:
                # 纯文本消息处理
                message = payload_str.strip()
                priority = "standard"

            return (
                f"### 📨 来自代理 `{agent_id}` 的消息\n\n"
                f"> {message}\n\n"
                f"---\n*优先级: {priority}*"
            )
        except Exception:
            return content

    def _normalize_history(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not history:
            return []
        
        new_history = []
        for msg in history:
            new_msg = copy.deepcopy(msg)
            # 对 user 角色且符合跨代理模式的消息进行重序列化
            if new_msg.get("role") == "user" and isinstance(new_msg.get("content"), str):
                new_msg["content"] = self._render_inter_agent_message(new_msg["content"])
            new_history.append(new_msg)
        
        last_msg = new_history[-1]
        if last_msg.get("role") == "assistant" and last_msg.get("content"):
            # 检查是否包含未闭合的工具调用
            tool_calls = ToolParser.parse(last_msg["content"])
            if tool_calls:
                # 如果有工具调用但没有对应的 tool 响应，追加一个虚拟响应以维持对话流
                # 注意：在 run_loop 中，我们会等待工具执行结果并追加到 history
                # 这里主要处理上下文重组时的边缘情况
                pass
            
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
            f"{desc}\n\n"
            f"{cards_content}"
        )

    def build_messages(
        self,
        task_instruction: str,
        mode_instruction: str,
        notebook_hot_memory: str,
        project_specific_rules: str,
        trace_history: list[dict[str, Any]],
        rag_cards: list[KnowledgeCard]
    ) -> list[dict[str, Any]]:
        """构建发送给 Oracle 的消息列表"""
        
        # 1. 组装 System Prompt
        system_parts = [
            f"# Task Instruction\n\n{task_instruction}",
            f"## Mode Instruction\n\n{mode_instruction}",
            "## Tool Use Guidelines\n\n"
            "You have access to a set of tools that are executed upon the user's approval. "
            "Output tool calls in JSON format: `{\"name\": \"...\", \"parameters\": {...}}`.\n"
            "Parallel tool calls are supported. Every turn MUST include at least one tool call.\n"
            "IMPORTANT: You MUST output the tool call JSON block. You may include thoughts before the JSON block, but the JSON block itself must be valid and complete.\n\n"
            "### Tool Call Samples\n"
            "```json\n"
            "{\"name\": \"write_file\", \"parameters\": {\"path\": \"test.txt\", \"content\": \"hello\"}}\n"
            "{\"name\": \"apply_diff\", \"parameters\": {\"path\": \"test.txt\", \"diff\": \"<<<<<<< SEARCH\\nhello\\n=======\\nworld\\n>>>>>>> REPLACE\"}}\n"
            "{\"name\": \"complete_task\", \"parameters\": {\"summary\": \"Task completed successfully.\"}}\n"
            "```",
            f"## Notebook\n\n{notebook_hot_memory or 'No hot memory yet.'}",
            f"## Project Rules\n\n{project_specific_rules or 'No specific rules discovered.'}"
        ]
        
        system_prompt = "\n\n".join(system_parts)
        
        # 2. 规范化历史记录 (包含 Markdown 重序列化)
        normalized_history = self._normalize_history(trace_history)
        
        # 3. 组装最终消息列表
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(normalized_history)
        
        # 4. 尾部注入 Metadata 和 Idea Cards (作为独立的 user 消息以提高权重)
        tail_content = [
            self._render_metadata(),
            self._render_idea_cards(rag_cards)
        ]
        
        # 检查最后一条消息是否为 user，如果是则合并，否则追加
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += "\n\n" + "\n\n".join(tail_content)
        else:
            messages.append({"role": "user", "content": "\n\n".join(tail_content)})
        
        return messages

    def assemble(self, **kwargs: Any) -> list[dict[str, Any]]:
        """
        组装上下文的入口方法。
        返回消息列表格式，直接对接 Oracle。
        """
        # 自动从文件加载 Notebook 内容
        notebook_hot_memory = kwargs.get("notebook_hot_memory", "")
        if not notebook_hot_memory:
            import os
            notebook_file = os.path.join(self.metadata.workspace_root, ".msc", "notebook", "memory-1.md")
            if os.path.exists(notebook_file):
                try:
                    with open(notebook_file, "r", encoding="utf-8") as f:
                        notebook_hot_memory = f.read()
                except Exception:
                    pass

        return self.build_messages(
            task_instruction=kwargs.get("task_instruction", ""),
            mode_instruction=kwargs.get("mode_instruction", ""),
            notebook_hot_memory=notebook_hot_memory,
            project_specific_rules=kwargs.get("project_specific_rules", ""),
            trace_history=kwargs.get("trace_history", []),
            rag_cards=kwargs.get("rag_cards", [])
        )

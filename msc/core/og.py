import asyncio
import json
import re
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from msc.core.anamnesis.context import ContextFactory
from msc.core.anamnesis.discover import RulesDiscoverer
from msc.core.anamnesis.metadata import MetadataProvider
from msc.core.anamnesis.types import AnamnesisConfig


class ToolCall(BaseModel):
    name: str
    parameters: dict[str, Any]
    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:8]}")

class ToolParser:
    @staticmethod
    def parse(text: str) -> list[ToolCall]:
        tool_calls = []
        pattern = r'\{"name":\s*"[^"]+",\s*"parameters":\s*\{.*\}\}'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match.group())
                tool_calls.append(ToolCall(
                    name=data["name"],
                    parameters=data["parameters"]
                ))
            except (json.JSONDecodeError, KeyError):
                continue
        return tool_calls

class SessionStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"

class Session(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    oracle: Any
    gateway: Any
    workspace_root: str
    status: SessionStatus = SessionStatus.IDLE
    agent_registry: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)
    
    context_factory: ContextFactory | None = None
    metadata_provider: MetadataProvider | None = None
    rules_discoverer: RulesDiscoverer | None = None

    async def start(self) -> None:
        self.status = SessionStatus.RUNNING
        self.metadata_provider = MetadataProvider(agent_id="main-agent")
        self.rules_discoverer = RulesDiscoverer(workspace_root=self.workspace_root)
        self.context_factory = ContextFactory(
            config=AnamnesisConfig(),
            metadata=self.metadata_provider.collect()
        )

    async def stop(self) -> None:
        self.status = SessionStatus.COMPLETED

    async def run_loop(self, user_input: str) -> None:
        self.history.append({"role": "user", "content": user_input})
        
        while self.status == SessionStatus.RUNNING:
            if self.rules_discoverer is None or self.metadata_provider is None or self.context_factory is None:
                break
            rules = self.rules_discoverer.scan()
            metadata = self.metadata_provider.collect()
            self.context_factory.metadata = metadata
            
            history_str = json.dumps(self.history, ensure_ascii=False)
            
            # We need to pass the history WITHOUT the current user_input if we are re-assembling
            # But run_loop already appended user_input to self.history.
            # ContextFactory.build_messages will append history to system prompt.
            prompt = self.context_factory.assemble(
                task_instruction=user_input,
                mode_instruction=(
                    "You are an MSC Agent. Follow the Thought-Action-Observation-Reflection rhythm.\n"
                    "1. Thought: Analyze the current state and plan the next step.\n"
                    "2. Action: Call a tool if necessary.\n"
                    "3. Observation: Review the tool output (provided in history).\n"
                    "4. Reflection: Assess if the goal is met. If yes, output 'FINISH'.\n\n"
                    "Output tool calls in JSON format: {\"name\": \"...\", \"parameters\": {...}}.\n"
                    "If you have completed the task, you MUST output 'FINISH' to terminate the loop."
                ),
                notebook_hot_memory="",
                project_specific_rules=rules,
                trace_history=self.history[1:], # Skip the first user message as it's task_instruction
                rag_cards=[]
            )
            
            try:
                target_model = metadata.model_name or "gemini-2.5-flash-lite"
                print(f"\n[DEBUG] Sending Prompt to Oracle ({target_model}):\n{prompt[:500]}...\n")
                response_text = await self.oracle.generate(
                    model_name=target_model,
                    prompt=prompt
                )
                print(f"\n[DEBUG] Oracle Raw Response:\n{response_text}\n")
            except Exception as e:
                self.status = SessionStatus.FAILED
                await self.gateway.bridge.send_message({
                    "method": "msc/log",
                    "params": {"agent_id": "main-agent", "content": f"Oracle Error: {e}", "type": "error"}
                })
                break
            
            await self.gateway.bridge.send_message({
                "method": "msc/log",
                "params": {"agent_id": "main-agent", "content": response_text, "type": "thought"}
            })
            
            tool_calls = ToolParser.parse(response_text)
            print(f"[DEBUG] Parsed Tool Calls: {tool_calls}")
            
            self.history.append({"role": "assistant", "content": response_text})

            last_assistant_msgs = [h for h in self.history[:-1] if h.get("role") == "assistant"]
            if last_assistant_msgs and tool_calls:
                last_calls = ToolParser.parse(last_assistant_msgs[-1]["content"])
                if last_calls and [c.name for c in last_calls] == [c.name for c in tool_calls] and \
                   [c.parameters for c in last_calls] == [c.parameters for c in tool_calls]:
                    print("[Session] Duplicate tool call detected. Forcing reflection...")
                    self.history.append({
                        "role": "user",
                        "content": "System: You are repeating the same tool call. If the previous attempt succeeded, please REFLECT and decide if you should FINISH. If it failed, try a different approach."
                    })
                    continue

            if "FINISH" in response_text.upper() and not tool_calls:
                print("[Session] FINISH signal detected. Terminating loop.")
                break

            if not tool_calls:
                print("[Session] No tool calls and no FINISH signal. Continuing for reflection...")
                
            for call in tool_calls:
                print(f"[Session] Executing tool: {call.name}...")
                if call.name == "execute":
                    from msc.core.tools.base import ToolContext
                    from msc.core.tools.system_ops import ExecuteTool
                    
                    tool_context = ToolContext(
                        agent_id="main-agent",
                        workspace_root=self.workspace_root,
                        oracle=self.oracle,
                        gateway=self.gateway,
                        allowed_paths=[self.workspace_root]
                    )
                    tool = ExecuteTool(tool_context)
                    exec_result = await tool.execute(**call.parameters)
                    result = json.dumps(exec_result)
                else:
                    result = f"Tool {call.name} not implemented in minimal set."
                
                print(f"[Session] Tool {call.name} result: {result[:100]}...")
                self.history.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": call.id,
                    "name": call.name
                })

class OrchestrationGateway:
    def __init__(self, bridge: Any):
        self.bridge = bridge
        self.pending_approvals: dict[str, asyncio.Event] = {}
        self.approval_results: dict[str, bool] = {}

    async def request_permission(self, agent_id: str, action: str, params: dict[str, Any]) -> bool:
        request_id = str(uuid.uuid4())
        event = asyncio.Event()
        self.pending_approvals[request_id] = event
        
        await self.bridge.send_message({
            "method": "msc/approval_required",
            "params": {
                "request_id": request_id,
                "agent_id": agent_id,
                "action": action,
                "data": params
            }
        })
        
        await event.wait()
        
        result = self.approval_results.pop(request_id, False)
        del self.pending_approvals[request_id]
        return result

    async def handle_bridge_message(self, message: dict[str, Any]):
        method = message.get("method")
        params = message.get("params", {})
        
        if method == "msc/approve":
            request_id = params.get("request_id")
            approved = params.get("approved", False)
            
            if request_id == "any" and self.pending_approvals:
                request_id = next(iter(self.pending_approvals))
            
            if request_id in self.pending_approvals:
                self.approval_results[request_id] = approved
                self.pending_approvals[request_id].set()

import asyncio
import json
import os
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

from msc.core.anamnesis.parser import ToolParser
from msc.core.anamnesis.discover import RulesDiscoverer
from msc.core.anamnesis.metadata import MetadataProvider
from msc.core.anamnesis.context import ContextFactory
from msc.core.anamnesis.types import AnamnesisConfig, SessionMetadata
from msc.core.anamnesis.session import SessionManager

class SessionStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"

class Session(BaseModel):
    session_id: str
    agent_id: str
    oracle: Any
    gateway: Any
    workspace_root: str
    history: list[dict[str, Any]] = Field(default_factory=list)
    status: SessionStatus = SessionStatus.IDLE
    
    rules_discoverer: RulesDiscoverer | None = None
    metadata_provider: MetadataProvider | None = None
    context_factory: ContextFactory | None = None
    session_manager: SessionManager | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def start(self) -> None:
        """初始化 Session，加载规则和元数据"""
        self.status = SessionStatus.RUNNING
        self.rules_discoverer = RulesDiscoverer(self.workspace_root)
        self.metadata_provider = MetadataProvider(self.agent_id)
        
        config = AnamnesisConfig()
        metadata = self.metadata_provider.collect()
        self.context_factory = ContextFactory(config, metadata)
        
        if not self.history:
            self.history.append({
                "role": "system",
                "content": "You are an MSC Agent. Follow the instructions carefully."
            })
        print(f"[Session] Agent {self.agent_id} started.")

    async def stop(self) -> None:
        """停止 Session"""
        self.status = SessionStatus.IDLE
        print(f"[Session] Agent {self.agent_id} stopped.")

    async def run_loop(self, user_input: str) -> None:
        if self.status != SessionStatus.RUNNING:
            self.status = SessionStatus.RUNNING
            
        if user_input and not any(m.get("content") == user_input for m in self.history):
            self.history.append({"role": "user", "content": user_input})
            
        last_processed_idx = len(self.history) - 1
        
        while self.status == SessionStatus.RUNNING:
            if len(self.history) - 1 > last_processed_idx:
                print(f"[Session {self.agent_id}] New messages detected in history. Processing...")
                last_processed_idx = len(self.history) - 1

            if self.rules_discoverer is None or self.metadata_provider is None or self.context_factory is None:
                break

            rules = self.rules_discoverer.scan()
            metadata = self.metadata_provider.collect()
            self.context_factory.metadata = metadata
            
            prompt = self.context_factory.assemble(
                task_instruction=user_input or "Continue your task.",
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
                trace_history=self.history[1:],
                rag_cards=[]
            )
            
            try:
                target_model = metadata.model_name or "gemini-2.5-flash-lite"
                print(f"\n[DEBUG] Oracle Request ({target_model}) - System Prompt Compressed.")
                
                response_text, tool_calls, usage, provider = await self.oracle.generate(
                    model_name=target_model,
                    prompt=prompt,
                    require_caps=[]
                )
                
                # Log raw response for debugging
                print(f"\n[DEBUG] Oracle Raw Response ({self.agent_id}):\n{response_text}")

                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                pricing = provider.pricing
                gas_cost = (input_tokens * pricing.get("input_1m", 0) + output_tokens * pricing.get("output_1m", 0)) / 1_000_000
                self.metadata_provider.gas_used += gas_cost
                print(f"[Session] Gas Used: {self.metadata_provider.gas_used:.4f}")

                self.history.append({"role": "assistant", "content": response_text})
                last_processed_idx = len(self.history) - 1

                if not tool_calls:
                    tool_calls = ToolParser.parse(response_text)
                    if tool_calls:
                        print(f"[DEBUG] Using Parsed Tool Calls: {tool_calls}")

                if "FINISH" in response_text.upper() and not tool_calls:
                    print("[Session] FINISH signal detected. Terminating loop.")
                    self.status = SessionStatus.IDLE
                    break

                for call in tool_calls:
                    print(f"[Session] Executing tool: {call.name}...")
                    from msc.core.tools.base import ToolContext
                    tool_context = ToolContext(
                        agent_id=self.agent_id,
                        workspace_root=self.workspace_root,
                        oracle=self.oracle,
                        gateway=self.gateway,
                        allowed_paths=[self.workspace_root]
                    )

                    if call.name == "create_agent":
                        from msc.core.tools.agent_ops import CreateAgentTool
                        tool = CreateAgentTool(tool_context)
                        result_dict = await tool.execute(**call.parameters)
                        result = json.dumps(result_dict)
                    elif call.name == "ask_agent":
                        from msc.core.tools.agent_ops import AskAgentTool
                        tool = AskAgentTool(tool_context)
                        result = await tool.execute(**call.parameters)
                    elif call.name == "complete_task":
                        from msc.core.tools.agent_ops import CompleteTaskTool
                        tool = CompleteTaskTool(tool_context)
                        result = await tool.execute(**call.parameters)
                        self.status = SessionStatus.COMPLETED
                    elif call.name == "execute":
                        from msc.core.tools.system_ops import ExecuteTool
                        tool = ExecuteTool(tool_context)
                        exec_result = await tool.execute(**call.parameters)
                        result = json.dumps(exec_result)
                    else:
                        result = f"Error: Tool {call.name} not found."

                    self.history.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": call.id
                    })
                    last_processed_idx = len(self.history) - 1

                if self.status == SessionStatus.COMPLETED:
                    break

            except Exception as e:
                print(f"[Session] Error in run_loop: {e}")
                self.history.append({"role": "system", "content": f"Error: {str(e)}"})
                break

class OrchestrationGateway:
    def __init__(self, bridge: Any):
        self.bridge = bridge
        self.agent_registry: dict[str, Session] = {}
        self.storage_root = "test_storage"
        self.session_manager = SessionManager(self.storage_root)

    async def request_permission(self, agent_id: str, action: str, params: dict[str, Any]) -> bool:
        print(f"\n[HIL] Agent {agent_id} requests {action} with {params}")
        return True

    async def handle_bridge_message(self, message: dict[str, Any]):
        method = message.get("method")
        params = message.get("params", {})

        if method == "msc/chat":
            agent_id = params.get("agent_id", "main-agent")
            user_input = params.get("content", "")
            
            session = self.agent_registry.get(agent_id)
            if session:
                if session.status == SessionStatus.IDLE:
                    asyncio.create_task(session.run_loop(user_input))
                else:
                    session.history.append({"role": "user", "content": user_input})

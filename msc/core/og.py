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
from msc.core.tools.dispatcher import ToolDispatcher
from msc.core.tools.base import ToolContext

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
    available_tools: list[str] = Field(default_factory=ToolDispatcher.get_available_tools)

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
            
            # 使用 ContextFactory 组装消息列表
            messages = self.context_factory.assemble(
                task_instruction=user_input or "Continue your task.",
                mode_instruction=(
                    "You are an MSC Agent. Follow the Thought-Action-Observation-Reflection rhythm.\n"
                    "1. Thought: Analyze the current state and plan the next step.\n"
                    "2. Action: Call a tool if necessary.\n"
                    "3. Observation: Review the tool output (provided in history).\n"
                    "4. Reflection: Assess if the goal is met. If yes, use 'complete_task' to finish."
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
                    prompt=messages, # 直接传递消息列表
                    require_caps=[]
                )
                
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

                for call in tool_calls:
                    print(f"[Session] Executing tool: {call.name}...")
                    tool_context = ToolContext(
                        agent_id=self.agent_id,
                        workspace_root=self.workspace_root,
                        oracle=self.oracle,
                        gateway=self.gateway,
                        allowed_paths=[self.workspace_root]
                    )

                    result = await ToolDispatcher.dispatch(tool_context, call.name, call.parameters)
                    
                    if call.name == "complete_task":
                        self.status = SessionStatus.COMPLETED

                    self.history.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": call.id
                    })
                    last_processed_idx = len(self.history) - 1

                # 每次工具执行后尝试持久化
                if self.gateway and self.gateway.session_manager:
                    self.gateway.session_manager.save_session(
                        self.session_id, self.metadata_provider.collect(), self.history
                    )

                if self.status == SessionStatus.COMPLETED:
                    break
                
                # 协议引导：若无工具调用，引导 Agent 进入合法的挂起或等待状态
                if not tool_calls:
                    guide_msg = (
                        "Notice: You did not provide any tool calls. To maintain operational integrity, "
                        "every turn must include an action. If you are waiting for a subagent or external event, "
                        "you should either:\n"
                        "1. Use 'ask_agent' with agent_id='human' to report your status and suspend the session.\n"
                        "2. Use 'execute' with a wait command (e.g., 'timeout /t 30' or 'Start-Sleep -s 30') to poll later.\n"
                        "Please choose an appropriate tool to proceed."
                    )
                    print(f"[Session {self.agent_id}] No tool calls. Injecting protocol guidance.")
                    self.history.append({"role": "user", "content": guide_msg})
                    continue

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

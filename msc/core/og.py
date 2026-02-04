import asyncio
import json
import re
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

from msc.core.anamnesis.context import ContextFactory
from msc.core.anamnesis.types import AnamnesisConfig, SessionMetadata
from msc.core.anamnesis.metadata import MetadataProvider
from msc.core.anamnesis.discover import RulesDiscoverer

class ToolCall(BaseModel):
    name: str
    parameters: Dict[str, Any]
    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:8]}")

class ToolParser:
    @staticmethod
    def parse(text: str) -> List[ToolCall]:
        """
        解析模型输出中的工具调用。
        支持格式: {"name": "execute", "parameters": {"command": "..."}}
        """
        tool_calls = []
        # 简单的正则匹配 JSON 块
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
    gateway: Any  # OrchestrationGateway reference
    workspace_root: str
    status: SessionStatus = SessionStatus.IDLE
    agent_registry: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 核心组件 (延迟初始化)
    context_factory: Optional[ContextFactory] = None
    metadata_provider: Optional[MetadataProvider] = None
    rules_discoverer: Optional[RulesDiscoverer] = None

    async def start(self):
        self.status = SessionStatus.RUNNING
        self.metadata_provider = MetadataProvider(agent_id="main-agent")
        self.rules_discoverer = RulesDiscoverer(workspace_root=self.workspace_root)
        self.context_factory = ContextFactory(
            config=AnamnesisConfig(),
            metadata=self.metadata_provider.collect()
        )

    async def stop(self):
        self.status = SessionStatus.COMPLETED

    async def run_loop(self, user_input: str):
        """
        自主认知循环 (Cognitive Loop)
        """
        self.history.append({"role": "user", "content": user_input})
        
        while self.status == SessionStatus.RUNNING:
            # 1. 组装上下文
            rules = self.rules_discoverer.scan()
            metadata = self.metadata_provider.collect()
            self.context_factory.metadata = metadata
            
            # 关键修复：使用 json.dumps 确保 history 被正确序列化为字符串
            # 并且在 prompt 中明确指示模型如何处理 history
            history_str = json.dumps(self.history, ensure_ascii=False)
            
            prompt = self.context_factory.assemble(
                task_instruction=user_input,
                core_base_template=(
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
                trace_history_part1="",
                trace_history_part2=f"Conversation History:\n{history_str}",
                rag_cards=[]
            )
            
            # 2. 调用 Oracle
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
            
            # 推送日志到桥接层
            await self.gateway.bridge.send_message({
                "method": "msc/log",
                "params": {"agent_id": "main-agent", "content": response_text, "type": "thought"}
            })
            
            # 3. 解析工具调用
            tool_calls = ToolParser.parse(response_text)
            print(f"[DEBUG] Parsed Tool Calls: {tool_calls}")
            
            # 关键修复：必须记录模型自身的回复，否则上下文会断裂导致死循环
            self.history.append({"role": "assistant", "content": response_text})

            # 幂等性校验：检测重复动作
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
                # 没有工具调用且没有 FINISH，可能是在思考或卡住了
                print("[Session] No tool calls and no FINISH signal. Continuing for reflection...")
                
            # 4. 执行工具 (由工具内部处理 HIL，避免双重审批死锁)
            for call in tool_calls:
                print(f"[Session] Executing tool: {call.name}...")
                if call.name == "execute":
                    from msc.core.tools.system_ops import ExecuteTool
                    from msc.core.tools.base import ToolContext
                    
                    tool_context = ToolContext(
                        agent_id="main-agent",
                        workspace_root=self.workspace_root,
                        oracle=self.oracle,
                        gateway=self.gateway, # 传递网关引用，让工具自主请求权限
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
        self.pending_approvals: Dict[str, asyncio.Event] = {}
        self.approval_results: Dict[str, bool] = {}

    async def request_permission(self, agent_id: str, action: str, params: Dict[str, Any]) -> bool:
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

    async def handle_bridge_message(self, message: Dict[str, Any]):
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

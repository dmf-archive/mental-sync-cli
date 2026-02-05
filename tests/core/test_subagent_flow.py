import pytest
import asyncio
import json
from msc.core.og import OrchestrationGateway, Session, SessionStatus
from msc.core.anamnesis.metadata import MetadataProvider

class MockProvider:
    def __init__(self, model_name):
        self.model_name = model_name
        self.pricing = {"input_1m": 1.0, "output_1m": 2.0}

class MockOracle:
    def __init__(self):
        self.providers = [MockProvider("test-model"), MockProvider("main-agent-model")]

    async def generate(self, model_name, prompt, **kwargs):
        usage = {"input_tokens": 100, "output_tokens": 50}
        provider = next((p for p in self.providers if p.model_name == model_name), self.providers[0])
        if "agent-sub" in prompt:
            return '{"name": "execute", "parameters": {"command": "echo subagent_done"}}', usage, provider
        return '{"name": "create_agent", "parameters": {"task_description": "subtask", "model_name": "test-model"}}', usage, provider

@pytest.mark.asyncio
async def test_subagent_coroutine_spawning():
    # 1. Setup OG and Main Session
    gateway = OrchestrationGateway(bridge=None)
    oracle = MockOracle()
    
    main_session = Session(
        session_id="test-session",
        agent_id="main-agent",
        oracle=oracle,
        gateway=gateway,
        workspace_root="."
    )
    
    await main_session.start()
    
    # 2. Simulate create_agent tool call logic
    sub_agent_id = "agent-sub-123"
    sub_session = Session(
        session_id="test-session",
        agent_id=sub_agent_id,
        oracle=oracle,
        gateway=gateway,
        workspace_root="."
    )
    
    gateway.agent_registry[sub_agent_id] = sub_session
    await sub_session.start()
    
    assert sub_session.status == SessionStatus.RUNNING
    assert sub_agent_id in gateway.agent_registry

@pytest.mark.asyncio
async def test_gas_metering_logic():
    # Test if metadata correctly tracks gas_used
    provider = MetadataProvider(agent_id="test-agent")
    provider.set_pfms_status(model_name="gpt-4o", gas_used=0.05, gas_limit=1.0)
    
    metadata = provider.collect()
    assert metadata.gas_used == 0.05
    assert metadata.model_name == "gpt-4o"

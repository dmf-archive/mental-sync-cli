import pytest
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock
from msc.core.og import OrchestrationGateway, Session, SessionStatus
from msc.core.anamnesis.session import SessionManager
from msc.core.anamnesis.types import SessionMetadata
from datetime import datetime

@pytest.fixture
def mock_oracle():
    oracle = MagicMock()
    oracle.generate = AsyncMock(return_value=("Thought: I will use a tool.", [], {"input_tokens": 10, "output_tokens": 5}, MagicMock(pricing={"input_1m": 0.1, "output_1m": 0.2})))
    return oracle

@pytest.fixture
def mock_bridge():
    bridge = MagicMock()
    bridge.send_message = AsyncMock()
    return bridge

@pytest.mark.asyncio
async def test_session_lifecycle_and_gas_tracking(mock_oracle, mock_bridge, tmp_path):
    """
    验证 Session 生命周期管理与 Gas 计费逻辑
    """
    og = OrchestrationGateway(bridge=mock_bridge)
    workspace = str(tmp_path)
    
    session = Session(
        session_id="test-session",
        agent_id="main-agent",
        oracle=mock_oracle,
        gateway=og,
        workspace_root=workspace
    )
    
    await session.start()
    assert session.status == SessionStatus.RUNNING
    assert session.metadata_provider is not None
    
    # 模拟一次运行循环
    # 使用 ToolCall 命名元组以匹配 og.py 的期望
    from msc.core.anamnesis.parser import ToolCall
    mock_oracle.generate.side_effect = [
        ("I will finish.", [ToolCall(name="complete_task", parameters={"summary": "Done"}, id="call_1")], {"input_tokens": 100, "output_tokens": 50}, MagicMock(pricing={"input_1m": 1.0, "output_1m": 2.0}))
    ]
    
    await session.run_loop("Start task")
    
    assert session.status == SessionStatus.COMPLETED
    # 验证 Gas 计费: (100 * 1.0 + 50 * 2.0) / 1,000,000 = 0.0002
    assert session.metadata_provider.gas_used == pytest.approx(0.0002)
    
    await session.stop()
    assert session.status == SessionStatus.IDLE

@pytest.mark.asyncio
async def test_session_persistence_and_recovery(tmp_path):
    """
    验证 SessionManager 的持久化与恢复一致性
    """
    storage_root = str(tmp_path / "sessions")
    manager = SessionManager(storage_root)
    
    session_id = "persistent-session"
    agent_id = "agent-007"
    metadata = SessionMetadata(
        agent_id=agent_id,
        workspace_root="/tmp",
        model_name="gpt-4",
        start_time=datetime.now()
    )
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"}
    ]
    
    # 保存
    path = manager.save_session(session_id, metadata, history)
    assert os.path.exists(path)
    
    # 加载
    record = manager.load_session(session_id, agent_id)
    assert record is not None
    assert record.metadata.agent_id == agent_id
    assert record.history == history
    assert record.metadata.model_name == "gpt-4"

@pytest.mark.asyncio
async def test_og_message_routing(mock_bridge, mock_oracle, tmp_path):
    """
    验证 OG 的消息路由逻辑 (msc/chat)
    """
    og = OrchestrationGateway(bridge=mock_bridge)
    workspace = str(tmp_path)
    
    # 预注册一个 Session
    session = Session(
        session_id="chat-session",
        agent_id="main-agent",
        oracle=mock_oracle,
        gateway=og,
        workspace_root=workspace
    )
    og.agent_registry["main-agent"] = session
    await session.start()
    
    # 模拟 Bridge 消息
    msg = {
        "method": "msc/chat",
        "params": {
            "agent_id": "main-agent",
            "content": "New user message"
        }
    }
    
    # 模拟 run_loop 行为
    # 注意：Session 是 Pydantic 模型，不能直接赋值覆盖方法，需使用 patch
    from unittest.mock import patch
    with patch.object(Session, 'run_loop', new_callable=AsyncMock) as mock_run:
        await og.handle_bridge_message(msg)
        # 验证消息已加入历史
        assert any(m.get("content") == "New user message" for m in session.history)

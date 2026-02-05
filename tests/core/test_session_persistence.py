import os
import json
import shutil
import pytest
from datetime import datetime
from pathlib import Path
from msc.core.anamnesis.types import SessionMetadata, ThreadedSessionRecord
# We expect a SessionManager to handle the persistence logic
# from msc.core.og import SessionManager 

@pytest.fixture
def session_storage():
    storage_path = Path("test_storage/sessions")
    if storage_path.exists():
        shutil.rmtree(storage_path)
    storage_path.mkdir(parents=True)
    yield storage_path
    if storage_path.exists():
        shutil.rmtree(storage_path)

def test_session_persistence_red_phase(session_storage):
    # This test will fail because SessionManager and the required Pydantic models 
    # (ThreadedSessionRecord) are not fully implemented or integrated yet.
    
    from msc.core.og import SessionManager
    
    manager = SessionManager(storage_root=str(session_storage))
    
    # 1. Create dummy metadata and history
    meta = SessionMetadata(
        agent_id="main-agent",
        model_name="test-model",
        gas_used=0.01,
        workspace_root=os.getcwd()
    )
    history = [{"role": "user", "content": "hello"}]
    
    # 2. Save session
    session_dir = manager.save_session(
        session_id="test-session-123",
        metadata=meta,
        history=history
    )
    
    assert os.path.exists(session_dir)
    assert os.path.exists(os.path.join(session_dir, "main-agent.json"))
    
    # 3. Verify content
    with open(os.path.join(session_dir, "main-agent.json"), "r") as f:
        data = json.load(f)
        assert data["metadata"]["agent_id"] == "main-agent"
        assert data["history"][0]["content"] == "hello"
        # ACL should NOT be here
        assert "acl" not in data

def test_subagent_persistence_red_phase(session_storage):
    from msc.core.og import SessionManager
    
    manager = SessionManager(storage_root=str(session_storage))
    session_id = "test-multi-agent"
    
    # Save main agent
    manager.save_session(
        session_id=session_id,
        metadata=SessionMetadata(agent_id="main-agent"),
        history=[]
    )
    
    # Save sub agent
    sub_meta = SessionMetadata(agent_id="agent-sub-999", parent_id="main-agent")
    sub_history = [{"role": "user", "content": "subtask"}]
    
    manager.save_session(
        session_id=session_id,
        metadata=sub_meta,
        history=sub_history
    )
    
    session_dir = os.path.join(session_storage, session_id)
    assert os.path.exists(os.path.join(session_dir, "agent-sub-999.json"))

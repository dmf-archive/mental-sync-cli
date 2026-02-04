from datetime import datetime

from msc.core.anamnesis.context import ContextFactory
from msc.core.anamnesis.types import AnamnesisConfig, KnowledgeCard, SessionMetadata


def test_context_factory_assembles_v3_standard():
    config = AnamnesisConfig()
    metadata = SessionMetadata(
        agent_id="main-agent",
        workspace_root="e:/Dev/Chain/mental-sync-cli",
        model_name="claude-3-5-sonnet",
        start_time=datetime(2026, 2, 4, 14, 14, 9)
    )
    factory = ContextFactory(config=config, metadata=metadata)
    
    # 模拟输入
    task_instr = "Analyze dependencies"
    mode_instr = "You are Roo, a tech lead."
    notebook = "- [x] Task 1"
    project_rules = {"REQ-101": "No comments allowed."}
    # V3 接口使用消息列表
    trace_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"}
    ]
    rag_cards = [KnowledgeCard(title="Python Best Practices", content="Use type hints.")]
    
    # 模拟动态内容
    mcp_desc = "- server_name: filesystem"
    skills_desc = "- skill: brainstorming"
    mode_list = "- architect\n- code"
    model_list = "- claude-3-5-sonnet"

    # 调用新接口 build_messages
    messages = factory.build_messages(
        task_instruction=task_instr,
        mode_instruction=mode_instr,
        notebook_hot_memory=notebook,
        project_specific_rules=project_rules,
        trace_history=trace_history,
        rag_cards=rag_cards,
        available_mcp_description=mcp_desc,
        available_skills_description=skills_desc,
        mode_list=mode_list,
        model_list=model_list
    )
    
    # 验证多消息对象结构
    assert len(messages) >= 4  # System, User, Assistant, Metadata, Idea Cards (if any)
    
    # 1. 验证主 System Prompt
    system_msg = messages[0]
    assert system_msg["role"] == "system"
    prompt = system_msg["content"]
    assert task_instr in prompt
    assert mode_instr in prompt
    assert notebook in prompt
    assert "#### REQ-101\nNo comments allowed." in prompt
    # 验证清理逻辑：不应包含批注和 demo
    assert "[!PROTOCOL NOTE]" not in prompt
    assert "```demo" not in prompt
    
    # 2. 验证历史记录
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"
    
    # 3. 验证尾部注入的 Metadata & Idea Cards (最后一条)
    footer_msg = messages[-1]
    assert footer_msg["role"] == "user"
    assert "## Metadata" in footer_msg["content"]
    assert "## Idea Cards" in footer_msg["content"]
    assert "main-agent" in footer_msg["content"]
    assert "Python Best Practices" in footer_msg["content"]

def test_context_factory_normalize_history():
    config = AnamnesisConfig()
    factory = ContextFactory(config=config, metadata=SessionMetadata(agent_id="test"))
    
    # 模拟未闭合的工具调用
    history = [
        {"role": "user", "content": "Run ls"},
        {"role": "assistant", "content": "Calling ls...", "tool_calls": [{"id": "1", "type": "function"}]}
    ]
    
    normalized = factory._normalize_history(history)
    
    # 验证是否追加了虚拟结果
    assert len(normalized) == 3
    assert normalized[-1]["role"] == "tool"
    assert "interrupted" in normalized[-1]["content"].lower()

def test_context_factory_triggers_rag_on_step():
    config = AnamnesisConfig(trigger_interval=2)
    factory = ContextFactory(config=config, metadata=SessionMetadata(agent_id="test"))
    
    assert factory.should_trigger_rag(step=1) is False
    assert factory.should_trigger_rag(step=2) is True

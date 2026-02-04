import pytest
from msc.core.anamnesis.context import ContextFactory
from msc.core.anamnesis.types import AnamnesisConfig, SessionMetadata

def test_context_factory_assembles_8_sections():
    config = AnamnesisConfig()
    metadata = SessionMetadata(agent_id="test-agent", workspace_root="/tmp")
    factory = ContextFactory(config=config, metadata=metadata)
    
    # 模拟输入
    task_instr = "Do something"
    base_template = "You are an agent"
    notebook = "Memory: I like cats"
    project_rules = {"rule1.md": "Rule 1 content"}
    trace_p1 = "User: Hello\nAssistant: Hi"
    trace_p2 = "User: How are you?"
    
    prompt = factory.assemble(
        task_instruction=task_instr,
        core_base_template=base_template,
        notebook_hot_memory=notebook,
        project_specific_rules=project_rules,
        trace_history_part1=trace_p1,
        trace_history_part2=trace_p2,
        rag_cards=[]
    )
    
    # 验证 8 个 Section 是否都存在
    assert "Section 1: Task Instruction" in prompt
    assert "Section 2: Core Base Template" in prompt
    assert "Section 3: Notebook (Hot Memory)" in prompt
    assert "Section 4: Project Rules" in prompt
    assert "Section 5: Trace History (Part 1)" in prompt
    assert "Section 6: Trace History (Part 2)" in prompt
    assert "Section 7: Metadata" in prompt
    assert "Section 8: RAG Cards (Cold Memory)" in prompt
    
    # 验证内容注入
    assert task_instr in prompt
    assert "test-agent" in prompt

def test_context_factory_triggers_rag_on_step():
    config = AnamnesisConfig(trigger_interval=2)
    factory = ContextFactory(config=config, metadata=SessionMetadata(agent_id="test"))
    
    # Step 1: 不触发
    assert factory.should_trigger_rag(step=1) is False
    # Step 2: 触发
    assert factory.should_trigger_rag(step=2) is True
    # Step 3: 不触发
    assert factory.should_trigger_rag(step=3) is False
    # Step 4: 触发
    assert factory.should_trigger_rag(step=4) is True

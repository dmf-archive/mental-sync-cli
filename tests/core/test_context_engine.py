import pytest
import os
from datetime import datetime
from msc.core.anamnesis.context import ContextFactory
from msc.core.anamnesis.types import AnamnesisConfig, SessionMetadata, KnowledgeCard
from msc.core.anamnesis.rag import LiteRAG
from msc.core.anamnesis.metadata import MetadataProvider

@pytest.fixture
def mock_metadata():
    return SessionMetadata(
        agent_id="test-agent",
        workspace_root=os.getcwd(),
        model_name="test-model",
        start_time=datetime.now()
    )

@pytest.fixture
def anamnesis_config():
    return AnamnesisConfig(
        trigger_interval=1,
        max_cards_inject=2,
        search_scope=["project"]
    )

def test_context_assembly_with_metadata_and_rag(mock_metadata, anamnesis_config):
    """
    验证 ContextFactory 的组装逻辑：
    1. Metadata 正确注入
    2. RAG 卡片正确注入
    3. 历史记录规范化 (Markdown 重序列化)
    """
    factory = ContextFactory(anamnesis_config, mock_metadata)
    
    rag_cards = [
        KnowledgeCard(title="Test Card", content="Test Content", path="test.md")
    ]
    
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]
    
    messages = factory.build_messages(
        task_instruction="Do something",
        mode_instruction="You are a helper",
        notebook_hot_memory="Memory: active",
        project_specific_rules="Rule 1: Be fast",
        trace_history=history,
        rag_cards=rag_cards
    )
    
    # 验证 System Prompt 包含关键组件
    system_msg = messages[0]["content"]
    assert "Do something" in system_msg
    assert "You are a helper" in system_msg
    assert "Memory: active" in system_msg
    assert "Rule 1: Be fast" in system_msg
    
    # 验证尾部注入 (Metadata 和 Idea Cards)
    last_msg = messages[-1]["content"]
    assert "## Metadata" in last_msg
    assert "test-agent" in last_msg
    assert "## Idea Cards" in last_msg
    assert "Test Card" in last_msg
    assert "Test Content" in last_msg

def test_inter_agent_message_rendering(mock_metadata, anamnesis_config):
    """
    验证跨代理消息的 Markdown 重序列化
    """
    factory = ContextFactory(anamnesis_config, mock_metadata)
    
    raw_content = 'Message from sub-agent-1: {"type": "task_result", "status": "success", "summary": "Job done"}'
    rendered = factory._render_inter_agent_message(raw_content)
    
    assert "### 🏁 任务结果汇报：来自 `sub-agent-1`" in rendered
    assert "**状态**: ✅ SUCCESS" in rendered
    assert "Job done" in rendered

def test_lite_rag_search(tmp_path):
    """
    验证 LiteRAG 的启发式搜索逻辑
    """
    # 创建模拟知识库
    cards_dir = tmp_path / ".msc" / "knowledge-cards"
    cards_dir.mkdir(parents=True)
    
    card_content = """---
title: "Python Typing"
tags: ["python"]
---
Use list[str] instead of List."""
    (cards_dir / "python_typing.md").write_text(card_content, encoding="utf-8")
    
    config = AnamnesisConfig(search_scope=["project"], max_cards_inject=2)
    rag = LiteRAG(config, project_root=str(tmp_path))
    
    # 启发式提取关键词并搜索
    context = "I am writing some Python code with typing"
    keywords = rag._extract_keywords_heuristic(context)
    assert "Python" in keywords
    
    results = rag.search(keywords)
    assert len(results) == 1
    assert results[0].title == "Python Typing"
    assert "list[str]" in results[0].content

def test_metadata_collection():
    """
    验证 MetadataProvider 的实时数据收集
    """
    provider = MetadataProvider(agent_id="main-agent")
    metadata = provider.collect()
    
    assert metadata.agent_id == "main-agent"
    assert os.path.exists(metadata.workspace_root)
    # 验证 gas_used 初始为 0
    assert provider.gas_used == 0.0

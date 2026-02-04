import tempfile
from pathlib import Path

from msc.core.anamnesis.rag import LiteRAG
from msc.core.anamnesis.types import AnamnesisConfig


def test_heuristic_keyword_extraction():
    rag = LiteRAG(config=AnamnesisConfig())
    context = 'Implementing "DynSIHA" in Python. Use `AsyncIO` for concurrency. Refer to "RFC-123".'
    keywords = rag._extract_keywords_heuristic(context)
    
    # 应该提取引号内的词、反引号内的词、大写缩写
    assert "DynSIHA" in keywords
    assert "AsyncIO" in keywords
    assert "RFC-123" in keywords

def test_rag_search_project_priority():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # 创建项目知识卡
        project_dir = tmp_path / ".msc" / "knowledge-cards"
        project_dir.mkdir(parents=True)
        project_card = project_dir / "p1.md"
        project_card.write_text("---\ntitle: Project Card\ntags: [test]\n---\nContent about DynSIHA", encoding="utf-8")
        
        # 创建全局知识卡
        global_dir = tmp_path / "global" / "knowledge-cards"
        global_dir.mkdir(parents=True)
        global_card = global_dir / "g1.md"
        global_card.write_text("---\ntitle: Global Card\ntags: [test]\n---\nContent about DynSIHA", encoding="utf-8")
        
        rag = LiteRAG(
            config=AnamnesisConfig(search_scope=["project", "global"]),
            project_root=tmpdir,
            global_root=str(tmp_path / "global")
        )
        
        results = rag.search(["DynSIHA"])
        
        # 验证结果包含项目卡片
        titles = [c.title for c in results]
        assert "Project Card" in titles
        assert len(results) <= 3

def test_rag_parse_markdown_card():
    content = """---
title: "Test Card"
tags: ["a", "b"]
relevance_score: 0.8
---
## Body
Content here."""
    rag = LiteRAG(config=AnamnesisConfig())
    card = rag._parse_card(content, "test.md")
    
    assert card.title == "Test Card"
    assert card.tags == ["a", "b"]
    assert card.relevance_score == 0.8
    assert "## Body" in card.content

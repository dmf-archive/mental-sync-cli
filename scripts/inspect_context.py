from msc.core.anamnesis.context import ContextFactory
from msc.core.anamnesis.types import AnamnesisConfig, SessionMetadata, KnowledgeCard
from msc.core.anamnesis.metadata import MetadataProvider
from datetime import datetime

def inspect_raw_context():
    # 1. 初始化配置与元数据
    config = AnamnesisConfig(trigger_interval=1)
    provider = MetadataProvider(agent_id="MSC-Main-001")
    provider.set_pfms_status(
        model_name="claude-3.5-sonnet", 
        cost={"input": 0.003, "output": 0.015}
    )
    metadata = provider.collect()
    
    # 2. 准备模拟数据
    task_instr = "Implement a secure file upload handler in Python."
    mode_instr = "You are a senior security engineer. Follow the MSC protocol."
    notebook = "- User prefers async/await over threading.\n- Project uses Pydantic v2."
    project_rules = {
        "security.md": "Rule: Never use `os.system`.\nRule: Validate all input paths.",
        "coding-style.md": "Rule: Use type hints for all function signatures."
    }
    # V3 接口使用消息列表
    trace_history = [
        {"role": "user", "content": "I need to handle file uploads."},
        {"role": "assistant", "content": "I will help you with that. What's the target directory?"},
        {"role": "user", "content": "/var/uploads, and make sure it's safe."}
    ]
    
    # 模拟 RAG 命中的知识卡
    rag_cards = [
        KnowledgeCard(
            title="Path Validation Best Practices",
            content="Always use `pathlib.Path.resolve()` and check against a whitelist of allowed base directories.",
            tags=["security", "python"]
        ),
        KnowledgeCard(
            title="Async File I/O",
            content="Use `aiofiles` for non-blocking file operations in Python.",
            tags=["async", "performance"]
        )
    ]
    
    # 3. 组装上下文
    factory = ContextFactory(config=config, metadata=metadata)
    messages = factory.build_messages(
        task_instruction=task_instr,
        mode_instruction=mode_instr,
        notebook_hot_memory=notebook,
        project_specific_rules=project_rules,
        trace_history=trace_history,
        rag_cards=rag_cards,
        available_mcp_description="- filesystem\n- shell",
        available_skills_description="- brainstorming\n- spec",
        mode_list="- architect\n- code",
        model_list="- claude-3.5-sonnet\n- gpt-4o"
    )
    
    # 4. 打印结果
    print("="*60)
    print("MSC v3.0 MULTI-MESSAGE CONTEXT INSPECTION")
    print("="*60)
    for i, msg in enumerate(messages):
        role = msg["role"].upper()
        print(f"[{i}] ROLE: {role}")
        print("-" * 20)
        print(msg["content"])
        print("-" * 60)
    print("="*60)

if __name__ == "__main__":
    inspect_raw_context()

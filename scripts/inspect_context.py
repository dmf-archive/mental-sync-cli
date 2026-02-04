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
    base_template = "You are a senior security engineer. Follow the MSC protocol."
    notebook = "- User prefers async/await over threading.\n- Project uses Pydantic v2."
    project_rules = {
        "security.md": "Rule: Never use `os.system`.\nRule: Validate all input paths.",
        "coding-style.md": "Rule: Use type hints for all function signatures."
    }
    trace_p1 = "User: I need to handle file uploads.\nAssistant: I will help you with that. What's the target directory?"
    trace_p2 = "User: /var/uploads, and make sure it's safe."
    
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
    raw_prompt = factory.assemble(
        task_instruction=task_instr,
        core_base_template=base_template,
        notebook_hot_memory=notebook,
        project_specific_rules=project_rules,
        trace_history_part1=trace_p1,
        trace_history_part2=trace_p2,
        rag_cards=rag_cards
    )
    
    # 4. 打印结果
    print("="*40)
    print("MSC v3.0 RAW CONTEXT INSPECTION")
    print("="*40)
    print(raw_prompt)
    print("="*40)

if __name__ == "__main__":
    inspect_raw_context()

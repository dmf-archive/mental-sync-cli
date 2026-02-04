from typing import List, Dict, Any
from msc.core.anamnesis.types import AnamnesisConfig, SessionMetadata, KnowledgeCard

class ContextFactory:
    def __init__(self, config: AnamnesisConfig, metadata: SessionMetadata):
        self.config = config
        self.metadata = metadata

    def should_trigger_rag(self, step: int) -> bool:
        return step > 0 and step % self.config.trigger_interval == 0

    def assemble(
        self,
        task_instruction: str,
        core_base_template: str,
        notebook_hot_memory: str,
        project_specific_rules: Dict[str, str],
        trace_history_part1: str,
        trace_history_part2: str,
        rag_cards: List[KnowledgeCard]
    ) -> str:
        sections = []
        
        # Section 1: Task Instruction
        sections.append(f"### Section 1: Task Instruction\n\n{task_instruction}")
        
        # Section 2: Core Base Template
        sections.append(f"### Section 2: Core Base Template\n\n{core_base_template}")
        
        # Section 3: Notebook (Hot Memory)
        sections.append(f"### Section 3: Notebook (Hot Memory)\n\n{notebook_hot_memory}")
        
        # Section 4: Project Rules
        rules_content = "\n\n".join([f"#### {name}\n{content}" for name, content in project_specific_rules.items()])
        sections.append(f"### Section 4: Project Rules\n\n{rules_content}")
        
        # Section 5: Trace History (Part 1)
        sections.append(f"### Section 5: Trace History (Part 1)\n\n{trace_history_part1}")
        
        # Section 6: Trace History (Part 2)
        sections.append(f"### Section 6: Trace History (Part 2)\n\n{trace_history_part2}")
        
        # Section 7: Metadata
        metadata_str = (
            f"- **当前时间**: {self.metadata.start_time.isoformat()}\n"
            f"- **工作区根目录**: {self.metadata.workspace_root}\n"
            f"- **Agent ID**: {self.metadata.agent_id}\n"
            f"- **逻辑模型**: {self.metadata.model_name}\n"
        )
        sections.append(f"### Section 7: Metadata\n\n{metadata_str}")
        
        # Section 8: RAG Cards (Cold Memory)
        cards_content = "\n\n".join([f"#### {card.title}\n{card.content}" for card in rag_cards])
        sections.append(f"### Section 8: RAG Cards (Cold Memory)\n\n{cards_content}")
        
        return "\n\n---\n\n".join(sections)

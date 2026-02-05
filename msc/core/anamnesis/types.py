from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class KeywordExtractionStrategy(Enum):
    HEURISTIC = "heuristic"
    SELF_EXTRACT = "self_extract"

@dataclass
class KnowledgeCard:
    title: str
    content: str
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source_agent: str | None = None
    relevance_score: float = 0.0
    path: str | None = None

@dataclass
class AnamnesisConfig:
    trigger_interval: int = 1
    context_window_steps: int = 5
    max_cards_inject: int = 3
    keyword_extraction: KeywordExtractionStrategy = KeywordExtractionStrategy.HEURISTIC
    search_scope: list[str] = field(default_factory=lambda: ["project", "global"])

@dataclass
class SessionMetadata:
    agent_id: str
    start_time: datetime = field(default_factory=datetime.now)
    workspace_root: str = ""
    parent_id: str | None = None
    capabilities: list[str] = field(default_factory=list)
    model_name: str = ""
    gas_used: float = 0.0
    gas_limit: float = 0.0
    active_terminals: list[dict[str, Any]] = field(default_factory=list)
    resource_limits: dict[str, Any] = field(default_factory=dict)

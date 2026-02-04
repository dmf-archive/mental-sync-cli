from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class KeywordExtractionStrategy(Enum):
    HEURISTIC = "heuristic"
    SELF_EXTRACT = "self_extract"

@dataclass
class KnowledgeCard:
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source_agent: Optional[str] = None
    relevance_score: float = 0.0
    path: Optional[str] = None

@dataclass
class AnamnesisConfig:
    trigger_interval: int = 1
    context_window_steps: int = 5
    max_cards_inject: int = 3
    keyword_extraction: KeywordExtractionStrategy = KeywordExtractionStrategy.HEURISTIC
    search_scope: List[str] = field(default_factory=lambda: ["project", "global"])

@dataclass
class SessionMetadata:
    agent_id: str
    start_time: datetime = field(default_factory=datetime.now)
    workspace_root: str = ""
    parent_id: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    model_name: str = ""
    provider_cost: Dict[str, float] = field(default_factory=dict)
    active_terminals: List[Dict[str, Any]] = field(default_factory=list)
    resource_limits: Dict[str, Any] = field(default_factory=dict)

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class KeywordExtractionStrategy(str, Enum):
    HEURISTIC = "heuristic"
    SELF_EXTRACT = "self_extract"


class KnowledgeCard(BaseModel):
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    source_agent: str | None = None
    relevance_score: float = 0.0
    path: str | None = None


class AnamnesisConfig(BaseModel):
    trigger_interval: int = 1
    context_window_steps: int = 5
    max_cards_inject: int = 3
    keyword_extraction: KeywordExtractionStrategy = KeywordExtractionStrategy.HEURISTIC
    search_scope: list[str] = Field(default_factory=lambda: ["project", "global"])


class SessionMetadata(BaseModel):
    agent_id: str
    start_time: datetime = Field(default_factory=datetime.now)
    workspace_root: str = ""
    parent_id: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    model_name: str = ""
    gas_used: float = 0.0
    gas_limit: float = 0.0
    active_terminals: list[dict[str, Any]] = Field(default_factory=list)
    resource_limits: dict[str, Any] = Field(default_factory=dict)


class ThreadedSessionRecord(BaseModel):
    metadata: SessionMetadata
    history: list[dict[str, Any]] = Field(default_factory=list)

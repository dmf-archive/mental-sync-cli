import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel
from msc.core.anamnesis.types import SessionMetadata

class ThreadedSessionRecord(BaseModel):
    metadata: SessionMetadata
    history: list[dict[str, Any]]

class SessionManager:
    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def get_session_dir(self, session_id: str) -> Path:
        return self.storage_root / session_id

    def save_session(
        self,
        session_id: str,
        metadata: SessionMetadata,
        history: list[dict[str, Any]]
    ) -> str:
        session_dir = self.get_session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        record = ThreadedSessionRecord(metadata=metadata, history=history)
        file_path = session_dir / f"{metadata.agent_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(record.model_dump_json(indent=2))

        return str(session_dir)

    def load_session(self, session_id: str, agent_id: str) -> ThreadedSessionRecord | None:
        file_path = self.get_session_dir(session_id) / f"{agent_id}.json"
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return ThreadedSessionRecord(**data)

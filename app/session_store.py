"""In-process session memory. Same key shape the orchestrator merges on follow-ups."""

from __future__ import annotations

from typing import Optional

_SESSIONS: dict[str, dict] = {}


def get(session_id: str) -> Optional[dict]:
    row = _SESSIONS.get(session_id)
    return dict(row) if row else None


def save(session_id: str, record: dict) -> None:
    _SESSIONS[session_id] = {
        "customer_id": record.get("customer_id"),
        "last_intent": record.get("last_intent"),
        "last_entities": dict(record.get("last_entities") or {}),
        "last_language": record.get("last_language"),
        "last_facts": record.get("last_facts") or {},
    }


def clear(session_id: Optional[str] = None) -> None:
    if session_id is None:
        _SESSIONS.clear()
        return
    _SESSIONS.pop(session_id, None)


def clear_session(session_id: Optional[str] = None) -> None:
    clear(session_id)

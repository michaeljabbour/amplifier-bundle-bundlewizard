"""File-based session store — persists desktop UI chat history to ~/.amplifier/desktop-sessions/."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_STORE_DIR = Path.home() / ".amplifier" / "desktop-sessions"


def _ensure_dir() -> Path:
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    return _STORE_DIR


def save_session(
    session_id: str,
    messages: list[dict[str, Any]],
    *,
    amplifier_session_id: str | None = None,
    title: str | None = None,
    graph_state: dict | None = None,
) -> None:
    """Persist a session's messages (and optional graph state) to disk."""
    path = _ensure_dir() / f"{session_id}.json"

    if not title:
        for m in messages:
            if m.get("role") == "user":
                text = m.get("content", "")
                title = text[:80].strip() or "Untitled"
                break
        else:
            title = "Untitled"

    existing = _read_raw(path)
    now = time.time()

    data = {
        "id": session_id,
        "title": title,
        "created_at": existing.get("created_at", now) if existing else now,
        "updated_at": now,
        "amplifier_session_id": amplifier_session_id,
        "messages": messages,
        "graph_state": graph_state,
    }

    try:
        path.write_text(json.dumps(data, default=str), encoding="utf-8")
    except Exception:
        logger.debug("Failed to save session %s", session_id, exc_info=True)


def load_session(session_id: str) -> dict[str, Any] | None:
    path = _STORE_DIR / f"{session_id}.json"
    return _read_raw(path)


def list_sessions(limit: int = 50) -> list[dict[str, Any]]:
    d = _STORE_DIR
    if not d.exists():
        return []

    sessions: list[dict[str, Any]] = []
    for p in d.glob("*.json"):
        data = _read_raw(p)
        if not data:
            continue
        sessions.append(
            {
                "id": data.get("id", p.stem),
                "title": data.get("title", "Untitled"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "amplifier_session_id": data.get("amplifier_session_id"),
                "messages": data.get("messages", []),
                "graph_state": data.get("graph_state"),
            }
        )

    sessions.sort(key=lambda s: s.get("updated_at", 0), reverse=True)
    return sessions[:limit]


def delete_session(session_id: str) -> bool:
    path = _STORE_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def _read_raw(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

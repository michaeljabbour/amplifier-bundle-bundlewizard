"""Tests for graph_state persistence in session_store.save_session / list_sessions.

Loss Point 1 fix verification:
- save_session() must accept a graph_state kwarg and write it to disk.
- list_sessions() must include graph_state in each returned session summary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_GRAPH_STATE: dict[str, Any] = {
    "version": "1.0",
    "meta": {
        "bundleName": "test-bundle",
        "bundleVersion": "0.1.0",
        "phase": "explore",
        "changes": [],
    },
    "clusters": [],
    "nodes": [{"id": "n1", "type": "agent", "title": "Explorer", "properties": []}],
    "edges": [],
}


# ---------------------------------------------------------------------------
# Test 1 — save_session persists graph_state to disk
# ---------------------------------------------------------------------------


class TestSaveSessionGraphState:
    """save_session must write graph_state into the session JSON file."""

    def test_save_session_persists_graph_state(self, tmp_path: Path) -> None:
        """save_session with graph_state stores it in the JSON file on disk."""
        from bundlewizard_bridge.session_store import save_session  # noqa: PLC0415

        session_id = "test-graph-session-001"
        messages = [{"role": "user", "content": "design a bundle"}]

        with patch("bundlewizard_bridge.session_store._STORE_DIR", tmp_path):
            save_session(session_id, messages, graph_state=SAMPLE_GRAPH_STATE)

        saved_file = tmp_path / f"{session_id}.json"
        assert saved_file.exists(), "Session file must be created on disk"

        data = json.loads(saved_file.read_text(encoding="utf-8"))
        assert "graph_state" in data, "graph_state key must be present in saved JSON"
        assert data["graph_state"] is not None
        assert data["graph_state"]["version"] == "1.0"
        assert data["graph_state"]["nodes"][0]["id"] == "n1"

    def test_save_session_graph_state_none_when_not_provided(
        self, tmp_path: Path
    ) -> None:
        """save_session without graph_state stores null for graph_state."""
        from bundlewizard_bridge.session_store import save_session  # noqa: PLC0415

        session_id = "test-no-graph-session"
        messages = [{"role": "user", "content": "hello"}]

        with patch("bundlewizard_bridge.session_store._STORE_DIR", tmp_path):
            save_session(session_id, messages)

        saved_file = tmp_path / f"{session_id}.json"
        data = json.loads(saved_file.read_text(encoding="utf-8"))

        # graph_state key must be present but None
        assert "graph_state" in data
        assert data["graph_state"] is None


# ---------------------------------------------------------------------------
# Test 2 — list_sessions returns graph_state in each summary
# ---------------------------------------------------------------------------


class TestListSessionsGraphState:
    """list_sessions must include graph_state in each returned session dict."""

    def test_list_sessions_returns_graph_state(self, tmp_path: Path) -> None:
        """list_sessions includes graph_state field from saved data."""
        from bundlewizard_bridge.session_store import (  # noqa: PLC0415
            list_sessions,
            save_session,
        )

        session_id = "test-list-graph-session"
        messages = [{"role": "user", "content": "list test"}]

        with patch("bundlewizard_bridge.session_store._STORE_DIR", tmp_path):
            save_session(session_id, messages, graph_state=SAMPLE_GRAPH_STATE)
            sessions = list_sessions()

        assert len(sessions) == 1
        assert "graph_state" in sessions[0], (
            "graph_state must be present in session summary"
        )
        assert sessions[0]["graph_state"] is not None
        assert sessions[0]["graph_state"]["version"] == "1.0"

    def test_list_sessions_graph_state_none_when_not_saved(
        self, tmp_path: Path
    ) -> None:
        """list_sessions returns None for graph_state when none was saved."""
        from bundlewizard_bridge.session_store import (  # noqa: PLC0415
            list_sessions,
            save_session,
        )

        session_id = "test-list-no-graph"
        messages = [{"role": "user", "content": "no graph"}]

        with patch("bundlewizard_bridge.session_store._STORE_DIR", tmp_path):
            save_session(session_id, messages)
            sessions = list_sessions()

        assert len(sessions) == 1
        assert sessions[0].get("graph_state") is None

    def test_list_sessions_graph_state_none_for_legacy_file(
        self, tmp_path: Path
    ) -> None:
        """list_sessions returns None for graph_state from legacy files lacking the key."""
        from bundlewizard_bridge.session_store import list_sessions  # noqa: PLC0415

        # Write a legacy file without graph_state key
        legacy_file = tmp_path / "legacy-session.json"
        legacy_data = {
            "id": "legacy-session",
            "title": "Legacy",
            "created_at": 0.0,
            "updated_at": 0.0,
            "amplifier_session_id": None,
            "messages": [],
        }
        legacy_file.write_text(json.dumps(legacy_data), encoding="utf-8")

        with patch("bundlewizard_bridge.session_store._STORE_DIR", tmp_path):
            sessions = list_sessions()

        assert len(sessions) == 1
        assert sessions[0].get("graph_state") is None

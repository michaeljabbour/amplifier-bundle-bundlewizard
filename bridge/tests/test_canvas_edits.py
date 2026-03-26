"""Tests for canvas_edits message type handling in ws_handler.

These tests verify that:
1. MessageType.CANVAS_EDITS is recognized by route_message.
2. Existing message types (prompt, approval_response) still route correctly.
3. Unknown message types still return MessageType.UNKNOWN.
4. handle_websocket injects canvas edits into the next prompt exactly once.
"""

from __future__ import annotations

import asyncio
import json

from bundlewizard_bridge.ws_handler import MessageType, handle_websocket, route_message


# ---------------------------------------------------------------------------
# Message routing tests
# ---------------------------------------------------------------------------


def test_message_type_canvas_edits_recognized() -> None:
    """route_message returns CANVAS_EDITS for a canvas_edits message."""
    msg = {"type": "canvas_edits", "data": "node A -> node B"}
    result = route_message(msg)
    assert result == MessageType.CANVAS_EDITS


def test_message_type_backward_compatible() -> None:
    """Existing prompt and approval_response types still route correctly; unknown returns UNKNOWN."""
    assert route_message({"type": "prompt", "text": "hello"}) == MessageType.PROMPT
    assert (
        route_message({"type": "approval_response", "approved": True})
        == MessageType.APPROVAL_RESPONSE
    )
    assert route_message({"type": "totally_unknown"}) == MessageType.UNKNOWN


# ---------------------------------------------------------------------------
# handle_websocket canvas injection lifecycle tests
# ---------------------------------------------------------------------------


class _MockWebSocket:
    """Async-iterable WebSocket stand-in that serves preset messages."""

    def __init__(self, messages: list[dict]) -> None:
        self._messages = [json.dumps(m) for m in messages]
        self.sent: list[dict] = []

    def __aiter__(self) -> _MockWebSocket:
        return self

    async def __anext__(self) -> str:
        if not self._messages:
            raise StopAsyncIteration
        return self._messages.pop(0)

    async def send(self, raw: str) -> None:
        self.sent.append(json.loads(raw))


class _RecordingSession:
    """Minimal session that records every prompt text it receives."""

    def __init__(self) -> None:
        self.received: list[str] = []

    async def execute(self, text: str) -> str:
        self.received.append(text)
        return "ok"


def test_handle_websocket_injects_canvas_edits_into_next_prompt() -> None:
    """canvas_edits message causes the edit text to be appended to the next prompt."""
    ws = _MockWebSocket(
        [
            {"type": "canvas_edits", "data": "node A -> node B"},
            {"type": "prompt", "text": "Hello"},
        ]
    )
    session = _RecordingSession()

    asyncio.run(handle_websocket(ws, session))

    assert len(session.received) == 1
    assert session.received[0] == "Hello\n\n[CANVAS EDITS: node A -> node B]"


def test_handle_websocket_canvas_edits_cleared_after_injection() -> None:
    """canvas_edits are injected exactly once; the second prompt is unmodified."""
    ws = _MockWebSocket(
        [
            {"type": "canvas_edits", "data": "node A -> node B"},
            {"type": "prompt", "text": "First"},
            {"type": "prompt", "text": "Second"},
        ]
    )
    session = _RecordingSession()

    asyncio.run(handle_websocket(ws, session))

    assert len(session.received) == 2
    assert "[CANVAS EDITS:" in session.received[0]
    assert "[CANVAS EDITS:" not in session.received[1]
    assert session.received[1] == "Second"

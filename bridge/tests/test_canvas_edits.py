"""Tests for canvas_edits message type handling in ws_handler.

These tests verify that:
1. MessageType.CANVAS_EDITS is recognized by route_message.
2. Existing message types (prompt, approval_response) still route correctly.
3. Unknown message types still return MessageType.UNKNOWN.
"""

from __future__ import annotations

from bundlewizard_bridge.ws_handler import MessageType, route_message


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

"""Tests for _execute_prompt() WebSocket execution path in ws_handler.

These tests verify the integration between the session executor and the
WebSocket forwarding logic, including graph block extraction.
"""

from __future__ import annotations

import asyncio
import json

# The integration is exposed via session_bridge, which imports _execute_prompt
# from ws_handler — this is the actual bridge runtime path.
from bundlewizard_bridge.session_bridge import execute_prompt


class _MockWebSocket:
    """Minimal WebSocket stand-in that records sent messages."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, raw: str) -> None:  # noqa: D401
        self.sent.append(json.loads(raw))


class _MockSession:
    """Minimal Amplifier session stand-in."""

    def __init__(self, response: str) -> None:
        self._response = response

    async def execute(self, _text: str) -> str:
        return self._response


def test_execute_prompt_sends_clean_text_as_response() -> None:
    """_execute_prompt sends the graph-stripped text as a 'response' message."""
    ws = _MockWebSocket()
    session = _MockSession(
        "Here is the result.\n"
        "```bundlewizard-graph\n"
        '{"nodes": [], "edges": []}\n'
        "```\n"
        "Done."
    )
    chat_log: list[dict[str, str]] = []

    asyncio.run(execute_prompt(ws, session, "hello", chat_log))

    response_msgs = [m for m in ws.sent if m["type"] == "response"]
    assert len(response_msgs) == 1
    assert "```bundlewizard-graph" not in response_msgs[0]["data"]
    assert "Done." in response_msgs[0]["data"]


def test_execute_prompt_sends_graph_state_when_block_present() -> None:
    """_execute_prompt sends a 'graph_state' message when a graph block is present."""
    ws = _MockWebSocket()
    session = _MockSession(
        "Graph follows:\n"
        "```bundlewizard-graph\n"
        '{"nodes": [{"id": "X"}], "edges": [{"from": "X", "to": "Y"}]}\n'
        "```\n"
    )
    chat_log: list[dict[str, str]] = []

    asyncio.run(execute_prompt(ws, session, "prompt", chat_log))

    graph_msgs = [m for m in ws.sent if m["type"] == "graph_state"]
    assert len(graph_msgs) == 1
    assert graph_msgs[0]["data"]["nodes"] == [{"id": "X"}]
    assert graph_msgs[0]["data"]["edges"] == [{"from": "X", "to": "Y"}]


def test_execute_prompt_no_graph_state_when_no_block() -> None:
    """_execute_prompt does NOT send a 'graph_state' message when no graph block exists."""
    ws = _MockWebSocket()
    session = _MockSession("Plain response, no graph.")
    chat_log: list[dict[str, str]] = []

    asyncio.run(execute_prompt(ws, session, "prompt", chat_log))

    graph_msgs = [m for m in ws.sent if m["type"] == "graph_state"]
    assert len(graph_msgs) == 0


def test_execute_prompt_persists_clean_text_in_chat_log() -> None:
    """_execute_prompt appends clean_text (not raw content) to chat_log."""
    ws = _MockWebSocket()
    session = _MockSession(
        'Answer:\n```bundlewizard-graph\n{"nodes": [], "edges": []}\n```\nThat is all.'
    )
    chat_log: list[dict[str, str]] = []

    asyncio.run(execute_prompt(ws, session, "q", chat_log))

    assert len(chat_log) == 1
    assert chat_log[0]["role"] == "assistant"
    assert "```bundlewizard-graph" not in chat_log[0]["content"]
    assert "That is all." in chat_log[0]["content"]

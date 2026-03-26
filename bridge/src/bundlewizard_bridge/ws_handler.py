"""WebSocket handler for the Bundlewizard bridge.

Handles incoming WebSocket connections, routes prompts to the Amplifier
session, and extracts bundlewizard-graph fenced blocks from AI responses
before forwarding clean text and graph state to connected clients.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from enum import Enum, auto
from typing import Any

from .session_store import save_session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Message routing
# ---------------------------------------------------------------------------


class MessageType(Enum):
    """Enumeration of recognised WebSocket message types."""

    PROMPT = auto()
    APPROVAL_RESPONSE = auto()
    CANVAS_EDITS = auto()
    UNKNOWN = auto()


def route_message(msg: dict[str, Any]) -> MessageType:
    """Return the :class:`MessageType` for *msg* based on its ``type`` field."""
    msg_type = msg.get("type", "")
    if msg_type == "prompt":
        return MessageType.PROMPT
    if msg_type == "approval_response":
        return MessageType.APPROVAL_RESPONSE
    if msg_type == "canvas_edits":
        return MessageType.CANVAS_EDITS
    return MessageType.UNKNOWN


# Compiled regex that matches ```bundlewizard-graph ... ``` fenced blocks.
_GRAPH_BLOCK_RE = re.compile(
    r"```bundlewizard-graph\s*\n([\s\S]*?)```",
    re.MULTILINE,
)


def extract_graph_block(text: str) -> tuple[dict[str, Any] | None, str]:
    """Extract the last bundlewizard-graph fenced block from *text*.

    Returns a tuple of ``(graph_json, clean_text)`` where:

    * ``graph_json`` is the parsed JSON dict from the last graph block, or
      ``None`` if no block was present or the JSON was malformed.
    * ``clean_text`` is *text* with all graph blocks removed and excess blank
      lines collapsed.
    """
    matches = list(_GRAPH_BLOCK_RE.finditer(text))

    if not matches:
        return None, text

    # Parse the last match — it represents the most recent graph state.
    graph_json: dict[str, Any] | None = None
    last_match = matches[-1]
    raw_json = last_match.group(1).strip()
    try:
        parsed = json.loads(raw_json)
        if isinstance(parsed, dict):
            graph_json = parsed
        else:
            logger.warning(
                "bundlewizard-graph block contained valid JSON but not an object (got %s); ignoring.",
                type(parsed).__name__,
            )
    except json.JSONDecodeError:
        logger.warning("bundlewizard-graph block contained invalid JSON; ignoring.")

    # Strip every graph block from the text.
    clean_text = _GRAPH_BLOCK_RE.sub("", text).strip()

    # Collapse runs of three or more newlines down to two.
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)

    return graph_json, clean_text


# ---------------------------------------------------------------------------
# WebSocket handler
# ---------------------------------------------------------------------------


async def _execute_prompt(
    websocket: Any,
    session: Any,
    text: str,
    chat_log: list[dict[str, str]],
    *,
    web_session_id: str | None = None,
    latest_graph_state: list[dict[str, Any] | None] | None = None,
) -> None:
    """Execute *text* against *session* and forward results over *websocket*.

    After the AI response is received:
    * Graph blocks are extracted and forwarded as ``graph_state`` messages.
    * The cleaned response text is forwarded as a ``response`` message.
    * Only the cleaned text is persisted in *chat_log*.
    * When *web_session_id* is provided the session (including the latest graph
      state accumulated across turns) is persisted to disk via ``save_session``.
    """
    response = await session.execute(text)

    # ``response`` may be a string or an object with a ``.content`` attribute.
    content: str = response if isinstance(response, str) else response.content

    graph_json, clean_text = extract_graph_block(content)

    # Accumulate the most-recent graph state across turns so that turns without
    # a graph block still carry forward the last known graph when saving.
    if graph_json is not None and latest_graph_state is not None:
        latest_graph_state[0] = graph_json

    # Persist clean text and (if available) the latest graph state to disk.
    chat_log.append({"role": "assistant", "content": clean_text})
    if web_session_id is not None:
        save_session(
            web_session_id,
            chat_log,
            graph_state=latest_graph_state[0]
            if latest_graph_state is not None
            else None,
        )

    # Send the clean (graph-stripped) assistant text to the client.
    await websocket.send(json.dumps({"type": "response", "data": clean_text}))

    # If a graph was present, forward it as a separate graph_state message.
    if graph_json is not None:
        node_count = len(graph_json.get("nodes", []))
        edge_count = len(graph_json.get("edges", []))
        logger.info(
            "Sending graph_state: %d node(s), %d edge(s).",
            node_count,
            edge_count,
        )
        await websocket.send(json.dumps({"type": "graph_state", "data": graph_json}))


async def handle_websocket(websocket: Any, session: Any) -> None:
    """Handle an active WebSocket connection for the lifetime of the session.

    Reads incoming JSON messages, routes them by type, and dispatches each to
    the appropriate handler:

    * ``prompt`` — forwards text to the AI session, optionally prepending any
      pending canvas edits before clearing that state.
    * ``approval_response`` — placeholder for future approval gate handling.
    * ``canvas_edits`` — stores the canvas diff for injection into the next prompt.
    * All other types are logged and discarded.
    """
    chat_log: list[dict[str, str]] = []
    latest_graph_state: list[dict[str, Any] | None] = [None]
    web_session_id = str(uuid.uuid4())
    pending_canvas_edits: str | None = None

    async for raw in websocket:
        try:
            msg: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Received non-JSON message; discarding.")
            continue

        msg_type = route_message(msg)

        if msg_type == MessageType.PROMPT:
            text: str = msg.get("text", "")
            if pending_canvas_edits is not None:
                text = f"{text}\n\n[CANVAS EDITS: {pending_canvas_edits}]"
                pending_canvas_edits = None
            await _execute_prompt(
                websocket,
                session,
                text,
                chat_log,
                web_session_id=web_session_id,
                latest_graph_state=latest_graph_state,
            )

        elif msg_type == MessageType.APPROVAL_RESPONSE:
            logger.info("Received approval_response: %s", msg)

        elif msg_type == MessageType.CANVAS_EDITS:
            pending_canvas_edits = msg.get("data", "")
            logger.info("Stored pending canvas edits: %s", pending_canvas_edits)

        else:
            logger.warning("Unhandled message type '%s'; discarding.", msg.get("type"))

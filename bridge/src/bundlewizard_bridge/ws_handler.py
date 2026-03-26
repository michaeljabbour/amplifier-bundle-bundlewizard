"""WebSocket handler for the Bundlewizard bridge.

Handles incoming WebSocket connections, routes prompts to the Amplifier
session, and extracts bundlewizard-graph fenced blocks from AI responses
before forwarding clean text and graph state to connected clients.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

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
        graph_json = json.loads(raw_json)
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
) -> None:
    """Execute *text* against *session* and forward results over *websocket*.

    After the AI response is received:
    * Graph blocks are extracted and forwarded as ``graph_state`` messages.
    * The cleaned response text is forwarded as a ``response`` message.
    * Only the cleaned text is persisted in *chat_log*.
    """
    response = await session.execute(text)

    # ``response`` may be a string or an object with a ``.content`` attribute.
    content: str = response if isinstance(response, str) else response.content

    graph_json, clean_text = extract_graph_block(content)

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

    # Persist the clean text (not the raw AI output) in the conversation log.
    chat_log.append({"role": "assistant", "content": clean_text})

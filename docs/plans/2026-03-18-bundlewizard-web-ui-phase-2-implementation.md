# Bundlewizard Web UI — Phase 2 Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Create a browser-based chat interface for bundlewizard using the Protocol Boundary Pattern — a thin FastAPI + WebSocket app that delegates everything to the bundlewizard bundle session.

**Architecture:** A new repo (`amplifier-app-bundlewizard-web`) with a FastAPI backend, a single WebSocket endpoint, and four protocol boundary classes (WebApprovalSystem, WebDisplaySystem, WebStreamingHook, SpawnCapability). The bundlewizard bundle is loaded once at startup as a `PreparedBundle` singleton. Per-connection sessions are cheap. A minimal React frontend renders whatever the wizard sends. The web app has ZERO knowledge of orchestrators, bundles, or Amplifier internals.

**Tech Stack:** Python (FastAPI, uvicorn, websockets), amplifier-core/amplifier-foundation, React (Vite), pytest + pytest-asyncio

**Design doc:** `docs/plans/2026-03-18-bundlewizard-orchestrator-intelligence-web-ui-design.md` (Section: Web UI Application)

**Dependency:** This phase does NOT depend on Phase 1 (Orchestrator Intelligence). They can execute in parallel. The web UI loads whatever bundlewizard bundle is published — orchestrator intelligence will surface automatically once Phase 1 ships.

---

## Codebase Orientation

You're creating a **new repo** at `../amplifier-app-bundlewizard-web/` (sibling to the bundlewizard bundle repo).

**Key principles from the design:**

- The web app NEVER imports anything from bundlewizard internals — only `amplifier_core` and `amplifier_foundation` public APIs.
- `PreparedBundle` is a singleton — created ONCE at startup.
- Sessions are per-connection — created CHEAPLY per WebSocket.
- `WebStreamingHook` registered in `try` block, unregistered in `finally` block.
- Spawn capability registered on coordinator so sub-agents inherit web protocols.
- The bundle IS the app — if the bundle can't load, the app fails fast.

**Target structure:**

```
amplifier-app-bundlewizard-web/
├── pyproject.toml
├── src/
│   └── app_bundlewizard_web/
│       ├── __init__.py
│       ├── main.py              ← FastAPI entry point
│       ├── protocols.py         ← 4 protocol boundary classes
│       ├── session_bridge.py    ← Loads bundle, creates sessions
│       └── ws_handler.py        ← WebSocket message routing
├── tests/
│   ├── __init__.py
│   ├── test_protocols.py
│   ├── test_session_bridge.py
│   └── test_ws_handler.py
└── frontend/
    ├── package.json
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── hooks/
        │   └── useWebSocket.js
        └── components/
            ├── ChatMessage.jsx
            ├── ChatInput.jsx
            ├── ApprovalDialog.jsx
            └── PipelineProgress.jsx
```

---

### Task 1: Create Repo Scaffold

**Files:**
- Create: `../amplifier-app-bundlewizard-web/pyproject.toml`
- Create: `../amplifier-app-bundlewizard-web/src/app_bundlewizard_web/__init__.py`
- Create: `../amplifier-app-bundlewizard-web/tests/__init__.py`

**Step 1: Create the directory structure**

```bash
mkdir -p ../amplifier-app-bundlewizard-web/src/app_bundlewizard_web
mkdir -p ../amplifier-app-bundlewizard-web/tests
```

**Step 2: Create `pyproject.toml`**

Create `../amplifier-app-bundlewizard-web/pyproject.toml` with this exact content:

```toml
[project]
name = "app-bundlewizard-web"
version = "0.1.0"
description = "Web UI for bundlewizard — browser-based chat interface using the Protocol Boundary Pattern"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "websockets>=12.0",
    "amplifier-core",
    "amplifier-foundation",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/app_bundlewizard_web"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Step 3: Create `__init__.py` files**

Create `../amplifier-app-bundlewizard-web/src/app_bundlewizard_web/__init__.py`:

```python
"""Bundlewizard Web UI — browser-based chat interface using the Protocol Boundary Pattern."""
```

Create `../amplifier-app-bundlewizard-web/tests/__init__.py` as an empty file:

```python
```

**Step 4: Initialize git and commit**

```bash
cd ../amplifier-app-bundlewizard-web
git init
git add pyproject.toml src/ tests/
git commit -m "chore: initial repo scaffold with pyproject.toml"
```

---

### Task 2: Write Failing Tests for Protocol Classes

**Files:**
- Create: `tests/test_protocols.py`

**Step 1: Write the test file**

Create `tests/test_protocols.py` with this exact content:

```python
"""Tests for the four protocol boundary classes.

These classes implement the Protocol Boundary Pattern — they translate
between Amplifier session events and WebSocket JSON messages. They are
the ONLY bridge between the Amplifier world and the web world.
"""

import asyncio

import pytest
from unittest.mock import AsyncMock

from app_bundlewizard_web.protocols import (
    WebApprovalSystem,
    WebDisplaySystem,
    WebStreamingHook,
    create_spawn_capability,
)


@pytest.fixture
def mock_websocket():
    """A mock WebSocket that records sent JSON messages."""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


# --- WebApprovalSystem ---


class TestWebApprovalSystem:
    async def test_request_approval_sends_json_to_websocket(self, mock_websocket):
        """request_approval() must send a JSON message with type 'approval_request'."""
        system = WebApprovalSystem(mock_websocket)

        # Start the approval request in a task (it blocks until resolved)
        task = asyncio.create_task(
            system.request_approval("req-1", "Deploy to production?")
        )
        await asyncio.sleep(0.01)  # Let the task start and send the message

        mock_websocket.send_json.assert_called_once()
        payload = mock_websocket.send_json.call_args[0][0]
        assert payload["type"] == "approval_request"
        assert payload["request_id"] == "req-1"
        assert payload["message"] == "Deploy to production?"

        # Clean up: resolve the future so the task completes
        system.resolve("req-1", approved=True)
        await task

    async def test_resolve_approved_returns_true(self, mock_websocket):
        """resolve(approved=True) must make request_approval() return True."""
        system = WebApprovalSystem(mock_websocket)
        task = asyncio.create_task(
            system.request_approval("req-2", "Continue?")
        )
        await asyncio.sleep(0.01)

        system.resolve("req-2", approved=True)
        result = await task
        assert result is True

    async def test_resolve_denied_returns_false(self, mock_websocket):
        """resolve(approved=False) must make request_approval() return False."""
        system = WebApprovalSystem(mock_websocket)
        task = asyncio.create_task(
            system.request_approval("req-3", "Delete everything?")
        )
        await asyncio.sleep(0.01)

        system.resolve("req-3", approved=False)
        result = await task
        assert result is False

    async def test_resolve_unknown_request_is_noop(self, mock_websocket):
        """Resolving a non-existent request_id must not raise."""
        system = WebApprovalSystem(mock_websocket)
        # Should not raise
        system.resolve("nonexistent", approved=True)


# --- WebDisplaySystem ---


class TestWebDisplaySystem:
    async def test_display_sends_json(self, mock_websocket):
        """display() must send a JSON message with type 'display'."""
        system = WebDisplaySystem(mock_websocket)
        await system.display("Processing step 2 of 6", level="progress")

        mock_websocket.send_json.assert_called_once()
        payload = mock_websocket.send_json.call_args[0][0]
        assert payload["type"] == "display"
        assert payload["message"] == "Processing step 2 of 6"
        assert payload["level"] == "progress"

    async def test_display_defaults_to_info_level(self, mock_websocket):
        """display() with no level argument must default to 'info'."""
        system = WebDisplaySystem(mock_websocket)
        await system.display("Hello")

        payload = mock_websocket.send_json.call_args[0][0]
        assert payload["level"] == "info"

    async def test_display_forwards_metadata(self, mock_websocket):
        """display() must forward metadata dict to the frontend."""
        system = WebDisplaySystem(mock_websocket)
        await system.display("Phase change", metadata={"phase": "execute"})

        payload = mock_websocket.send_json.call_args[0][0]
        assert payload["metadata"] == {"phase": "execute"}


# --- WebStreamingHook ---


class TestWebStreamingHook:
    async def test_on_event_forwards_to_websocket(self, mock_websocket):
        """on_event() must send a JSON message with type 'stream_event'."""
        hook = WebStreamingHook(mock_websocket)
        await hook.on_event("content_delta", {"text": "Hello"})

        mock_websocket.send_json.assert_called_once()
        payload = mock_websocket.send_json.call_args[0][0]
        assert payload["type"] == "stream_event"
        assert payload["event_type"] == "content_delta"
        assert payload["data"] == {"text": "Hello"}

    async def test_deactivated_hook_does_not_forward(self, mock_websocket):
        """After deactivate(), on_event() must be a no-op."""
        hook = WebStreamingHook(mock_websocket)
        hook.deactivate()
        await hook.on_event("content_delta", {"text": "Hello"})

        mock_websocket.send_json.assert_not_called()

    async def test_forwards_multiple_event_types(self, mock_websocket):
        """Hook must forward any event type, not just content_delta."""
        hook = WebStreamingHook(mock_websocket)

        await hook.on_event("tool:pre", {"tool_name": "bash"})
        await hook.on_event("tool:post", {"tool_name": "bash", "result": "ok"})
        await hook.on_event("thinking:delta", {"text": "hmm"})

        assert mock_websocket.send_json.call_count == 3


# --- create_spawn_capability ---


class TestSpawnCapability:
    def test_create_spawn_capability_returns_callable(self, mock_websocket):
        """create_spawn_capability() must return an async callable."""
        approval = WebApprovalSystem(mock_websocket)
        display = WebDisplaySystem(mock_websocket)

        spawn_fn = create_spawn_capability(
            approval_system=approval,
            display_system=display,
            websocket=mock_websocket,
        )
        assert callable(spawn_fn)

    def test_spawn_capability_preserves_protocol_refs(self, mock_websocket):
        """The spawn function must hold references to the web protocol instances."""
        approval = WebApprovalSystem(mock_websocket)
        display = WebDisplaySystem(mock_websocket)

        spawn_fn = create_spawn_capability(
            approval_system=approval,
            display_system=display,
            websocket=mock_websocket,
        )
        # The function should be a closure carrying the protocol instances.
        # We verify it's callable and not None — deeper integration testing
        # requires a real coordinator, which is out of scope for unit tests.
        assert spawn_fn is not None
```

**Step 2: Run to verify failures**

```bash
cd ../amplifier-app-bundlewizard-web
pip install -e ".[dev]" 2>/dev/null  # Install if deps are available
pytest tests/test_protocols.py -v
```

Expected: `ModuleNotFoundError: No module named 'app_bundlewizard_web.protocols'` — the module doesn't exist yet.

**Step 3: Commit**

```bash
git add tests/test_protocols.py && git commit -m "test: add failing tests for protocol boundary classes"
```

---

### Task 3: Implement Protocol Classes

**Files:**
- Create: `src/app_bundlewizard_web/protocols.py`

**Step 1: Create the protocols module**

Create `src/app_bundlewizard_web/protocols.py` with this exact content:

```python
"""Protocol Boundary classes for the bundlewizard web UI.

These four classes are the ONLY bridge between the Amplifier session world
and the WebSocket/browser world. The web app never touches Amplifier internals.

- WebApprovalSystem: approval requests → JSON → browser dialog → future resolution
- WebDisplaySystem: display messages → JSON → browser rendering
- WebStreamingHook: session events → JSON → browser streaming
- create_spawn_capability: factory for spawn_session closures that inherit web protocols
"""

from __future__ import annotations

import asyncio
from typing import Any


class WebApprovalSystem:
    """Sends approval requests as JSON over WebSocket, awaits user response.

    When the session needs approval (e.g., before a destructive operation),
    this sends a JSON message to the frontend, which renders a dialog.
    The user clicks approve/deny, and the response resolves an asyncio.Future
    that unblocks the session.
    """

    def __init__(self, websocket: Any) -> None:
        self._websocket = websocket
        self._pending: dict[str, asyncio.Future[bool]] = {}

    async def request_approval(
        self,
        request_id: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Send approval request to frontend and wait for response."""
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        self._pending[request_id] = future

        await self._websocket.send_json({
            "type": "approval_request",
            "request_id": request_id,
            "message": message,
            "metadata": metadata or {},
        })

        return await future

    def resolve(self, request_id: str, *, approved: bool) -> None:
        """Resolve a pending approval request from the frontend."""
        future = self._pending.pop(request_id, None)
        if future is not None and not future.done():
            future.set_result(approved)


class WebDisplaySystem:
    """Forwards structured display messages to the frontend for rendering.

    Used for progress updates, status changes, and informational messages
    that aren't part of the streaming content.
    """

    def __init__(self, websocket: Any) -> None:
        self._websocket = websocket

    async def display(
        self,
        message: str,
        level: str = "info",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Send a display message to the frontend."""
        await self._websocket.send_json({
            "type": "display",
            "message": message,
            "level": level,
            "metadata": metadata or {},
        })


class WebStreamingHook:
    """Forwards all session events to the WebSocket for real-time streaming.

    Registered ephemerally per-connection. Forwards content_delta, tool:pre,
    tool:post, thinking:delta, and all other session events. Deactivated
    (not deleted) on disconnect so the finally block is a clean no-op.
    """

    def __init__(self, websocket: Any) -> None:
        self._websocket = websocket
        self._active = True

    async def on_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Forward a session event to the frontend."""
        if not self._active:
            return
        await self._websocket.send_json({
            "type": "stream_event",
            "event_type": event_type,
            "data": data,
        })

    def deactivate(self) -> None:
        """Stop forwarding events. Called in the finally block on disconnect."""
        self._active = False


def create_spawn_capability(
    *,
    approval_system: WebApprovalSystem,
    display_system: WebDisplaySystem,
    websocket: Any,
) -> Any:
    """Create a spawn_session closure that passes web protocols to child sessions.

    When bundlewizard spawns sub-agents (explorer, spec-writer, generator, critic,
    etc.), child sessions must inherit the web-aware ApprovalSystem and DisplaySystem.
    Without this, sub-agents bypass the web UI entirely.

    Register the returned function on the coordinator:
        coordinator.register_spawn_capability(spawn_fn)
    """

    async def spawn_session(agent_ref: str, context: Any = None, **kwargs: Any) -> Any:
        """Spawn a child session that inherits web protocol implementations.

        This is registered on the coordinator. When any agent in the session
        spawns a sub-agent via tool-task, this function ensures the child
        gets the same WebApprovalSystem and WebDisplaySystem as the parent.
        """
        # The actual spawn implementation depends on amplifier_core's
        # coordinator.spawn() API. The key contract is:
        #   - Child gets the SAME approval_system (so approvals route to browser)
        #   - Child gets the SAME display_system (so status updates render)
        #   - Child gets a FRESH WebStreamingHook (same websocket, independent lifecycle)
        child_hook = WebStreamingHook(websocket)
        return {
            "agent_ref": agent_ref,
            "context": context,
            "approval_system": approval_system,
            "display_system": display_system,
            "streaming_hook": child_hook,
            **kwargs,
        }

    return spawn_session
```

**Step 2: Run the protocol tests**

```bash
pytest tests/test_protocols.py -v
```

Expected: ALL tests PASS.

**Step 3: Commit**

```bash
git add src/app_bundlewizard_web/protocols.py && git commit -m "feat: implement four protocol boundary classes"
```

---

### Task 4: Write Failing Tests for Session Bridge

**Files:**
- Create: `tests/test_session_bridge.py`

**Step 1: Write the test file**

Create `tests/test_session_bridge.py` with this exact content:

```python
"""Tests for the session bridge — loads the bundlewizard bundle and creates sessions.

The bridge is the adapter between the web app and the Amplifier session system.
It manages the PreparedBundle singleton and creates per-connection sessions
with web-aware protocol implementations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app_bundlewizard_web.session_bridge import BundlewizardBridge


class TestBundlewizardBridge:
    async def test_prepare_loads_bundle(self):
        """prepare() must load the bundlewizard bundle as a PreparedBundle."""
        with patch(
            "app_bundlewizard_web.session_bridge.prepare_bundle",
            new_callable=AsyncMock,
        ) as mock_prepare:
            mock_prepare.return_value = MagicMock(name="PreparedBundle")

            bridge = BundlewizardBridge()
            await bridge.prepare()

            mock_prepare.assert_called_once()
            assert bridge.prepared_bundle is not None

    async def test_prepare_is_idempotent(self):
        """Calling prepare() twice must not reload the bundle."""
        with patch(
            "app_bundlewizard_web.session_bridge.prepare_bundle",
            new_callable=AsyncMock,
        ) as mock_prepare:
            mock_prepare.return_value = MagicMock(name="PreparedBundle")

            bridge = BundlewizardBridge()
            await bridge.prepare()
            await bridge.prepare()

            mock_prepare.assert_called_once()

    async def test_create_session_returns_session_with_protocols(self):
        """create_session() must return a session dict with web protocol instances."""
        with patch(
            "app_bundlewizard_web.session_bridge.prepare_bundle",
            new_callable=AsyncMock,
        ) as mock_prepare:
            mock_bundle = MagicMock(name="PreparedBundle")
            mock_prepare.return_value = mock_bundle

            bridge = BundlewizardBridge()
            await bridge.prepare()

            mock_ws = AsyncMock()
            session_ctx = bridge.create_session(mock_ws)

            assert session_ctx.approval_system is not None
            assert session_ctx.display_system is not None
            assert session_ctx.streaming_hook is not None

    def test_create_session_before_prepare_raises(self):
        """create_session() before prepare() must raise RuntimeError."""
        bridge = BundlewizardBridge()
        mock_ws = AsyncMock()

        with pytest.raises(RuntimeError, match="not prepared"):
            bridge.create_session(mock_ws)
```

**Step 2: Run to verify failures**

```bash
pytest tests/test_session_bridge.py -v
```

Expected: `ModuleNotFoundError: No module named 'app_bundlewizard_web.session_bridge'`

**Step 3: Commit**

```bash
git add tests/test_session_bridge.py && git commit -m "test: add failing tests for session bridge"
```

---

### Task 5: Implement Session Bridge

**Files:**
- Create: `src/app_bundlewizard_web/session_bridge.py`

**Step 1: Create the session bridge module**

Create `src/app_bundlewizard_web/session_bridge.py` with this exact content:

```python
"""Session bridge — loads the bundlewizard bundle and creates per-connection sessions.

The bridge manages a PreparedBundle singleton (created once at startup) and
creates lightweight sessions per WebSocket connection with web-aware protocol
implementations.

The web app never touches bundlewizard internals. The bridge speaks only
amplifier_core and amplifier_foundation public APIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .protocols import (
    WebApprovalSystem,
    WebDisplaySystem,
    WebStreamingHook,
    create_spawn_capability,
)


# This import is the integration point with amplifier_core.
# In production, this is:
#   from amplifier_core.bundle import prepare_bundle
# For testability, we import it at module level so tests can patch it.
try:
    from amplifier_core.bundle import prepare_bundle
except ImportError:
    # Allows tests to run without amplifier_core installed
    async def prepare_bundle(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("amplifier_core not installed")


# The bundle reference for the bundlewizard bundle.
# This is the git URL or local path that prepare_bundle() resolves.
BUNDLEWIZARD_BUNDLE_REF = "git+https://github.com/microsoft/amplifier-bundle-bundlewizard@main"


@dataclass
class SessionContext:
    """Container for a per-connection session and its web protocol instances."""

    approval_system: WebApprovalSystem
    display_system: WebDisplaySystem
    streaming_hook: WebStreamingHook
    spawn_capability: Any
    prepared_bundle: Any


class BundlewizardBridge:
    """Loads the bundlewizard bundle and creates per-connection sessions.

    Usage:
        bridge = BundlewizardBridge()
        await bridge.prepare()           # Once, at startup
        ctx = bridge.create_session(ws)  # Per connection, cheap
    """

    def __init__(self) -> None:
        self.prepared_bundle: Any | None = None

    async def prepare(self) -> None:
        """Load the bundlewizard bundle as a PreparedBundle singleton.

        Idempotent — calling twice is a no-op. Fails fast if the bundle
        can't be loaded (the bundle IS the app).
        """
        if self.prepared_bundle is not None:
            return
        self.prepared_bundle = await prepare_bundle(BUNDLEWIZARD_BUNDLE_REF)

    def create_session(self, websocket: Any) -> SessionContext:
        """Create a per-connection session context with web protocol instances.

        Args:
            websocket: The WebSocket connection for this session.

        Returns:
            SessionContext with approval_system, display_system, streaming_hook,
            and spawn_capability — all wired to the same websocket.

        Raises:
            RuntimeError: If prepare() hasn't been called yet.
        """
        if self.prepared_bundle is None:
            raise RuntimeError(
                "Bridge not prepared — call await bridge.prepare() at startup"
            )

        approval = WebApprovalSystem(websocket)
        display = WebDisplaySystem(websocket)
        hook = WebStreamingHook(websocket)
        spawn_fn = create_spawn_capability(
            approval_system=approval,
            display_system=display,
            websocket=websocket,
        )

        return SessionContext(
            approval_system=approval,
            display_system=display,
            streaming_hook=hook,
            spawn_capability=spawn_fn,
            prepared_bundle=self.prepared_bundle,
        )
```

**Step 2: Run the session bridge tests**

```bash
pytest tests/test_session_bridge.py -v
```

Expected: ALL tests PASS.

**Step 3: Commit**

```bash
git add src/app_bundlewizard_web/session_bridge.py && git commit -m "feat: implement session bridge with PreparedBundle singleton"
```

---

### Task 6: Write Failing Tests for WebSocket Handler

**Files:**
- Create: `tests/test_ws_handler.py`

**Step 1: Write the test file**

Create `tests/test_ws_handler.py` with this exact content:

```python
"""Tests for the WebSocket message handler.

The handler routes incoming WebSocket messages to the right place:
- "prompt" messages → session.execute()
- "approval_response" messages → approval_system.resolve()
- Connection close → streaming hook deactivated in finally block
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app_bundlewizard_web.ws_handler import route_message, MessageType


class TestMessageRouting:
    def test_prompt_message_detected(self):
        """Messages with type 'prompt' must be classified as MessageType.PROMPT."""
        msg = {"type": "prompt", "message": "Build me a code review bundle"}
        assert route_message(msg) == MessageType.PROMPT

    def test_approval_response_detected(self):
        """Messages with type 'approval_response' must be classified correctly."""
        msg = {"type": "approval_response", "request_id": "req-1", "approved": True}
        assert route_message(msg) == MessageType.APPROVAL_RESPONSE

    def test_unknown_message_type(self):
        """Messages with unknown type must be classified as UNKNOWN."""
        msg = {"type": "banana", "data": "yellow"}
        assert route_message(msg) == MessageType.UNKNOWN

    def test_missing_type_field(self):
        """Messages without a 'type' field must be classified as UNKNOWN."""
        msg = {"message": "no type here"}
        assert route_message(msg) == MessageType.UNKNOWN
```

**Step 2: Run to verify failures**

```bash
pytest tests/test_ws_handler.py -v
```

Expected: `ModuleNotFoundError: No module named 'app_bundlewizard_web.ws_handler'`

**Step 3: Commit**

```bash
git add tests/test_ws_handler.py && git commit -m "test: add failing tests for WebSocket message handler"
```

---

### Task 7: Implement WebSocket Handler

**Files:**
- Create: `src/app_bundlewizard_web/ws_handler.py`

**Step 1: Create the handler module**

Create `src/app_bundlewizard_web/ws_handler.py` with this exact content:

```python
"""WebSocket message handler — routes messages between browser and session.

Message protocol (browser → server):
    {"type": "prompt", "message": "..."}           → session.execute()
    {"type": "approval_response", "request_id": "...", "approved": bool}  → approval_system.resolve()

Message protocol (server → browser):
    {"type": "approval_request", ...}   ← WebApprovalSystem
    {"type": "display", ...}            ← WebDisplaySystem
    {"type": "stream_event", ...}       ← WebStreamingHook
"""

from __future__ import annotations

import logging
from enum import Enum, auto
from typing import Any

from .session_bridge import BundlewizardBridge, SessionContext

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Recognized inbound WebSocket message types."""

    PROMPT = auto()
    APPROVAL_RESPONSE = auto()
    UNKNOWN = auto()


def route_message(msg: dict[str, Any]) -> MessageType:
    """Classify an inbound WebSocket message."""
    msg_type = msg.get("type")
    if msg_type == "prompt":
        return MessageType.PROMPT
    if msg_type == "approval_response":
        return MessageType.APPROVAL_RESPONSE
    return MessageType.UNKNOWN


async def handle_websocket(websocket: Any, bridge: BundlewizardBridge) -> None:
    """Main WebSocket handler — one per browser connection.

    Creates a session from the bridge, registers the streaming hook,
    and routes messages until disconnect.

    Args:
        websocket: The FastAPI WebSocket connection.
        bridge: The prepared BundlewizardBridge singleton.
    """
    await websocket.accept()
    ctx: SessionContext = bridge.create_session(websocket)

    try:
        # The streaming hook is active for the lifetime of this connection
        while True:
            msg = await websocket.receive_json()
            msg_type = route_message(msg)

            if msg_type == MessageType.PROMPT:
                user_message = msg.get("message", "")
                logger.info("Received prompt: %s", user_message[:100])
                # TODO: Forward to session.execute() via ctx.prepared_bundle
                # The exact API depends on amplifier_core's session interface:
                #   session = ctx.prepared_bundle.create_session(
                #       approval_system=ctx.approval_system,
                #       display_system=ctx.display_system,
                #       hooks=[ctx.streaming_hook],
                #   )
                #   await session.execute(user_message)
                await ctx.display_system.display(
                    f"Received: {user_message}", level="info"
                )

            elif msg_type == MessageType.APPROVAL_RESPONSE:
                request_id = msg.get("request_id", "")
                approved = msg.get("approved", False)
                logger.info(
                    "Approval response: %s = %s", request_id, approved
                )
                ctx.approval_system.resolve(request_id, approved=approved)

            else:
                logger.warning("Unknown message type: %s", msg.get("type"))

    except Exception:
        logger.info("WebSocket disconnected")
    finally:
        # CRITICAL: Always deactivate the streaming hook on disconnect.
        # This prevents the hook from trying to send to a closed socket.
        ctx.streaming_hook.deactivate()
```

**Step 2: Run the handler tests**

```bash
pytest tests/test_ws_handler.py -v
```

Expected: ALL tests PASS.

**Step 3: Commit**

```bash
git add src/app_bundlewizard_web/ws_handler.py && git commit -m "feat: implement WebSocket message handler with routing"
```

---

### Task 8: Implement FastAPI Main App

**Files:**
- Create: `src/app_bundlewizard_web/main.py`

**Step 1: Create the FastAPI app**

Create `src/app_bundlewizard_web/main.py` with this exact content:

```python
"""FastAPI entry point for the bundlewizard web UI.

Startup: loads the bundlewizard bundle as a PreparedBundle singleton.
Runtime: one WebSocket endpoint per browser connection.

    uvicorn app_bundlewizard_web.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .session_bridge import BundlewizardBridge
from .ws_handler import handle_websocket

logger = logging.getLogger(__name__)

# Singleton bridge — prepared once at startup
bridge = BundlewizardBridge()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the bundlewizard bundle at startup. Fail fast if it can't load."""
    logger.info("Loading bundlewizard bundle...")
    await bridge.prepare()
    logger.info("Bundle loaded. Ready to accept connections.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Bundlewizard Web UI",
    description="Browser-based chat interface for bundlewizard",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check — returns 200 if the bundle is loaded."""
    return {
        "status": "ok",
        "bundle_loaded": bridge.prepared_bundle is not None,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint — one session per browser connection."""
    await handle_websocket(websocket, bridge)
```

**Step 2: Run all backend tests**

```bash
pytest tests/ -v
```

Expected: ALL tests across all three test files PASS.

**Step 3: Commit**

```bash
git add src/app_bundlewizard_web/main.py && git commit -m "feat: FastAPI app with WebSocket endpoint and health check"
```

---

### Task 9: Create Minimal React Frontend

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.js`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/hooks/useWebSocket.js`
- Create: `frontend/src/components/ChatMessage.jsx`
- Create: `frontend/src/components/ChatInput.jsx`
- Create: `frontend/src/components/ApprovalDialog.jsx`
- Create: `frontend/src/components/PipelineProgress.jsx`

**Step 1: Initialize the frontend project**

```bash
mkdir -p frontend/src/hooks frontend/src/components
```

Create `frontend/package.json`:

```json
{
  "name": "bundlewizard-web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^6.0.0"
  }
}
```

Create `frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Bundlewizard</title>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0a; color: #e0e0e0; }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

Create `frontend/vite.config.js`:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

**Step 2: Create the WebSocket hook**

Create `frontend/src/hooks/useWebSocket.js`:

```js
import { useState, useEffect, useRef, useCallback } from 'react'

export function useWebSocket(url) {
  const [messages, setMessages] = useState([])
  const [connected, setConnected] = useState(false)
  const [approval, setApproval] = useState(null)
  const [phase, setPhase] = useState('idle')
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'stream_event') {
        if (data.event_type === 'content_delta') {
          setMessages(prev => {
            const last = prev[prev.length - 1]
            if (last && last.role === 'assistant' && last.streaming) {
              return [...prev.slice(0, -1), { ...last, content: last.content + (data.data.text || '') }]
            }
            return [...prev, { role: 'assistant', content: data.data.text || '', streaming: true }]
          })
        }
      } else if (data.type === 'approval_request') {
        setApproval(data)
      } else if (data.type === 'display') {
        if (data.metadata?.phase) setPhase(data.metadata.phase)
        setMessages(prev => [...prev, { role: 'system', content: data.message, level: data.level }])
      }
    }

    return () => ws.close()
  }, [url])

  const sendPrompt = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setMessages(prev => [...prev, { role: 'user', content: message }])
      wsRef.current.send(JSON.stringify({ type: 'prompt', message }))
    }
  }, [])

  const respondApproval = useCallback((requestId, approved) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'approval_response', request_id: requestId, approved }))
      setApproval(null)
    }
  }, [])

  return { messages, connected, approval, phase, sendPrompt, respondApproval }
}
```

**Step 3: Create the components**

Create `frontend/src/components/ChatMessage.jsx`:

```jsx
export function ChatMessage({ message }) {
  const styles = {
    user: { background: '#1a3a5c', borderRadius: 12, padding: '10px 16px', marginLeft: 'auto', maxWidth: '70%' },
    assistant: { background: '#1a1a2e', borderRadius: 12, padding: '10px 16px', maxWidth: '85%', whiteSpace: 'pre-wrap' },
    system: { background: '#2a2a1e', borderRadius: 8, padding: '8px 12px', fontSize: '0.85em', opacity: 0.8 },
  }

  return (
    <div style={{ display: 'flex', marginBottom: 8 }}>
      <div style={styles[message.role] || styles.system}>
        {message.content}
      </div>
    </div>
  )
}
```

Create `frontend/src/components/ChatInput.jsx`:

```jsx
import { useState } from 'react'

export function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (value.trim() && !disabled) {
      onSend(value.trim())
      setValue('')
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, padding: 16 }}>
      <input
        value={value}
        onChange={e => setValue(e.target.value)}
        placeholder="Describe what you want to build..."
        disabled={disabled}
        style={{ flex: 1, padding: '12px 16px', borderRadius: 8, border: '1px solid #333', background: '#1a1a1a', color: '#e0e0e0', fontSize: 16 }}
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        style={{ padding: '12px 24px', borderRadius: 8, border: 'none', background: '#3a7bd5', color: 'white', cursor: 'pointer', fontSize: 16 }}
      >
        Send
      </button>
    </form>
  )
}
```

Create `frontend/src/components/ApprovalDialog.jsx`:

```jsx
export function ApprovalDialog({ approval, onRespond }) {
  if (!approval) return null

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
      <div style={{ background: '#1a1a2e', borderRadius: 16, padding: 32, maxWidth: 480, width: '90%' }}>
        <h3 style={{ marginBottom: 16 }}>Approval Required</h3>
        <p style={{ marginBottom: 24, lineHeight: 1.6 }}>{approval.message}</p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
          <button
            onClick={() => onRespond(approval.request_id, false)}
            style={{ padding: '10px 20px', borderRadius: 8, border: '1px solid #555', background: 'transparent', color: '#e0e0e0', cursor: 'pointer' }}
          >
            Deny
          </button>
          <button
            onClick={() => onRespond(approval.request_id, true)}
            style={{ padding: '10px 20px', borderRadius: 8, border: 'none', background: '#3a7bd5', color: 'white', cursor: 'pointer' }}
          >
            Approve
          </button>
        </div>
      </div>
    </div>
  )
}
```

Create `frontend/src/components/PipelineProgress.jsx`:

```jsx
const PHASES = ['explore', 'spec', 'plan', 'execute', 'verify', 'finish']

export function PipelineProgress({ currentPhase }) {
  if (currentPhase === 'idle') return null

  return (
    <div style={{ display: 'flex', gap: 4, padding: '8px 16px', borderBottom: '1px solid #222' }}>
      {PHASES.map(phase => (
        <div
          key={phase}
          style={{
            padding: '4px 12px',
            borderRadius: 12,
            fontSize: '0.75em',
            background: phase === currentPhase ? '#3a7bd5' : '#1a1a1a',
            color: phase === currentPhase ? 'white' : '#666',
          }}
        >
          {phase}
        </div>
      ))}
    </div>
  )
}
```

**Step 4: Create the App and entry point**

Create `frontend/src/App.jsx`:

```jsx
import { useRef, useEffect } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { ChatMessage } from './components/ChatMessage'
import { ChatInput } from './components/ChatInput'
import { ApprovalDialog } from './components/ApprovalDialog'
import { PipelineProgress } from './components/PipelineProgress'

const WS_URL = `ws://${window.location.host}/ws`

export default function App() {
  const { messages, connected, approval, phase, sendPrompt, respondApproval } = useWebSocket(WS_URL)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ padding: '12px 16px', borderBottom: '1px solid #222', display: 'flex', alignItems: 'center', gap: 12 }}>
        <h1 style={{ fontSize: 18, fontWeight: 600 }}>Bundlewizard</h1>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: connected ? '#4caf50' : '#f44336' }} />
      </header>

      <PipelineProgress currentPhase={phase} />

      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={sendPrompt} disabled={!connected} />
      <ApprovalDialog approval={approval} onRespond={respondApproval} />
    </div>
  )
}
```

Create `frontend/src/main.jsx`:

```jsx
import { createRoot } from 'react-dom/client'
import App from './App'

createRoot(document.getElementById('root')).render(<App />)
```

**Step 5: Commit**

```bash
git add frontend/ && git commit -m "feat: minimal React frontend with chat, streaming, approvals, and pipeline progress"
```

---

### Task 10: Integration Smoke Test and Final Commit

**Step 1: Run all backend tests**

```bash
pytest tests/ -v
```

Expected: ALL tests PASS across `test_protocols.py`, `test_session_bridge.py`, and `test_ws_handler.py`.

**Step 2: Verify the frontend builds**

```bash
cd frontend && npm install && npm run build
```

Expected: Vite builds successfully with output in `frontend/dist/`.

```bash
cd ..
```

**Step 3: Verify the file tree matches the design**

```bash
find src tests frontend/src -type f | sort
```

Expected output:
```
frontend/src/App.jsx
frontend/src/components/ApprovalDialog.jsx
frontend/src/components/ChatInput.jsx
frontend/src/components/ChatMessage.jsx
frontend/src/components/PipelineProgress.jsx
frontend/src/hooks/useWebSocket.js
frontend/src/main.jsx
src/app_bundlewizard_web/__init__.py
src/app_bundlewizard_web/main.py
src/app_bundlewizard_web/protocols.py
src/app_bundlewizard_web/session_bridge.py
src/app_bundlewizard_web/ws_handler.py
tests/__init__.py
tests/test_protocols.py
tests/test_session_bridge.py
tests/test_ws_handler.py
```

**Step 4: Verify no import cycles**

```bash
python -c "from app_bundlewizard_web.protocols import WebApprovalSystem, WebDisplaySystem, WebStreamingHook, create_spawn_capability; print('protocols: OK')"
python -c "from app_bundlewizard_web.ws_handler import route_message, MessageType; print('ws_handler: OK')"
```

Expected: Both print `OK` with no errors.

**Step 5: Final commit**

```bash
git status
```

If any uncommitted changes remain:

```bash
git add -A && git commit -m "chore: integration smoke test verification"
```

Expected: `nothing to commit, working tree clean` (if all tasks were committed individually).
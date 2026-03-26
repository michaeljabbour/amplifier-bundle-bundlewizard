# Phase 1: Foundation — Bug Fixes + Bridge Changes

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Fix the four blocking bugs and add bridge-side graph extraction so the desktop app has a working chat pipeline and can receive structured graph state from the AI.

**Architecture:** Fix WebSocket race, delete duplicate SYSTEM_PREAMBLE, unify persistence to the Python bridge's `session_store.py`, forward thinking blocks as separate events, change the bridge bundle URI to load `bundles/desktop.yaml`, add `extract_graph_block()` to strip `bundlewizard-graph` fenced blocks from responses and send them as separate `graph_state` WebSocket messages, and add `canvas_edits` message handling to inject user canvas changes into prompts.

**Tech Stack:** Swift 5 (SwiftUI, @Observable, @MainActor), Python 3.11+ (FastAPI, WebSocket, async/await), Swift Testing framework (`import Testing`, `@Suite`, `@Test`, `#expect`)

**Repos:**
- `amplifier-app-bundlewizard-macos` at `/Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/`
- `amplifier-bundle-bundlewizard` at `/Users/michaeljabbour/dev/amplifier-bundle-bundlewizard/`

**Quality bar reference:** `/Users/michaeljabbour/Downloads/cicd-wizard-canvas.html`

---

## Conventions Discovered From Codebase

- **Swift tests** use `import Testing` + `@testable import BundlewizardCore`, `@Suite("Name")`, `@Test("description")`, `#expect(...)`. NOT XCTest.
- **Models** are `Codable, Sendable` structs in `Sources/BundlewizardCore/Models/`.
- **Services** are `@Observable @MainActor public final class` in `Sources/BundlewizardCore/Services/`.
- **Views** are in `Sources/bundlewizard/Views/`.
- **Python bridge** files are in `bridge/src/bundlewizard_bridge/`.
- **No bridge tests exist yet** — we add them at `bridge/tests/`.
- **Build command:** `cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build`
- **Test command:** `cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test`
- **Python test command:** `cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/ -v`
- **Package.swift** uses `swift-tools-version: 6.0` but `swiftLanguageModes: [.v5]` (strict concurrency OFF).

---

### Task 1: Fix WebSocket Race on `newConversation()`

**Files:**
- Modify: `Sources/BundlewizardCore/Services/AmplifierService.swift` (lines 157, 187-194, 196-201, 218-221, 449, 466-472)
- Modify: `Sources/bundlewizard/Views/ContentView.swift` (line 187)
- Test: `Tests/BundlewizardCoreTests/WebSocketReadyTests.swift` (create)

**Problem:** `reconnectForNewSession()` calls `disconnect()` then fires `connect()` inside a detached `Task` with a 200ms sleep. If `send()` fires before the reconnect completes, the WebSocket is nil and the message silently fails.

**Step 1: Write the failing test**

Create `Tests/BundlewizardCoreTests/WebSocketReadyTests.swift`:

```swift
import Testing
@testable import BundlewizardCore

@Suite("WebSocket ready gate")
struct WebSocketReadyTests {
    @Test("webSocketReady starts as false")
    @MainActor func startsNotReady() {
        let bm = BridgeManager()
        let service = AmplifierService(bridgeManager: bm)
        #expect(service.webSocketReady == false)
    }

    @Test("webSocketReady is true after connect sets it")
    @MainActor func readyAfterConnect() async {
        let bm = BridgeManager()
        let service = AmplifierService(bridgeManager: bm)
        // Simulate the ready flag being set (connect() would set it after handshake)
        service.webSocketReady = true
        #expect(service.webSocketReady == true)
    }

    @Test("send returns early when not connected and webSocket is nil")
    @MainActor func sendEarlyReturnWhenDisconnected() async {
        let bm = BridgeManager()
        let service = AmplifierService(bridgeManager: bm)
        // send() on an unconnected service should not crash or hang
        await service.send("test message")
        // Should have added an error message or simply returned
        // The key assertion: isLoading should be false (not stuck)
        #expect(service.isLoading == false)
    }
}
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test --filter WebSocketReadyTests 2>&1 | tail -20
```

Expected: FAIL — `webSocketReady` property doesn't exist yet.

**Step 3: Implement the fix**

In `Sources/BundlewizardCore/Services/AmplifierService.swift`, make these changes:

1. Add a `webSocketReady` property after line 157 (after `activityPhase`):

```swift
    public var webSocketReady = false
```

2. Update `connect()` (lines 187-194) to set the flag. Replace the entire method:

```swift
    public func connect() async throws {
        let url = URL(string: "ws://127.0.0.1:\(bridgeManager.port)/ws")!
        let session = URLSession(configuration: .default)
        webSocket = session.webSocketTask(with: url)
        webSocket?.resume()
        webSocketReady = true
        receiveTask = Task { await receiveLoop() }
        Log.swift("WebSocket connected to port \(bridgeManager.port)")
    }
```

3. Update `disconnect()` (lines 196-201) to clear the flag. Replace the entire method:

```swift
    public func disconnect() {
        webSocketReady = false
        receiveTask?.cancel()
        receiveTask = nil
        webSocket?.cancel(with: .normalClosure, reason: nil)
        webSocket = nil
    }
```

4. Replace `reconnectForNewSession()` (lines 466-472) to await the reconnect:

```swift
    /// Disconnect and reconnect WebSocket to get a fresh session from the bridge.
    private func reconnectForNewSession() async {
        disconnect()
        try? await Task.sleep(for: .milliseconds(200))
        try? await connect()
    }
```

5. Update `newConversation()` (line 449) signature to be async:

```swift
    public func newConversation() async {
```

And change the reconnect call inside it from `reconnectForNewSession()` to `await reconnectForNewSession()`.

6. Update the `send()` method's WebSocket nil check (lines 218-221). Replace:

```swift
        // Ensure WebSocket is connected
        if webSocket == nil {
            try? await connect()
            try? await Task.sleep(for: .milliseconds(200))
        }
```

With:

```swift
        // Ensure WebSocket is connected
        guard webSocketReady, webSocket != nil else {
            Log.warn("WebSocket not ready — cannot send")
            messages.append(ChatMessage(role: .error, text: "Not connected to bridge. Please wait for connection."))
            isLoading = false
            return
        }
```

**Step 4: Update callers of `newConversation()`**

In `Sources/bundlewizard/Views/ContentView.swift`, the HistoryPanel calls `service.newConversation()` on line 187. Wrap it in a Task. Replace:

```swift
            Button {
                service.newConversation()
                withAnimation { showHistory = false }
            } label: {
```

With:

```swift
            Button {
                Task { await service.newConversation() }
                withAnimation { showHistory = false }
            } label: {
```

**Step 5: Run tests to verify they pass**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test --filter WebSocketReadyTests 2>&1 | tail -20
```

Expected: PASS

**Step 6: Verify the full test suite still passes**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: All tests pass (the `BuildPromptTests` will be updated in Task 2).

**Step 7: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "fix: add webSocketReady gate to prevent send() before connection completes"
```

---

### Task 2: Delete SYSTEM_PREAMBLE and buildPrompt()

**Files:**
- Modify: `Sources/BundlewizardCore/Services/AmplifierService.swift` (lines 101-143, 170, 235-238, 273-276, 460, 528-539, 573-659)
- Delete: `Tests/BundlewizardCoreTests/BuildPromptTests.swift`
- Delete: `Tests/BundlewizardCoreTests/ClassifyStepTests.swift`
- Delete: `Tests/BundlewizardCoreTests/ExtractWorkflowStepsTests.swift`
- Modify: `Sources/bundlewizard/Views/ContentView.swift` (lines 82-124)
- Test: `Tests/BundlewizardCoreTests/SendRawPromptTests.swift` (create)

**Problem:** `SYSTEM_PREAMBLE` duplicates the bundle's own `context/instructions.md`. The `buildPrompt()` method prepends it to every user message. The `extractWorkflowSteps()` and `classifyStep()` methods are regex-based canvas population that will be replaced by structured `bundlewizard-graph` emissions.

**Step 1: Write the new test**

Create `Tests/BundlewizardCoreTests/SendRawPromptTests.swift`:

```swift
import Testing
@testable import BundlewizardCore

@Suite("Raw prompt — no preamble")
struct SendRawPromptTests {
    @Test("serializeTranscript does not contain SYSTEM CONTEXT")
    func noPreambleInTranscript() {
        let msgs = [ChatMessage(role: .user, text: "Hello")]
        let transcript = AmplifierService.serializeTranscript(msgs)
        #expect(!transcript.contains("SYSTEM CONTEXT"))
    }

    @Test("extractDOT is still available")
    func extractDOTStillWorks() {
        let text = """
        ```dot
        digraph G { A -> B }
        ```
        """
        let dot = AmplifierService.extractDOT(from: text)
        #expect(dot != nil)
        #expect(dot!.contains("A -> B"))
    }
}
```

**Step 2: Run test to verify it passes** (it should already pass since `serializeTranscript` never used the preamble)

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test --filter SendRawPromptTests 2>&1 | tail -20
```

Expected: PASS

**Step 3: Delete the code**

In `Sources/BundlewizardCore/Services/AmplifierService.swift`:

1. **Delete the entire `// MARK: - System Preamble` section** (lines 101-143) — the `private let SYSTEM_PREAMBLE` string.

2. **Delete `parsedWorkflowSteps` property** (line 170):
   ```swift
       public var parsedWorkflowSteps: [(title: String, nodeType: String)] = []
   ```

3. **Replace the `buildPrompt` call in `send()`** (around lines 235-238). Replace:
   ```swift
           let fullPrompt = Self.buildPrompt(
               userText: text,
               attachments: attachment.map { [(name: $0.name, contents: $0.contents)] } ?? []
           )

           // Send prompt over WebSocket
           let payload: [String: Any] = ["type": "prompt", "message": fullPrompt]
   ```

   With:
   ```swift
           // Build prompt — raw user text + optional attachment prefix
           var promptText = text
           if let att = attachment {
               promptText = "[Attached: \(att.name)]\n\(att.contents)\n[End attachment]\n\n" + promptText
           }

           // Send prompt over WebSocket
           let payload: [String: Any] = ["type": "prompt", "message": promptText]
   ```

4. **Delete the `extractWorkflowSteps` post-processing** (lines 273-276):
   ```swift
           let steps = Self.extractWorkflowSteps(from: responseText)
           if !steps.isEmpty {
               parsedWorkflowSteps = steps
           }
   ```

5. **In `newConversation()`**, delete the line `parsedWorkflowSteps = []`.

6. **Delete the `buildPrompt()` static method** in the extension (lines 528-539).

7. **Delete the `extractWorkflowSteps()` static method** (lines 573-645).

8. **Delete the `classifyStep()` static method** (lines 647-659).

**Step 4: Delete the test files for deleted code**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos
rm Tests/BundlewizardCoreTests/BuildPromptTests.swift
rm Tests/BundlewizardCoreTests/ClassifyStepTests.swift
rm Tests/BundlewizardCoreTests/ExtractWorkflowStepsTests.swift
```

**Step 5: Update ContentView**

In `Sources/bundlewizard/Views/ContentView.swift`, **delete the entire `.onChange(of: service.parsedWorkflowSteps.count)` block** (lines 82-124). This is the block that starts with:
```swift
            // Auto-populate canvas when workflow steps are detected in response
            .onChange(of: service.parsedWorkflowSteps.count) { _, newCount in
```
Delete from line 82 through the closing `}` on line 124.

**Step 6: Run full test suite**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -30
```

Expected: All remaining tests pass. Build succeeds.

**Step 7: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "refactor: delete SYSTEM_PREAMBLE, buildPrompt(), extractWorkflowSteps(), classifyStep()

The bundle's own context/instructions.md provides the system prompt.
Structured bundlewizard-graph emissions will replace regex-based canvas population."
```

---

### Task 3: Unify Persistence — Delete Swift-Side Storage, Add REST Endpoints

**Files:**
- Modify: `Sources/BundlewizardCore/Services/AmplifierService.swift` (lines 183, 281-282, 461, 494-521)
- Modify: `bridge/src/bundlewizard_bridge/main.py` (add REST endpoints after line 58)
- Delete: `Tests/BundlewizardCoreTests/PersistenceTests.swift`
- Test: `Tests/BundlewizardCoreTests/PersistenceRemovedTests.swift` (create)

**Problem:** Swift saves to `~/.bundlewizard/conversations.json` and Python saves to `~/.amplifier/desktop-sessions/`. Two stores diverge. Python's `session_store.py` is the source of truth.

**Step 1: Write the test**

Create `Tests/BundlewizardCoreTests/PersistenceRemovedTests.swift`:

```swift
import Testing
@testable import BundlewizardCore

@Suite("Persistence removed from Swift")
struct PersistenceRemovedTests {
    @Test("Conversations start empty — no disk loading")
    @MainActor func noLocalPersistence() {
        let bm = BridgeManager()
        let service = AmplifierService(bridgeManager: bm)
        #expect(service.conversations.isEmpty)
    }
}
```

**Step 2: Delete Swift-side persistence**

In `Sources/BundlewizardCore/Services/AmplifierService.swift`:

1. **In `init()`** (line 183), remove `loadConversationsFromDisk()`. Replace:
   ```swift
       public init(bridgeManager: BridgeManager) {
           self.bridgeManager = bridgeManager
           loadConversationsFromDisk()
       }
   ```
   With:
   ```swift
       public init(bridgeManager: BridgeManager) {
           self.bridgeManager = bridgeManager
       }
   ```

2. **In `send()`**, remove the `saveCurrentConversation()` and `saveToDisk()` calls at the end of the method (around lines 281-282). Delete these two lines:
   ```swift
           saveCurrentConversation()
           saveToDisk()
   ```

3. **In `newConversation()`**, remove the `saveToDisk()` call. Delete the line:
   ```swift
           saveToDisk()
   ```

4. **Delete the entire `// MARK: - Persistence` section** (lines 494-521) — `storagePath`, `saveToDisk()`, and `loadConversationsFromDisk()`.

**Step 3: Delete old persistence test**

```bash
rm Tests/BundlewizardCoreTests/PersistenceTests.swift
```

**Step 4: Add REST endpoints to the bridge**

In `bridge/src/bundlewizard_bridge/main.py`, add this import after line 27 (`from .ws_handler import handle_websocket`):

```python
from .session_store import list_sessions, load_session, delete_session
```

Then add these endpoints after the `/health` endpoint (after line 58):

```python
@app.get("/sessions")
async def get_sessions(limit: int = 50) -> list[dict[str, Any]]:
    """List recent sessions for the history panel."""
    return list_sessions(limit=limit)


@app.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """Load a specific session's messages."""
    data = load_session(session_id)
    if data is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return data


@app.delete("/sessions/{session_id}")
async def remove_session(session_id: str) -> dict[str, str]:
    """Delete a session."""
    deleted = delete_session(session_id)
    return {"status": "deleted" if deleted else "not_found"}
```

**Step 5: Run tests**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: All tests pass.

**Step 6: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "refactor: unify persistence — delete Swift-side storage, add REST endpoints to bridge

Swift no longer saves to ~/.bundlewizard/conversations.json.
Bridge session_store.py at ~/.amplifier/desktop-sessions/ is the single source of truth.
Added GET /sessions, GET /sessions/{id}, DELETE /sessions/{id} endpoints."
```

---

### Task 4: Thinking Block Forwarding

**Files:**
- Modify: `bridge/src/bundlewizard_bridge/protocols.py` (lines 111-132 — WebStreamingHook)
- Modify: `Sources/BundlewizardCore/Services/AmplifierService.swift` (lines 405-412 — handleStreamEvent)
- Test: `bridge/tests/test_thinking_blocks.py` (create)
- Test: `Tests/BundlewizardCoreTests/ThinkingBlockTests.swift` (create)

**Problem:** The bridge registers hooks for `content_block:start` but doesn't distinguish thinking blocks from text blocks. Swift can't populate `.thinking` ChatMessages.

**Step 1: Write the Python test**

Create `bridge/tests/__init__.py` (empty file) and `bridge/tests/test_thinking_blocks.py`:

```python
"""Tests for thinking block extraction from streaming events."""


def test_thinking_block_start_detected():
    """The streaming hook should identify thinking blocks by their type field."""
    from bundlewizard_bridge.protocols import WebStreamingHook

    data = {"type": "thinking", "index": 0}
    assert WebStreamingHook.is_thinking_block(data) is True


def test_text_block_not_thinking():
    """Regular text blocks should not be identified as thinking."""
    from bundlewizard_bridge.protocols import WebStreamingHook

    data = {"type": "text", "index": 0}
    assert WebStreamingHook.is_thinking_block(data) is False


def test_missing_type_not_thinking():
    """Events without a type field should not be identified as thinking."""
    from bundlewizard_bridge.protocols import WebStreamingHook

    assert WebStreamingHook.is_thinking_block({}) is False
    assert WebStreamingHook.is_thinking_block(None) is False
```

**Step 2: Run Python test to verify it fails**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/test_thinking_blocks.py -v 2>&1 | tail -20
```

Expected: FAIL — `is_thinking_block` doesn't exist yet.

**Step 3: Add `is_thinking_block` to WebStreamingHook**

In `bridge/src/bundlewizard_bridge/protocols.py`:

1. Update `WebStreamingHook.__init__` (line 114). Replace:
   ```python
       def __init__(self, websocket: Any) -> None:
           self._websocket = websocket
           self._active = True
   ```
   With:
   ```python
       def __init__(self, websocket: Any) -> None:
           self._websocket = websocket
           self._active = True
           self._in_thinking_block = False
   ```

2. Replace the `on_event` method (lines 118-132):
   ```python
       async def on_event(self, event_type: str, data: Any) -> None:
           """Forward a streaming event over WebSocket (no-op when deactivated).

           Thinking blocks are remapped to thinking:start / thinking:end events
           so Swift can populate .thinking ChatMessages.
           """
           if not self._active:
               return

           # Remap content_block events for thinking blocks
           actual_event_type = event_type
           if event_type == "content_block:start" and self.is_thinking_block(data):
               actual_event_type = "thinking:start"
               self._in_thinking_block = True
           elif event_type == "content_block:end" and self._in_thinking_block:
               actual_event_type = "thinking:end"
               self._in_thinking_block = False

           try:
               await self._websocket.send_json(
                   {
                       "type": MSG_STREAM_EVENT,
                       "event_type": actual_event_type,
                       "data": self._make_serializable(data),
                   }
               )
           except Exception:
               logger.debug("Failed to forward %s event to WebSocket", event_type)
   ```

3. Add the `is_thinking_block` static method after `_make_serializable` (around line 157):
   ```python
       @staticmethod
       def is_thinking_block(data: Any) -> bool:
           """Check if a content_block event is a thinking block."""
           if isinstance(data, dict):
               return data.get("type") == "thinking"
           return False
   ```

**Step 4: Run Python test to verify it passes**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/test_thinking_blocks.py -v 2>&1 | tail -20
```

Expected: PASS

**Step 5: Write the Swift test**

Create `Tests/BundlewizardCoreTests/ThinkingBlockTests.swift`:

```swift
import Testing
@testable import BundlewizardCore

@Suite("Thinking block handling")
struct ThinkingBlockTests {
    @Test("ChatMessage.Role includes thinking case")
    func thinkingRoleExists() {
        let msg = ChatMessage(role: .thinking, text: "Analyzing the problem...")
        #expect(msg.role == .thinking)
    }

    @Test("Thinking message starts collapsed")
    func thinkingStartsCollapsed() {
        let msg = ChatMessage(role: .thinking, text: "...", collapsed: true)
        #expect(msg.collapsed == true)
    }
}
```

**Step 6: Update Swift `handleStreamEvent` to create thinking messages**

In `Sources/BundlewizardCore/Services/AmplifierService.swift`, add a `currentThinkingId` property near the other private properties (after line 178, `currentAssistantId`):

```swift
    private var currentThinkingId: UUID?
```

Then update `handleStreamEvent` (around line 405). Insert these two new cases after the `case "content_block:end": break` line:

```swift
        case "thinking:start":
            activityPhase = .thinking
            statusLine = "Thinking..."
            let thinkingMsg = ChatMessage(role: .thinking, text: "", collapsed: true)
            currentThinkingId = thinkingMsg.id
            if let aidx = messages.firstIndex(where: { $0.id == currentAssistantId }) {
                messages.insert(thinkingMsg, at: aidx)
            } else {
                messages.append(thinkingMsg)
            }

        case "thinking:end":
            currentThinkingId = nil
            activityPhase = .responding
            statusLine = "Receiving response..."
```

**Step 7: Run full test suite**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: All tests pass.

**Step 8: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: forward thinking blocks as separate events from bridge to Swift

Bridge remaps content_block:start with type=thinking to thinking:start/end.
Swift creates .thinking ChatMessages and populates the purple collapsible bubble."
```

---

### Task 5: Bridge Bundle URI Change

**Files:**
- Modify: `bridge/src/bundlewizard_bridge/session_bridge.py` (lines 35-37)
- Test: `bridge/tests/test_bundle_ref.py` (create)

**Step 1: Write the test**

Create `bridge/tests/test_bundle_ref.py`:

```python
"""Tests for the bundle reference URI."""


def test_bundle_ref_points_to_desktop_variant():
    """The bridge should load the desktop bundle variant, not the base bundle."""
    from bundlewizard_bridge.session_bridge import BUNDLEWIZARD_BUNDLE_REF

    assert "bundles/desktop.yaml" in BUNDLEWIZARD_BUNDLE_REF
    assert "amplifier-bundle-bundlewizard" in BUNDLEWIZARD_BUNDLE_REF


def test_bundle_ref_uses_subdirectory_fragment():
    """The desktop variant is specified via #subdirectory= fragment."""
    from bundlewizard_bridge.session_bridge import BUNDLEWIZARD_BUNDLE_REF

    assert "#subdirectory=" in BUNDLEWIZARD_BUNDLE_REF
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/test_bundle_ref.py -v 2>&1 | tail -20
```

Expected: FAIL — current URI doesn't contain `bundles/desktop.yaml`.

**Step 3: Update the bundle reference**

In `bridge/src/bundlewizard_bridge/session_bridge.py`, replace lines 35-37:

```python
BUNDLEWIZARD_BUNDLE_REF = (
    "git+https://github.com/michaeljabbour/amplifier-bundle-bundlewizard@main"
)
```

With:

```python
BUNDLEWIZARD_BUNDLE_REF = (
    "git+https://github.com/michaeljabbour/amplifier-bundle-bundlewizard@main"
    "#subdirectory=bundles/desktop.yaml"
)
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/test_bundle_ref.py -v 2>&1 | tail -20
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: bridge loads desktop bundle variant (bundles/desktop.yaml)

The desktop variant inherits the base bundle and adds canvas awareness context."
```

---

### Task 6: Bridge Graph Block Extraction

**Files:**
- Modify: `bridge/src/bundlewizard_bridge/ws_handler.py` (add extract_graph_block function, update _execute_prompt at lines 74-77, 80)
- Test: `bridge/tests/test_graph_extraction.py` (create)

**Step 1: Write the test**

Create `bridge/tests/test_graph_extraction.py`:

```python
"""Tests for bundlewizard-graph block extraction."""

import json


def test_extract_graph_block_valid():
    """Should extract valid JSON from a bundlewizard-graph fence."""
    from bundlewizard_bridge.ws_handler import extract_graph_block

    graph_data = {
        "version": "1",
        "meta": {"phase": "explore"},
        "nodes": [],
        "edges": [],
        "clusters": [],
    }
    text = f"""Here is the architecture:

```bundlewizard-graph
{json.dumps(graph_data, indent=2)}
```

The canvas has been updated."""

    graph_json, clean_text = extract_graph_block(text)

    assert graph_json is not None
    assert graph_json["version"] == "1"
    assert graph_json["meta"]["phase"] == "explore"
    assert "bundlewizard-graph" not in clean_text
    assert "canvas has been updated" in clean_text
    assert "Here is the architecture" in clean_text


def test_extract_graph_block_no_block():
    """Should return None when no bundlewizard-graph block exists."""
    from bundlewizard_bridge.ws_handler import extract_graph_block

    text = "This is a normal response with no graph."
    graph_json, clean_text = extract_graph_block(text)

    assert graph_json is None
    assert clean_text == text


def test_extract_graph_block_malformed_json():
    """Should return None for malformed JSON inside the fence."""
    from bundlewizard_bridge.ws_handler import extract_graph_block

    text = """```bundlewizard-graph
{this is not valid json}
```"""

    graph_json, clean_text = extract_graph_block(text)

    assert graph_json is None
    # Clean text should still have the block stripped
    assert "bundlewizard-graph" not in clean_text


def test_extract_graph_block_multiple_blocks():
    """Should extract only the last block (latest state)."""
    from bundlewizard_bridge.ws_handler import extract_graph_block

    block1 = json.dumps({"version": "1", "meta": {"phase": "explore"}, "nodes": [], "edges": [], "clusters": []})
    block2 = json.dumps({"version": "1", "meta": {"phase": "spec"}, "nodes": [], "edges": [], "clusters": []})

    text = f"""First:

```bundlewizard-graph
{block1}
```

Second:

```bundlewizard-graph
{block2}
```"""

    graph_json, clean_text = extract_graph_block(text)

    assert graph_json is not None
    assert graph_json["meta"]["phase"] == "spec"
    assert "bundlewizard-graph" not in clean_text


def test_extract_preserves_other_code_blocks():
    """Should not strip non-graph code blocks."""
    from bundlewizard_bridge.ws_handler import extract_graph_block

    text = """Here's YAML:

```yaml
name: my-bundle
```

And graph:

```bundlewizard-graph
{"version": "1", "meta": {}, "nodes": [], "edges": [], "clusters": []}
```"""

    graph_json, clean_text = extract_graph_block(text)

    assert graph_json is not None
    assert "```yaml" in clean_text
    assert "my-bundle" in clean_text
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/test_graph_extraction.py -v 2>&1 | tail -20
```

Expected: FAIL — `extract_graph_block` doesn't exist.

**Step 3: Implement `extract_graph_block`**

In `bridge/src/bundlewizard_bridge/ws_handler.py`, add these imports at the top (after `import asyncio` on line 5):

```python
import json
import re
```

Then add the function after the existing imports (after line 16, before the `MessageType` class):

```python
# Pattern matches ```bundlewizard-graph ... ``` fenced blocks
_GRAPH_BLOCK_RE = re.compile(
    r"```bundlewizard-graph\s*\n([\s\S]*?)```",
    re.MULTILINE,
)


def extract_graph_block(text: str) -> tuple[dict[str, Any] | None, str]:
    """Extract the last bundlewizard-graph fenced block from response text.

    Returns (graph_json, clean_text) where:
    - graph_json is the parsed JSON dict, or None if no valid block found
    - clean_text is the response with all bundlewizard-graph blocks stripped
    """
    matches = list(_GRAPH_BLOCK_RE.finditer(text))
    if not matches:
        return None, text

    # Parse the last block (most recent state)
    last_match = matches[-1]
    raw_json = last_match.group(1).strip()

    graph_json: dict[str, Any] | None = None
    try:
        graph_json = json.loads(raw_json)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Malformed JSON in bundlewizard-graph block: %.100s", raw_json)

    # Strip all graph blocks from the text
    clean_text = _GRAPH_BLOCK_RE.sub("", text).strip()
    # Clean up any resulting triple+ newlines
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)

    return graph_json, clean_text
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/test_graph_extraction.py -v 2>&1 | tail -20
```

Expected: PASS

**Step 5: Wire `extract_graph_block` into `_execute_prompt`**

In `bridge/src/bundlewizard_bridge/ws_handler.py`, in the `_execute_prompt` function, replace lines 74-77 and 80:

Replace:
```python
        response = await session.execute(text)
        content = response or ""

        await websocket.send_json({"type": "response", "content": content})

        # Persist — append assistant message and save.
        chat_log.append({"role": "assistant", "content": content})
```

With:
```python
        response = await session.execute(text)
        content = response or ""

        # Extract graph state if present
        graph_json, clean_text = extract_graph_block(content)

        await websocket.send_json({"type": "response", "content": clean_text})

        if graph_json:
            await websocket.send_json({"type": "graph_state", "data": graph_json})
            logger.info(
                "Sent graph_state (%d nodes, %d edges)",
                len(graph_json.get("nodes", [])),
                len(graph_json.get("edges", [])),
            )

        # Persist — append assistant message and save (clean text without graph blocks).
        chat_log.append({"role": "assistant", "content": clean_text})
```

**Step 6: Run all bridge tests**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/ -v 2>&1 | tail -30
```

Expected: All PASS.

**Step 7: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: extract bundlewizard-graph blocks from AI responses in bridge

Adds extract_graph_block() that strips graph fenced blocks from response text
and sends them as separate graph_state WebSocket messages. Chat receives clean
text with graph blocks removed."
```

---

### Task 7: Bridge Canvas Edits Injection

**Files:**
- Modify: `bridge/src/bundlewizard_bridge/ws_handler.py` (MessageType enum, route_message, handle_websocket)
- Test: `bridge/tests/test_canvas_edits.py` (create)

**Step 1: Write the test**

Create `bridge/tests/test_canvas_edits.py`:

```python
"""Tests for canvas_edits message handling."""


def test_message_type_canvas_edits_recognized():
    """The route_message function should recognize canvas_edits type."""
    from bundlewizard_bridge.ws_handler import MessageType, route_message

    msg = {"type": "canvas_edits", "data": "Added node: my-agent"}
    result = route_message(msg)
    assert result == MessageType.CANVAS_EDITS


def test_message_type_backward_compatible():
    """Existing message types should still route correctly."""
    from bundlewizard_bridge.ws_handler import MessageType, route_message

    assert route_message({"type": "prompt", "message": "hello"}) == MessageType.PROMPT
    assert route_message({"type": "approval_response"}) == MessageType.APPROVAL_RESPONSE
    assert route_message({"type": "unknown_thing"}) == MessageType.UNKNOWN
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/test_canvas_edits.py -v 2>&1 | tail -20
```

Expected: FAIL — `CANVAS_EDITS` not in `MessageType`.

**Step 3: Implement canvas_edits handling**

In `bridge/src/bundlewizard_bridge/ws_handler.py`:

1. Add `CANVAS_EDITS` to the `MessageType` enum. Replace:
   ```python
   class MessageType(Enum):
       PROMPT = auto()
       APPROVAL_RESPONSE = auto()
       UNKNOWN = auto()
   ```
   With:
   ```python
   class MessageType(Enum):
       PROMPT = auto()
       APPROVAL_RESPONSE = auto()
       CANVAS_EDITS = auto()
       UNKNOWN = auto()
   ```

2. Update `route_message` to recognize canvas_edits. Replace:
   ```python
   def route_message(msg: dict[str, Any]) -> MessageType:
       msg_type = msg.get("type")
       if msg_type == "prompt":
           return MessageType.PROMPT
       if msg_type == "approval_response":
           return MessageType.APPROVAL_RESPONSE
       return MessageType.UNKNOWN
   ```
   With:
   ```python
   def route_message(msg: dict[str, Any]) -> MessageType:
       msg_type = msg.get("type")
       if msg_type == "prompt":
           return MessageType.PROMPT
       if msg_type == "approval_response":
           return MessageType.APPROVAL_RESPONSE
       if msg_type == "canvas_edits":
           return MessageType.CANVAS_EDITS
       return MessageType.UNKNOWN
   ```

3. In `handle_websocket`, add canvas_edits state tracking. After the `chat_log` declaration (around line 104), add:
   ```python
       pending_canvas_edits: str | None = None
   ```

4. In the `PROMPT` handler, inject canvas edits. Replace:
   ```python
               if message_type is MessageType.PROMPT:
                   text = msg.get("message", "")
                   logger.info("Received prompt: %.100s", text)
   ```
   With:
   ```python
               if message_type is MessageType.PROMPT:
                   text = msg.get("message", "")

                   # Inject pending canvas edits into the prompt
                   if pending_canvas_edits:
                       text += f"\n\n[CANVAS EDITS: {pending_canvas_edits}]"
                       pending_canvas_edits = None

                   logger.info("Received prompt: %.100s", text)
   ```

5. After the `APPROVAL_RESPONSE` handler (around line 135), add the `CANVAS_EDITS` handler:
   ```python
               elif message_type is MessageType.CANVAS_EDITS:
                   pending_canvas_edits = msg.get("data", "")
                   logger.info("Received canvas edits: %.100s", pending_canvas_edits)
   ```

**Step 4: Run test to verify it passes**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/test_canvas_edits.py -v 2>&1 | tail -20
```

Expected: PASS

**Step 5: Run all bridge tests**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/ -v 2>&1 | tail -30
```

Expected: All PASS.

**Step 6: Run full Swift test suite**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: All PASS.

**Step 7: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: bridge handles canvas_edits messages and injects into prompts

When Swift sends canvas_edits before a prompt, the bridge appends
[CANVAS EDITS: ...] to the prompt text so the AI can incorporate
user canvas changes into its next graph emission."
```

---

## Phase 1 Complete Checklist

After all 7 tasks, verify:

```bash
# Swift tests
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -10

# Python bridge tests
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/ -v 2>&1 | tail -20

# Build succeeds
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build 2>&1 | tail -5
```

**What changed:**
1. WebSocket race fixed — `send()` gates on `webSocketReady` flag
2. `SYSTEM_PREAMBLE` deleted — user's raw text goes to bridge
3. Swift-side persistence deleted — bridge REST endpoints serve history
4. Thinking blocks forwarded — bridge remaps to `thinking:start/end`, Swift creates `.thinking` messages
5. Bundle URI updated — bridge loads `bundles/desktop.yaml` (created in Phase 2)
6. Graph extraction added — `extract_graph_block()` strips graph blocks, sends as `graph_state` message
7. Canvas edits handling — bridge accepts `canvas_edits` messages and injects into prompts

**Next:** Phase 2 creates the bundle files and Swift models.

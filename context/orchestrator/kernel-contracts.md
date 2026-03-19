# Orchestrator Kernel Contracts

Authoritative reference for orchestrator module kernel compliance. Every orchestrator module must satisfy the contracts documented here.

---

## The Orchestrator Protocol

All orchestrators implement the `OrchestratorProtocol` and are registered via `mount()`. The core contract:

```python
from typing import Protocol
from amplifier_core import (
    Session,
    ProviderRegistry,
    ToolRegistry,
    HookRegistry,
    ExecutionContext,
    OrchestratorResult,
)


class OrchestratorProtocol(Protocol):
    async def execute(
        self,
        session: Session,
        providers: ProviderRegistry,
        tools: ToolRegistry,
        hooks: HookRegistry,
        context: ExecutionContext,
    ) -> OrchestratorResult:
        """Run the execution loop and return the final result."""
        ...
```

`OrchestratorResult` carries the final assistant message, token counts, tool call history, and any metadata the orchestrator wants to surface.

---

## Required Events

Every orchestrator **MUST** emit the following 7 events. The kernel uses these events to drive hooks, logging, and observability. An orchestrator that omits any event breaks hook composition.

| Event | When | Payload |
|-------|------|---------|
| `execution:start` | Before the first provider call | `{session_id, turn, context}` |
| `execution:end` | After the final result is produced | `{session_id, turn, result, token_counts}` |
| `provider:request` | Before each provider call | `{session_id, turn, iteration, messages, provider_id}` |
| `provider:response` | After each provider response | `{session_id, turn, iteration, response, provider_id}` |
| `tool:pre` | Before each tool execution | `{session_id, turn, iteration, tool_name, tool_input}` |
| `tool:post` | After each tool execution | `{session_id, turn, iteration, tool_name, tool_result}` |
| `orchestrator:complete` | When the orchestrator finishes | `{session_id, turn, final_message, orchestrator_name}` |

Emit events using the kernel event bus:

```python
await context.events.emit("execution:start", {
    "session_id": session.id,
    "turn": session.turn_count,
    "context": context.metadata,
})
```

---

## HookResult Handling

Hooks attached to kernel events return `HookResult` values that the orchestrator must honour. When multiple hooks fire on the same event, the orchestrator resolves them by **priority order**:

```
deny  >  modify  >  inject_context  >  ask_user  >  continue
```

Higher-priority results take precedence. A `deny` from any hook always wins.

| HookResult | Orchestrator Action |
|------------|---------------------|
| `deny` | Abort the current operation immediately. Return an error result to the caller. Do not proceed with the provider call or tool execution. |
| `modify` | Replace the event payload with the modified payload provided by the hook before proceeding. |
| `inject_context` | Append the hook-supplied context message(s) to the message list before the next provider call. |
| `ask_user` | Pause execution, surface the hook's question to the user, and wait for a response before continuing. |
| `continue` | No action required. Proceed normally. |

### Resolving Multiple HookResults

```python
results = await hooks.run("tool:pre", payload)

# Priority resolution
if any(r.type == "deny" for r in results):
    return deny_result(results)

for r in results:
    if r.type == "modify":
        payload = r.modified_payload

injected = [r.context for r in results if r.type == "inject_context"]
if injected:
    messages.extend(injected)

for r in results:
    if r.type == "ask_user":
        user_response = await context.ask_user(r.question)
        messages.append(user_response)
```

---

## The mount() Pattern

Every orchestrator module exposes a `mount()` function. The kernel calls `mount()` at startup to register the orchestrator with the coordinator.

```python
# amplifier_module_loop_myname/orchestrator.py

from amplifier_core import Coordinator, OrchestratorResult
from .loop import MyNameOrchestrator


def mount(coordinator: Coordinator) -> None:
    """Register this orchestrator with the kernel coordinator."""
    orchestrator = MyNameOrchestrator()
    coordinator.register_orchestrator(
        name="loop-myname",
        orchestrator=orchestrator,
    )
```

### pyproject.toml Entry Point

Modules are discovered by the kernel via Python entry points. Register the `mount` function under the `amplifier.modules` group in `pyproject.toml`:

```toml
[project.entry-points."amplifier.modules"]
loop-myname = "amplifier_module_loop_myname.orchestrator:mount"
```

The kernel iterates all installed `amplifier.modules` entry points at startup, calls each `mount()` function, and builds the orchestrator registry.

---

## Naming Convention

| Artifact | Convention | Example |
|----------|-----------|---------|
| Package (PyPI / wheel) | `amplifier-module-loop-{name}` | `amplifier-module-loop-convergence` |
| Python module (import path) | `amplifier_module_loop_{name}` | `amplifier_module_loop_convergence` |
| Orchestrator name (runtime) | `loop-{name}` | `loop-convergence` |
| Entry point key | `loop-{name}` | `loop-convergence` |

The `loop-` prefix signals that this package provides an execution loop, as opposed to a tool, hook, context, or provider module.

---

## Testing Requirements

Orchestrator modules must include tests that verify protocol compliance and event correctness. The `amplifier_core.testing` module provides the following fixtures:

| Fixture | Purpose |
|---------|---------|
| `MockProvider` | Scripted provider that returns predetermined responses without network calls |
| `MockTool` | Fake tool implementation for verifying tool dispatch and result handling |
| `EventRecorder` | Captures emitted events for assertion in tests |
| `TestCoordinator` | Minimal coordinator for mounting and running orchestrators in isolation |

### Required Test Categories

Every orchestrator module must include tests in these four categories:

1. **Protocol Compliance** — Verify that `mount()` successfully registers the orchestrator and that `execute()` returns a valid `OrchestratorResult`.

2. **Event Emission** — Use `EventRecorder` to assert that all 7 required events are emitted in the correct order for a single turn.

3. **HookResult Handling** — Test that each `HookResult` type (`deny`, `modify`, `inject_context`, `ask_user`) is correctly handled when returned by a hook attached to a kernel event.

4. **Loop Termination** — Verify that the orchestrator terminates correctly: on a stop condition, on a tool-free response, and when the iteration limit is reached.

# Orchestrator Catalog

Complete reference for existing orchestrators and reusable pattern library.

---

## Existing Orchestrators

All three orchestrators share the **same loop shape**: receive input → call provider → handle tool calls → repeat until done. They differ only in what they **emit** during execution.

| Name | Description | Key Characteristic |
|------|-------------|-------------------|
| `loop-basic` | Simple request/response cycle | No streaming; delivers complete response at end of turn |
| `loop-streaming` | Token-by-token delivery | Streams via `content_delta` events; same loop shape as basic |
| `loop-events` | Full observability | Detailed event emissions for every hook firing; same loop shape as streaming |

**Key insight:** `loop-basic`, `loop-streaming`, and `loop-events` are not fundamentally different orchestrators — they are the same loop with increasing verbosity of events. When building a new orchestrator, start with whichever matches your observability needs, then modify the loop behavior.

---

## Pattern Library

Five reusable patterns for common orchestration needs. Each can be scaffolded as a new module using the naming conventions below.

---

### Pattern 1: `loop-parallel`

| Attribute | Detail |
|-----------|--------|
| **Loop shape** | Single provider; tool calls dispatched concurrently via `asyncio.gather` |
| **Events** | Standard `tool:pre` / `tool:post` per tool; `provider:request` / `provider:response` per LLM call |
| **Use when** | One provider returns multiple tool calls in a single response that are independent and can execute simultaneously |
| **Termination** | When the provider stops issuing tool calls (same as `loop-basic`) |

**How it differs from `loop-basic`:** `loop-basic` dispatches tool calls sequentially. `loop-parallel` collects all tool calls from a single provider response and runs them concurrently with `asyncio.gather`, then appends all results before the next provider call. The loop iteration count is identical; only the execution model for tool dispatch changes.

---

### Pattern 2: `loop-multi-provider`

| Attribute | Detail |
|-----------|--------|
| **Loop shape** | Structured turns between N providers following a role schedule |
| **Events** | `provider:request` / `provider:response` emitted per provider per turn; `tool:pre` / `tool:post` as normal |
| **Use when** | Different providers have different capabilities, cost profiles, or roles (e.g., reasoning model for planning, fast model for execution) |
| **Termination** | When the active provider signals completion or the role schedule reaches its end condition |

**Constraints:** All providers are mounted at session initialization. The role schedule (which provider handles which turn) is defined at loop construction time, not dynamically. Switching providers mid-loop requires this pattern; `inject_context` or hook composition cannot route across providers.

---

### Pattern 3: `loop-phased`

| Attribute | Detail |
|-----------|--------|
| **Loop shape** | Two sequential phases: Phase 1 runs without tools; Phase 2 runs standard tool-calling loop |
| **Events** | Phase boundary emits a custom `phase:transition` event; each phase uses standard provider/tool events |
| **Use when** | You need structured decomposition before execution — e.g., plan first (no tools), then implement (with tools) |
| **Termination** | Phase 1 terminates on provider stop-token or max turns; Phase 2 terminates when provider stops issuing tool calls |

**Phase 1 — Decompose:** The provider is called without any tools registered. It produces a plan or decomposition as structured output or plain text.

**Phase 2 — Execute:** The full tool set is available. The Phase 1 output is injected into the context before the first Phase 2 provider call, and the loop proceeds identically to `loop-basic`.

---

### Pattern 4: `loop-convergence`

| Attribute | Detail |
|-----------|--------|
| **Loop shape** | K passes with evaluation after each pass; terminates on quality threshold or iteration limit |
| **Events** | `convergence:pass_complete` after each evaluation; standard provider/tool events within each pass |
| **Use when** | Output quality is measurable and iterative refinement improves it — e.g., code review + fix cycles, essay drafts, test-driven generation |
| **Termination** | Fixed-iteration (always K passes) or quality-threshold (stop when evaluator score ≥ threshold); both modes supported |

**Evaluator contract:** The evaluator is a function `(output: str) -> float` returning a score in [0, 1]. A threshold of 1.0 forces all K passes. The loop tracks the best output seen so far and returns it regardless of which pass produced it.

---

### Pattern 5: `loop-swarm`

| Attribute | Detail |
|-----------|--------|
| **Loop shape** | Parent session manages N concurrent child sessions; parent dispatches work via `tool-task`; children run independently |
| **Events** | Parent emits `swarm:child_spawned` and `swarm:child_complete`; children emit their own standard events |
| **Use when** | Work can be decomposed into independent subtasks that benefit from true parallelism across separate sessions |
| **Termination** | Parent completes when all child sessions have terminated; individual children terminate using their own loop shape |

**Lineage:** Parent/child relationships are tracked via `parent_id` on each child session. The parent session ID is injected at spawn time. This allows observability tools to reconstruct the full execution tree.

**Child sessions:** Each child is a full session with its own context, tools, and provider. The parent communicates via `tool-task` calls, not shared memory. Children are isolated — a failure in one child does not terminate siblings.

---

## Pattern Selection Guide

| User need | Recommended pattern |
|-----------|-------------------|
| Tool calls are independent and slow | `loop-parallel` |
| Different steps need different models | `loop-multi-provider` |
| Planning before execution is required | `loop-phased` |
| Output quality needs iterative refinement | `loop-convergence` |
| Work decomposes into independent parallel subtasks | `loop-swarm` |
| Simple single-provider request/response | `loop-basic` (existing) |
| Streaming output to the user | `loop-streaming` (existing) |
| Full hook-level observability | `loop-events` (existing) |

---

## Naming Conventions

All orchestrator modules **must** use the `loop-` prefix. This is mandatory — it signals that the module owns a provider loop and implements the `mount()` contract as an orchestrator.

| Slot | Convention | Example |
|------|-----------|---------|
| Display name | `loop-{descriptor}` | `loop-parallel` |
| Package name | `amplifier-module-loop-{descriptor}` | `amplifier-module-loop-parallel` |
| Python module | `amplifier_module_loop_{descriptor}` | `amplifier_module_loop_parallel` |
| Entry point | `loop-{descriptor}` | `loop-parallel` |

The entry point in `pyproject.toml` must match the display name exactly:

```toml
[project.entry-points."amplifier.modules"]
loop-parallel = "amplifier_module_loop_parallel:mount"
```

**The `loop-` prefix is mandatory.** Modules that implement a provider loop but omit the prefix will not be recognized as orchestrators by the kernel and will fail the naming conventions check during bundle validation.

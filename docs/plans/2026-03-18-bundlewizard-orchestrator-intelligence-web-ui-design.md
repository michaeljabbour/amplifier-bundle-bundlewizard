# Bundlewizard Evolution: Orchestrator Intelligence + Web UI

## Goal

Two additions to the bundlewizard bundle that extend its capabilities without changing its existing pipeline:

1. **Orchestrator Intelligence** — Bundlewizard gains the ability to detect when a custom orchestrator is genuinely needed, adversarially validate that need against Amplifier kernel experts, and generate compliant orchestrator modules as a first-class artifact type alongside its existing bundle YAML generation.

2. **Web UI** — A simple, separate web application (`amplifier-app-bundlewizard-web`) that serves as a friendlier front door to bundlewizard's full capabilities, using the Application Integration Guide's Protocol Boundary Pattern. The CLI and web UI are interchangeable — all intelligence lives in the bundle, not the app.

## Background

The Amplifier ecosystem has well-populated tool (16), hook (13), and provider (11) module types — but only 3 orchestrators, all sequential loops. This is by design: the philosophy is "mechanism vs policy," pushing complexity to tools and hooks while keeping orchestrators simple.

Yet there are legitimate cases where the execution loop shape itself must change — parallel dispatch, multi-provider alternation, phased execution. The DX showcase already envisions research orchestrators like `loop-observer-swarm` and `loop-parallel-exploration` that go beyond sequential loops. Bundlewizard, as the ecosystem's bundle creator, is the natural place to arbitrate this tension: when does a user genuinely need a new orchestrator vs. clever composition on existing ones?

The web UI addresses a simpler problem: the CLI is powerful but intimidating. A browser-based chat interface lets users engage with the wizard's agentic pipeline without terminal complexity.

## Approach

**Unified Pipeline** — Orchestrators become another artifact type in bundlewizard's existing explore → spec → plan → execute → verify → finish pipeline. No new modes, no separate factory. The explore phase gains a dedicated `orchestrator-advisor` agent that applies a kernel-derived litmus test. The web UI is a thin FastAPI + WebSocket app implementing four protocol boundary points. Both additions are architecturally independent — neither depends on the other to ship.

## Architecture

### Orchestrator Intelligence

The existing pipeline gains awareness of orchestrators as a first-class artifact type. A dedicated `orchestrator-advisor` agent (context sink carrying kernel contracts and the litmus test) is consulted during the explore phase. When the advisor confirms a new orchestrator is genuinely needed, the pipeline generates a compliant orchestrator module (Python code + pyproject.toml + tests) alongside the usual bundle YAML. When it's not needed, the advisor recommends hook/tool/bundle composition instead — and that becomes the spec.

### Web UI

A new lightweight application repo (`amplifier-app-bundlewizard-web`) using the Protocol Boundary Pattern. FastAPI backend, WebSocket streaming, simple React frontend. The bundlewizard bundle is the `PreparedBundle` — the web app is just a different front door to the same wizard.

### Key Principle

The web UI has zero knowledge of orchestrators, bundles, or Amplifier internals. It implements four protocol points and delegates everything to the bundlewizard session. All intelligence lives in the bundle, not the app. The CLI and web UI are interchangeable front doors.

## Components

### The Orchestrator Advisor Agent

At the heart of the orchestrator intelligence is a new agent: `orchestrator-advisor`. This agent is a **context sink** — it carries the heavy documentation so the main bundlewizard session stays lean.

**What it carries** (via `@mentions`):
- The full Orchestrator Contract from core's contracts documentation
- The synthesized 12-point litmus test
- The complete catalog of existing orchestrators and their capabilities
- Reference implementations: `loop-basic` as the canonical example
- The showcase orchestrator concepts (observer-swarm, parallel-exploration, perspective-synthesis, iterative-refinement) as design patterns

**Three verdicts** — When consulted during the explore phase, the advisor applies the litmus test and returns:

- **"Compose"** — This can be achieved with hooks + tools on existing orchestrators. Here's how.
- **"Extend"** — An existing orchestrator gets you 80% there with configuration. Here's what to configure.
- **"Create"** — This genuinely requires a new orchestrator. Here's the loop shape it needs and why.

**Adversarial check** — For "Create" verdicts, bundlewizard makes a second delegation to `core:core-expert` (kernel contract validation) and/or `amplifier:amplifier-expert` (ecosystem-level "does this already exist?" checks). Only if both agree does the pipeline proceed to orchestrator generation.

### The Litmus Test

A new orchestrator is required if and only if you need to change the **shape of the execution loop**.

**New orchestrator needed when (any of these):**

| # | Question |
|---|----------|
| 1 | Does it change WHEN the LLM is called? |
| 2 | Does it change HOW MANY TIMES the LLM is called? |
| 3 | Does it change WHICH PROVIDERS drive the loop (structured alternation)? |
| 4 | Does it change WHAT HAPPENS TO RESULTS structurally? |
| 5 | Does it change tool dispatch from sequential to parallel? |
| 6 | Does it add a structured phase before/after the main loop requiring LLM inference? |

**Compose on existing orchestrators when (any of these):**

| # | Question | Mechanism |
|---|----------|-----------|
| 7 | Feedback/validation within an existing loop? | `inject_context` hook |
| 8 | Block/permit operations? | `deny`/`ask_user` hook |
| 9 | Observe, log, or emit metrics? | observation hook |
| 10 | Delegate work to another agent? | `tool-task` (tool layer) |
| 11 | Parallelize within a single capability? | internal tool async |
| 12 | Select between already-mounted providers? | orchestrator config |

### The Pattern Library

When the advisor says "Create," bundlewizard draws from proven loop shapes:

**Pattern 1: Parallel Dispatch** (`loop-parallel`)
Instead of `for each tool_call: execute()`, it does `asyncio.gather(*[execute(tc) for tc in tool_calls])`. Same events, same hook handling, just concurrent. One provider, parallel tools.

**Pattern 2: Multi-Provider Alternation** (`loop-multi-provider`)
Structured turns between providers. Provider A drafts → Provider B critiques → Provider A revises. Selects from the `providers` dict per-turn based on a role schedule. All providers mounted at session init.

**Pattern 3: Plan-Then-Execute** (`loop-phased`)
Two structured phases within a single `execute()` call. Phase 1: one LLM call to decompose the problem (no tools). Phase 2: standard tool-calling loop executing the plan. Loop ends when all plan steps are marked complete.

**Pattern 4: Convergence Loop** (`loop-convergence`)
Fixed-iteration or quality-threshold termination. Runs K passes regardless of tool calls, or until an evaluator function returns "converged."

**Pattern 5: Swarm Coordinator** (`loop-swarm`)
Parent loop manages N concurrent child sessions (spawned via `tool-task`). Fans out work, collects results, synthesizes. Parent's loop shape is novel (aggregator); each child runs standard `loop-streaming`. Parent/child/grandchild lineage tracked via `parent_id`.

Each pattern ships with: the Python implementation, required event emissions, hook result handling, unit tests using `amplifier_core.testing` fixtures, and a companion bundle snippet.

### Web UI Application

The web app is a separate repo: `amplifier-app-bundlewizard-web`.

**Backend** — FastAPI with a single WebSocket endpoint. At startup, loads the bundlewizard bundle as a `PreparedBundle` singleton. Per connection, creates a session with four web-aware protocol implementations:

- **WebApprovalSystem** — Sends approval requests as JSON over WebSocket. Frontend renders a dialog. User clicks approve/deny. Response resolves an `asyncio.Future` that unblocks the session.
- **WebDisplaySystem** — Forwards structured display messages to the frontend for rendering.
- **WebStreamingHook** — Registered ephemerally per-connection. Forwards all session events (`content_delta`, `tool:pre`, `tool:post`, `thinking:delta`) to WebSocket. Unregistered in `finally` block on disconnect.
- **Spawn Capability** — A `spawn_session()` function registered on the coordinator. When bundlewizard spawns sub-agents, child sessions inherit web-aware `ApprovalSystem` and `DisplaySystem`.

**Session pattern**: Pattern C (Singleton) — one wizard session per browser connection, continuous context accumulation through the full pipeline.

**Frontend** — Simple React chat interface. Token streaming, tool call visualization, approval dialogs, and a progress indicator showing pipeline phase (explore → spec → plan → execute → verify → finish). WebSocket in, rendered output out.

## Bundle Structure Changes

All changes to the bundlewizard bundle are purely additive:

```
amplifier-bundle-bundlewizard/        (existing repo)
├── agents/
│   └── orchestrator-advisor.md       ← NEW (context sink agent)
├── context/
│   └── orchestrator/                 ← NEW directory
│       ├── kernel-contracts.md       ← NEW (agent @mentions only)
│       ├── litmus-test.md            ← NEW (agent @mentions only)
│       └── catalog.md               ← NEW (agent @mentions only)
└── behaviors/
    └── bundlewizard.yaml             ← MODIFY: +1 line in agents.include
```

- `bundle.md` — unchanged
- `context/instructions.md` — optional 4-line addition pointing to the advisor
- Root context stays at ≤2 files — bundlewizard's own discipline preserved
- Heavy orchestrator content loads ONLY when the advisor agent is spawned

## Web UI Application Structure

```
amplifier-app-bundlewizard-web/        ← Separate repo
├── pyproject.toml                     ← Web app Python package
├── src/
│   └── app_bundlewizard_web/
│       ├── main.py                    ← FastAPI entry point
│       ├── ws_handler.py             ← WebSocket + Protocol Boundary
│       └── session_bridge.py         ← Loads bundlewizard bundle at runtime
└── frontend/
    └── src/                           ← React chat interface
```

The bundle is unaware of the web app. The web app references the bundle.

## Data Flow

### Orchestrator Intelligence Flow

```
User describes need
  → Explorer detects orchestrator-adjacent language
  → Delegates to orchestrator-advisor (context sink)
  → Advisor applies 12-point litmus test
  → Returns verdict: Compose | Extend | Create
  → [If Create] Second delegation to core-expert / amplifier-expert
  → [If both agree] Pipeline continues with artifact_type: orchestrator_module
  → Spec includes loop shape, events, termination logic
  → Plan includes Python scaffold + companion bundle YAML
  → Execute generates via convergence loop (generate → critique → refine)
  → Verify checks protocol compliance
  → Finish packages standalone repo scaffold + companion bundle
```

### Web UI Flow

```
Browser connects via WebSocket
  → FastAPI creates session from PreparedBundle
  → Registers WebApprovalSystem, WebDisplaySystem, WebStreamingHook
  → Registers spawn_session() for sub-agent inheritance
  → User messages forwarded to session
  → Session events stream back over WebSocket
  → Approval requests render as frontend dialogs
  → User approve/deny resolves asyncio.Future
  → Session continues
```

## Pipeline Adaptation

Each phase gains orchestrator awareness as a branch, not a replacement:

**Explore**: Detects orchestrator-adjacent language. Delegates to `orchestrator-advisor`. Advisor applies litmus test, returns verdict. For "Create" verdicts, adversarial second check. Explore output now includes an `artifact_type` field: `bundle`, `behavior`, `application_bundle`, or `orchestrator_module`.

**Spec**: For orchestrator modules, the spec includes: loop shape description, required events, termination logic, provider interaction pattern, and naming convention (`amplifier-module-loop-{name}`).

**Plan**: For orchestrator modules, the plan includes tasks for: Python module scaffold, the orchestrator class implementing the Orchestrator protocol, `mount()` function, required event emissions, hook result handling, unit tests, and the companion bundle YAML. Two artifacts, one plan.

**Execute**: The convergence loop (generate → critique → refine → evaluate) works the same, but the generator produces Python code instead of (or alongside) YAML. The critic validates against kernel contracts. The evaluator checks protocol compliance.

**Verify**: Three-level evaluation applies identically. For orchestrators: structural validation (implements protocol?), functional validation (emits required events?), integration validation (companion bundle loads it?).

**Finish**: Packages the orchestrator module repo + companion bundle. Creates the repo scaffold with proper naming (`amplifier-module-loop-{name}`), pyproject.toml entry points, and README.

## Expert-Validated Corrections

Four corrections from Amplifier kernel and ecosystem experts are incorporated into this design:

1. **No separate behavior** — The `orchestrator-advisor` agent wires into the existing `behaviors/bundlewizard.yaml` (one line added to `agents.include`). A separate behavior is premature abstraction — extract later only if other bundles need to compose it.

2. **Heavy context stays lazy** — Three new context files under `context/orchestrator/` are `@mentioned` only by the advisor agent. Root sessions get a 4-line pointer. Bundlewizard's ≤2-root-files rule preserved.

3. **Generated orchestrators are standalone repo scaffolds** — If an orchestrator passes the litmus test, it's by definition generally useful. The execute phase produces TWO artifacts: an `amplifier-module-loop-{name}/` repo scaffold AND the bundle YAML referencing it via git URL. Not a `modules/` subdirectory inside the bundle.

4. **Web UI needs Spawn Capability** — The fourth protocol boundary point. Bundlewizard spawns ~10 sub-agents through its pipeline. Without a registered `spawn_session()` function that passes web-aware protocol implementations to child sessions, sub-agents bypass the web UI entirely.

## Error Handling

**Advisor disagreement**: If the adversarial check (core-expert / amplifier-expert) disagrees with a "Create" verdict, the advisor's reasoning and the expert's objection are both surfaced to the user for a decision. The wizard doesn't silently override.

**Generated code fails protocol compliance**: The verify phase catches this. The convergence loop re-enters critique → refine until compliance passes or max iterations are reached. On max iterations, the wizard surfaces what's failing and asks for guidance.

**WebSocket disconnect**: The `WebStreamingHook` is unregistered in a `finally` block. The session itself can persist (Pattern C) — reconnection resumes streaming from current state.

**Bundle load failure at startup**: The web app fails fast with a clear error if the bundlewizard bundle can't be loaded as a `PreparedBundle`. No graceful degradation — the bundle IS the app.

## Testing Strategy

**Orchestrator advisor**: Scenario-based tests with known correct answers:
- "I want parallel web searches" → Compose (internal tool parallelism)
- "I want three LLMs to debate" → Create (multi-provider alternation)
- "I want approval before dangerous tools" → Compose (deny/ask_user hooks)

**Generated orchestrators**: Every generated orchestrator uses `amplifier_core.testing` fixtures — `MockProvider`, `MockTool`, `EventRecorder`, `TestCoordinator`. Checks: Does it implement the protocol? Does it emit all required events? Does the companion bundle load it?

**Web UI**: Test the four protocol classes in isolation (WebApprovalSystem resolves futures correctly, WebStreamingHook forwards events). Test the WebSocket handler with a mock session. Amplifier doesn't need to be running for UI tests.

## What We're NOT Building

- No kernel changes. Everything composes on existing contracts.
- No hot-swapping providers outside the mounted dict. The orchestrator selects from what's mounted.
- No runtime orchestrator switching within a session. One orchestrator per session stays.
- No WASM/gRPC module transport. Python modules only.
- No multi-user web UI in v1. Pattern C (singleton session). Multi-user (Pattern B) is a future evolution.

## Open Questions

1. Should the pattern library be extensible (community-contributed patterns) or curated (only bundlewizard-maintained)?
2. What's the right granularity for the orchestrator catalog — auto-discover from MODULES.md or manually maintained in the advisor's context?
3. For the web UI frontend, fork `amplifier-web` or build from scratch? Fork is faster; from scratch is simpler if we only need chat + approvals.
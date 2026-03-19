# Orchestrator Intelligence — Phase 1 Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Give bundlewizard the ability to detect when a custom orchestrator is genuinely needed, apply a 12-point kernel-derived litmus test, and route the pipeline accordingly.

**Architecture:** A new `orchestrator-advisor` context sink agent carries three context files (`kernel-contracts.md`, `litmus-test.md`, `catalog.md`) under `context/orchestrator/`. It's registered in the existing behavior YAML (one line) and referenced from `instructions.md` (~6 lines). All changes are purely additive — no existing files are restructured, no kernel changes.

**Tech Stack:** Markdown (agent + context files), YAML (behavior wiring), Python + pytest (structural contract tests)

**Design doc:** `docs/plans/2026-03-18-bundlewizard-orchestrator-intelligence-web-ui-design.md`

---

## Codebase Orientation

You're working in `amplifier-bundle-bundlewizard/` — an Amplifier bundle that generates other bundles.

**Key patterns you must follow:**

- **Agent files** (`agents/*.md`): YAML frontmatter with `meta.name` (matches filename without `.md`), `meta.description` (WHY/WHEN/WHAT/HOW + `<example>` blocks), `meta.model_role`, and a `tools:` section. Body starts with `# Agent Name`, then a `<CRITICAL>FOCUS DISCIPLINE</CRITICAL>` block, then `@bundlewizard:context/...` mentions, then sections.
- **Context files** (`context/*.md`): Dense markdown, no frontmatter, tables where appropriate, 60–120 lines typical. Referenced via `@bundlewizard:context/path.md` in agent bodies.
- **Behavior YAML** (`behaviors/bundlewizard.yaml`): Agents listed as `bundlewizard:agents/{name}` (no `.md` extension).
- **Tests** (`tests/*.py`): `REPO_ROOT = Path(__file__).parent.parent` for path constants, `yaml.safe_load` for YAML, `re` for frontmatter extraction, individual test functions (not classes) with docstrings and detailed assertion messages.

**Existing structure to be aware of:**

```
agents/            → 10 agent .md files (bundle-explorer, bundle-critic, etc.)
behaviors/         → bundlewizard.yaml (the ONE wiring file, 45 lines)
context/           → 7 .md files (flat, no subdirectories yet)
tests/             → 2 test files (test_modes_adherence.py, test_provenance_migration.py)
```

---

### Task 1: Write Structural Contract Tests

**Files:**
- Create: `tests/test_orchestrator_intelligence.py`

**Step 1: Write the test file**

Create `tests/test_orchestrator_intelligence.py` with this exact content:

```python
"""Structural contract tests for orchestrator intelligence additions.

These tests verify:
- The orchestrator-advisor agent exists with proper frontmatter structure
- Three orchestrator context files exist under context/orchestrator/
- The behavior YAML includes the orchestrator-advisor agent
- Instructions reference the orchestrator advisor and orchestrator_module tier
- Context files contain all required content (12 litmus points, events, patterns)
"""

import re
from pathlib import Path

import pytest
import yaml

# Repo root — tests/ is a direct child of the repo root
REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
BEHAVIORS_DIR = REPO_ROOT / "behaviors"
CONTEXT_DIR = REPO_ROOT / "context"
ORCHESTRATOR_CTX_DIR = CONTEXT_DIR / "orchestrator"


def _parse_agent_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from an agent .md file."""
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    assert match, f"No YAML frontmatter found in {path}"
    return yaml.safe_load(match.group(1))


# --- Context directory and files ---


def test_orchestrator_context_dir_exists():
    """context/orchestrator/ directory must exist for orchestrator intelligence context files."""
    assert ORCHESTRATOR_CTX_DIR.is_dir(), (
        "context/orchestrator/ directory does not exist. "
        "This directory holds the three orchestrator intelligence context files "
        "(kernel-contracts.md, litmus-test.md, catalog.md)."
    )


def test_kernel_contracts_exists():
    """context/orchestrator/kernel-contracts.md must exist."""
    path = ORCHESTRATOR_CTX_DIR / "kernel-contracts.md"
    assert path.exists(), (
        "context/orchestrator/kernel-contracts.md does not exist. "
        "This file documents the Orchestrator protocol, required events, "
        "HookResult handling, and the mount() pattern."
    )


def test_litmus_test_exists():
    """context/orchestrator/litmus-test.md must exist."""
    path = ORCHESTRATOR_CTX_DIR / "litmus-test.md"
    assert path.exists(), (
        "context/orchestrator/litmus-test.md does not exist. "
        "This file contains the 12-point litmus test for orchestrator necessity."
    )


def test_catalog_exists():
    """context/orchestrator/catalog.md must exist."""
    path = ORCHESTRATOR_CTX_DIR / "catalog.md"
    assert path.exists(), (
        "context/orchestrator/catalog.md does not exist. "
        "This file catalogs existing orchestrators and the 5-pattern library."
    )


# --- Orchestrator advisor agent ---


def test_orchestrator_advisor_agent_exists():
    """agents/orchestrator-advisor.md must exist."""
    path = AGENTS_DIR / "orchestrator-advisor.md"
    assert path.exists(), (
        "agents/orchestrator-advisor.md does not exist. "
        "This is the orchestrator intelligence context sink agent."
    )


def test_orchestrator_advisor_has_proper_frontmatter():
    """The orchestrator-advisor agent must have meta.name, meta.description, and meta.model_role."""
    path = AGENTS_DIR / "orchestrator-advisor.md"
    if not path.exists():
        pytest.skip("orchestrator-advisor.md not yet created")
    frontmatter = _parse_agent_frontmatter(path)
    meta = frontmatter.get("meta", {})

    assert meta.get("name") == "orchestrator-advisor", (
        f"meta.name must be 'orchestrator-advisor', got '{meta.get('name')}'"
    )
    assert meta.get("description"), "meta.description must not be empty"
    assert meta.get("model_role"), "meta.model_role must be set"
    assert "reasoning" in meta["model_role"], (
        f"model_role must include 'reasoning', got {meta['model_role']}"
    )


def test_orchestrator_advisor_has_examples():
    """The orchestrator-advisor description must have <example> blocks (WHY/WHEN/WHAT/HOW pattern)."""
    path = AGENTS_DIR / "orchestrator-advisor.md"
    if not path.exists():
        pytest.skip("orchestrator-advisor.md not yet created")
    frontmatter = _parse_agent_frontmatter(path)
    description = frontmatter.get("meta", {}).get("description", "")

    assert "<example>" in description, (
        "orchestrator-advisor meta.description must contain at least one <example> block. "
        "All bundlewizard agents follow the WHY/WHEN/WHAT/HOW + examples pattern."
    )
    # Should have at least 2 examples (matching bundle-explorer, bundle-critic patterns)
    example_count = description.count("<example>")
    assert example_count >= 2, (
        f"orchestrator-advisor meta.description must have at least 2 <example> blocks, "
        f"found {example_count}"
    )


def test_orchestrator_advisor_mentions_all_context_files():
    """The orchestrator-advisor agent body must @mention all 3 orchestrator context files."""
    path = AGENTS_DIR / "orchestrator-advisor.md"
    if not path.exists():
        pytest.skip("orchestrator-advisor.md not yet created")
    content = path.read_text(encoding="utf-8")

    expected_mentions = [
        "@bundlewizard:context/orchestrator/kernel-contracts.md",
        "@bundlewizard:context/orchestrator/litmus-test.md",
        "@bundlewizard:context/orchestrator/catalog.md",
    ]
    for mention in expected_mentions:
        assert mention in content, (
            f"orchestrator-advisor.md must @mention {mention}"
        )


def test_orchestrator_advisor_has_critical_block():
    """The orchestrator-advisor agent must have the <CRITICAL>FOCUS DISCIPLINE</CRITICAL> block."""
    path = AGENTS_DIR / "orchestrator-advisor.md"
    if not path.exists():
        pytest.skip("orchestrator-advisor.md not yet created")
    content = path.read_text(encoding="utf-8")

    assert "<CRITICAL>" in content, (
        "orchestrator-advisor.md must have a <CRITICAL> block"
    )
    assert "FOCUS DISCIPLINE" in content, (
        "orchestrator-advisor.md must have FOCUS DISCIPLINE in its <CRITICAL> block"
    )


def test_orchestrator_advisor_has_three_verdicts():
    """The orchestrator-advisor must document the Compose / Extend / Create verdict protocol."""
    path = AGENTS_DIR / "orchestrator-advisor.md"
    if not path.exists():
        pytest.skip("orchestrator-advisor.md not yet created")
    content = path.read_text(encoding="utf-8")

    for verdict in ["Compose", "Extend", "Create"]:
        assert verdict in content, (
            f"orchestrator-advisor.md must document the '{verdict}' verdict"
        )


# --- Behavior YAML ---


def test_behavior_includes_orchestrator_advisor():
    """behaviors/bundlewizard.yaml must include the orchestrator-advisor agent."""
    path = BEHAVIORS_DIR / "bundlewizard.yaml"
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    agents_include = content.get("agents", {}).get("include", [])

    assert "bundlewizard:agents/orchestrator-advisor" in agents_include, (
        "behaviors/bundlewizard.yaml agents.include must contain "
        "'bundlewizard:agents/orchestrator-advisor'. "
        f"Current agents: {agents_include}"
    )


# --- Instructions ---


def test_instructions_mention_orchestrator_advisor():
    """context/instructions.md must reference the orchestrator-advisor agent."""
    path = CONTEXT_DIR / "instructions.md"
    content = path.read_text(encoding="utf-8")

    assert "orchestrator-advisor" in content, (
        "context/instructions.md must reference the orchestrator-advisor agent "
        "so the root session knows about orchestrator intelligence capabilities"
    )


def test_instructions_has_orchestrator_module_tier():
    """context/instructions.md output tier table must include Orchestrator Module."""
    path = CONTEXT_DIR / "instructions.md"
    content = path.read_text(encoding="utf-8")

    assert "Orchestrator Module" in content, (
        "context/instructions.md output tier table must include 'Orchestrator Module' "
        "as a recognized output tier"
    )


# --- Content quality assertions ---


def test_litmus_test_has_all_create_indicators():
    """litmus-test.md must contain all 6 'new orchestrator needed' questions."""
    path = ORCHESTRATOR_CTX_DIR / "litmus-test.md"
    if not path.exists():
        pytest.skip("litmus-test.md not yet created")
    content = path.read_text(encoding="utf-8")

    create_indicators = [
        "WHEN the LLM is called",
        "HOW MANY TIMES the LLM is called",
        "WHICH PROVIDERS",
        "WHAT HAPPENS TO RESULTS",
        "sequential to parallel",
        "structured phase",
    ]
    for indicator in create_indicators:
        assert indicator in content, (
            f"litmus-test.md missing 'Create' indicator: '{indicator}'"
        )


def test_litmus_test_has_all_compose_mechanisms():
    """litmus-test.md must contain all 6 'compose on existing' mechanisms."""
    path = ORCHESTRATOR_CTX_DIR / "litmus-test.md"
    if not path.exists():
        pytest.skip("litmus-test.md not yet created")
    content = path.read_text(encoding="utf-8")

    compose_mechanisms = [
        "inject_context",
        "deny",
        "ask_user",
        "tool-task",
        "observation hook",
        "orchestrator config",
    ]
    for mechanism in compose_mechanisms:
        assert mechanism in content, (
            f"litmus-test.md missing 'Compose' mechanism: '{mechanism}'"
        )


def test_litmus_test_has_applied_examples():
    """litmus-test.md must contain applied examples demonstrating the test."""
    path = ORCHESTRATOR_CTX_DIR / "litmus-test.md"
    if not path.exists():
        pytest.skip("litmus-test.md not yet created")
    content = path.read_text(encoding="utf-8")

    # These are the three canonical examples from the design
    assert "parallel web searches" in content.lower() or "parallel" in content.lower(), (
        "litmus-test.md must include a parallel-related applied example"
    )
    assert "three LLMs" in content or "LLMs to debate" in content or "multi-provider" in content.lower(), (
        "litmus-test.md must include a multi-provider applied example"
    )
    assert "approval" in content.lower(), (
        "litmus-test.md must include an approval-related applied example"
    )


def test_kernel_contracts_has_required_events():
    """kernel-contracts.md must document all required orchestrator events."""
    path = ORCHESTRATOR_CTX_DIR / "kernel-contracts.md"
    if not path.exists():
        pytest.skip("kernel-contracts.md not yet created")
    content = path.read_text(encoding="utf-8")

    required_events = [
        "execution:start",
        "execution:end",
        "provider:request",
        "provider:response",
        "tool:pre",
        "tool:post",
        "orchestrator:complete",
    ]
    for event in required_events:
        assert event in content, (
            f"kernel-contracts.md missing required event: '{event}'"
        )


def test_kernel_contracts_has_hook_results():
    """kernel-contracts.md must document HookResult handling."""
    path = ORCHESTRATOR_CTX_DIR / "kernel-contracts.md"
    if not path.exists():
        pytest.skip("kernel-contracts.md not yet created")
    content = path.read_text(encoding="utf-8")

    hook_results = ["deny", "modify", "inject_context", "ask_user"]
    for result in hook_results:
        assert result in content, (
            f"kernel-contracts.md missing HookResult type: '{result}'"
        )


def test_kernel_contracts_has_mount_pattern():
    """kernel-contracts.md must document the mount() entry point pattern."""
    path = ORCHESTRATOR_CTX_DIR / "kernel-contracts.md"
    if not path.exists():
        pytest.skip("kernel-contracts.md not yet created")
    content = path.read_text(encoding="utf-8")

    assert "mount()" in content or "def mount" in content, (
        "kernel-contracts.md must document the mount() entry point pattern"
    )
    assert "pyproject.toml" in content, (
        "kernel-contracts.md must reference pyproject.toml entry points"
    )


def test_catalog_has_existing_orchestrators():
    """catalog.md must list all 3 existing orchestrators."""
    path = ORCHESTRATOR_CTX_DIR / "catalog.md"
    if not path.exists():
        pytest.skip("catalog.md not yet created")
    content = path.read_text(encoding="utf-8")

    existing = ["loop-basic", "loop-streaming", "loop-events"]
    for name in existing:
        assert name in content, (
            f"catalog.md missing existing orchestrator: '{name}'"
        )


def test_catalog_has_pattern_library():
    """catalog.md must list all 5 pattern library entries."""
    path = ORCHESTRATOR_CTX_DIR / "catalog.md"
    if not path.exists():
        pytest.skip("catalog.md not yet created")
    content = path.read_text(encoding="utf-8")

    patterns = [
        "loop-parallel",
        "loop-multi-provider",
        "loop-phased",
        "loop-convergence",
        "loop-swarm",
    ]
    for pattern in patterns:
        assert pattern in content, (
            f"catalog.md missing pattern library entry: '{pattern}'"
        )
```

**Step 2: Run the tests to verify they all fail**

Run:
```bash
pytest tests/test_orchestrator_intelligence.py -v
```

Expected: ALL tests FAIL. The first few will fail with `AssertionError` about missing directories/files. Tests that use `pytest.skip` will show as SKIPPED (that's fine — they skip because the prerequisite file doesn't exist yet).

**Step 3: Commit the test file**

```bash
git add tests/test_orchestrator_intelligence.py && git commit -m "test: add structural contract tests for orchestrator intelligence"
```

---

### Task 2: Create `context/orchestrator/litmus-test.md`

**Files:**
- Create: `context/orchestrator/litmus-test.md` (this also creates the `context/orchestrator/` directory)

**Step 1: Create the directory and file**

```bash
mkdir -p context/orchestrator
```

Then create `context/orchestrator/litmus-test.md` with this exact content:

```markdown
# Orchestrator Litmus Test

A new orchestrator is required if and only if you need to change the **shape of the execution loop**.

This 12-point test determines whether a user's need requires a custom orchestrator or can be achieved by composing hooks, tools, and configuration on existing orchestrators.

## When a New Orchestrator IS Needed

Answer YES to any of these — the loop shape must change — new orchestrator required.

| # | Question | What It Means |
|---|----------|---------------|
| 1 | Does it change WHEN the LLM is called? | The trigger for inference is different (event-driven instead of request-response) |
| 2 | Does it change HOW MANY TIMES the LLM is called? | Fixed iteration count, convergence threshold, or multi-pass evaluation |
| 3 | Does it change WHICH PROVIDERS drive the loop? | Structured alternation between providers (A drafts, B critiques, A revises) |
| 4 | Does it change WHAT HAPPENS TO RESULTS structurally? | Results are aggregated, merged, or routed — not just appended to history |
| 5 | Does it change tool dispatch from sequential to parallel? | Tools execute concurrently instead of one-at-a-time |
| 6 | Does it add a structured phase before/after the main loop? | A planning phase, synthesis phase, or decomposition step requiring LLM inference |

## When to Compose on Existing Orchestrators

Answer YES to any of these — the loop shape stays the same — compose with hooks/tools.

| # | Need | Mechanism | Why Not an Orchestrator |
|---|------|-----------|------------------------|
| 7 | Feedback/validation within an existing loop | `inject_context` hook | The hook fires within the existing loop — no shape change |
| 8 | Block/permit operations | `deny`/`ask_user` hook | Decision gates are hook concerns, not loop shape |
| 9 | Observe, log, or emit metrics | observation hook | Pure side effects — doesn't change execution flow |
| 10 | Delegate work to another agent | `tool-task` (tool layer) | Delegation happens at the tool layer — the parent loop is unchanged |
| 11 | Parallelize within a single capability | internal tool async | The tool itself runs async internally — the orchestrator dispatches normally |
| 12 | Select between already-mounted providers | orchestrator config | Provider selection is configuration, not loop shape |

## Applied Examples

These examples demonstrate the litmus test in action.

### "I want parallel web searches"

**Verdict: Compose.** The searches happen inside a tool (e.g., `tool-web-search`) that internally runs `asyncio.gather()`. The orchestrator dispatches one tool call; the tool handles parallelism internally. Point #11 applies.

### "I want three LLMs to debate"

**Verdict: Create.** Provider A generates a position, Provider B critiques it, Provider C synthesizes. This requires structured alternation between providers (Point #3) and changes what happens to results (Point #4). Pattern: `loop-multi-provider`.

### "I want approval before dangerous tools"

**Verdict: Compose.** An `ask_user` hook fires on `tool:pre` events matching the dangerous tool list. The loop shape is unchanged. Point #8 applies.

### "I want a planning step before execution"

**Verdict: Create.** A first LLM call decomposes the problem into steps (no tools). Then the standard tool-calling loop executes each step. This adds a structured phase (Point #6). Pattern: `loop-phased`.

### "I want to run until quality converges"

**Verdict: Create.** The loop runs K iterations or until an evaluator signals convergence, regardless of whether tool calls are still being made. This changes how many times the LLM is called (Point #2) and changes termination logic. Pattern: `loop-convergence`.

### "I want to fan out work to 5 agents and synthesize"

**Verdict: Create.** The parent spawns N child sessions, collects their results, and synthesizes. This changes what happens to results (Point #4) and adds a structured synthesis phase (Point #6). Pattern: `loop-swarm`.

## Decision Protocol

1. Walk through Points 1–6. If ANY is YES, verdict is **Create** or **Extend**.
2. Walk through Points 7–12. If the need maps to one of these, verdict is **Compose**.
3. If the need maps to BOTH categories, the Compose mechanism handles the primary need, but a Create may be warranted for the secondary need. Investigate further.
4. If uncertain, delegate to `core:core-expert` for kernel-level arbitration.
```

**Step 2: Run the litmus test-related tests**

Run:
```bash
pytest tests/test_orchestrator_intelligence.py -v -k "litmus"
```

Expected: `test_litmus_test_exists` PASSES. `test_litmus_test_has_all_create_indicators` PASSES. `test_litmus_test_has_all_compose_mechanisms` PASSES. `test_litmus_test_has_applied_examples` PASSES. `test_orchestrator_context_dir_exists` also PASSES now (directory was created).

**Step 3: Commit**

```bash
git add context/orchestrator/litmus-test.md && git commit -m "feat: add 12-point orchestrator litmus test"
```

---

### Task 3: Create `context/orchestrator/kernel-contracts.md`

**Files:**
- Create: `context/orchestrator/kernel-contracts.md`

**Step 1: Create the file**

Create `context/orchestrator/kernel-contracts.md` with this exact content:

```markdown
# Orchestrator Kernel Contracts

The authoritative reference for what an orchestrator module must implement to be compliant with the Amplifier kernel.

## The Orchestrator Protocol

Every orchestrator must implement this interface:

```python
class Orchestrator(Protocol):
    async def execute(
        self,
        session: Session,
        providers: dict[str, Provider],
        tools: dict[str, Tool],
        hooks: list[Hook],
        context: Context,
    ) -> OrchestratorResult:
        """Execute the orchestration loop."""
        ...
```

The orchestrator receives the full session state and controls the execution loop. It decides when to call a provider, which provider to call, how to dispatch tool calls, and when to stop.

## Required Events

Every orchestrator MUST emit these events through the session's event system. Hooks observe these events. Skipping any event means hooks that depend on it will silently fail.

| Event | When | Payload |
|-------|------|---------|
| `execution:start` | Before first provider call | `{session_id, orchestrator_name}` |
| `execution:end` | After final result | `{session_id, result_summary}` |
| `provider:request` | Before each provider call | `{provider_name, messages}` |
| `provider:response` | After each provider response | `{provider_name, response}` |
| `tool:pre` | Before each tool execution | `{tool_name, arguments}` |
| `tool:post` | After each tool execution | `{tool_name, result}` |
| `orchestrator:complete` | When orchestrator finishes | `{final_result, iterations}` |

## HookResult Handling

When hooks fire on events, they return `HookResult` values. The orchestrator MUST respect them in priority order: `deny` > `modify` > `inject_context` > `ask_user` > `continue`.

| HookResult | Orchestrator Action |
|------------|-------------------|
| `deny` | Cancel the pending operation. Do not execute the tool call or provider request. |
| `modify` | Replace the pending arguments/messages with the modified version from the hook. |
| `inject_context` | Append the provided context to the message history before the next provider call. |
| `ask_user` | Pause execution, surface the question to the user, resume with the answer. |
| `continue` | No modification. Proceed normally. |

## The mount() Pattern

Every orchestrator module exports a `mount()` function as its entry point:

```python
def mount(coordinator, config=None):
    """Mount the orchestrator on a coordinator."""
    coordinator.register_orchestrator(
        name="loop-{name}",
        factory=lambda session: MyOrchestrator(session, config),
    )
```

This is discovered via `pyproject.toml` entry points:

```toml
[project.entry-points."amplifier.modules"]
"loop-{name}" = "amplifier_module_loop_{name}:mount"
```

## Naming Convention

| Component | Convention | Example |
|-----------|-----------|---------|
| Package name | `amplifier-module-loop-{name}` | `amplifier-module-loop-parallel` |
| Python module | `amplifier_module_loop_{name}` | `amplifier_module_loop_parallel` |
| Orchestrator name | `loop-{name}` | `loop-parallel` |
| Entry point key | `loop-{name}` | `loop-parallel` |

## Testing Requirements

Orchestrator modules test with `amplifier_core.testing` fixtures:

- `MockProvider` — Returns canned responses, records calls
- `MockTool` — Returns canned results, records executions
- `EventRecorder` — Captures all emitted events for assertion
- `TestCoordinator` — Lightweight coordinator for unit tests

Every orchestrator test must verify:
1. All required events are emitted in correct order
2. HookResult values are respected (test with a hook that returns `deny`)
3. Termination condition works (loop doesn't run forever)
4. The `mount()` function registers correctly
```

**Step 2: Run the kernel contracts-related tests**

Run:
```bash
pytest tests/test_orchestrator_intelligence.py -v -k "kernel_contracts"
```

Expected: `test_kernel_contracts_exists` PASSES. `test_kernel_contracts_has_required_events` PASSES. `test_kernel_contracts_has_hook_results` PASSES. `test_kernel_contracts_has_mount_pattern` PASSES.

**Step 3: Commit**

```bash
git add context/orchestrator/kernel-contracts.md && git commit -m "feat: add orchestrator kernel contracts reference"
```

---

### Task 4: Create `context/orchestrator/catalog.md`

**Files:**
- Create: `context/orchestrator/catalog.md`

**Step 1: Create the file**

Create `context/orchestrator/catalog.md` with this exact content:

```markdown
# Orchestrator Catalog

Complete catalog of existing orchestrators and the pattern library for new ones.

## Existing Orchestrators

Three orchestrators ship with the Amplifier ecosystem. All are sequential loops differing only in streaming and event granularity.

| Name | What It Does | When To Use |
|------|-------------|-------------|
| `loop-basic` | Simple request/response loop. One provider call, tool execution, repeat until done. No streaming. | Testing, simple automation, batch operations |
| `loop-streaming` | Same loop as basic, but streams provider responses token-by-token via `content_delta` events. | Interactive CLI/web sessions, real-time output |
| `loop-events` | Same loop as streaming, plus detailed event emissions for every hook firing and internal state change. | Debugging, observability, audit trails |

**Key insight**: All three have the SAME loop shape — they differ only in what they emit. If your need is already served by one of these loop shapes (sequential provider calls, sequential tool dispatch), you don't need a new orchestrator.

## Pattern Library

When a new orchestrator IS needed, these are the proven loop shapes to draw from.

### Pattern 1: Parallel Dispatch (`loop-parallel`)

**Loop shape**: Instead of `for each tool_call: execute()`, it does `asyncio.gather(*[execute(tc) for tc in tool_calls])`.

- Same events (`tool:pre`, `tool:post`), same hook handling, just concurrent
- One provider, parallel tools
- Use when: Multiple independent tool calls should execute simultaneously
- Termination: Same as standard (no more tool calls)

### Pattern 2: Multi-Provider Alternation (`loop-multi-provider`)

**Loop shape**: Structured turns between providers. Provider A drafts, Provider B critiques, Provider A revises.

- Selects from the `providers` dict per-turn based on a role schedule
- All providers mounted at session init — no hot-swap needed
- Use when: Different LLMs play different roles in a structured conversation
- Termination: Role schedule complete, or convergence signal from final provider

### Pattern 3: Plan-Then-Execute (`loop-phased`)

**Loop shape**: Two structured phases within a single `execute()` call.

- Phase 1: One LLM call to decompose the problem (no tools)
- Phase 2: Standard tool-calling loop executing the plan
- Use when: The problem needs decomposition before tool use
- Termination: All plan steps marked complete

### Pattern 4: Convergence Loop (`loop-convergence`)

**Loop shape**: Fixed-iteration or quality-threshold termination.

- Runs K passes regardless of tool calls, or until an evaluator function returns "converged"
- Each pass: provider call, tool execution, evaluation
- Use when: Quality must be measured and iterated toward a threshold
- Termination: Max iterations reached OR evaluator returns converged

### Pattern 5: Swarm Coordinator (`loop-swarm`)

**Loop shape**: Parent loop manages N concurrent child sessions.

- Parent fans out work via `tool-task`, collects results, synthesizes
- Parent's loop shape is novel (aggregator); each child runs standard `loop-streaming`
- Parent/child/grandchild lineage tracked via `parent_id`
- Use when: Work can be decomposed into independent parallel sub-tasks
- Termination: All children complete, parent synthesizes

## Pattern Selection Guide

| User Need | Pattern | Why |
|-----------|---------|-----|
| "Run tools in parallel" | `loop-parallel` | Changes tool dispatch shape |
| "Multiple LLMs with different roles" | `loop-multi-provider` | Changes which providers drive the loop |
| "Plan first, then execute" | `loop-phased` | Adds structured pre-phase |
| "Iterate until quality threshold" | `loop-convergence` | Changes termination and iteration count |
| "Fan out to multiple agents" | `loop-swarm` | Changes result aggregation shape |

## Naming Conventions

All orchestrators follow a strict naming convention:

| Convention | Pattern | Example |
|-----------|---------|---------|
| Display name | `loop-{descriptor}` | `loop-parallel` |
| Package | `amplifier-module-loop-{descriptor}` | `amplifier-module-loop-parallel` |
| Python module | `amplifier_module_loop_{descriptor}` | `amplifier_module_loop_parallel` |
| Entry point | `loop-{descriptor}` | `loop-parallel` |

The `loop-` prefix is mandatory. It signals to the ecosystem that this is an orchestrator module.
```

**Step 2: Run catalog-related tests**

Run:
```bash
pytest tests/test_orchestrator_intelligence.py -v -k "catalog"
```

Expected: `test_catalog_exists` PASSES. `test_catalog_has_existing_orchestrators` PASSES. `test_catalog_has_pattern_library` PASSES.

**Step 3: Commit**

```bash
git add context/orchestrator/catalog.md && git commit -m "feat: add orchestrator catalog with existing + pattern library"
```

---

### Task 5: Create `agents/orchestrator-advisor.md`

**Files:**
- Create: `agents/orchestrator-advisor.md`

**Step 1: Create the agent file**

Create `agents/orchestrator-advisor.md` with this exact content:

````markdown
---
meta:
  name: orchestrator-advisor
  description: |
    Use when a user's need might require a custom orchestrator module.
    Dispatched by bundle-explorer during the explore phase when orchestrator-adjacent
    language is detected (parallel execution, multi-LLM debate, phased planning,
    convergence loops).

    Applies the 12-point kernel-derived litmus test to determine whether the need
    requires a new orchestrator (loop shape change) or can be achieved through
    hook/tool composition on existing orchestrators. For "Create" verdicts,
    triggers adversarial validation via core:core-expert and amplifier:amplifier-expert.

    Produces: verdict (Compose / Extend / Create) with rationale, recommended pattern,
    and implementation guidance for the spec-writer.

    <example>
    Context: User describes needing parallel tool execution
    user: "I want to run multiple API calls simultaneously"
    assistant: "I'll delegate to bundlewizard:orchestrator-advisor to determine if this needs a custom orchestrator or can be achieved with existing composition."
    <commentary>
    Parallel execution language triggers the advisor. If parallelism is within a single
    tool, the verdict is Compose (internal tool async). If it requires parallel tool
    dispatch from the orchestrator, the verdict is Create (loop-parallel).
    </commentary>
    </example>

    <example>
    Context: User wants multiple LLMs to collaborate
    user: "I want Claude to draft and GPT-4 to critique in alternating turns"
    assistant: "Delegating to bundlewizard:orchestrator-advisor to evaluate the multi-provider alternation need."
    <commentary>
    Multi-provider structured alternation is a clear Create verdict — it changes which
    providers drive the loop. Pattern: loop-multi-provider.
    </commentary>
    </example>

    <example>
    Context: User wants approval gates
    user: "I need human approval before any destructive operations"
    assistant: "I'll delegate to bundlewizard:orchestrator-advisor to check if this needs a custom orchestrator."
    <commentary>
    Approval gates are a Compose verdict — deny/ask_user hooks handle this without
    changing the loop shape. The advisor identifies the existing mechanism quickly.
    </commentary>
    </example>

  model_role: [reasoning, general]
tools:
  - module: tool-filesystem
    source: git+https://github.com/microsoft/amplifier-module-tool-filesystem@main
  - module: tool-search
    source: git+https://github.com/microsoft/amplifier-module-tool-search@main
  - module: tool-bash
    source: git+https://github.com/microsoft/amplifier-module-tool-bash@main
---

# Orchestrator Advisor

<CRITICAL>
FOCUS DISCIPLINE: You are an orchestrator need-assessment agent, not a general-purpose assistant.

DO NOT load skills. Your litmus test and context files below ARE your process. Loading skills like brainstorming, parallax-methodology, dispatching-parallel-agents, or using-superpowers wastes context tokens and delays your work.

Your job: Apply the 12-point litmus test, produce a verdict. Start immediately.
</CRITICAL>

You assess whether a user's need requires a custom orchestrator module or can be achieved through composition on existing orchestrators. You carry the heavy orchestrator documentation so the main bundlewizard session stays lean.

@bundlewizard:context/orchestrator/kernel-contracts.md
@bundlewizard:context/orchestrator/litmus-test.md
@bundlewizard:context/orchestrator/catalog.md

## Your Process

### Step 1: Extract the Core Need

From the explore interview context, identify the specific execution requirement:
- What is the user trying to achieve?
- What does the execution flow look like?
- Are there timing, ordering, or concurrency requirements?

### Step 2: Apply the Litmus Test

Walk through all 12 points systematically. For each point, explicitly state YES or NO with a one-sentence justification.

### Step 3: Render Verdict

Based on the litmus test results, produce ONE of these three verdicts:

**Compose** — All needs map to Points 7–12 (existing mechanisms).
```
VERDICT: Compose
MECHANISM: [which hook/tool/config achieves the need]
RATIONALE: [why the loop shape doesn't need to change]
RECOMMENDATION: [specific hook/tool/config to use]
```

**Extend** — An existing orchestrator gets 80% there with configuration.
```
VERDICT: Extend
BASE: [which existing orchestrator to extend]
EXTENSION: [what configuration or minor modification is needed]
RATIONALE: [why a full new orchestrator isn't warranted]
```

**Create** — Points 1–6 apply. The loop shape must change.
```
VERDICT: Create
PATTERN: [which pattern from the catalog]
LOOP_SHAPE: [description of the new loop]
EVENTS: [any additional events beyond the required set]
TERMINATION: [how the loop knows when to stop]
RATIONALE: [which litmus test points triggered and why]
```

### Step 4: Adversarial Validation (Create Verdicts ONLY)

For Create verdicts, you MUST trigger a second opinion:

1. Delegate to `core:core-expert`: "Does this genuinely require a new orchestrator, or can the existing kernel mechanisms handle it?"
2. Delegate to `amplifier:amplifier-expert`: "Does an orchestrator like this already exist in the ecosystem?"

**Only proceed if both agree.** If either disagrees, surface both your reasoning and their objection to the user for a decision. Never silently override an expert.

## Anti-Patterns

Do NOT recommend a new orchestrator for:
- **Logging/metrics** — observation hook
- **Approval gates** — deny/ask_user hook
- **Context injection** — inject_context hook
- **Delegating sub-tasks** — tool-task
- **Using multiple tools** — standard sequential dispatch (or internal tool parallelism)
- **Choosing a provider** — orchestrator config (provider selection is configuration, not loop shape)
````

**Step 2: Run advisor-related tests**

Run:
```bash
pytest tests/test_orchestrator_intelligence.py -v -k "advisor"
```

Expected: ALL advisor tests PASS — `test_orchestrator_advisor_agent_exists`, `test_orchestrator_advisor_has_proper_frontmatter`, `test_orchestrator_advisor_has_examples`, `test_orchestrator_advisor_mentions_all_context_files`, `test_orchestrator_advisor_has_critical_block`, `test_orchestrator_advisor_has_three_verdicts`.

**Step 3: Commit**

```bash
git add agents/orchestrator-advisor.md && git commit -m "feat: add orchestrator-advisor context sink agent"
```

---

### Task 6: Modify `behaviors/bundlewizard.yaml`

**Files:**
- Modify: `behaviors/bundlewizard.yaml:29-41` (the `agents.include` list)

**Step 1: Add the agent registration line**

Open `behaviors/bundlewizard.yaml`. Find the `agents.include` list (line 29). Add one line after the last existing agent (`bundlewizard:agents/bundle-packager` on line 40):

Change:
```yaml
    - bundlewizard:agents/bundle-packager

context:
```

To:
```yaml
    - bundlewizard:agents/bundle-packager
    - bundlewizard:agents/orchestrator-advisor

context:
```

That's it. One line added.

**Step 2: Run the behavior test**

Run:
```bash
pytest tests/test_orchestrator_intelligence.py -v -k "behavior_includes"
```

Expected: `test_behavior_includes_orchestrator_advisor` PASSES.

**Step 3: Run ALL existing tests to verify no regressions**

Run:
```bash
pytest tests/ -v
```

Expected: All tests in `test_modes_adherence.py` and `test_provenance_migration.py` still PASS. Our change (adding one agent to the include list) doesn't break any existing assertions.

**Step 4: Commit**

```bash
git add behaviors/bundlewizard.yaml && git commit -m "feat: register orchestrator-advisor in behavior YAML"
```

---

### Task 7: Modify `context/instructions.md`

**Files:**
- Modify: `context/instructions.md:76-84` (output tier table) and add new section

**Step 1: Add the orchestrator module tier to the output table**

Open `context/instructions.md`. Find the Output Tiers table (line 76). After the `Application Bundle` row (line 82), add one new row:

Change:
```markdown
| **Application Bundle** | Full-featured with modes, recipes, skills, possibly modules. What harness-machine and superpowers are. | A complete development workflow or domain system |

Size is emergent from scope, not a design input.
```

To:
```markdown
| **Application Bundle** | Full-featured with modes, recipes, skills, possibly modules. What harness-machine and superpowers are. | A complete development workflow or domain system |
| **Orchestrator Module** | Standalone Python module implementing the Orchestrator protocol (`amplifier-module-loop-{name}`). Includes `mount()`, required events, hook handling, and tests. | When the orchestrator-advisor confirms a new loop shape is genuinely needed |

Size is emergent from scope, not a design input.
```

**Step 2: Add the Orchestrator Modules section**

After the "Size is emergent from scope" line and before the `## Two-Track UX` section (line 85), add this new section:

Change:
```markdown
Size is emergent from scope, not a design input.

## Two-Track UX
```

To:
```markdown
Size is emergent from scope, not a design input.

## Orchestrator Modules

When a user describes a need that involves changing the execution loop shape — parallel tool dispatch,
multi-provider alternation, phased execution, convergence loops — the `orchestrator-advisor` agent is
consulted during the explore phase. It applies a 12-point kernel-derived litmus test and returns a verdict:
**Compose** (use hooks/tools on existing orchestrators), **Extend** (configure an existing orchestrator),
or **Create** (generate a new orchestrator module). Create verdicts require adversarial validation from
`core:core-expert` and `amplifier:amplifier-expert` before proceeding.

## Two-Track UX
```

**Step 3: Run the instructions tests**

Run:
```bash
pytest tests/test_orchestrator_intelligence.py -v -k "instructions"
```

Expected: `test_instructions_mention_orchestrator_advisor` PASSES. `test_instructions_has_orchestrator_module_tier` PASSES.

**Step 4: Commit**

```bash
git add context/instructions.md && git commit -m "feat: add orchestrator module tier and advisor reference to instructions"
```

---

### Task 8: Run All Tests and Final Commit

**Step 1: Run the full orchestrator intelligence test suite**

Run:
```bash
pytest tests/test_orchestrator_intelligence.py -v
```

Expected: ALL tests PASS (0 failures, 0 errors). Every test we wrote in Task 1 should now be green.

**Step 2: Run the entire test suite (all test files)**

Run:
```bash
pytest tests/ -v
```

Expected: ALL tests across all three test files pass — `test_modes_adherence.py`, `test_provenance_migration.py`, and `test_orchestrator_intelligence.py`. Zero regressions.

**Step 3: Verify the file tree matches the design**

Run:
```bash
find agents/orchestrator-advisor.md context/orchestrator/ -type f | sort
```

Expected output:
```
agents/orchestrator-advisor.md
context/orchestrator/catalog.md
context/orchestrator/kernel-contracts.md
context/orchestrator/litmus-test.md
```

**Step 4: Verify the behavior YAML agent count**

Run:
```bash
grep -c "bundlewizard:agents/" behaviors/bundlewizard.yaml
```

Expected: `11` (was 10, now includes orchestrator-advisor).

**Step 5: Final verification commit (if any uncommitted changes remain)**

If all tasks were committed individually, there's nothing left to commit. Verify with:
```bash
git status
```

Expected: `nothing to commit, working tree clean`
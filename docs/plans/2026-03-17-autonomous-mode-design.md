# Autonomous Mode Design: Replacing bundle-bot

## Goal

Replace the "bundle-bot" god-mode in amplifier-bundle-bundlewizard with a proper autonomous operating profile that leverages the existing modes infrastructure from amplifier-bundle-modes. The current bundle-bot mode (`default_action: allow`, all tools safe) conflates three independent concerns -- gate friction, human checkpoints, and tool policy overrides -- into a single mode that destroys the carefully designed pipeline. The new design separates these concerns using existing mechanisms plus a small (~10 line) generic addition to the modes infrastructure.

## Background

### The Problem with bundle-bot

When Amplifier needs a capability or bundle it doesn't have (e.g., can't find in MODULES.md), it spawns bundlewizard to autonomously create what's needed. The current approach uses a "bundle-bot" mode with `default_action: allow` and all tools marked safe. This is a god-mode that:

- Destroys the 7-stage pipeline by allowing any tool in any mode
- Removes architectural constraints that encode expert discipline
- Conflates "no human watching" with "no rules apply"

### The Meaning of Bundle Wizard

"Bundle Wizard" is intentionally a double meaning:

1. **Wizard as guided flow (computing sense)** -- It acts like a classic setup wizard. It walks the system step-by-step through creating, configuring, and refining a bundle using structured stages and transitions.

2. **Wizard as mastery (craft sense)** -- It embodies expert-level capability. It doesn't just guide, it applies best practices, patterns, and judgment to produce high-quality bundles with minimal friction.

What that means in practice:

- It guides the process through defined steps (via modes + transitions).
- It elevates the outcome by applying intelligent defaults, patterns, and refinements.
- It automates when appropriate, but stays within normal mode semantics (no global overrides).
- It feels like a flow to the user, but behaves like a skilled builder under the hood.

**One-liner:** The Bundle Wizard is both a guided flow and an expert builder: it walks you through the process while quietly doing the work like a master.

The god-mode bundle-bot violated both meanings -- it destroyed the guided flow (no pipeline structure enforced) and undermined the mastery (by removing architectural constraints that encode the expert's discipline). A master craftsperson who "skips all the rules" isn't a master -- they're reckless.

The autonomous design preserves both: same pipeline modes, same transition graph, same quality gates. The wizard works unsupervised but with the same discipline. Autonomous means the wizard is trusted to apply both without human checkpoints -- not that either is optional.

### Use Case

When Amplifier itself detects it needs a capability or bundle it doesn't have, it spawns bundlewizard in "yolo mode" to autonomously create what's needed. This is machine-initiated, but may still involve the user (Amplifier might interview the user while operating bundlewizard autonomously). "Yolo mode" means "no human gates" -- not "no humans."

The autonomous profile must work on both tracks:

- **Recipe track** -- running `bundle-development-cycle.yaml` with auto-advancing approval gates
- **Interactive/agent track** -- mode-driven pipeline with frictionless transitions

## Approach

### Core Insight: Autonomous as a Session Property

"Yolo mode" isn't a mode -- it's a session-scoped modifier. A mode says "what phase are you in." Autonomous says "who's driving." These are orthogonal.

The tool tier semantics in autonomous mode:

| Tier | Behavior | Rationale |
|------|----------|-----------|
| `safe` | Unchanged (no restriction) | Already unrestricted |
| `warn` | Promoted to `safe` | No human to warn -- the two-call friction is pure waste |
| `confirm` | Promoted to `safe` | No human to approve |
| `block` | **STAYS BLOCKED** | Architectural quality, not human friction |

This means `block` encodes architectural intent, not human trust. In execute mode, `write_file` is blocked because the orchestrator pattern requires delegation -- true whether a human or Amplifier is driving. In explore mode, writes are blocked because exploration shouldn't produce artifacts -- also true regardless of who's driving.

## Architecture

Two layers of change across two repos.

```
amplifier-bundle-modes (mechanism)     amplifier-bundle-bundlewizard (policy)
================================       =====================================
hooks-mode.py                          behaviors/bundlewizard-autonomous.yaml
  + autonomous config flag               (new file, parallel to bundlewizard.yaml)
  + warn/confirm bypass in cascade
  + banner annotation                  context/autonomous-protocol.md
                                         (new file, behavioral override)
tool-mode: NO CHANGES
  (gate_policy: "auto" already exists)  modes/bundle-bot.md
                                         (DELETED -- replaced by composition)
```

### How the Caller Chooses

- **Interactive:** compose `bundlewizard:behaviors/bundlewizard` (the default via `bundle.md`)
- **Autonomous:** compose `bundlewizard:behaviors/bundlewizard-autonomous` (the caller explicitly selects this when spawning)

## Components

### Layer 1: amplifier-bundle-modes Changes (~10 lines)

A small, generic addition to `hooks-mode`: an `autonomous` config flag.

**Change 1: `ModeHooks.__init__`** -- accept the flag:

```python
self.autonomous: bool = config.get("autonomous", False) if config else False
```

Default `False` -- zero behavior change for existing consumers.

**Change 2: `handle_tool_pre` cascade** -- two insertions after the existing `safe_tools` check and before `warn_tools`/`confirm_tools` branches:

```python
if self.autonomous and tool_name in mode.confirm_tools:
    return HookResult(action="continue")  # No human to confirm

if self.autonomous and tool_name in mode.warn_tools:
    return HookResult(action="continue")  # No human to warn
```

The `block_tools` check fires BEFORE these -- architectural blocks are never touched.

**Change 3: `handle_provider_request` banner** -- append when autonomous:

```python
banner = f"MODE ACTIVE: {name}"
if self.autonomous:
    banner += " (AUTONOMOUS)"
```

**Change 4: `mount()`** -- pass `autonomous` from hook config to `ModeHooks` constructor. One line.

**What doesn't change:** `ModeDefinition` dataclass, `ModeDiscovery`, `parse_mode_file()`, the `block` path in the cascade, the `infrastructure_tools` bypass, `reset_warnings()`. `tool-mode` needs zero changes -- `gate_policy: "auto"` already exists.

### Layer 2: amplifier-bundle-bundlewizard Changes

Three changes. No mode files touched.

#### New: `behaviors/bundlewizard-autonomous.yaml`

Structurally identical to existing `behaviors/bundlewizard.yaml` with three differences:

```yaml
hooks:
  - module: hooks-mode
    config:
      search_paths: ["@bundlewizard:modes"]
      autonomous: true          # promotes warn/confirm -> safe

tools:
  - module: tool-mode
    config:
      gate_policy: "auto"       # no transition friction

context:
  include:
    - bundlewizard:context/instructions.md
    - bundlewizard:context/philosophy.md
    - bundlewizard:context/autonomous-protocol.md  # behavioral override
```

Same agents, same skills, same search_paths for modes. Same 10 agents registered.

#### New: `context/autonomous-protocol.md`

A single context file (~30-40 lines) loaded only by the autonomous behavior. Contains:

- "You are in autonomous mode" declaration
- Override instructions: when a mode says "ask the user" or "confirm with user," proceed directly using triggering context
- Auto-transition rule: transition immediately at golden-path completion, don't pause
- Machine quality gates that remain enforced (convergence loop, structural validation, all three evaluation levels)
- Audit trail requirements: the `generated_by:` metadata block with `triggered_by`, `trigger_reason`, and convergence summary -- migrated from the deleted bundle-bot mode
- Return-to-process contract: what to return to the calling session (what was built, capability provided, how to compose, convergence summary)
- The wizard identity anchor:

> "Autonomous mode is the wizard working unsupervised, not the wizard abandoning its craft. The pipeline is the wizard's process. The quality gates are the wizard's standards. Autonomous means the wizard is trusted to apply both without human checkpoints -- not that either is optional."

#### Delete: `modes/bundle-bot.md`

The god mode is replaced by composition.

**What stays unchanged:** all 7 pipeline mode files, all 10 agents, all 5 recipes, both skills, all other context files, the interactive `behaviors/bundlewizard.yaml`, `bundle.md`.

## Data Flow

### Interactive Profile (existing, unchanged)

```
User -> bundlewizard (behaviors/bundlewizard.yaml)
  -> hooks-mode (autonomous: false)
     -> warn tools: two-call friction
     -> confirm tools: approval routing
     -> block tools: deny
  -> tool-mode (gate_policy: "warn")
     -> transition friction with user confirmation
```

### Autonomous Profile (new)

```
Amplifier -> bundlewizard (behaviors/bundlewizard-autonomous.yaml)
  -> hooks-mode (autonomous: true)
     -> warn tools: continue (promoted to safe)
     -> confirm tools: continue (promoted to safe)
     -> block tools: deny (UNCHANGED)
  -> tool-mode (gate_policy: "auto")
     -> frictionless transitions
  -> autonomous-protocol.md
     -> "ask the user" overrides
     -> auto-transition at golden-path completion
     -> audit trail generation
```

### Recipe Track (autonomous)

```
Amplifier -> bundle-development-cycle.yaml
  context:
    auto_approve: true
  -> Stage 1 (explore + spec) -> auto-approve gate
  -> Stage 2 (plan)           -> auto-approve gate
  -> Stage 3 (execute + verify)-> auto-approve gate
  -> Convergence loop runs normally (not an approval gate)
  -> Evaluator scores all three levels
  -> Critic reviews with context_depth: "none"
```

## Preserved vs Removed

### Preserved (machine quality -- the wizard's discipline)

- Convergence loop (generate -> critique -> refine -> evaluate)
- Structural validation (Level 1)
- Philosophical validation (Level 2)
- Functional validation (Level 3)
- Architectural blocks (execute delegates, debug diagnoses, explore doesn't write)
- Transition graph enforcement (`allowed_transitions`)
- `allow_clear` enforcement
- Version stamping and audit trail

### Removed (human friction -- only relevant with a human supervisor)

- `warn` tier two-call friction (promoted to safe)
- `confirm` tier approval prompts (promoted to safe)
- `gate_policy: "warn"` transition friction (set to auto)
- "Ask the user" / "Confirm with user" behavioral instructions (overridden by autonomous-protocol.md)
- Recipe approval gates (auto-approved with logging)

## Recipe Auto-Approve

The `bundle-development-cycle.yaml` has 3 approval gates. In autonomous mode these need to auto-advance.

When executing the recipe autonomously, the caller passes `auto_approve: true` in the context:

```yaml
context:
  auto_approve: true
  bundle_description: "a code review bundle"
  output_dir: "/path/to/output"
```

Each approval gate conditionally skips based on this variable. This is a recipe-runner concern, not a bundlewizard-specific hack -- any staged recipe could use this pattern.

**What this does NOT bypass:**

- The convergence loop still runs (it's a `while` recipe, not an approval gate)
- The evaluator still scores all three levels
- The critic still reviews with `context_depth: "none"`
- Structural validation still gates the pipeline

**Audit difference:** When `auto_approve: true`, the recipe logs each auto-advanced gate in the convergence summary. This replaces the human decision record with a machine decision record.

**Dependency:** Requires recipe engine support for `auto_approve` or equivalent conditional approval skipping.

## Error Handling

Error handling is unchanged from the existing pipeline. The autonomous profile inherits all existing error paths:

- **Mode transition violations** -- `allowed_transitions` enforcement denies invalid transitions identically in both profiles
- **Blocked tool invocations** -- `block` tier returns `deny` with the same error message regardless of autonomous flag
- **Convergence failures** -- The convergence loop's retry/fail logic is in the recipe/agent layer, untouched by this design
- **Evaluation failures** -- All three evaluation levels gate the pipeline identically

The one new error path: if the recipe engine does not support `auto_approve`, the recipe track falls back to requiring a non-staged recipe variant (see Open Questions).

## Philosophy Alignment

| Principle | How it applies |
|-----------|---------------|
| Mechanism, not policy | `autonomous` flag is mechanism (how tiers are interpreted). Mode files are policy (what goes in which tier). |
| Composition, not configuration | Swap behavior YAML to change profile. Don't toggle flags at runtime. |
| Ruthless simplicity | ~10 lines in hooks-mode. One context file. One behavior YAML. Delete one mode. |
| The center stays still | Modes infrastructure gets a small generic mechanism. Bundlewizard's edges move freely. |
| Two-implementation rule | bundlewizard + harness-machine + future factory-core consumers. Satisfied. |
| Bricks and studs | Mode files are bricks -- untouched. The autonomous behavior is a different stud arrangement of the same bricks. |
| Security by construction | `block` is never overridable. Architectural constraints are invariants, not permissions. |

## Testing Strategy

### amplifier-bundle-modes tests (mechanism)

Extend `test_hooks.py`:

- `autonomous: false` (default): cascade behavior unchanged (existing tests still pass)
- `autonomous: true`: `warn` tools return `continue` (no warn-once cycle)
- `autonomous: true`: `confirm` tools return `continue` (no approval routing)
- `autonomous: true`: `block` tools still return `deny` (the critical invariant)
- `autonomous: true`: `safe` tools still return `continue` (unchanged)
- `autonomous: true`: `infrastructure_tools` still bypass (unchanged)
- Banner injection includes `(AUTONOMOUS)` when flag is set

No new tests needed in `test_tool_mode.py` -- `gate_policy: "auto"` is already tested.

### amplifier-bundle-bundlewizard tests

Extend `test_modes_adherence.py`:

- Verify `modes/bundle-bot.md` does NOT exist (regression guard)
- Verify all 7 pipeline mode files still have expected `allowed_transitions` and `allow_clear` values
- Verify `behaviors/bundlewizard-autonomous.yaml` exists and sets `gate_policy: "auto"` and `autonomous: true`
- Verify `context/autonomous-protocol.md` exists and contains audit trail requirements
- Verify autonomous behavior registers same 10 agents as interactive behavior (no agent drift)

### Out of scope for this layer

- Whether the LLM follows `autonomous-protocol.md` (behavioral, not structural)
- End-to-end autonomous bundle generation (integration testing, separate scope)
- Recipe auto-approve (depends on recipe engine support, covered separately)

## Open Questions

1. **Recipe engine `auto_approve` support** -- Does the recipe engine already support conditional approval skipping, or does it need enhancement? If not available, the recipe track in autonomous mode would need a workaround (e.g., a non-staged version of the development cycle recipe that uses flat steps instead of approval gates).

2. **Caller spawn mechanism** -- When Amplifier spawns bundlewizard as a sub-session, it composes the autonomous behavior via `bundlewizard:behaviors/bundlewizard-autonomous`. Confirm the spawn API supports behavior selection at composition time.

3. **Should `context/instructions.md` reference the autonomous profile?** -- Instinct says no. The autonomous behavior is composed, not chosen interactively. Keep it out of the interactive instructions.

## Migration Path

Changes are additive with one deletion. Dependency order: modes repo first (provides the mechanism), then bundlewizard repo (consumes it).

1. **amplifier-bundle-modes**: Add `autonomous` config support to hooks-mode. Push first (dependency).
2. **amplifier-bundle-bundlewizard**: Add autonomous behavior YAML, add `autonomous-protocol.md`, delete `bundle-bot.md`. Push second.

No breaking changes -- existing interactive behavior is completely untouched. Default `autonomous: false` means zero behavior change for current consumers.

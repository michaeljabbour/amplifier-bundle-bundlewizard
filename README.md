# Bundlewizard

**The Bundle Wizard is both a guided flow and an expert builder:** it walks you through the process while quietly doing the work like a master.

Bundlewizard generates new Amplifier bundles and upgrades existing ones. You describe what you need — or point it at a bundle to improve — and it interviews you, designs the composition, generates artifacts through an adversarial convergence loop, and delivers a ready-to-use bundle.

It works two ways:
- **As a guided flow** (the computing sense of "wizard"): a step-by-step process through explore, spec, plan, execute, verify, and finish
- **As an expert builder** (the craft sense of "wizard"): applying best practices, patterns, and quality gates automatically under the hood

## Install

```bash
# Register bundlewizard with Amplifier
amplifier bundle add git+https://github.com/michaeljabbour/amplifier-bundle-bundlewizard@main

# Set as your active bundle
amplifier bundle use bundlewizard

# Start a session
amplifier
```

Bundlewizard includes `amplifier-foundation` automatically. No additional dependencies needed.

To switch back to your normal bundle when done:

```bash
amplifier bundle use superpowers  # or whatever your default is
```

## Quick Start

### Create a new bundle

```
You: I need a bundle that helps with code review — linting, style checks, PR summaries.
```

Bundlewizard interviews you about scope, checks the ecosystem for existing bundles, designs the composition, and builds it through the convergence pipeline.

### Improve an existing bundle

```
You: Improve my bundle at ~/dev/my-bundle
```

Bundlewizard audits the bundle against three quality levels, presents findings, and fixes what you choose.

### Upgrade an older generated bundle

```
You: Upgrade ~/dev/amplifier-bundle-project-memory
```

Bundlewizard detects older provenance metadata (`bundlewizard:` legacy format), migrates it to the canonical `generated_by` schema, and runs targeted improvements. You can also just point it at an older bundle — it will auto-detect the legacy format and offer to upgrade.

### Go autonomous (yolo mode)

Add `"yolo"`, `"go autonomous"`, or `"run it all"` to any request:

```
You: Build me a bundle for managing git worktrees, yolo
```

Exploration still happens first (bundlewizard needs to understand what you want). After that, the full pipeline runs without human checkpoints. Machine quality gates remain fully enforced — you skip human approval, not quality.

### Amplifier-as-caller

Amplifier itself can spawn bundlewizard when it detects a missing capability. In this mode, Amplifier performs the explore phase directly (it already knows what it needs), then launches the autonomous continuation recipe. The user sees: *"I needed X capability, so I built it. Here's what I created: [summary]. Continuing."*

### Audit only (no changes)

```
You: Audit the bundle at ~/dev/my-bundle — just tell me what's wrong, don't change anything.
```

Returns a structured findings report with scores and priority-ordered issues.

## Two Tracks

**Modes are the steering wheel. Recipes are cruise control.**

| Track | How | Best For |
|-------|-----|----------|
| **Interactive** (default) | Navigate modes manually: `/bundle-explore` through `/bundle-finish` | Hands-on control at each step |
| **Autonomous** (opt-in) | `/bundle-explore` detects autonomy request and launches the full pipeline automatically | End-to-end generation without checkpoints |

Both tracks produce the same output. The autonomous track just removes the human checkpoints after exploration is complete. If the autonomous run hits trouble (failed verification, unresolved requirements, convergence stall), it offers a takeover point via `STATE.yaml` rather than forcing one — the caller decides whether to continue, ask the user, or switch to manual steering.

## How It Works

```
EXPLORE ——— interview, audit, ecosystem survey, upgrade detection
   │
   ├── [default] ——→ manual mode pipeline
   │
   └── [yolo] ———→ autonomous continuation recipe
                     │
   ┌─────────────────┘
   v
 SPEC ————— design composition (bundle-spec.md)
   │
   v
 PLAN ————— break into ordered tasks
   │
   v
EXECUTE ——— convergence loop:
   │        ┌─ generate ─> critique ─> refine ─> evaluate ─┐
   │        └──────────────── (until converged) <───────────┘
   │
   v
VERIFY ———— independent three-level verification
   │
   v
FINISH ———— version stamp, git init/branch, deliver
```

The critic always runs with `context_depth="none"` — fresh eyes, no shared context from the generator. The evaluator is independent of both. This adversarial structure catches issues that self-review misses.

## Modes

| Command | Phase | What Happens |
|---------|-------|--------------|
| `/bundle-explore` | Interview | Understand what you need, detect upgrade candidates, route to create/improve/upgrade — or launch autonomous continuation |
| `/bundle-spec` | Design | Compose the bundle specification |
| `/bundle-plan` | Planning | Break spec into implementation tasks |
| `/bundle-execute` | Generation | Convergence loop: generate, critique, refine, evaluate |
| `/bundle-verify` | Verification | Independent evidence that the bundle works |
| `/bundle-finish` | Delivery | Version stamp, git init/branch, deliver |
| `/bundle-debug` | Off-ramp | Diagnose issues at any stage |

Flow: `explore` > `spec` > `plan` > `execute` > `verify` > `finish`. Debug is available from any mode.

## Agents

| Agent | Role | When It Runs |
|-------|------|--------------|
| `bundle-explorer` | Adaptive interview, experience detection, upgrade detection, routing | Every session starts here |
| `bundle-auditor` | Three-level audit of existing bundles | Improve and upgrade paths |
| `ecosystem-scout` | Survey ecosystem for similar bundles and reusable parts | Create path, during interview |
| `bundle-spec-writer` | Design the bundle composition | After interview |
| `bundle-plan-writer` | Break spec into ordered tasks | After spec approval |
| `bundle-generator` | Write bundle artifacts (YAML, markdown, files) | Inside convergence loop |
| `bundle-critic` | Adversarial review with fresh eyes (`context_depth="none"`) | After each generation |
| `bundle-refiner` | Targeted fixes from critic feedback only | When critic says NEEDS CHANGES |
| `bundle-evaluator` | Three-level convergence scoring | After each refinement |
| `bundle-packager` | Version stamp, provenance metadata, git, delivery | Terminal step |

## Recipes

| Recipe | Pattern | Use |
|--------|---------|-----|
| `bundle-autonomous-post-explore.yaml` | Staged, no gates | Autonomous track — launched by explore when yolo requested |
| `bundle-development-cycle.yaml` | Staged, 3 approval gates | Full interactive pipeline with human checkpoints |
| `bundle-audit.yaml` | Flat sequential | Evaluate existing bundle without making changes |
| `bundle-batch-generation.yaml` | Foreach with STATE.yaml | Generate multiple bundles from a target list |
| `bundle-refinement-loop.yaml` | While-loop convergence | Internal — called by other recipes |
| `bundle-single-iteration.yaml` | Sequential 4-step | Internal — called by refinement loop |

### Running recipes directly

```bash
# Full interactive pipeline — create new
amplifier run --bundle bundlewizard \
  "run bundlewizard:recipes/bundle-development-cycle.yaml"

# Full interactive pipeline — improve existing
amplifier run --bundle bundlewizard \
  "run bundlewizard:recipes/bundle-development-cycle.yaml \
  with path='~/dev/my-bundle'"

# Audit only
amplifier run --bundle bundlewizard \
  "run bundlewizard:recipes/bundle-audit.yaml \
  with bundle_path='~/dev/my-bundle'"
```

## Quality System

Every bundle produced by bundlewizard passes a three-level convergence check.

### Level 1: Structural (pass/fail)

All gates must pass or the score is zero.

- Bundle loads (valid YAML frontmatter)
- Agent references resolve (every agent in behavior YAML has a file)
- URI syntax valid (all `source:` URIs match `git+https://...@tag` format)
- No duplicate context (nothing loaded at root AND @mentioned by agents)
- Sources reachable (structurally valid URIs)

### Level 2: Philosophical (scored 0.0-1.0, threshold 0.85)

| Criterion | Weight |
|-----------|--------|
| Thin bundle pattern | 25% |
| Context sink discipline | 25% |
| Agent description quality (WHY/WHEN/WHAT/HOW) | 25% |
| Composition hygiene | 25% |

### Level 3: Functional (scored 0.0-1.0, threshold 0.80)

Does the bundle actually do what it claims? Evaluated by the appropriate domain expert.

**Convergence formula:**

```
converged = (L1 == PASS) AND (L2 >= 0.85) AND (L3 >= 0.80)
```

The generate/critique/refine/evaluate loop runs up to 10 iterations until convergence is met. Best result is always checkpointed.

## Provenance and Upgrade Support

Every machine-generated bundle gets a `generated_by` block in its `bundle.md` frontmatter:

```yaml
bundle:
  generated_by:
    tool: bundlewizard
    version: 0.2.0
    schema_version: 1
    timestamp: 2026-03-18T12:00:00Z
    mode: interactive  # or autonomous
    convergence:
      level_score: 0.92
      critic_verdict: PASS
      tests_passed: 45
      tests_failed: 0
      commits: 3
```

This metadata enables:
- **Traceability** — you can always tell which bundles were machine-generated and what quality bar they met
- **Upgrades** — bundlewizard detects older provenance formats (legacy `bundlewizard:` shape without `generated_by`) and offers to migrate them to the canonical schema
- **Audit trail** — autonomous runs include `triggered_by` and `trigger_reason` fields for full provenance chain

### Upgrade detection

Bundlewizard recognizes older generated bundles automatically:
- Legacy `bundle.bundlewizard` provenance (no `generated_by`, no `schema_version`)
- Older `generated_by` blocks with `schema_version` below current

When detected, upgrade routes through the existing improve flow — not a separate mode stack. The upgrade normalizes provenance metadata and runs targeted improvements based on what changed between versions.

## Takeover Model

When running autonomously, bundlewizard classifies outcomes into three buckets:

1. **Continue autonomously** — normal progress, recoverable feedback, keep going
2. **Pause and offer takeover** — unresolved requirements, repeated stalls, judgment calls needed. Updates `STATE.yaml` with `takeover.status: "paused"` and a recommended re-entry point
3. **Escalate** — broken assumptions, missing source material, contradictions. Updates `STATE.yaml` with `takeover.status: "escalated"` and returns an error

Takeover is **offered, not forced**. If Amplifier is the caller, it can consume the takeover signal and decide next steps without bouncing to the user.

## Output Tiers

Bundlewizard produces three tiers of output depending on scope:

| Tier | What It Is | Example |
|------|-----------|---------|
| **Behavior** | YAML + context + agents, composed via `includes:` | A reusable capability package |
| **Bundle** | Standalone: bundle.md, behaviors, agents, context | A focused tool |
| **Application Bundle** | Full: modes, recipes, skills, possibly modules | A complete workflow system |

Size is emergent from scope, not a design input.

## Skills

Two skills are included for quick reference during sessions:

- **bundle-design** — Composition patterns, common mistakes, tier selection
- **bundle-reference** — Complete reference tables for modes, agents, recipes

```
load_skill(skill_name="bundle-design")
load_skill(skill_name="bundle-reference")
```

## Requirements

- [Amplifier CLI](https://github.com/microsoft/amplifier) installed
- An LLM provider configured (Anthropic, OpenAI, etc.)

## License

MIT

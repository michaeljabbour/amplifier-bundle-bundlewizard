# Bundlewizard

Bundle generation and improvement factory for the Amplifier ecosystem.

Bundlewizard builds bundles. You describe what you want (or point it at an existing bundle to improve), and it interviews you, designs the composition, generates artifacts, reviews them adversarially, refines until quality converges, and delivers a ready-to-use bundle.

## Install

```bash
# Add to your Amplifier registry
amplifier bundle add git+https://github.com/michaeljabbour/amplifier-bundle-bundlewizard@main

# Set as active bundle
amplifier bundle use bundlewizard

# Start a session
amplifier
```

Bundlewizard includes `amplifier-foundation` automatically. No additional dependencies needed.

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

### Audit only (no changes)

```
You: Audit the bundle at ~/dev/my-bundle — just tell me what's wrong, don't change anything.
```

Returns a structured findings report with scores and priority-ordered issues.

### Go autonomous

Add "yolo", "go autonomous", or "hands-off" to any request and bundlewizard runs the full pipeline without stopping for approval.

```
You: Build me a bundle for managing git worktrees, yolo
```

## Two Tracks

Both tracks produce the same artifact. Modes give you the steering wheel; recipes give you cruise control.

| Track | How | Best For |
|-------|-----|----------|
| **Interactive** (default) | Navigate modes manually: `/bundle-explore` through `/bundle-finish` | Hands-on control at each step |
| **Autonomous** (opt-in) | `/bundle-explore` launches the full pipeline automatically | End-to-end with no gates |

## Modes

| Command | Phase | What Happens |
|---------|-------|--------------|
| `/bundle-explore` | Interview | Understand what you need, route to create or improve |
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
| `bundle-explorer` | Adaptive interview, experience detection, routing | Every session starts here |
| `bundle-auditor` | Three-level audit of existing bundles | Improve path only |
| `ecosystem-scout` | Survey ecosystem for similar bundles and reusable parts | Create path, during interview |
| `bundle-spec-writer` | Design the bundle composition | After interview |
| `bundle-plan-writer` | Break spec into ordered tasks | After spec approval |
| `bundle-generator` | Write bundle artifacts (YAML, markdown, files) | Inside convergence loop |
| `bundle-critic` | Adversarial review with fresh eyes (`context_depth="none"`) | After each generation |
| `bundle-refiner` | Targeted fixes from critic feedback only | When critic says NEEDS CHANGES |
| `bundle-evaluator` | Three-level convergence scoring | After each refinement |
| `bundle-packager` | Version stamp, git, delivery options (merge/PR/keep/discard) | Terminal step |

## Recipes

| Recipe | Pattern | Use |
|--------|---------|-----|
| `bundle-autonomous-post-explore.yaml` | Staged, no gates | Autonomous track (launched by explore) |
| `bundle-development-cycle.yaml` | Staged, 3 approval gates | Full interactive pipeline |
| `bundle-audit.yaml` | Flat sequential | Evaluate existing bundle, no changes |
| `bundle-batch-generation.yaml` | Foreach with STATE.yaml | Generate multiple bundles |
| `bundle-refinement-loop.yaml` | While-loop convergence | Internal (called by other recipes) |
| `bundle-single-iteration.yaml` | Sequential 4-step | Internal (called by refinement loop) |

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

# Batch generation
amplifier run --bundle bundlewizard \
  "run bundlewizard:recipes/bundle-batch-generation.yaml \
  with targets=['code review helper','git worktree manager']"
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

## Output Tiers

Bundlewizard produces three tiers of output depending on scope:

| Tier | What It Is | Example |
|------|-----------|---------|
| **Behavior** | YAML + context + agents, composed via `includes:` | A reusable capability package |
| **Bundle** | Standalone: bundle.md, behaviors, agents, context | A focused tool |
| **Application Bundle** | Full: modes, recipes, skills, possibly modules | A complete workflow system |

Size is emergent from scope, not a design input.

## Provenance Tracking

Every machine-generated bundle gets a `generated_by` block in its `bundle.md`:

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

## How It Works

```
EXPLORE ─── interview, audit, ecosystem survey
   │
   v
 SPEC ───── design composition (bundle-spec.md)
   │
   v
 PLAN ───── break into ordered tasks
   │
   v
EXECUTE ─── convergence loop:
   │        ┌─ generate ─> critique ─> refine ─> evaluate ─┐
   │        └──────────────── (until converged) <───────────┘
   │
   v
VERIFY ──── independent three-level verification
   │
   v
FINISH ──── version stamp, git, deliver
```

The critic always runs with `context_depth="none"` (fresh eyes, no shared context from the generator). The evaluator is independent of both. This adversarial structure catches issues that self-review misses.

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

# Bundlewizard Guide

## What is Bundlewizard?

Bundlewizard is a bundle that builds other bundles. It's a factory — you describe what you want, and bundlewizard designs, generates, reviews, and delivers it.

An **Amplifier bundle** is a package of markdown and YAML files that gives an AI assistant new capabilities. Think of it like a plugin system. Bundlewizard automates the creation and improvement of these plugins.

### What can it do?

1. **Create new bundles** from a description of what you need
2. **Improve existing bundles** by auditing them and fixing issues
3. **Batch-generate** multiple bundles from a target list

### How does it work?

Bundlewizard uses a **factory pipeline**: interview → design → plan → generate → critique → refine → evaluate → deliver. Each step is handled by a specialist agent. The generate/critique/refine/evaluate cycle repeats until quality criteria are met — this is called the **convergence loop**.

---

## Quick Start: Create a New Bundle

### Option A: Interactive (mode-by-mode)

```
You: I want to build a bundle that helps with code review.
```

Bundlewizard detects this is a "create new" request and starts the interview:

1. `/bundle-explore` — Interview: What problem does this solve? What tier? What capabilities?
2. `/bundle-spec` — Design: Produces a bundle-spec.md with the complete composition design
3. `/bundle-plan` — Planning: Breaks the spec into ordered implementation tasks
4. `/bundle-execute` — Generation: Runs the convergence loop (generate → critique → refine → evaluate)
5. `/bundle-verify` — Verification: Independent three-level quality check
6. `/bundle-finish` — Delivery: Version stamp, git init, deliver

You control the pace. Review each step. Move forward when ready.

### Option B: Recipe (automated with checkpoints)

```bash
amplifier run "execute bundlewizard:recipes/bundle-development-cycle.yaml \
  with bundle_description='a bundle that helps with code review' \
  output_dir='~/dev/amplifier-bundle-code-review' \
  path='create'"
```

Same pipeline, but automated. You approve at 3 checkpoints:
1. After the spec is written (is the design right?)
2. After the plan is written (is the task breakdown right?)
3. After verification (does the bundle meet quality criteria?)

Between checkpoints, bundlewizard runs autonomously.

---

## Quick Start: Improve an Existing Bundle

### Option A: Interactive

```
You: Can you review and improve my bundle at ~/dev/my-bundle?
```

Bundlewizard detects the path and runs an audit:

1. `/bundle-explore` — Audit: Reads the whole bundle, runs three-level evaluation, presents findings
2. You choose which improvements to make (all, critical only, add new capabilities)
3. `/bundle-spec` → `/bundle-plan` → `/bundle-execute` → `/bundle-verify` → `/bundle-finish`

### Option B: Recipe

```bash
amplifier run "execute bundlewizard:recipes/bundle-development-cycle.yaml \
  with bundle_description='improve code review bundle' \
  output_dir='~/dev/my-bundle' \
  path='~/dev/my-bundle'"
```

### Option C: Audit only (no changes)

```bash
amplifier run "execute bundlewizard:recipes/bundle-audit.yaml \
  with bundle_path='~/dev/my-bundle'"
```

Returns findings and scores without making any changes.

---

## Two-Track UX: Modes vs Recipes

| Track | How It Works | Best For |
|-------|-------------|----------|
| **Interactive modes** | You navigate manually: `/bundle-explore` → `/bundle-spec` → ... | Hands-on sessions where you want control at each step |
| **Recipe automation** | `bundle-development-cycle.yaml` runs the pipeline with approval gates | End-to-end generation with 3 human checkpoints |

Both tracks use the same agents, same context, same convergence criteria. The only difference is who decides when to advance.

---

## Available Commands

### Mode Shortcuts

| Command | What It Does |
|---------|-------------|
| `/bundle-explore` | Start the interview — understand what to build or improve |
| `/bundle-spec` | Design the bundle composition |
| `/bundle-plan` | Break the spec into implementation tasks |
| `/bundle-execute` | Run the convergence loop (generate → critique → refine → evaluate) |
| `/bundle-verify` | Independent quality verification |
| `/bundle-finish` | Package and deliver |
| `/bundle-debug` | Diagnose issues at any stage |
| `/dangerously-skip-permissions` | Autonomous mode — all approval gates bypassed |

### Recipe Commands

```bash
# Full pipeline (create or improve)
amplifier run "execute bundlewizard:recipes/bundle-development-cycle.yaml \
  with bundle_description='...' output_dir='...' path='create'"

# Standalone audit
amplifier run "execute bundlewizard:recipes/bundle-audit.yaml \
  with bundle_path='...'"

# Batch generation
amplifier run "execute bundlewizard:recipes/bundle-batch-generation.yaml \
  with targets=['...','...'] state_yaml_path='...' output_dir='...'"

# Check pending approvals
amplifier run "list pending approvals"

# Approve a stage
amplifier run "approve recipe session <session-id> stage <stage-name>"
```

---

## Available Agents

| Agent | What It Does | When It Runs |
|-------|-------------|-------------|
| `bundle-explorer` | Interviews you, detects experience level, routes to create/improve | First agent in every session |
| `bundle-auditor` | Deep analysis of existing bundles (improve path only) | During exploration, dispatched by explorer |
| `ecosystem-scout` | Checks if similar bundles exist, finds reusable components | During exploration, dispatched by explorer |
| `bundle-spec-writer` | Designs the bundle composition, produces bundle-spec.md | After interview, in /bundle-spec |
| `bundle-plan-writer` | Creates implementation plan from the spec | After spec approved, in /bundle-plan |
| `bundle-generator` | Writes all bundle artifacts (YAML, markdown, files) | Each iteration in /bundle-execute |
| `bundle-critic` | Adversarial review with fresh eyes (no shared context) | Each iteration in /bundle-execute |
| `bundle-refiner` | Targeted fixes for issues the critic found | Each iteration (when critique says NEEDS CHANGES) |
| `bundle-evaluator` | Three-level convergence scoring | After each iteration + /bundle-verify |
| `bundle-packager` | Version stamp, git, deliver | Terminal step in /bundle-finish |

---

## Available Recipes

| Recipe | What It Does | When to Use |
|--------|-------------|-------------|
| `bundle-development-cycle.yaml` | Full pipeline with 3 approval gates | Create or improve a bundle end-to-end |
| `bundle-refinement-loop.yaml` | Convergence loop (max 10 iterations) | Runs inside the development cycle — not for direct use |
| `bundle-single-iteration.yaml` | One generate/critique/refine/evaluate cycle | Runs inside the refinement loop — not for direct use |
| `bundle-batch-generation.yaml` | Generate multiple bundles from a target list | When you need many bundles at once |
| `bundle-audit.yaml` | Standalone audit with three-level scoring | When you just want to evaluate, not change |

---

## /dangerously-skip-permissions

This mode is for when Amplifier itself needs to build a bundle without human intervention. All approval gates are bypassed — the pipeline runs end-to-end autonomously.

**What stays enforced:**
- The convergence loop (generate → critique → refine → evaluate) — quality is non-negotiable
- Structural validation (Level 1) — a broken bundle is worse than no bundle
- Philosophical validation (Level 2) — pattern violations cause downstream problems
- Version stamping — every machine-generated bundle must be traceable

**What gets skipped:**
- Human approval between stages
- "Does this look right?" checkpoints
- Interview routing questions (context already tells bundlewizard what's needed)
- Experience calibration (Amplifier is always "experienced")

**Audit trail:** Every bundle generated in this mode includes `generated_by.mode: dangerously-skip-permissions` in its frontmatter, plus the session ID and trigger reason.

---

## FAQ

**Q: How long does it take to generate a bundle?**
A: Depends on complexity. A simple behavior (Tier 1) typically converges in 2-3 iterations (a few minutes). A full application bundle (Tier 3) may take 5-8 iterations (10-15 minutes). Batch generation time scales linearly with target count.

**Q: What if the convergence loop gets stuck?**
A: After 10 iterations without convergence, the loop stops and returns the best result achieved so far. Use `/bundle-debug` to diagnose why convergence stalled — usually it means the spec needs revision, not more iterations.

**Q: Can I use bundlewizard to improve bundlewizard?**
A: Yes. Point it at its own bundle and run the improve path. The anti-rationalization rules still apply — it goes through the full convergence loop even on itself.

**Q: What's the difference between the audit recipe and the full development cycle?**
A: The audit recipe (`bundle-audit.yaml`) only evaluates — it reads the bundle, scores it, and reports findings. No changes are made. The development cycle (`bundle-development-cycle.yaml`) with `path` set to an existing bundle does the full improve pipeline: audit → spec → plan → generate → verify → deliver.

**Q: What if I disagree with the critic's findings?**
A: In interactive mode (modes), you have full control — you can override, skip, or redirect at any point. In recipe mode, the DENY option at approval gates lets you provide feedback and iterate. The convergence loop is a quality tool, not a cage.

**Q: Can bundlewizard generate bundles that use Python modules?**
A: Bundlewizard generates the bundle structure (YAML, markdown, file organization). If the bundle needs Python modules, bundlewizard will specify the module requirements in the spec and generate the behavior YAML that mounts them, but the actual Python code would need to be written separately or by a coding agent.

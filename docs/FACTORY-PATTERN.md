# The Factory Pattern

## What is the Factory Pattern?

The factory pattern is a reusable pipeline for generating, reviewing, and delivering artifacts through iterative convergence. It's the architecture shared by bundlewizard (generates bundles) and harness-machine (generates constraint code).

The pattern is domain-agnostic. The pipeline stages, agent slots, convergence loop, two-track UX, and anti-rationalization enforcement are the same regardless of what you're generating. The domain-specific parts (what "quality" means, what artifacts look like, what experts know) are plugged in through agent implementations and convergence criteria.

**Current status:** The pattern lives inside bundlewizard as internal structure. It will be extracted into `amplifier-bundle-factory-core` when both bundlewizard and harness-machine are stable and a third consumer appears.

## Abstract Pipeline Stages

Every factory follows this stage sequence. Domain-specific factories fill each stage with their own agents.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   EXPLORE   │ →  │    SPEC     │ →  │    PLAN     │
│  (interview)│    │  (design)   │    │  (tasks)    │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
   APPROVAL           APPROVAL           APPROVAL
    GATE               GATE               GATE
       │                  │                  │
       ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────┐
│                    EXECUTE                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────┐ │
│  │ GENERATE │→ │ CRITIQUE │→ │  REFINE  │→ │EVAL │ │
│  └──────────┘  └──────────┘  └──────────┘  └──┬──┘ │
│       ▲                                       │     │
│       └───────── not converged ───────────────┘     │
└──────────────────────────┬───────────────────────────┘
                       │ converged
                       ▼
┌─────────────┐    ┌─────────────┐
│   VERIFY    │ →  │   FINISH    │
│ (evidence)  │    │ (deliver)   │
└──────┬──────┘    └─────────────┘
       │
   APPROVAL
    GATE
```

## Abstract Agent Slots

Each factory defines agents that fill these abstract slots:

| Slot | Responsibility | Bundlewizard Agent | Harness-Machine Agent |
|------|---------------|-------------------|----------------------|
| `explorer` | Interview, understand the problem, route | `bundle-explorer` | `environment-analyst` |
| `spec-writer` | Design the solution, produce spec document | `bundle-spec-writer` | `spec-writer` |
| `plan-writer` | Break spec into implementation tasks | `bundle-plan-writer` | `plan-writer` |
| `generator` | Produce artifacts from the plan | `bundle-generator` | `harness-generator` |
| `critic` | Adversarial review (context_depth="none") | `bundle-critic` | `harness-critic` |
| `refiner` | Targeted fixes from critic feedback | `bundle-refiner` | `harness-refiner` |
| `evaluator` | Measure convergence (did we improve?) | `bundle-evaluator` | `harness-evaluator` |
| `packager` | Version stamp, git, deliver | `bundle-packager` | `harness-generator` (dual role) |

Domain-specific factories may add extra agents beyond these core slots (e.g., bundlewizard adds `bundle-auditor` and `ecosystem-scout`; harness-machine adds `environment-analyst`).

## Convergence Loop Protocol

The convergence loop is the core quality mechanism. It's a `while (!converged)` loop over four steps:

```
iteration = 0
best_score = 0
patience_counter = 0

while not converged and iteration < max_iterations:
    iteration += 1

    # 1. Generate (or refine if iteration > 1)
    artifacts = generator.generate(spec, plan, previous_critique)

    # 2. Critique (adversarial, fresh context)
    critique = critic.review(artifacts)  # context_depth="none"

    # 3. Refine (targeted fixes only — no scope creep)
    if critique.needs_changes:
        artifacts = refiner.fix(artifacts, critique)

    # 4. Evaluate (domain-specific scoring)
    score = evaluator.score(artifacts)

    # Checkpoint best
    if score > best_score:
        best_score = score
        checkpoint(artifacts)
        patience_counter = 0
    else:
        patience_counter += 1

    if patience_counter >= patience_limit:
        diagnose("Score stalled for {patience_limit} iterations")

    converged = meets_criteria(score)

# On exit: deliver checkpoint_best (not necessarily last iteration)
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `context_depth="none"` for critic | Fresh eyes catch assumptions the generator shares with the orchestrator |
| Refiner fixes ONLY flagged issues | Scope creep during refinement destroys convergence |
| Evaluate after EVERY refinement | Can't attribute score changes to specific fixes if you batch |
| checkpoint_best, not checkpoint_last | Last iteration might be worse (refinement oscillation) |
| patience_limit | Prevents infinite loops on diminishing returns |
| on_timeout: return_best | 95% quality is better than 0% (pipeline failure) |

### Domain-Specific Convergence Parameters

| Parameter | Bundlewizard | Harness-Machine | Rationale |
|-----------|-------------|----------------|-----------|
| max_iterations | 10 | 60 | Bundles are compositional; constraints are algorithmic |
| patience_limit | 3 | 15 | Bundle issues are usually spec problems, not iteration problems |
| convergence_criteria | 3-level (structural + philosophical + functional) | Legal action rate ≥ target | Different domains, different quality metrics |

## Two-Track UX Infrastructure

Every factory provides two ways to use the pipeline:

| Component | Interactive Track | Recipe Track |
|-----------|------------------|--------------| 
| Stage transitions | User types `/mode-name` | Recipe `stages:` with approval gates |
| Approval points | Implicit (user sees output, decides to continue) | Explicit `approval.required: true` |
| Convergence loop | Mode orchestrates agent delegation | `refinement-loop.yaml` sub-recipe |
| Single iteration | Agent delegation from execute mode | `single-iteration.yaml` sub-recipe |

Both tracks use the SAME agents with the SAME context. The only difference is who decides when to advance to the next stage.

## Anti-Rationalization Enforcement

Every factory has an anti-rationalization table. These are GATES, not guidelines.

The universal anti-rationalization rules (domain-independent):

| Temptation | Rule |
|-----------|------|
| "I'll just write it directly" | No. Use the generator. The critic reviews everything. |
| "The fix is obvious, skip the critic" | No. The critic has fresh context you don't. |
| "This is simple, skip the evaluator" | No. Simple artifacts are under-scrutinized. |
| "I know what the expert would say" | No. Delegate. Experts have authoritative context. |
| "One more fix, then evaluate" | No. Evaluate after every refinement. |

Domain factories ADD to this table with domain-specific temptations.

## Version Stamping

Every artifact produced by a factory gets metadata:

```yaml
generated_by:
  tool: <factory-name>
  version: <factory-version>
  timestamp: <ISO 8601>
  convergence:
    iterations: <N>
    <domain-specific scores>
```

This enables traceability — you can always tell which artifacts were machine-generated and what quality bar they met.

## How to Build a New Domain Factory

If you want to create a factory for a new domain (e.g., generating test suites, API clients, documentation sites):

### Step 1: Define Your Convergence Criteria

What does "done" mean for your domain? Define measurable quality levels.

### Step 2: Fill the Agent Slots

Create domain-specific agents for each abstract slot (explorer, spec-writer, plan-writer, generator, critic, refiner, evaluator, packager).

### Step 3: Create the Recipes

Copy the recipe structure from bundlewizard or harness-machine. Change agent references and prompts. Adjust `max_while_iterations` and convergence parameters.

### Step 4: Create the Modes

One mode per pipeline stage with appropriate tool permissions.

### Step 5: Write the Anti-Rationalization Table

What temptations will agents face in your domain? Document them as gates.

### Step 6: Test the Loop

Run the convergence loop on a simple example. Verify that the critic finds real issues, the refiner fixes them, and the evaluator's scores track improvement.

## Future: amplifier-bundle-factory-core Extraction Plan

When ready, the shared patterns will be extracted into `amplifier-bundle-factory-core`:

**What moves to factory-core:**
- Abstract pipeline stage definitions
- Convergence loop recipe templates
- Two-track UX infrastructure (mode templates + recipe templates)
- Anti-rationalization enforcement patterns
- Version stamping protocol
- STATE.yaml schema for batch generation

**What stays domain-specific:**
- Agent implementations (the actual markdown files)
- Convergence criteria (what "quality" means)
- Context files (domain knowledge)
- Domain-specific modes and their tool permissions

**Extraction trigger:** When a third consumer exists (beyond bundlewizard and harness-machine). Don't extract prematurely — the pattern needs at least two working implementations to know what's truly shared.

**Documented separately at:** `amplifier-bundle-harness-machine/docs/plans/2026-03-16-factory-core-extraction.md`

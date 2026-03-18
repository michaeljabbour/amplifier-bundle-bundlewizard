# Factory Protocol

This document defines the abstract factory pattern used by bundlewizard. It is structured for future extraction into `amplifier-bundle-factory-core` when a second consumer (harness-machine) is ready to share it.

**Current status:** Internal to bundlewizard. Do not depend on this from outside the bundle.

## Abstract Pipeline Stages

Every factory follows this stage sequence. Domain-specific factories fill each stage with their own agents.

| Stage | Abstract Slot | Bundlewizard Agent | Purpose |
|-------|--------------|-------------------|---------|
| Explore | `explorer` | `bundle-explorer` | Understand the problem, interview the user, route to the right path |
| Spec | `spec-writer` | `bundle-spec-writer` | Design the solution, produce a specification document |
| Plan | `plan-writer` | `bundle-plan-writer` | Break the spec into implementation tasks |
| Execute | `generator` | `bundle-generator` | Produce artifacts from the plan |
| Execute | `critic` | `bundle-critic` | Adversarial review of generated artifacts |
| Execute | `refiner` | `bundle-refiner` | Targeted fixes based on critic feedback |
| Execute | `evaluator` | `bundle-evaluator` | Measure convergence (did we improve?) |
| Verify | `evaluator` | `bundle-evaluator` | Final independent verification |
| Finish | `packager` | `bundle-packager` | Version stamp, package, deliver |
| Debug | (none) | (user-directed) | Off-ramp for issues at any stage |


## Architecture Diagram as Visual Contract

Every factory produces an evolving `bundle-architecture.dot` file:

| Stage | DOT Action |
|-------|-----------|
| Explore | Create initial diagram from user requirements |
| Spec | Refine with exact names, relationships, sources |
| Plan | Update if planning changes the architecture |
| Execute | Finalize to match actual generated artifacts |
| Verify | Critic validates artifacts against the diagram |

The diagram serves as a visual contract — a single artifact that everyone can point to and say "this is what we're building." Discrepancies between the diagram and the artifacts are bugs.

The Execute stage contains the **convergence loop**: generator → critic → refiner → evaluator, repeated until convergence criteria are met or patience exhausts.

## Convergence Loop Protocol

```
iteration = 0
best_score = 0
patience_counter = 0

while not converged and iteration < max_iterations:
    iteration += 1
    
    # Generate (or refine if iteration > 1)
    artifacts = generator.generate(spec, plan, previous_critique)
    
    # Critique (adversarial, context_depth="none")
    critique = critic.review(artifacts)
    
    # Refine (targeted fixes only)
    artifacts = refiner.fix(artifacts, critique)
    
    # Evaluate (three-level scoring)
    score = evaluator.score(artifacts)
    
    if score > best_score:
        best_score = score
        checkpoint_best(artifacts)
        patience_counter = 0
    else:
        patience_counter += 1
    
    if patience_counter >= patience_limit:
        diagnose("Score stalled for {patience_limit} iterations")
    
    converged = meets_convergence_criteria(score)

# On exit: deliver best_checkpoint (not necessarily last iteration)
```

### Key discipline:

- **checkpoint_best** after every improvement — never lose progress
- **patience_limit** (default: 3 for bundles) — don't spin forever on diminishing returns
- **On timeout:** deliver checkpoint_best with a note about what didn't converge. 95% is better than nothing.
- **Never skip the critic** — even for "obvious" fixes. The critic sees what you can't.

## Two-Track UX Infrastructure

| Component | Interactive Track | Recipe Track |
|-----------|------------------|--------------| 
| Stage transitions | User types `/mode-name` | Recipe `stages:` with approval gates |
| Approval points | Implicit (user sees output, decides next step) | Explicit `gate: approval` between stages |
| Convergence loop | `/bundle-execute` mode orchestrates | `bundle-refinement-loop.yaml` recipe |
| Single iteration | Agent delegation from execute mode | `bundle-single-iteration.yaml` sub-recipe |

Both tracks use the **same agents** with the **same context**. The only difference is who decides when to advance to the next stage.

## Version Stamping

Every bundle produced by the factory gets a provenance stamp in its `bundle.md` frontmatter.

### Canonical Schema

```yaml
bundle:
  name: <generated-bundle-name>
  version: 0.1.0
  description: |
    <generated description>
  generated_by:
    tool: bundlewizard
    version: <bundlewizard version from bundle.md>
    schema_version: 1
    timestamp: <ISO 8601>
    mode: <interactive|autonomous>
    convergence:
      level_score: <float>
      critic_verdict: <PASS|FAIL>
      tests_passed: <int>
      tests_failed: <int>
      commits: <int>
```

The `generated_by` block is nested under `bundle:` — it is bundle metadata, not a separate top-level key.

### Upgrade Stub Fields

These four fields are the upgrade contract. Upgrade logic reads them to decide whether migration is needed:

- `generated_by.tool` — identifies the generator
- `generated_by.version` — which version of the generator ran
- `generated_by.schema_version` — artifact format version (integer, bump when structure changes)
- `generated_by.timestamp` — when the bundle was generated

Everything under `convergence` is audit trail — upgrade logic ignores it.

### Legacy Fingerprint Recognition

Older generated bundles may use a different provenance shape. The legacy fingerprint is:

- `bundle.bundlewizard` key present (instead of `bundle.generated_by`)
- No `generated_by` key anywhere
- No `schema_version` field

When this fingerprint is detected, the upgrade path normalizes it to the canonical shape:
- `bundle.bundlewizard` → `bundle.generated_by`
- `bundlewizard.packaged_at` → `generated_by.timestamp`
- `bundlewizard.level_score` → `generated_by.convergence.level_score`
- `bundlewizard.critic_verdict` → `generated_by.convergence.critic_verdict`
- `bundlewizard.tests_passed` → `generated_by.convergence.tests_passed`
- `bundlewizard.tests_failed` → `generated_by.convergence.tests_failed`
- `bundlewizard.commits` → `generated_by.convergence.commits`
- Add `generated_by.tool: bundlewizard`
- Add `generated_by.version: <current bundlewizard version>`
- Add `generated_by.schema_version: 1`
- Remove the legacy `bundlewizard` key

This metadata enables traceability and upgradeability — you can always tell which bundles were machine-generated, what quality bar they met, and whether they need a schema migration.

## Domain-Specific Extensions

Each factory adds domain-specific agents beyond the core slots:

| Factory | Extra Agents | Purpose |
|---------|-------------|---------|
| Bundlewizard | `bundle-auditor`, `ecosystem-scout` | Improve-path audit, ecosystem survey |
| Harness-machine | `environment-analyst` | Environment feasibility mapping |

These are NOT part of the abstract protocol — they're domain concerns.

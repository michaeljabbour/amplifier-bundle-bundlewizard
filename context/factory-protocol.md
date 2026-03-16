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

Every bundle produced by the factory gets a version stamp:

```yaml
# In the generated bundle.md frontmatter:
bundle:
  name: <generated-bundle-name>
  version: 0.1.0
  description: |
    <generated description>
  generated_by:
    tool: bundlewizard
    version: 0.1.0
    convergence:
      iterations: <N>
      level_1: PASS
      level_2: <score>
      level_3: <score>
```

This metadata enables traceability — you can always tell which bundles were machine-generated and what quality bar they met.

## Domain-Specific Extensions

Each factory adds domain-specific agents beyond the core slots:

| Factory | Extra Agents | Purpose |
|---------|-------------|---------|
| Bundlewizard | `bundle-auditor`, `ecosystem-scout` | Improve-path audit, ecosystem survey |
| Harness-machine | `environment-analyst` | Environment feasibility mapping |

These are NOT part of the abstract protocol — they're domain concerns.

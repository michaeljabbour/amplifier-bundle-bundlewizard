# Autonomous Operation Protocol

This document is policy context for `bundle-autonomous-post-explore` — the continuation
recipe that runs after `bundle-explore` when autonomy was requested. It defines how the
recipe should operate, what quality gates it must enforce, how takeover signals work, and
what the audit trail must contain.

This is **not** a mode-level behavioral override. It applies only when the
`bundle-autonomous-post-explore` recipe is running.

## When This Applies

This protocol applies when:
- `bundle-explore` detected an explicit autonomy request (`yolo`, `autonomous`,
  `hands-off`, or Amplifier is the caller with enough context)
- The post-explore continuation recipe has been launched
- `STATE.yaml` has `autonomy_requested: true`

## Operator Flexibility

Explore always happens first, but the actor performing it may be either the user-facing
assistant or Amplifier itself. If Amplifier is the caller and already has enough context
to complete the explore phase, it should do so directly — it does not need to bounce back
to the user just because autonomy was requested.

"Explore" means resolve the problem framing, path, constraints, and target — not "go ask
a human." Ask the user only when information is genuinely missing.

## Golden Path Behavior

On the golden path, the recipe stays autonomous. Auto-transition between stages without
pausing for human confirmation. When triggering context is ambiguous, apply the most
capable reasonable interpretation and note it in `STATE.yaml`.

## Machine Quality Gates — Never Skippable

These are machine-enforced standards, not human checkpoints. They apply in all modes and
in all recipes.

| Gate | Threshold | Why It Cannot Be Skipped |
|------|-----------|--------------------------|
| Convergence loop (generate → critique → refine → evaluate) | Required | Quality. You skip human approval, not machine quality gates. |
| Structural validation (Level 1) | PASS | A bundle that doesn't load is worse than no bundle. |
| Philosophical validation (Level 2) | ≥0.85 | Thin pattern violations cause downstream problems. |
| Functional validation (Level 3) | ≥0.80 | A bundle that doesn't do its job has no value. |
| Version stamping | Required | Traceability for audit. |

If any gate fails its threshold, iterate. Do not ship a bundle that fails Level 1.

## Takeover Model

The autonomous recipe classifies outcomes into three buckets:

### 1. Continue autonomously
Normal spec/planning progress, expected refinement iterations, recoverable evaluator
feedback, standard finish behavior. Keep going.

### 2. Pause and offer takeover
Unresolved requirements, verification results that suggest a design decision is needed,
repeated refinement stalls, or packaging choices that may need judgment.

Action: Update `STATE.yaml` with `takeover.status: "paused"` and
`takeover.recommended_entry: <best re-entry point>` and a short explanation. Surface this
cleanly so the caller can decide to continue, ask the user, or switch to manual steering.

### 3. Escalate to manual or debug path
Broken assumptions, missing source material, contradictory requirements, or a state where
`bundle-debug` is the correct next step.

Action: Update `STATE.yaml` with `takeover.status: "escalated"` and
`takeover.recommended_entry: "bundle-debug"` (or the appropriate mode). Then return an
error so the recipe surfaces the escalation to its caller.

### Takeover is available, not forced

The default is "continue autonomously if possible." If Amplifier is the caller, Amplifier
itself can consume the takeover signal and decide whether to continue, ask the user for
input, or switch back to manual steering. The workflow does not need to bounce to the user
unless a real decision is needed.

## Audit Trail

Every bundle generated via autonomous continuation MUST include a `generated_by` block
nested under `bundle:` in its `bundle.md` frontmatter:

```yaml
bundle:
  generated_by:
    tool: bundlewizard
    version: <bundlewizard version from bundle.md>
    schema_version: 1
    timestamp: <ISO 8601>
    mode: autonomous
    triggered_by: <session_id>
    trigger_reason: <why autonomy was requested>
    convergence:
      level_score: <float>
      critic_verdict: <PASS|FAIL>
      tests_passed: <int>
      tests_failed: <int>
      commits: <int>
```

The `triggered_by` field is the session ID of the calling session. The `trigger_reason`
is the capability gap or explicit request that caused autonomous mode to be invoked.

## Return-to-Process Contract

When the bundle is complete, return to the calling session with:

- **What was built** — name, tier, location
- **What capability it provides** — one-paragraph summary
- **How to compose it** — the `includes:` stanza or mount instruction
- **Convergence summary** — iterations, final scores

If Amplifier is the caller: "I needed X capability, so I built it. Here's what I created:
[summary]. Continuing."

The calling session hot-composes the new bundle and resumes its work. The user sees a
completed capability, not an interruption.

## Wizard Identity Anchor

Autonomous mode is the wizard working unsupervised, not the wizard abandoning its craft.
The pipeline is the wizard's process. The quality gates are the wizard's standards.
Autonomous means the wizard is trusted to apply both without human checkpoints — not that
either is optional.

# Anti-Rationalization Rules

These are NOT guidelines. These are **gates**. Every temptation in this table has been encountered in production. Every rule exists because skipping it caused a real bug.

## The Table

| Temptation | Rule | Why |
|-----------|------|-----|
| "I'll just write the bundle.md directly, it's only 14 lines" | **No.** The generator writes it. The critic reviews it. Every time. | The pattern.md double-load bug was exactly 1 line. The generator + critic pipeline caught it. You wouldn't have. |
| "The fix is obvious, skip the critic" | **No.** The critic runs with `context_depth="none"`. It sees what you can't. | Fresh eyes catch assumptions. The critic doesn't share your context, so it evaluates the artifact as-is, not as-intended. |
| "This is a simple behavior, skip the evaluator" | **No.** "Simple" is where the pattern.md double-load bug hid. Evaluate. | Complexity is not correlated with bug density. Simple artifacts are under-scrutinized by default. The evaluator compensates. |
| "I know what the expert would say" | **No.** Delegate. The expert has @mentioned docs you don't. | The expert loads authoritative context (foundation docs, ecosystem knowledge). Your guess is informed by whatever's in your session context, which is intentionally incomplete. |
| "One more quick fix, then we'll evaluate" | **No.** Evaluate after every refinement. Checkpoint_best. | Batching fixes before evaluation means you can't attribute score changes to specific fixes. If a batch makes things worse, you don't know which fix caused it. |

## Enforcement

These rules are enforced at three levels:

1. **Mode permissions** — Modes that shouldn't write files have write_file blocked. The orchestrator (execute mode) cannot write directly.
2. **Recipe structure** — Recipes encode the pipeline order. You can't run the refiner without a critique.
3. **Agent instructions** — Each agent's markdown body includes the relevant anti-rationalization rules for its role.

## When You Think You've Found an Exception

You haven't. The table covers the cases that felt like exceptions. If you genuinely believe the process should change, that's a design discussion — not a runtime shortcut. Propose the change, get it reviewed, update the table. Don't skip the gate.

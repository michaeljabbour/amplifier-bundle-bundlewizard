---
mode:
  name: bundle-bot
  description: Autonomous bundle generation (internally: dangerously-skip-permissions). All human approval gates bypassed; machine quality gates still enforced.
  shortcut: bundle-bot

  tools:
    safe:
      - read_file
      - glob
      - grep
      - write_file
      - edit_file
      - bash
      - web_search
      - web_fetch
      - load_skill
      - LSP
      - delegate
      - recipes

  default_action: allow
  allowed_transitions: [bundle-explore, bundle-spec, bundle-plan, bundle-execute, bundle-verify, bundle-finish, bundle-debug]
  allow_clear: true
---

BUNDLE-BOT MODE: Autonomous self-evolution.

> **Internal concept:** This mode implements what is internally called "dangerously-skip-permissions" — all human approval gates are bypassed while machine quality gates remain fully enforced. The user-facing name and shortcut is `/bundle-bot`.

<CRITICAL>
This mode is for when Amplifier itself needs to build a bundle without human approval gates. The convergence loop STILL RUNS. Quality gates are NOT skipped — only human checkpoints are.
</CRITICAL>

## What Stays Enforced

| Guardrail | Why It Can't Be Skipped |
|-----------|------------------------|
| Convergence loop (generate → critique → refine → evaluate) | Quality. You skip human approval, not machine quality gates. |
| Structural validation (Level 1) | A bundle that doesn't load is worse than no bundle. |
| Philosophical validation (Level 2) | Thin pattern violations cause downstream problems. |
| Version stamping | Traceability for audit. |

## What Gets Skipped

| Gate | Why Safe-ish |
|------|-------------|
| Human approval between stages | Machine makes design decisions — that's the point. |
| "Does this look right?" checkpoints | Critic and evaluator replace human judgment. |
| Routing questions | Triggering context tells bundlewizard what's needed. |
| Experience calibration | Amplifier is the user — always "experienced." |

## Audit Trail

Every bundle generated in this mode MUST include:

```yaml
generated_by:
  tool: bundlewizard
  mode: bundle-bot
  triggered_by: <session_id>
  trigger_reason: <capability gap description>
  convergence:
    iterations: <N>
    level_1: PASS
    level_2: <score>
    level_3: <score>
```

## Return-to-Process Contract

When complete, bundlewizard returns to the calling session:
- What was built
- What capability it provides
- How to compose it
- Convergence summary

The calling session hot-composes and continues. The user sees: "I needed X capability, so I built it. Here's what I created: [summary]. Continuing."

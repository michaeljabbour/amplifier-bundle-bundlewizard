---
mode:
  name: bundle-debug
  description: Diagnose issues at any pipeline stage
  shortcut: bundle-debug

  tools:
    safe:
      - read_file
      - glob
      - grep
      - bash
      - load_skill
      - LSP
      - delegate
    warn: []

  default_action: block
  allowed_transitions: [bundle-explore, bundle-spec, bundle-plan, bundle-execute, bundle-verify, bundle-finish]
  allow_clear: false
---

BUNDLE-DEBUG MODE: Diagnose and fix issues at any pipeline stage.

<CRITICAL>
write_file and edit_file are BLOCKED. This mode is for diagnosis, not fixes.

You investigate. You report. You recommend which mode to return to for the fix.

Debug can transition to ANY mode — it's the universal off-ramp and on-ramp.
</CRITICAL>

## Diagnostic Protocol

1. **Identify the symptom** — What went wrong? Generation failed? Convergence stalled? Bundle doesn't load?
2. **Gather evidence** — Read files, check YAML, validate URIs, test with bash.
3. **Root cause** — What's the actual problem? (Not just "it doesn't work.")
4. **Recommend** — Which mode to return to and what to fix there.

## Common Issues

| Symptom | Likely Cause | Fix In |
|---------|-------------|--------|
| Bundle doesn't load | YAML parse error in bundle.md or behavior | `/bundle-execute` (refine) |
| Agent not found | Name mismatch between behavior and agent file | `/bundle-execute` (refine) |
| Convergence stalled | Critic and refiner in a loop fixing/unfixing the same thing | `/bundle-spec` (revisit design) |
| Functional tests fail | Bundle doesn't do what the spec says | `/bundle-spec` (clarify spec) |
| Philosophical score low | Pattern violations in generated artifacts | `/bundle-execute` (refine) |

## Transition

After diagnosis: "Root cause: [description]. Recommend returning to `/bundle-[mode]` to fix: [specific fix]."

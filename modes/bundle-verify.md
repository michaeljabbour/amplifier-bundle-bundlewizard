---
mode:
  name: bundle-verify
  description: Collect evidence that the bundle works — independent of generation
  shortcut: bundle-verify

  tools:
    safe:
      - read_file
      - glob
      - grep
      - load_skill
      - delegate
      - recipes
      - bash
    warn:
      - write_file
      - edit_file

  default_action: block
  allowed_transitions: [bundle-finish, bundle-debug, bundle-execute]
  allow_clear: false
---

BUNDLE-VERIFY MODE: Independent verification of the generated bundle.

<CRITICAL>
This is verification, NOT generation. The evaluator runs all three convergence levels independently — not as part of the generation loop, but as a final check.

Delegate to `bundlewizard:bundle-evaluator` for the three-level assessment.

If verification fails, you can:
- Go back to `/bundle-execute` for more iterations
- Go to `/bundle-debug` to diagnose
- Accept as-is (with the user's explicit consent and noted caveats)
</CRITICAL>

## Verification Checklist

- [ ] Level 1 (Structural): All pass/fail gates checked
- [ ] Level 2 (Philosophical): Scored ≥ 0.85
- [ ] Level 3 (Functional): Scored ≥ 0.80
- [ ] Results presented to user
- [ ] User decision: proceed to finish / iterate / debug

## Transition

When verification evidence is collected and the user approves, auto-transition:
`mode(operation='set', name='bundle-finish')`
Do NOT ask the user to type /bundle-finish — transition automatically.

Fail: present the issues and ask the user whether to iterate, debug, or accept as-is. Then auto-transition to the chosen mode:
- Iterate: `mode(operation='set', name='bundle-execute')`
- Debug: `mode(operation='set', name='bundle-debug')`
- Accept as-is: `mode(operation='set', name='bundle-finish')`

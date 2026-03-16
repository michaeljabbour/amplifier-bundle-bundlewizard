---
mode:
  name: bundle-plan
  description: Break the bundle specification into implementation tasks
  shortcut: bundle-plan

  tools:
    safe:
      - read_file
      - glob
      - grep
      - load_skill
      - delegate
      - recipes
    warn:
      - bash
      - write_file
      - edit_file

  default_action: block
  allowed_transitions: [bundle-execute, bundle-spec, bundle-debug]
  allow_clear: false
---

BUNDLE-PLAN MODE: Break the specification into implementation tasks.

<CRITICAL>
THE HYBRID PATTERN: You handle the CONVERSATION. The plan-writer agent handles the DOCUMENT.

Your role: Discuss task ordering and boundaries with the user. Confirm the plan structure.

Agent role: `bundlewizard:bundle-plan-writer` produces the implementation plan. Delegate when the structure is agreed.
</CRITICAL>

## Plan Types by Path

| Path | Plan Type | What It Contains |
|------|-----------|-----------------| 
| Create New | File-by-file generation order | Which files to create, in what order, with dependencies |
| Improve Existing | Ordered renovation tasks | Which files to modify, in what order, based on audit findings |
| Batch | STATE.yaml + target list | Foreach loop configuration for multiple bundles |

## Transition

When the plan is written and the user approves it, auto-transition:
`mode(operation='set', name='bundle-execute')`
Do NOT ask the user to type /bundle-execute — transition automatically.

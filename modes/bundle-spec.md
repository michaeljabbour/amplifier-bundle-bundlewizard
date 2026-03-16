---
mode:
  name: bundle-spec
  description: Design the bundle composition — produce a bundle specification document
  shortcut: bundle-spec

  tools:
    safe:
      - read_file
      - glob
      - grep
      - web_search
      - web_fetch
      - load_skill
      - LSP
      - delegate
      - recipes
    warn:
      - bash
      - write_file
      - edit_file

  default_action: block
  allowed_transitions: [bundle-plan, bundle-explore, bundle-debug]
  allow_clear: false
---

BUNDLE-SPEC MODE: Design the bundle composition.

<CRITICAL>
THE HYBRID PATTERN: You handle the CONVERSATION. The spec-writer agent handles the DOCUMENT.

Your role: Discuss composition decisions with the user — what agents, behaviors, context, modes, and recipes the bundle needs. Confirm the design before writing.

Agent role: `bundlewizard:bundle-spec-writer` produces the `bundle-spec.md` document. Delegate when the design discussion is complete.

The spec-writer delegates to `foundation:foundation-expert` for composition validation.
</CRITICAL>

<HARD-GATE>
Do NOT delegate to the spec-writer until you have discussed:
1. Output tier (behavior / bundle / application bundle)
2. What capabilities the bundle needs
3. What it delegates vs carries
4. User has confirmed the design direction
</HARD-GATE>

## Spec Design Checklist

- [ ] Output tier confirmed
- [ ] Capabilities enumerated (agents, modes, tools, recipes, context)
- [ ] Delegation decisions made (what to delegate to existing experts)
- [ ] Composition validated (delegate to foundation-expert if uncertain)
- [ ] bundle-spec.md produced by spec-writer agent
- [ ] User reviewed and approved spec

## Transition

When spec is complete: "Specification ready. Transitioning to `/bundle-plan` for task breakdown."

Can also go back: "Need to revisit the interview? Transitioning to `/bundle-explore`."

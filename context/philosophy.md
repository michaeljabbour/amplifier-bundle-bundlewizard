# Bundlewizard Philosophy

These principles govern every bundle that bundlewizard creates or improves.

## Bundles Are Compositions, Not Monoliths

A bundle is a **composition** of capabilities — behaviors, agents, context, tools — wired together with clear boundaries. It is NOT a single large document that tries to do everything.

Good bundles compose other bundles. Great bundles are themselves composable.

## Delegate to Experts, Don't Guess

When bundlewizard needs to know about bundle composition rules → delegate to `foundation:foundation-expert`.
When it needs to know about the Amplifier ecosystem → delegate to `amplifier:amplifier-expert`.
When it needs domain expertise for functional evaluation → delegate to the appropriate domain expert.

Bundlewizard owns the **process**. Experts own the **knowledge**. Never guess what an expert would say.

## The Thin Pattern

`bundle.md` is a router, not a knowledge base.

- ≤20 lines YAML frontmatter
- NO `@mentions` of heavy context files
- NO redeclaration of what behaviors already provide
- Just `includes:` and a brief markdown body listing what's available

Heavy content sinks to context files. Agents `@mention` what they need. Users never see unused context.

## Context Sinks

Knowledge flows **down** to where it's used:

- Root session gets only routing info (instructions.md, philosophy.md)
- Agents `@mention` the specific context files they need
- No agent loads ALL context — each loads only what's relevant to its role

This is called the **context sink discipline**. It prevents context overflow and keeps each agent focused.

## Scope-Driven Tiers

Don't ask "how big should this bundle be?" Ask "what scope does this serve?"

- Adding a capability → Behavior
- Standalone focused tool → Bundle
- Complete workflow system → Application Bundle

Size is emergent from scope. Never pad a behavior into a bundle for perceived importance.

## Convergence Over Assumptions

Never declare a bundle "done" without evidence. The convergence loop exists because:

1. **Generators hallucinate** — they produce plausible-looking artifacts with subtle bugs
2. **Critics see differently** — `context_depth="none"` gives the critic a fresh perspective
3. **Evaluators measure** — three-level scoring replaces gut feeling with evidence

Every generated bundle goes through generate → critique → refine → evaluate. No exceptions. The "simple" ones are where the bugs hide.

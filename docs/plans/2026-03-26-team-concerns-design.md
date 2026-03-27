# Team Concerns Enhancement Design

## Goal

Address 8 team concerns about gaps in validation, testing, intent capture, consumer experience, visualization, scope awareness, and triangulation — by extending existing bundlewizard agents and capabilities rather than introducing new ones.

## Background

The bundlewizard bundle (v0.4.0) is a bundle generation and improvement factory for the Amplifier ecosystem. The team raised concerns spanning intent traceability, scope awareness, consumer experience, shadow-based testing, fast iteration feedback, visualization, and cross-cutting triangulation. After brainstorming all 8 concerns, we arrived at a design that addresses every one through extensions to the existing agent set — no new agents, no new modes, no new dependencies.

Three design constraints guided every decision:

1. **Leverage existing modes and capabilities** — `/bundle-verify`, `/bundle-explore`, and the convergence loop continue to work as-is
2. **Do everything the Amplifier way** — behaviors compose, agents are context sinks, skills are on-demand knowledge, modes enforce phases
3. **Don't over-engineer** — extend, don't proliferate

## Priority Order

Intent cluster first, then validation, then experience.

## Approach

Four coordinated change sets, each extending existing agents and artifacts:

| Change Set | Focus | Agents Extended |
|---|---|---|
| Section 1 | Intent Capture & Traceability | Explorer, Spec-writer |
| Section 2 | Validation & Shadow Testing | Evaluator, Critic |
| Section 3 | Triangulation & Exemplar Corpus | Evaluator, Critic, `bundle-reference` skill |
| Section 4 | Extended DOT Visualization | Critic, Explorer |

## Section 1: Intent Capture & Traceability

### Explorer — Suitability Check

The explorer interview already captures a 15-field handoff payload and routes across 4 paths. Two additions:

1. **Suitability check** in the first 1-2 questions — before the full interview, the explorer assesses whether the request fits bundlewizard's capabilities:
   - Needs custom Python? → Flag as out-of-scope, suggest manual approach
   - Trivially a 5-line behavior? → Suggest quick path instead of full pipeline
   - Needs a dev-machine setup? → Steer away from bundlewizard

   This is the same routing logic the explorer already uses for its 4 paths, with a suitability lens added up front.

2. **Consumer question** — "Who will use this bundle and what's their experience level?" This feeds the spec's new consumer experience section.

### Spec-Writer — Template Extensions

The `bundle-spec.md` template gains three new sections:

**`## Requirements`** — Numbered, structured requirements derived from the explorer's handoff. Each requirement has:
- A unique ID (R1, R2, R3...)
- A description
- An acceptance criterion

**`## Consumer Experience`** — Target persona, first-run expectations, progressive disclosure path. Populated from the explorer's consumer question.

**`## Scope Exclusions`** — What this bundle explicitly does NOT do. Borrowed from IDD's `scope_out` pattern (concept borrowed, not dependency added).

### Traceability Matrix

Lives at the bottom of the spec as `## Traceability Matrix`.

- Initially populated by the spec-writer: `R1 → (pending)`, `R2 → (pending)`
- The evaluator fills in artifact mappings: `R1 → agents/review-agent.md`, `R2 → modes/review.md`
- The critic checks for orphaned artifacts (no requirement) and unmet requirements (no artifact)

This creates a closed loop: explorer captures intent → spec-writer structures it → evaluator maps it → critic validates it.

## Section 2: Validation & Shadow Testing

### Evaluator — Shadow-Based Smoke Test

The evaluator currently runs a smoke test via `amplifier --bundle ./bundle.md --run "list available agents"` in the real environment. Three upgrades:

**1. Shadow workflow** — Replace the real-environment smoke test with:

```
amplifier-shadow create → install bundle → run test prompts → capture output → destroy shadow
```

The evaluator already has `tool-bash`, so this is `amplifier-shadow create` / `exec` / `destroy` commands in its protocol. If shadow tooling isn't available (not installed), fall back to the current real-environment smoke test gracefully.

**2. Surface test results** — Enhance the evaluator's report format to include a `## Shadow Test Results` section with:
- Each test prompt run
- The result (pass/fail)
- Key output

This gives fast-iteration feedback without a new mode — the user sees what happened every iteration through the existing convergence loop and verify mode.

**3. Consumer lens in L3** — The evaluator's Level 3 functional scoring gains a consumer sub-check:
- Would a new user understand this bundle's README?
- Are agent descriptions clear?
- Are modes discoverable?

Scored against the `consumer_experience` section from the spec (which the explorer populated). This isn't a separate pass — it's an additional consideration within L3.

### Critic — Traceability Validation

The critic gains traceability validation: check that every numbered requirement (R1, R2...) maps to at least one generated artifact, and every generated artifact traces back to at least one requirement. Orphans and gaps are flagged.

### No New Agents or Modes

`/bundle-verify` continues to work exactly as it does — it already delegates to the evaluator, which now does more thorough work. No new modes, no new entry points.

## Section 3: Triangulation & Exemplar Corpus

### Exemplar Corpus in `bundle-reference` Skill

The existing `skills/bundle-reference/` skill is expanded with a scored exemplar corpus:

**Known-good bundles (5-10):**
- `amplifier-bundle-recipes` as canonical reference
- `superpowers`, `modes`, and other established bundles
- Each annotated with what makes it good ("this bundle demonstrates X well")

**Anti-pattern examples (3-5):**
- Monolith `bundle.md` (everything in one file)
- Context loaded everywhere (no scoping discipline)
- Agents with no examples (unclear delegation)
- Circular includes
- Each annotated with what's wrong ("this bundle violates Y")

Annotations are short — not full audits, just pattern pointers.

### Agent Stubs

The critic and evaluator agents get a lightweight `@mention` stub in their context (or a line in their instructions):

> "When scoring L2 philosophical quality, load the `bundle-reference` skill for pattern comparison against known-good exemplars."

The skill stays out of their token budget until they actually load it. Real corpus lives in the on-demand skill; agents get pointers.

### Triangulation Check

Not a new gate or a new level. It's a section in the evaluator's existing output. After L1/L2/L3 scoring, the evaluator adds a `## Triangulation` section that confirms three legs:

1. **Intent** — Traceability matrix has no orphaned artifacts and no unmet requirements
2. **Structure** — L2 philosophical score meets threshold AND patterns match known-good exemplars
3. **Function** — L3 functional score meets threshold AND shadow test prompts passed

If any two of the three legs disagree (e.g., L2 passes but traceability shows unmet requirements), the evaluator flags it. This isn't a new convergence level — it's a cross-check across what already exists.

## Section 4: Extended DOT Visualization

### New Edge Categories

The existing `bundle-architecture.dot` schema has file nodes and delegation/context edges. Two new edge categories are added to the same artifact:

**Composition edges** — Show the `includes:` chain:
- `bundle.md` → `behaviors/bundlewizard.yaml` → `amplifier-bundle-modes` (behavior include)
- Answer the question: "What does this bundle bring into my session?"
- Visual style: `style=dashed, color=blue`

**Agentic flow edges** — Show runtime delegation paths:
- `bundle-explorer` → `ecosystem-scout` → `amplifier:amplifier-expert`
- Answer the question: "What happens when I use this bundle?"
- Visual style: `style=bold, color=green`

No new artifact. Same DOT file, richer edge types. Subgraphs cluster external dependencies (things from other namespaces) vs. local artifacts.

### Critic Validation for New Edges

The critic already validates node↔file correspondence and delegation edges. Extended to also validate:
- Composition edges match actual `includes:` entries in behavior YAML
- Flow edges match actual `delegate()` calls in agent instructions

### Explorer DOT Enhancement

When the explorer produces the initial DOT diagram during interview, it now includes tentative composition edges (what the bundle will need to include) alongside the existing tentative file nodes. This makes the "visual intent contract" richer from the start.

## Team Concerns Coverage Matrix

| # | Concern (Owner) | Addressed By | Mechanism |
|---|---|---|---|
| 1 | Bundle validation & testing (Manoj) | Section 2 | Evaluator shadow-based smoke test, critic traceability validation |
| 2 | Fast iteration & usability testing (Ken) | Section 2 | Evaluator surfaces shadow test results every iteration |
| 3 | UAT in shadow environment (Ken) | Section 2 | Evaluator runs test prompts in shadow environment |
| 4 | Consumer experience (Ken) | Sections 1+2 | Explorer captures consumer intent, evaluator validates against spec |
| 5 | Intent capture & validation (Ken) | Section 1 | Numbered requirements, traceability matrix, scope exclusions |
| 6 | Visualization options | Section 4 | Extended DOT with composition and flow edges |
| 7 | Scope awareness | Section 1 | Explorer suitability check in first 1-2 questions |
| 8 | Triangulation (MJ) | Section 3 | Exemplar corpus in skill, stubs in agents, evaluator cross-check |

## Files That Will Change

| File | Change Type | What Changes |
|---|---|---|
| `agents/bundle-explorer.md` | Extend | Add suitability check protocol + consumer question to interview |
| `agents/bundle-spec-writer.md` | Extend | Add Requirements, Consumer Experience, Scope Exclusions, Traceability Matrix to spec template |
| `agents/bundle-evaluator.md` | Extend | Shadow smoke test, surface test results, consumer L3 lens, triangulation section |
| `agents/bundle-critic.md` | Extend | Traceability validation (requirement ↔ artifact), composition/flow edge validation in DOT |
| `skills/bundle-reference/SKILL.md` | Extend | Add scored exemplar corpus (5-10 good, 3-5 anti-patterns) |
| `context/convergence-criteria.md` | Extend | Document traceability and triangulation as evaluation dimensions |
| `context/factory-protocol.md` | Extend | Document composition and flow edge types in DOT schema |

## What Does NOT Change

- No changes to mode files (`modes/*`)
- No changes to recipe files (`recipes/*`)
- No changes to `bundle.md` or behavior YAML
- No changes to the convergence formula (L1 pass + L2 ≥ 0.85 + L3 ≥ 0.80)
- No new agents, tools, hooks, or modules

## Open Questions

None. All sections were validated during the design conversation.
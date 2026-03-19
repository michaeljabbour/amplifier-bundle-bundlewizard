# Explore Interview Flow v2: Four-Path Routing Design

## Goal
Add a fourth routing path to `bundle-explore` that serves users who want to customize their overall Amplifier experience rather than work on a single capability bundle.

## The Gap

The current `bundle-explore` mode routes users down three paths:

| Path | Name | Purpose |
|------|------|---------|
| **A** | Create New | Build a new capability bundle |
| **B** | Improve Existing | Enhance an existing bundle |
| **C** | Rebuild from Reference | Reconstruct a bundle from reference material |

All three assume the user wants to work on a *capability bundle*.

But there's a class of user who says things like "customize my amplifier," "replace foundation," "my own setup," "I use GitHub Copilot not foundation." They're not building a capability — they're designing a **personal Amplifier experience**: identity, provider, persona, tool selection, infrastructure. None of the three paths serve them.

**Path D: Design My Experience** fills this gap. It's an experience-oriented interview that helps users compose their overall Amplifier setup rather than a single bundle.

## Chosen Approach

Add Path D as a peer to the existing three paths, reusing the same shared handoff block and pipeline infrastructure. No new agents, recipes, or context files are introduced. Path D branches into three sub-paths (D1/D2/D3) to cover the spectrum from "tweak foundation" to "build from scratch," with D3 redirecting into the existing Path C to avoid logic duplication.

## Four-Path Routing Fork

The entry point adds a 4th option to the disambiguation. When user signals are ambiguous, the explorer asks:

> *"Are you looking to: (a) add a capability, (b) improve an existing bundle, (c) rebuild something from a reference, or (d) customize your overall Amplifier experience?"*

### Path D Signal Detection

Path D triggers when the user's input matches experience-customization intent. Signal phrases include:

| Category | Example phrases |
|----------|----------------|
| Direct customization | "customize my amplifier," "my own setup," "replace foundation" |
| Provider/tool preferences | "I use GitHub Copilot," "I don't want foundation defaults" |
| Experience design | "design my experience," "build my own from scratch" |

### Shared Handoff Convergence

All four paths converge at the same shared handoff block:

1. Compile structured handoff payload
2. Gate on `autonomy_requested` + `open_questions`
3. Route to either the autonomous continuation recipe or `/bundle-spec`

Path D adds `path_decision: "design_my_experience"` to the handoff payload schema, joining the existing values (`create_new`, `improve_existing`, `rebuild_from_reference`).

## Path D Sub-Routing (D1 / D2 / D3)

Once a user is on Path D, they hit a second fork — "How do you want to build your experience?"

### D1: Foundation + Customize

For users who want foundation's rich defaults but need to override specific things (provider, persona, drop/add behaviors).

**7-step interview:**

1. **Identity** — Who is this experience for? What's the use case?
2. **Provider** — Which LLM provider and model preferences?
3. **Persona** — What personality and communication style?
4. **Keep/Drop Behaviors** — Which foundation behaviors to retain, which to drop?
5. **Add Capabilities** — Any additional capability bundles to layer in?
6. **Naming** — Bundle name, description, metadata
7. **Autonomy** — Manual, autonomous, or hybrid workflow preference?

### D2: Start from Scratch

For users who want a pure cherry-pick build with no inherited defaults. Complete control over every layer.

**10-step interview:**

1. **Identity** — Who is this experience for? What's the use case?
2. **Provider** — Which LLM provider and model preferences?
3. **Persona** — What personality and communication style?
4. **Orchestrator Choice** — Which orchestrator model to use?
5. **Context Manager** — How should context be managed?
6. **Tools** — Which tools to include?
7. **Hooks** — Which hooks to wire up?
8. **Agents** — Which agents to include?
9. **System Instructions** — Custom system-level instructions and policies?
10. **Autonomy** — Manual, autonomous, or hybrid workflow preference?

### D3: Adapt Existing

For users who have something already and want to reshape it.

**Redirects to Path C** with an `experience_lens` flag. No separate interview is needed. The flag tells the spec phase to frame the rebuild as experience customization rather than capability reconstruction. This avoids duplicating Path C's existing logic.

## Implementation Scope

This is a contained change — no new agents, no new recipes, no new context files. Three files change:

| File | Change |
|------|--------|
| `agents/bundle-explorer.md` | Add Path D signal detection, 4th disambiguation option, D1/D2/D3 interview logic |
| `modes/bundle-explore.md` | Add "Design My Experience" checklist, add `path_decision: "design_my_experience"` to handoff payload schema |
| `context/instructions.md` | Rename "Three-Path Routing Fork" → "Four-Path Routing Fork", add Path D signals table and interview flow description |

No structural changes to the pipeline. Path D uses the same shared handoff block as A/B/C. The D3→C redirect means no existing logic is duplicated.

## Supporting Artifacts

A complete Graphviz flow diagram captures the full four-path routing:

- **Source:** `docs/stories/explore-interview-flow.dot` (616 lines)
- **Render:** `docs/stories/explore-interview-flow.png` (831 KB)

The diagram uses a dark theme with color-coded paths (A=green, B=gold, C=blue, D=purple), diamond decision nodes, and all interview steps for every path and sub-path.

## Open Questions

None. All sections were validated during the design conversation.
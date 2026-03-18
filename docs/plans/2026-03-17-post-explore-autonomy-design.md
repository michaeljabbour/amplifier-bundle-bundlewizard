# Bundlewizard Post-Explore Autonomy Design

> **Supersedes:** `docs/plans/2026-03-17-autonomous-mode-design.md`.
> This design replaces the earlier version because all shipped changes must remain inside `amplifier-bundle-bundlewizard`.

## Goal
Redesign bundlewizard autonomy so all shipped changes remain inside `amplifier-bundle-bundlewizard`, while preserving the manual bundlewizard flow and adding opt-in autonomy after exploration.

## Background
The earlier autonomy design depended on upstream changes in `amplifier-bundle-modes`. This replacement design removes that dependency and instead mirrors the established superpowers pattern: manual modes remain the steering wheel, while recipes provide cruise control.

That pattern is explicit in the superpowers bundle:
- `amplifier-bundle-superpowers/context/instructions.md:58` presents the two-track UX.
- `amplifier-bundle-superpowers/context/instructions.md:64` points complete work to the full-cycle recipe.
- `amplifier-bundle-superpowers/bundle.md:50` shows the manual pipeline.
- `amplifier-bundle-superpowers/bundle.md:53` states the core metaphor: modes give the steering wheel, recipes give cruise control.
- `amplifier-bundle-superpowers/docs/USAGE_GUIDE.md:67` shows the automated pipeline entry.
- `amplifier-bundle-superpowers/docs/USAGE_GUIDE.md:663` names the canonical full-cycle recipe.
- `amplifier-bundle-superpowers/docs/USAGE_GUIDE.md:808` recommends the hybrid pattern of interactive work first and autonomous work later.
- `amplifier-bundle-superpowers/recipes/superpowers-full-development-cycle.yaml:16` defines the full-cycle recipe entrypoint.

This design applies that same split to bundlewizard without introducing an upstream modes-infrastructure fork.

## Constraints
- Manual flow remains the default.
- `bundle-explore` stays the front door.
- Autonomy is opt-in only (`autonomous`, `yolo`, or similar requests).
- If autonomy is requested up front, `bundle-explore` automatically hands off after explore completes.
- Explicit `continue autonomously` after explore also works.
- Once autonomy starts, it stays autonomous by default, but takeover remains available if the flow leaves the golden path.
- Amplifier itself may perform the explore phase when it already has enough context; it does not need to bounce back to the user just because autonomy was requested by Amplifier.
- All shipped changes remain inside `amplifier-bundle-bundlewizard`.

## Chosen Approach
Bundlewizard should adopt the same split that superpowers uses:
- the current manual mode pipeline remains the canonical workflow
- autonomy is recipe-driven
- autonomy begins only after `bundle-explore`

This means bundlewizard does **not** gain a second autonomous mode stack, a separate autonomous behavior profile, or new upstream modes machinery. Instead, it keeps the existing manual path intact and adds a bundle-local continuation recipe that takes over after exploration when autonomy has been requested.

The key rule is:

> Explore always happens first, but the actor performing it may be either the user-facing assistant or Amplifier itself.

## Architecture
`bundle-explore` remains the front door and the handoff gate.

The architecture is:
- `bundle-explore` handles the explore phase
- the existing manual mode pipeline remains the default path
- if autonomy was requested up front, `bundle-explore` automatically launches a bundle-local continuation recipe after explore completes
- if autonomy is requested after explore, the same continuation recipe is launched explicitly
- the continuation recipe owns the autonomous path through:
  - `bundle-spec`
  - `bundle-plan`
  - `bundle-execute`
  - `bundle-verify`
  - `bundle-finish`

This keeps the manual and autonomous paths conceptually aligned. Modes still represent staged workflow. The recipe simply automates the continuation once the explore phase has established direction.

## Handoff Semantics
`bundle-explore` remains universal, but its job is defined by what it resolves rather than by who it talks to.

The explore phase must resolve a structured handoff payload containing:
- `path_decision` (`create new`, `improve existing`, `rebuild from reference`)
- `target`
- `tier`
- `summary_of_requirements`
- `known_constraints`
- `autonomy_requested`
- `trigger_reason`
- `open_questions`

If Amplifier is the caller and already has enough context, Amplifier should complete this explore phase directly instead of sending the workflow back to the user.

Control rules:
- if autonomy is not requested, continue into normal manual `bundle-spec`
- if autonomy is requested and explore has enough context, auto-launch the post-explore continuation recipe
- if autonomy was requested but explore still has unresolved blockers, remain in explore until those blockers are resolved

This makes explore the universal entrypoint while keeping the operator flexible.

## Autonomous Recipe Design
Autonomy after explore is implemented as a bundle-local continuation recipe, not as a second autonomous mode universe.

The continuation recipe owns:
- `bundle-spec`
- `bundle-plan`
- `bundle-execute`
- `bundle-verify`
- `bundle-finish`

Its input is the structured handoff payload produced by explore. That payload may come from a user interview or from Amplifier's own exploration when Amplifier is the caller. The contract stays the same either way.

On the golden path, the recipe stays autonomous by default. If it leaves the golden path, it should surface takeover points instead of forcing a handoff.

`templates/STATE.yaml` is the shared bridge between manual and autonomous execution. It serves as the pause, resume, and takeover contract across both tracks.

## Failure and Takeover Model
The continuation recipe should classify outcomes into three buckets.

### 1. Continue autonomously
Use this for:
- normal spec and planning progress
- expected refinement iterations
- recoverable evaluator feedback
- standard finish behavior

### 2. Pause and offer takeover
Use this for:
- unresolved requirements
- verification results that suggest a design decision is needed
- repeated refinement stalls
- packaging or delivery choices that may need judgment

### 3. Escalate to manual or debug path
Use this for:
- broken assumptions
- missing source material
- contradictory requirements
- a state where `bundle-debug` is the correct next phase

`STATE.yaml` should record:
- current stage
- status (`completed`, `blocked`, `needs_takeover`, `failed_verification`)
- latest outputs such as the spec, plan, and evaluation summary
- recommended next manual entrypoint (`bundle-spec`, `bundle-plan`, `bundle-execute`, `bundle-debug`, and similar)
- a short explanation of why takeover is being suggested

If Amplifier is the caller, Amplifier itself can consume the takeover signal and decide whether to continue, ask the user for input, or switch back to manual steering. The workflow should not bounce to the user unless a real decision is needed.

## Shipped Surface vs Non-Shipped Surface
### What ships
- `bundle.md` remains the thin default entrypoint
- `behaviors/bundlewizard.yaml` remains the only default shipped behavior
- the current manual mode stack remains the canonical mode pipeline
- `modes/bundle-explore.md` becomes the handoff gate:
  - it still performs explore
  - it detects whether autonomy was requested
  - if yes, it launches the continuation recipe after explore completes
  - if not, it transitions into normal manual `bundle-spec`
- add a bundle-local continuation recipe, named something like `recipes/bundle-autonomous-post-explore.yaml`, which owns:
  - spec
  - plan
  - execute
  - verify
  - finish
- keep `context/autonomous-protocol.md`, but repurpose it as recipe and autonomy policy context rather than a behavior-level profile switch
- use `templates/STATE.yaml` as the shared bridge between manual and autonomous operation

### What does not ship
- no upstream `amplifier-bundle-modes` changes
- no bundle-local reliance on custom `hooks-mode.autonomous`
- no `bundlewizard-autonomous.yaml` if it depends on a non-upstream mechanism
- no second autonomous mode universe
- no `bundle-bot.md`

Local experiments in the `amplifier-bundle-modes` submodule are scratch and reference material only. They are not part of the shipped design.

## Open Implementation Implications
- `bundle-explore` becomes the single gate that decides between continuing manually and launching autonomy.
- The autonomous path must be implemented as a bundle-local recipe rather than a behavior-level profile switch.
- `templates/STATE.yaml` becomes the formal contract for pause, resume, and takeover across manual and autonomous flows.
- `context/autonomous-protocol.md` remains useful, but only as autonomy policy context for the continuation recipe.
- Existing upstream-dependent experiments are reference material only and should not shape the shipped surface.

## Open Questions
None in the validated design. The remaining work is implementation detail inside the contained bundle-local approach described above.

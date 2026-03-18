# Post-Explore Autonomy Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Implement opt-in post-explore autonomy inside `amplifier-bundle-bundlewizard` — modes stay the steering wheel, a new bundle-local recipe becomes cruise control.

**Architecture:** `bundle-explore` becomes the handoff gate: after exploration, it either auto-transitions into manual `bundle-spec` (default) or launches a new bundle-local continuation recipe (`bundle-autonomous-post-explore.yaml`) when autonomy was requested. The recipe owns `spec → plan → execute → verify → finish` autonomously. `STATE.yaml` is the shared bridge for pause, resume, and takeover across both tracks.

**Tech Stack:** Markdown mode files with YAML frontmatter, recipe YAML, pytest + PyYAML for structural tests, `pathlib.Path` for file operations.

**Design doc:** `docs/plans/2026-03-17-post-explore-autonomy-design.md`

---

## Scope boundaries — read before starting

- ALL changes stay inside `amplifier-bundle-bundlewizard`
- Do NOT touch `amplifier-bundle-modes/` — it is a scratch submodule, not part of this plan
- `behaviors/bundlewizard-autonomous.yaml` must be **deleted** — it depends on upstream-only infrastructure
- `behaviors/bundlewizard.yaml` is the **only** shipped behavior after this plan; do not create another
- Manual flow remains the default; autonomy is opt-in only and starts AFTER explore
- Amplifier itself may perform exploration — do not force a bounce back to the user when Amplifier already has enough context

---

## Pre-flight check

Before starting, verify the repo state:

```bash
cd /path/to/amplifier-bundle-bundlewizard
git status
pytest tests/test_modes_adherence.py -v
```

Expected: you see `behaviors/bundlewizard-autonomous.yaml` exists and several tests pass for it. Those tests are about to be replaced. That's intentional.

---

## Phase 1 — Remove the Wrong-Path Surface

### Task 1: Rewrite tests and delete the abandoned behavior file

**Files:**
- Modify: `tests/test_modes_adherence.py` (full rewrite of wrong-design tests)
- Delete: `behaviors/bundlewizard-autonomous.yaml`

---

**Step 1: Write the failing regression guard test**

Open `tests/test_modes_adherence.py`. Locate the three wrong-design test functions and the module-level directory constants. You need to do two things: (a) add `TEMPLATES_DIR` and `RECIPES_DIR` constants, and (b) replace the three wrong-design tests with correct-design tests.

Replace the entire block from line 115 to the end of the file with the following. Do NOT delete anything above line 114 — the `test_bundle_bot_does_not_exist`, `test_pipeline_modes_exist`, `test_pipeline_mode_transitions`, `test_pipeline_mode_allow_clear`, `test_autonomous_protocol_exists`, `test_autonomous_protocol_has_audit_trail`, and `test_instructions_no_bundle_bot` tests are still correct and must be kept.

First, add the two missing directory constants near the top of the file, right after `CONTEXT_DIR`:

```python
TEMPLATES_DIR = REPO_ROOT / "templates"
RECIPES_DIR = REPO_ROOT / "recipes"
```

Now replace the three wrong-design functions (everything from `def test_autonomous_behavior_exists` through `def test_autonomous_behavior_agents_match`, inclusive) with the following new block. This goes in the same position, between `test_pipeline_mode_allow_clear` and `test_autonomous_protocol_exists`:

```python
def test_autonomous_behavior_does_not_exist():
    """behaviors/bundlewizard-autonomous.yaml must NOT exist.

    The upstream-dependent autonomous behavior has been replaced by a bundle-local
    post-explore continuation recipe (recipes/bundle-autonomous-post-explore.yaml).
    Shipping this file would re-introduce an upstream amplifier-bundle-modes dependency.
    """
    path = BEHAVIORS_DIR / "bundlewizard-autonomous.yaml"
    assert not path.exists(), (
        "behaviors/bundlewizard-autonomous.yaml still exists. "
        "This upstream-dependent file must be deleted. "
        "Autonomy is now handled by recipes/bundle-autonomous-post-explore.yaml."
    )


def test_state_yaml_has_autonomy_fields():
    """templates/STATE.yaml must include autonomy handoff and takeover contract fields."""
    path = TEMPLATES_DIR / "STATE.yaml"
    assert path.exists(), "templates/STATE.yaml does not exist"
    content = yaml.safe_load(path.read_text(encoding="utf-8"))

    session = content.get("session", {})
    assert "autonomy_requested" in session, (
        "STATE.yaml session block must have an autonomy_requested field"
    )
    assert "trigger_reason" in session, (
        "STATE.yaml session block must have a trigger_reason field"
    )

    assert "takeover" in content, (
        "STATE.yaml must have a top-level takeover section"
    )
    takeover = content["takeover"]
    assert "status" in takeover, "STATE.yaml takeover must have a status field"
    assert "recommended_entry" in takeover, (
        "STATE.yaml takeover must have a recommended_entry field"
    )
    assert "explanation" in takeover, (
        "STATE.yaml takeover must have an explanation field"
    )


def test_autonomous_protocol_is_recipe_policy():
    """context/autonomous-protocol.md must be repurposed as recipe/autonomy policy.

    It must NOT contain mode-level behavioral override instructions (old design).
    It MUST reference the post-explore continuation recipe.
    """
    path = CONTEXT_DIR / "autonomous-protocol.md"
    assert path.exists(), "context/autonomous-protocol.md does not exist"
    content = path.read_text(encoding="utf-8")

    assert "bundle-autonomous-post-explore" in content, (
        "autonomous-protocol.md must reference bundle-autonomous-post-explore "
        "to establish it as recipe/autonomy policy context"
    )
    assert "When any mode instruction says" not in content, (
        "autonomous-protocol.md still contains mode-level behavioral override language. "
        "This file must be repurposed as recipe policy context, not a mode-level override."
    )


def test_explore_mode_is_handoff_gate():
    """modes/bundle-explore.md must act as a handoff gate.

    It must detect autonomy_requested and reference the post-explore recipe.
    """
    path = MODES_DIR / "bundle-explore.md"
    assert path.exists(), "modes/bundle-explore.md does not exist"
    content = path.read_text(encoding="utf-8")

    assert "autonomy_requested" in content, (
        "bundle-explore.md must detect autonomy_requested to decide the handoff path"
    )
    assert "bundle-autonomous-post-explore" in content, (
        "bundle-explore.md must reference bundle-autonomous-post-explore "
        "for launching autonomous continuation"
    )


def test_autonomous_post_explore_recipe_exists():
    """recipes/bundle-autonomous-post-explore.yaml must exist."""
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    assert path.exists(), (
        "recipes/bundle-autonomous-post-explore.yaml does not exist. "
        "This recipe is the autonomous continuation engine for post-explore operation."
    )


def test_autonomous_post_explore_recipe_stages():
    """The post-explore recipe must contain all 5 required continuation stages."""
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    if not path.exists():
        pytest.skip("bundle-autonomous-post-explore.yaml not yet created")
    content = yaml.safe_load(path.read_text(encoding="utf-8"))

    stages = [s["name"] for s in content.get("stages", [])]
    required = {"spec", "plan", "execute", "verify", "finish"}
    missing = required - set(stages)
    assert not missing, (
        f"bundle-autonomous-post-explore.yaml is missing required stages: {missing}. "
        f"Found: {stages}"
    )


def test_autonomous_post_explore_recipe_no_required_approval_gates():
    """The post-explore recipe must NOT have required: true approval gates.

    It is the autonomous track — human approval gates defeat the purpose.
    Takeover points are offered via STATE.yaml, not forced via approval gates.
    """
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    if not path.exists():
        pytest.skip("bundle-autonomous-post-explore.yaml not yet created")
    content = yaml.safe_load(path.read_text(encoding="utf-8"))

    for stage in content.get("stages", []):
        approval = stage.get("approval", {})
        assert approval.get("required", False) is not True, (
            f"Stage '{stage['name']}' has required: true approval gate. "
            "The autonomous recipe must not force human approval gates."
        )


def test_autonomous_post_explore_recipe_reuses_refinement_loop():
    """The post-explore recipe must reuse bundle-refinement-loop for execution.

    Do not duplicate the convergence loop — reuse the existing sub-recipe.
    """
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    if not path.exists():
        pytest.skip("bundle-autonomous-post-explore.yaml not yet created")
    content = path.read_text(encoding="utf-8")

    assert "bundle-refinement-loop" in content, (
        "bundle-autonomous-post-explore.yaml must invoke bundle-refinement-loop.yaml "
        "for the execute stage — do not duplicate convergence logic."
    )


def test_instructions_describes_opt_in_autonomy():
    """context/instructions.md must describe the opt-in autonomy-after-explore path."""
    path = CONTEXT_DIR / "instructions.md"
    content = path.read_text(encoding="utf-8")

    assert "bundle-autonomous-post-explore" in content, (
        "context/instructions.md must reference bundle-autonomous-post-explore.yaml "
        "in its two-track UX description"
    )
```

**Step 2: Run the tests to confirm failures**

```bash
pytest tests/test_modes_adherence.py -v
```

Expected failures (this is correct — you are about to fix them one by one):
- `FAILED test_autonomous_behavior_does_not_exist` — file still exists
- `FAILED test_state_yaml_has_autonomy_fields` — fields not added yet
- `FAILED test_autonomous_protocol_is_recipe_policy` — file not updated yet
- `FAILED test_explore_mode_is_handoff_gate` — mode not updated yet
- `FAILED test_autonomous_post_explore_recipe_exists` — recipe not created yet
- `FAILED test_instructions_describes_opt_in_autonomy` — instructions not updated yet

Tests that should still PASS:
- `test_bundle_bot_does_not_exist`
- `test_pipeline_modes_exist`
- `test_pipeline_mode_transitions`
- `test_pipeline_mode_allow_clear`
- `test_autonomous_protocol_exists`
- `test_autonomous_protocol_has_audit_trail`
- `test_instructions_no_bundle_bot`

If any of the "still PASS" group fails, stop and investigate before continuing.

**Step 3: Delete the abandoned behavior file**

```bash
git rm behaviors/bundlewizard-autonomous.yaml
```

**Step 4: Run the first test to confirm it now passes**

```bash
pytest tests/test_modes_adherence.py::test_autonomous_behavior_does_not_exist -v
```

Expected: `PASSED`

**Step 5: Commit**

```bash
git add tests/test_modes_adherence.py
git commit -m "refactor: replace wrong-design tests with contained-design contract

- Remove test_autonomous_behavior_exists (upstream-dependent design)
- Remove test_autonomous_behavior_config (upstream-dependent design)
- Remove test_autonomous_behavior_agents_match (upstream-dependent design)
- Delete behaviors/bundlewizard-autonomous.yaml (upstream hooks-mode.autonomous dependency)
- Add test_autonomous_behavior_does_not_exist (regression guard)
- Add test_state_yaml_has_autonomy_fields (handoff contract)
- Add test_autonomous_protocol_is_recipe_policy (repurposed context)
- Add test_explore_mode_is_handoff_gate (new gate behavior)
- Add test_autonomous_post_explore_recipe_exists (new recipe)
- Add test_autonomous_post_explore_recipe_stages (new recipe shape)
- Add test_autonomous_post_explore_recipe_no_required_approval_gates (autonomy constraint)
- Add test_autonomous_post_explore_recipe_reuses_refinement_loop (reuse constraint)
- Add test_instructions_describes_opt_in_autonomy (updated docs)"
```

---

## Phase 2 — Lock the Explore Handoff Contract

### Task 2: Expand `templates/STATE.yaml` with autonomy and takeover fields

**Files:**
- Modify: `templates/STATE.yaml`

---

**Step 1: Verify the failing test**

```bash
pytest tests/test_modes_adherence.py::test_state_yaml_has_autonomy_fields -v
```

Expected: `FAILED` — `autonomy_requested` and `trigger_reason` not in `session`, `takeover` block missing.

**Step 2: Update `templates/STATE.yaml`**

Replace the entire content of `templates/STATE.yaml` with:

```yaml
# Bundlewizard Factory State
# Copied into the working directory at the start of a factory run.
# Updated by agents after each stage.
#
# Used as the shared bridge between manual and autonomous operation.
# Manual flow: the user or Amplifier updates fields between mode transitions.
# Autonomous flow: the post-explore recipe updates fields as each stage completes.
# Takeover: if autonomous flow leaves the golden path, the takeover section
#           describes what happened and where to re-enter manually.

session:
  id: ""                     # Session ID (auto-populated)
  started: ""                # ISO 8601 timestamp
  path: ""                   # "create_new" | "improve_existing" | "rebuild_from_reference"
  tier: ""                   # "behavior" | "bundle" | "application_bundle"
  target: ""                 # Bundle name (create) or path/URL (improve/rebuild)
  autonomy_requested: false  # Set true when autonomous continuation was opted in
  trigger_reason: ""         # Why autonomy was requested (e.g., "yolo", "amplifier-caller")
  open_questions: ""         # Unresolved questions from explore (must be empty before recipe runs)

stages:
  explore:
    status: pending          # pending | in_progress | completed | skipped
    completed_at: ""
    notes: ""
  spec:
    status: pending
    completed_at: ""
    spec_path: ""            # Path to bundle-spec.md
  plan:
    status: pending
    completed_at: ""
    plan_path: ""            # Path to implementation plan
  execute:
    status: pending
    completed_at: ""
    iterations: 0
    best_score: 0.0
    converged: false
  verify:
    status: pending          # pending | in_progress | completed | failed_verification | needs_takeover
    completed_at: ""
    level_1: ""              # PASS | FAIL
    level_2: 0.0
    level_3: 0.0
  finish:
    status: pending
    completed_at: ""
    delivery: ""             # merge | pr | keep | discard

convergence:
  current_iteration: 0
  max_iterations: 10
  patience_limit: 3
  patience_counter: 0
  best_checkpoint: ""        # Path to best-so-far artifacts
  history: []                # List of {iteration, level_1, level_2, level_3, notes}

takeover:
  status: ""                 # "" | "not_needed" | "paused" | "escalated"
  recommended_entry: ""      # "bundle-spec" | "bundle-plan" | "bundle-execute" | "bundle-debug" | "bundle-explore"
  explanation: ""            # Short explanation of why takeover is needed
  caller_notes: ""           # For Amplifier-as-caller: notes on suggested next action
```

**Step 3: Run the test to verify it passes**

```bash
pytest tests/test_modes_adherence.py::test_state_yaml_has_autonomy_fields -v
```

Expected: `PASSED`

**Step 4: Commit**

```bash
git add templates/STATE.yaml
git commit -m "feat: expand STATE.yaml with autonomy handoff and takeover contract

- Add session.autonomy_requested and session.trigger_reason
- Add session.open_questions for unresolved explore blockers
- Add takeover section with status, recommended_entry, explanation, caller_notes
- Add needs_takeover and failed_verification as valid verify stage statuses
- Document as shared bridge between manual and autonomous operation"
```

---

### Task 3: Repurpose `context/autonomous-protocol.md`

**Files:**
- Modify: `context/autonomous-protocol.md`

---

**Step 1: Verify the failing test**

```bash
pytest tests/test_modes_adherence.py::test_autonomous_protocol_is_recipe_policy -v
```

Expected: `FAILED` — file still contains behavioral override language and does not reference the new recipe.

**Step 2: Rewrite `context/autonomous-protocol.md`**

Replace the entire content with:

```markdown
# Autonomous Operation Protocol

This document is policy context for `bundle-autonomous-post-explore` — the continuation
recipe that runs after `bundle-explore` when autonomy was requested. It defines how the
recipe should operate, what quality gates it must enforce, how takeover signals work, and
what the audit trail must contain.

This is **not** a mode-level behavioral override. It applies only when the
`bundle-autonomous-post-explore` recipe is running.

## When This Applies

This protocol applies when:
- `bundle-explore` detected an explicit autonomy request (`yolo`, `autonomous`,
  `hands-off`, or Amplifier is the caller with enough context)
- The post-explore continuation recipe has been launched
- `STATE.yaml` has `autonomy_requested: true`

## Operator Flexibility

Explore always happens first, but the actor performing it may be either the user-facing
assistant or Amplifier itself. If Amplifier is the caller and already has enough context
to complete the explore phase, it should do so directly — it does not need to bounce back
to the user just because autonomy was requested.

"Explore" means resolve the problem framing, path, constraints, and target — not "go ask
a human." Ask the user only when information is genuinely missing.

## Golden Path Behavior

On the golden path, the recipe stays autonomous. Auto-transition between stages without
pausing for human confirmation. When triggering context is ambiguous, apply the most
capable reasonable interpretation and note it in `STATE.yaml`.

## Machine Quality Gates — Never Skippable

These are machine-enforced standards, not human checkpoints. They apply in all modes and
in all recipes.

| Gate | Threshold | Why It Cannot Be Skipped |
|------|-----------|--------------------------|
| Convergence loop (generate → critique → refine → evaluate) | Required | Quality. You skip human approval, not machine quality gates. |
| Structural validation (Level 1) | PASS | A bundle that doesn't load is worse than no bundle. |
| Philosophical validation (Level 2) | ≥0.85 | Thin pattern violations cause downstream problems. |
| Functional validation (Level 3) | ≥0.80 | A bundle that doesn't do its job has no value. |
| Version stamping | Required | Traceability for audit. |

If any gate fails its threshold, iterate. Do not ship a bundle that fails Level 1.

## Takeover Model

The autonomous recipe classifies outcomes into three buckets:

### 1. Continue autonomously
Normal spec/planning progress, expected refinement iterations, recoverable evaluator
feedback, standard finish behavior. Keep going.

### 2. Pause and offer takeover
Unresolved requirements, verification results that suggest a design decision is needed,
repeated refinement stalls, or packaging choices that may need judgment.

Action: Update `STATE.yaml` with `takeover.status: "paused"` and
`takeover.recommended_entry: <best re-entry point>` and a short explanation. Surface this
cleanly so the caller can decide to continue, ask the user, or switch to manual steering.

### 3. Escalate to manual or debug path
Broken assumptions, missing source material, contradictory requirements, or a state where
`bundle-debug` is the correct next step.

Action: Update `STATE.yaml` with `takeover.status: "escalated"` and
`takeover.recommended_entry: "bundle-debug"` (or the appropriate mode). Then return an
error so the recipe surfaces the escalation to its caller.

### Takeover is available, not forced

The default is "continue autonomously if possible." If Amplifier is the caller, Amplifier
itself can consume the takeover signal and decide whether to continue, ask the user for
input, or switch back to manual steering. The workflow does not need to bounce to the user
unless a real decision is needed.

## Audit Trail

Every bundle generated via autonomous continuation MUST include a `generated_by` block in
its `bundle.md` frontmatter:

```yaml
generated_by:
  tool: bundlewizard
  mode: autonomous
  triggered_by: <session_id>
  trigger_reason: <why autonomy was requested>
  convergence:
    iterations: <N>
    level_1: PASS
    level_2: <score>
    level_3: <score>
```

The `triggered_by` field is the session ID of the calling session. The `trigger_reason`
is the capability gap or explicit request that caused autonomous mode to be invoked.

## Return-to-Process Contract

When the bundle is complete, return to the calling session with:

- **What was built** — name, tier, location
- **What capability it provides** — one-paragraph summary
- **How to compose it** — the `includes:` stanza or mount instruction
- **Convergence summary** — iterations, final scores

If Amplifier is the caller: "I needed X capability, so I built it. Here's what I created:
[summary]. Continuing."

The calling session hot-composes the new bundle and resumes its work. The user sees a
completed capability, not an interruption.

## Wizard Identity Anchor

Autonomous mode is the wizard working unsupervised, not the wizard abandoning its craft.
The pipeline is the wizard's process. The quality gates are the wizard's standards.
Autonomous means the wizard is trusted to apply both without human checkpoints — not that
either is optional.
```

**Step 3: Run the test to verify it passes**

```bash
pytest tests/test_modes_adherence.py::test_autonomous_protocol_is_recipe_policy -v
pytest tests/test_modes_adherence.py::test_autonomous_protocol_exists -v
pytest tests/test_modes_adherence.py::test_autonomous_protocol_has_audit_trail -v
```

Expected: all three `PASSED` — the repurposed file satisfies the new test, keeps the `generated_by:` audit trail, and still exists at the expected path.

**Step 4: Commit**

```bash
git add context/autonomous-protocol.md
git commit -m "refactor: repurpose autonomous-protocol.md as recipe policy context

- Remove mode-level behavioral override instructions (old design artifact)
- Add recipe policy framing: applies only when post-explore recipe is running
- Add operator flexibility section (Amplifier-as-actor rule)
- Add golden path behavior, takeover model with 3 buckets
- Reference bundle-autonomous-post-explore as the policy target
- Preserve machine quality gates, audit trail schema, wizard identity anchor"
```

---

### Task 4: Update `modes/bundle-explore.md` to be the handoff gate

**Files:**
- Modify: `modes/bundle-explore.md`

---

**Step 1: Verify the failing test**

```bash
pytest tests/test_modes_adherence.py::test_explore_mode_is_handoff_gate -v
```

Expected: `FAILED` — file does not contain `autonomy_requested` or `bundle-autonomous-post-explore`.

**Step 2: Update `modes/bundle-explore.md`**

The YAML frontmatter at the top of the file does NOT change — do not touch lines 1–23.

Replace the **entire content from `BUNDLE-EXPLORE MODE:` to the end of the file** with the following:

```markdown
BUNDLE-EXPLORE MODE: Understand what the user needs before designing anything.

<CRITICAL>
THE HYBRID PATTERN: You handle the CONVERSATION. Investigation agents handle the RESEARCH.

Your role: Ask the user about their needs, discuss what they want to create, improve, or
rebuild, detect their experience level passively. This is interactive dialogue between you
and the user.

Agent roles:
- `bundlewizard:ecosystem-scout` — When you need to check if something similar exists or
  find reusable components
- `bundlewizard:bundle-auditor` — When the user points at an existing bundle for the
  "improve" path
- `amplifier:amplifier-expert` — When you need ecosystem knowledge

You CANNOT write files in this mode. write_file and edit_file are blocked. This mode is
for understanding, not creating.

AMPLIFIER-AS-ACTOR RULE: If Amplifier is the caller and already has enough context to
complete the explore phase, Amplifier should do so directly. Do NOT bounce back to the
user just because autonomy was requested. "Explore" means resolve the problem framing,
path, constraints, and target — not "go ask a human." Ask only when information is
genuinely missing.
</CRITICAL>

<HARD-GATE>
Do NOT delegate to any generation agent, invoke any generation recipe, OR transition to
bundle-spec OR launch bundle-autonomous-post-explore until you have:
1. Determined whether this is "create new," "improve existing," or "rebuild from reference"
2. Gathered enough context to write a meaningful spec
3. Resolved all open blockers (none remaining in open_questions)
4. Determined whether autonomy was requested

This applies to EVERY request regardless of perceived simplicity.
</HARD-GATE>

## Your Checklist

Track progress using the todo tool:

For **Create New**:
- [ ] What problem does this solve? Who uses it?
- [ ] Ecosystem check: does something similar exist? (delegate to ecosystem-scout)
- [ ] What tier? Behavior / Bundle / Application Bundle
- [ ] What capabilities? Agents, tools, modes, recipes, context
- [ ] What should delegate to existing experts vs carry itself?
- [ ] Autonomy requested? Detect from user vocabulary or Amplifier caller context
- [ ] All blockers resolved — ready for transition

For **Improve Existing**:
- [ ] Bundle identified (path or repo URL)
- [ ] Audit complete (delegate to bundle-auditor)
- [ ] Findings presented and discussed
- [ ] Improvements selected (all / critical / specific)
- [ ] New capabilities to add?
- [ ] Autonomy requested? Detect from user vocabulary or Amplifier caller context
- [ ] All blockers resolved — ready for transition

For **Rebuild from Reference**:
- [ ] Reference artifact identified (path, repo URL, or file)
- [ ] Delegate to bundle-auditor to analyze the reference artifact
- [ ] Determine what to keep, what to restructure, what to add
- [ ] Establish what the NEW bundle should do (vs what the reference does)
- [ ] What tier for the new bundle? Behavior / Bundle / Application Bundle
- [ ] Autonomy requested? Detect from user vocabulary or Amplifier caller context
- [ ] All blockers resolved — ready for transition

## Experience Detection

Detect experience level passively from vocabulary and adjust your depth:

**Experienced user signals:** Uses "behavior," "context sink," "thin pattern," references
specific bundles/modules by name, discusses architecture unprompted.
→ Accelerate: Skip fundamentals, ask about composition decisions and architecture.

**Newcomer signals:** Describes outcome not mechanism ("I want something that does X"),
no bundle vocabulary, asks what terms mean.
→ Guide: Explain what a bundle is, show tier examples, translate their outcome into bundle
concepts.

Never ask "are you experienced?" — detect and adapt.

## Handoff Payload

Before transitioning, resolve these fields. They become the input to either the next
manual mode or the autonomous continuation recipe:

```yaml
path_decision: ""          # "create_new" | "improve_existing" | "rebuild_from_reference"
target: ""                 # Bundle name (create) or path/URL (improve/rebuild)
tier: ""                   # "behavior" | "bundle" | "application_bundle"
summary_of_requirements: "" # What was learned in explore
known_constraints: ""      # Constraints discovered (scope limits, dependencies, etc.)
autonomy_requested: false  # True if user or Amplifier caller requested autonomy
trigger_reason: ""         # Why autonomy was requested (e.g., "yolo", "amplifier-caller")
open_questions: ""         # Any remaining unresolved questions (must be empty before launch)
```

## Transition

When exploration is complete and all blockers are resolved, check `autonomy_requested`:

### Default path (no autonomy requested)

Auto-transition to bundle-spec:
```
mode(operation='set', name='bundle-spec')
```
Do NOT ask the user to type /bundle-spec — transition automatically.

### Opt-in autonomous path (autonomy was requested)

If `autonomy_requested` is true AND `open_questions` is empty, launch the post-explore
continuation recipe instead:
```
recipes(operation='execute',
        recipe_path='bundlewizard:recipes/bundle-autonomous-post-explore.yaml',
        context={
          "path_decision": "<resolved>",
          "target": "<resolved>",
          "tier": "<resolved>",
          "summary_of_requirements": "<resolved>",
          "known_constraints": "<resolved>",
          "trigger_reason": "<resolved>",
          "open_questions": "",
          "output_dir": "output"
        })
```
Do NOT transition to bundle-spec when launching the recipe. The recipe owns the
continuation.

### If autonomy was requested but open_questions is non-empty

Stay in explore. Resolve the blockers before launching. The recipe cannot safely proceed
with unresolved blockers.
```

**Step 3: Run the test to verify it passes**

```bash
pytest tests/test_modes_adherence.py::test_explore_mode_is_handoff_gate -v
pytest tests/test_modes_adherence.py::test_pipeline_mode_transitions -v
pytest tests/test_modes_adherence.py::test_pipeline_mode_allow_clear -v
```

Expected: all three `PASSED`. The transition test still passes because the YAML frontmatter (which it reads) was not changed.

**Step 4: Commit**

```bash
git add modes/bundle-explore.md
git commit -m "feat: bundle-explore becomes the handoff gate for post-explore autonomy

- Add AMPLIFIER-AS-ACTOR rule (Amplifier performs explore when it has enough context)
- Add autonomy_requested detection to all three path checklists
- Add structured handoff payload section with all 7 required fields
- Add conditional Transition section:
  - Default: auto-transition to bundle-spec (unchanged)
  - Opt-in: launch bundle-autonomous-post-explore recipe with full handoff payload
  - Blocked: stay in explore until open_questions is empty
- Update HARD-GATE to cover both recipe launch and bundle-spec transition"
```

---

## Phase 3 — Build the Autonomous Continuation Engine

### Task 5: Create `recipes/bundle-autonomous-post-explore.yaml`

**Files:**
- Create: `recipes/bundle-autonomous-post-explore.yaml`

---

**Step 1: Verify the failing tests**

```bash
pytest tests/test_modes_adherence.py::test_autonomous_post_explore_recipe_exists -v
pytest tests/test_modes_adherence.py::test_autonomous_post_explore_recipe_stages -v
pytest tests/test_modes_adherence.py::test_autonomous_post_explore_recipe_no_required_approval_gates -v
pytest tests/test_modes_adherence.py::test_autonomous_post_explore_recipe_reuses_refinement_loop -v
```

Expected: all four `FAILED` (skipping would also be acceptable for the stage/gates/loop tests since the file doesn't exist yet).

**Step 2: Create `recipes/bundle-autonomous-post-explore.yaml`**

Create this new file with the following content:

```yaml
# Bundle Autonomous Post-Explore Continuation
# Autonomous continuation recipe for bundlewizard.
#
# This recipe runs AFTER bundle-explore completes when autonomy was requested.
# It owns the full continuation: spec → plan → execute → verify → finish.
# No human approval gates — machine quality gates are fully enforced.
# Takeover is offered (not forced) if the workflow leaves the golden path.
#
# Pattern: mirrors bundle-development-cycle.yaml (interactive gated cycle) but
# removes forced approval gates and adds STATE.yaml-based takeover semantics.
# Reuses bundle-refinement-loop for execution — no duplicated convergence logic.
#
# Autonomy policy: @bundlewizard:context/autonomous-protocol.md
#
# Context variables = structured handoff payload from bundle-explore:
#   path_decision           — "create_new" | "improve_existing" | "rebuild_from_reference"
#   target                  — bundle name (create) or path/URL (improve/rebuild)
#   tier                    — "behavior" | "bundle" | "application_bundle"
#   summary_of_requirements — what explore resolved
#   known_constraints       — constraints discovered during explore
#   trigger_reason          — why autonomy was requested
#   open_questions          — unresolved questions (must be empty when recipe launches)
#   output_dir              — where to write generated artifacts
#
# Usage (launched by bundle-explore after autonomy detection):
#   recipes(operation='execute',
#           recipe_path='bundlewizard:recipes/bundle-autonomous-post-explore.yaml',
#           context={...handoff payload...})

name: "bundle-autonomous-post-explore"
description: >
  Autonomous continuation recipe — spec → plan → execute → verify → finish after
  bundle-explore. No approval gates; machine quality gates fully enforced. Takeover
  offered (not forced) if the workflow leaves the golden path.
version: "1.0.0"
author: "Bundlewizard Bundle"
tags:
  - bundle
  - autonomous
  - post-explore
  - continuation
  - no-approval-gates

context:
  path_decision: ""             # Required: "create_new" | "improve_existing" | "rebuild_from_reference"
  target: ""                    # Required: bundle name (create) or path/URL (improve/rebuild)
  tier: ""                      # Required: "behavior" | "bundle" | "application_bundle"
  summary_of_requirements: ""   # Required: what explore resolved
  known_constraints: ""         # Optional: constraints discovered during explore
  trigger_reason: ""            # Why autonomy was requested
  open_questions: ""            # Unresolved questions — must be empty before recipe proceeds
  output_dir: "output"          # Where to write generated artifacts

stages:
  # ============================================================================
  # STAGE 1: Spec
  # Write the bundle specification from the explore handoff payload.
  # No approval gate — agent proceeds directly without human input.
  # Takeover: if open_questions are blockers, agent sets STATE.yaml takeover
  #           status and returns an error rather than guessing dangerously.
  # ============================================================================
  - name: "spec"
    steps:
      - id: "write-spec"
        agent: "bundlewizard:bundle-spec-writer"
        prompt: |
          Produce a concrete bundle specification from the explore handoff payload.
          This is autonomous operation — do not ask the user for input.

          Autonomy policy: @bundlewizard:context/autonomous-protocol.md

          HANDOFF PAYLOAD:
          - Path decision: {{path_decision}}
          - Target: {{target}}
          - Tier: {{tier}}
          - Requirements summary: {{summary_of_requirements}}
          - Known constraints: {{known_constraints}}
          - Open questions: {{open_questions}}

          OUTPUT DIR: {{output_dir}}

          IMPORTANT: If open_questions is non-empty, assess each question:
          - If it is NOT a blocker: apply the most capable reasonable interpretation.
            Note your decision in STATE.yaml stages.spec.notes.
          - If it IS a blocker: update STATE.yaml with
              takeover.status: "paused"
              takeover.recommended_entry: "bundle-explore"
              takeover.explanation: "<what needs resolution>"
            Then return an error.

          Create the specification at: {{output_dir}}/bundle-spec.md

          The specification MUST include:
          - Output tier: behavior | bundle | application-bundle
          - Complete file structure (tree diagram of all files)
          - Component design: agents, behaviors, context files, modes, recipes
          - Delegation map: which existing experts handle which concerns
          - Convergence expectations: Level 1 gates, Level 2 targets, Level 3 criteria
          - For improve/rebuild paths: ordered list of changes from audit findings

          Delegate to foundation:foundation-expert to validate the composition.

          Update STATE.yaml:
            stages.spec.status: "completed"
            stages.spec.spec_path: <path>
            stages.spec.completed_at: <timestamp>

          Return the spec file path.
        output: "spec_path"
        timeout: 600
        on_error: "continue"

  # ============================================================================
  # STAGE 2: Plan
  # Create the implementation plan from the approved spec.
  # No approval gate — agent proceeds directly without human input.
  # Takeover: if spec_path is empty (spec stage failed), agent escalates.
  # ============================================================================
  - name: "plan"
    steps:
      - id: "write-plan"
        agent: "bundlewizard:bundle-plan-writer"
        prompt: |
          Create an implementation plan from the bundle specification.
          This is autonomous operation — do not ask the user for input.

          Autonomy policy: @bundlewizard:context/autonomous-protocol.md

          PATH DECISION: {{path_decision}}
          TIER: {{tier}}
          OUTPUT DIR: {{output_dir}}
          SPEC: {{spec_path}}

          First, verify spec_path is non-empty and the file exists.
          If spec_path is empty or the spec file cannot be read:
          - Update STATE.yaml:
              takeover.status: "escalated"
              takeover.recommended_entry: "bundle-spec"
              takeover.explanation: "spec stage did not produce a readable spec file"
          - Return an error.

          Produce a concrete implementation plan at: {{output_dir}}/bundle-plan.md

          The plan MUST include:
          - File-by-file generation order (create) or ordered renovation tasks (improve)
          - Dependencies between files (what must exist before what)
          - For each file: exact path, what it should contain, validation check
          - Estimated number of convergence iterations

          Update STATE.yaml:
            stages.plan.status: "completed"
            stages.plan.plan_path: <path>
            stages.plan.completed_at: <timestamp>

          Return the plan file path.
        output: "plan_path"
        timeout: 600
        on_error: "continue"

  # ============================================================================
  # STAGE 3: Execute
  # Invokes bundle-refinement-loop as a sub-recipe.
  # REUSES the existing convergence machinery — no duplication.
  # No approval gate — the loop runs to convergence.
  # ============================================================================
  - name: "execute"
    steps:
      - id: "run-refinement-loop"
        type: recipe
        recipe: "bundlewizard:recipes/bundle-refinement-loop.yaml"
        context:
          spec_path: "{{spec_path}}"
          plan_path: "{{plan_path}}"
          output_path: "{{output_dir}}/bundle"
          converged: "false"
          iteration: "0"
        output: "refinement_result"
        timeout: 3600
        on_error: "continue"

  # ============================================================================
  # STAGE 4: Verify
  # Independent three-level evaluation (same evaluator as development-cycle).
  # No forced approval gate — machine gates still fully enforced.
  # If thresholds are not met, STATE.yaml is updated with needs_takeover and
  # the caller decides whether to iterate, ask the user, or switch to manual.
  # ============================================================================
  - name: "verify"
    steps:
      - id: "run-verification"
        agent: "bundlewizard:bundle-evaluator"
        prompt: |
          Run independent verification of the generated bundle.
          This is autonomous operation — do not ask the user for input.

          Autonomy policy: @bundlewizard:context/autonomous-protocol.md

          PATH DECISION: {{path_decision}}
          SPEC: {{spec_path}}
          BUNDLE PATH: {{output_dir}}/bundle
          REFINEMENT RESULT: {{refinement_result}}

          This is INDEPENDENT verification — fresh eyes, not the same evaluation
          that ran during the convergence loop.

          Evaluate against all three levels:

          Level 1 (Structural): All pass/fail gates from convergence-criteria.md.
          - Does bundle.md parse? Do agent references resolve? Are URIs valid?
          - Any duplicate context loading? Mode files discoverable?

          Level 2 (Philosophical): Score each of the 4 criteria. Threshold: 0.85.
          - Thin bundle pattern, context sink discipline, agent description quality,
            composition hygiene.
          - Delegate to foundation:foundation-expert for authoritative checks.

          Level 3 (Functional): Does the bundle achieve its stated purpose? Threshold: 0.80.
          - Delegate to the appropriate domain expert for functional assessment.

          After evaluation, update STATE.yaml based on outcome:

          ALL levels pass thresholds:
            stages.verify.status: "completed"
            stages.verify.level_1: "PASS"
            stages.verify.level_2: <score>
            stages.verify.level_3: <score>
            takeover.status: "not_needed"

          Level 1 FAILS:
            stages.verify.status: "failed_verification"
            takeover.status: "paused"
            takeover.recommended_entry: "bundle-execute"
            takeover.explanation: "Level 1 structural check failed: <details>"
            Return an error.

          Level 2 or 3 below threshold:
            stages.verify.status: "needs_takeover"
            takeover.status: "paused"
            takeover.recommended_entry: "bundle-execute"
            takeover.explanation: "Scores below threshold — L2: <score>, L3: <score>. <details>"
            Return the report (do NOT return an error — let finish surface the takeover).

          Return a verification report including:
          - Level 1: PASS/FAIL with details for each gate
          - Level 2: scored rubric
          - Level 3: scored assessment
          - Overall: CONVERGED or NOT CONVERGED
          - Recommendation: SHIP IT or NEEDS MORE WORK
        output: "verification_report"
        timeout: 900
        on_error: "continue"

  # ============================================================================
  # STAGE 5: Finish
  # Package and deliver the verified bundle.
  # No forced approval gate — agent checks STATE.yaml before proceeding.
  # If STATE.yaml shows takeover.status is paused/escalated, agent surfaces
  # a structured handoff instead of packaging. This gives the caller
  # (user or Amplifier) all the information needed to decide next steps.
  # ============================================================================
  - name: "finish"
    steps:
      - id: "package-bundle"
        agent: "bundlewizard:bundle-packager"
        prompt: |
          Package the bundle for delivery, or surface a structured takeover if needed.
          This is autonomous operation — do not ask the user for input unless a real
          decision requires it.

          Autonomy policy: @bundlewizard:context/autonomous-protocol.md

          BUNDLE PATH: {{output_dir}}/bundle
          OUTPUT DIR: {{output_dir}}
          PATH DECISION: {{path_decision}}
          SPEC: {{spec_path}}
          VERIFICATION REPORT: {{verification_report}}
          TRIGGER REASON: {{trigger_reason}}

          STEP 1: Read STATE.yaml and check takeover.status.

          If takeover.status is "paused" or "escalated":
          - Do NOT package the bundle.
          - Return a structured takeover summary:
              current_stage: <from STATE.yaml>
              recommended_entry: <from STATE.yaml takeover.recommended_entry>
              explanation: <from STATE.yaml takeover.explanation>
              artifacts_available:
                spec_path: {{spec_path}}
                plan_path: {{plan_path}}
                bundle_path: {{output_dir}}/bundle (if execute stage reached)
              caller_notes: >
                "Autonomous continuation paused. Resume from <recommended_entry>
                 or review the explanation and decide next steps."
          - Update STATE.yaml stages.finish.status: "needs_takeover"
          - Return this summary. Do not treat this as an error — it is a clean handoff.

          If takeover.status is empty, "not_needed", or not set:
          - Proceed with packaging.

          STEP 2 (packaging only): Add generated_by block to bundle.md frontmatter.
          See autonomous-protocol.md for the required schema. Include:
            tool: bundlewizard
            mode: autonomous
            triggered_by: <session ID>
            trigger_reason: {{trigger_reason}}
            convergence: <from verification report>

          STEP 3 (packaging only): Generate or update README.md with usage instructions.

          STEP 4 (packaging only — create_new path):
            git init (if not already a repo)
            git add .
            git commit -m "feat: initial bundle generation by bundlewizard"
            Default delivery: keep (locally available)

          STEP 4 (packaging only — improve_existing or rebuild_from_reference path):
            git checkout -b bundlewizard/improvements
            git add .
            git commit -m "feat: bundle improvements by bundlewizard"
            Default delivery: keep (branch ready — caller can merge or open PR)

          STEP 5 (packaging only): Update STATE.yaml:
            stages.finish.status: "completed"
            stages.finish.completed_at: <timestamp>
            stages.finish.delivery: <delivery option>
            takeover.status: "not_needed"

          Return a completion summary:
          - Final artifact paths
          - Convergence scores achieved
          - How to use this bundle
          - Delivery option chosen
          - If Amplifier is the caller: include the hot-compose stanza
            (includes: block the calling session needs to mount this bundle)
        output: "completion_summary"
        timeout: 600
        on_error: "continue"
```

**Step 3: Run all four new recipe tests**

```bash
pytest tests/test_modes_adherence.py::test_autonomous_post_explore_recipe_exists -v
pytest tests/test_modes_adherence.py::test_autonomous_post_explore_recipe_stages -v
pytest tests/test_modes_adherence.py::test_autonomous_post_explore_recipe_no_required_approval_gates -v
pytest tests/test_modes_adherence.py::test_autonomous_post_explore_recipe_reuses_refinement_loop -v
```

Expected: all four `PASSED`

**Step 4: Commit**

```bash
git add recipes/bundle-autonomous-post-explore.yaml
git commit -m "feat: add bundle-autonomous-post-explore recipe

- Autonomous continuation recipe: spec → plan → execute → verify → finish
- No human approval gates; machine quality gates fully enforced
- Reuses bundle-refinement-loop for execution (no convergence duplication)
- STATE.yaml-based takeover model:
  - paused: offered for unresolved requirements, score misses, stall
  - escalated: hard failure requiring bundle-debug or bundle-explore restart
- Finish stage surfaces structured handoff instead of packaging when takeover is set
- Amplifier-as-caller support: hot-compose stanza returned on completion
- Input contract: structured handoff payload from bundle-explore"
```

---

### Task 6: Update `recipes/bundle-development-cycle.yaml` to clarify coexistence

**Files:**
- Modify: `recipes/bundle-development-cycle.yaml` (header comments only)

---

**Step 1: Update the header comment block**

Open `recipes/bundle-development-cycle.yaml`. Replace the existing header comment block (lines 1–23) with:

```yaml
# Bundle Development Cycle
# Full INTERACTIVE cycle with 3 human approval gates: explore → spec → plan → execute → verify → finish.
#
# This is the GATED track. Each stage requires human review and approval before proceeding.
# Use this when you want hands-on control at every critical juncture.
#
# For the AUTONOMOUS track (no approval gates, post-explore recipe):
#   use bundlewizard:recipes/bundle-autonomous-post-explore.yaml
#   launched automatically by bundle-explore when autonomy is requested
#
# Pattern: staged recipe with human checkpoints.
# Each stage has a defined job; approval gates let the human validate at critical junctures.
#
# Stages:
#   1. exploration  — bundle-explorer + bundle-spec-writer           → APPROVAL GATE
#   2. planning     — bundle-plan-writer                             → APPROVAL GATE
#   3. execution    — invokes bundle-refinement-loop sub-recipe      (no gate — let it run)
#   4. verification — bundle-evaluator independent assessment        → APPROVAL GATE
#   5. completion   — bundle-packager delivers the artifact
#
# Context variables:
#   bundle_description — What the user wants (e.g., "a bundle that helps with code review")
#   output_dir         — Where to put generated artifacts (e.g., "~/dev/my-new-bundle")
#   path               — "create" for new bundles, or a filesystem path/URL for improve mode
#
# Usage:
#   amplifier run "execute bundlewizard:recipes/bundle-development-cycle.yaml
#     with bundle_description='a bundle that helps with code review'
#     output_dir='~/dev/amplifier-bundle-code-review'
#     path='create'"
```

**Step 2: Run the full test suite to confirm no regressions**

```bash
pytest tests/test_modes_adherence.py -v
```

Expected: all tests pass. No new failures from this change.

**Step 3: Commit**

```bash
git add recipes/bundle-development-cycle.yaml
git commit -m "docs: clarify bundle-development-cycle is the interactive gated track

- Distinguish from bundle-autonomous-post-explore (autonomous track)
- Header now explains the two-track relationship explicitly
- No structural changes — comments only"
```

---

## Phase 4 — Polish the Shipped Surface

### Task 7: Update `bundle.md`

**Files:**
- Modify: `bundle.md`

---

**Step 1: Replace `bundle.md` content**

Replace the entire content with:

```markdown
---
bundle:
  name: bundlewizard
  version: 0.1.0
  description: |
    Bundle generation and improvement factory for the Amplifier ecosystem.
    Generates new bundles and improves existing ones through structured
    interview + iterative convergence using the factory pattern.

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: bundlewizard:behaviors/bundlewizard
---

# Bundlewizard

Bundle generation and improvement factory. Two paths: create new bundles or improve
existing ones. Default flow is interactive and manual. Autonomous continuation is opt-in
after exploration.

## Modes

| Shortcut | Phase | What Happens |
|----------|-------|--------------|
| `/bundle-explore` | Interview | Understand what you need, route to create or improve — or launch autonomous continuation |
| `/bundle-spec` | Design | Compose the bundle specification |
| `/bundle-plan` | Planning | Break spec into implementation tasks |
| `/bundle-execute` | Generation | Convergence loop: generate → critique → refine → evaluate |
| `/bundle-verify` | Verification | Collect evidence that the bundle works |
| `/bundle-finish` | Delivery | Package, version stamp, deliver |
| `/bundle-debug` | Off-ramp | Diagnose issues at any stage |

## Two Tracks

**Modes are the steering wheel. Recipes are cruise control.**

| Track | How | Best For |
|-------|-----|----------|
| **Interactive** (default) | Navigate modes manually: `/bundle-explore` → `/bundle-spec` → ... | Hands-on sessions, control at each step |
| **Autonomous** (opt-in) | Request autonomy during explore; `bundle-explore` launches the post-explore recipe automatically | End-to-end generation without manual checkpoints |

Both tracks produce the same output. The autonomous track just removes the human
checkpoints after exploration is complete.

## Recipes

| Recipe | Track | What It Does |
|--------|-------|--------------|
| `bundle-autonomous-post-explore.yaml` | Autonomous | Continues after explore: spec → plan → execute → verify → finish. No approval gates. |
| `bundle-development-cycle.yaml` | Interactive | Full pipeline with 3 human approval gates. |
| `bundle-audit.yaml` | Standalone | Audit an existing bundle without full regeneration. |
| `bundle-batch-generation.yaml` | Standalone | Generate multiple bundles from a target list. |

## Getting Started

Say what you want to build, or point me at a bundle to improve. I'll figure out the rest.

To go fully autonomous, add `"go autonomous"`, `"yolo"`, or `"run it all"` to your
request. Exploration still happens first — autonomous continuation begins after.
```

**Step 2: Run the full test suite**

```bash
pytest tests/test_modes_adherence.py -v
```

Expected: all tests pass.

**Step 3: Commit**

```bash
git add bundle.md
git commit -m "docs: update bundle.md with two-track UX and autonomous recipe entry

- Add Two Tracks section: interactive (default) vs autonomous (opt-in)
- Add recipes table with track column and coexistence notes
- Update mode table to reflect explore-as-handoff-gate role
- Add getting started note for autonomous opt-in vocabulary"
```

---

### Task 8: Update `context/instructions.md`

**Files:**
- Modify: `context/instructions.md`

---

**Step 1: Verify the failing test**

```bash
pytest tests/test_modes_adherence.py::test_instructions_describes_opt_in_autonomy -v
```

Expected: `FAILED` — `bundle-autonomous-post-explore` not yet referenced in the file.

**Step 2: Update the Two-Track UX section**

Open `context/instructions.md`. Locate the `## Two-Track UX` section (currently lines 85–92). Replace that section and the `## Experience Detection` heading block with:

```markdown
## Two-Track UX

**Modes are the steering wheel. Recipes are cruise control.**

| Track | How | Best For |
|-------|-----|----------|
| **Interactive** (default) | Navigate modes manually: `/bundle-explore` → `/bundle-spec` → ... | Hands-on sessions, control at each step |
| **Autonomous** (opt-in) | Request autonomy during explore; `bundle-explore` launches `bundle-autonomous-post-explore.yaml` | End-to-end generation without manual checkpoints |

Both tracks produce the same output. The autonomous track removes human checkpoints after
exploration is complete.

### Autonomous opt-in rules

- Autonomy is **always opt-in**. The default is interactive.
- Autonomy detection happens inside `bundle-explore`. Vocabulary signals: `"yolo"`,
  `"go autonomous"`, `"run it all"`, `"hands-off"`.
- Amplifier-as-caller: if Amplifier is the caller and has enough context, it may perform
  the explore phase directly and then launch the continuation recipe without bouncing back
  to the user.
- Once autonomy starts, it stays autonomous by default. Takeover is offered — not forced
  — if the workflow leaves the golden path.
- The post-explore recipe owns: `bundle-spec` → `bundle-plan` → `bundle-execute` →
  `bundle-verify` → `bundle-finish`.
- `STATE.yaml` is the shared bridge between manual and autonomous operation. It records
  current stage, status, latest outputs, and takeover signals.

### Interactive gated track

For full manual control with human approval gates at every critical juncture, use:
`bundlewizard:recipes/bundle-development-cycle.yaml`

This is the right choice when you want to review the spec before planning starts and
review the plan before generation begins.
```

**Step 3: Run the test and the full suite**

```bash
pytest tests/test_modes_adherence.py::test_instructions_describes_opt_in_autonomy -v
pytest tests/test_modes_adherence.py -v
```

Expected: `test_instructions_describes_opt_in_autonomy` now `PASSED`. Full suite: all tests pass.

**Step 4: Commit**

```bash
git add context/instructions.md
git commit -m "docs: update instructions.md with opt-in autonomy after explore

- Replace Two-Track UX section with modes=steering-wheel / recipes=cruise-control framing
- Add explicit autonomous opt-in rules (vocabulary signals, Amplifier-as-caller rule)
- Reference bundle-autonomous-post-explore.yaml as the autonomous track entry
- Reference STATE.yaml as the shared bridge
- Distinguish interactive gated track (bundle-development-cycle.yaml) clearly"
```

---

### Task 9: Final validation

**Files:**
- No file changes — this is verification only.

---

**Step 1: Run the complete test suite**

```bash
pytest tests/test_modes_adherence.py -v
```

Expected output — all tests PASSED:
```
PASSED test_bundle_bot_does_not_exist
PASSED test_pipeline_modes_exist
PASSED test_pipeline_mode_transitions
PASSED test_pipeline_mode_allow_clear
PASSED test_autonomous_behavior_does_not_exist
PASSED test_state_yaml_has_autonomy_fields
PASSED test_autonomous_protocol_is_recipe_policy
PASSED test_explore_mode_is_handoff_gate
PASSED test_autonomous_post_explore_recipe_exists
PASSED test_autonomous_post_explore_recipe_stages
PASSED test_autonomous_post_explore_recipe_no_required_approval_gates
PASSED test_autonomous_post_explore_recipe_reuses_refinement_loop
PASSED test_autonomous_protocol_exists
PASSED test_autonomous_protocol_has_audit_trail
PASSED test_instructions_no_bundle_bot
PASSED test_instructions_describes_opt_in_autonomy
```

If any test fails, do not continue — investigate and fix before the final commit.

**Step 2: Regression check — no product file references the deleted behavior**

```bash
grep -r "bundlewizard-autonomous" . \
  --include="*.md" --include="*.yaml" --include="*.py" \
  --exclude-dir=".git" --exclude-dir="amplifier-bundle-modes" \
  --exclude-dir="amplifier-bundle-superpowers" \
  --exclude-dir="docs"
```

Expected: no output. If any matches appear in product files (not docs/plans), fix them.

**Step 3: Regression check — no product file references `hooks-mode.autonomous`**

```bash
grep -r "hooks-mode.autonomous\|autonomous: true" . \
  --include="*.yaml" \
  --exclude-dir=".git" --exclude-dir="amplifier-bundle-modes" \
  --exclude-dir="amplifier-bundle-superpowers"
```

Expected: no output. If matches appear in behaviors/ or recipes/, fix them.

**Step 4: Verify the shipped behavior surface**

```bash
ls behaviors/
```

Expected: only `bundlewizard.yaml`. No `bundlewizard-autonomous.yaml`.

**Step 5: Verify the recipe surface**

```bash
ls recipes/
```

Expected: `bundle-audit.yaml`, `bundle-autonomous-post-explore.yaml`,
`bundle-batch-generation.yaml`, `bundle-development-cycle.yaml`,
`bundle-refinement-loop.yaml`, `bundle-single-iteration.yaml`.

**Step 6: Final commit**

```bash
git add -A
git commit -m "chore: final validation — post-explore autonomy implementation complete

All 16 structural tests pass. No product files reference deleted upstream-dependent
artifacts. Shipped surface: one behavior (bundlewizard.yaml), manual mode stack unchanged,
one autonomous continuation recipe (bundle-autonomous-post-explore.yaml)."
```

---

## Completion Checklist

Before calling this done, verify every item:

- [ ] `behaviors/bundlewizard-autonomous.yaml` deleted from the repo
- [ ] `behaviors/bundlewizard.yaml` is the only shipped behavior (unchanged)
- [ ] `recipes/bundle-autonomous-post-explore.yaml` created with 5 stages and no required approval gates
- [ ] `recipes/bundle-autonomous-post-explore.yaml` invokes `bundle-refinement-loop` for execution
- [ ] `modes/bundle-explore.md` detects `autonomy_requested` and conditionally launches the recipe
- [ ] `context/autonomous-protocol.md` is recipe policy context, not a behavioral override
- [ ] `templates/STATE.yaml` has `autonomy_requested`, `trigger_reason`, `open_questions` in session block
- [ ] `templates/STATE.yaml` has `takeover` section with `status`, `recommended_entry`, `explanation`
- [ ] `bundle.md` describes the two-track UX and references the new recipe
- [ ] `context/instructions.md` describes opt-in autonomy-after-explore and references the new recipe
- [ ] `recipes/bundle-development-cycle.yaml` header clarifies it is the interactive gated track
- [ ] All 16 tests in `tests/test_modes_adherence.py` pass
- [ ] No product files reference `bundlewizard-autonomous` or `hooks-mode.autonomous: true`
- [ ] No changes outside `amplifier-bundle-bundlewizard/` (do not commit changes in `amplifier-bundle-modes/`)

---

## What Was NOT Changed (Intentionally)

- `modes/bundle-spec.md` — unchanged; manual flow is default and correct
- `modes/bundle-plan.md` — unchanged
- `modes/bundle-execute.md` — unchanged
- `modes/bundle-verify.md` — unchanged
- `modes/bundle-finish.md` — unchanged
- `modes/bundle-debug.md` — unchanged
- `behaviors/bundlewizard.yaml` — unchanged; it is the only shipped behavior
- `recipes/bundle-refinement-loop.yaml` — unchanged; reused by the new recipe
- `recipes/bundle-single-iteration.yaml` — unchanged; reused via refinement loop
- `recipes/bundle-audit.yaml` — unchanged
- `recipes/bundle-batch-generation.yaml` — unchanged
- `agents/*.md` — unchanged; same agents serve both tracks
- `context/philosophy.md`, `context/factory-protocol.md`, `context/convergence-criteria.md` — unchanged
- `amplifier-bundle-modes/` submodule — not touched; it is scratch/reference only

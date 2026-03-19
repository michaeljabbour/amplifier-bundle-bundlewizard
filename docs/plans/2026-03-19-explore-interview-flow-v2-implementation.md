# Explore Interview Flow v2: Four-Path Routing — Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Add Path D: Design My Experience as a fourth routing path to the bundlewizard's explore interview flow, with D1/D2/D3 sub-routing and experience_lens redirect to Path C.

**Architecture:** Three existing markdown files change, one recipe YAML gains two new context fields, one new test file is created. No new agents, modes, recipes, or context files. All four paths converge at the same shared handoff block. D3 redirects to Path C with an `experience_lens` flag to avoid logic duplication.

**Tech Stack:** Markdown (agent/mode/context files), YAML (recipe context), Python/pytest (structural contract tests)

**Design doc:** `docs/plans/2026-03-19-explore-interview-flow-v2-design.md`

---

## Task 1: Write Tests for Four-Path Routing

**Files:**
- Create: `tests/test_four_path_routing.py`

All tests will fail initially because the source files haven't been modified yet. This is the TDD red phase — we write all the tests first, then implement across Tasks 2–5.

**Step 1: Create the test file**

Create `tests/test_four_path_routing.py` with the following complete content:

```python
"""Structural contract tests for four-path routing (Path D: Design My Experience).

These tests verify:
- context/instructions.md has been updated from three-path to four-path
- modes/bundle-explore.md has the Design My Experience checklist and handoff fields
- agents/bundle-explorer.md has Path D signals, disambiguation, and D1/D2/D3 interviews
- recipes/bundle-autonomous-post-explore.yaml has experience design context fields
"""

import re
from pathlib import Path

import pytest

# Repo root — tests/ is a direct child of the repo root
REPO_ROOT = Path(__file__).parent.parent
MODES_DIR = REPO_ROOT / "modes"
AGENTS_DIR = REPO_ROOT / "agents"
CONTEXT_DIR = REPO_ROOT / "context"
RECIPES_DIR = REPO_ROOT / "recipes"


# ---------------------------------------------------------------------------
# context/instructions.md
# ---------------------------------------------------------------------------


def test_instructions_has_four_path_heading():
    """context/instructions.md must use 'Four-Path Routing Fork' heading."""
    path = CONTEXT_DIR / "instructions.md"
    assert path.exists(), "context/instructions.md does not exist"
    content = path.read_text(encoding="utf-8")
    assert "Four-Path Routing Fork" in content, (
        "instructions.md must rename 'Three-Path' to 'Four-Path Routing Fork'"
    )
    assert "Three-Path Routing Fork" not in content, (
        "instructions.md must not retain the old 'Three-Path Routing Fork' heading"
    )


def test_instructions_has_path_d_signals():
    """context/instructions.md must list Path D signal phrases."""
    path = CONTEXT_DIR / "instructions.md"
    content = path.read_text(encoding="utf-8")
    assert "customize my amplifier" in content.lower(), (
        "instructions.md must include 'customize my amplifier' as a Path D signal"
    )
    assert "design my experience" in content.lower(), (
        "instructions.md must include 'design my experience' as a Path D signal"
    )


def test_instructions_has_path_d_interview_flow():
    """context/instructions.md must describe Path D: Design My Experience flow."""
    path = CONTEXT_DIR / "instructions.md"
    content = path.read_text(encoding="utf-8")
    assert "Path D" in content, (
        "instructions.md must have a 'Path D' section"
    )
    assert "Design My Experience" in content, (
        "instructions.md must reference 'Design My Experience' as Path D's name"
    )


# ---------------------------------------------------------------------------
# modes/bundle-explore.md
# ---------------------------------------------------------------------------


def test_explore_mode_has_path_d_checklist():
    """modes/bundle-explore.md must have a 'Design My Experience' checklist."""
    path = MODES_DIR / "bundle-explore.md"
    assert path.exists(), "modes/bundle-explore.md does not exist"
    content = path.read_text(encoding="utf-8")
    assert "Design My Experience" in content, (
        "bundle-explore.md must have a 'Design My Experience' checklist section"
    )


def test_explore_mode_has_experience_design_handoff_fields():
    """modes/bundle-explore.md handoff payload must contain experience design fields."""
    path = MODES_DIR / "bundle-explore.md"
    content = path.read_text(encoding="utf-8")
    assert "design_my_experience" in content, (
        "bundle-explore.md handoff payload must include 'design_my_experience' as a path_decision value"
    )
    assert "experience_sub_path" in content, (
        "bundle-explore.md handoff payload must include 'experience_sub_path' field"
    )
    assert "experience_lens" in content, (
        "bundle-explore.md handoff payload must include 'experience_lens' field"
    )


# ---------------------------------------------------------------------------
# agents/bundle-explorer.md
# ---------------------------------------------------------------------------


def test_explorer_agent_has_path_d_signals():
    """agents/bundle-explorer.md must detect Path D signal phrases."""
    path = AGENTS_DIR / "bundle-explorer.md"
    assert path.exists(), "agents/bundle-explorer.md does not exist"
    content = path.read_text(encoding="utf-8")
    assert "Design My Experience" in content, (
        "bundle-explorer.md must reference 'Design My Experience' as a routing path"
    )
    assert re.search(r"customize.*experience|design.*experience", content, re.IGNORECASE), (
        "bundle-explorer.md must include experience-customization signal phrases in the routing table"
    )


def test_explorer_agent_has_d1_d2_d3_interview():
    """agents/bundle-explorer.md must describe D1, D2, and D3 sub-path interviews."""
    path = AGENTS_DIR / "bundle-explorer.md"
    content = path.read_text(encoding="utf-8")
    assert "D1" in content, (
        "bundle-explorer.md must describe the D1 (Foundation + Customize) interview"
    )
    assert "D2" in content, (
        "bundle-explorer.md must describe the D2 (Start from Scratch) interview"
    )
    assert "D3" in content, (
        "bundle-explorer.md must describe the D3 (Adapt Existing) sub-path"
    )
    assert "experience_lens" in content, (
        "bundle-explorer.md must mention experience_lens for the D3→C redirect"
    )


# ---------------------------------------------------------------------------
# recipes/bundle-autonomous-post-explore.yaml
# ---------------------------------------------------------------------------


def test_recipe_has_experience_design_context_fields():
    """Autonomous recipe context must include experience_sub_path and experience_lens."""
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    assert path.exists(), "bundle-autonomous-post-explore.yaml does not exist"
    content = path.read_text(encoding="utf-8")
    assert "experience_sub_path" in content, (
        "Recipe context must include 'experience_sub_path' field"
    )
    assert "experience_lens" in content, (
        "Recipe context must include 'experience_lens' field"
    )
```

**Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && python -m pytest tests/test_four_path_routing.py -v
```

Expected: **8 FAILED** — all tests fail because the source files haven't been updated yet. Specifically:
- `test_instructions_has_four_path_heading` — FAIL (still says "Three-Path")
- `test_instructions_has_path_d_signals` — FAIL (no Path D signals)
- `test_instructions_has_path_d_interview_flow` — FAIL (no Path D section)
- `test_explore_mode_has_path_d_checklist` — FAIL (no "Design My Experience" checklist)
- `test_explore_mode_has_experience_design_handoff_fields` — FAIL (no `design_my_experience` in handoff)
- `test_explorer_agent_has_path_d_signals` — FAIL (no Path D in signals)
- `test_explorer_agent_has_d1_d2_d3_interview` — FAIL (no D1/D2/D3)
- `test_recipe_has_experience_design_context_fields` — FAIL (no experience fields in recipe)

**Step 3: Commit the test file**

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && git add tests/test_four_path_routing.py && git commit -m "test: add structural contract tests for four-path routing (all red)"
```

---

## Task 2: Update `context/instructions.md`

**Files:**
- Modify: `context/instructions.md`

This task makes 3 tests go green: `test_instructions_has_four_path_heading`, `test_instructions_has_path_d_signals`, `test_instructions_has_path_d_interview_flow`.

**Step 1: Rename the heading (line 19)**

In `context/instructions.md`, find this exact string on line 19:

```
## The Three-Path Routing Fork
```

Replace with:

```
## The Four-Path Routing Fork
```

**Step 2: Update the introductory sentence (line 21)**

Find this exact string on line 21:

```
The FIRST question in every session is implicit: does the user want to **create a new bundle**, **improve an existing one**, or **rebuild from a reference artifact**?
```

Replace with:

```
The FIRST question in every session is implicit: does the user want to **create a new bundle**, **improve an existing one**, **rebuild from a reference artifact**, or **design their overall Amplifier experience**?
```

**Step 3: Add Path D signals block**

Find this exact block (lines 34–38, the last signals section before the Orchestrator Intelligence section):

```
**Signals for "rebuild from reference":**
- "Here's a module, make it a bundle" / "Turn this into a proper bundle"
- "Rebuild this bundle from scratch" / "Start over with this"
- "Use X as a reference" / "Base it on X"
- User provides an existing file, module, or bundle as input material
```

Replace with:

```
**Signals for "rebuild from reference":**
- "Here's a module, make it a bundle" / "Turn this into a proper bundle"
- "Rebuild this bundle from scratch" / "Start over with this"
- "Use X as a reference" / "Base it on X"
- User provides an existing file, module, or bundle as input material

**Signals for "design my experience":**
- "Customize my amplifier" / "My own setup" / "Replace foundation"
- "I use GitHub Copilot" / "I don't want foundation defaults"
- "Design my experience" / "Build my own from scratch"
- User wants to compose their overall Amplifier identity, provider, persona, or tool selection — not a single capability bundle
```

**Step 4: Add Path D interview flow section**

Find this exact block (lines 74–85, the end of Path C and the key distinction note):

```
### Path C: Rebuild from Reference

`/bundle-explore` → analyze reference → `/bundle-spec` → `/bundle-plan` → `/bundle-execute` → `/bundle-verify` → `/bundle-finish`

Interview flow:
1. What's the reference artifact? (path, repo URL, or file)
2. `bundle-auditor` analyzes the reference (what does it do, what patterns does it use, what's worth keeping)
3. What should the NEW bundle do differently? Keep the same domain? Restructure? Expand scope?
4. What tier for the new bundle? (behavior / bundle / application bundle)
5. Produces `bundle-spec.md` that references the original as source material

**Key distinction from Path B:** Path B modifies the existing artifact in-place. Path C creates a new artifact *inspired by* the reference — the original is source material, not the target of renovation.
```

Replace with:

```
### Path C: Rebuild from Reference

`/bundle-explore` → analyze reference → `/bundle-spec` → `/bundle-plan` → `/bundle-execute` → `/bundle-verify` → `/bundle-finish`

Interview flow:
1. What's the reference artifact? (path, repo URL, or file)
2. `bundle-auditor` analyzes the reference (what does it do, what patterns does it use, what's worth keeping)
3. What should the NEW bundle do differently? Keep the same domain? Restructure? Expand scope?
4. What tier for the new bundle? (behavior / bundle / application bundle)
5. Produces `bundle-spec.md` that references the original as source material

**Key distinction from Path B:** Path B modifies the existing artifact in-place. Path C creates a new artifact *inspired by* the reference — the original is source material, not the target of renovation.

### Path D: Design My Experience

`/bundle-explore` → experience interview → `/bundle-spec` → `/bundle-plan` → `/bundle-execute` → `/bundle-verify` → `/bundle-finish`

Path D serves users who want to customize their overall Amplifier experience — identity, provider, persona, tool selection — rather than work on a single capability bundle. It branches into three sub-paths:

**D1: Foundation + Customize** — Start with foundation's defaults, override specific things.
Interview (7 steps): identity → provider → persona → keep/drop behaviors → add capabilities → naming → autonomy

**D2: Start from Scratch** — Pure cherry-pick build, no inherited defaults.
Interview (10 steps): identity → provider → persona → orchestrator → context manager → tools → hooks → agents → system instructions → autonomy

**D3: Adapt Existing** — Reshape something that already exists.
Redirects to Path C with `experience_lens: true`. No separate interview needed — the flag tells the spec phase to frame the rebuild as experience customization rather than capability reconstruction.
```

**Step 5: Run the three instructions tests to verify they pass**

Run:
```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && python -m pytest tests/test_four_path_routing.py::test_instructions_has_four_path_heading tests/test_four_path_routing.py::test_instructions_has_path_d_signals tests/test_four_path_routing.py::test_instructions_has_path_d_interview_flow -v
```

Expected: **3 PASSED**

**Step 6: Run full existing test suite to check for regressions**

Run:
```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && python -m pytest tests/test_modes_adherence.py -v
```

Expected: All existing tests still PASS. The `test_instructions_describes_upgrade_path` test should still pass because we didn't remove any upgrade content.

**Step 7: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && git add context/instructions.md && git commit -m "feat: add Path D signals and interview flow to instructions (four-path routing)"
```

---

## Task 3: Update `modes/bundle-explore.md`

**Files:**
- Modify: `modes/bundle-explore.md`

This task makes 2 tests go green: `test_explore_mode_has_path_d_checklist`, `test_explore_mode_has_experience_design_handoff_fields`.

**Step 1: Update the HARD-GATE to include the fourth path (line 60)**

In `modes/bundle-explore.md`, find this exact string on line 60:

```
1. Determined whether this is "create new," "improve existing," or "rebuild from reference"
```

Replace with:

```
1. Determined whether this is "create new," "improve existing," "rebuild from reference," or "design my experience"
```

**Step 2: Add the Design My Experience checklist**

Find this exact block (lines 90–97, the end of the Rebuild from Reference checklist):

```
For **Rebuild from Reference**:
- [ ] Reference artifact identified (path, repo URL, or file)
- [ ] Delegate to bundle-auditor to analyze the reference artifact
- [ ] Determine what to keep, what to restructure, what to add
- [ ] Establish what the NEW bundle should do (vs what the reference does)
- [ ] What tier for the new bundle? Behavior / Bundle / Application Bundle
- [ ] Autonomy requested? Detect from user vocabulary or Amplifier caller context
- [ ] All blockers resolved — ready for transition
```

Replace with:

```
For **Rebuild from Reference**:
- [ ] Reference artifact identified (path, repo URL, or file)
- [ ] Delegate to bundle-auditor to analyze the reference artifact
- [ ] Determine what to keep, what to restructure, what to add
- [ ] Establish what the NEW bundle should do (vs what the reference does)
- [ ] What tier for the new bundle? Behavior / Bundle / Application Bundle
- [ ] Autonomy requested? Detect from user vocabulary or Amplifier caller context
- [ ] All blockers resolved — ready for transition

For **Design My Experience**:
- [ ] Determine sub-path: D1 (Foundation + Customize), D2 (Start from Scratch), or D3 (Adapt Existing)
- [ ] If D3: redirect to Rebuild from Reference checklist with experience_lens flag — stop here
- [ ] If D1: gather identity, provider, persona, keep/drop behaviors, add capabilities, naming
- [ ] If D2: gather identity, provider, persona, orchestrator, context manager, tools, hooks, agents, system instructions
- [ ] Autonomy requested? Detect from user vocabulary or Amplifier caller context
- [ ] All blockers resolved — ready for transition
```

**Step 3: Update the handoff payload schema**

Find this exact block (lines 119–133, the handoff payload YAML):

```yaml
path_decision: ""          # "create_new" | "improve_existing" | "rebuild_from_reference"
target: ""                 # Bundle name (create) or path/URL (improve/rebuild)
tier: ""                   # "behavior" | "bundle" | "application_bundle"
summary_of_requirements: "" # What was learned in explore
known_constraints: ""      # Constraints discovered (scope limits, dependencies, etc.)
autonomy_requested: false  # True if user or Amplifier caller requested autonomy
trigger_reason: ""         # Why autonomy was requested (e.g., "yolo", "amplifier-caller")
open_questions: ""         # Any remaining unresolved questions (must be empty before launch)
upgrade_requested: false  # True if upgrade intent detected or legacy provenance found
upgrade_reason: ""         # "explicit_intent" | "legacy_provenance_detected" | "schema_mismatch"
provenance_shape: ""       # "legacy_bundlewizard" | "generated_by_v1" | "none"
source_schema_version: ""  # Schema version found in target (empty if none)
target_schema_version: "1" # Current canonical schema version
```

Replace with:

```yaml
path_decision: ""          # "create_new" | "improve_existing" | "rebuild_from_reference" | "design_my_experience"
target: ""                 # Bundle name (create) or path/URL (improve/rebuild)
tier: ""                   # "behavior" | "bundle" | "application_bundle"
summary_of_requirements: "" # What was learned in explore
known_constraints: ""      # Constraints discovered (scope limits, dependencies, etc.)
autonomy_requested: false  # True if user or Amplifier caller requested autonomy
trigger_reason: ""         # Why autonomy was requested (e.g., "yolo", "amplifier-caller")
open_questions: ""         # Any remaining unresolved questions (must be empty before launch)
upgrade_requested: false  # True if upgrade intent detected or legacy provenance found
upgrade_reason: ""         # "explicit_intent" | "legacy_provenance_detected" | "schema_mismatch"
provenance_shape: ""       # "legacy_bundlewizard" | "generated_by_v1" | "none"
source_schema_version: ""  # Schema version found in target (empty if none)
target_schema_version: "1" # Current canonical schema version
experience_sub_path: ""    # "d1_foundation_customize" | "d2_start_from_scratch" | "d3_adapt_existing" (Path D only)
experience_lens: false     # True when D3 redirects to Path C — frames rebuild as experience customization
```

**Step 4: Update the recipe context block**

Find this exact block (lines 152–168, the recipe invocation context):

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
          "output_dir": "output",
          "upgrade_requested": "<resolved>",
          "upgrade_reason": "<resolved>",
          "provenance_shape": "<resolved>",
          "source_schema_version": "<resolved>",
          "target_schema_version": "1"
        })
```

Replace with:

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
          "output_dir": "output",
          "upgrade_requested": "<resolved>",
          "upgrade_reason": "<resolved>",
          "provenance_shape": "<resolved>",
          "source_schema_version": "<resolved>",
          "target_schema_version": "1",
          "experience_sub_path": "<resolved>",
          "experience_lens": "<resolved>"
        })
```

**Step 5: Run the two mode tests to verify they pass**

Run:
```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && python -m pytest tests/test_four_path_routing.py::test_explore_mode_has_path_d_checklist tests/test_four_path_routing.py::test_explore_mode_has_experience_design_handoff_fields -v
```

Expected: **2 PASSED**

**Step 6: Run full existing test suite to check for regressions**

Run:
```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && python -m pytest tests/test_modes_adherence.py -v
```

Expected: All existing tests still PASS. The `test_explore_mode_has_upgrade_handoff_fields` and `test_explore_mode_detects_upgrade_intent` tests should still pass because we didn't remove any upgrade content.

**Step 7: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && git add modes/bundle-explore.md && git commit -m "feat: add Design My Experience checklist and handoff fields to bundle-explore mode"
```

---

## Task 4: Update `agents/bundle-explorer.md`

**Files:**
- Modify: `agents/bundle-explorer.md`

This task makes 2 tests go green: `test_explorer_agent_has_path_d_signals`, `test_explorer_agent_has_d1_d2_d3_interview`.

**Step 1: Update the agent description in frontmatter (lines 4–16)**

In `agents/bundle-explorer.md`, find this exact block (the description value in YAML frontmatter, lines 4–16):

```
  description: |
    Use when starting a new bundlewizard session — creating a new bundle, improving an existing one,
    or rebuilding something new from a reference artifact.
    REQUIRED as the first agent in any bundle generation workflow.

    Opens an adaptive-depth interview to understand what the user needs. Detects experience
    level passively (from vocabulary, specificity, ecosystem awareness) and adjusts depth.
    Routes to "create new," "improve existing," or "rebuild from reference" path. For create:
    surveys the ecosystem for similar bundles. For improve: dispatches the auditor for full
    analysis. For rebuild: dispatches the auditor to analyze the reference, then builds a spec
    for the new artifact.

    Produces: interview summary + routing decision + context for the spec-writer.
```

Replace with:

```
  description: |
    Use when starting a new bundlewizard session — creating a new bundle, improving an existing one,
    rebuilding something new from a reference artifact, or designing a custom Amplifier experience.
    REQUIRED as the first agent in any bundle generation workflow.

    Opens an adaptive-depth interview to understand what the user needs. Detects experience
    level passively (from vocabulary, specificity, ecosystem awareness) and adjusts depth.
    Routes to "create new," "improve existing," "rebuild from reference," or "design my experience"
    path. For create: surveys the ecosystem for similar bundles. For improve: dispatches the auditor
    for full analysis. For rebuild: dispatches the auditor to analyze the reference, then builds a
    spec for the new artifact. For experience design: conducts a D1/D2/D3 sub-routing interview
    to customize identity, provider, persona, and tool selection.

    Produces: interview summary + routing decision + context for the spec-writer.
```

**Step 2: Add a Path D example block**

Find this exact block (lines 45–53, the last example in the frontmatter):

```
    <example>
    Context: User provides an existing module as reference material
    user: "Here's my tool-filesystem module — use it as a reference to build a proper standalone bundle"
    assistant: "I'll delegate to bundlewizard:bundle-explorer to analyze the reference module and interview you about what the new bundle should do differently."
    <commentary>
    Providing an existing artifact as starting material triggers Path C (rebuild from reference),
    not Path B (improve existing). The goal is a new artifact, not an in-place renovation.
    </commentary>
    </example>
```

Replace with:

```
    <example>
    Context: User provides an existing module as reference material
    user: "Here's my tool-filesystem module — use it as a reference to build a proper standalone bundle"
    assistant: "I'll delegate to bundlewizard:bundle-explorer to analyze the reference module and interview you about what the new bundle should do differently."
    <commentary>
    Providing an existing artifact as starting material triggers Path C (rebuild from reference),
    not Path B (improve existing). The goal is a new artifact, not an in-place renovation.
    </commentary>
    </example>

    <example>
    Context: User wants to customize their overall Amplifier experience
    user: "I want to replace foundation with my own setup — different provider, different persona, cherry-pick which tools I keep"
    assistant: "I'll delegate to bundlewizard:bundle-explorer to interview you about your custom Amplifier experience — we'll figure out whether to start from foundation and customize, or build from scratch."
    <commentary>
    Requests to customize the overall Amplifier experience (not a single bundle) trigger Path D
    (Design My Experience). The explorer will sub-route to D1, D2, or D3.
    </commentary>
    </example>
```

**Step 3: Rename "Three Jobs" to "Four Jobs" (line 80)**

Find this exact string:

```
## Your Three Jobs
```

Replace with:

```
## Your Four Jobs
```

**Step 4: Add Path D to the signal table and update disambiguation (lines 84–91)**

Find this exact block:

```
**Create New**, **Improve Existing**, or **Rebuild from Reference** — detect from the user's first message:

| Signal | Path |
|--------|------|
| "Build," "create," "generate," "I want something that..." | Create New |
| "Review," "improve," "fix," "look at this bundle" + path/URL | Improve Existing |
| "Turn this into," "rebuild from," "use X as reference," provides artifact as input material | Rebuild from Reference |
| Ambiguous | Ask: "Are you looking to create something new, improve an existing bundle, or use an existing artifact as reference material?" |
```

Replace with:

```
**Create New**, **Improve Existing**, **Rebuild from Reference**, or **Design My Experience** — detect from the user's first message:

| Signal | Path |
|--------|------|
| "Build," "create," "generate," "I want something that..." | Create New |
| "Review," "improve," "fix," "look at this bundle" + path/URL | Improve Existing |
| "Turn this into," "rebuild from," "use X as reference," provides artifact as input material | Rebuild from Reference |
| "Customize my amplifier," "my own setup," "replace foundation," "design my experience," "I use GitHub Copilot," "I don't want foundation defaults," "build my own from scratch" | Design My Experience |
| Ambiguous | Ask: "Are you looking to (a) add a capability, (b) improve an existing bundle, (c) rebuild something from a reference, or (d) customize your overall Amplifier experience?" |
```

**Step 5: Add the Design My Experience interview flow**

Find this exact block (lines 111–117, the end of the Rebuild from Reference interview):

```
**For Rebuild from Reference:**

1. **Get the reference artifact** — Path, repo URL, or file. This is the *source material*, not the renovation target.
2. **Run the audit** — Delegate to `bundlewizard:bundle-auditor` to analyze the reference: what does it do, what patterns does it use, what's worth keeping.
3. **Interview for the new artifact** — What should the NEW bundle do differently? Same domain or expanded? Restructure the architecture? New tier?
4. **Confirm the distinction** — Make clear: this produces a *new* artifact. The reference is inspiration, not the thing being edited.
5. **Scope the new bundle** — Tier, capabilities, what it borrows vs what it invents fresh.
```

Replace with:

```
**For Rebuild from Reference:**

1. **Get the reference artifact** — Path, repo URL, or file. This is the *source material*, not the renovation target.
2. **Run the audit** — Delegate to `bundlewizard:bundle-auditor` to analyze the reference: what does it do, what patterns does it use, what's worth keeping.
3. **Interview for the new artifact** — What should the NEW bundle do differently? Same domain or expanded? Restructure the architecture? New tier?
4. **Confirm the distinction** — Make clear: this produces a *new* artifact. The reference is inspiration, not the thing being edited.
5. **Scope the new bundle** — Tier, capabilities, what it borrows vs what it invents fresh.

**For Design My Experience:**

First, determine the sub-path — ask: "How do you want to build your experience?"

- **D1: Foundation + Customize** — Start with foundation's rich defaults, override specific things.
- **D2: Start from Scratch** — Pure cherry-pick build, no inherited defaults. Full control.
- **D3: Adapt Existing** — Reshape something that already exists. → Redirect to **Rebuild from Reference** with `experience_lens: true`. No separate interview needed.

**D1 interview (7 steps):**
1. **Identity** — Who is this experience for? What's the use case?
2. **Provider** — Which LLM provider and model preferences?
3. **Persona** — What personality and communication style?
4. **Keep/Drop Behaviors** — Which foundation behaviors to retain, which to drop?
5. **Add Capabilities** — Any additional capability bundles to layer in?
6. **Naming** — Bundle name, description, metadata
7. **Autonomy** — Manual, autonomous, or hybrid workflow preference?

**D2 interview (10 steps):**
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
```

**Step 6: Update the interview summary template (line 194)**

Find this exact block (lines 191–202, the Output section):

```
```markdown
## Interview Summary

- **Path:** Create New / Improve Existing / Rebuild from Reference
- **Target:** [bundle name or path]
- **Reference:** [path or URL of reference artifact, if Path C]
- **Tier:** Behavior / Bundle / Application Bundle
- **Problem:** [what it solves]
- **Capabilities:** [what it needs]
- **Delegates to:** [which existing experts]
- **Key decisions:** [anything notable from the interview]
```
```

Replace with:

```
```markdown
## Interview Summary

- **Path:** Create New / Improve Existing / Rebuild from Reference / Design My Experience
- **Sub-path:** [D1 / D2 / D3, if Path D]
- **Target:** [bundle name or path]
- **Reference:** [path or URL of reference artifact, if Path C]
- **Experience Lens:** [true/false — set when D3 redirects to Path C]
- **Tier:** Behavior / Bundle / Application Bundle
- **Problem:** [what it solves]
- **Capabilities:** [what it needs]
- **Delegates to:** [which existing experts]
- **Key decisions:** [anything notable from the interview]
```
```

**Step 7: Run the two agent tests to verify they pass**

Run:
```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && python -m pytest tests/test_four_path_routing.py::test_explorer_agent_has_path_d_signals tests/test_four_path_routing.py::test_explorer_agent_has_d1_d2_d3_interview -v
```

Expected: **2 PASSED**

**Step 8: Run full existing test suite to check for regressions**

Run:
```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && python -m pytest tests/test_modes_adherence.py -v
```

Expected: All existing tests still PASS.

**Step 9: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && git add agents/bundle-explorer.md && git commit -m "feat: add Path D signals, disambiguation, and D1/D2/D3 interview to bundle-explorer"
```

---

## Task 5: Update `recipes/bundle-autonomous-post-explore.yaml`

**Files:**
- Modify: `recipes/bundle-autonomous-post-explore.yaml`

This task makes the last test go green: `test_recipe_has_experience_design_context_fields`.

**Step 1: Add experience design fields to the recipe context object**

In `recipes/bundle-autonomous-post-explore.yaml`, find this exact block (lines 34–38, the last entries in the context object):

```
  upgrade_requested: false   # True if upgrade intent or legacy provenance detected
  upgrade_reason: ""         # "explicit_intent" | "legacy_provenance_detected" | "schema_mismatch"
  provenance_shape: ""       # "legacy_bundlewizard" | "generated_by_v1" | "none"
  source_schema_version: ""  # Schema version found in target (empty if none)
  target_schema_version: "1" # Current canonical schema version
```

Replace with:

```
  upgrade_requested: false   # True if upgrade intent or legacy provenance detected
  upgrade_reason: ""         # "explicit_intent" | "legacy_provenance_detected" | "schema_mismatch"
  provenance_shape: ""       # "legacy_bundlewizard" | "generated_by_v1" | "none"
  source_schema_version: ""  # Schema version found in target (empty if none)
  target_schema_version: "1" # Current canonical schema version
  experience_sub_path: ""    # "d1_foundation_customize" | "d2_start_from_scratch" | "d3_adapt_existing" (Path D only)
  experience_lens: false     # True when D3 redirects to Path C — frames rebuild as experience customization
```

**Step 2: Run the recipe test to verify it passes**

Run:
```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && python -m pytest tests/test_four_path_routing.py::test_recipe_has_experience_design_context_fields -v
```

Expected: **1 PASSED**

**Step 3: Run the full existing test suite to check for regressions**

Run:
```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && python -m pytest tests/test_modes_adherence.py -v
```

Expected: All existing tests still PASS. Specifically, `test_recipe_context_has_upgrade_fields` should still pass because the upgrade fields are untouched.

**Step 4: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && git add recipes/bundle-autonomous-post-explore.yaml && git commit -m "feat: add experience_sub_path and experience_lens to autonomous recipe context"
```

---

## Task 6: Run All Tests Green

**Files:** None (verification only)

**Step 1: Run the full new test file**

Run:
```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && python -m pytest tests/test_four_path_routing.py -v
```

Expected: **8 PASSED, 0 FAILED**

**Step 2: Run the complete test suite**

Run:
```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && python -m pytest tests/ -v
```

Expected: All tests PASS (both `test_modes_adherence.py` and `test_four_path_routing.py`).

If any tests fail, fix the specific issue before proceeding.

---

## Task 7: Commit Supporting Artifacts (DOT + PNG)

**Files:**
- Stage: `docs/stories/explore-interview-flow.dot` (already exists, untracked)
- Stage: `docs/stories/explore-interview-flow.png` (already exists, untracked)

These files already exist on disk. They were generated during the design phase and are currently untracked.

**Step 1: Stage and commit the artifacts**

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && git add docs/stories/explore-interview-flow.dot docs/stories/explore-interview-flow.png && git commit -m "docs: add four-path routing flow diagram (DOT source + PNG render)"
```

**Step 2: Verify clean git status**

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && git status
```

Expected: Working tree clean (except possibly `docs/.DS_Store` which is unrelated).

---

## Summary

| Task | What | Tests affected | Commit message |
|------|------|---------------|----------------|
| 1 | Create test file (all red) | 8 new tests, all FAIL | `test: add structural contract tests for four-path routing (all red)` |
| 2 | Update `context/instructions.md` | 3 go green | `feat: add Path D signals and interview flow to instructions (four-path routing)` |
| 3 | Update `modes/bundle-explore.md` | 2 go green | `feat: add Design My Experience checklist and handoff fields to bundle-explore mode` |
| 4 | Update `agents/bundle-explorer.md` | 2 go green | `feat: add Path D signals, disambiguation, and D1/D2/D3 interview to bundle-explorer` |
| 5 | Update `recipes/bundle-autonomous-post-explore.yaml` | 1 goes green | `feat: add experience_sub_path and experience_lens to autonomous recipe context` |
| 6 | Run all tests green | 8/8 PASS + full regression | — (no commit, verification only) |
| 7 | Commit DOT + PNG | — | `docs: add four-path routing flow diagram (DOT source + PNG render)` |

**Total: 7 tasks, 7 commits, 8 new tests, 5 files modified, 1 file created, 2 files staged**
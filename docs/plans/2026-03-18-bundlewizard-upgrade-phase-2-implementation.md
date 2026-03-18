# Bundlewizard Upgrade Phase 2: Routed Upgrade Behavior + Live Validation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make upgrade a routed specialization of `improve_existing` inside `bundle-explore`, with both explicit upgrade intent and automatic legacy detection. Validate end-to-end on `~/dev/amplifier-bundle-project-memory`.

**Architecture:** Upgrade routing lives inside the existing `bundle-explore` handoff gate. The autonomous recipe becomes upgrade-aware via new context fields with safe defaults. Live validation proves the full upgrade path against a real legacy-generated repo.

**Tech Stack:** Markdown mode files, YAML recipe, pytest, live repo validation.

**Design doc:** `docs/plans/2026-03-18-bundlewizard-upgrade-design.md`

**Prerequisite:** Phase 1 must be complete (canonical schema defined in `context/factory-protocol.md`, packager aligned, autonomous-protocol aligned, recipe finish stage aligned, legacy fixture + migration tests passing).

---

## Task 1: Add upgrade routing tests (RED)

**Modify:** `tests/test_modes_adherence.py`

Write the upgrade surface contract tests first so they fail (RED), then implement in Tasks 2–5 to make them pass (GREEN).

**Add the following tests after the existing tests (after line 320):**

```python
# ---------------------------------------------------------------------------
# Upgrade routing surface tests
# ---------------------------------------------------------------------------


def test_explore_mode_detects_upgrade_intent():
    """modes/bundle-explore.md must recognize upgrade intent phrases."""
    path = MODES_DIR / "bundle-explore.md"
    assert path.exists(), "modes/bundle-explore.md does not exist"
    content = path.read_text(encoding="utf-8")

    # Must recognize explicit upgrade vocabulary
    assert "upgrade" in content.lower(), (
        "bundle-explore.md must recognize 'upgrade' as an intent signal"
    )
    assert "legacy" in content.lower() or "migrate" in content.lower(), (
        "bundle-explore.md must recognize legacy provenance detection or "
        "migration as part of upgrade routing"
    )


def test_explore_mode_has_upgrade_handoff_fields():
    """modes/bundle-explore.md handoff payload must include upgrade fields."""
    path = MODES_DIR / "bundle-explore.md"
    assert path.exists(), "modes/bundle-explore.md does not exist"
    content = path.read_text(encoding="utf-8")

    assert "upgrade_requested" in content, (
        "bundle-explore.md handoff payload must include upgrade_requested field"
    )
    assert "upgrade_reason" in content, (
        "bundle-explore.md handoff payload must include upgrade_reason field"
    )
    assert "provenance_shape" in content, (
        "bundle-explore.md handoff payload must include provenance_shape field"
    )
    assert "source_schema_version" in content, (
        "bundle-explore.md handoff payload must include source_schema_version field"
    )
    assert "target_schema_version" in content, (
        "bundle-explore.md handoff payload must include target_schema_version field"
    )


def test_recipe_context_has_upgrade_fields():
    """The autonomous recipe context block must include upgrade fields with safe defaults."""
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    assert path.exists(), (
        "recipes/bundle-autonomous-post-explore.yaml does not exist"
    )
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    context = content.get("context", {})

    assert "upgrade_requested" in context, (
        "Recipe context must include upgrade_requested with a safe default"
    )
    # Safe default should be false (not true)
    assert context["upgrade_requested"] is False or context["upgrade_requested"] == "false", (
        "upgrade_requested must default to false (safe default)"
    )


def test_instructions_describes_upgrade_path():
    """context/instructions.md must describe upgrade as a recognized path."""
    path = CONTEXT_DIR / "instructions.md"
    assert path.exists(), "context/instructions.md does not exist"
    content = path.read_text(encoding="utf-8")

    assert "upgrade" in content.lower(), (
        "instructions.md must describe upgrade as a recognized user-facing path"
    )


def test_bundle_version_bumped():
    """bundle.md version must be >= 0.2.0 to reflect the upgrade capability."""
    assert BUNDLE_MD.exists(), "bundle.md does not exist"
    content = BUNDLE_MD.read_text(encoding="utf-8")

    # Extract version from frontmatter
    match = re.search(r"version:\s*(\d+\.\d+\.\d+)", content)
    assert match, "bundle.md must contain a version field"
    version = match.group(1)
    parts = [int(p) for p in version.split(".")]
    # version >= 0.2.0
    assert (parts[0] > 0) or (parts[0] == 0 and parts[1] >= 2), (
        f"bundle.md version is {version} — must be >= 0.2.0 to reflect "
        "the upgrade capability addition"
    )
```

**Verification:**
- `python_check tests/test_modes_adherence.py` is clean
- `pytest tests/test_modes_adherence.py -v` — 17 existing tests pass, 5 new tests fail (RED)

**Commit:** `test: add upgrade routing surface contract tests (RED)`

---

## Task 2: Add upgrade routing to `bundle-explore.md`

**Modify:** `modes/bundle-explore.md`

**Current state:** The file is 161 lines. The `<CRITICAL>` section (lines 28–50) has the hybrid pattern and Amplifier-as-actor rule. The checklists (lines 63–92) track explore progress per path. The handoff payload (lines 109–123) has the current fields. The transition section (lines 125–161) handles manual vs autonomous handoff.

**Changes:**

### Change 1: Add upgrade detection to the `<CRITICAL>` section

After the existing `<HARD-GATE>` block (line 61), add upgrade detection guidance:

```markdown
## Upgrade Detection

Upgrade is a specialization of "improve existing" — NOT a separate path.

### Explicit upgrade intent
Detect from vocabulary: "upgrade this bundle", "refresh this bundle", "migrate",
"bring up to date", "update to latest bundlewizard format".

### Automatic legacy detection
When inspecting an existing bundle's `bundle.md` frontmatter, check for:
- `bundle.bundlewizard` present with no `generated_by` → legacy shape (pre-schema)
- `generated_by` present but no `schema_version` → old shape (unversioned)
- `generated_by.schema_version` < 1 → stale shape (upgradeable)

If any of these conditions are detected, set the upgrade handoff fields even if the
user didn't explicitly say "upgrade." Surface the finding: "I notice this bundle was
generated by an older version of bundlewizard. I'll upgrade the metadata as part of
the improvement."

### Unknown origin
If the target bundle has NO recognizable bundlewizard provenance (no `bundlewizard`
key, no `generated_by`), stay in normal `improve_existing` semantics. Only treat as
upgrade if the caller explicitly requested it.
```

### Change 2: Add upgrade-aware fields to the Handoff Payload block

Add these fields to the existing handoff payload YAML block (after `open_questions` at line 122):

```yaml
upgrade_requested: false   # True if explicit upgrade intent or legacy detected
upgrade_reason: ""         # "explicit_intent" | "legacy_provenance_detected" | "schema_mismatch" | ""
provenance_shape: ""       # "legacy_bundlewizard" | "generated_by_v1" | "none" | ""
source_schema_version: ""  # "0" (legacy) | "1" | "unknown" | ""
target_schema_version: "1" # Always "1" for current bundlewizard
```

### Change 3: Update the autonomous recipe launch call

In the `recipes()` call (around lines 142–153), add the upgrade fields to the context dict:

```python
          "upgrade_requested": "<resolved>",
          "upgrade_reason": "<resolved>",
          "provenance_shape": "<resolved>",
          "source_schema_version": "<resolved>",
          "target_schema_version": "1",
```

**Verification:**
- `pytest tests/test_modes_adherence.py::test_explore_mode_detects_upgrade_intent -v` → PASSES
- `pytest tests/test_modes_adherence.py::test_explore_mode_has_upgrade_handoff_fields -v` → PASSES
- `pytest tests/test_modes_adherence.py::test_explore_mode_is_handoff_gate -v` → still PASSES (no regression)
- `pytest tests/test_modes_adherence.py::test_pipeline_mode_transitions -v` → still PASSES (frontmatter unchanged)

**Commit:** `feat: add upgrade routing to bundle-explore handoff gate`

---

## Task 3: Make autonomous recipe upgrade-aware

**Modify:** `recipes/bundle-autonomous-post-explore.yaml`

**Current state:** The context block (lines 24–33) has the explore handoff payload fields but no upgrade fields.

**Changes:**

### Change 1: Add upgrade fields to the context block (after line 33)

Add these lines after `output_dir: "output"`:

```yaml
  # ── Upgrade handoff fields (safe defaults — no upgrade unless explore says so) ──
  upgrade_requested: false       # True if explore detected upgrade intent or legacy provenance
  upgrade_reason: ""             # "explicit_intent" | "legacy_provenance_detected" | "schema_mismatch" | ""
  provenance_shape: ""           # "legacy_bundlewizard" | "generated_by_v1" | "none" | ""
  source_schema_version: ""      # "0" (legacy) | "1" | "unknown" | ""
  target_schema_version: "1"     # Always "1" for current bundlewizard
```

### Change 2: Update the spec stage prompt to handle upgrade context

In the spec stage prompt (around lines 46–100), add a paragraph after the initial instruction block that tells the agent how to handle upgrade context:

```
          UPGRADE CONTEXT (only applies if upgrade_requested is true):
          If {{upgrade_requested}} is true, this is an upgrade run. The spec should include:
          - Provenance migration: normalize {{provenance_shape}} to canonical generated_by
          - Schema version migration from {{source_schema_version}} to {{target_schema_version}}
          - Upgrade reason: {{upgrade_reason}}
          If upgrade_requested is false or empty, ignore this section entirely.
```

### Change 3: Update the finish stage prompt to handle legacy migration

In the finish stage prompt (around the `2a. Add canonical generated_by block` section), add a pre-step:

```
          UPGRADE PRE-STEP (only if {{upgrade_requested}} is true):
          Before writing the canonical generated_by block, check if the target bundle
          has a legacy bundle.bundlewizard block. If so, read its audit values and
          remove the legacy block before writing the canonical shape. Map legacy fields
          per the migration preservation rules in factory-protocol.md.
```

**Verification:**
- `pytest tests/test_modes_adherence.py::test_recipe_context_has_upgrade_fields -v` → PASSES
- `pytest tests/test_modes_adherence.py::test_autonomous_post_explore_recipe_stages -v` → still PASSES
- `pytest tests/test_modes_adherence.py::test_autonomous_post_explore_recipe_reuses_refinement_loop -v` → still PASSES

**Commit:** `feat: make autonomous recipe upgrade-aware with safe defaults`

---

## Task 4: Update `context/instructions.md` for upgrade support

**Modify:** `context/instructions.md`

**Current state:** 118 lines. The Three-Path Routing Fork (lines 19–73) describes create, improve, and rebuild paths. The Two-Track UX section (lines 85–118) describes manual vs autonomous. No mention of upgrade.

**Changes:**

### Change 1: Add upgrade as a recognized concept

After the `### Path C: Rebuild from Reference` section (after line 73) and before `## Output Tiers`, add:

```markdown
### Upgrade: A Specialization of Path B

Bundlewizard can upgrade older generated bundles to the current provenance format. This
is NOT a separate path — it routes through "improve existing" with upgrade-aware metadata.

**Signals for "upgrade":**
- "Upgrade this bundle" / "Refresh this bundle"
- "Migrate to latest format" / "Bring up to date"
- Automatic: bundlewizard detects legacy `bundle.bundlewizard` provenance shape
- Automatic: bundlewizard detects missing or outdated `schema_version`

**What upgrade adds to the improve flow:**
- Provenance migration: legacy `bundle.bundlewizard` → canonical `bundle.generated_by`
- Schema version stamping: `generated_by.schema_version` set to current
- Version source correction: `generated_by.version` sourced from bundlewizard's own version
- Audit trail preservation: existing convergence values are kept, not discarded

**Upgrade does NOT:**
- Create a separate mode stack or recipe universe
- Bypass the normal improve pipeline
- Require explicit user action if legacy provenance is detected automatically
```

**Verification:**
- `pytest tests/test_modes_adherence.py::test_instructions_describes_upgrade_path -v` → PASSES
- `pytest tests/test_modes_adherence.py::test_instructions_describes_opt_in_autonomy -v` → still PASSES
- `pytest tests/test_modes_adherence.py::test_instructions_no_bundle_bot -v` → still PASSES

**Commit:** `docs: add upgrade path to instructions.md`

---

## Task 5: Update `bundle.md` for upgrade support and version bump

**Modify:** `bundle.md`

**Current state:** 59 lines. Version is `0.1.0` at line 4. Modes table at lines 23–31. Two Tracks section at lines 33–43. Recipes table at lines 47–52. Getting Started at lines 54–59.

**Changes:**

### Change 1: Bump version from `0.1.0` to `0.2.0`

Line 4: change `version: 0.1.0` to `version: 0.2.0`

### Change 2: Update the `/bundle-explore` row in the Modes table

Line 25: update the "What Happens" column to mention upgrade detection:

```
| `/bundle-explore` | Interview | Understand what you need, route to create, improve, or upgrade — or launch autonomous continuation |
```

### Change 3: Add upgrade mention to Getting Started

After line 59 (end of file), add:

```markdown

Bundlewizard also upgrades older generated bundles automatically. Point it at a bundle
with legacy provenance metadata and it will migrate to the current format as part of the
improvement flow.
```

**Verification:**
- `pytest tests/test_modes_adherence.py::test_bundle_version_bumped -v` → PASSES
- `pytest tests/test_modes_adherence.py::test_bundle_md_matches_two_track_public_surface -v` → still PASSES (existing invariants unchanged)

**Commit:** `docs: add upgrade mention to bundle.md, bump to 0.2.0`

---

## Task 6: Live validation on `~/dev/amplifier-bundle-project-memory`

**Target:** `~/dev/amplifier-bundle-project-memory` (read-only reference — do not modify)

This is a manual verification task. The goal is to confirm that the upgrade design would work against a real legacy-generated repo.

### Pre-condition checks

Verify the target has the expected legacy shape:

```bash
# Check that bundle.bundlewizard exists
grep -c "bundlewizard:" ~/dev/amplifier-bundle-project-memory/bundle.md

# Check that generated_by does NOT exist
grep -c "generated_by:" ~/dev/amplifier-bundle-project-memory/bundle.md
# Expected: 0

# Check that schema_version does NOT exist
grep -c "schema_version:" ~/dev/amplifier-bundle-project-memory/bundle.md
# Expected: 0
```

### Detection verification

Confirm that bundlewizard's explore mode would correctly classify this target:

1. Read `modes/bundle-explore.md` — verify the upgrade detection section covers `bundle.bundlewizard` with no `generated_by`
2. Read `context/factory-protocol.md` — verify the legacy fingerprint table matches the shape found in the target
3. Confirm the classification: **Legacy (pre-schema)** — `bundle.bundlewizard` present, no `generated_by`

### Migration verification (conceptual)

Confirm that the packager's migration instructions would correctly transform the target:

1. Read `agents/bundle-packager.md` — verify legacy migration instructions cover the field mapping:
   - `bundlewizard.packaged_at` → `generated_by.timestamp`
   - `bundlewizard.level_score` → `convergence.level_score`
   - `bundlewizard.critic_verdict` → `convergence.critic_verdict`
   - `bundlewizard.tests_passed` → `convergence.tests_passed`
   - `bundlewizard.tests_failed` → `convergence.tests_failed`
   - `bundlewizard.commits` → `convergence.commits`
2. Confirm the legacy `bundle.bundlewizard` block would be removed (no dual-write)
3. Confirm `generated_by.version` would be set to bundlewizard's current version (`0.2.0` after Task 5)
4. Confirm `generated_by.schema_version` would be set to `1`

### Post-upgrade shape verification (conceptual)

After a hypothetical upgrade, the target's `bundle.md` frontmatter should look like:

```yaml
bundle:
  name: project-memory
  version: 0.1.0
  description: |
    Persistent project-scoped memory across sessions.
    Automatic capture via hooks, curated storage, session briefings.
  generated_by:
    tool: bundlewizard
    version: 0.2.0
    schema_version: 1
    timestamp: <new ISO 8601>
    mode: interactive
    convergence:
      level_score: 0.94
      critic_verdict: PASS
      tests_passed: 223
      tests_failed: 0
      commits: 7
```

Verify this shape is consistent with the canonical schema in `context/factory-protocol.md`.

### Idempotency verification (conceptual)

Confirm that running upgrade a second time on the post-upgrade shape would:
- Detect `generated_by.schema_version: 1` (current)
- NOT trigger legacy migration (no `bundle.bundlewizard` present)
- NOT require forced upgrade (schema is current)
- Result in no provenance changes (only substantive improvements if requested)

**This task produces no code changes.** It is a verification-only gate.

**Commit if any issues found require cleanup:** `chore: Phase 2 live validation findings`

---

## Task 7: Final validation

**Run:** `pytest tests/ -v`

**Expected:** All tests pass — the 17 existing structural tests, the provenance migration tests from Phase 1, and the 5 new upgrade routing tests.

**Run regression greps:**

```bash
# No /bundle-bot references
grep -rn "/bundle-bot" agents/ context/ modes/ recipes/ behaviors/ --include="*.md" --include="*.yaml"

# schema_version present in canonical locations
grep -rn "schema_version" context/factory-protocol.md agents/bundle-packager.md context/autonomous-protocol.md recipes/bundle-autonomous-post-explore.yaml modes/bundle-explore.md

# upgrade_requested present in explore + recipe
grep -rn "upgrade_requested" modes/bundle-explore.md recipes/bundle-autonomous-post-explore.yaml

# No hardcoded version: 0.1.0 in generated_by code blocks
grep -rn "version: 0.1.0" agents/ context/ recipes/ --include="*.md" --include="*.yaml" | grep -i "generated_by"

# bundle.md version is 0.2.0
grep "version:" bundle.md
```

**Expected regression grep results:**
- `/bundle-bot`: zero matches
- `schema_version`: at least one match in each of the five files
- `upgrade_requested`: at least one match in each of the two files
- Hardcoded version in generated_by: zero matches
- `bundle.md` version: `0.2.0`

**Verify the full shipped surface:**

```bash
# Behavior surface — single shipped behavior
ls behaviors/

# Recipe surface — includes post-explore with upgrade awareness
ls recipes/

# Mode surface — 7 pipeline modes, no bundle-bot
ls modes/

# Test surface — adherence + provenance migration
ls tests/test_*.py
```

**Commit:** `chore: bundlewizard upgrade implementation complete`

---

## Execution Notes

### Task ordering

```
Task 1 (RED tests) → write first, watch fail
Task 2 (explore routing) → depends on Task 1 (makes 2 tests GREEN)
Task 3 (recipe upgrade-aware) → depends on Task 1 (makes 1 test GREEN)
Task 4 (instructions) → depends on Task 1 (makes 1 test GREEN)
Task 5 (bundle.md) → depends on Task 1 (makes 1 test GREEN)
Task 6 (live validation) → depends on Tasks 2–5 (all product changes landed)
Task 7 (final validation) → depends on all
```

Tasks 2, 3, 4, and 5 are independent of each other and could be implemented in parallel after Task 1. Task 6 requires all product changes to be in place. Task 7 is the final gate.

### Scope boundary

- All changes are inside `amplifier-bundle-bundlewizard`
- `~/dev/amplifier-bundle-project-memory` is read-only reference — never modified by this plan
- No new modes, no new recipes, no new agents — only routing enhancements and field additions
- No upstream `amplifier-bundle-modes` changes
- Upgrade is a routing specialization of `improve_existing`, not a separate control surface

### Phase 1 prerequisite

This plan assumes Phase 1 is complete:
- `context/factory-protocol.md` has the canonical `generated_by` schema with `schema_version` and legacy recognition
- `agents/bundle-packager.md` sources version from bundlewizard's `bundle.md`, not hardcoded
- `agents/bundle-packager.md` has legacy migration instructions
- `context/autonomous-protocol.md` audit trail is aligned to canonical schema
- `recipes/bundle-autonomous-post-explore.yaml` finish stage has `version` and `schema_version`
- `tests/fixtures/legacy-provenance.yaml` exists with the old format
- `tests/test_provenance_migration.py` tests all pass

If any Phase 1 tests fail at the start of Phase 2, fix them before proceeding.

### What success looks like

After both phases are complete:

1. Every newly generated bundle carries `generated_by.version` and `generated_by.schema_version`
2. Legacy bundles like `project-memory` are automatically detected and would be migrated
3. Users can say "upgrade this bundle" and bundlewizard routes correctly
4. The upgrade path uses the existing improve pipeline — no new mode stack
5. The autonomous recipe handles upgrade context with safe defaults
6. All tests pass, all regression greps are clean
7. `bundle.md` version reflects the new capability (`0.2.0`)

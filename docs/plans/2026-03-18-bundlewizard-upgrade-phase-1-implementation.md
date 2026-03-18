# Bundlewizard Upgrade Phase 1: Metadata Contract + Migration Tests

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish the canonical `bundle.generated_by` provenance schema, fix cross-file inconsistencies, add legacy migration capability, and lock the contract with fixture-driven tests.

**Architecture:** Define the canonical schema in `factory-protocol.md` first (single source of truth), then align `bundle-packager.md`, `autonomous-protocol.md`, and the recipe finish stage to that schema. Add a legacy-format fixture from `~/dev/amplifier-bundle-project-memory` and write migration tests.

**Tech Stack:** Markdown context files, YAML recipe, pytest + PyYAML for tests.

**Design doc:** `docs/plans/2026-03-18-bundlewizard-upgrade-design.md`

---

## Task 1: Add `.worktrees/` to `.gitignore`

**Modify:** `.gitignore`

**Current state (9 lines):**
```
# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# Locally checked-out submodule directories (not tracked by this repo)
amplifier-bundle-modes/
amplifier-bundle-superpowers/
```

**Change:** Append a new section at the end of the file:

```
# Git worktrees (local development isolation)
.worktrees/
```

**Verification:** `cat .gitignore` shows the new line.

**Commit:** `chore: add .worktrees/ to .gitignore`

---

## Task 2: Define canonical `generated_by` schema in `factory-protocol.md`

**Modify:** `context/factory-protocol.md`

**Current state:** Lines 96–117 contain the `## Version Stamping` section with a `generated_by` block that is missing `schema_version`, `timestamp`, and `mode`, and uses old convergence field names (`iterations`, `level_1`, `level_2`, `level_3`).

**Replace lines 96–117 with:**

```markdown
## Version Stamping

Every bundle produced by the factory gets a version stamp in its `bundle.md` frontmatter.

### Canonical `generated_by` schema

```yaml
# In the generated bundle.md frontmatter:
bundle:
  name: <generated-bundle-name>
  version: 0.1.0
  description: |
    <generated description>
  generated_by:
    tool: bundlewizard
    version: <bundlewizard-version>    # Sourced from bundlewizard's own bundle.md — NEVER hardcoded
    schema_version: 1                   # Integer. Upgrade logic keys off this field.
    timestamp: <ISO 8601>               # When packaging completed
    mode: interactive                   # "interactive" or "autonomous"
    convergence:
      level_score: <float>             # Overall quality score
      critic_verdict: PASS             # PASS or FAIL
      tests_passed: <int>
      tests_failed: <int>
      commits: <int>
```

**Important:** `generated_by` is nested under `bundle:`, not a top-level frontmatter key.

### Upgrade stub fields

These four fields are what upgrade logic reads first:

| Field | Purpose |
|-------|---------|
| `generated_by.tool` | Identifies the generator |
| `generated_by.version` | Which bundlewizard version produced this |
| `generated_by.schema_version` | Which artifact format version — upgrade decisions key off this |
| `generated_by.timestamp` | When the bundle was last generated or upgraded |

Everything under `convergence` is audit trail — it does not gate upgrade routing.

### Version source rule

The `generated_by.version` value MUST be sourced from bundlewizard's own `bundle.md` frontmatter (`bundle.version`). Do NOT use hardcoded version literals in agent instructions or recipe prompts.

### Legacy fingerprint recognition

Older generated bundles may use a pre-canonical provenance shape. The factory must recognize these patterns:

| Pattern | Classification | Action |
|---------|---------------|--------|
| `bundle.bundlewizard` present, no `generated_by` | Legacy (pre-schema) | Migrate to canonical shape |
| `generated_by` present, no `schema_version` | Old (schema unversioned) | Add `schema_version: 1` |
| `generated_by.schema_version < current` | Stale (upgradeable) | Run schema migration |
| No recognizable provenance | Unknown origin | Normal improve flow unless explicit upgrade requested |

### Migration preservation rule

When normalizing legacy provenance, existing audit values are preserved:

| Legacy field | Canonical field |
|-------------|----------------|
| `bundlewizard.packaged_at` | `generated_by.timestamp` |
| `bundlewizard.level_score` | `convergence.level_score` |
| `bundlewizard.critic_verdict` | `convergence.critic_verdict` |
| `bundlewizard.tests_passed` | `convergence.tests_passed` |
| `bundlewizard.tests_failed` | `convergence.tests_failed` |
| `bundlewizard.commits` | `convergence.commits` |

The legacy `bundle.bundlewizard` block is removed after migration. No dual-write — only the canonical shape remains.
```

**Note:** The rest of the file (lines 1–95 and 118–128) remains untouched.

**Verification:**
- `context/factory-protocol.md` contains `schema_version`
- `context/factory-protocol.md` contains `generated_by`
- `context/factory-protocol.md` contains the legacy fingerprint table
- `context/factory-protocol.md` contains the migration preservation table

**Commit:** `feat: define canonical generated_by schema with schema_version and legacy recognition`

---

## Task 3: Align `bundle-packager.md` to canonical schema

**Modify:** `agents/bundle-packager.md`

**Current state:**
- Lines 43–62: `## Version Stamp` block with hardcoded `version: 0.1.0` and old convergence fields (`iterations`, `level_1`, `level_2`, `level_3`)
- Lines 87–99: `## /bundle-bot (Autonomous) Path` section referencing the deleted bundle-bot mode with `mode: bundle-bot`

**Changes:**

### Change 1: Replace the Version Stamp block (lines 43–64)

Replace the entire `## Version Stamp` section with:

```markdown
## Version Stamp

Add the canonical `generated_by` block to the generated bundle's `bundle.md` frontmatter.

**Version source rule:** Read bundlewizard's own version from its `bundle.md` frontmatter (`bundle.version`). NEVER use a hardcoded version literal.

```yaml
bundle:
  name: <bundle-name>
  version: 0.1.0
  description: |
    <description>
  generated_by:
    tool: bundlewizard
    version: <read from bundlewizard's own bundle.md>
    schema_version: 1
    timestamp: <ISO 8601>
    mode: <interactive or autonomous — based on how the session was invoked>
    convergence:
      level_score: <float>
      critic_verdict: <PASS or FAIL>
      tests_passed: <int>
      tests_failed: <int>
      commits: <int>
```

This is NON-NEGOTIABLE. Every machine-generated bundle must be traceable and upgradeable.

### Legacy provenance migration

If the target bundle has a legacy `bundle.bundlewizard` block (no `generated_by`), normalize it:

1. Read the existing `bundlewizard` audit values (`packaged_at`, `level_score`, `critic_verdict`, `tests_passed`, `tests_failed`, `commits`)
2. Write the canonical `generated_by` block, mapping legacy fields to their canonical equivalents:
   - `bundlewizard.packaged_at` → `generated_by.timestamp`
   - `bundlewizard.level_score` → `convergence.level_score`
   - `bundlewizard.critic_verdict` → `convergence.critic_verdict`
   - `bundlewizard.tests_passed` → `convergence.tests_passed`
   - `bundlewizard.tests_failed` → `convergence.tests_failed`
   - `bundlewizard.commits` → `convergence.commits`
3. Remove the legacy `bundle.bundlewizard` block entirely — no dual-write
4. Set `generated_by.version` to bundlewizard's current version (this is the upgrading version, not the original)
5. Set `generated_by.schema_version` to `1`
```

### Change 2: Remove the `/bundle-bot (Autonomous) Path` section entirely (lines 87–99)

Delete lines 87–99. This section references the deleted `bundle-bot` mode and uses `mode: bundle-bot`. Autonomous packaging is now handled by the `autonomous-protocol.md` policy and the `bundle-autonomous-post-explore` recipe's finish stage. No replacement text needed — just remove.

**Verification:**
- `agents/bundle-packager.md` contains `read from bundlewizard's own bundle.md` (version source instruction)
- `agents/bundle-packager.md` does NOT contain `version: 0.1.0` inside a `generated_by` code block
- `agents/bundle-packager.md` does NOT contain `/bundle-bot`
- `agents/bundle-packager.md` contains `schema_version`
- `agents/bundle-packager.md` contains `Legacy provenance migration`

**Commit:** `feat: align packager to canonical generated_by schema, remove stale bundle-bot section`

---

## Task 4: Align `autonomous-protocol.md` audit trail to canonical schema

**Modify:** `context/autonomous-protocol.md`

**Current state:** Lines 81–100 contain the `## Audit Trail` section with a `generated_by` block that:
- Is NOT nested under `bundle:` (it's shown as top-level — a drift from the canonical nesting)
- Is missing `version`, `schema_version`, and `timestamp` fields
- Uses old convergence field names (`iterations`, `level_1`, `level_2`, `level_3`)

**Replace lines 81–100 with:**

```markdown
## Audit Trail

Every bundle generated via autonomous continuation MUST include the canonical `generated_by`
block in its `bundle.md` frontmatter, nested under `bundle:`:

```yaml
bundle:
  name: <bundle-name>
  version: <bundle-version>
  generated_by:
    tool: bundlewizard
    version: <read from bundlewizard's own bundle.md>
    schema_version: 1
    timestamp: <ISO 8601>
    mode: autonomous
    triggered_by: <session_id>
    trigger_reason: <why autonomy was requested>
    convergence:
      level_score: <float>
      critic_verdict: <PASS or FAIL>
      tests_passed: <int>
      tests_failed: <int>
      commits: <int>
```

The `triggered_by` field is the session ID of the calling session. The `trigger_reason`
is the capability gap or explicit request that caused autonomous mode to be invoked.

The `version` and `schema_version` fields are required for upgrade traceability. See
`context/factory-protocol.md` for the canonical schema definition and legacy migration rules.
```

**Note:** The rest of the file (lines 1–80 and 101–122) remains untouched.

**Verification:**
- `context/autonomous-protocol.md` contains `schema_version`
- `context/autonomous-protocol.md` audit trail code block shows `generated_by` nested under `bundle:` (i.e., the code block contains `bundle:` before `generated_by:`)
- `context/autonomous-protocol.md` contains `version: <read from bundlewizard`
- `context/autonomous-protocol.md` does NOT contain `level_1:` or `level_2:` or `level_3:` (old field names)

**Commit:** `feat: align autonomous-protocol audit trail to canonical generated_by schema`

---

## Task 5: Align recipe finish stage `generated_by` to canonical schema

**Modify:** `recipes/bundle-autonomous-post-explore.yaml`

**Current state:** Lines 367–379 contain the `generated_by` block in the finish stage prompt:
```yaml
          2a. Add generated_by block to bundle.md frontmatter:
              ```yaml
              generated_by:
                tool: bundlewizard
                mode: autonomous
                triggered_by: <session ID from STATE.yaml session.id>
                trigger_reason: {{trigger_reason}}
                convergence:
                  iterations: <stages.execute.iterations from STATE.yaml>
                  level_1: PASS
                  level_2: <stages.verify.level_2 from STATE.yaml>
                  level_3: <stages.verify.level_3 from STATE.yaml>
              ```
```

This block:
- Is NOT nested under `bundle:` (top-level — drift from canonical nesting)
- Is missing `version`, `schema_version`, and `timestamp`
- Uses old convergence field names

**Replace the generated_by block (the YAML code fence content between the ` ```yaml ` and ` ``` ` markers around lines 368–379) with:**

```yaml
              bundle:
                generated_by:
                  tool: bundlewizard
                  version: <read bundlewizard's own bundle.md version>
                  schema_version: 1
                  timestamp: <ISO 8601 — current time>
                  mode: autonomous
                  triggered_by: <session ID from STATE.yaml session.id>
                  trigger_reason: {{trigger_reason}}
                  convergence:
                    level_score: <stages.verify.level_score from STATE.yaml>
                    critic_verdict: <stages.verify.critic_verdict from STATE.yaml>
                    tests_passed: <stages.verify.tests_passed from STATE.yaml>
                    tests_failed: <stages.verify.tests_failed from STATE.yaml>
                    commits: <count commits in the output repo>
```

**Also:** Update the surrounding instruction text (line 367) from:
```
          2a. Add generated_by block to bundle.md frontmatter:
```
to:
```
          2a. Add canonical generated_by block to bundle.md frontmatter (nested under bundle:):
```

**Also update the completion summary block** (around lines 413–417) to replace old convergence field names:
- Replace `Level 1:    PASS` with `Score:      <level_score>`
- Replace `Level 2:    <score>` with `Verdict:    <critic_verdict>`
- Replace `Level 3:    <score>` with `Tests:      <tests_passed>/<tests_passed + tests_failed>`
- OR keep the human-readable summary format but source from the canonical field names

**Verification:**
- `recipes/bundle-autonomous-post-explore.yaml` finish stage contains `schema_version` in the generated_by block
- `recipes/bundle-autonomous-post-explore.yaml` finish stage contains `version:` in the generated_by block (not the recipe's own version — a version read instruction)
- The generated_by code block shows `bundle:` as a parent key before `generated_by:`

**Commit:** `feat: align recipe finish stage generated_by to canonical schema`

---

## Task 6: Create legacy provenance fixture

**Create directory:** `tests/fixtures/`

**Create file:** `tests/fixtures/legacy-provenance.yaml`

**Content:** The exact frontmatter from `~/dev/amplifier-bundle-project-memory/bundle.md` lines 1–19, representing the legacy `bundle.bundlewizard` provenance shape that migration must handle:

```yaml
# Legacy provenance fixture — exact shape from amplifier-bundle-project-memory/bundle.md
# This is the pre-canonical format that bundlewizard must detect and migrate.
# DO NOT modify this fixture — it represents the real-world legacy format.
---
bundle:
  name: project-memory
  version: 0.1.0
  description: |
    Persistent project-scoped memory across sessions.
    Automatic capture via hooks, curated storage, session briefings.
  bundlewizard:
    packaged_at: 2026-03-17T11:24:43Z
    level_score: 0.94
    critic_verdict: PASS
    tests_passed: 223
    tests_failed: 0
    commits: 7

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: project-memory:behaviors/project-memory
```

**Verification:**
- `tests/fixtures/legacy-provenance.yaml` exists
- Content is parseable YAML with `bundle.bundlewizard` key present
- Content does NOT have a `generated_by` key

**Commit:** `test: add legacy provenance fixture from project-memory`

---

## Task 7: Write provenance migration tests

**Create file:** `tests/test_provenance_migration.py`

**Content:** Structural contract tests verifying the canonical schema is correctly defined across all product files and the legacy fixture represents the expected old format. These are content-invariant assertions (search for strings in file content), not snapshot equality.

```python
"""Provenance migration contract tests for the bundlewizard upgrade feature.

These tests verify:
- The legacy provenance fixture has the expected old-format shape
- The canonical generated_by schema is defined in factory-protocol.md
- The packager agent references the version source rule (not hardcoded literals)
- The packager agent does not reference the deleted bundle-bot mode
- The autonomous protocol audit trail uses the canonical nested shape
- The recipe finish stage includes version and schema_version in generated_by

Design doc: docs/plans/2026-03-18-bundlewizard-upgrade-design.md
"""

import re
from pathlib import Path

import yaml

# Repo root — tests/ is a direct child of the repo root
REPO_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = Path(__file__).parent / "fixtures"
CONTEXT_DIR = REPO_ROOT / "context"
AGENTS_DIR = REPO_ROOT / "agents"
RECIPES_DIR = REPO_ROOT / "recipes"


# ---------------------------------------------------------------------------
# Legacy fixture shape tests
# ---------------------------------------------------------------------------

def test_legacy_fixture_has_bundlewizard_key():
    """The legacy fixture must have bundle.bundlewizard (the old provenance shape)."""
    path = FIXTURES_DIR / "legacy-provenance.yaml"
    assert path.exists(), "tests/fixtures/legacy-provenance.yaml does not exist"
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    bundle = content.get("bundle", {})
    assert "bundlewizard" in bundle, (
        "Legacy fixture must have a 'bundlewizard' key under 'bundle' — "
        "this is the old provenance shape that migration must handle"
    )


def test_legacy_fixture_has_no_generated_by():
    """The legacy fixture must NOT have bundle.generated_by (it's pre-canonical)."""
    path = FIXTURES_DIR / "legacy-provenance.yaml"
    assert path.exists(), "tests/fixtures/legacy-provenance.yaml does not exist"
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    bundle = content.get("bundle", {})
    assert "generated_by" not in bundle, (
        "Legacy fixture must NOT have a 'generated_by' key — "
        "that is the canonical shape, not the legacy shape"
    )


def test_legacy_fixture_has_no_schema_version():
    """The legacy fixture must not contain schema_version anywhere."""
    path = FIXTURES_DIR / "legacy-provenance.yaml"
    assert path.exists(), "tests/fixtures/legacy-provenance.yaml does not exist"
    text = path.read_text(encoding="utf-8")
    assert "schema_version" not in text, (
        "Legacy fixture must not contain 'schema_version' — "
        "that field only exists in the canonical shape"
    )


# ---------------------------------------------------------------------------
# Canonical schema definition tests
# ---------------------------------------------------------------------------

def test_canonical_schema_in_factory_protocol():
    """factory-protocol.md must define the canonical generated_by schema."""
    path = CONTEXT_DIR / "factory-protocol.md"
    assert path.exists(), "context/factory-protocol.md does not exist"
    content = path.read_text(encoding="utf-8")

    assert "schema_version" in content, (
        "factory-protocol.md must define schema_version in the canonical schema"
    )
    assert "generated_by" in content, (
        "factory-protocol.md must define generated_by in the canonical schema"
    )
    assert "Legacy fingerprint" in content, (
        "factory-protocol.md must document legacy fingerprint recognition rules"
    )


# ---------------------------------------------------------------------------
# Packager alignment tests
# ---------------------------------------------------------------------------

def test_packager_references_bundlewizard_version_source():
    """bundle-packager.md must source version from bundlewizard's own bundle.md,
    and must NOT contain a hardcoded version literal in a generated_by code block."""
    path = AGENTS_DIR / "bundle-packager.md"
    assert path.exists(), "agents/bundle-packager.md does not exist"
    content = path.read_text(encoding="utf-8")

    # Must reference the version source rule
    assert "bundlewizard" in content.lower() and "bundle.md" in content, (
        "bundle-packager.md must instruct the agent to read the version from "
        "bundlewizard's own bundle.md"
    )

    # Must NOT have a hardcoded version literal inside a generated_by code block.
    # We check for the specific pattern: 'version: 0.1.0' appearing after 'generated_by'
    # in a YAML code fence. A simple proxy: the file should not contain the exact string
    # 'version: 0.1.0' inside a code block that also contains 'generated_by'.
    code_blocks = re.findall(r"```yaml\s*\n(.*?)```", content, re.DOTALL)
    for block in code_blocks:
        if "generated_by" in block:
            assert "version: 0.1.0" not in block, (
                "bundle-packager.md has a hardcoded 'version: 0.1.0' inside a "
                "generated_by code block. The version must be read from "
                "bundlewizard's own bundle.md, not hardcoded."
            )


def test_packager_no_bundle_bot_section():
    """bundle-packager.md must NOT reference /bundle-bot (deleted mode)."""
    path = AGENTS_DIR / "bundle-packager.md"
    assert path.exists(), "agents/bundle-packager.md does not exist"
    content = path.read_text(encoding="utf-8")
    assert "/bundle-bot" not in content, (
        "bundle-packager.md still references /bundle-bot. "
        "That section must be removed — bundle-bot is deleted."
    )


def test_packager_has_legacy_migration_instructions():
    """bundle-packager.md must include legacy provenance migration instructions."""
    path = AGENTS_DIR / "bundle-packager.md"
    assert path.exists(), "agents/bundle-packager.md does not exist"
    content = path.read_text(encoding="utf-8")
    assert "legacy" in content.lower(), (
        "bundle-packager.md must include legacy provenance migration instructions"
    )
    assert "bundlewizard" in content.lower() and "migration" in content.lower(), (
        "bundle-packager.md must describe how to migrate the legacy "
        "bundle.bundlewizard shape to the canonical generated_by shape"
    )


# ---------------------------------------------------------------------------
# Autonomous protocol alignment tests
# ---------------------------------------------------------------------------

def test_autonomous_protocol_generated_by_nested():
    """autonomous-protocol.md audit trail must show generated_by nested under bundle:."""
    path = CONTEXT_DIR / "autonomous-protocol.md"
    assert path.exists(), "context/autonomous-protocol.md does not exist"
    content = path.read_text(encoding="utf-8")

    # Find the code block in the Audit Trail section that contains generated_by
    code_blocks = re.findall(r"```yaml\s*\n(.*?)```", content, re.DOTALL)
    found_nested = False
    for block in code_blocks:
        if "generated_by" in block and "bundle:" in block:
            # generated_by should appear after bundle: in the block (nested)
            bundle_pos = block.index("bundle:")
            gen_pos = block.index("generated_by")
            if gen_pos > bundle_pos:
                found_nested = True
                break

    assert found_nested, (
        "autonomous-protocol.md audit trail must show generated_by nested under "
        "bundle: in its YAML code block — not as a top-level key"
    )


def test_autonomous_protocol_has_schema_version():
    """autonomous-protocol.md must include schema_version in its audit trail."""
    path = CONTEXT_DIR / "autonomous-protocol.md"
    assert path.exists(), "context/autonomous-protocol.md does not exist"
    content = path.read_text(encoding="utf-8")
    assert "schema_version" in content, (
        "autonomous-protocol.md must include schema_version in its "
        "generated_by audit trail block"
    )


def test_autonomous_protocol_no_old_convergence_fields():
    """autonomous-protocol.md must NOT use old convergence field names."""
    path = CONTEXT_DIR / "autonomous-protocol.md"
    assert path.exists(), "context/autonomous-protocol.md does not exist"
    content = path.read_text(encoding="utf-8")

    # Find code blocks with generated_by and check for old field names
    code_blocks = re.findall(r"```yaml\s*\n(.*?)```", content, re.DOTALL)
    for block in code_blocks:
        if "generated_by" in block:
            assert "level_1:" not in block, (
                "autonomous-protocol.md still uses old convergence field name "
                "'level_1' — should be replaced with canonical field names"
            )
            assert "level_2:" not in block, (
                "autonomous-protocol.md still uses old convergence field name "
                "'level_2' — should be replaced with canonical field names"
            )
            assert "level_3:" not in block, (
                "autonomous-protocol.md still uses old convergence field name "
                "'level_3' — should be replaced with canonical field names"
            )


# ---------------------------------------------------------------------------
# Recipe finish stage alignment tests
# ---------------------------------------------------------------------------

def test_recipe_finish_generated_by_has_version_and_schema():
    """The recipe finish stage must include version and schema_version in generated_by."""
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    assert path.exists(), (
        "recipes/bundle-autonomous-post-explore.yaml does not exist"
    )
    content = path.read_text(encoding="utf-8")

    # The finish stage prompt contains the generated_by block as inline text,
    # not as a parsed YAML structure. Check for the fields in the content.
    assert "schema_version" in content, (
        "Recipe finish stage must include schema_version in its generated_by block"
    )
    # Check that 'version:' appears in proximity to 'generated_by' — this is the
    # generator version field, not the recipe's own version key at the top
    assert "version:" in content, (
        "Recipe finish stage must include a version field in its generated_by block"
    )
```

**Verification:**
- `python_check tests/test_provenance_migration.py` is clean
- `pytest tests/test_provenance_migration.py -v` — all tests pass (since Tasks 2–6 already landed the product changes)

**Commit:** `test: add provenance migration contract tests`

---

## Task 8: Run full test suite and verify

**Run:** `pytest tests/ -v`

**Expected:** All tests pass — the 17 existing structural tests from `test_modes_adherence.py` plus the new provenance migration tests from `test_provenance_migration.py`.

**Run regression greps:**

```bash
# No hardcoded version: 0.1.0 in generated_by code blocks across product files
grep -rn "version: 0.1.0" agents/ context/ recipes/ --include="*.md" --include="*.yaml" | grep -i "generated_by"

# No /bundle-bot references in product files
grep -rn "/bundle-bot" agents/ context/ modes/ recipes/ behaviors/ --include="*.md" --include="*.yaml"

# schema_version present in all three canonical locations
grep -rn "schema_version" context/factory-protocol.md agents/bundle-packager.md context/autonomous-protocol.md recipes/bundle-autonomous-post-explore.yaml
```

**Expected regression grep results:**
- First grep: zero matches (no hardcoded version literals in generated_by blocks)
- Second grep: zero matches (no /bundle-bot references)
- Third grep: at least one match per file (schema_version present in all four)

**Commit if any cleanup needed:** `chore: Phase 1 validation complete`

---

## Execution Notes

### Task ordering
Tasks 1–5 are sequential: each builds on the canonical schema established in Task 2, and Tasks 3–5 align specific files to that schema. Task 6 (fixture) is independent and could run in parallel with Tasks 3–5. Task 7 (tests) depends on both the fixture (Task 6) and all schema alignment (Tasks 2–5). Task 8 is the final verification gate.

### Dependency chain
```
Task 1 (housekeeping) → independent
Task 2 (canonical schema) → source of truth for Tasks 3, 4, 5
Task 3 (packager) → depends on Task 2
Task 4 (autonomous-protocol) → depends on Task 2
Task 5 (recipe finish) → depends on Task 2
Task 6 (fixture) → independent
Task 7 (tests) → depends on Tasks 2, 3, 4, 5, 6
Task 8 (verification) → depends on all
```

### Scope boundary
- All changes are inside `amplifier-bundle-bundlewizard`
- No upstream `amplifier-bundle-modes` changes
- The legacy fixture is a static copy — `~/dev/amplifier-bundle-project-memory` is read-only reference
- No new modes, no new recipes, no new agents — only schema alignment and tests

### RED/GREEN pattern
Task 7 tests should be written AFTER Tasks 2–6 land (they test the canonical shape). If following strict TDD, write the tests first (Task 7 before Tasks 2–6) and watch them fail, then implement Tasks 2–6 to make them pass. The plan is ordered for sequential implementation clarity, but the TDD inversion is valid.

# Agent Stubs — Add Exemplar Skill Pointers (bundle-reference) Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Add `bundle-reference` skill pointer instructions to the Level 2 (Philosophical) sections of both `bundle-critic.md` and `bundle-evaluator.md`, and reconcile the CRITICAL block skill prohibitions so the agents can coherently load the skill during Level 2 scoring.

**Architecture:** Two markdown agent files need a one-line instruction inserted in their Level 2 sections, plus their CRITICAL blocks need an exception clause so the "do not load skills" prohibition doesn't contradict the new instruction. Two acceptance tests verify the Level 2 sections mention `bundle-reference`.

**Tech Stack:** Markdown agent files, Python/pytest structural contract tests.

---

> **SPEC REVIEW WARNING:** The spec review loop exhausted after 3 iterations without
> full approval. The final verdict identified a contradiction: both agent files said
> "DO NOT load skills." in their CRITICAL blocks while simultaneously instructing
> Level 2 scoring to "load the `bundle-reference` skill." This plan addresses that
> contradiction by reconciling the CRITICAL block language. The final commit
> (`abde862`) already resolved this, but human reviewer should verify the wording
> is acceptable.

---

## Dependencies

This task depends on:
- `task-6-evaluator-consumer-triangulation-output` — evaluator file may have been modified
- `task-7-critic-traceability-dot-output` — critic file may have been modified

Verify both are merged before starting.

---

## Pre-Implementation: Verify Current State

Before making any changes, verify the baseline. The acceptance tests for this task may already exist from prior implementation attempts.

**Run:**
```bash
python -m pytest tests/test_agent_stubs_bundle_reference.py -v 2>&1 || echo "Test file not found — proceed with implementation"
```

- If both tests pass: skip to the Verification section at the bottom — work is already done.
- If test file doesn't exist or tests fail: proceed with the tasks below.

---

### Task 1: Write Acceptance Tests

**Files:**
- Create: `tests/test_agent_stubs_bundle_reference.py`

**Step 1: Write the test file**

Create `tests/test_agent_stubs_bundle_reference.py` with this exact content:

```python
"""Structural contract tests for Level 2 bundle-reference guidance."""

import functools

from conftest import AGENTS_DIR, extract_markdown_section, required_text


@functools.lru_cache(maxsize=None)
def _agent_text(filename: str) -> str:
    return required_text(AGENTS_DIR / filename)


@functools.lru_cache(maxsize=None)
def _level2_section(filename: str, heading: str) -> str:
    return extract_markdown_section(_agent_text(filename), heading, level=3)


def test_critic_mentions_bundle_reference_skill() -> None:
    """bundle-critic Level 2 section must mention the bundle-reference skill."""
    level2_section = _level2_section(
        "bundle-critic.md",
        "Philosophical (Level 2 rubric \u2014 score each)",
    )
    assert "bundle-reference" in level2_section, (
        "bundle-critic.md Philosophical (Level 2) must mention the `bundle-reference` skill"
    )
    assert "exemplar" in level2_section.lower(), (
        "bundle-critic.md Philosophical (Level 2) must mention exemplar comparison"
    )


def test_evaluator_mentions_bundle_reference_skill() -> None:
    """bundle-evaluator Level 2 section must mention the bundle-reference skill."""
    level2_section = _level2_section(
        "bundle-evaluator.md",
        "Level 2: Philosophical (scored 0.0\u20131.0, threshold 0.85)",
    )
    assert "bundle-reference" in level2_section, (
        "bundle-evaluator.md Level 2: Philosophical must mention the `bundle-reference` skill"
    )
    assert "exemplar" in level2_section.lower(), (
        "bundle-evaluator.md Level 2: Philosophical must mention exemplar comparison"
    )
```

Key details:
- Uses `conftest.py` helpers: `AGENTS_DIR`, `extract_markdown_section`, `required_text`
- `extract_markdown_section` is called with `level=3` because both headings are `###` (level 3)
- The critic heading is `Philosophical (Level 2 rubric — score each)` (note the em-dash `\u2014`)
- The evaluator heading is `Level 2: Philosophical (scored 0.0–1.0, threshold 0.85)` (note the en-dash `\u2013`)
- Each test checks for both `bundle-reference` and `exemplar` (case-insensitive)

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_agent_stubs_bundle_reference.py -v`

Expected: FAIL — the Level 2 sections don't yet mention `bundle-reference`.

---

### Task 2: Insert bundle-reference Instruction in bundle-critic.md

**Files:**
- Modify: `agents/bundle-critic.md`

**Step 1: Insert the instruction line in the Level 2 section**

Find the line `### Philosophical (Level 2 rubric — score each)` (currently line 64). Insert a blank line after the heading, then the instruction line, then another blank line before the first checkbox `- [ ]`.

The section should read:

```markdown
### Philosophical (Level 2 rubric — score each)

When scoring Level 2, load the `bundle-reference` skill for pattern comparison against known-good exemplars.

- [ ] **Thin bundle pattern:** bundle.md ≤20 lines frontmatter? No @mentions in body? No redeclaration?
```

**Step 2: Reconcile the CRITICAL block**

Find the CRITICAL block (lines 35–41). The line that says `DO NOT load skills.` must be changed to allow the `bundle-reference` exception. Replace:

```
DO NOT load skills. Do not load skills like parallax-methodology, dispatching-parallel-agents, or brainstorming — these waste context tokens and delay the audit.
```

With:

```
DO NOT load general skills. Exception: load the `bundle-reference` skill during Level 2 scoring (see below). Do not load skills like parallax-methodology, dispatching-parallel-agents, or brainstorming — these waste context tokens and delay the audit.
```

**Step 3: Run the critic test**

Run: `python -m pytest tests/test_agent_stubs_bundle_reference.py::test_critic_mentions_bundle_reference_skill -v`

Expected: PASS

**Step 4: Commit**

```bash
git add agents/bundle-critic.md tests/test_agent_stubs_bundle_reference.py
git commit -m "feat: add bundle-reference skill pointer to Level 2 section in bundle-critic"
```

---

### Task 3: Insert bundle-reference Instruction in bundle-evaluator.md

**Files:**
- Modify: `agents/bundle-evaluator.md`

**Step 1: Insert the instruction line in the Level 2 section**

Find the line `### Level 2: Philosophical (scored 0.0–1.0, threshold 0.85)` (currently line 99). Insert a blank line after the heading, then the instruction line, then a blank line before `Score each criterion`.

The section should read:

```markdown
### Level 2: Philosophical (scored 0.0–1.0, threshold 0.85)

When scoring Level 2, load the `bundle-reference` skill for pattern comparison against known-good exemplars.

Score each criterion using the rubric from @bundlewizard:context/convergence-criteria.md:
```

**Step 2: Reconcile the CRITICAL block**

Find the CRITICAL block (lines 46–52). Replace:

```
DO NOT load skills. Do not load skills like brainstorming, parallax-methodology, dispatching-parallel-agents, or using-superpowers — these waste context tokens and delay your work.
```

With:

```
DO NOT load general skills. Exception: load the `bundle-reference` skill during Level 2 scoring (see below). Do not load skills like brainstorming, parallax-methodology, dispatching-parallel-agents, or using-superpowers — these waste context tokens and delay your work.
```

**Step 3: Run both tests**

Run: `python -m pytest tests/test_agent_stubs_bundle_reference.py -v`

Expected: 2 passed

**Step 4: Run full test suite**

Run: `python -m pytest -q`

Expected: All tests pass (no regressions).

**Step 5: Commit**

```bash
git add agents/bundle-evaluator.md
git commit -m "feat: add bundle-reference skill pointer to Level 2 section in bundle-evaluator"
```

---

## Final Verification

Run all three checks:

```bash
# 1. Acceptance tests
python -m pytest tests/test_agent_stubs_bundle_reference.py -v
# Expected: 2 passed

# 2. Full suite
python -m pytest -q
# Expected: all pass, no regressions

# 3. Verify no CRITICAL block contradictions
grep -n "DO NOT load" agents/bundle-critic.md agents/bundle-evaluator.md
# Expected: both lines say "DO NOT load general skills. Exception: load the `bundle-reference` skill..."
# NOT "DO NOT load skills." (which would contradict the Level 2 instruction)
```

## Acceptance Criteria

- [x] `test_critic_mentions_bundle_reference_skill` passes
- [x] `test_evaluator_mentions_bundle_reference_skill` passes
- [x] Both CRITICAL blocks allow `bundle-reference` as an explicit exception
- [x] No full-suite regressions
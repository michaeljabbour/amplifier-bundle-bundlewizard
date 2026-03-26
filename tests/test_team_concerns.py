"""Structural contract tests for the team-concerns enhancement.

Verifies that ``agents/bundle-spec-writer.md`` contains all four new spec
template sections required by the team-concerns enhancement:

  - ## Requirements
  - ## Consumer Experience
  - ## Scope Exclusions
  - ## Traceability Matrix

Also verifies section ordering, table column headers, step-5 instruction
updates, and that original sections are preserved.

All 27 tests in this module form the acceptance gate for task-1-spec-template.
"""

import re

from conftest import AGENTS_DIR, CONTEXT_DIR, REPO_ROOT  # noqa: F401 – CONTEXT_DIR kept for API

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

SPEC_WRITER_MD = AGENTS_DIR / "bundle-spec-writer.md"

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _read(path) -> str:
    """Return file content as UTF-8 text; asserts the file exists."""
    assert path.exists(), f"{path} does not exist"
    return path.read_text(encoding="utf-8")


def _extract_template_block(text: str) -> str:
    """Extract the content of the first ```markdown … ``` code block.

    Returns the raw inner text (without the fence lines) so tests can assert
    on template section headings independently of the surrounding prose.
    """
    match = re.search(r"```markdown\n(.*?)```", text, re.DOTALL)
    assert match, "No ```markdown code block found in bundle-spec-writer.md"
    return match.group(1)


# ---------------------------------------------------------------------------
# 1. File-existence gate
# ---------------------------------------------------------------------------


def test_bundle_spec_writer_file_exists():
    """agents/bundle-spec-writer.md must exist."""
    assert SPEC_WRITER_MD.exists(), f"{SPEC_WRITER_MD} does not exist"


# ---------------------------------------------------------------------------
# 2. Template code block presence
# ---------------------------------------------------------------------------


def test_spec_template_code_block_exists():
    """The file must contain a ```markdown code block (the spec template)."""
    text = _read(SPEC_WRITER_MD)
    _extract_template_block(text)  # asserts internally


# ---------------------------------------------------------------------------
# 3. Original sections preserved
# ---------------------------------------------------------------------------


def test_spec_template_contains_file_structure_section():
    """## File Structure must still be present in the spec template."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    assert "## File Structure" in block, "## File Structure missing from spec template"


def test_spec_template_contains_convergence_expectations_section():
    """## Convergence Expectations must still be present in the spec template."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    assert "## Convergence Expectations" in block, (
        "## Convergence Expectations missing from spec template"
    )


# ---------------------------------------------------------------------------
# 4. New section presence (primary acceptance criteria)
# ---------------------------------------------------------------------------


def test_spec_template_has_requirements_section():
    """The spec template must contain a ## Requirements section."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    assert "## Requirements" in block, "## Requirements missing from spec template"


def test_spec_template_has_consumer_experience_section():
    """The spec template must contain a ## Consumer Experience section."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    assert "## Consumer Experience" in block, (
        "## Consumer Experience missing from spec template"
    )


def test_spec_template_has_scope_exclusions_section():
    """The spec template must contain a ## Scope Exclusions section."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    assert "## Scope Exclusions" in block, (
        "## Scope Exclusions missing from spec template"
    )


def test_spec_template_has_traceability_matrix_section():
    """The spec template must contain a ## Traceability Matrix section."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    assert "## Traceability Matrix" in block, (
        "## Traceability Matrix missing from spec template"
    )


# ---------------------------------------------------------------------------
# 5. ## Requirements table columns
# ---------------------------------------------------------------------------


def test_requirements_section_has_id_column():
    """## Requirements table must have an ID column."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    req_idx = block.index("## Requirements")
    # Look for the table header near the Requirements heading
    snippet = block[req_idx : req_idx + 400]
    assert "ID" in snippet, "## Requirements table must include an ID column"


def test_requirements_section_has_requirement_column():
    """## Requirements table must have a Requirement column."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    req_idx = block.index("## Requirements")
    snippet = block[req_idx : req_idx + 400]
    assert "Requirement" in snippet, (
        "## Requirements table must include a Requirement column"
    )


def test_requirements_section_has_acceptance_criterion_column():
    """## Requirements table must have an Acceptance Criterion column."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    req_idx = block.index("## Requirements")
    snippet = block[req_idx : req_idx + 400]
    assert "Acceptance Criterion" in snippet, (
        "## Requirements table must include an Acceptance Criterion column"
    )


# ---------------------------------------------------------------------------
# 6. ## Consumer Experience content
# ---------------------------------------------------------------------------


def test_consumer_experience_has_target_persona():
    """## Consumer Experience must mention a target persona."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    ce_idx = block.index("## Consumer Experience")
    # Find the next ## heading to bound the section
    next_section = re.search(r"\n## ", block[ce_idx + 1 :])
    end = ce_idx + 1 + next_section.start() if next_section else len(block)
    snippet = block[ce_idx:end]
    assert re.search(r"persona", snippet, re.IGNORECASE), (
        "## Consumer Experience must reference a target persona"
    )


def test_consumer_experience_has_first_run_expectations():
    """## Consumer Experience must describe first-run expectations."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    ce_idx = block.index("## Consumer Experience")
    next_section = re.search(r"\n## ", block[ce_idx + 1 :])
    end = ce_idx + 1 + next_section.start() if next_section else len(block)
    snippet = block[ce_idx:end]
    assert re.search(r"first.run", snippet, re.IGNORECASE), (
        "## Consumer Experience must describe first-run expectations"
    )


def test_consumer_experience_has_progressive_disclosure():
    """## Consumer Experience must include progressive disclosure bullets."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    ce_idx = block.index("## Consumer Experience")
    next_section = re.search(r"\n## ", block[ce_idx + 1 :])
    end = ce_idx + 1 + next_section.start() if next_section else len(block)
    snippet = block[ce_idx:end]
    assert re.search(r"progressive disclosure", snippet, re.IGNORECASE), (
        "## Consumer Experience must include progressive disclosure content"
    )


# ---------------------------------------------------------------------------
# 7. ## Scope Exclusions content
# ---------------------------------------------------------------------------


def test_scope_exclusions_has_does_not_content():
    """## Scope Exclusions must describe what the bundle does NOT do."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    se_idx = block.index("## Scope Exclusions")
    next_section = re.search(r"\n## ", block[se_idx + 1 :])
    end = se_idx + 1 + next_section.start() if next_section else len(block)
    snippet = block[se_idx:end]
    assert re.search(r"not|omit|exclud|deliberate", snippet, re.IGNORECASE), (
        "## Scope Exclusions must describe what the bundle does NOT do"
    )


# ---------------------------------------------------------------------------
# 8. ## Traceability Matrix table columns
# ---------------------------------------------------------------------------


def test_traceability_matrix_has_requirement_column():
    """## Traceability Matrix table must have a Requirement column."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    tm_idx = block.index("## Traceability Matrix")
    snippet = block[tm_idx : tm_idx + 400]
    assert "Requirement" in snippet, (
        "## Traceability Matrix must include a Requirement column"
    )


def test_traceability_matrix_has_artifact_column():
    """## Traceability Matrix table must have an Artifact column."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    tm_idx = block.index("## Traceability Matrix")
    snippet = block[tm_idx : tm_idx + 400]
    assert "Artifact" in snippet, (
        "## Traceability Matrix must include an Artifact column"
    )


def test_traceability_matrix_has_status_column():
    """## Traceability Matrix table must have a Status column."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    tm_idx = block.index("## Traceability Matrix")
    snippet = block[tm_idx : tm_idx + 400]
    assert "Status" in snippet, "## Traceability Matrix must include a Status column"


# ---------------------------------------------------------------------------
# 9. Section ordering within the template
# ---------------------------------------------------------------------------


def test_file_structure_appears_before_requirements():
    """## File Structure must appear before ## Requirements in the template."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    assert block.index("## File Structure") < block.index("## Requirements"), (
        "## File Structure must precede ## Requirements"
    )


def test_requirements_appears_before_components():
    """## Requirements must appear before ## Components in the template."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    assert block.index("## Requirements") < block.index("## Components"), (
        "## Requirements must precede ## Components"
    )


def test_consumer_experience_appears_before_components():
    """## Consumer Experience must appear before ## Components in the template."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    assert block.index("## Consumer Experience") < block.index("## Components"), (
        "## Consumer Experience must precede ## Components"
    )


def test_scope_exclusions_appears_before_components():
    """## Scope Exclusions must appear before ## Components in the template."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    assert block.index("## Scope Exclusions") < block.index("## Components"), (
        "## Scope Exclusions must precede ## Components"
    )


def test_traceability_matrix_appears_after_convergence():
    """## Traceability Matrix must appear after ## Convergence Expectations."""
    text = _read(SPEC_WRITER_MD)
    block = _extract_template_block(text)
    assert block.index("## Convergence Expectations") < block.index(
        "## Traceability Matrix"
    ), "## Traceability Matrix must follow ## Convergence Expectations"


# ---------------------------------------------------------------------------
# 10. Step-5 instruction updates
# ---------------------------------------------------------------------------


def test_step5_mentions_requirements():
    """Step 5 prose (outside the template block) must reference Requirements."""
    text = _read(SPEC_WRITER_MD)
    # Step 5 is the prose immediately before the template code block
    step5_match = re.search(
        r"### 5\. Produce bundle-spec\.md(.*?)```markdown", text, re.DOTALL
    )
    assert step5_match, "Step 5 section not found"
    step5_prose = step5_match.group(1)
    assert re.search(r"[Rr]equirements", step5_prose), (
        "Step 5 instructions must reference Requirements"
    )


def test_step5_mentions_consumer_experience():
    """Step 5 prose must reference Consumer Experience."""
    text = _read(SPEC_WRITER_MD)
    step5_match = re.search(
        r"### 5\. Produce bundle-spec\.md(.*?)```markdown", text, re.DOTALL
    )
    assert step5_match, "Step 5 section not found"
    step5_prose = step5_match.group(1)
    assert re.search(r"[Cc]onsumer [Ee]xperience", step5_prose), (
        "Step 5 instructions must reference Consumer Experience"
    )


def test_step5_mentions_scope_exclusions():
    """Step 5 prose must reference Scope Exclusions."""
    text = _read(SPEC_WRITER_MD)
    step5_match = re.search(
        r"### 5\. Produce bundle-spec\.md(.*?)```markdown", text, re.DOTALL
    )
    assert step5_match, "Step 5 section not found"
    step5_prose = step5_match.group(1)
    assert re.search(r"[Ss]cope [Ee]xclusions", step5_prose), (
        "Step 5 instructions must reference Scope Exclusions"
    )


def test_step5_mentions_r_id():
    """Step 5 instructions must reference R-ID (one per interview finding)."""
    text = _read(SPEC_WRITER_MD)
    step5_match = re.search(
        r"### 5\. Produce bundle-spec\.md(.*?)```markdown", text, re.DOTALL
    )
    assert step5_match, "Step 5 section not found"
    step5_prose = step5_match.group(1)
    assert re.search(r"R-ID|R\d+", step5_prose), (
        "Step 5 instructions must reference R-ID requirement identifiers"
    )

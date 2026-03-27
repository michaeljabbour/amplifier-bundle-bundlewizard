"""Structural contract tests for Explorer Job 0 Suitability Check and Consumer Context Question.

These tests verify that bundle-explorer.md has been updated with:
- A Job 0: Suitability Check section before Job 1
- The heading changed from 'Four Jobs' to 'Five Jobs'
- A 4-row suitability table with correct signal/action content
- Skip logic for clearly-fitting requests
- A consumer context question numbered as item 6 in the For Create New interview section

All tests in this file were RED (failing) until implementation was complete.
"""

from pathlib import Path

# Repo root — tests/ is a direct child of the repo root
REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / "agents"


def _load_explorer() -> str:
    """Load bundle-explorer.md content once, with explicit UTF-8 encoding."""
    return (AGENTS_DIR / "bundle-explorer.md").read_text(encoding="utf-8")


def test_explorer_has_suitability_check():
    """bundle-explorer.md must contain a Job 0: Suitability Check section."""
    explorer = _load_explorer()
    assert "### Job 0: Suitability Check" in explorer, (
        "Expected '### Job 0: Suitability Check' section in agents/bundle-explorer.md"
    )
    # Heading must be updated to Five Jobs
    assert "## Your Five Jobs" in explorer, (
        "Expected '## Your Five Jobs' heading in agents/bundle-explorer.md "
        "(was 'Your Four Jobs')"
    )
    # Job 0 must appear before Job 1 in the document
    job0_pos = explorer.index("### Job 0: Suitability Check")
    job1_pos = explorer.index("### Job 1: Determine the Path")
    assert job0_pos < job1_pos, (
        "Job 0 must appear before Job 1 in agents/bundle-explorer.md"
    )


def test_explorer_suitability_table_content():
    """Job 0 table must contain all four signal/action rows with correct content."""
    explorer = _load_explorer()

    # Row 1: Custom Python modules → partial scope
    assert "Needs custom Python modules" in explorer, (
        "Expected row for 'Needs custom Python modules' in Job 0 suitability table"
    )
    assert "Flag as partial scope" in explorer, (
        "Expected 'Flag as partial scope' action in Job 0 suitability table"
    )

    # Row 2: Trivial 5-line behavior → quick path
    assert "Trivially a 5-line behavior" in explorer, (
        "Expected row for 'Trivially a 5-line behavior' in Job 0 suitability table"
    )
    assert "Suggest quick path" in explorer, (
        "Expected 'Suggest quick path' action in Job 0 suitability table"
    )

    # Row 3: Full dev-machine setup → steer toward dev-machine
    assert "Needs full dev-machine setup" in explorer, (
        "Expected row for 'Needs full dev-machine setup' in Job 0 suitability table"
    )
    assert "Steer toward dev-machine" in explorer, (
        "Expected 'Steer toward dev-machine' action in Job 0 suitability table"
    )

    # Row 4: Fits bundlewizard → proceed to Job 1
    assert "Fits bundlewizard" in explorer, (
        "Expected row for 'Fits bundlewizard' in Job 0 suitability table"
    )
    assert "Proceed to Job 1" in explorer, (
        "Expected 'Proceed to Job 1' action in Job 0 suitability table"
    )


def test_explorer_suitability_skip_logic():
    """Job 0 must include skip logic for clearly-fitting requests."""
    explorer = _load_explorer()
    assert "Skip logic:" in explorer, (
        "Expected 'Skip logic:' sentence in Job 0 Suitability Check section"
    )
    assert "skip Job 0 and proceed directly to Job 1" in explorer, (
        "Expected skip instruction 'skip Job 0 and proceed directly to Job 1' in "
        "agents/bundle-explorer.md"
    )


def test_explorer_has_consumer_question():
    """bundle-explorer.md must contain a consumer context question in the For Create New interview."""
    explorer = _load_explorer()
    # The question must mention consumer context
    assert "Consumer context" in explorer, (
        "Expected 'Consumer context' question in agents/bundle-explorer.md"
    )
    # The question must ask about experience level with Amplifier
    assert "experience level with Amplifier" in explorer, (
        "Expected question about experience level with Amplifier in agents/bundle-explorer.md"
    )
    # The consumer context question must appear in the For Create New section
    # and before For Improve Existing
    create_new_pos = explorer.index("**For Create New")
    consumer_pos = explorer.index("Consumer context")
    improve_pos = explorer.index("**For Improve Existing:**")
    assert create_new_pos < consumer_pos < improve_pos, (
        "Consumer context question must appear in the 'For Create New' section "
        "and before '**For Improve Existing:**' in agents/bundle-explorer.md"
    )


def test_explorer_consumer_question_is_number_six():
    """Consumer context must be numbered as item 6 in the Create New interview sequence."""
    explorer = _load_explorer()
    assert "6. **Consumer context**" in explorer, (
        "Expected 'Consumer context' to be numbered as item 6 in the Create New "
        "interview sequence in agents/bundle-explorer.md"
    )

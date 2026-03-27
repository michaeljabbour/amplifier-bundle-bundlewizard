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
    """Job 0 table must contain all four signal/action rows with correct paired content.

    Validates row-level pairings — each signal must be matched with its correct action
    on the same markdown table row, and there must be exactly four data rows.
    """
    explorer = _load_explorer()

    # Extract the Job 0 section to scope all assertions to that section only
    assert "### Job 0: Suitability Check" in explorer, (
        "Prerequisite: '### Job 0: Suitability Check' must exist before checking table content"
    )
    assert "### Job 1: Determine the Path" in explorer, (
        "Prerequisite: '### Job 1: Determine the Path' must exist as the section boundary"
    )
    job0_start = explorer.index("### Job 0: Suitability Check")
    job1_start = explorer.index("### Job 1: Determine the Path")
    job0_section = explorer[job0_start:job1_start]

    # Parse table data rows (skip header row and separator row)
    table_rows = [
        line
        for line in job0_section.splitlines()
        if line.startswith("|")
        and not line.startswith("| Signal")
        and not line.startswith("|---")
    ]

    assert len(table_rows) == 4, (
        f"Expected exactly 4 data rows in the Job 0 suitability table, "
        f"got {len(table_rows)}:\n" + "\n".join(table_rows)
    )

    # Each signal must be paired with the correct action on the same row
    expected_pairs = [
        ("Needs custom Python modules", "Flag as partial scope"),
        ("Trivially a 5-line behavior", "Suggest quick path"),
        ("Needs full dev-machine setup", "Steer toward dev-machine"),
        ("Fits bundlewizard", "Proceed to Job 1"),
    ]

    for signal, action in expected_pairs:
        matching = [row for row in table_rows if signal in row and action in row]
        assert matching, (
            f"Expected a Job 0 table row pairing signal '{signal}' with action '{action}'. "
            f"No such row found. Table rows:\n" + "\n".join(table_rows)
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
    """Consumer context must be numbered as item 6, and Q1–Q6 must appear in order.

    Validates the full ordered sequence within the For Create New section so that
    reordering or removing earlier questions causes a failure, not just Q6 being absent.
    """
    explorer = _load_explorer()

    # Q6 must carry the correct label
    assert "6. **Consumer context**" in explorer, (
        "Expected 'Consumer context' to be numbered as item 6 in the Create New "
        "interview sequence in agents/bundle-explorer.md"
    )

    # Extract the For Create New section to scope sequence checks
    assert "**For Create New" in explorer, (
        "Prerequisite: '**For Create New' section must exist"
    )
    assert "**For Improve Existing:**" in explorer, (
        "Prerequisite: '**For Improve Existing:**' section must exist as boundary"
    )
    create_new_start = explorer.index("**For Create New")
    improve_start = explorer.index("**For Improve Existing:**")
    create_new_section = explorer[create_new_start:improve_start]

    # All six questions must be present in the section
    expected_questions = [
        ("1.", "What problem does this solve"),
        ("2.", "Ecosystem check"),
        ("3.", "What tier"),
        ("4.", "What capabilities"),
        ("5.", "Delegation decisions"),
        ("6.", "Consumer context"),
    ]

    for num, phrase in expected_questions:
        assert phrase in create_new_section, (
            f"Expected question {num} (containing '{phrase}') in the 'For Create New' "
            f"section of agents/bundle-explorer.md"
        )

    # Questions must appear in ascending order (Q1 before Q2 before … before Q6)
    positions = [
        (num, phrase, create_new_section.index(phrase))
        for num, phrase in expected_questions
    ]
    for i in range(len(positions) - 1):
        curr_num, curr_phrase, curr_pos = positions[i]
        next_num, next_phrase, next_pos = positions[i + 1]
        assert curr_pos < next_pos, (
            f"Question {curr_num} ('{curr_phrase}') must appear before "
            f"question {next_num} ('{next_phrase}') in the 'For Create New' section"
        )

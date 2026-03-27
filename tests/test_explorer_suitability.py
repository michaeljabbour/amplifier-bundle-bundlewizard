"""Structural contract tests for Explorer Job 0 Suitability Check and Consumer Context Question.

These tests verify that bundle-explorer.md has been updated with:
- A Job 0: Suitability Check section before Job 1
- The heading changed from 'Four Jobs' to 'Five Jobs'
- A consumer context question (question 6) in the For Create New interview section

All tests in this file were RED (failing) until implementation was complete.
"""

from pathlib import Path

# Repo root — tests/ is a direct child of the repo root
REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / "agents"


def test_explorer_has_suitability_check():
    """bundle-explorer.md must contain a Job 0: Suitability Check section."""
    explorer = (AGENTS_DIR / "bundle-explorer.md").read_text()
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


def test_explorer_has_consumer_question():
    """bundle-explorer.md must contain a consumer context question in the For Create New interview."""
    explorer = (AGENTS_DIR / "bundle-explorer.md").read_text()
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

"""Evaluator consumer experience, triangulation, and output template tests.

Verify that agents/bundle-evaluator.md contains:
- Level 3 references to consumer experience
- A Triangulation section
- Shadow Test Results in the output template
"""

from conftest import AGENTS_DIR, required_text

EVALUATOR_MD = AGENTS_DIR / "bundle-evaluator.md"


def test_evaluator_level3_references_consumer():
    """bundle-evaluator.md Level 3 section must reference consumer experience."""
    text = required_text(EVALUATOR_MD)
    assert "consumer" in text.lower(), (
        "agents/bundle-evaluator.md must reference consumer experience in the Level 3 section"
    )


def test_evaluator_has_triangulation_section():
    """bundle-evaluator.md must contain a Triangulation section."""
    text = required_text(EVALUATOR_MD)
    assert "### Triangulation" in text, (
        "agents/bundle-evaluator.md must contain a '### Triangulation' section"
    )


def test_evaluator_output_has_shadow_test_results():
    """bundle-evaluator.md output template must contain Shadow Test Results section."""
    text = required_text(EVALUATOR_MD)
    assert "### Shadow Test Results" in text, (
        "agents/bundle-evaluator.md output template must contain '### Shadow Test Results' section"
    )

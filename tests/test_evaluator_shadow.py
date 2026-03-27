"""Evaluator shadow smoke test workflow contract tests.

Verify that agents/bundle-evaluator.md contains shadow-based smoke testing
in the Runtime Verification section.
"""

from conftest import AGENTS_DIR, required_text

EVALUATOR_MD = AGENTS_DIR / "bundle-evaluator.md"


def test_evaluator_has_shadow_workflow():
    """bundle-evaluator.md must reference amplifier-shadow in Runtime Verification."""
    text = required_text(EVALUATOR_MD)
    assert "amplifier-shadow" in text, (
        "agents/bundle-evaluator.md must contain 'amplifier-shadow' reference "
        "in the Runtime Verification section"
    )

"""Convergence criteria document structural contract tests.

Verify that context/convergence-criteria.md contains:
- A ## Traceability section with lifecycle documentation
- A ## Triangulation section with cross-check documentation
"""

from conftest import CONTEXT_DIR, required_text

CONVERGENCE_MD = CONTEXT_DIR / "convergence-criteria.md"


def _read_convergence() -> str:
    """Return the raw text of context/convergence-criteria.md."""
    assert CONVERGENCE_MD.exists(), f"{CONVERGENCE_MD} does not exist"
    return required_text(CONVERGENCE_MD)


# ---------------------------------------------------------------------------
# Traceability section tests
# ---------------------------------------------------------------------------


def test_convergence_has_traceability_section():
    """convergence-criteria.md must contain a ## Traceability section."""
    text = _read_convergence()
    assert "## Traceability" in text, (
        "context/convergence-criteria.md must contain a '## Traceability' section"
    )


# ---------------------------------------------------------------------------
# Triangulation section tests
# ---------------------------------------------------------------------------


def test_convergence_has_triangulation_section():
    """convergence-criteria.md must contain a ## Triangulation section."""
    text = _read_convergence()
    assert "## Triangulation" in text, (
        "context/convergence-criteria.md must contain a '## Triangulation' section"
    )

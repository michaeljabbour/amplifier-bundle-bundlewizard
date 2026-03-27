"""Convergence criteria document structural contract tests.

This test suite validates that context/convergence-criteria.md contains:

1. A ## Traceability section with:
   - Subsections: Lifecycle, Scoring
   - Three-actor model: spec-writer, evaluator, critic
   - Scoring outcomes: PASS, FLAG, FAIL (binary, not blended)
   - Unmet requirement vs orphaned artifact distinction

2. A ## Triangulation section with:
   - Three Dimensions: Intent, Structure, Function
   - Cross-Check Rule and disagreement examples
   - Signal philosophy: "does not override convergence formula"
   - All three disagreement scenarios (Intent✓/Structure✓/Function✗, etc.)
"""

import functools
import re

from conftest import CONTEXT_DIR, extract_markdown_section, required_text

CONVERGENCE_MD = CONTEXT_DIR / "convergence-criteria.md"


# ---------------------------------------------------------------------------
# Cached section helpers (avoid re-extracting on every test)
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=None)
def _convergence_section(heading: str, *, level: int = 2) -> str:
    return extract_markdown_section(required_text(CONVERGENCE_MD), heading, level=level)


@functools.lru_cache(maxsize=None)
def _convergence_subsection(parent_heading: str, heading: str) -> str:
    return extract_markdown_section(
        _convergence_section(parent_heading), heading, level=3
    )


def _table_row_containing(section: str, label: str) -> str:
    """Return the first markdown table row that contains *label*, or ``""``."""
    for line in section.splitlines():
        if line.lstrip().startswith("|") and label in line:
            return line
    return ""


# ---------------------------------------------------------------------------
# Traceability Section: Basic Structure
# ---------------------------------------------------------------------------


def test_traceability_has_required_subsections():
    """Traceability section must have both ### Lifecycle and ### Scoring subsections."""
    traceability_section = _convergence_section("Traceability")
    for subsection in ("### Lifecycle", "### Scoring"):
        assert subsection in traceability_section, (
            f"Traceability section must contain a '{subsection}' subsection"
        )


# ---------------------------------------------------------------------------
# Traceability: Lifecycle and Actor Roles
# ---------------------------------------------------------------------------


def test_traceability_lifecycle_actor_roles():
    """Lifecycle must document all three actor roles and reference R-IDs."""
    lifecycle_section = _convergence_subsection("Traceability", "Lifecycle")
    for role in ("spec-writer", "evaluator", "critic"):
        assert role in lifecycle_section.lower(), (
            f"Traceability Lifecycle must mention '{role}' as a role"
        )
    assert "R-ID" in lifecycle_section, "Traceability Lifecycle must reference R-IDs"


# ---------------------------------------------------------------------------
# Traceability: Scoring Outcomes
# ---------------------------------------------------------------------------


def test_traceability_scoring_outcomes():
    """Scoring must define PASS, FLAG, and FAIL as traceability outcomes."""
    scoring_section = _convergence_subsection("Traceability", "Scoring")
    for outcome in ("**PASS**", "**FLAG**", "**FAIL**"):
        assert outcome in scoring_section, (
            f"Traceability Scoring must include '{outcome}' as an outcome"
        )


def test_traceability_distinguishes_orphaned_vs_unmet():
    """Scoring must explicitly distinguish FLAG (orphaned) from FAIL (unmet)."""
    scoring_section = _convergence_subsection("Traceability", "Scoring")

    # Both terms should appear in the Scoring section
    assert "orphaned" in scoring_section.lower(), (
        "Traceability must explain 'orphaned' artifacts as a FLAG condition"
    )
    assert "unmet" in scoring_section.lower(), (
        "Traceability must explain 'unmet' requirements as a FAIL condition"
    )


# ---------------------------------------------------------------------------
# Traceability: Binary vs Blended Scoring
# ---------------------------------------------------------------------------


def test_traceability_scoring_is_binary():
    """Traceability scoring must be binary (not blended into L2 or L3)."""
    traceability_section = _convergence_section("Traceability")
    assert "binary" in traceability_section.lower(), (
        "Traceability Scoring must state that scoring is binary"
    )
    # Tolerate 'does not blend' and 'not blend' as equivalent phrasings
    assert re.search(
        r"does\s+not\s+blend|not\s+blend", traceability_section, re.IGNORECASE
    ), "Traceability Scoring must state it does not blend into Level 2 or Level 3"


# ---------------------------------------------------------------------------
# Triangulation Section: Basic Structure
# ---------------------------------------------------------------------------


def test_triangulation_has_required_subsections():
    """Triangulation section must have Three Dimensions and Cross-Check Rule subsections."""
    triangulation_section = _convergence_section("Triangulation")
    for subsection in ("### Three Dimensions", "### Cross-Check Rule"):
        assert subsection in triangulation_section, (
            f"Triangulation section must contain a '{subsection}' subsection"
        )


# ---------------------------------------------------------------------------
# Triangulation: Three Dimensions (Intent, Structure, Function)
# ---------------------------------------------------------------------------


def test_triangulation_three_dimensions_content():
    """Three Dimensions must include all three legs with correct score references.

    Table-driven check: each leg's table row must reference the appropriate
    scoring layer (via any accepted alias).  The keyword search is scoped to
    the specific row so a keyword appearing elsewhere in the section cannot
    satisfy the assertion.
    """
    dimensions_section = _convergence_subsection("Triangulation", "Three Dimensions")

    # (bold label, accepted keywords that must appear in *that leg's own row*)
    legs = [
        ("**Intent**", ["traceability", "r-id"]),
        ("**Structure**", ["level 2", "l2", "philosophical"]),
        ("**Function**", ["level 3", "l3", "functional", "smoke test"]),
    ]
    for label, keywords in legs:
        row = _table_row_containing(dimensions_section, label)
        assert row, f"Triangulation Three Dimensions must include '{label}' as a leg"
        assert any(kw in row.lower() for kw in keywords), (
            f"{label.strip('*')} row must reference one of {keywords!r}; got: {row!r}"
        )


def test_table_row_containing_ignores_non_table_mentions():
    """Row lookup must ignore prose mentions and stay scoped to markdown tables."""
    sample = "\n".join(
        [
            "Note: **Intent** is validated elsewhere in the document.",
            "| Leg | Evidence Source |",
            "|-----|-----------------|",
            "| **Intent** | Traceability matrix (R-ID coverage) |",
        ]
    )

    assert _table_row_containing(sample, "**Intent**") == (
        "| **Intent** | Traceability matrix (R-ID coverage) |"
    )


# ---------------------------------------------------------------------------
# Triangulation: Disagreement Examples
# ---------------------------------------------------------------------------


def test_triangulation_includes_disagreement_examples():
    """Cross-Check Rule must include examples of disagreement scenarios."""
    triangulation_section = _convergence_section("Triangulation")

    # The section should mention that disagreements trigger review
    assert "disagree" in triangulation_section.lower(), (
        "Triangulation must discuss disagreement scenarios"
    )
    assert "example" in triangulation_section.lower(), (
        "Triangulation should provide examples of disagreements"
    )


def test_triangulation_has_intent_structure_function_disagreement():
    """Must include example: Intent pass, Structure pass, Function fail (smoke test/runtime)."""
    section = _convergence_subsection("Triangulation", "Cross-Check Rule")

    # All three dimensions must appear in the examples
    for dimension in ("Intent", "Structure", "Function"):
        assert dimension in section, (
            f"Cross-Check Rule must reference '{dimension}' in a disagreement example"
        )

    # Scope the check to the specific numbered example block so keywords
    # appearing in neighboring examples do not create a false positive.
    example_match = re.search(
        r"^\s*\d+\.\s+\*\*Intent\s*✓,\s*Structure\s*✓,\s*Function\s*✗\*\*"
        r"(?P<body>.*?)(?=^\s*\d+\. |\Z)",
        section,
        re.MULTILINE | re.DOTALL,
    )
    assert example_match, (
        "Cross-Check Rule must contain the Intent✓/Structure✓/Function✗ disagreement example"
    )
    example_block = example_match.group(0).lower()

    # The Intent✓/Structure✓/Function✗ example must mention the smoke test / runtime failure
    assert "smoke test" in example_block, (
        "Cross-Check Rule must include an example mentioning 'smoke test'"
    )
    assert "runtime" in example_block, (
        "Cross-Check Rule example must mention the runtime failure scenario"
    )


def test_triangulation_has_intent_structure_function_disagreement_descriptions():
    """Disagreement examples must explain why misalignment occurs."""
    section = _convergence_subsection("Triangulation", "Cross-Check Rule")

    # Examples should explain the consequences/signals
    assert "fragile" in section.lower() or "error" in section.lower(), (
        "Disagreement examples must explain the technical implications"
    )


# ---------------------------------------------------------------------------
# Triangulation: Philosophy (Not a Gate)
# ---------------------------------------------------------------------------


def test_triangulation_does_not_override_convergence_formula():
    """Triangulation must not introduce a new gate or override convergence formula."""
    triangulation_section = _convergence_section("Triangulation")

    # The Triangulation section should explicitly state it cannot override the formula
    assert "not override" in triangulation_section.lower(), (
        "Triangulation must state it does not override the convergence formula"
    )


def test_triangulation_is_signal_not_gate():
    """Triangulation must be described as a signal, not a gate."""
    triangulation_section = _convergence_section("Triangulation")
    assert "signal" in triangulation_section.lower(), (
        "Triangulation must include a section or statement about being a signal"
    )


def test_triangulation_agreement_is_validation():
    """Triangulation must state that agreement across three legs validates readiness."""
    triangulation_section = _convergence_section("Triangulation")
    assert "agree" in triangulation_section.lower(), (
        "Triangulation must discuss agreement across the three legs"
    )


# ---------------------------------------------------------------------------
# Ordering and Cross-Section Relationships
# ---------------------------------------------------------------------------


def test_traceability_before_triangulation():
    """Traceability section must appear before Triangulation in the document."""
    text = required_text(CONVERGENCE_MD)

    traceability_pos = text.index("## Traceability")
    triangulation_pos = text.index("## Triangulation")

    assert traceability_pos < triangulation_pos, (
        "Traceability must appear before Triangulation (Traceability is a dependency)"
    )


def test_convergence_formula_remains_central():
    """The three-level convergence formula section must appear before Traceability/Triangulation."""
    text = required_text(CONVERGENCE_MD)

    # The Convergence Formula section must precede the Traceability section
    formula_section_pos = text.index("## Convergence Formula")
    traceability_pos = text.index("## Traceability")
    assert formula_section_pos < traceability_pos, (
        "Convergence Formula section must appear before Traceability/Triangulation sections"
    )

    # The formula section must contain the key invariants of the 3-level formula
    formula_section = _convergence_section("Convergence Formula")
    for token in ("level_1", "level_2", "level_3", "PASS"):
        assert token in formula_section, (
            f"Convergence Formula section must contain the key token '{token}'"
        )
    # Level 2 and Level 3 threshold values must both be present.
    for threshold in ("0.85", "0.80"):
        assert threshold in formula_section, (
            f"Convergence Formula must contain the threshold value '{threshold}'"
        )

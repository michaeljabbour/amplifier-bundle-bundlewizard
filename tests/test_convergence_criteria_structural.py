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

from conftest import CONTEXT_DIR, extract_markdown_section, required_text

CONVERGENCE_MD = CONTEXT_DIR / "convergence-criteria.md"


# ---------------------------------------------------------------------------
# Cached section helpers (avoid re-extracting on every test)
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=None)
def _convergence_text() -> str:
    """Return the cached raw text of context/convergence-criteria.md."""
    return required_text(CONVERGENCE_MD)


@functools.lru_cache(maxsize=None)
def _convergence_section(heading: str, *, level: int = 2) -> str:
    return extract_markdown_section(_convergence_text(), heading, level=level)


@functools.lru_cache(maxsize=None)
def _convergence_subsection(parent_heading: str, heading: str) -> str:
    return extract_markdown_section(
        _convergence_section(parent_heading), heading, level=3
    )


# ---------------------------------------------------------------------------
# Traceability Section: Basic Structure
# ---------------------------------------------------------------------------


def test_traceability_has_lifecycle_subsection():
    """Traceability section must have a ### Lifecycle subsection."""
    assert "### Lifecycle" in _convergence_section("Traceability"), (
        "Traceability section must contain a '### Lifecycle' subsection"
    )


def test_traceability_has_scoring_subsection():
    """Traceability section must have a ### Scoring subsection."""
    assert "### Scoring" in _convergence_section("Traceability"), (
        "Traceability section must contain a '### Scoring' subsection"
    )


# ---------------------------------------------------------------------------
# Traceability: Lifecycle and Actor Roles
# ---------------------------------------------------------------------------


def test_traceability_lifecycle_mentions_spec_writer():
    """Lifecycle must document the spec-writer's role in populating R-IDs."""
    lifecycle_section = _convergence_subsection("Traceability", "Lifecycle")
    assert "spec-writer" in lifecycle_section.lower(), (
        "Traceability Lifecycle must mention 'spec-writer' as a role"
    )
    assert "R-ID" in lifecycle_section, "Traceability Lifecycle must reference R-IDs"


def test_traceability_lifecycle_mentions_evaluator():
    """Lifecycle must document the evaluator's role in filling artifact mappings."""
    lifecycle_section = _convergence_subsection("Traceability", "Lifecycle")
    assert "evaluator" in lifecycle_section.lower(), (
        "Traceability Lifecycle must mention 'evaluator' as a role"
    )


def test_traceability_lifecycle_mentions_critic():
    """Lifecycle must document the critic's role in validating the matrix."""
    lifecycle_section = _convergence_subsection("Traceability", "Lifecycle")
    assert "critic" in lifecycle_section.lower(), (
        "Traceability Lifecycle must mention 'critic' as a role"
    )


# ---------------------------------------------------------------------------
# Traceability: Scoring Outcomes
# ---------------------------------------------------------------------------


def test_traceability_scoring_has_pass_outcome():
    """Scoring must define PASS as a traceability outcome."""
    scoring_section = _convergence_subsection("Traceability", "Scoring")
    assert "**PASS**" in scoring_section, (
        "Traceability Scoring must include '**PASS**' as an outcome"
    )


def test_traceability_scoring_has_flag_outcome():
    """Scoring must define FLAG as a traceability outcome (orphaned artifacts)."""
    scoring_section = _convergence_subsection("Traceability", "Scoring")
    assert "**FLAG**" in scoring_section, (
        "Traceability Scoring must include '**FLAG**' as an outcome"
    )


def test_traceability_scoring_has_fail_outcome():
    """Scoring must define FAIL as a traceability outcome (unmet requirements)."""
    scoring_section = _convergence_subsection("Traceability", "Scoring")
    assert "**FAIL**" in scoring_section, (
        "Traceability Scoring must include '**FAIL**' as an outcome"
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
    assert (
        "not blend" in traceability_section.lower()
        or "does not blend" in traceability_section.lower()
    ), "Traceability Scoring must state it does not blend into Level 2 or Level 3"


# ---------------------------------------------------------------------------
# Triangulation Section: Basic Structure
# ---------------------------------------------------------------------------


def test_triangulation_has_three_dimensions_subsection():
    """Triangulation section must have a ### Three Dimensions subsection."""
    assert "### Three Dimensions" in _convergence_section("Triangulation"), (
        "Triangulation section must contain a '### Three Dimensions' subsection"
    )


def test_triangulation_has_cross_check_rule_subsection():
    """Triangulation section must have a ### Cross-Check Rule subsection."""
    assert "### Cross-Check Rule" in _convergence_section("Triangulation"), (
        "Triangulation section must contain a '### Cross-Check Rule' subsection"
    )


# ---------------------------------------------------------------------------
# Triangulation: Three Dimensions (Intent, Structure, Function)
# ---------------------------------------------------------------------------


def test_triangulation_three_dimensions_has_intent():
    """Three Dimensions must include Intent as a leg."""
    dimensions_section = _convergence_subsection("Triangulation", "Three Dimensions")
    assert "**Intent**" in dimensions_section, (
        "Triangulation Three Dimensions must include '**Intent**' as a leg"
    )
    # Intent should check requirements (R-ID coverage / Traceability)
    assert (
        "intent" in dimensions_section.lower()
        and "traceability" in dimensions_section.lower()
    ), "Intent leg must reference Traceability matrix (R-ID coverage)"


def test_triangulation_three_dimensions_has_structure():
    """Three Dimensions must include Structure as a leg."""
    dimensions_section = _convergence_subsection("Triangulation", "Three Dimensions")
    assert "**Structure**" in dimensions_section, (
        "Triangulation Three Dimensions must include '**Structure**' as a leg"
    )
    # Structure should check L2 (philosophical) score
    assert "structure" in dimensions_section.lower() and (
        "level 2" in dimensions_section.lower()
        or "l2" in dimensions_section.lower()
        or "philosophical" in dimensions_section.lower()
    ), "Structure leg must reference Level 2 philosophical score"


def test_triangulation_three_dimensions_has_function():
    """Three Dimensions must include Function as a leg."""
    dimensions_section = _convergence_subsection("Triangulation", "Three Dimensions")
    assert "**Function**" in dimensions_section, (
        "Triangulation Three Dimensions must include '**Function**' as a leg"
    )
    # Function should check L3 (functional) score
    assert "function" in dimensions_section.lower() and (
        "level 3" in dimensions_section.lower()
        or "l3" in dimensions_section.lower()
        or "functional" in dimensions_section.lower()
    ), "Function leg must reference Level 3 functional score"


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
    assert (
        "examples" in triangulation_section.lower()
        or "example" in triangulation_section.lower()
    ), "Triangulation should provide examples of disagreements"


def test_triangulation_has_intent_structure_function_disagreement():
    """Must include example: Intent ✓, Structure ✓, Function ✗."""
    section = _convergence_subsection("Triangulation", "Cross-Check Rule")

    assert "Intent \u2713, Structure \u2713, Function \u2717" in section, (
        "Cross-Check Rule must contain the example label 'Intent ✓, Structure ✓, Function ✗'"
    )
    assert "smoke test" in section.lower(), (
        "Cross-Check Rule first disagreement example must mention 'smoke test'"
    )


def test_triangulation_has_intent_structure_function_disagreement_descriptions():
    """Disagreement examples must explain why misalignment occurs."""
    section = _convergence_subsection("Triangulation", "Cross-Check Rule")

    # Examples should explain the consequences/signals
    assert (
        "fragile" in section.lower()
        or "runtime" in section.lower()
        or "error" in section.lower()
    ), "Disagreement examples must explain the technical implications"


# ---------------------------------------------------------------------------
# Triangulation: Philosophy (Not a Gate)
# ---------------------------------------------------------------------------


def test_triangulation_does_not_override_convergence_formula():
    """Triangulation must not introduce a new gate or override convergence formula."""
    triangulation_section = _convergence_section("Triangulation")

    # The Triangulation section should explicitly state it cannot override the formula
    assert (
        "does not override" in triangulation_section.lower()
        or "not override" in triangulation_section.lower()
    ), "Triangulation must state it does not override the convergence formula"


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
    text = _convergence_text()

    traceability_pos = text.index("## Traceability")
    triangulation_pos = text.index("## Triangulation")

    assert traceability_pos < triangulation_pos, (
        "Traceability must appear before Triangulation (Traceability is a dependency)"
    )


def test_convergence_formula_remains_central():
    """The three-level convergence formula must remain the central structure."""
    text = _convergence_text()

    # Formula should appear near the beginning, before Traceability and Triangulation
    formula_pos = text.index("converged = (level_1 == PASS)")
    traceability_pos = text.index("## Traceability")

    assert formula_pos < traceability_pos, (
        "Convergence formula must appear before and centrally to Traceability/Triangulation sections"
    )

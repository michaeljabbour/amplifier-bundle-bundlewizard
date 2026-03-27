"""Bundle reference skill exemplar corpus structural contract tests.

Verify that skills/bundle-reference/SKILL.md contains:
- A ## Reference: Exemplar Corpus section
- Mention of amplifier-bundle-recipes as a known-good bundle
- At least 3 anti-pattern table entries
"""

from pathlib import Path

from conftest import required_text

SKILL_MD = Path(__file__).parent.parent / "skills" / "bundle-reference" / "SKILL.md"


def _read_skill() -> str:
    """Return the raw text of skills/bundle-reference/SKILL.md."""
    assert SKILL_MD.exists(), f"{SKILL_MD} does not exist"
    return required_text(SKILL_MD)


# ---------------------------------------------------------------------------
# Exemplar Corpus section tests
# ---------------------------------------------------------------------------


def test_bundle_reference_has_exemplar_corpus():
    """SKILL.md must contain a ## Reference: Exemplar Corpus section."""
    text = _read_skill()
    assert "## Reference: Exemplar Corpus" in text, (
        "skills/bundle-reference/SKILL.md must contain a "
        "'## Reference: Exemplar Corpus' section"
    )


def test_bundle_reference_mentions_recipes_exemplar():
    """SKILL.md must mention amplifier-bundle-recipes as a known-good bundle."""
    text = _read_skill()
    assert "amplifier-bundle-recipes" in text, (
        "skills/bundle-reference/SKILL.md must mention 'amplifier-bundle-recipes' "
        "in the Known-Good Bundles table"
    )


def test_bundle_reference_has_anti_patterns():
    """SKILL.md must have at least 3 anti-pattern table entries in the Exemplar Corpus section."""
    text = _read_skill()
    # Find the Anti-Pattern Examples section
    assert "### Anti-Pattern Examples" in text, (
        "skills/bundle-reference/SKILL.md must contain a "
        "'### Anti-Pattern Examples' subsection"
    )
    # Extract the section after Anti-Pattern Examples
    section_start = text.index("### Anti-Pattern Examples")
    section_text = text[section_start:]

    # Count table rows (lines starting with | that are not header or separator rows)
    # Header row contains "Anti-Pattern", separator row contains "---"
    lines = section_text.split("\n")
    data_rows = [
        line
        for line in lines
        if line.startswith("|")
        and "---" not in line
        and "Anti-Pattern" not in line
        and line.strip() != "|"
    ]
    assert len(data_rows) >= 3, (
        f"SKILL.md Anti-Pattern Examples table must have at least 3 data rows, "
        f"found {len(data_rows)}: {data_rows}"
    )

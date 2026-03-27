"""Bundle reference skill exemplar corpus structural contract tests.

Verify that skills/bundle-reference/SKILL.md contains:
- A ## Reference: Exemplar Corpus section
- Mention of amplifier-bundle-recipes as a known-good bundle
- At least 3 anti-pattern table entries
"""

import functools

from conftest import SKILLS_DIR, extract_markdown_section, required_text

SKILL_MD = SKILLS_DIR / "bundle-reference" / "SKILL.md"


def _skill_text() -> str:
    """Return the raw text of skills/bundle-reference/SKILL.md."""
    return required_text(SKILL_MD)


@functools.lru_cache(maxsize=1)
def _exemplar_corpus_section() -> str:
    """Return the cached ## Reference: Exemplar Corpus section."""
    return extract_markdown_section(_skill_text(), "Reference: Exemplar Corpus")


# ---------------------------------------------------------------------------
# Exemplar Corpus section tests
# ---------------------------------------------------------------------------


def test_bundle_reference_has_exemplar_corpus():
    """SKILL.md must contain a ## Reference: Exemplar Corpus section."""
    assert _exemplar_corpus_section().startswith("## Reference: Exemplar Corpus"), (
        "skills/bundle-reference/SKILL.md must contain a "
        "'## Reference: Exemplar Corpus' section"
    )


def test_bundle_reference_mentions_recipes_exemplar():
    """SKILL.md must mention amplifier-bundle-recipes as a known-good bundle."""
    assert "amplifier-bundle-recipes" in _exemplar_corpus_section(), (
        "skills/bundle-reference/SKILL.md must mention 'amplifier-bundle-recipes' "
        "in the Known-Good Bundles table"
    )


def test_bundle_reference_has_anti_patterns():
    """SKILL.md must have at least 3 anti-pattern table entries in the Exemplar Corpus section."""
    anti_pattern_section = extract_markdown_section(
        _exemplar_corpus_section(), "Anti-Pattern Examples", level=3
    )

    # Count table rows (lines starting with | that are not header or separator rows)
    # Header row contains "Anti-Pattern", separator row contains "---"
    lines = anti_pattern_section.split("\n")
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

"""Structural contract tests: bundle-reference skill pointer in Level 2 sections.

These tests verify that both bundle-critic.md and bundle-evaluator.md mention the
`bundle-reference` skill within their respective Level 2 (Philosophical) sections,
instructing the agent to load it for pattern comparison against known-good exemplars.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
BUNDLE_CRITIC = REPO_ROOT / "agents" / "bundle-critic.md"
BUNDLE_EVALUATOR = REPO_ROOT / "agents" / "bundle-evaluator.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_level2_section(content: str, heading: str) -> str:
    """Return the text of the Level 2 section identified by *heading*.

    Searches from the heading to the next ``###``-level heading (or EOF).
    Raises AssertionError if the heading is not found.
    """
    start = content.find(heading)
    assert start != -1, f"Level 2 heading not found: {heading!r}"
    next_heading = content.find("\n### ", start + 1)
    return content[start:next_heading] if next_heading != -1 else content[start:]


def test_critic_mentions_bundle_reference_skill():
    """bundle-critic.md Level 2 section must mention the `bundle-reference` skill
    and instruct the agent to load it for pattern comparison against known-good exemplars.
    """
    content = _read(BUNDLE_CRITIC)

    # Locate the Level 2 (Philosophical) heading used in the critic
    heading = "### Philosophical (Level 2 rubric"
    level2_section = _extract_level2_section(content, heading)

    assert "bundle-reference" in level2_section, (
        "bundle-critic.md Philosophical (Level 2) section must mention `bundle-reference` skill"
    )
    assert "exemplar" in level2_section.lower(), (
        "bundle-critic.md Philosophical (Level 2) section must mention exemplar comparison"
    )


def test_evaluator_mentions_bundle_reference_skill():
    """bundle-evaluator.md Level 2 section must mention the `bundle-reference` skill
    and instruct the agent to load it for pattern comparison against known-good exemplars.
    """
    content = _read(BUNDLE_EVALUATOR)

    # Locate the Level 2 (Philosophical) heading used in the evaluator
    heading = "### Level 2: Philosophical"
    level2_section = _extract_level2_section(content, heading)

    assert "bundle-reference" in level2_section, (
        "bundle-evaluator.md Level 2: Philosophical section must mention `bundle-reference` skill"
    )
    assert "exemplar" in level2_section.lower(), (
        "bundle-evaluator.md Level 2: Philosophical section must mention exemplar comparison"
    )

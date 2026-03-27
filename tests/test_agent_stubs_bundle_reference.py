"""Structural contract tests for Level 2 bundle-reference guidance."""

import functools

from conftest import AGENTS_DIR, extract_markdown_section, required_text


@functools.lru_cache(maxsize=None)
def _agent_text(filename: str) -> str:
    return required_text(AGENTS_DIR / filename)


@functools.lru_cache(maxsize=None)
def _level2_section(filename: str, heading: str) -> str:
    return extract_markdown_section(_agent_text(filename), heading, level=3)


def test_critic_mentions_bundle_reference_skill() -> None:
    """bundle-critic Level 2 section must mention the bundle-reference skill."""
    level2_section = _level2_section(
        "bundle-critic.md",
        "Philosophical (Level 2 rubric \u2014 score each)",
    )
    assert "bundle-reference" in level2_section, (
        "bundle-critic.md Philosophical (Level 2) must mention the `bundle-reference` skill"
    )
    assert "exemplar" in level2_section.lower(), (
        "bundle-critic.md Philosophical (Level 2) must mention exemplar comparison"
    )


def test_evaluator_mentions_bundle_reference_skill() -> None:
    """bundle-evaluator Level 2 section must mention the bundle-reference skill."""
    level2_section = _level2_section(
        "bundle-evaluator.md",
        "Level 2: Philosophical (scored 0.0\u20131.0, threshold 0.85)",
    )
    assert "bundle-reference" in level2_section, (
        "bundle-evaluator.md Level 2: Philosophical must mention the `bundle-reference` skill"
    )
    assert "exemplar" in level2_section.lower(), (
        "bundle-evaluator.md Level 2: Philosophical must mention exemplar comparison"
    )

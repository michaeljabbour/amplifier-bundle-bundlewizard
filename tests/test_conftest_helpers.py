"""Regression tests for shared helpers in tests/conftest.py."""

from conftest import extract_markdown_section


def test_extract_markdown_section_stops_at_higher_level_heading():
    """A level-3 section must stop before the next level-2 heading."""
    sample = "## Parent A\n### Target\n- keep this\n## Parent B\n- not this\n"

    assert extract_markdown_section(sample, "Target", level=3) == (
        "### Target\n- keep this\n"
    )

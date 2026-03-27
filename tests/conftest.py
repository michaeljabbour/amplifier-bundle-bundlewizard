"""Shared test fixtures and helpers for bundlewizard structural contract tests."""

import functools
import re
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Shared repo path constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
MODES_DIR = REPO_ROOT / "modes"
AGENTS_DIR = REPO_ROOT / "agents"
BEHAVIORS_DIR = REPO_ROOT / "behaviors"
CONTEXT_DIR = REPO_ROOT / "context"
RECIPES_DIR = REPO_ROOT / "recipes"
SKILLS_DIR = REPO_ROOT / "skills"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=32)
def optional_text(path: Path) -> str | None:
    """Return file content as UTF-8 text, or ``None`` if the file is absent.

    Returning ``None`` preserves the distinction between:
    - a missing file (``None``), and
    - an existing but empty file (``""``)

    Callers that gate on file existence should therefore check ``is None`` rather
    than relying on truthiness, so empty files still fail content assertions.
    """
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


@functools.lru_cache(maxsize=32)
def required_text(path: Path) -> str:
    """Return file content as UTF-8 text; raises FileNotFoundError if the file is absent."""
    return path.read_text(encoding="utf-8")


def parse_frontmatter_text(text: str, source_hint: str = "<unknown>") -> dict:
    """Extract YAML frontmatter from already-read markdown text.

    Uses the same regex / yaml parsing semantics as :func:`parse_frontmatter`,
    but operates on a string rather than reading a file.

    Args:
        text: Markdown text that may contain a YAML frontmatter block at the top.
        source_hint: A label used in the assertion error message (e.g. a file path).

    Returns:
        Parsed frontmatter as a dictionary.

    Raises:
        AssertionError: If no YAML frontmatter block is found.
    """
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    assert match, f"No YAML frontmatter found in {source_hint}"
    return yaml.safe_load(match.group(1))


def extract_markdown_section(text: str, heading: str, *, level: int = 2) -> str:
    """Return a markdown section through the next heading of the same or higher level.

    Matches headings at line starts only, so an inline mention of the heading
    string is not mistakenly picked up. Raises ``AssertionError`` with a
    descriptive message when the heading is absent.
    """
    prefix = "#" * level + " "
    start_pattern = re.compile(
        r"^" + re.escape(prefix + heading) + r"[ \t]*$", re.MULTILINE
    )
    m = start_pattern.search(text)
    assert m, f"Heading not found: '{prefix}{heading}'"
    start = m.start()
    next_pattern = re.compile(r"^#{1," + str(level) + r"} ", re.MULTILINE)
    next_m = next_pattern.search(text, m.end())
    return text[start : next_m.start()] if next_m else text[start:]


def parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file.

    Reads the file as UTF-8, extracts the top-of-file YAML block delimited
    by ``---``, asserts it is present, and returns the parsed dict.

    Args:
        path: Path to the markdown file containing YAML frontmatter.

    Returns:
        Parsed frontmatter as a dictionary.

    Raises:
        AssertionError: If no YAML frontmatter block is found.
    """
    content = required_text(path)
    return parse_frontmatter_text(content, source_hint=str(path))

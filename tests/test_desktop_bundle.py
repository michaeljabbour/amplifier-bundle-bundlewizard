"""Desktop bundle variant structural contract tests.

Verify:
- bundles/desktop.yaml has the correct bundle metadata (name, version)
- includes list references the base bundlewizard bundle
- Markdown body contains the expected @mention for the visual adapter context
"""

import re

import yaml

from conftest import REPO_ROOT

BUNDLES_DIR = REPO_ROOT / "bundles"
DESKTOP_YAML = BUNDLES_DIR / "desktop.yaml"


def _read_desktop() -> str:
    """Return the raw text of bundles/desktop.yaml."""
    assert DESKTOP_YAML.exists(), f"{DESKTOP_YAML} does not exist"
    return DESKTOP_YAML.read_text(encoding="utf-8")


def _parse_frontmatter(text: str) -> dict:
    """Extract and parse the YAML frontmatter block from the file."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    assert match, "bundles/desktop.yaml has no YAML frontmatter delimited by ---"
    return yaml.safe_load(match.group(1))


def _parse_body(text: str) -> str:
    """Return everything after the closing --- frontmatter delimiter."""
    # Strip the frontmatter block and return the remainder
    match = re.match(r"^---\s*\n.*?\n---\s*\n?(.*)", text, re.DOTALL)
    assert match, "bundles/desktop.yaml has no body after frontmatter"
    return match.group(1)


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------


def test_desktop_bundle_name():
    """bundle.name must be bundlewizard-desktop."""
    data = _parse_frontmatter(_read_desktop())
    assert data.get("bundle", {}).get("name") == "bundlewizard-desktop", (
        "bundle.name must be 'bundlewizard-desktop'"
    )


def test_desktop_bundle_version():
    """bundle.version must be 0.4.0."""
    data = _parse_frontmatter(_read_desktop())
    assert data.get("bundle", {}).get("version") == "0.4.0", (
        "bundle.version must be '0.4.0'"
    )


# ---------------------------------------------------------------------------
# Includes tests
# ---------------------------------------------------------------------------


def test_desktop_includes_exactly_one_entry():
    """includes list must have exactly one entry."""
    data = _parse_frontmatter(_read_desktop())
    includes = data.get("includes", [])
    assert len(includes) == 1, (
        f"includes must have exactly one entry, got {len(includes)}"
    )


def test_desktop_includes_bundlewizard():
    """The single includes entry must reference the bundlewizard bundle."""
    data = _parse_frontmatter(_read_desktop())
    includes = data.get("includes", [])
    assert len(includes) >= 1, "includes must have at least one entry"
    entry = includes[0]
    assert entry.get("bundle") == "bundlewizard", (
        f"includes[0].bundle must be 'bundlewizard', got {entry.get('bundle')!r}"
    )


# ---------------------------------------------------------------------------
# Body / @mention tests
# ---------------------------------------------------------------------------


def test_desktop_body_contains_visual_adapter_mention():
    """Markdown body must contain the @mention for the desktop visual adapter context."""
    body = _parse_body(_read_desktop())
    mention = "@bundlewizard:context/desktop-visual-adapter.md"
    assert mention in body, f"Body must contain '{mention}' but it was not found"

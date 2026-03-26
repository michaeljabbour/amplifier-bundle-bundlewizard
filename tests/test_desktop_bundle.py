"""Desktop bundle variant structural contract tests.

Verify:
- bundles/desktop.md has the correct bundle metadata (name, version)
- includes list references the base bundlewizard bundle
- Markdown body contains the expected @mention for the visual adapter context
"""

import re

import yaml

from conftest import REPO_ROOT

BUNDLES_DIR = REPO_ROOT / "bundles"
DESKTOP_MD = BUNDLES_DIR / "desktop.md"


def _read_desktop() -> str:
    """Return the raw text of bundles/desktop.md."""
    assert DESKTOP_MD.exists(), f"{DESKTOP_MD} does not exist"
    return DESKTOP_MD.read_text(encoding="utf-8")


def _parse_frontmatter(text: str) -> dict:
    """Extract and parse the YAML frontmatter block from the file."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    assert match, "bundles/desktop.md has no YAML frontmatter delimited by ---"
    return yaml.safe_load(match.group(1))


def _parse_body(text: str) -> str:
    """Return everything after the closing --- frontmatter delimiter."""
    # Strip the frontmatter block and return the remainder
    match = re.match(r"^---\s*\n.*?\n---\s*\n?(.*)", text, re.DOTALL)
    assert match, "bundles/desktop.md has no body after frontmatter"
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
    """bundle.version must be 0.4.1."""
    data = _parse_frontmatter(_read_desktop())
    assert data.get("bundle", {}).get("version") == "0.4.1", (
        "bundle.version must be '0.4.1'"
    )


# ---------------------------------------------------------------------------
# Includes tests
# ---------------------------------------------------------------------------


def test_desktop_includes_exactly_two_entries():
    """includes list must have exactly two entries (bundlewizard + stories)."""
    data = _parse_frontmatter(_read_desktop())
    includes = data.get("includes", [])
    assert len(includes) == 2, (
        f"includes must have exactly two entries, got {len(includes)}"
    )


def test_desktop_includes_stories_bundle():
    """The second includes entry must reference the amplifier-module-stories bundle."""
    data = _parse_frontmatter(_read_desktop())
    includes = data.get("includes", [])
    assert len(includes) >= 2, "includes must have at least two entries"
    entry = includes[1]
    bundle_ref = entry.get("bundle", "")
    assert "amplifier-module-stories" in bundle_ref, (
        f"includes[1].bundle must reference 'amplifier-module-stories', got {bundle_ref!r}"
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


# ---------------------------------------------------------------------------
# Desktop visual adapter context tests
# ---------------------------------------------------------------------------

VISUAL_ADAPTER = REPO_ROOT / "context" / "desktop-visual-adapter.md"


def _read_visual_adapter() -> str:
    """Return the raw text of context/desktop-visual-adapter.md."""
    assert VISUAL_ADAPTER.exists(), f"{VISUAL_ADAPTER} does not exist"
    return VISUAL_ADAPTER.read_text(encoding="utf-8")


def test_visual_adapter_file_exists():
    """context/desktop-visual-adapter.md must exist."""
    assert VISUAL_ADAPTER.exists(), "context/desktop-visual-adapter.md does not exist"


def test_visual_adapter_contains_graph_fence_type():
    """File must reference the bundlewizard-graph fenced code block type."""
    content = _read_visual_adapter()
    assert "bundlewizard-graph" in content, (
        "desktop-visual-adapter.md must contain 'bundlewizard-graph'"
    )


def test_visual_adapter_mentions_all_node_types():
    """File must mention all 8 node types."""
    content = _read_visual_adapter()
    node_types = [
        "agent",
        "tool",
        "context",
        "mode",
        "recipe",
        "state",
        "behavior",
        "bundle",
    ]
    for node_type in node_types:
        assert node_type in content, (
            f"desktop-visual-adapter.md must mention node type '{node_type}'"
        )


def test_visual_adapter_mentions_all_edge_types():
    """File must mention all 10 edge types."""
    content = _read_visual_adapter()
    edge_types = [
        "inheritance",
        "spawn",
        "toolRegistration",
        "pipelineFlow",
        "adversarial",
        "loopBack",
        "modeTransition",
        "contextLoad",
        "recipeNesting",
        "stateReadWrite",
    ]
    for edge_type in edge_types:
        assert edge_type in content, (
            f"desktop-visual-adapter.md must mention edge type '{edge_type}'"
        )


def test_visual_adapter_contains_emission_sections():
    """File must contain 'When to emit' and 'When NOT to emit' sections."""
    content = _read_visual_adapter()
    assert "When to emit" in content, (
        "desktop-visual-adapter.md must contain a 'When to emit' section"
    )
    assert "When NOT to emit" in content, (
        "desktop-visual-adapter.md must contain a 'When NOT to emit' section"
    )


def test_visual_adapter_progressive_emission_strategy():
    """File must describe progressive/skeleton emission from the first response."""
    content = _read_visual_adapter()
    # At least one of these terms must appear, confirming the progressive strategy
    has_skeleton = "skeleton" in content.lower()
    has_scaffolding = "scaffolding" in content.lower()
    has_first_response = "first response" in content.lower()
    assert has_skeleton or has_scaffolding or has_first_response, (
        "desktop-visual-adapter.md must mention 'skeleton', 'scaffolding', or "
        "'first response' to confirm progressive emission strategy"
    )


def test_visual_adapter_contains_example_json_block():
    """File must contain a concrete example JSON emission with expected keys."""
    content = _read_visual_adapter()
    # The example must be a bundlewizard-graph JSON block with key structural elements
    assert '"bundle-root"' in content, (
        "desktop-visual-adapter.md must contain an example JSON block with a 'bundle-root' node"
    )
    assert '"explore-phase"' in content, (
        "desktop-visual-adapter.md must contain an example JSON block with an 'explore-phase' node"
    )
    assert '"tentative"' in content, (
        "desktop-visual-adapter.md must contain 'tentative' markers in the example JSON"
    )


def test_visual_adapter_phase_guidance():
    """File must contain per-phase emission guidance."""
    content = _read_visual_adapter()
    for phase in ["Explore", "Spec", "Plan", "Execute"]:
        assert phase in content, (
            f"desktop-visual-adapter.md must contain phase guidance for '{phase}'"
        )


# ---------------------------------------------------------------------------
# Story Generation section tests
# ---------------------------------------------------------------------------


def test_visual_adapter_has_story_generation_section():
    """File must contain a 'Story Generation' section heading."""
    content = _read_visual_adapter()
    assert "## Story Generation" in content, (
        "desktop-visual-adapter.md must contain a '## Story Generation' section"
    )


def test_visual_adapter_story_generation_mentions_agents():
    """Story Generation section must mention key story agents."""
    content = _read_visual_adapter()
    for agent in [
        "storyteller",
        "story-researcher",
        "content-strategist",
        "technical-writer",
    ]:
        assert agent in content, (
            f"desktop-visual-adapter.md must mention story agent '{agent}'"
        )


def test_visual_adapter_story_generation_html_format():
    """Story Generation section must reference HTML output format."""
    content = _read_visual_adapter()
    assert "HTML" in content, (
        "desktop-visual-adapter.md must mention HTML in the Story Generation section"
    )

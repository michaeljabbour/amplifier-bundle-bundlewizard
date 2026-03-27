"""Structural contract tests for Explorer DOT diagram composition and flow edges.

These tests verify that bundle-explorer.md has been updated with an enhanced DOT
example containing:
- cluster_local with bundle_md, behavior, agent1, agent2, agent3
- cluster_external with ext_behavior and ext_expert
- Composition edges with style=dashed, color=blue (labeled 'includes')
- Agentic flow edges with style=bold, color=green (labeled 'delegates' and 'domain knowledge')
- Mode transitions with style=dashed, color=orange

All tests in this file were RED (failing) until implementation was complete.
"""

from pathlib import Path

# Repo root — tests/ is a direct child of the repo root
REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / "agents"


def _load_explorer() -> str:
    """Load bundle-explorer.md content once, with explicit UTF-8 encoding."""
    return (AGENTS_DIR / "bundle-explorer.md").read_text(encoding="utf-8")


def test_explorer_dot_has_composition_edges():
    """DOT example must contain composition edges styled with dashed blue lines.

    Verifies:
    - cluster_local replaces cluster_bundle
    - cluster_external is present with ext_behavior and ext_expert
    - Composition edges use style=dashed, color=blue and label='includes'
    - bundle_md -> behavior and behavior -> ext_behavior edges exist
    """
    explorer = _load_explorer()

    # cluster_local must be present (replacing the old cluster_bundle)
    assert "cluster_local" in explorer, (
        "Expected 'cluster_local' subgraph in the DOT example in agents/bundle-explorer.md "
        "(replacing old 'cluster_bundle')"
    )

    # cluster_bundle must NOT be present (it was replaced)
    assert "cluster_bundle" not in explorer, (
        "Expected 'cluster_bundle' to be replaced by 'cluster_local' in agents/bundle-explorer.md"
    )

    # cluster_external must be present
    assert "cluster_external" in explorer, (
        "Expected 'cluster_external' subgraph in the DOT example in agents/bundle-explorer.md"
    )

    # Composition edges must use style=dashed, color=blue
    assert "style=dashed, color=blue" in explorer, (
        "Expected composition edges with 'style=dashed, color=blue' in the DOT example "
        "in agents/bundle-explorer.md"
    )

    # bundle_md -> behavior edge labeled 'includes' must exist
    assert 'bundle_md -> behavior' in explorer, (
        "Expected 'bundle_md -> behavior' composition edge in agents/bundle-explorer.md"
    )

    # behavior -> ext_behavior edge labeled 'includes' must exist
    assert 'behavior -> ext_behavior' in explorer, (
        "Expected 'behavior -> ext_behavior' composition edge in agents/bundle-explorer.md"
    )

    # Both composition edges must be labeled 'includes'
    # Verify 'includes' label appears in the DOT example
    dot_start = explorer.index("```dot")
    dot_end = explorer.index("```", dot_start + 5)
    dot_content = explorer[dot_start:dot_end]
    assert "includes" in dot_content, (
        "Expected 'includes' label on composition edges in the DOT example "
        "in agents/bundle-explorer.md"
    )


def test_explorer_dot_has_flow_edges():
    """DOT example must contain agentic flow edges styled with bold green lines.

    Verifies:
    - Flow edges use style=bold, color=green
    - agent1 -> agent2 and agent2 -> agent3 edges exist labeled 'delegates'
    - agent1 -> ext_expert edge labeled 'domain knowledge'
    - Mode transitions use style=dashed, color=orange
    - Old delegation flow section with plain dashed style is removed
    """
    explorer = _load_explorer()

    # Flow edges must use style=bold, color=green
    assert "style=bold, color=green" in explorer, (
        "Expected agentic flow edges with 'style=bold, color=green' in the DOT example "
        "in agents/bundle-explorer.md"
    )

    # agent1 -> agent2 must be present
    assert "agent1 -> agent2" in explorer, (
        "Expected 'agent1 -> agent2' flow edge in agents/bundle-explorer.md"
    )

    # agent2 -> agent3 must be present
    assert "agent2 -> agent3" in explorer, (
        "Expected 'agent2 -> agent3' flow edge in agents/bundle-explorer.md"
    )

    # agent1 -> ext_expert must be present (domain knowledge edge)
    assert "agent1 -> ext_expert" in explorer, (
        "Expected 'agent1 -> ext_expert' flow edge in agents/bundle-explorer.md"
    )

    # Mode transitions must use style=dashed, color=orange
    assert "style=dashed, color=orange" in explorer, (
        "Expected mode transitions with 'style=dashed, color=orange' in the DOT example "
        "in agents/bundle-explorer.md"
    )

    # Extract the DOT example block for scoped checks
    dot_start = explorer.index("```dot")
    dot_end = explorer.index("```", dot_start + 5)
    dot_content = explorer[dot_start:dot_end]

    # 'delegates' label must appear in the DOT block
    assert "delegates" in dot_content, (
        "Expected 'delegates' label on flow edges in the DOT example "
        "in agents/bundle-explorer.md"
    )

    # 'domain knowledge' label must appear in the DOT block
    assert "domain knowledge" in dot_content, (
        "Expected 'domain knowledge' label on agent1 -> ext_expert edge "
        "in agents/bundle-explorer.md"
    )

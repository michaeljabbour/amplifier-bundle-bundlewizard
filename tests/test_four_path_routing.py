"""Structural contract tests for four-path routing.

These tests verify that the bundle-explorer system has been updated from
three-path to four-path routing, including:
- context/instructions.md updated to four-path routing
- modes/bundle-explore.md has Design My Experience checklist and handoff fields
- agents/bundle-explorer.md has Path D signals, disambiguation, and D1/D2/D3 interviews
- recipes/bundle-autonomous-post-explore.yaml has experience design context fields

All tests in this file are RED (failing) until implementation is complete.
"""

import re
from pathlib import Path


# Repo root — tests/ is a direct child of the repo root
REPO_ROOT = Path(__file__).parent.parent
MODES_DIR = REPO_ROOT / "modes"
AGENTS_DIR = REPO_ROOT / "agents"
CONTEXT_DIR = REPO_ROOT / "context"
RECIPES_DIR = REPO_ROOT / "recipes"


# ---------------------------------------------------------------------------
# context/instructions.md tests
# ---------------------------------------------------------------------------


def test_instructions_has_four_path_heading():
    """instructions.md must reference Four-Path Routing Fork, not Three-Path."""
    instructions = (CONTEXT_DIR / "instructions.md").read_text()
    assert "Four-Path Routing Fork" in instructions, (
        "Expected 'Four-Path Routing Fork' heading in context/instructions.md"
    )
    assert "Three-Path Routing Fork" not in instructions, (
        "Old 'Three-Path Routing Fork' heading must be removed from context/instructions.md"
    )


def test_instructions_has_path_d_signals():
    """instructions.md must contain Path D trigger signals (case-insensitive)."""
    instructions = (CONTEXT_DIR / "instructions.md").read_text().lower()
    assert "customize my amplifier" in instructions, (
        "Expected signal phrase 'customize my amplifier' in context/instructions.md"
    )
    assert "design my experience" in instructions, (
        "Expected signal phrase 'design my experience' in context/instructions.md"
    )


def test_instructions_has_path_d_interview_flow():
    """instructions.md must document Path D and the Design My Experience interview flow.

    Case-sensitive: these are section headings with specific capitalisation.
    """
    instructions = (CONTEXT_DIR / "instructions.md").read_text()
    assert "Path D" in instructions, (
        "Expected 'Path D' routing description in context/instructions.md"
    )
    assert "Design My Experience" in instructions, (
        "Expected 'Design My Experience' interview flow reference in context/instructions.md"
    )


# ---------------------------------------------------------------------------
# modes/bundle-explore.md tests
# ---------------------------------------------------------------------------


def test_explore_mode_has_path_d_checklist():
    """bundle-explore.md must include a Design My Experience checklist section."""
    explore_mode = (MODES_DIR / "bundle-explore.md").read_text()
    assert "Design My Experience" in explore_mode, (
        "Expected 'Design My Experience' checklist in modes/bundle-explore.md"
    )


def test_explore_mode_has_experience_design_handoff_fields():
    """bundle-explore.md must declare handoff fields for experience design sub-paths."""
    explore_mode = (MODES_DIR / "bundle-explore.md").read_text()
    assert "design_my_experience" in explore_mode, (
        "Expected handoff field 'design_my_experience' in modes/bundle-explore.md"
    )
    assert "experience_sub_path" in explore_mode, (
        "Expected handoff field 'experience_sub_path' in modes/bundle-explore.md"
    )
    assert "experience_lens" in explore_mode, (
        "Expected handoff field 'experience_lens' in modes/bundle-explore.md"
    )


# ---------------------------------------------------------------------------
# agents/bundle-explorer.md tests
# ---------------------------------------------------------------------------


def test_explorer_agent_has_path_d_signals():
    """bundle-explorer.md must include Path D detection signals."""
    explorer = (AGENTS_DIR / "bundle-explorer.md").read_text()
    assert "Design My Experience" in explorer, (
        "Expected 'Design My Experience' in agents/bundle-explorer.md"
    )
    # Regex check: must contain at least one of the key trigger phrases
    pattern = re.compile(
        r"customize.{0,20}amplifier|design.{0,20}experience", re.IGNORECASE
    )
    assert pattern.search(explorer), (
        "Expected regex match for 'customize...amplifier' or 'design...experience' "
        "signals in agents/bundle-explorer.md"
    )


def test_explorer_agent_has_d1_d2_d3_interview():
    """bundle-explorer.md must contain D1, D2, D3 interview steps and experience_lens."""
    explorer = (AGENTS_DIR / "bundle-explorer.md").read_text()
    assert "D1" in explorer, "Expected 'D1' interview step in agents/bundle-explorer.md"
    assert "D2" in explorer, "Expected 'D2' interview step in agents/bundle-explorer.md"
    assert "D3" in explorer, "Expected 'D3' interview step in agents/bundle-explorer.md"
    assert "experience_lens" in explorer, (
        "Expected 'experience_lens' field in agents/bundle-explorer.md"
    )


# ---------------------------------------------------------------------------
# recipes/bundle-autonomous-post-explore.yaml tests
# ---------------------------------------------------------------------------


def test_recipe_has_experience_design_context_fields():
    """bundle-autonomous-post-explore.yaml must include experience design context fields."""
    recipe = (RECIPES_DIR / "bundle-autonomous-post-explore.yaml").read_text()
    assert "experience_sub_path" in recipe, (
        "Expected 'experience_sub_path' context field in "
        "recipes/bundle-autonomous-post-explore.yaml"
    )
    assert "experience_lens" in recipe, (
        "Expected 'experience_lens' context field in "
        "recipes/bundle-autonomous-post-explore.yaml"
    )


def test_recipe_path_decision_comment_includes_design_my_experience():
    """path_decision comment must enumerate all four valid values including design_my_experience.

    Guards against stale comments when new paths are added — the comment is the
    developer-visible schema contract for what values the field accepts.
    """
    recipe = (RECIPES_DIR / "bundle-autonomous-post-explore.yaml").read_text()
    assert '"design_my_experience"' in recipe, (
        "Expected '\"design_my_experience\"' in the path_decision comment in "
        "recipes/bundle-autonomous-post-explore.yaml — comment must enumerate all four paths"
    )

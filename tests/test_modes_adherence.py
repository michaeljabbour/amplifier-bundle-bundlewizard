"""Structural contract tests for bundlewizard modes and autonomy handoff files.

These tests verify:
- bundle-bot.md does NOT exist (regression guard)
- All 7 pipeline modes have correct transitions and allow_clear
- The abandoned autonomous behavior YAML does NOT exist
- The post-explore autonomy handoff contract is present
- Autonomous protocol context file exists with audit trail
- Instructions don't reference bundle-bot
"""

import re
from pathlib import Path

import pytest
import yaml

# Repo root — tests/ is a direct child of the repo root
REPO_ROOT = Path(__file__).parent.parent
MODES_DIR = REPO_ROOT / "modes"
BEHAVIORS_DIR = REPO_ROOT / "behaviors"
CONTEXT_DIR = REPO_ROOT / "context"
TEMPLATES_DIR = REPO_ROOT / "templates"
RECIPES_DIR = REPO_ROOT / "recipes"
BUNDLE_MD = REPO_ROOT / "bundle.md"


# Expected transition graph for all 7 pipeline modes
EXPECTED_TRANSITIONS = {
    "bundle-explore": {
        "allowed": ["bundle-spec", "bundle-debug"],
        "allow_clear": False,
    },
    "bundle-spec": {
        "allowed": ["bundle-plan", "bundle-explore", "bundle-debug"],
        "allow_clear": False,
    },
    "bundle-plan": {
        "allowed": ["bundle-execute", "bundle-spec", "bundle-debug"],
        "allow_clear": False,
    },
    "bundle-execute": {
        "allowed": ["bundle-verify", "bundle-debug"],
        "allow_clear": False,
    },
    "bundle-verify": {
        "allowed": ["bundle-finish", "bundle-debug", "bundle-execute"],
        "allow_clear": False,
    },
    "bundle-finish": {"allowed": [], "allow_clear": True},
    "bundle-debug": {
        "allowed": [
            "bundle-explore",
            "bundle-spec",
            "bundle-plan",
            "bundle-execute",
            "bundle-verify",
            "bundle-finish",
        ],
        "allow_clear": False,
    },
}


def _parse_mode_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a mode .md file."""
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    assert match, f"No YAML frontmatter found in {path}"
    return yaml.safe_load(match.group(1))


def test_bundle_bot_does_not_exist():
    """bundle-bot.md must NOT exist — autonomy is now handled by the contained post-explore recipe model."""
    bot_path = MODES_DIR / "bundle-bot.md"
    assert not bot_path.exists(), (
        "modes/bundle-bot.md still exists! It should have been deleted. "
        "Autonomy is now handled by the contained post-explore recipe model, "
        "not a god-mode bundle-bot file."
    )


def test_pipeline_modes_exist():
    """All 7 pipeline mode files must exist."""
    for mode_name in EXPECTED_TRANSITIONS:
        mode_path = MODES_DIR / f"{mode_name}.md"
        assert mode_path.exists(), f"Missing pipeline mode: {mode_path}"


def test_pipeline_mode_transitions():
    """Each pipeline mode's allowed_transitions must match the expected graph."""
    for mode_name, expected in EXPECTED_TRANSITIONS.items():
        mode_path = MODES_DIR / f"{mode_name}.md"
        frontmatter = _parse_mode_frontmatter(mode_path)
        mode_config = frontmatter["mode"]
        actual = sorted(mode_config.get("allowed_transitions", []))
        expected_sorted = sorted(expected["allowed"])
        assert actual == expected_sorted, (
            f"{mode_name}: allowed_transitions mismatch.\n"
            f"  Expected: {expected_sorted}\n"
            f"  Actual:   {actual}"
        )


def test_pipeline_mode_allow_clear():
    """Only bundle-finish should have allow_clear: true."""
    for mode_name, expected in EXPECTED_TRANSITIONS.items():
        mode_path = MODES_DIR / f"{mode_name}.md"
        frontmatter = _parse_mode_frontmatter(mode_path)
        mode_config = frontmatter["mode"]
        actual = mode_config.get(
            "allow_clear", True
        )  # default is True per ModeDefinition
        assert actual == expected["allow_clear"], (
            f"{mode_name}: allow_clear mismatch. "
            f"Expected {expected['allow_clear']}, got {actual}"
        )


def test_autonomous_behavior_does_not_exist():
    """behaviors/bundlewizard-autonomous.yaml must NOT exist.

    The upstream-dependent autonomous behavior has been replaced by a bundle-local
    post-explore continuation recipe (recipes/bundle-autonomous-post-explore.yaml).
    Shipping this file would re-introduce an upstream amplifier-bundle-modes dependency.
    """
    path = BEHAVIORS_DIR / "bundlewizard-autonomous.yaml"
    assert not path.exists(), (
        "behaviors/bundlewizard-autonomous.yaml still exists. "
        "This upstream-dependent file must be deleted. "
        "Autonomy is now handled by recipes/bundle-autonomous-post-explore.yaml."
    )


def test_state_yaml_has_autonomy_fields():
    """templates/STATE.yaml must include autonomy handoff and takeover contract fields."""
    path = TEMPLATES_DIR / "STATE.yaml"
    assert path.exists(), "templates/STATE.yaml does not exist"
    content = yaml.safe_load(path.read_text(encoding="utf-8"))

    session = content.get("session", {})
    assert "autonomy_requested" in session, (
        "STATE.yaml session block must have an autonomy_requested field"
    )
    assert "trigger_reason" in session, (
        "STATE.yaml session block must have a trigger_reason field"
    )

    assert "takeover" in content, "STATE.yaml must have a top-level takeover section"
    takeover = content["takeover"]
    assert "status" in takeover, "STATE.yaml takeover must have a status field"
    assert "recommended_entry" in takeover, (
        "STATE.yaml takeover must have a recommended_entry field"
    )
    assert "explanation" in takeover, (
        "STATE.yaml takeover must have an explanation field"
    )


def test_autonomous_protocol_is_recipe_policy():
    """context/autonomous-protocol.md must be repurposed as recipe/autonomy policy.

    It must NOT contain mode-level behavioral override instructions (old design).
    It MUST reference the post-explore continuation recipe.
    """
    path = CONTEXT_DIR / "autonomous-protocol.md"
    assert path.exists(), "context/autonomous-protocol.md does not exist"
    content = path.read_text(encoding="utf-8")

    assert "bundle-autonomous-post-explore" in content, (
        "autonomous-protocol.md must reference bundle-autonomous-post-explore "
        "to establish it as recipe/autonomy policy context"
    )
    assert "When any mode instruction says" not in content, (
        "autonomous-protocol.md still contains mode-level behavioral override language. "
        "This file must be repurposed as recipe policy context, not a mode-level override."
    )


def test_explore_mode_is_handoff_gate():
    """modes/bundle-explore.md must act as a handoff gate.

    It must detect autonomy_requested and reference the post-explore recipe.
    """
    path = MODES_DIR / "bundle-explore.md"
    assert path.exists(), "modes/bundle-explore.md does not exist"
    content = path.read_text(encoding="utf-8")

    assert "autonomy_requested" in content, (
        "bundle-explore.md must detect autonomy_requested to decide the handoff path"
    )
    assert "bundle-autonomous-post-explore" in content, (
        "bundle-explore.md must reference bundle-autonomous-post-explore "
        "for launching autonomous continuation"
    )


def test_autonomous_post_explore_recipe_exists():
    """recipes/bundle-autonomous-post-explore.yaml must exist."""
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    assert path.exists(), (
        "recipes/bundle-autonomous-post-explore.yaml does not exist. "
        "This recipe is the autonomous continuation engine for post-explore operation."
    )


def test_autonomous_post_explore_recipe_stages():
    """The post-explore recipe must contain all 5 required continuation stages."""
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    if not path.exists():
        pytest.skip("bundle-autonomous-post-explore.yaml not yet created")
    content = yaml.safe_load(path.read_text(encoding="utf-8"))

    stages = [s["name"] for s in content.get("stages", [])]
    required = {"spec", "plan", "execute", "verify", "finish"}
    missing = required - set(stages)
    assert not missing, (
        f"bundle-autonomous-post-explore.yaml is missing required stages: {missing}. "
        f"Found: {stages}"
    )


def test_autonomous_post_explore_recipe_no_required_approval_gates():
    """The post-explore recipe must NOT have required: true approval gates.

    It is the autonomous track — human approval gates defeat the purpose.
    Takeover points are offered via STATE.yaml, not forced via approval gates.
    """
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    if not path.exists():
        pytest.skip("bundle-autonomous-post-explore.yaml not yet created")
    content = yaml.safe_load(path.read_text(encoding="utf-8"))

    for stage in content.get("stages", []):
        approval = stage.get("approval", {})
        assert approval.get("required", False) is not True, (
            f"Stage '{stage['name']}' has required: true approval gate. "
            "The autonomous recipe must not force human approval gates."
        )


def test_autonomous_post_explore_recipe_reuses_refinement_loop():
    """The post-explore recipe must reuse bundle-refinement-loop for execution.

    Do not duplicate the convergence loop — reuse the existing sub-recipe.
    """
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    if not path.exists():
        pytest.skip("bundle-autonomous-post-explore.yaml not yet created")
    content = path.read_text(encoding="utf-8")

    assert "bundle-refinement-loop" in content, (
        "bundle-autonomous-post-explore.yaml must invoke bundle-refinement-loop.yaml "
        "for the execute stage — do not duplicate convergence logic."
    )


def test_instructions_describes_opt_in_autonomy():
    """context/instructions.md must describe the opt-in autonomy-after-explore path."""
    path = CONTEXT_DIR / "instructions.md"
    content = path.read_text(encoding="utf-8")

    assert "bundle-autonomous-post-explore" in content, (
        "context/instructions.md must reference bundle-autonomous-post-explore.yaml "
        "in its two-track UX description"
    )


def test_bundle_md_matches_two_track_public_surface():
    """bundle.md must describe the contained two-track UX surface."""
    assert BUNDLE_MD.exists(), "bundle.md does not exist"
    content = BUNDLE_MD.read_text(encoding="utf-8")

    assert "## Two Tracks" in content, "bundle.md must contain a 'Two Tracks' section"
    assert "bundle-autonomous-post-explore.yaml" in content, (
        "bundle.md Recipes table must list bundle-autonomous-post-explore.yaml"
    )
    assert "Default flow is interactive and manual" in content, (
        "bundle.md must state that the default flow is interactive and manual"
    )
    assert "Autonomous continuation is opt-in" in content, (
        "bundle.md must state that autonomous continuation is opt-in"
    )
    assert "go autonomous" in content, (
        "bundle.md Getting Started must include the 'go autonomous' trigger phrase"
    )
    assert "Exploration still happens first" in content, (
        "bundle.md must state that exploration always precedes autonomous continuation"
    )


def test_autonomous_protocol_exists():
    """The autonomous protocol context file must exist."""
    path = CONTEXT_DIR / "autonomous-protocol.md"
    assert path.exists(), (
        "context/autonomous-protocol.md does not exist. "
        "This file provides recipe/autonomy policy context for post-explore continuation."
    )


def test_autonomous_protocol_has_audit_trail():
    """The autonomous protocol must contain the generated_by audit trail schema."""
    path = CONTEXT_DIR / "autonomous-protocol.md"
    if not path.exists():
        pytest.skip("autonomous-protocol.md not yet created")
    content = path.read_text(encoding="utf-8")
    assert "generated_by:" in content, (
        "autonomous-protocol.md must contain the 'generated_by:' audit trail schema "
        "(migrated from the deleted bundle-bot.md)"
    )


def test_instructions_no_bundle_bot():
    """context/instructions.md must NOT reference /bundle-bot."""
    path = CONTEXT_DIR / "instructions.md"
    content = path.read_text(encoding="utf-8")
    assert "/bundle-bot" not in content, (
        "context/instructions.md still references /bundle-bot. "
        "The bundle-bot row should be removed from the mode routing table."
    )

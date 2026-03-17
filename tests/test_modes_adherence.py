"""Structural contract tests for bundlewizard modes and behaviors.

These tests verify:
- bundle-bot.md does NOT exist (regression guard)
- All 7 pipeline modes have correct transitions and allow_clear
- Autonomous behavior YAML exists with correct config
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


# Expected transition graph for all 7 pipeline modes
EXPECTED_TRANSITIONS = {
    "bundle-explore": {"allowed": ["bundle-spec", "bundle-debug"], "allow_clear": False},
    "bundle-spec": {"allowed": ["bundle-plan", "bundle-explore", "bundle-debug"], "allow_clear": False},
    "bundle-plan": {"allowed": ["bundle-execute", "bundle-spec", "bundle-debug"], "allow_clear": False},
    "bundle-execute": {"allowed": ["bundle-verify", "bundle-debug"], "allow_clear": False},
    "bundle-verify": {"allowed": ["bundle-finish", "bundle-debug", "bundle-execute"], "allow_clear": False},
    "bundle-finish": {"allowed": [], "allow_clear": True},
    "bundle-debug": {"allowed": ["bundle-explore", "bundle-spec", "bundle-plan", "bundle-execute", "bundle-verify", "bundle-finish"], "allow_clear": False},
}


def _parse_mode_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a mode .md file."""
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    assert match, f"No YAML frontmatter found in {path}"
    return yaml.safe_load(match.group(1))


def test_bundle_bot_does_not_exist():
    """bundle-bot.md must NOT exist — it's replaced by the autonomous behavior."""
    bot_path = MODES_DIR / "bundle-bot.md"
    assert not bot_path.exists(), (
        f"modes/bundle-bot.md still exists! It should have been deleted. "
        f"The god mode is replaced by behaviors/bundlewizard-autonomous.yaml."
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
        actual = mode_config.get("allow_clear", True)  # default is True per ModeDefinition
        assert actual == expected["allow_clear"], (
            f"{mode_name}: allow_clear mismatch. "
            f"Expected {expected['allow_clear']}, got {actual}"
        )


def test_autonomous_behavior_exists():
    """The autonomous behavior YAML must exist."""
    path = BEHAVIORS_DIR / "bundlewizard-autonomous.yaml"
    assert path.exists(), (
        "behaviors/bundlewizard-autonomous.yaml does not exist. "
        "This file provides the autonomous operating profile."
    )


def test_autonomous_behavior_config():
    """Autonomous behavior must set gate_policy: auto and autonomous: true."""
    path = BEHAVIORS_DIR / "bundlewizard-autonomous.yaml"
    if not path.exists():
        pytest.skip("bundlewizard-autonomous.yaml not yet created")
    content = yaml.safe_load(path.read_text(encoding="utf-8"))

    # Check hooks-mode autonomous flag
    hooks = content.get("hooks", [])
    hooks_mode_config = None
    for hook in hooks:
        if hook.get("module") == "hooks-mode":
            hooks_mode_config = hook.get("config", {})
            break
    assert hooks_mode_config is not None, "hooks-mode not found in autonomous behavior"
    assert hooks_mode_config.get("autonomous") is True, (
        "hooks-mode config must have autonomous: true"
    )

    # Check tool-mode gate_policy
    tools = content.get("tools", [])
    tool_mode_config = None
    for tool in tools:
        if tool.get("module") == "tool-mode":
            tool_mode_config = tool.get("config", {})
            break
    assert tool_mode_config is not None, "tool-mode not found in autonomous behavior"
    assert tool_mode_config.get("gate_policy") == "auto", (
        "tool-mode config must have gate_policy: auto"
    )


def test_autonomous_behavior_agents_match():
    """Autonomous behavior must register the same 10 agents as interactive."""
    interactive_path = BEHAVIORS_DIR / "bundlewizard.yaml"
    autonomous_path = BEHAVIORS_DIR / "bundlewizard-autonomous.yaml"
    if not autonomous_path.exists():
        pytest.skip("bundlewizard-autonomous.yaml not yet created")

    interactive = yaml.safe_load(interactive_path.read_text(encoding="utf-8"))
    autonomous = yaml.safe_load(autonomous_path.read_text(encoding="utf-8"))

    interactive_agents = sorted(interactive.get("agents", {}).get("include", []))
    autonomous_agents = sorted(autonomous.get("agents", {}).get("include", []))

    assert interactive_agents == autonomous_agents, (
        f"Agent lists differ between interactive and autonomous behaviors.\n"
        f"Interactive: {interactive_agents}\n"
        f"Autonomous:  {autonomous_agents}"
    )


def test_autonomous_protocol_exists():
    """The autonomous protocol context file must exist."""
    path = CONTEXT_DIR / "autonomous-protocol.md"
    assert path.exists(), (
        "context/autonomous-protocol.md does not exist. "
        "This file provides behavioral overrides for autonomous operation."
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

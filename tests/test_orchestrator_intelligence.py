"""Structural contract tests for the orchestrator intelligence feature.

These tests verify:
- The orchestrator-advisor agent exists with proper frontmatter structure
- Three orchestrator context files exist under context/orchestrator/
- The behavior YAML includes the orchestrator-advisor agent in agents.include
- Instructions reference the orchestrator advisor and Orchestrator Module tier
- Content quality assertions for litmus-test.md, kernel-contracts.md, and catalog.md

All tests are expected to FAIL initially (RED phase of TDD) because the
orchestrator intelligence files do not exist yet.
"""

import re
from pathlib import Path

import pytest
import yaml

# Repo root — tests/ is a direct child of the repo root
REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
BEHAVIORS_DIR = REPO_ROOT / "behaviors"
CONTEXT_DIR = REPO_ROOT / "context"
ORCHESTRATOR_CONTEXT_DIR = CONTEXT_DIR / "orchestrator"

AGENT_FILE = AGENTS_DIR / "orchestrator-advisor.md"
BEHAVIOR_FILE = BEHAVIORS_DIR / "bundlewizard.yaml"
INSTRUCTIONS_FILE = CONTEXT_DIR / "instructions.md"

LITMUS_TEST_FILE = ORCHESTRATOR_CONTEXT_DIR / "litmus-test.md"
KERNEL_CONTRACTS_FILE = ORCHESTRATOR_CONTEXT_DIR / "kernel-contracts.md"
CATALOG_FILE = ORCHESTRATOR_CONTEXT_DIR / "catalog.md"


def _parse_agent_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from an agent .md file."""
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    assert match, f"No YAML frontmatter found in {path}"
    return yaml.safe_load(match.group(1))


# ---------------------------------------------------------------------------
# 1. orchestrator-advisor agent existence and frontmatter
# ---------------------------------------------------------------------------


def test_orchestrator_advisor_agent_exists():
    """The orchestrator-advisor agent file must exist at agents/orchestrator-advisor.md."""
    assert AGENT_FILE.exists(), (
        f"agents/orchestrator-advisor.md does not exist at {AGENT_FILE}. "
        "The orchestrator-advisor agent must be created as part of the "
        "orchestrator intelligence feature."
    )


def test_orchestrator_advisor_has_meta_name():
    """The orchestrator-advisor agent frontmatter must have meta.name set correctly."""
    if not AGENT_FILE.exists():
        pytest.skip("orchestrator-advisor.md does not exist yet")
    frontmatter = _parse_agent_frontmatter(AGENT_FILE)
    meta = frontmatter.get("meta", {})
    assert "name" in meta, (
        "agents/orchestrator-advisor.md frontmatter must have a meta.name field. "
        f"Found meta keys: {list(meta.keys())}"
    )
    assert meta["name"] == "orchestrator-advisor", (
        f"meta.name must be 'orchestrator-advisor', got '{meta['name']}'"
    )


def test_orchestrator_advisor_has_meta_description():
    """The orchestrator-advisor agent frontmatter must have meta.description."""
    if not AGENT_FILE.exists():
        pytest.skip("orchestrator-advisor.md does not exist yet")
    frontmatter = _parse_agent_frontmatter(AGENT_FILE)
    meta = frontmatter.get("meta", {})
    assert "description" in meta, (
        "agents/orchestrator-advisor.md frontmatter must have a meta.description field. "
        f"Found meta keys: {list(meta.keys())}"
    )
    description = meta["description"]
    assert description and len(description.strip()) > 0, (
        "meta.description must not be empty"
    )


def test_orchestrator_advisor_description_has_example_blocks():
    """The orchestrator-advisor description must contain at least one <example> block."""
    if not AGENT_FILE.exists():
        pytest.skip("orchestrator-advisor.md does not exist yet")
    frontmatter = _parse_agent_frontmatter(AGENT_FILE)
    description = frontmatter.get("meta", {}).get("description", "")
    assert "<example>" in description, (
        "agents/orchestrator-advisor.md meta.description must contain at least one "
        "<example> block. Agent descriptions require concrete usage examples to help "
        "the orchestrator know when to delegate."
    )


def test_orchestrator_advisor_has_model_role():
    """The orchestrator-advisor agent frontmatter must have meta.model_role."""
    if not AGENT_FILE.exists():
        pytest.skip("orchestrator-advisor.md does not exist yet")
    frontmatter = _parse_agent_frontmatter(AGENT_FILE)
    meta = frontmatter.get("meta", {})
    assert "model_role" in meta, (
        "agents/orchestrator-advisor.md frontmatter must have a meta.model_role field. "
        "The orchestrator-advisor requires reasoning capability for kernel contract analysis."
    )


def test_orchestrator_advisor_model_role_includes_reasoning():
    """The orchestrator-advisor meta.model_role must include 'reasoning'."""
    if not AGENT_FILE.exists():
        pytest.skip("orchestrator-advisor.md does not exist yet")
    frontmatter = _parse_agent_frontmatter(AGENT_FILE)
    model_role = frontmatter.get("meta", {}).get("model_role", [])
    # model_role may be a list or a string
    if isinstance(model_role, str):
        roles = [model_role]
    else:
        roles = list(model_role)
    assert "reasoning" in roles, (
        f"meta.model_role must include 'reasoning' but got: {roles}. "
        "The orchestrator-advisor performs deep architectural analysis of kernel "
        "contracts and orchestrator design decisions, requiring the reasoning model."
    )


# ---------------------------------------------------------------------------
# 2. Orchestrator context files existence
# ---------------------------------------------------------------------------


def test_orchestrator_context_directory_exists():
    """The context/orchestrator/ directory must exist."""
    assert ORCHESTRATOR_CONTEXT_DIR.exists(), (
        f"context/orchestrator/ directory does not exist at {ORCHESTRATOR_CONTEXT_DIR}. "
        "Three orchestrator context files must live here: "
        "kernel-contracts.md, litmus-test.md, and catalog.md."
    )


def test_litmus_test_file_exists():
    """context/orchestrator/litmus-test.md must exist."""
    assert LITMUS_TEST_FILE.exists(), (
        f"context/orchestrator/litmus-test.md does not exist at {LITMUS_TEST_FILE}. "
        "This file teaches the advisor the Create vs Compose distinction for "
        "orchestrator design decisions."
    )


def test_kernel_contracts_file_exists():
    """context/orchestrator/kernel-contracts.md must exist."""
    assert KERNEL_CONTRACTS_FILE.exists(), (
        f"context/orchestrator/kernel-contracts.md does not exist at {KERNEL_CONTRACTS_FILE}. "
        "This file documents the kernel event system, HookResult types, and mount() "
        "contract that all orchestrator modules must implement."
    )


def test_catalog_file_exists():
    """context/orchestrator/catalog.md must exist."""
    assert CATALOG_FILE.exists(), (
        f"context/orchestrator/catalog.md does not exist at {CATALOG_FILE}. "
        "This file provides a reference catalog of existing orchestrators and "
        "reusable pattern library entries."
    )


# ---------------------------------------------------------------------------
# 3. Behavior YAML includes orchestrator-advisor
# ---------------------------------------------------------------------------


def test_behavior_yaml_includes_orchestrator_advisor():
    """behaviors/bundlewizard.yaml agents.include must list the orchestrator-advisor."""
    if not BEHAVIOR_FILE.exists():
        pytest.skip("behaviors/bundlewizard.yaml does not exist yet")
    content = yaml.safe_load(BEHAVIOR_FILE.read_text(encoding="utf-8"))
    agents_include = content.get("agents", {}).get("include", [])
    advisor_entries = [
        entry for entry in agents_include if "orchestrator-advisor" in str(entry)
    ]
    assert advisor_entries, (
        "behaviors/bundlewizard.yaml agents.include must contain an entry for "
        "'orchestrator-advisor'. "
        f"Current agents.include: {agents_include}"
    )


# ---------------------------------------------------------------------------
# 4. Instructions reference orchestrator-advisor and Orchestrator Module tier
# ---------------------------------------------------------------------------


def test_instructions_references_orchestrator_advisor():
    """context/instructions.md must reference the orchestrator-advisor agent."""
    if not INSTRUCTIONS_FILE.exists():
        pytest.skip("context/instructions.md does not exist yet")
    content = INSTRUCTIONS_FILE.read_text(encoding="utf-8")
    assert "orchestrator-advisor" in content, (
        "context/instructions.md must reference 'orchestrator-advisor'. "
        "The main instructions must guide the orchestrator on when to delegate "
        "to the orchestrator-advisor for kernel contract and design decisions."
    )


def test_instructions_references_orchestrator_module_tier():
    """context/instructions.md must reference the Orchestrator Module tier."""
    if not INSTRUCTIONS_FILE.exists():
        pytest.skip("context/instructions.md does not exist yet")
    content = INSTRUCTIONS_FILE.read_text(encoding="utf-8")
    assert "Orchestrator Module" in content, (
        "context/instructions.md must reference 'Orchestrator Module' tier. "
        "This establishes the orchestrator module as a named architectural tier "
        "that users can request and the advisor can explain."
    )


# ---------------------------------------------------------------------------
# 5. Content quality: litmus-test.md
# ---------------------------------------------------------------------------


def test_litmus_test_has_create_indicator_when_llm_called():
    """litmus-test.md must document the 'WHEN the LLM is called' Create indicator."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "WHEN the LLM is called" in content, (
        "litmus-test.md must contain the 'WHEN the LLM is called' Create indicator. "
        "This is the first of 6 Create indicators that distinguish orchestrators "
        "from composition approaches."
    )


def test_litmus_test_has_create_indicator_how_many_times():
    """litmus-test.md must document the 'HOW MANY TIMES the LLM is called' Create indicator."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "HOW MANY TIMES the LLM is called" in content, (
        "litmus-test.md must contain the 'HOW MANY TIMES the LLM is called' Create indicator. "
        "This is the second of 6 Create indicators."
    )


def test_litmus_test_has_create_indicator_which_providers():
    """litmus-test.md must document the 'WHICH PROVIDERS' Create indicator."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "WHICH PROVIDERS" in content, (
        "litmus-test.md must contain the 'WHICH PROVIDERS' Create indicator. "
        "This is the third of 6 Create indicators."
    )


def test_litmus_test_has_create_indicator_what_happens_to_results():
    """litmus-test.md must document the 'WHAT HAPPENS TO RESULTS' Create indicator."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "WHAT HAPPENS TO RESULTS" in content, (
        "litmus-test.md must contain the 'WHAT HAPPENS TO RESULTS' Create indicator. "
        "This is the fourth of 6 Create indicators."
    )


def test_litmus_test_has_create_indicator_sequential_to_parallel():
    """litmus-test.md must document the 'sequential to parallel' Create indicator."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "sequential to parallel" in content, (
        "litmus-test.md must contain the 'sequential to parallel' Create indicator. "
        "This is the fifth of 6 Create indicators — when you need to change from "
        "sequential to parallel execution patterns."
    )


def test_litmus_test_has_create_indicator_structured_phase():
    """litmus-test.md must document the 'structured phase' Create indicator."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "structured phase" in content, (
        "litmus-test.md must contain the 'structured phase' Create indicator. "
        "This is the sixth of 6 Create indicators."
    )


def test_litmus_test_has_compose_mechanism_inject_context():
    """litmus-test.md must document the 'inject_context' Compose mechanism."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "inject_context" in content, (
        "litmus-test.md must contain the 'inject_context' Compose mechanism. "
        "This is the first of 6 Compose mechanisms for modifying behavior without "
        "writing a custom orchestrator."
    )


def test_litmus_test_has_compose_mechanism_deny():
    """litmus-test.md must document the 'deny' Compose mechanism."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert re.search(r"\bdeny\b", content), (
        "litmus-test.md must contain the 'deny' Compose mechanism. "
        "This is the second of 6 Compose mechanisms — blocks tool calls or "
        "provider requests via hook results."
    )


def test_litmus_test_has_compose_mechanism_ask_user():
    """litmus-test.md must document the 'ask_user' Compose mechanism."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "ask_user" in content, (
        "litmus-test.md must contain the 'ask_user' Compose mechanism. "
        "This is the third of 6 Compose mechanisms — pauses execution to gather "
        "human input via hook results."
    )


def test_litmus_test_has_compose_mechanism_tool_task():
    """litmus-test.md must document the 'tool-task' Compose mechanism."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "tool-task" in content, (
        "litmus-test.md must contain the 'tool-task' Compose mechanism. "
        "This is the fourth of 6 Compose mechanisms — delegates work via tool-task "
        "without a custom orchestrator."
    )


def test_litmus_test_has_compose_mechanism_observation_hook():
    """litmus-test.md must document the 'observation hook' Compose mechanism."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "observation hook" in content, (
        "litmus-test.md must contain the 'observation hook' Compose mechanism. "
        "This is the fifth of 6 Compose mechanisms — lets you react to events "
        "without controlling the loop."
    )


def test_litmus_test_has_compose_mechanism_orchestrator_config():
    """litmus-test.md must document the 'orchestrator config' Compose mechanism."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "orchestrator config" in content, (
        "litmus-test.md must contain the 'orchestrator config' Compose mechanism. "
        "This is the sixth of 6 Compose mechanisms — configuring an existing "
        "orchestrator (e.g., changing loop limits) is often sufficient without "
        "building a new one."
    )


def test_litmus_test_has_applied_examples_section():
    """litmus-test.md must have an 'Applied Examples' section header."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "## Applied Examples" in content, (
        "litmus-test.md must contain an '## Applied Examples' section header. "
        "The applied examples (parallel, multi-provider, approval) must live under "
        "a dedicated section so their scope is unambiguous."
    )


def test_litmus_test_has_applied_example_parallel():
    """litmus-test.md must contain an applied example for parallel execution."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "## Applied Examples" in content, (
        "litmus-test.md must have an '## Applied Examples' section before checking "
        "for the parallel example."
    )
    assert "parallel" in content, (
        "litmus-test.md must contain an applied example for parallel orchestration. "
        "Concrete examples help the advisor recognize when the Create path is appropriate."
    )


def test_litmus_test_has_applied_example_multi_provider():
    """litmus-test.md must contain an applied example for multi-provider routing."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "## Applied Examples" in content, (
        "litmus-test.md must have an '## Applied Examples' section before checking "
        "for the multi-provider example."
    )
    assert "multi-provider" in content, (
        "litmus-test.md must contain an applied example for multi-provider routing. "
        "Multi-provider is a key signal that a custom orchestrator is needed."
    )


def test_litmus_test_has_applied_example_approval():
    """litmus-test.md must contain an applied example for approval gates."""
    if not LITMUS_TEST_FILE.exists():
        pytest.skip("litmus-test.md does not exist yet")
    content = LITMUS_TEST_FILE.read_text(encoding="utf-8")
    assert "## Applied Examples" in content, (
        "litmus-test.md must have an '## Applied Examples' section before checking "
        "for the approval example."
    )
    assert "approval" in content, (
        "litmus-test.md must contain an applied example for approval gates. "
        "Approval gates are a common orchestrator pattern that the advisor must "
        "be able to distinguish from hook-based composition."
    )


# ---------------------------------------------------------------------------
# 6. Content quality: kernel-contracts.md
# ---------------------------------------------------------------------------


def test_kernel_contracts_has_event_execution_start():
    """kernel-contracts.md must document the execution:start kernel event."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "execution:start" in content, (
        "kernel-contracts.md must document the 'execution:start' kernel event. "
        "This is the first of 7 required kernel events that orchestrators may intercept."
    )


def test_kernel_contracts_has_event_execution_end():
    """kernel-contracts.md must document the execution:end kernel event."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "execution:end" in content, (
        "kernel-contracts.md must document the 'execution:end' kernel event. "
        "This is the second of 7 required kernel events."
    )


def test_kernel_contracts_has_event_provider_request():
    """kernel-contracts.md must document the provider:request kernel event."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "provider:request" in content, (
        "kernel-contracts.md must document the 'provider:request' kernel event. "
        "This is the third of 7 required kernel events."
    )


def test_kernel_contracts_has_event_provider_response():
    """kernel-contracts.md must document the provider:response kernel event."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "provider:response" in content, (
        "kernel-contracts.md must document the 'provider:response' kernel event. "
        "This is the fourth of 7 required kernel events."
    )


def test_kernel_contracts_has_event_tool_pre():
    """kernel-contracts.md must document the tool:pre kernel event."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "tool:pre" in content, (
        "kernel-contracts.md must document the 'tool:pre' kernel event. "
        "This is the fifth of 7 required kernel events — fires before a tool "
        "is executed and supports deny/modify."
    )


def test_kernel_contracts_has_event_tool_post():
    """kernel-contracts.md must document the tool:post kernel event."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "tool:post" in content, (
        "kernel-contracts.md must document the 'tool:post' kernel event. "
        "This is the sixth of 7 required kernel events."
    )


def test_kernel_contracts_has_event_orchestrator_complete():
    """kernel-contracts.md must document the orchestrator:complete kernel event."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "orchestrator:complete" in content, (
        "kernel-contracts.md must document the 'orchestrator:complete' kernel event. "
        "This is the seventh of 7 required kernel events."
    )


def test_kernel_contracts_has_hookresult_deny():
    """kernel-contracts.md must document the 'deny' HookResult type."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert re.search(r"\bdeny\b", content), (
        "kernel-contracts.md must document the 'deny' HookResult type. "
        "This is the first of 4 HookResult types that hooks can return."
    )


def test_kernel_contracts_has_hookresult_modify():
    """kernel-contracts.md must document the 'modify' HookResult type."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "modify" in content, (
        "kernel-contracts.md must document the 'modify' HookResult type. "
        "This is the second of 4 HookResult types — allows changing the payload "
        "before it is processed."
    )


def test_kernel_contracts_has_hookresult_inject_context():
    """kernel-contracts.md must document the 'inject_context' HookResult type."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "inject_context" in content, (
        "kernel-contracts.md must document the 'inject_context' HookResult type. "
        "This is the third of 4 HookResult types."
    )


def test_kernel_contracts_has_hookresult_ask_user():
    """kernel-contracts.md must document the 'ask_user' HookResult type."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "ask_user" in content, (
        "kernel-contracts.md must document the 'ask_user' HookResult type. "
        "This is the fourth of 4 HookResult types."
    )


def test_kernel_contracts_has_mount_pattern():
    """kernel-contracts.md must document the mount() pattern."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "mount()" in content, (
        "kernel-contracts.md must document the 'mount()' pattern. "
        "All orchestrator modules implement mount() as their entry point — "
        "this is the fundamental kernel contract."
    )


def test_kernel_contracts_has_pyproject_toml_reference():
    """kernel-contracts.md must reference pyproject.toml for the mount() pattern."""
    if not KERNEL_CONTRACTS_FILE.exists():
        pytest.skip("kernel-contracts.md does not exist yet")
    content = KERNEL_CONTRACTS_FILE.read_text(encoding="utf-8")
    assert "pyproject.toml" in content, (
        "kernel-contracts.md must reference 'pyproject.toml' in the context of "
        "the mount() pattern. Modules are registered via pyproject.toml entry points, "
        "and the advisor must understand this wiring."
    )


# ---------------------------------------------------------------------------
# 7. Content quality: catalog.md
# ---------------------------------------------------------------------------


def test_catalog_has_existing_orchestrator_loop_basic():
    """catalog.md must list the 'loop-basic' existing orchestrator."""
    if not CATALOG_FILE.exists():
        pytest.skip("catalog.md does not exist yet")
    content = CATALOG_FILE.read_text(encoding="utf-8")
    assert "loop-basic" in content, (
        "catalog.md must reference the 'loop-basic' existing orchestrator. "
        "This is the first of 3 existing orchestrators that provide the canonical "
        "starting point for new orchestrator designs."
    )


def test_catalog_has_existing_orchestrator_loop_streaming():
    """catalog.md must list the 'loop-streaming' existing orchestrator."""
    if not CATALOG_FILE.exists():
        pytest.skip("catalog.md does not exist yet")
    content = CATALOG_FILE.read_text(encoding="utf-8")
    assert "loop-streaming" in content, (
        "catalog.md must reference the 'loop-streaming' existing orchestrator. "
        "This is the second of 3 existing orchestrators."
    )


def test_catalog_has_existing_orchestrator_loop_events():
    """catalog.md must list the 'loop-events' existing orchestrator."""
    if not CATALOG_FILE.exists():
        pytest.skip("catalog.md does not exist yet")
    content = CATALOG_FILE.read_text(encoding="utf-8")
    assert "loop-events" in content, (
        "catalog.md must reference the 'loop-events' existing orchestrator. "
        "This is the third of 3 existing orchestrators."
    )


def test_catalog_has_pattern_loop_parallel():
    """catalog.md must contain the 'loop-parallel' pattern library entry."""
    if not CATALOG_FILE.exists():
        pytest.skip("catalog.md does not exist yet")
    content = CATALOG_FILE.read_text(encoding="utf-8")
    assert "loop-parallel" in content, (
        "catalog.md must contain the 'loop-parallel' pattern library entry. "
        "This is the first of 5 reusable patterns that users can request by name."
    )


def test_catalog_has_pattern_loop_multi_provider():
    """catalog.md must contain the 'loop-multi-provider' pattern library entry."""
    if not CATALOG_FILE.exists():
        pytest.skip("catalog.md does not exist yet")
    content = CATALOG_FILE.read_text(encoding="utf-8")
    assert "loop-multi-provider" in content, (
        "catalog.md must contain the 'loop-multi-provider' pattern library entry. "
        "This is the second of 5 reusable patterns."
    )


def test_catalog_has_pattern_loop_phased():
    """catalog.md must contain the 'loop-phased' pattern library entry."""
    if not CATALOG_FILE.exists():
        pytest.skip("catalog.md does not exist yet")
    content = CATALOG_FILE.read_text(encoding="utf-8")
    assert "loop-phased" in content, (
        "catalog.md must contain the 'loop-phased' pattern library entry. "
        "This is the third of 5 reusable patterns."
    )


def test_catalog_has_pattern_loop_convergence():
    """catalog.md must contain the 'loop-convergence' pattern library entry."""
    if not CATALOG_FILE.exists():
        pytest.skip("catalog.md does not exist yet")
    content = CATALOG_FILE.read_text(encoding="utf-8")
    assert "loop-convergence" in content, (
        "catalog.md must contain the 'loop-convergence' pattern library entry. "
        "This is the fourth of 5 reusable patterns."
    )


def test_catalog_has_pattern_loop_swarm():
    """catalog.md must contain the 'loop-swarm' pattern library entry."""
    if not CATALOG_FILE.exists():
        pytest.skip("catalog.md does not exist yet")
    content = CATALOG_FILE.read_text(encoding="utf-8")
    assert "loop-swarm" in content, (
        "catalog.md must contain the 'loop-swarm' pattern library entry. "
        "This is the fifth of 5 pattern library entries in the catalog."
    )

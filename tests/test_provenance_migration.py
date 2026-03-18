"""Provenance migration contract tests.

Verify:
- Legacy fixture has the expected old shape (bundle.bundlewizard, no generated_by)
- Canonical schema files contain the right new shape
- Packager is aligned to canonical schema
- No stale bundle-bot references remain in provenance-related files
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
CONTEXT_DIR = REPO_ROOT / "context"
AGENTS_DIR = REPO_ROOT / "agents"
RECIPES_DIR = REPO_ROOT / "recipes"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture_frontmatter(path: Path) -> dict:
    """Load YAML frontmatter from a fixture file."""
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    assert match, f"No YAML frontmatter found in {path}"
    return yaml.safe_load(match.group(1))


# --- Legacy fixture shape tests ---

def test_legacy_fixture_has_bundlewizard_key():
    """Legacy fixture must have bundle.bundlewizard key (the old provenance shape)."""
    path = FIXTURES_DIR / "legacy-provenance.yaml"
    assert path.exists(), "tests/fixtures/legacy-provenance.yaml does not exist"
    data = _load_fixture_frontmatter(path)
    bundle = data.get("bundle", {})
    assert "bundlewizard" in bundle, (
        "Legacy fixture must have bundle.bundlewizard key"
    )


def test_legacy_fixture_has_no_generated_by():
    """Legacy fixture must NOT have bundle.generated_by (that's the new shape)."""
    path = FIXTURES_DIR / "legacy-provenance.yaml"
    data = _load_fixture_frontmatter(path)
    bundle = data.get("bundle", {})
    assert "generated_by" not in bundle, (
        "Legacy fixture must NOT have bundle.generated_by — it represents the old format"
    )


def test_legacy_fixture_has_no_schema_version():
    """Legacy fixture must NOT have schema_version anywhere."""
    path = FIXTURES_DIR / "legacy-provenance.yaml"
    content = path.read_text(encoding="utf-8")
    assert "schema_version" not in content, (
        "Legacy fixture must NOT contain schema_version — it represents the old format"
    )


# --- Canonical schema contract tests ---

def test_canonical_schema_in_factory_protocol():
    """factory-protocol.md must define the canonical generated_by schema with schema_version."""
    path = CONTEXT_DIR / "factory-protocol.md"
    content = path.read_text(encoding="utf-8")
    assert "schema_version" in content, (
        "factory-protocol.md must contain schema_version in the canonical schema"
    )
    assert "generated_by:" in content, (
        "factory-protocol.md must contain generated_by in the canonical schema"
    )
    assert "Legacy Fingerprint Recognition" in content, (
        "factory-protocol.md must document legacy fingerprint recognition rules"
    )


def test_packager_references_bundlewizard_version_source():
    """Packager must source version from bundlewizard's own bundle.md, not a hardcoded literal."""
    path = AGENTS_DIR / "bundle-packager.md"
    content = path.read_text(encoding="utf-8")
    assert "bundle.md" in content.lower() or "bundlewizard" in content.lower(), (
        "Packager must reference bundlewizard's own bundle.md as the version source"
    )
    # Check that there is no hardcoded version literal in generated_by code blocks
    # Look for `version: 0.1.0` inside a generated_by context (not the bundle's own version)
    lines = content.split("\n")
    in_generated_by = False
    for line in lines:
        stripped = line.strip()
        if "generated_by:" in stripped:
            in_generated_by = True
        elif in_generated_by and stripped.startswith("version:") and "0.1.0" in stripped:
            raise AssertionError(
                "Packager must NOT hardcode version: 0.1.0 inside generated_by. "
                "It should instruct the agent to read from bundlewizard's own bundle.md."
            )
        elif in_generated_by and stripped and not stripped.startswith(("#", "-", "`")):
            if not stripped.startswith(" ") and ":" not in stripped:
                in_generated_by = False


def test_packager_no_bundle_bot_section():
    """Packager must NOT contain a /bundle-bot section (stale from deleted mode)."""
    path = AGENTS_DIR / "bundle-packager.md"
    content = path.read_text(encoding="utf-8")
    assert "/bundle-bot" not in content, (
        "Packager still contains a /bundle-bot section. "
        "This is stale from the deleted bundle-bot mode and must be removed."
    )


def test_autonomous_protocol_generated_by_nested():
    """autonomous-protocol.md must show generated_by nested under bundle:, not top-level."""
    path = CONTEXT_DIR / "autonomous-protocol.md"
    content = path.read_text(encoding="utf-8")
    # Check that the generated_by block appears after "bundle:" in a code block
    assert "bundle:\n" in content and "generated_by:" in content, (
        "autonomous-protocol.md must show generated_by nested under bundle:"
    )


def test_autonomous_protocol_has_schema_version():
    """autonomous-protocol.md must include schema_version in the generated_by block."""
    path = CONTEXT_DIR / "autonomous-protocol.md"
    content = path.read_text(encoding="utf-8")
    assert "schema_version" in content, (
        "autonomous-protocol.md must contain schema_version in the audit trail"
    )


def test_recipe_finish_generated_by_has_version_and_schema():
    """Recipe finish stage must include version and schema_version in generated_by."""
    path = RECIPES_DIR / "bundle-autonomous-post-explore.yaml"
    content = path.read_text(encoding="utf-8")
    assert "schema_version" in content, (
        "Recipe finish stage must contain schema_version in the generated_by block"
    )
    assert "version:" in content, (
        "Recipe finish stage must contain version in the generated_by block"
    )

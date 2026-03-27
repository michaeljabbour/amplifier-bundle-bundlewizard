"""Structural contract tests for bundle-critic.md traceability and DOT edge checkboxes.

These tests verify:
- Traceability (Requirement ↔ Artifact) checklist section exists between
  Cross-Cutting and Architecture Diagram Validation sections
- Composition edge checkbox exists in Architecture Diagram Validation section
- Flow edge checkbox exists in Architecture Diagram Validation section
- Output template contains a Traceability section between Level 2 and Issues
"""

from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
BUNDLE_CRITIC = REPO_ROOT / "agents" / "bundle-critic.md"


def _read_critic() -> str:
    return BUNDLE_CRITIC.read_text(encoding="utf-8")


def test_critic_has_traceability_checklist():
    """Critic must have a Traceability (Requirement ↔ Artifact) section with 3 checkboxes
    placed between the Cross-Cutting and Architecture Diagram Validation sections.
    """
    content = _read_critic()

    # Section heading must exist
    assert "### Traceability (Requirement" in content, (
        "Missing '### Traceability (Requirement ↔ Artifact)' section heading in bundle-critic.md"
    )

    # Verify the three required checkboxes are present (case-insensitive)
    lower = content.lower()
    assert (
        "every requirement" in lower and "maps to" in lower and "artifact" in lower
    ), "Missing checkbox: every requirement maps to artifact"

    assert (
        "every artifact" in lower and "traces to" in lower and "requirement" in lower
    ), "Missing checkbox: every artifact traces to requirement"

    assert "orphaned artifact" in lower or "unmet requirement" in lower, (
        "Missing checkbox: no orphaned artifacts or unmet requirements"
    )

    # Verify section ordering: Cross-Cutting BEFORE Traceability BEFORE Architecture Diagram
    cross_cutting_pos = content.find("### Cross-Cutting")
    traceability_pos = content.find("### Traceability (Requirement")
    arch_diagram_pos = content.find("### Architecture Diagram Validation")

    assert cross_cutting_pos != -1, "Missing '### Cross-Cutting' section"
    assert traceability_pos != -1, (
        "Missing '### Traceability (Requirement ↔ Artifact)' section"
    )
    assert arch_diagram_pos != -1, (
        "Missing '### Architecture Diagram Validation' section"
    )

    assert cross_cutting_pos < traceability_pos, (
        "Traceability section must appear AFTER Cross-Cutting section"
    )
    assert traceability_pos < arch_diagram_pos, (
        "Traceability section must appear BEFORE Architecture Diagram Validation section"
    )


def test_critic_has_composition_edge_checkbox():
    """Critic's Architecture Diagram Validation section must contain a checkbox for
    composition edges (style=dashed, color=blue) matching includes: entries in behavior YAML.
    """
    content = _read_critic()

    arch_section_start = content.find("### Architecture Diagram Validation")
    assert arch_section_start != -1, (
        "Missing '### Architecture Diagram Validation' section"
    )

    # Find the end of the arch section (next ### heading or end of file)
    next_heading = content.find("\n### ", arch_section_start + 1)
    arch_section = (
        content[arch_section_start:next_heading]
        if next_heading != -1
        else content[arch_section_start:]
    )

    assert "style=dashed" in arch_section and "color=blue" in arch_section, (
        "Missing composition edge checkbox with style=dashed, color=blue in Architecture Diagram Validation section"
    )
    assert "includes:" in arch_section, (
        "Missing reference to 'includes:' entries in behavior YAML in composition edge checkbox"
    )


def test_critic_has_flow_edge_checkbox():
    """Critic's Architecture Diagram Validation section must contain a checkbox for
    flow edges (style=bold, color=green) matching actual delegate() calls.
    """
    content = _read_critic()

    arch_section_start = content.find("### Architecture Diagram Validation")
    assert arch_section_start != -1, (
        "Missing '### Architecture Diagram Validation' section"
    )

    # Find the end of the arch section (next ### heading or end of file)
    next_heading = content.find("\n### ", arch_section_start + 1)
    arch_section = (
        content[arch_section_start:next_heading]
        if next_heading != -1
        else content[arch_section_start:]
    )

    assert "style=bold" in arch_section and "color=green" in arch_section, (
        "Missing flow edge checkbox with style=bold, color=green in Architecture Diagram Validation section"
    )
    assert "delegate()" in arch_section, (
        "Missing reference to 'delegate()' calls in flow edge checkbox"
    )


def test_critic_output_has_traceability():
    """Critic output template must contain a ### Traceability section between
    Level 2 and Issues sections, with Unmet requirements and Orphaned artifacts fields.
    """
    content = _read_critic()

    # Find the output template block (within the markdown code block)
    output_block_start = content.find("## Output")
    assert output_block_start != -1, "Missing '## Output' section"

    output_section = content[output_block_start:]

    assert "### Traceability" in output_section, (
        "Output template missing '### Traceability' section"
    )

    assert "Unmet requirements" in output_section, (
        "Output template Traceability section missing 'Unmet requirements' field"
    )

    assert "Orphaned artifacts" in output_section, (
        "Output template Traceability section missing 'Orphaned artifacts' field"
    )

    # Verify ordering: Level 2 BEFORE Traceability BEFORE Issues
    level2_pos = output_section.find("### Level 2")
    traceability_pos = output_section.find("### Traceability")
    issues_pos = output_section.find("### Issues")

    assert level2_pos != -1, "Output template missing '### Level 2' section"
    assert issues_pos != -1, "Output template missing '### Issues' section"

    assert level2_pos < traceability_pos, (
        "Traceability section must appear AFTER Level 2 in output template"
    )
    assert traceability_pos < issues_pos, (
        "Traceability section must appear BEFORE Issues in output template"
    )

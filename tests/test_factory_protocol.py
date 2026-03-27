"""Factory protocol document structural contract tests.

Verify that context/factory-protocol.md contains:
- A ### DOT Edge Schema subsection with edge type table
- Composition edge type definition
- Agentic flow edge type definition
"""

from conftest import CONTEXT_DIR, required_text

FACTORY_PROTOCOL_MD = CONTEXT_DIR / "factory-protocol.md"


# ---------------------------------------------------------------------------
# DOT Edge Schema section tests
# ---------------------------------------------------------------------------


def test_factory_protocol_has_dot_edge_schema():
    """factory-protocol.md must contain a '### DOT Edge Schema' subsection."""
    text = required_text(FACTORY_PROTOCOL_MD)
    assert "### DOT Edge Schema" in text, (
        "context/factory-protocol.md must contain a '### DOT Edge Schema' subsection"
    )


def test_factory_protocol_dot_schema_mentions_composition():
    """factory-protocol.md DOT Edge Schema must define Composition edge type."""
    text = required_text(FACTORY_PROTOCOL_MD)
    assert "### DOT Edge Schema" in text, (
        "context/factory-protocol.md must contain a '### DOT Edge Schema' subsection"
    )
    # Find the DOT Edge Schema section and check for Composition
    schema_start = text.index("### DOT Edge Schema")
    # Find next heading of same or higher level
    next_heading_pos = len(text)
    for marker in ["### ", "## ", "# "]:
        pos = text.find("\n" + marker, schema_start + 1)
        if pos != -1 and pos < next_heading_pos:
            next_heading_pos = pos
    schema_section = text[schema_start:next_heading_pos]
    assert "Composition" in schema_section, (
        "The '### DOT Edge Schema' section must mention 'Composition' edge type"
    )


def test_factory_protocol_dot_schema_mentions_agentic_flow():
    """factory-protocol.md DOT Edge Schema must define Agentic flow edge type."""
    text = required_text(FACTORY_PROTOCOL_MD)
    assert "### DOT Edge Schema" in text, (
        "context/factory-protocol.md must contain a '### DOT Edge Schema' subsection"
    )
    # Find the DOT Edge Schema section and check for Agentic flow
    schema_start = text.index("### DOT Edge Schema")
    # Find next heading of same or higher level
    next_heading_pos = len(text)
    for marker in ["### ", "## ", "# "]:
        pos = text.find("\n" + marker, schema_start + 1)
        if pos != -1 and pos < next_heading_pos:
            next_heading_pos = pos
    schema_section = text[schema_start:next_heading_pos]
    assert "Agentic flow" in schema_section, (
        "The '### DOT Edge Schema' section must mention 'Agentic flow' edge type"
    )

"""Factory protocol document structural contract tests.

Verify that context/factory-protocol.md contains:
- A ### DOT Edge Schema subsection with edge type table
- Composition edge type definition
- Agentic flow edge type definition
"""

import functools

from conftest import CONTEXT_DIR, extract_markdown_section, required_text

FACTORY_PROTOCOL_MD = CONTEXT_DIR / "factory-protocol.md"


@functools.lru_cache(maxsize=1)
def _dot_edge_schema_section() -> str:
    """Return the cached ### DOT Edge Schema subsection."""
    return extract_markdown_section(
        required_text(FACTORY_PROTOCOL_MD), "DOT Edge Schema", level=3
    )


# ---------------------------------------------------------------------------
# DOT Edge Schema section tests
# ---------------------------------------------------------------------------


def test_factory_protocol_has_dot_edge_schema():
    """factory-protocol.md must contain a '### DOT Edge Schema' subsection."""
    assert _dot_edge_schema_section().startswith("### DOT Edge Schema"), (
        "context/factory-protocol.md must contain a '### DOT Edge Schema' subsection"
    )


def test_factory_protocol_dot_schema_mentions_composition():
    """factory-protocol.md DOT Edge Schema must define Composition edge type."""
    assert "Composition" in _dot_edge_schema_section(), (
        "The '### DOT Edge Schema' section must mention 'Composition' edge type"
    )


def test_factory_protocol_dot_schema_mentions_agentic_flow():
    """factory-protocol.md DOT Edge Schema must define Agentic flow edge type."""
    assert "Agentic flow" in _dot_edge_schema_section(), (
        "The '### DOT Edge Schema' section must mention 'Agentic flow' edge type"
    )

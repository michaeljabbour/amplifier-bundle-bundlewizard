"""Tests for extract_graph_block() in ws_handler."""

from bundlewizard_bridge.ws_handler import extract_graph_block


def test_extract_graph_block_valid():
    """Valid bundlewizard-graph block is extracted and clean text is returned."""
    text = (
        "Here is the graph:\n"
        "```bundlewizard-graph\n"
        '{"nodes": [{"id": "A"}], "edges": [{"from": "A", "to": "B"}]}\n'
        "```\n"
        "Done."
    )
    graph_json, clean_text = extract_graph_block(text)

    assert graph_json is not None
    assert graph_json["nodes"] == [{"id": "A"}]
    assert graph_json["edges"] == [{"from": "A", "to": "B"}]
    assert "```bundlewizard-graph" not in clean_text
    assert "Done." in clean_text


def test_extract_graph_block_no_block():
    """Text with no bundlewizard-graph block returns (None, original text)."""
    text = "Just some plain text with no graph block."
    graph_json, clean_text = extract_graph_block(text)

    assert graph_json is None
    assert clean_text == text


def test_extract_graph_block_malformed_json():
    """Malformed JSON in block returns None for graph but still strips the block."""
    text = (
        "Before block.\n"
        "```bundlewizard-graph\n"
        "{this is not valid json}\n"
        "```\n"
        "After block."
    )
    graph_json, clean_text = extract_graph_block(text)

    assert graph_json is None
    assert "```bundlewizard-graph" not in clean_text
    assert "After block." in clean_text


def test_extract_graph_block_multiple_blocks():
    """When multiple blocks exist, the last one is extracted (latest state)."""
    text = (
        "First state:\n"
        "```bundlewizard-graph\n"
        '{"nodes": [{"id": "first"}], "edges": []}\n'
        "```\n"
        "Second state:\n"
        "```bundlewizard-graph\n"
        '{"nodes": [{"id": "second"}], "edges": []}\n'
        "```\n"
        "Final text."
    )
    graph_json, clean_text = extract_graph_block(text)

    assert graph_json is not None
    assert graph_json["nodes"] == [{"id": "second"}]
    assert "```bundlewizard-graph" not in clean_text
    assert "Final text." in clean_text


def test_extract_preserves_other_code_blocks():
    """Non-graph code blocks (yaml, python, etc.) are preserved in clean text."""
    text = (
        "Here is some yaml:\n"
        "```yaml\n"
        "key: value\n"
        "```\n"
        "And a graph:\n"
        "```bundlewizard-graph\n"
        '{"nodes": [], "edges": []}\n'
        "```\n"
        "End."
    )
    graph_json, clean_text = extract_graph_block(text)

    assert graph_json is not None
    assert "```yaml" in clean_text
    assert "key: value" in clean_text
    assert "```bundlewizard-graph" not in clean_text

"""Test dialog preprocessing in AIF graphs."""

import json
from pathlib import Path

from arguebuf.load._load_aif import preprocess_dialog
from arguebuf.schemas import aif


def test_preprocess_dialog_6064():
    """Test preprocessing of complex dialog structure in 6064.json."""
    # Load test data
    data_dir = Path(__file__).parent.parent / "data"

    with open(data_dir / "6064-original.json") as f:
        original = json.load(f)

    with open(data_dir / "6064-reconstructed.json") as f:
        expected = json.load(f)

    # Run preprocessing
    result = preprocess_dialog(original)

    # Check that we have the same number of nodes
    assert len(result["nodes"]) == len(expected["nodes"])

    # Separate original nodes from new rephrase nodes
    original_node_ids = {n["nodeID"] for n in original["nodes"]}

    result_original_nodes = [
        n for n in result["nodes"] if n["nodeID"] in original_node_ids
    ]
    result_new_nodes = [
        n for n in result["nodes"] if n["nodeID"] not in original_node_ids
    ]

    expected_original_nodes = [
        n for n in expected["nodes"] if n["nodeID"] in original_node_ids
    ]
    expected_new_nodes = [
        n for n in expected["nodes"] if n["nodeID"] not in original_node_ids
    ]

    # Check original nodes are preserved correctly
    assert len(result_original_nodes) == len(expected_original_nodes)

    result_original_sorted = sorted(result_original_nodes, key=lambda n: n["nodeID"])
    expected_original_sorted = sorted(
        expected_original_nodes, key=lambda n: n["nodeID"]
    )

    for r_node, e_node in zip(result_original_sorted, expected_original_sorted):
        assert r_node["nodeID"] == e_node["nodeID"]
        assert r_node["type"] == e_node["type"]
        assert r_node["text"] == e_node["text"]
        assert r_node["timestamp"] == e_node["timestamp"]

    # Check new rephrase nodes
    assert len(result_new_nodes) == len(expected_new_nodes)
    for node in result_new_nodes:
        assert node["type"] == "MA"
        assert node["text"] == "Default Rephrase"

    # Check edges count
    assert len(result["edges"]) == len(expected["edges"])

    # Check that locutions are preserved (they match the expected output)
    assert len(result["locutions"]) == len(original["locutions"])

    # Verify all dialogue nodes were removed
    for node in result["nodes"]:
        assert node["type"] not in {"L", "TA", "YA"}, (
            f"Dialogue node {node['nodeID']} not removed"
        )


def test_preprocess_dialog_preserves_argument_structure():
    """Test that preprocessing preserves the essential argument structure."""
    original: aif.Graph = {
        "nodes": [
            {"nodeID": "n1", "text": "Claim 1", "type": "I", "timestamp": ""},
            {"nodeID": "n2", "text": "Support", "type": "RA", "timestamp": ""},
            {"nodeID": "n3", "text": "Claim 2", "type": "I", "timestamp": ""},
            {"nodeID": "l1", "text": "Speaker", "type": "L", "timestamp": ""},
            {"nodeID": "ta1", "text": "Transition", "type": "TA", "timestamp": ""},
            {"nodeID": "ya1", "text": "Asserting", "type": "YA", "timestamp": ""},
        ],
        "edges": [
            {"edgeID": "e1", "fromID": "n1", "toID": "n2", "formEdgeID": None},
            {"edgeID": "e2", "fromID": "n2", "toID": "n3", "formEdgeID": None},
            {"edgeID": "e3", "fromID": "l1", "toID": "ta1", "formEdgeID": None},
            {"edgeID": "e4", "fromID": "ta1", "toID": "ya1", "formEdgeID": None},
            {"edgeID": "e5", "fromID": "ya1", "toID": "n1", "formEdgeID": None},
        ],
        "locutions": [],
    }

    result = preprocess_dialog(original)

    # Check that argument nodes and edges are preserved
    assert len([n for n in result["nodes"] if n["type"] == "I"]) == 2
    assert len([n for n in result["nodes"] if n["type"] == "RA"]) == 1

    # Check that the main argument structure is intact
    edges = result["edges"]
    assert any(e["fromID"] == "n1" and e["toID"] == "n2" for e in edges)
    assert any(e["fromID"] == "n2" and e["toID"] == "n3" for e in edges)

    # Check that dialogue nodes are removed
    assert not any(n["type"] in {"L", "TA", "YA"} for n in result["nodes"])


def test_preprocess_dialog_no_dialogue_nodes():
    """Test that preprocessing works correctly when there are no dialogue nodes."""
    original: aif.Graph = {
        "nodes": [
            {"nodeID": "n1", "text": "Claim 1", "type": "I", "timestamp": ""},
            {"nodeID": "n2", "text": "Support", "type": "RA", "timestamp": ""},
            {"nodeID": "n3", "text": "Claim 2", "type": "I", "timestamp": ""},
        ],
        "edges": [
            {"edgeID": "e1", "fromID": "n1", "toID": "n2", "formEdgeID": None},
            {"edgeID": "e2", "fromID": "n2", "toID": "n3", "formEdgeID": None},
        ],
        "locutions": [],
    }

    result = preprocess_dialog(original)

    # Should be unchanged
    assert len(result["nodes"]) == len(original["nodes"])
    assert len(result["edges"]) == len(original["edges"])
    assert all(n in result["nodes"] for n in original["nodes"])
    assert all(e in result["edges"] for e in original["edges"])

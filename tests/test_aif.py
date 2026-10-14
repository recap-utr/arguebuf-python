"""Test the import and export of AIF and xAIF graphs."""

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pytest

import arguebuf as ag
from arguebuf.model.scheme import Attack, Preference, Rephrase, Support

DATA = Path(__file__).parent.parent / "data"


def _relations(graph: ag.Graph) -> Counter[tuple[str, frozenset[str], frozenset[str]]]:
    return Counter(
        (
            node.label,
            frozenset(atom.id for atom in graph.incoming_atom_nodes(node)),
            frozenset(atom.id for atom in graph.outgoing_atom_nodes(node)),
        )
        for node in graph.scheme_nodes.values()
    )


def test_reconstruct_dialog():
    config = ag.load.Config(reconstruct_dialog=True)
    graph = ag.load.file(DATA / "6064-original.json", config=config)
    expected = ag.load.file(DATA / "6064-reconstructed.json")

    assert graph.atom_nodes.keys() == expected.atom_nodes.keys()
    assert _relations(graph) == _relations(expected)


def test_dialog_xaif():
    def node(id: int, type: str, text: str = "") -> dict[str, object]:
        return {"nodeID": id, "text": text or f"{type}{id}", "type": type}

    def edge(id: int, source: int, target: int) -> dict[str, object]:
        return {"edgeID": id, "fromID": source, "toID": target}

    # L0 (Bob) asserts I1, L3 (Alice) asserts I4, both are linked by TA6
    obj = {
        "AIF": {
            "nodes": [
                node(0, "L", "Hello"),
                node(1, "I"),
                node(2, "YA"),
                node(3, "L", "Hi"),
                node(4, "I"),
                node(5, "YA"),
                node(6, "TA"),
            ],
            "edges": [
                edge(0, 0, 2),
                edge(1, 2, 1),
                edge(2, 3, 5),
                edge(3, 5, 4),
                edge(4, 0, 6),
                edge(5, 6, 3),
            ],
            "locutions": [{"nodeID": 0, "personID": 0}, {"nodeID": 3, "personID": 1}],
            "schemefulfillments": None,
            "descriptorfulfillments": None,
            "participants": [
                {"participantID": 0, "firstname": "Bob", "surname": "Smith"}
            ],
        },
        "text": {"txt": ""},
        "dialog": True,
    }

    graph = ag.load.dict(obj)

    assert len(graph.edges) == 0

    # participant 1 is not listed, so its name is unknown
    for id, name, text in (("1", "Bob Smith", "Hello"), ("4", None, "Hi")):
        atom = graph.atom_nodes[id]

        assert atom.participant and atom.participant.name == name
        assert atom.reference and atom.reference.text == text

    graph = ag.load.dict(obj, config=ag.load.Config(reconstruct_dialog=True))

    assert _relations(graph) == Counter(
        [("Rephrase", frozenset({"1"}), frozenset({"4"}))]
    )


@pytest.mark.parametrize("format", [ag.dump.Format.AIF, ag.dump.Format.XAIF])
def test_roundtrip(format: ag.dump.Format):
    timestamp = datetime(2020, 1, 2, 3, 4, 5, tzinfo=UTC)
    graph = ag.Graph()
    claim = ag.AtomNode("Claim", metadata=ag.Metadata(timestamp, timestamp))

    for scheme in (*Support, Attack.DEFAULT, Rephrase.DEFAULT, Preference.DEFAULT):
        premise = ag.AtomNode(scheme.value)
        graph.add_edge(ag.Edge(premise, node := ag.SchemeNode(scheme)))
        graph.add_edge(ag.Edge(node, claim))

    config = ag.dump.Config(format=format)
    loaded = ag.load.dict(json.loads(json.dumps(ag.dump.dict(graph, config))))

    assert _relations(loaded) == _relations(graph)
    assert loaded.edges.keys() == graph.edges.keys()
    # only AIF stores timestamps
    assert (loaded.atom_nodes[claim.id].metadata.created == timestamp) == (
        format == ag.dump.Format.AIF
    )

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
    graph = ag.load.file(DATA / "dialog-original.json", reconstruct_dialog=True)
    expected = ag.load.file(DATA / "dialog-reconstructed.json")

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

        assert atom.participant and graph.participants[atom.participant].name == name
        assert atom.reference and atom.reference.text == text

    graph = ag.load.dict(obj, reconstruct_dialog=True)

    assert _relations(graph) == Counter(
        [("Rephrase", frozenset({"1"}), frozenset({"4"}))]
    )


@pytest.mark.parametrize("format", [ag.dump.Format.AIF, ag.dump.Format.XAIF])
def test_roundtrip(format: ag.dump.Format):
    timestamp = datetime(2020, 1, 2, 3, 4, 5, tzinfo=UTC)
    graph = ag.Graph()
    claim = ag.AtomNode("Claim", metadata=ag.Metadata(timestamp))
    graph.add_node(claim)

    for scheme in (*Support, Attack.DEFAULT, Rephrase.DEFAULT, Preference.DEFAULT):
        premise = ag.AtomNode(scheme.value)
        graph.add_node(premise)
        graph.add_node(node := ag.SchemeNode(scheme))
        graph.add_edge(ag.Edge(premise.id, node.id))
        graph.add_edge(ag.Edge(node.id, claim.id))

    loaded = ag.load.dict(json.loads(json.dumps(ag.dump.dict(graph, format=format))))

    assert _relations(loaded) == _relations(graph)
    assert loaded.edges.keys() == graph.edges.keys()
    # only AIF stores timestamps
    assert (loaded.atom_nodes[claim.id].metadata.created == timestamp) == (
        format == ag.dump.Format.AIF
    )


def test_ambiguous_locutions():
    def node(id: int, type: str) -> dict[str, object]:
        return {"nodeID": id, "text": f"{type}{id}", "type": type}

    def edge(source: int, target: int) -> dict[str, object]:
        return {"edgeID": f"{source}-{target}", "fromID": source, "toID": target}

    # I0 is asserted by L1 and L2 of different persons, I3 by L4 and L5 of one person
    obj = {
        "nodes": [node(i, t) for i, t in enumerate("ILLILL")]
        + [node(i, "YA") for i in range(6, 10)],
        "edges": [
            *(edge(source, ya) for source, ya in ((1, 6), (2, 7), (4, 8), (5, 9))),
            *(edge(ya, atom) for ya, atom in ((6, 0), (7, 0), (8, 3), (9, 3))),
        ],
        "locutions": [
            {"nodeID": node_id, "personID": person}
            for node_id, person in ((1, "a"), (2, "b"), (4, "a"), (5, "a"))
        ],
    }
    graph = ag.load.dict(obj)

    assert graph.atom_nodes["0"].participant is None
    assert graph.atom_nodes["3"].participant == "a"
    assert graph.atom_nodes["0"].reference is None
    assert graph.atom_nodes["3"].reference is None


def test_xaif_resources_and_participants():
    graph = ag.Graph()
    graph.add_resource(ag.Resource("a < b &\nc"))
    graph.add_participant(ag.Participant("Bob van Smith"))
    xaif = ag.dump.xaif(graph)
    loaded = ag.load.dict(json.loads(json.dumps(xaif)))

    assert [r.text for r in loaded.resources.values()] == ["a < b &\nc"]
    assert [p.name for p in loaded.participants.values()] == ["Bob van Smith"]
    assert xaif["AIF"].get("participants") == [
        {
            "participantID": next(iter(graph.participants)),
            "firstname": "Bob",
            "surname": "van Smith",
        }
    ]


def test_lenient_aif():
    # a locution node listed with two speakers, no `locutions` key in the second graph
    nodes = [
        {"nodeID": 1, "text": "I1", "type": "I"},
        {"nodeID": 2.0, "text": "L2", "type": "L"},
        {"nodeID": "3", "text": "YA3", "type": "YA"},
        {"nodeID": 4, "text": "Default Conflict", "type": "CA", "scheme": None},
    ]
    edges = [
        {"edgeID": 1, "fromID": 2, "toID": 3},
        {"edgeID": 2, "fromID": 3, "toID": 1},
    ]
    locutions = [{"nodeID": 2, "personID": "a"}, {"nodeID": 2, "personID": "b"}]
    graph = ag.load.dict({"nodes": nodes, "edges": edges, "locutions": locutions})

    assert graph.atom_nodes["1"].participant is None
    assert graph.atom_nodes["1"].reference == ag.Reference("L2")
    assert graph.scheme_nodes["4"].label == "Attack"
    assert ag.load.dict({"nodes": nodes, "edges": edges}).nodes.keys() == {"1", "4"}
    assert not ag.load.dict({"AIF": {"nodes": [], "edges": []}, "text": None}).resources

    with pytest.raises(ValueError, match="integer"):
        ag.load.dict(
            {"nodes": [{"nodeID": 1.5, "text": "I", "type": "I"}], "edges": []}
        )

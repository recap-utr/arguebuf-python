import logging
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest
from arg_services.graph.v1 import graph_pb2

import arguebuf as ag
from arguebuf.load._helpers import new_reference
from arguebuf.model.utils import Entity

from .conftest import new_graph


def _sample() -> tuple[ag.Graph, ag.AtomNode, ag.Participant, ag.Resource]:
    p, r = ag.Participant("p"), ag.Resource("r")
    a = ag.AtomNode(
        "a", participant=p, reference=ag.Reference("a", resource=r, offset=0)
    )
    g = ag.Graph()
    g.add_participant(p)
    g.add_resource(r)
    g.add_node(a)

    return g, a, p, r


def test_parallel_edges():
    a, s = ag.AtomNode("a"), ag.SchemeNode()
    g = new_graph(a, s)
    e1, e2 = ag.Edge(a, s), ag.Edge(a, s)
    g.add_edge(e1)
    g.add_edge(e2)
    g.remove_edge(e1)

    assert g.outgoing_nodes(a) == {s}

    g.remove_edge(e2.id)

    assert g.outgoing_nodes(a) == set()


def test_remove_node_cascades():
    a, s = ag.AtomNode("a"), ag.SchemeNode(premise_descriptors=[])
    g = new_graph(a, s)
    s.premise_descriptors.append(a.id)
    g.major_claim = a
    g.remove_node(a.id)

    assert g.major_claim is None
    assert s.premise_descriptors == []


def test_remove_cascades_to_atoms():
    g, a, p, r = _sample()
    g.remove_participant(p)
    g.remove_resource(r.id)

    assert a.participant is None
    assert a.reference == ag.Reference("a")
    assert g.name is None


def test_strict_references():
    a = ag.AtomNode("a", id="x")
    g = new_graph(a)

    with pytest.raises(ValueError):
        g.add_edge(ag.Edge(ag.AtomNode("copy", id="x"), a))

    with pytest.raises(ValueError):
        g.add_node(
            ag.AtomNode("b", reference=ag.Reference("b", resource=ag.Resource("r")))
        )


def test_cycles_terminate():
    a1, a2, s1, s2 = (
        ag.AtomNode("a1"),
        ag.AtomNode("a2"),
        ag.SchemeNode(),
        ag.SchemeNode(),
    )
    g = new_graph(a1, a2, s1, s2, edges=((a1, s1), (s1, s2), (s2, s1), (a2, s2)))

    assert g.outgoing_atom_nodes(a1) == set()
    assert g.sibling_node_distances(a1, max_levels=None) == {s2: 1}


def test_entity_equality():
    assert ag.AtomNode("a", id="x") == ag.AtomNode("b", id="x")
    assert ag.AtomNode("a", id="x") != ag.SchemeNode(id="x")


@pytest.mark.parametrize(
    "entity",
    (
        ag.AtomNode("a", id="atom"),
        ag.SchemeNode(id="scheme"),
        ag.Edge(ag.AtomNode("a"), ag.AtomNode("b"), id="edge"),
        ag.Resource("r", id="resource"),
        ag.Participant("p", id="participant"),
        ag.Analyst("n", id="analyst"),
    ),
)
def test_entity_id_is_read_only(entity: Entity) -> None:
    original_id = entity.id

    with pytest.raises(AttributeError):
        object.__setattr__(entity, "id", "changed")

    with pytest.raises(AttributeError):
        delattr(entity, "id")

    assert entity.id == original_id
    assert deepcopy(entity) == entity


def test_networkx_attribute_names() -> None:
    atom, scheme = ag.AtomNode("a"), ag.SchemeNode()
    g = new_graph(atom, scheme, edges=((atom, scheme),))
    exported = ag.dump.networkx(
        g,
        graph_attrs={"incoming_graph_data": lambda graph: graph.name},
        atom_attrs={"node_for_adding": lambda node: node.id},
        scheme_attrs={"node_for_adding": lambda node: node.id},
        edge_attrs={
            "u_of_edge": lambda edge: edge.source.id,
            "v_of_edge": lambda edge: edge.target.id,
        },
    )

    assert exported.graph == {"incoming_graph_data": None}
    assert exported.nodes[atom.id] == {"label": "a", "node_for_adding": atom.id}
    assert exported.nodes[scheme.id] == {
        "label": "Unknown",
        "node_for_adding": scheme.id,
    }
    assert exported.edges[atom.id, scheme.id] == {
        "u_of_edge": atom.id,
        "v_of_edge": scheme.id,
    }


def test_dump_aif_utc():
    timestamp = datetime(2020, 1, 1, 12, tzinfo=timezone(timedelta(hours=2)))
    a = ag.AtomNode("a", metadata=ag.Metadata(timestamp))
    aif = ag.dump.aif(new_graph(a))

    assert aif["nodes"][0].get("timestamp") == "2020-01-01 10:00:00"


def test_protobuf_roundtrip():
    g, a, p, r = _sample()
    a.userdata["count"] = 1
    g.major_claim = a
    proto = ag.dump.protobuf(g)
    loaded = ag.load.protobuf(proto)

    assert proto.library_version.startswith("arguebuf-python:")
    assert loaded.major_claim == a
    assert loaded.atom_nodes[a.id].participant == p
    assert loaded.atom_nodes[a.id].reference == ag.Reference("a", resource=r, offset=0)
    assert loaded.atom_nodes[a.id].metadata == a.metadata
    assert ag.copy(g).atom_nodes[a.id].userdata == {"count": 1}


def test_protobuf_dangling(caplog: pytest.LogCaptureFixture):
    proto = graph_pb2.Graph(
        nodes={
            "a": graph_pb2.Node(
                atom=graph_pb2.Atom(
                    text="a",
                    participant="p",
                    reference=graph_pb2.Reference(text="a", resource="r", offset=1),
                )
            )
        },
        edges={"e": graph_pb2.Edge(source="a", target="b")},
        major_claim="b",
    )

    with caplog.at_level(logging.WARNING):
        g = ag.load.protobuf(proto)

    atom = g.atom_nodes["a"]

    assert len(g.edges) == 0
    assert g.major_claim is None
    assert atom.participant is None
    assert atom.reference == ag.Reference("a")
    assert len(caplog.records) == 4


def test_reference_offsets(caplog: pytest.LogCaptureFixture):
    resources = {"r": ag.Resource("text", id="r")}

    with caplog.at_level(logging.WARNING):
        known = new_reference("a", "r", 1, resources, "atom")
        missing = new_reference("a", "", 1, resources, "atom")
        unknown = new_reference("a", "x", 1, resources, "atom")

    assert known == ag.Reference("a", resource=resources["r"], offset=1)
    assert missing == ag.Reference("a", offset=1)
    assert unknown == ag.Reference("a")
    assert len(caplog.records) == 1

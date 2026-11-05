import copy
import logging
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest
from arg_services.graph.v1 import graph_pb2

import arguebuf as ag
from arguebuf.load._helpers import Context, new_reference
from arguebuf.model.utils import Entity

from .conftest import new_draft


def _sample() -> tuple[ag.GraphDraft, ag.AtomNode, ag.Participant, ag.Resource]:
    p, r = ag.Participant("p"), ag.Resource("a")
    a = ag.AtomNode(
        "a", participant=p.id, reference=ag.Reference("a", resource=r.id, offset=0)
    )
    g = ag.GraphDraft()
    g.add_participant(p)
    g.add_resource(r)
    g.add_node(a)

    return g, a, p, r


def test_strict_edges():
    a, b, s = ag.AtomNode("a"), ag.AtomNode("b"), ag.SchemeNode()
    g = new_draft(a, b, s)
    e = ag.Edge(a.id, s.id)
    g.add_edge(e)

    for edge, code in (
        (ag.Edge(a.id, s.id), "parallel-edge"),
        (ag.Edge(s.id, s.id), "self-loop"),
        (ag.Edge(a.id, b.id), "atom-edge"),
        (e, "duplicate-id"),
    ):
        with pytest.raises(ag.GraphError) as error:
            g.add_edge(edge)

        assert error.value.issue.code == code

    g.remove_edge(e.id)

    assert g.outgoing_nodes(a) == set()


def test_updates_validate_and_keep_edges():
    g, a, _, r = _sample()
    s = ag.SchemeNode()
    g.add_node(s)
    g.add_edge(ag.Edge(a.id, s.id, id="e"))
    g.update_atom(a, text="b")
    g.update_edge("e", userdata={"weight": 1})

    assert g.atom_nodes[a.id].text == "b"
    assert g.outgoing_edges(a) == {g.edges["e"]}
    assert g.edges["e"].userdata == {"weight": 1}

    with pytest.raises(ag.GraphError):
        g.update_atom(a, participant="missing")

    with pytest.raises(ag.GraphError):
        g.update_atom(s.id, text="scheme")

    g.update_resource(r, text="xa")

    assert g.atom_nodes[a.id].reference == ag.Reference("a", resource=r.id, offset=1)


def test_remove_node_cascades():
    a, s = ag.AtomNode("a", id="a"), ag.SchemeNode(premise_descriptors=["a"])
    g = new_draft(a, s)
    g.major_claim = a
    g.remove_node(a.id)

    assert g.major_claim is None
    assert g.scheme_nodes[s.id].premise_descriptors == ()


def test_remove_cascades_to_atoms():
    g, a, p, r = _sample()
    g.remove_participant(p)
    g.remove_resource(r.id)

    assert g.atom_nodes[a.id].participant is None
    assert g.atom_nodes[a.id].reference == ag.Reference("a")
    assert a.participant == p.id
    assert g.name is None


def test_drafts_never_leak_writes():
    g, a, p, r = _sample()
    s, c = ag.SchemeNode(id="s"), ag.AtomNode("c", id="c")
    g.add_node(s)
    g.add_node(c)
    g.connect([a.id], s, c)
    frozen = g.freeze()
    other = frozen.draft()

    def snapshot(graph: ag.Graph | ag.GraphDraft) -> object:
        return (
            graph.major_claim,
            list(graph.nodes),
            list(graph.edges),
            list(graph.resources),
            list(graph.participants),
            [
                (list(graph.incoming_edges(n)), list(graph.outgoing_edges(n)))
                for n in graph.nodes
            ],
        )

    before = snapshot(frozen)
    other.remove_edge(next(iter(other.incoming_edges(c.id))))
    other.add_edge(ag.Edge(s.id, c.id, id="e"))
    other.remove_participant(p)
    other.major_claim = c
    copied = snapshot(other)
    g.remove_node(s)
    g.remove_resource(r)
    g.add_node(ag.AtomNode("x", id="x"))

    assert snapshot(frozen) == before
    assert snapshot(other) == copied
    assert snapshot(g.freeze()) == snapshot(g)
    assert {n.id for n in other.incoming_nodes(s.id)} == {a.id}

    for name in ("name", "major_claim", "_store"):
        with pytest.raises(AttributeError):
            setattr(frozen, name, None)


def test_strict_references():
    a = ag.AtomNode("a", id="x")
    g = new_draft(a)

    with pytest.raises(ValueError):
        g.add_edge(ag.Edge("missing", a.id))

    with pytest.raises(ValueError):
        g.add_node(
            ag.AtomNode("b", reference=ag.Reference("b", resource=ag.Resource("r").id))
        )


def test_cycles_terminate():
    a1, a2, s1, s2 = (
        ag.AtomNode("a1"),
        ag.AtomNode("a2"),
        ag.SchemeNode(),
        ag.SchemeNode(),
    )
    g = new_draft(a1, a2, s1, s2, edges=((a1, s1), (s1, s2), (s2, s1), (a2, s2)))

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
        ag.Edge("a", "b", id="edge"),
        ag.Resource("r", id="resource"),
        ag.Participant("p", id="participant"),
        ag.Analyst("n", id="analyst"),
    ),
)
def test_entities_are_frozen(entity: Entity) -> None:
    original_id = entity.id

    with pytest.raises(AttributeError):
        setattr(entity, "id", "changed")  # noqa: B010

    with pytest.raises(AttributeError):
        delattr(entity, "id")

    assert entity.id == original_id
    assert deepcopy(entity) == entity


def test_networkx_attribute_names() -> None:
    atom, scheme = ag.AtomNode("a"), ag.SchemeNode()
    g = new_draft(atom, scheme, edges=((atom, scheme),))
    exported = ag.dump.networkx(
        g.freeze(),
        graph_attrs={"incoming_graph_data": lambda graph: graph.name},
        atom_attrs={"node_for_adding": lambda node: node.id},
        scheme_attrs={"node_for_adding": lambda node: node.id},
        edge_attrs={
            "u_of_edge": lambda edge: edge.source,
            "v_of_edge": lambda edge: edge.target,
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
    aif = ag.dump.aif(new_draft(a).freeze())

    assert aif["nodes"][0].get("timestamp") == "2020-01-01 10:00:00"


def test_protobuf_roundtrip():
    g, a, p, r = _sample()
    g.update_atom(a, userdata={"count": 1})
    g.major_claim = a
    analyst = ag.Analyst("Name", email="")
    g.add_analyst(analyst)
    graph = g.freeze()
    proto = ag.dump.protobuf(graph)
    loaded = ag.load.protobuf(proto)

    assert proto.library_version.startswith("arguebuf-python:")
    assert loaded.major_claim == a.id
    assert loaded.atom_nodes[a.id].participant == p.id
    assert loaded.atom_nodes[a.id].reference == ag.Reference("a", resource=r.id, offset=0)
    assert loaded.atom_nodes[a.id].metadata == graph.atom_nodes[a.id].metadata
    assert copy.deepcopy(graph).atom_nodes[a.id].userdata == {"count": 1}
    assert loaded.analysts[analyst.id].email == ""
    assert loaded.analysts[analyst.id].metadata == analyst.metadata


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
        ctx = Context(ag.Codecs())
        known = new_reference(ctx, "a", "r", 1, resources, "atom")
        missing = new_reference(ctx, "a", "", 1, resources, "atom")
        unknown = new_reference(ctx, "a", "x", 1, resources, "atom")

    assert known == ag.Reference("a", resource="r", offset=1)
    assert missing == ag.Reference("a", offset=1)
    assert unknown == ag.Reference("a")
    assert len(caplog.records) == 1


def test_removed_adjacency_does_not_accumulate() -> None:
    graph = ag.GraphDraft()
    graph.add_node(ag.AtomNode("", id="a"))
    graph.remove_node("a")
    baseline = len(graph._store._owned)

    for _ in range(1000):
        graph.add_node(ag.AtomNode("", id="a"))
        graph.remove_node("a")

    assert not graph.nodes
    assert len(graph._store._owned) == baseline


def test_batch_removals_and_links() -> None:
    g = new_draft(
        ag.AtomNode("Claim", id="c"),
        ag.AtomNode("Premise", id="p1"),
        ag.SchemeNode(ag.Support.EXPERT_OPINION, premise_descriptors=["p1"], id="s"),
    )
    g.add_resource(ag.Resource("Resource", id="r"))
    g.add_edge(ag.Edge("p1", "s", id="e1"))
    g.add_edge(ag.Edge("s", "c", id="e2"))

    with pytest.raises(ag.GraphError):
        g.remove_elements(["p1", "missing"])

    assert "p1" in g.nodes
    # the scheme is removed by the cascade before its turn, all removed ids are returned
    assert sorted(g.remove_elements(["p1", "s", "r"])) == ["e1", "e2", "p1", "r", "s"]
    assert list(g.nodes) == ["c"]
    assert not g.resources

    g.add_node(ag.AtomNode("", id="a"))

    assert (issue := g.check_link("a", "a")) is not None and issue.code == "self-loop"

    with pytest.raises(ag.GraphError):
        g.link("a", "a")

    assert g.check_link("a", "c") is None
    scheme = g.link("a", "c", scheme=ag.Attack.DEFAULT)
    assert scheme is not None and scheme.scheme is ag.Attack.DEFAULT
    assert list(g.outgoing_atom_nodes("a")) == [g.nodes["c"]]

    g.add_node(ag.AtomNode("", id="b"))

    assert (issue := g.check_link("a", scheme)) is not None and issue.code == "parallel-edge"
    assert g.link("b", scheme) is None
    assert list(g.premise_nodes(scheme)) == [g.nodes["a"], g.nodes["b"]]


def test_annotations() -> None:
    g = ag.GraphDraft()
    g.add_resource(ag.Resource("Resource", id="r"))

    for id, text, offset in (("a", "our", 3), ("b", "moved", 2), ("c", "Res", 0)):
        g.add_node(ag.AtomNode("", reference=ag.Reference(text, resource="r", offset=offset), id=id))

    assert [(item.node.id, item.start, item.end) for item in g.annotations("r")] == [
        ("c", 0, 3),
        ("a", 3, 6),
    ]


def test_init_with_elements():
    for cls in (ag.Graph, ag.GraphDraft):
        graph = cls(
            nodes=[ag.AtomNode("P", id="p"), ag.SchemeNode(id="s"), ag.AtomNode("C", id="c")],
            edges=[ag.Edge("p", "s"), ag.Edge("s", "c")],
            resources=[ag.Resource("Text", id="r")],
            analysts=[ag.Analyst("Name", id="n")],
            major_claim="c",
        )

        assert list(graph.nodes) == ["p", "s", "c"]
        assert graph.major_claim == "c"
        assert list(graph.resources) == ["r"]
        assert list(graph.analysts) == ["n"]

    with pytest.raises(ag.GraphError):
        ag.Graph(edges=[ag.Edge("p", "s")])


def test_remove_returns_ids():
    draft = ag.GraphDraft(
        resources=[ag.Resource("Text", id="r")],
        participants=[ag.Participant("Name", id="p")],
        analysts=[ag.Analyst("Name", id="a")],
        nodes=[ag.AtomNode("A", id="n1"), ag.SchemeNode(id="s")],
        edges=[ag.Edge("n1", "s", id="e")],
    )

    assert draft.remove_edge("e") == ["e"]
    assert draft.clean_resources() == ["r"]
    assert draft.clean_participants() == ["p"]
    assert draft.remove_elements(["a"]) == ["a"]

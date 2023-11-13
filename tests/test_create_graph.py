from pathlib import Path

import pytest
from arg_services.graph.v1 import graph_pb2

import arguebuf as ag


def generate_graph() -> ag.Graph:
    g = ag.Graph()
    a1 = ag.AtomNode("", id="a1")
    a2 = ag.AtomNode("", id="a2")
    a3 = ag.AtomNode("", id="a3")
    a4 = ag.AtomNode("", id="a4")
    s1 = ag.SchemeNode(id="s1")
    s2 = ag.SchemeNode(id="s2")

    g.add_edge(ag.Edge(a1, s1))
    g.add_edge(ag.Edge(s1, s2))
    g.add_edge(ag.Edge(s2, a4))
    g.add_edge(ag.Edge(a2, s1))
    g.add_edge(ag.Edge(a3, s2))

    return g


def test_strip_scheme_nodes():
    g = generate_graph()
    g.strip_scheme_nodes()

    assert len(g.nodes) == 4
    assert len(g.scheme_nodes) == 0
    assert len(g.edges) == 3


def test_remove_branch():
    g = generate_graph()
    g.remove_branch("s2")

    assert len(g.nodes) == 1
    assert len(g.edges) == 0


def test_sibling_nodes():
    g = ag.Graph()

    a1 = ag.AtomNode("", id="a1")
    a2 = ag.AtomNode("", id="a2")
    a3 = ag.AtomNode("", id="a3")
    a4 = ag.AtomNode("", id="a4")
    a5 = ag.AtomNode("", id="a5")
    a6 = ag.AtomNode("", id="a6")
    s1 = ag.SchemeNode(id="s1")
    s2 = ag.SchemeNode(id="s2")
    s3 = ag.SchemeNode(id="s3")
    s4 = ag.SchemeNode(id="s4")
    s5 = ag.SchemeNode(id="s5")

    g.add_edge(ag.Edge(a1, s1))
    g.add_edge(ag.Edge(a2, s2))
    g.add_edge(ag.Edge(s1, a3))
    g.add_edge(ag.Edge(s2, a3))
    g.add_edge(ag.Edge(a3, s3))
    g.add_edge(ag.Edge(s3, a4))
    g.add_edge(ag.Edge(s4, a4))
    g.add_edge(ag.Edge(a5, s4))
    g.add_edge(ag.Edge(s5, a5))
    g.add_edge(ag.Edge(a6, s5))

    siblings = g.sibling_node_distances(a2)

    assert len(siblings) == 3
    assert siblings[a1] == 2
    assert siblings[a6] == 4


def test_create_graph(tmp_path: Path):
    g = ag.Graph("Test")

    p1 = ag.Participant(
        name="Participant 1",
        username="Parti 1",
        email="Parti1@gmail.com",
        url="thesenuts",
        location="Trier",
        description="Hallo Welt!",
    )
    g.add_participant(p1)
    r1 = ag.Resource("Resource234")
    g.add_resource(r1)
    n1 = ag.AtomNode(
        text="Node 1",
        reference=ag.Reference(r1, 0, "Resource234"),
        participant=p1,
    )
    n2 = ag.SchemeNode(ag.Support.DEFAULT)
    n3 = ag.AtomNode("Node 3")
    n4 = ag.SchemeNode(ag.Support.DEFAULT)
    n5 = ag.AtomNode("Node 5")
    e12 = ag.Edge(n1, n2)
    e23 = ag.Edge(n2, n3)
    e34 = ag.Edge(n3, n4)
    e45 = ag.Edge(n4, n5)

    g.add_node(n1)
    g.add_edge(e12)
    g.add_edge(e23)
    g.add_edge(e34)
    g.add_edge(e45)

    assert e12.source == n1
    assert e12.target == n2
    assert e23.source == n2
    assert e23.target == n3
    assert e34.source == n3
    assert e34.target == n4
    assert e45.source == n4
    assert e45.target == n5

    assert len(g.incoming_nodes(n1)) == 0
    assert len(g.incoming_edges(n1)) == 0
    assert len(g.incoming_nodes(n3)) == 1
    assert len(g.incoming_edges(n3)) == 1
    assert len(g.incoming_edges(n5)) == 1
    assert len(g.incoming_edges(n5)) == 1

    assert len(g.outgoing_nodes(n1)) == 1
    assert len(g.outgoing_edges(n1)) == 1
    assert len(g.outgoing_nodes(n3)) == 1
    assert len(g.outgoing_edges(n3)) == 1
    assert len(g.outgoing_nodes(n5)) == 0
    assert len(g.outgoing_edges(n5)) == 0

    assert g.root_node == n5
    assert g.major_claim is None
    g.major_claim = n5
    assert g.major_claim == n5

    assert set(g.nodes.values()) == {n1, n2, n3, n4, n5}

    assert ag.traverse.node_distance(n1, n1, g.outgoing_nodes) == 0
    assert ag.traverse.node_distance(n1, n2, g.outgoing_nodes) == 1
    assert ag.traverse.node_distance(n1, n3, g.outgoing_nodes) == 2
    assert ag.traverse.node_distance(n1, n4, g.outgoing_nodes) == 3
    assert ag.traverse.node_distance(n1, n5, g.outgoing_nodes) == 4
    assert ag.traverse.node_distance(n2, n2, g.outgoing_nodes) == 0
    assert ag.traverse.node_distance(n3, n3, g.outgoing_nodes) == 0
    assert ag.traverse.node_distance(n4, n4, g.outgoing_nodes) == 0
    assert ag.traverse.node_distance(n5, n5, g.outgoing_nodes) == 0
    assert g.scheme_between(n1, n3) == n2
    assert g.outgoing_atom_nodes(n1) == {n3}

    assert len(g.resources) == 1
    r2 = ag.Resource(text="Resource", title="Resourca", source="Wikipedia")
    assert r2.plain_text == "Resource"
    g.add_resource(r2)
    g.add_resource(ag.Resource("Resource2"))
    assert len(g.resources) == 3
    assert len(g.atom_nodes) > 0
    assert len(g.scheme_nodes) > 0
    g.incoming_nodes(n3)
    g.incoming_atom_nodes(n2)
    g.outgoing_nodes(n3)
    g.outgoing_atom_nodes(n2)
    g.incoming_edges(n3)
    g.outgoing_edges(n3)

    g.remove_node(n4)
    g.add_node(n4)

    # e4 = "Hallo ich bin keine Kante"
    # g.add_edge(e4)

    with pytest.raises(ValueError):
        g.add_edge(e12)

    # r10 = "Hallo ich bin keine Quelle"
    # g.add_resource(r10)

    with pytest.raises(ValueError):
        g.add_resource(r2)

    # g.remove_resource(r10)
    g.remove_resource(r2)

    with pytest.raises(ValueError):
        g.remove_resource(r2)

    # p3 = "Hallo ich bin kein Teilnehmer"
    # g.add_participant(p3)

    with pytest.raises(ValueError):
        g.add_participant(p1)
    # g.remove_participant(p3)
    g.remove_participant(p1)

    with pytest.raises(ValueError):
        g.remove_participant(p1)

    assert len(g.participants) == 0

    assert isinstance(ag.dump.protobuf(g), graph_pb2.Graph)

    gc = ag.copy(g)

    assert len(g.nodes) == len(gc.nodes)

    ag.render.graphviz(ag.dump.graphviz(g), tmp_path / "test.pdf")

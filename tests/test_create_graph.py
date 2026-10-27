import arguebuf as ag

from .conftest import new_graph


def generate_graph() -> ag.Graph:
    a1, a2, a3, a4 = (ag.AtomNode("", id=f"a{i}") for i in range(1, 5))
    s1, s2, s3 = (ag.SchemeNode(id=f"s{i}") for i in range(1, 4))

    # s3 duplicates the path from a1 to a4
    return new_graph(
        *(a1, a2, a3, a4, s1, s2, s3),
        edges=((a1, s1), (s1, s2), (s2, a4), (a2, s1), (a3, s2), (a1, s3), (s3, a4)),
    )


def test_remove_scheme_nodes():
    g = generate_graph()
    g.remove_scheme_nodes()

    assert len(g.nodes) == 4
    assert len(g.scheme_nodes) == 0
    assert len(g.edges) == 3


def test_remove_branch():
    g = generate_graph()
    g.remove_branch("s2")

    assert g.nodes.keys() == {"a4", "s3"}
    assert len(g.edges) == 1


def test_sibling_nodes():
    a1, a2, a3, a4, a5, a6 = (ag.AtomNode("", id=f"a{i}") for i in range(1, 7))
    s1, s2, s3, s4, s5 = (ag.SchemeNode(id=f"s{i}") for i in range(1, 6))
    g = new_graph(
        *(a1, a2, a3, a4, a5, a6, s1, s2, s3, s4, s5),
        edges=(
            (a1, s1),
            (a2, s2),
            (s1, a3),
            (s2, a3),
            (a3, s3),
            (s3, a4),
            (s4, a4),
            (a5, s4),
            (s5, a5),
            (a6, s5),
        ),
    )

    assert g.sibling_node_distances(a2) == {}
    assert g.sibling_node_distances(a2, max_levels=None) == {a1: 2, a6: 4}
    assert g.sibling_nodes(a2, max_levels=2, node_type=ag.AtomNode) == {a1}


def test_create_graph() -> None:
    premise, scheme, claim = (
        ag.AtomNode("Premise"),
        ag.SchemeNode(),
        ag.AtomNode("Claim"),
    )
    graph = new_graph(
        premise, scheme, claim, edges=((premise, scheme), (scheme, claim))
    )

    assert graph.root_node is claim
    assert graph.leaf_nodes == {premise}
    assert graph.incoming_nodes(claim) == {scheme}
    assert not graph.incoming_edges(premise)
    assert graph.outgoing_nodes(premise) == {scheme}
    assert not graph.outgoing_edges(claim)
    assert graph.scheme_between(premise, claim) is scheme
    assert graph.outgoing_atom_nodes(premise) == {claim}
    assert graph.incoming_atom_nodes(claim) == {premise}

    for distance, node in enumerate((premise, scheme, claim)):
        assert (
            ag.traverse.node_distance(premise, node, graph.outgoing_nodes) == distance
        )

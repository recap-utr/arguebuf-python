import json
import multiprocessing
from typing import Any, Dict, List, Optional

import arguebuf as ag


def test_create_graph(shared_datadir):
    g = ag.Graph("Test")

    n1 = ag.AtomNode("Node 1")
    n2 = ag.SchemeNode(ag.SchemeType.SUPPORT)
    n3 = ag.AtomNode("Node 3")
    n4 = ag.SchemeNode(ag.SchemeType.SUPPORT)
    n5 = ag.AtomNode("Node 5")
    e12 = ag.Edge(n1, n2)
    e23 = ag.Edge(n2, n3)
    e34 = ag.Edge(n3, n4)
    e45 = ag.Edge(n4, n5)

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

    assert g.major_claim == n5

    assert set(g.nodes.values()) == set([n1, n2, n3, n4, n5])

    assert g.node_distance(n1, n1) == 0
    assert g.node_distance(n1, n2) == 1
    assert g.node_distance(n1, n3) == 2
    assert g.node_distance(n1, n4) == 3
    assert g.node_distance(n1, n5) == 4
    assert g.node_distance(n2, n2) == 0
    assert g.node_distance(n3, n3) == 0
    assert g.node_distance(n4, n4) == 0
    assert g.node_distance(n5, n5) == 0

    g.strip_snodes()

    assert len(g.nodes) == 3
    assert len(g.edges) == 2


def test_import_graphs(shared_datadir):
    brat_folder = shared_datadir / "brat"
    aif_folder = shared_datadir / "aif"
    ova_folder = shared_datadir / "ova"

    with multiprocessing.Pool() as pool:
        pool.map(_import_generic_graph, sorted(aif_folder.rglob("*.json")))
        pool.map(_import_generic_graph, sorted(ova_folder.rglob("*.json")))
        pool.map(_import_generic_graph, sorted(brat_folder.rglob("*.ann")))

        pool.map(_import_aif_graph, sorted(aif_folder.rglob("*.json")))


def _import_generic_graph(file):
    graph = ag.Graph.from_file(file)

    assert graph.to_dict(ag.GraphFormat.AIF) != {}
    assert graph.to_dict(ag.GraphFormat.ARGUEBUF) != {}
    assert graph.to_gv() is not None
    assert graph.to_nx() is not None


def _import_aif_graph(file):
    with file.open() as f:
        raw = json.load(f)

    graph = ag.Graph.from_file(file)
    export = graph.to_dict(ag.GraphFormat.AIF)

    assert export == raw, file
    # assert DeepDiff(raw, export, ignore_order=True) == {}, file

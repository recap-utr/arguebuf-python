import json
import multiprocessing
from typing import Any, Dict, List, Optional

import recap_argument_graph as ag
from deepdiff import DeepDiff

# TODO: Text length different
#  I-nodes sometimes have white instead of blue -> manually added ot the graph
#  Descriptors in node different than in edge (20130201_VBE_IT2)
_node_attrs = ("text_length", "color", "source", "descriptors", "is_check_worthy")
_graph_attrs = ("documentDate", "documentSource", "ovaVersion")


def test_create_graph(shared_datadir):
    g = ag.Graph("Test")

    n1 = ag.Node(g.keygen(), "Node 1", ag.NodeCategory.I)
    n2 = ag.Node(g.keygen(), "RA", ag.NodeCategory.RA)
    n3 = ag.Node(g.keygen(), "Node 3", ag.NodeCategory.I)
    e21 = ag.Edge(g.keygen(), n2, n1)
    e23 = ag.Edge(g.keygen(), n2, n3)

    g.add_edge(e21)
    g.add_edge(e23)

    assert n1.key == 1
    assert n2.key == 2
    assert n3.key == 3
    assert e21.key == 4
    assert e23.key == 5

    assert e21.start == n2
    assert e21.end == n1

    assert len(g.incoming_nodes[n1]) == 1
    assert len(g.incoming_edges[n1]) == 1
    assert len(g.incoming_nodes[n2]) == 1
    assert len(g.incoming_edges[n2]) == 1
    assert len(g.incoming_edges[n3]) == 0
    assert len(g.incoming_edges[n3]) == 0

    assert len(g.outgoing_nodes[n1]) == 0
    assert len(g.outgoing_edges[n1]) == 0
    assert len(g.outgoing_nodes[n2]) == 1
    assert len(g.outgoing_edges[n2]) == 1
    assert len(g.outgoing_nodes[n3]) == 1
    assert len(g.outgoing_edges[n3]) == 1

    assert g.major_claim == n1
    assert g.node_distance(n1, n1) == 0
    assert g.node_distance(n1, n2) == 1
    assert g.node_distance(n1, n3) == 2

    g.strip_snodes()

    assert len(g.nodes) == 2
    assert len(g.edges) == 1


def test_import_graphs(shared_datadir):
    folder = shared_datadir / "in" / "graph"

    with multiprocessing.Pool() as pool:
        pool.map(_import_json_graph, sorted(folder.rglob("*.json")))
        pool.map(_import_brat_graph, sorted(folder.rglob("*.ann")))


def _import_brat_graph(file):
    graph = ag.Graph.open(file)
    export = graph.to_dict()


def _import_json_graph(file):
    with file.open() as f:
        raw = json.load(f)

    graph = ag.Graph.open(file)
    export = graph.to_dict()

    if raw.get("analysis"):
        for attr in _graph_attrs:
            if not raw["analysis"].get(attr):
                del export["analysis"][attr]

    _clean_nodes(raw["nodes"])
    _clean_nodes(export["nodes"])
    _clean_edges(raw["edges"])
    _clean_edges(export["edges"])

    assert export == raw, file
    # assert DeepDiff(raw, export, ignore_order=True) == {}, file

    graph.to_gv()
    graph.to_nx()


def _clean_analysis(analysis: Optional[Dict[str, str]]) -> None:
    if analysis and "txt" in analysis:
        analysis["txt"] = analysis["txt"].replace(" hlcurrent", "")


def _clean_nodes(nodes: List[Dict[str, Any]]) -> None:
    for node in nodes:
        _clean_node(node)


def _clean_node(node: Optional[Dict[str, Any]]) -> None:
    for attr in _node_attrs:
        if node and node.get(attr) is not None:
            del node[attr]


def _clean_edges(edges: List[Dict[str, Any]]) -> None:
    for edge in edges:
        for node in (edge.get("from"), edge.get("to")):
            _clean_node(node)

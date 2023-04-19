import textwrap
import typing as t

from arguebuf.model import Graph
from arguebuf.model.edge import Edge
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.schemas.d2 import D2Graph, D2Edge, D2Node, D2Style


def dump_d2(
    graph: Graph,
    wrap_col: t.Optional[int] = None,
    atom_label: t.Optional[t.Callable[[AtomNode], str]] = None,
    scheme_label: t.Optional[t.Callable[[SchemeNode], str]] = None,
    max_nodes: t.Optional[int] = None,
) -> D2Graph:
    if len(graph.nodes) > (max_nodes or 1000):
        return None

    d2_graph = D2Graph(
        nodes=[],
        edges=[],
    )

    for node in graph._atom_nodes.values():
        _dump_node(
            node,
            d2_graph,
            major_claim=graph.major_claim == node,
            label_func=atom_label,
            wrap_col=wrap_col or 36,
        )

    for node in graph._scheme_nodes.values():
        _dump_node(
            node,
            d2_graph,
            label_func=scheme_label,
        )

    for edge in graph._edges.values():
        _dump_edge(edge, d2_graph)

    return d2_graph


def _dump_node(
    node: AtomNode,
    g: D2Graph,
    major_claim: bool,
    wrap_col: int,
    label_func: t.Optional[t.Callable[[AtomNode], str]] = None,
) -> None:
    label: str = label_func(node) if label_func else node.label

    if type(node) == AtomNode:
        color = node.color(major_claim)
    else:
        color = node.color(major_claim=False)
        label = textwrap.fill(label, wrap_col).strip()

    nodeStyle: D2Style = {
        "font_color": color.fg,
        "bold": "false",
        "stroke": color.border,
        "stroke_width": "2",
        "fill": color.bg,
    }

    n: D2Node = {
        "id": node.id,
        "label": label,
        "shape": "rectangle",
        "style": nodeStyle,
    }

    g["nodes"].append(n)


def _dump_edge(edge: Edge, g: D2Graph) -> None:
    """Submethod used to export Graph object g into D2 Graph format."""
    # g.add_connection(D2Connection.D2Connection(shape_1=edge.source.id, shape_2=edge.target.id))

    e: D2Edge = {
        "from_id": edge.source.id,
        "to_id": edge.target.id,
    }
    g["edges"].append(e)

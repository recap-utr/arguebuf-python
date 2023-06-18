import typing as t

from arguebuf.model import Graph
from arguebuf.model.edge import Edge
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.schemas.d2 import D2Edge, D2Graph, D2Node, D2Style


def dump_d2(
    graph: Graph,
    atom_label: t.Optional[t.Callable[[AtomNode], str]] = None,
    scheme_label: t.Optional[t.Callable[[SchemeNode], str]] = None,
    max_nodes: t.Optional[int] = None,
    monochrome: bool = False,
) -> t.Optional[D2Graph]:
    if len(graph.nodes) > (max_nodes or 1000):
        return None

    d2_graph = D2Graph(
        nodes=[],
        edges=[],
    )

    for node in graph.atom_nodes.values():
        _dump_atom(
            node,
            d2_graph,
            major_claim=graph.major_claim == node,
            label_func=atom_label,
            monochrome=monochrome,
        )

    for node in graph.scheme_nodes.values():
        _dump_scheme(
            node,
            d2_graph,
            label_func=scheme_label,
            major_claim=False,
            monochrome=monochrome,
        )

    for edge in graph.edges.values():
        _dump_edge(edge, d2_graph)

    return d2_graph


def _dump_atom(
    node: AtomNode,
    g: D2Graph,
    major_claim: bool,
    monochrome: bool,
    label_func: t.Optional[t.Callable[[AtomNode], str]] = None,
) -> None:
    label: str = label_func(node) if label_func else node.label
    color = node.color(major_claim, monochrome)

    nodeStyle: D2Style = D2Style(
        font_color=color.fg,
        stroke_width=2,
        bold=False,
        stroke=color.border,
        fill=color.bg,
    )

    g.nodes.append(
        D2Node(
            id=node.id,
            label=label.replace("\n", ""),
            shape="rectangle",
            style=nodeStyle,
        )
    )


def _dump_scheme(
    node: SchemeNode,
    g: D2Graph,
    major_claim: bool,
    monochrome: bool,
    label_func: t.Optional[t.Callable[[SchemeNode], str]] = None,
) -> None:
    label: str = label_func(node) if label_func else node.label
    color = node.color(False, monochrome)

    nodeStyle: D2Style = D2Style(
        font_color=color.fg,
        stroke_width=2,
        bold=False,
        stroke=color.border,
        fill=color.bg,
    )

    g.nodes.append(
        D2Node(
            id=node.id,
            label=label.replace("\n", ""),
            shape="rectangle",
            style=nodeStyle,
        )
    )


def _dump_edge(edge: Edge, g: D2Graph) -> None:
    """Submethod used to export Graph object g into D2 Graph format."""
    g.edges.append(D2Edge(from_id=edge.source.id, to_id=edge.target.id))

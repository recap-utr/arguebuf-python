import textwrap
import typing as t

from graphviz import Digraph

from arguebuf.model import Graph
from arguebuf.model.edge import Edge
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.schemas.graphviz import EdgeStyle, GraphvizGraph

try:
    from pygraphviz import AGraph

    def init_gv_graph(*args, **kwargs):  # type: ignore
        return AGraph(*args, **kwargs, directed=True)

    def add_gv_node(graph, *args, **kwargs):  # type: ignore
        return graph.add_node(*args, **kwargs)

    def add_gv_edge(graph, *args, **kwargs):  # type: ignore
        return graph.add_edge(*args, **kwargs)

except ModuleNotFoundError:

    def init_gv_graph(*args, **kwargs):  # type: ignore
        return Digraph(*args, **kwargs)

    def add_gv_node(graph, *args, **kwargs):  # type: ignore
        return graph.node(*args, **kwargs)

    def add_gv_edge(graph, *args, **kwargs):  # type: ignore
        return graph.edge(*args, **kwargs)


__all__ = ("dump_graphviz",)


def dump_graphviz(
    graph: Graph,
    nodesep: t.Optional[float] = None,
    ranksep: t.Optional[float] = None,
    wrap_col: t.Optional[int] = None,
    margin: t.Optional[t.Tuple[float, float]] = None,
    font_name: t.Optional[str] = None,
    font_size: t.Optional[float] = None,
    atom_label: t.Optional[t.Callable[[AtomNode], str]] = None,
    scheme_label: t.Optional[t.Callable[[SchemeNode], str]] = None,
    graph_attr: t.Optional[t.Mapping[str, str]] = None,
    node_attr: t.Optional[t.Mapping[str, str]] = None,
    edge_attr: t.Optional[t.Mapping[str, str]] = None,
    edge_style: t.Optional[EdgeStyle] = None,
    max_nodes: t.Optional[int] = None,
    monochrome: bool = False,
) -> t.Optional[GraphvizGraph]:
    """Transform a Graph instance into an instance of GraphViz directed graph. Make sure that a GraphViz Executable path is set on your machine for visualization. Refer to the GraphViz library for additional information."""

    if len(graph.nodes) > (max_nodes or 1000):
        return None

    def gv_margin(x):
        return f"{x[0]},{x[1]}"

    if not graph_attr:
        graph_attr = {}

    if not node_attr:
        node_attr = {}

    if not edge_attr:
        edge_attr = {}

    gv_graph = init_gv_graph(
        name=str(graph.name),
        strict=True,
    )
    # NameError

    gv_graph.node_attr.update(
        {
            "fontname": font_name or "Arial",
            "fontsize": str(font_size or 11),
            "margin": gv_margin(margin or (0.15, 0.1)),
            "style": "rounded,filled",
            "shape": "box",
            "width": "0",
            "height": "0",
            **node_attr,
        }
    )
    gv_graph.edge_attr.update(
        {"color": "#000000" if monochrome else "#9E9E9E", **edge_attr}
    )
    gv_graph.graph_attr.update(
        {
            "rankdir": "BT",
            "margin": "0",
            "nodesep": str(nodesep or 0.25),
            "ranksep": str(ranksep or 0.5),
            "overlap": "false",
            "splines": edge_style.value if edge_style else EdgeStyle.STEP.value,
            **graph_attr,
        }
    )

    for node in graph.atom_nodes.values():
        _dump_atom(
            node,
            gv_graph,
            graph.major_claim == node,
            label_func=atom_label,
            wrap_col=wrap_col or 36,
            monochrome=monochrome,
        )

    for node in graph.scheme_nodes.values():
        _dump_scheme(node, gv_graph, label_func=scheme_label, monochrome=monochrome)

    for edge in graph.edges.values():
        _dump_edge(edge, gv_graph)

    return gv_graph


def _dump_atom(
    node: AtomNode,
    g: GraphvizGraph,
    major_claim: bool,
    wrap_col: int,
    monochrome: bool,
    label_func: t.Optional[t.Callable[[AtomNode], str]] = None,
) -> None:
    """Submethod used to export Graph object g into GV Graph format."""
    color = node.color(major_claim, monochrome)
    label = label_func(node) if label_func else node.label

    # TODO: Improve wrapping
    # https://stackoverflow.com/a/26538082/7626878
    add_gv_node(
        g,
        node.id,
        label=textwrap.fill(label, wrap_col).strip(),
        fontcolor=color.fg,
        fillcolor=color.bg,
        color=color.border,
        root=str(major_claim),
    )


def _dump_scheme(
    node: SchemeNode,
    g: GraphvizGraph,
    monochrome: bool,
    label_func: t.Optional[t.Callable[[SchemeNode], str]] = None,
) -> None:
    """Submethod used to export Graph object g into GV Graph format."""

    color = node.color(False, monochrome)
    label = label_func(node) if label_func else node.label

    add_gv_node(
        g,
        node.id,
        label=label,
        fontcolor=color.fg,
        fillcolor=color.bg,
        color=color.border,
    )


def _dump_edge(edge: Edge, g: GraphvizGraph) -> None:
    """Submethod used to export Graph object g into GV Graph format."""
    add_gv_edge(
        g,
        edge.source.id,
        edge.target.id,
    )

import textwrap
import typing as t
from enum import Enum
from pathlib import Path

from graphviz import Digraph

from arguebuf.models.edge import Edge
from arguebuf.models.graph import Graph
from arguebuf.models.node import AtomNode, Node, SchemeNode

try:
    from pygraphviz import AGraph

    init_gv = lambda *args, **kwargs: AGraph(*args, **kwargs, directed=True)
    add_gv_node = lambda graph, *args, **kwargs: graph.add_node(*args, **kwargs)
    add_gv_edge = lambda graph, *args, **kwargs: graph.add_edge(*args, **kwargs)
except ModuleNotFoundError:
    init_gv = lambda *args, **kwargs: Digraph(*args, **kwargs)
    add_gv_node = lambda graph, *args, **kwargs: graph.node(*args, **kwargs)
    add_gv_edge = lambda graph, *args, **kwargs: graph.edge(*args, **kwargs)

GraphvizGraph = t.Union[Digraph, t.Any]


class EdgeStyle(Enum):
    BEZIER = "curved"
    STRAIGHT = "line"
    STEP = "ortho"


def export(
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
) -> t.Optional[GraphvizGraph]:
    """Transform a Graph instance into an instance of GraphViz directed graph. Make sure that a GraphViz Executable path is set on your machine for visualization. Refer to the GraphViz library for additional information."""

    if len(graph.nodes) > (max_nodes or 1000):
        return None

    gv_margin: t.Callable[[t.Tuple[float, float]], str] = lambda x: f"{x[0]},{x[1]}"

    if not graph_attr:
        graph_attr = {}

    if not node_attr:
        node_attr = {}

    if not edge_attr:
        edge_attr = {}

    gv_graph = AGraph(
        directed=True,
        name=str(graph.name),
        strict=True,
        # format=format or "pdf",
        # engine=engine or "dot",
    )

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
    gv_graph.edge_attr.update({"color": "#9E9E9E", **edge_attr})
    gv_graph.graph_attr.update(
        {
            # "bgcolor": "#000000",
            "rankdir": "BT",
            "margin": "0",
            "nodesep": str(nodesep or 0.25),
            "ranksep": str(ranksep or 0.5),
            "overlap": "false",
            "splines": edge_style.value if edge_style else EdgeStyle.STEP.value,
            **graph_attr,
        }
    )

    for node in graph._atom_nodes.values():
        _atom_to_gv(
            node,
            gv_graph,
            graph.major_claim == node,
            label_func=atom_label,
            wrap_col=wrap_col or 36,
        )

    for node in graph._scheme_nodes.values():
        _scheme_to_gv(
            node,
            gv_graph,
            label_func=scheme_label,
        )

    for edge in graph._edges.values():
        _edge_to_gv(edge, gv_graph)

    return gv_graph


def _atom_to_gv(
    node: AtomNode,
    g: GraphvizGraph,
    major_claim: bool,
    wrap_col: int,
    label_func: t.Optional[t.Callable[[AtomNode], str]] = None,
) -> None:
    """Submethod used to export Graph object g into GV Graph format."""
    color = node.color(major_claim)
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


def _scheme_to_gv(
    node: SchemeNode,
    g: GraphvizGraph,
    label_func: t.Optional[t.Callable[[SchemeNode], str]] = None,
) -> None:
    """Submethod used to export Graph object g into GV Graph format."""

    color = node.color(major_claim=False)
    label = label_func(node) if label_func else node.label

    add_gv_node(
        g,
        node.id,
        label=label,
        fontcolor=color.fg,
        fillcolor=color.bg,
        color=color.border,
    )


def _edge_to_gv(edge: Edge, g: GraphvizGraph) -> None:
    """Submethod used to export Graph object g into GV Graph format."""
    add_gv_edge(
        g,
        edge.source.id,
        edge.target.id,
    )


def render(
    graph: t.Optional[GraphvizGraph],
    path: t.Union[Path, str],
    prog: t.Literal["neato", "dot", "twopi", "circo", "fdp", "nop"] = "dot",
) -> None:
    """Visualize a Graph instance using a GraphViz backend. Make sure that a GraphViz Executable path is set on your machine for visualization."""
    if isinstance(path, str):
        path = Path(path)

    if graph is None:
        pass
    elif isinstance(graph, Graph):
        raise ValueError(
            "This method expects a graph in the 'DOT' format."
            "Please use 'graph.to_gv()' to convert your argument graph to the 'DOT' format."
        )
    elif isinstance(graph, Digraph):
        graph.render(outfile=path, renderer=prog)
    else:
        graph.draw(path=path, prog=prog)

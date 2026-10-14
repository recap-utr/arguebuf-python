import textwrap
from collections.abc import Callable, Mapping

from pygraphviz import AGraph

from arguebuf.model import Graph
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.schemas.graphviz import EdgeStyle

__all__ = ("dump_graphviz",)


def dump_graphviz[T](
    graph: Graph[T],
    nodesep: float = 0.25,
    ranksep: float = 0.5,
    wrap_col: int = 36,
    margin: tuple[float, float] = (0.15, 0.1),
    font_name: str = "Arial",
    font_size: float = 11,
    atom_label: Callable[[AtomNode[T]], str] | None = None,
    scheme_label: Callable[[SchemeNode], str] | None = None,
    graph_attr: Mapping[str, str] | None = None,
    node_attr: Mapping[str, str] | None = None,
    edge_attr: Mapping[str, str] | None = None,
    edge_style: EdgeStyle = EdgeStyle.STEP,
    max_nodes: int = 1000,
    monochrome: bool = False,
) -> AGraph | None:
    """Transform a graph into a directed GraphViz graph, returns `None` if it is too large."""
    if len(graph.nodes) > max_nodes:
        return None

    margin_x, margin_y = margin
    gv_graph = AGraph(name=graph.name, strict=True, directed=True)
    gv_graph.node_attr.update(
        {
            "fontname": font_name,
            "fontsize": str(font_size),
            "margin": f"{margin_x},{margin_y}",
            "style": "rounded,filled",
            "shape": "box",
            "width": "0",
            "height": "0",
            **(node_attr or {}),
        }
    )
    gv_graph.edge_attr.update(
        {"color": "#000000" if monochrome else "#9E9E9E", **(edge_attr or {})}
    )
    gv_graph.graph_attr.update(
        {
            "rankdir": "BT",
            "margin": "0",
            "nodesep": str(nodesep),
            "ranksep": str(ranksep),
            "overlap": "false",
            "splines": edge_style,
            **(graph_attr or {}),
        }
    )

    for node in graph.atom_nodes.values():
        major_claim = graph.major_claim == node
        color = node.color(major_claim, monochrome)
        label = atom_label(node) if atom_label else node.label

        # TODO: Improve wrapping
        # https://stackoverflow.com/a/26538082/7626878
        gv_graph.add_node(
            node.id,
            label=textwrap.fill(label, wrap_col).strip(),
            fontcolor=color.fg,
            fillcolor=color.bg,
            color=color.border,
            root=str(major_claim),
        )

    for node in graph.scheme_nodes.values():
        color = node.color(False, monochrome)
        gv_graph.add_node(
            node.id,
            label=scheme_label(node) if scheme_label else node.label,
            fontcolor=color.fg,
            fillcolor=color.bg,
            color=color.border,
        )

    for edge in graph.edges.values():
        gv_graph.add_edge(edge.source.id, edge.target.id)

    return gv_graph

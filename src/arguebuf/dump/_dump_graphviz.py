import textwrap
from collections.abc import Callable, Mapping
from typing import Literal, TypeAlias

from pygraphviz import AGraph

from arguebuf.model import GraphView
from arguebuf.model.node import AtomNode, SchemeNode

__all__ = ("EdgeStyle", "dump_graphviz")

# a classic alias, since typer cannot read `type` aliases
EdgeStyle: TypeAlias = Literal["curved", "line", "ortho"]  # noqa: UP040
"""GraphViz `splines` attribute that determines the shape of edges."""


def dump_graphviz[A, S, E, R, P, N, G](
    graph: GraphView[A, S, E, R, P, N, G],
    *,
    nodesep: float = 0.25,
    ranksep: float = 0.5,
    wrap_col: int = 36,
    margin: tuple[float, float] = (0.15, 0.1),
    font_name: str = "Arial",
    font_size: float = 11,
    atom_label: Callable[[AtomNode[A]], str] | None = None,
    scheme_label: Callable[[SchemeNode[S]], str] | None = None,
    graph_attr: Mapping[str, str] | None = None,
    node_attr: Mapping[str, str] | None = None,
    edge_attr: Mapping[str, str] | None = None,
    edge_style: EdgeStyle = "ortho",
    max_nodes: int = 1000,
    monochrome: bool = False,
    scheme_nodes: bool = True,
) -> AGraph | None:
    """Transform a graph into a directed GraphViz graph, returns `None` if it is too large.

    Without `scheme_nodes`, atom nodes are connected directly (see `Graph.atom_relations`)
    by edges colored like the scheme node between them.
    Atom labels are wrapped at whitespace after `wrap_col` characters.
    Backslashes and double quotes in labels are escaped,
    so they are rendered literally instead of being interpreted by GraphViz.
    """
    if len(graph.nodes) > max_nodes:
        return None

    margin_x, margin_y = margin
    gv_graph = AGraph(name=graph.name or "", strict=True, directed=True)
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
        major_claim = graph.major_claim == node.id
        color = node.color(major_claim=major_claim, monochrome=monochrome)
        label = atom_label(node) if atom_label else node.label
        gv_graph.add_node(
            node.id,
            label=_escape(
                textwrap.fill(label, wrap_col, break_on_hyphens=False).strip()
            ),
            fontcolor=color.fg,
            fillcolor=color.bg,
            color=color.border,
            root=str(major_claim).lower(),
        )

    if not scheme_nodes:
        for relation in graph.atom_relations():
            gv_graph.add_edge(
                relation.source.id,
                relation.target.id,
                color=relation.scheme.color(monochrome=monochrome).bg,
            )

        return gv_graph

    for node in graph.scheme_nodes.values():
        color = node.color(monochrome=monochrome)
        gv_graph.add_node(
            node.id,
            label=_escape(scheme_label(node) if scheme_label else node.label),
            fontcolor=color.fg,
            fillcolor=color.bg,
            color=color.border,
        )

    for edge in graph.edges.values():
        gv_graph.add_edge(edge.source, edge.target)

    return gv_graph


def _escape(label: str) -> str:
    # graphviz only escapes double quotes, a trailing backslash would escape the closing quote
    return label.replace("\\", "\\\\").replace('"', '\\"')

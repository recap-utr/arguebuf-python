from collections.abc import Callable

from arguebuf.model import Graph
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.schemas.d2 import D2Edge, D2Graph, D2Node, D2Style

__all__ = ("dump_d2",)


def dump_d2[A, S, E, G, R, P, N](
    graph: Graph[A, S, E, G, R, P, N],
    atom_label: Callable[[AtomNode[A]], str] | None = None,
    scheme_label: Callable[[SchemeNode[S]], str] | None = None,
    max_nodes: int = 1000,
    monochrome: bool = False,
    scheme_nodes: bool = True,
) -> D2Graph | None:
    """Transform a graph into the D2 diagram language, returns `None` if it is too large.

    Without `scheme_nodes`, atom nodes are connected directly (see `Graph.atom_relations`)
    by edges colored like the scheme node between them.
    """
    if len(graph.nodes) > max_nodes:
        return None

    if not scheme_nodes:
        return D2Graph(
            nodes=[
                _dump_node(
                    node,
                    atom_label(node) if atom_label else node.label,
                    graph.major_claim == node.id,
                    monochrome,
                )
                for node in graph.atom_nodes.values()
            ],
            edges=[
                D2Edge(
                    from_id=relation.source.id,
                    to_id=relation.target.id,
                    stroke=relation.scheme.color(False, monochrome).bg,
                )
                for relation in graph.atom_relations()
            ],
        )

    return D2Graph(
        nodes=[
            *(
                _dump_node(
                    node,
                    atom_label(node) if atom_label else node.label,
                    graph.major_claim == node.id,
                    monochrome,
                )
                for node in graph.atom_nodes.values()
            ),
            *(
                _dump_node(
                    node,
                    scheme_label(node) if scheme_label else node.label,
                    False,
                    monochrome,
                )
                for node in graph.scheme_nodes.values()
            ),
        ],
        edges=[
            D2Edge(from_id=edge.source, to_id=edge.target)
            for edge in graph.edges.values()
        ],
    )


def _dump_node(
    node: AbstractNode, label: str, major_claim: bool, monochrome: bool
) -> D2Node:
    color = node.color(major_claim, monochrome)

    return D2Node(
        id=node.id,
        label=label.replace("\n", " "),
        shape="rectangle",
        style=D2Style(
            font_color=color.fg,
            bold=False,
            stroke=color.border,
            stroke_width=2,
            fill=color.bg,
        ),
    )

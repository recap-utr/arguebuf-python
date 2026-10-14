from collections.abc import Callable

from arguebuf.model import Graph
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.schemas.d2 import D2Edge, D2Graph, D2Node, D2Style

__all__ = ("dump_d2",)


def dump_d2[T](
    graph: Graph[T],
    atom_label: Callable[[AtomNode[T]], str] | None = None,
    scheme_label: Callable[[SchemeNode], str] | None = None,
    max_nodes: int = 1000,
    monochrome: bool = False,
) -> D2Graph | None:
    """Transform a graph into the D2 diagram language, returns `None` if it is too large."""
    if len(graph.nodes) > max_nodes:
        return None

    return D2Graph(
        nodes=[
            *(
                _dump_node(
                    node,
                    atom_label(node) if atom_label else node.label,
                    graph.major_claim == node,
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
            D2Edge(from_id=edge.source.id, to_id=edge.target.id)
            for edge in graph.edges.values()
        ],
    )


def _dump_node(
    node: AbstractNode, label: str, major_claim: bool, monochrome: bool
) -> D2Node:
    color = node.color(major_claim, monochrome)

    return D2Node(
        id=node.id,
        label=label.replace("\n", ""),
        shape="rectangle",
        style=D2Style(
            font_color=color.fg,
            bold=False,
            stroke=color.border,
            stroke_width=2,
            fill=color.bg,
        ),
    )

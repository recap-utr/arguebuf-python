from collections.abc import Iterable

import arguebuf as ag


def new_graph(
    *nodes: ag.AtomOrSchemeNode,
    edges: Iterable[tuple[ag.AbstractNode, ag.AbstractNode]] = (),
) -> ag.Graph:
    """Create a graph from nodes and (source, target) pairs."""
    g = ag.Graph()

    for node in nodes:
        g.add_node(node)

    for source, target in edges:
        g.add_edge(ag.Edge(source, target))

    return g

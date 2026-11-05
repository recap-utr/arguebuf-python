from collections.abc import Iterable

import arguebuf as ag


def new_draft(
    *nodes: ag.Node,
    edges: Iterable[tuple[ag.AbstractNode, ag.AbstractNode]] = (),
) -> ag.GraphDraft:
    """Create a draft from nodes and (source, target) pairs."""
    g = ag.GraphDraft()

    for node in nodes:
        g.add_node(node)

    for source, target in edges:
        g.add_edge(ag.Edge(source.id, target.id))

    return g

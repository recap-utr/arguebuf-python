import copy as _copy

from arguebuf.model import Graph

__all__ = ("copy",)


def copy[A, S, E, G, R, P, N](
    graph: Graph[A, S, E, G, R, P, N],
) -> Graph[A, S, E, G, R, P, N]:
    """Create a lossless deep copy of a graph, including in-memory userdata.

    The userdata is copied with `copy.deepcopy`, its codecs are not used.

    Examples:
        >>> from arguebuf import AtomNode
        >>> g = Graph()
        >>> g.add_node(AtomNode("Claim", userdata={"count": 1}))
        >>> gc = copy(g)
        >>> gc.name == g.name and gc is not g
        True
        >>> next(iter(gc.atom_nodes.values())).userdata
        {'count': 1}
    """
    return _copy.deepcopy(graph)

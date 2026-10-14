from collections import deque
from collections.abc import Callable, Iterable
from collections.abc import Set as AbstractSet

from arguebuf.model import AbstractNode

__all__ = ("bfs", "dfs", "node_distance")


# https://eddmann.com/posts/depth-first-search-and-breadth-first-search-in-python/
def dfs[N: AbstractNode](
    start: N,
    connections: Callable[[N], AbstractSet[N]],
    include_start: bool = True,
) -> list[N]:
    """Visit all nodes reachable from `start` in depth-first order."""
    return _traverse(start, connections, include_start, deque.pop)


def bfs[N: AbstractNode](
    start: N,
    connections: Callable[[N], AbstractSet[N]],
    include_start: bool = True,
) -> list[N]:
    """Visit all nodes reachable from `start` in breadth-first order."""
    return _traverse(start, connections, include_start, deque.popleft)


def _traverse[N: AbstractNode](
    start: N,
    connections: Callable[[N], AbstractSet[N]],
    include_start: bool,
    pop: Callable[[deque[N]], N],
) -> list[N]:
    # a dict preserves the insertion order, a set does not
    visited: dict[N, None] = {}
    pending: deque[N] = deque([start])

    while pending:
        node = pop(pending)

        if node not in visited:
            visited[node] = None
            pending.extend(connections(node) - visited.keys())

    if not include_start:
        del visited[start]

    return list(visited)


def node_distance[N: AbstractNode](
    start_node: N,
    end_node: N,
    connections: Callable[[N], Iterable[N]],
    max_distance: int | None = None,
    directed: bool = True,
) -> int | None:
    """Get the distance between `start_node` and `end_node` in the graph.

    Args:
        start_node: Node object that is part of the graph.
        end_node: Node object that is part of the graph.
        connections: Callable containing links between nodes
            (e.g., `graph.incoming_atom_nodes` and `graph.outgoing_nodes`)
        max_distance: Only search for nodes having at most a distance of this argument.
            Especially helpful when dealing with large graphs where shorts paths are searched for.
        directed: If `False`, also search for the direction `end_node` -> `start_node`.

    Returns:
        Number of nodes in between or `None` if no path between

    Examples:
        >>> from arguebuf import Graph, AtomNode, SchemeNode, Edge
        >>> g = Graph()
        >>> n1 = AtomNode("Premise")
        >>> n2 = SchemeNode()
        >>> n3 = AtomNode("Claim")
        >>> g.add_edge(Edge(n1, n2))
        >>> g.add_edge(Edge(n2, n3))
        >>> node_distance(n1, n3, g.outgoing_nodes)
        2
        >>> node_distance(n3, n1, g.outgoing_nodes)
    """

    if start_node == end_node:
        return 0

    dist = _directed_node_distance(start_node, end_node, connections, max_distance)

    if dist is None and not directed:
        dist = _directed_node_distance(end_node, start_node, connections, max_distance)

    return dist


def _directed_node_distance[N: AbstractNode](
    start_node: N,
    end_node: N,
    connections: Callable[[N], Iterable[N]],
    max_distance: int | None,
) -> int | None:
    """Breadth-first search for the shortest distance."""
    visited = {start_node}
    pending: deque[tuple[N, int]] = deque([(start_node, 0)])

    while pending:
        node, distance = pending.popleft()

        if max_distance is not None and distance >= max_distance:
            continue

        for neighbor in connections(node):
            if neighbor == end_node:
                return distance + 1

            if neighbor not in visited:
                visited.add(neighbor)
                pending.append((neighbor, distance + 1))

    return None

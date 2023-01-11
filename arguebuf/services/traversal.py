import typing as t

from arguebuf.models.node import AtomNode, Node, SchemeNode

_Node = t.TypeVar("_Node", AtomNode, SchemeNode, Node)

# https://eddmann.com/posts/depth-first-search-and-breadth-first-search-in-python/
def dfs(
    start: _Node,
    connections: t.Callable[[Node], t.AbstractSet[_Node]],
    include_start: bool = True,
) -> t.List[_Node]:
    # Need to use a dict since a set does not preserve order
    visited: dict[_Node, None] = {}
    stack: list[_Node] = [start]

    while stack:
        node = stack.pop()

        if node not in visited:
            visited[node] = None
            stack.extend(set(connections(node)) - visited.keys())

    if include_start:
        return list(visited.keys())

    return [node for node in visited if node != start]


def bfs(
    start: _Node,
    connections: t.Callable[[Node], t.AbstractSet[_Node]],
    include_start: bool = True,
) -> t.List[_Node]:
    # Need to use a dict since a set does not preserve order
    visited: dict[_Node, None] = {}
    queue: list[_Node] = [start]

    while queue:
        node = queue.pop(0)

        if node not in visited:
            visited[node] = None
            queue.extend(set(connections(node)) - visited.keys())

    if include_start:
        return list(visited.keys())

    return [node for node in visited if node != start]


def node_distance(
    node1: Node,
    node2: Node,
    connections: t.Callable[[Node], t.Iterable[Node]],
    max_distance: t.Optional[int],
) -> t.Optional[int]:
    expansion: t.List[t.Tuple[Node, int]] = [(n, 1) for n in connections(node1)]

    while len(expansion) > 0:
        candidate, distance = expansion.pop()

        if max_distance is not None and distance > max_distance:
            continue
        elif candidate == node2:
            return distance
        else:
            expansion.extend((n, distance + 1) for n in connections(candidate))

    return None

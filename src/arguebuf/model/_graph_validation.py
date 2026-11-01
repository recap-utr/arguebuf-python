"""Rules that elements must satisfy to be added to a graph."""

from collections.abc import Mapping

from arguebuf.model._graph_store import GraphStore
from arguebuf.model.edge import Edge
from arguebuf.model.issue import GraphError, Issue, fail, issue
from arguebuf.model.node import AbstractNode, AtomNode
from arguebuf.model.utils import Entity, id_of

__all__ = ("edge_issue", "get", "vacate", "validate_edge", "validate_node")


def vacate(store: Mapping[str, Entity], value: Entity, kind: str) -> None:
    """The id of `value` must not be taken in `store`."""
    if value.id in store:
        fail("duplicate-id", f"{kind} '{value.id}' already exists.", [value.id])


def get[V: Entity](store: Mapping[str, V], value: str | Entity, kind: str) -> V:
    """The element of `store` with the id of `value`, which must exist."""
    id = id_of(value)

    if id not in store:
        fail("unknown-element", f"{kind} '{id}' does not exist.", [id])

    return store[id]


def validate_node[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], node: AbstractNode
) -> None:
    """The participant and the resource of the reference of an atom node must be part of the graph."""
    if not isinstance(node, AtomNode):
        return

    if node.participant and node.participant not in store.participants:
        fail(
            "unknown-element",
            f"Participant '{node.participant}' of node '{node.id}' does not exist.",
            [node.id, node.participant],
        )

    if (
        node.reference
        and (resource := node.reference.resource)
        and resource not in store.resources
    ):
        fail(
            "unknown-element",
            f"Resource '{resource}' of node '{node.id}' does not exist.",
            [node.id, resource],
        )


def edge_issue[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N],
    source: str,
    target: str,
    id: str | None = None,
) -> Issue | None:
    """The issue that prevents an edge from the source to the target, if any.

    Both must be part of the graph,
    self-loops, edges between two atom nodes, and parallel edges are rejected.

    Args:
        store: Store of the graph the edge would be added to.
        source: Id of the node the edge starts at.
        target: Id of the node the edge ends at.
        id: Id of the edge, the elements of the issue start with it if given.
    """
    prefix = () if id is None else (id,)

    for node in (source, target):
        if node not in store.nodes:
            return issue(
                "unknown-element", f"Node '{node}' does not exist.", (*prefix, node)
            )

    if source == target:
        return issue(
            "self-loop",
            f"Node '{source}' cannot be connected to itself.",
            (*prefix, source),
        )

    if source in store.atom_nodes and target in store.atom_nodes:
        return issue(
            "atom-edge",
            f"The atoms '{source}' and '{target}' cannot be connected directly.",
            (*prefix, source, target),
        )

    if any(store.edges[edge].target == target for edge in store.outgoing[source]):
        return issue(
            "parallel-edge",
            f"Nodes '{source}' and '{target}' are already connected.",
            (*prefix, source, target),
        )

    return None


def validate_edge[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], edge: Edge[E]
) -> None:
    """Raise the issue that prevents the edge, see `edge_issue`."""
    if (found := edge_issue(store, edge.source, edge.target, edge.id)) is not None:
        raise GraphError(found)

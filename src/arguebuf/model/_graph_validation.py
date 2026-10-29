"""Rules that elements must satisfy to be added to a graph."""

from collections.abc import Mapping

from arguebuf.model._graph_store import GraphStore
from arguebuf.model.edge import Edge
from arguebuf.model.issue import fail
from arguebuf.model.node import AbstractNode, AtomNode
from arguebuf.model.utils import Entity, id_of

__all__ = ("get", "vacate", "validate_edge", "validate_node")


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


def validate_edge[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], edge: Edge[E]
) -> None:
    """The source and target must be part of the graph.

    Self-loops, edges between two atom nodes, and parallel edges are rejected.
    """
    source, target = edge.source, edge.target

    for node in (source, target):
        if node not in store.nodes:
            fail(
                "unknown-element",
                f"Node '{node}' of edge '{edge.id}' does not exist.",
                [edge.id, node],
            )

    if source == target:
        fail(
            "self-loop",
            f"Edge '{edge.id}' connects node '{source}' to itself.",
            [edge.id, source],
        )

    if source in store.atom_nodes and target in store.atom_nodes:
        fail(
            "atom-edge",
            f"Edge '{edge.id}' directly connects the atoms '{source}' and '{target}'.",
            [edge.id, source, target],
        )

    if any(store.edges[id].target == target for id in store.outgoing[source]):
        fail(
            "parallel-edge",
            f"Nodes '{source}' and '{target}' are already connected.",
            [edge.id, source, target],
        )

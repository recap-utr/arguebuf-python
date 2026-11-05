import copy
import dataclasses
import weakref
from collections.abc import Mapping
from typing import Self, assert_never

from arguebuf._dt import now
from arguebuf.model.analyst import Analyst
from arguebuf.model.edge import Edge
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AbstractNode, AtomNode, AtomOrSchemeNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.resource import Resource

__all__ = ("GraphStore", "touched")


class _Container[V](dict[str, V]):
    """Container that a store can own without keeping it alive after removing it."""

    __slots__ = ("__weakref__",)


def touched(metadata: Metadata) -> Metadata:
    """The metadata of an element that changes now."""
    return dataclasses.replace(metadata, updated=now())


class GraphStore[A, S, E, R, P, N]:
    """Containers of a graph with copy on write.

    A fork shares all containers and clones each one before writing to it first.
    A forked store is not written anymore, since it belongs to an immutable graph.
    The store keeps the adjacency of nodes and edges consistent, but does not validate elements.
    Readers must not change the containers, writers use the methods of the store.
    """

    __slots__ = (
        "_owned",
        "analysts",
        "atom_nodes",
        "edges",
        "incoming",
        "major_claim",
        "nodes",
        "outgoing",
        "participants",
        "resources",
        "scheme_nodes",
    )

    def __init__(self) -> None:
        self.nodes: dict[str, AtomOrSchemeNode[A, S]] = {}
        self.atom_nodes: dict[str, AtomNode[A]] = {}
        self.scheme_nodes: dict[str, SchemeNode[S]] = {}
        self.edges: dict[str, Edge[E]] = {}
        # ids of the edges of each node, so that updating an edge only replaces it in `edges`
        self.incoming: dict[str, dict[str, None]] = {}
        self.outgoing: dict[str, dict[str, None]] = {}
        self.resources: dict[str, Resource[R]] = {}
        self.participants: dict[str, Participant[P]] = {}
        self.analysts: dict[str, Analyst[N]] = {}
        self.major_claim: str | None = None
        # containers that only this store references by their id, the others are shared with forks
        # (dicts cannot be weakly referenced, so the values keep them alive and their ids unique)
        # dictionaries are unhashable, so they are found by id and compared by identity
        self._owned: weakref.WeakValueDictionary[int, Mapping[str, object]] = (
            weakref.WeakValueDictionary()
        )

    def fork(self) -> Self:
        """A store sharing all containers with this one, which it clones before writing.

        This store is left unchanged and must not be written afterwards,
        since it still treats the shared containers as its own.
        """
        fork = copy.copy(self)
        fork._owned = weakref.WeakValueDictionary()

        return fork

    def _own[V](self, container: dict[str, V]) -> dict[str, V]:
        """The container for writing, cloned first if it is shared with a fork."""
        if self._owned.get(id(container)) is container:
            return container

        clone = _Container(container)
        self._owned[id(clone)] = clone

        return clone

    def own_edges(self) -> dict[str, Edge[E]]:
        self.edges = self._own(self.edges)

        return self.edges

    def own_resources(self) -> dict[str, Resource[R]]:
        self.resources = self._own(self.resources)

        return self.resources

    def own_participants(self) -> dict[str, Participant[P]]:
        self.participants = self._own(self.participants)

        return self.participants

    def own_analysts(self) -> dict[str, Analyst[N]]:
        self.analysts = self._own(self.analysts)

        return self.analysts

    def _own_nodes(self, node: AbstractNode) -> None:
        """Own the containers that writing `node` changes, i.e. all nodes and those of its type."""
        self.nodes = self._own(self.nodes)

        if isinstance(node, AtomNode):
            self.atom_nodes = self._own(self.atom_nodes)
        else:
            self.scheme_nodes = self._own(self.scheme_nodes)

    def _adjacency(self, node_id: str, *, outgoing: bool) -> dict[str, None]:
        """The edges of a node for writing, cloning the shared adjacency on the way."""
        if outgoing:
            self.outgoing = adjacency = self._own(self.outgoing)
        else:
            self.incoming = adjacency = self._own(self.incoming)

        adjacency[node_id] = edges = self._own(adjacency.get(node_id, {}))

        return edges

    def insert_node(self, node: AtomOrSchemeNode[A, S]) -> None:
        """Add a node without edges."""
        self.replace_node(node)
        self._adjacency(node.id, outgoing=False)
        self._adjacency(node.id, outgoing=True)

    def replace_node(self, node: AtomOrSchemeNode[A, S]) -> None:
        """Replace the node with the id of `node`, keeping its edges."""
        self._own_nodes(node)
        self.nodes[node.id] = node

        match node:
            case AtomNode():
                self.atom_nodes[node.id] = node
            case SchemeNode():
                self.scheme_nodes[node.id] = node
            case _:
                assert_never(node)

    def delete_node(self, node_id: str) -> AtomOrSchemeNode[A, S]:
        """Remove a node together with its edges, unsetting it as major claim."""
        removed = self.nodes[node_id]
        self._own_nodes(removed)
        del self.nodes[node_id]
        self.atom_nodes.pop(node_id, None)
        self.scheme_nodes.pop(node_id, None)

        # the adjacency of the removed node is dropped as a whole, only its neighbors change
        self.incoming = self._own(self.incoming)
        self.outgoing = self._own(self.outgoing)
        incoming = self.incoming.pop(node_id)
        outgoing = self.outgoing.pop(node_id)
        edges = self.own_edges()

        for edge_id in incoming:
            del self._adjacency(edges.pop(edge_id).source, outgoing=True)[edge_id]

        for edge_id in outgoing:
            del self._adjacency(edges.pop(edge_id).target, outgoing=False)[edge_id]

        if self.major_claim == node_id:
            self.major_claim = None

        return removed

    def insert_edge(self, edge: Edge[E]) -> None:
        """Add an edge between nodes of the store."""
        self.own_edges()[edge.id] = edge
        self._adjacency(edge.source, outgoing=True)[edge.id] = None
        self._adjacency(edge.target, outgoing=False)[edge.id] = None

    def delete_edge(self, edge_id: str) -> Edge[E]:
        """Remove an edge from the adjacency of its nodes."""
        removed = self.own_edges().pop(edge_id)
        del self._adjacency(removed.source, outgoing=True)[edge_id]
        del self._adjacency(removed.target, outgoing=False)[edge_id]

        return removed

    def neighbor_ids(self, node_id: str) -> list[str]:
        """Ids of the nodes connected to the node via incoming or outgoing edges."""
        return list(
            dict.fromkeys(
                (
                    *(self.edges[id].source for id in self.incoming[node_id]),
                    *(self.edges[id].target for id in self.outgoing[node_id]),
                )
            )
        )

    def is_dangling(self, node_id: str) -> bool:
        """Whether the node is a scheme without a premise (atom) or without a conclusion."""
        return node_id in self.scheme_nodes and (
            not self.outgoing[node_id]
            or not any(
                self.edges[id].source in self.atom_nodes
                for id in self.incoming[node_id]
            )
        )

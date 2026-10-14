import itertools
from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from dataclasses import KW_ONLY, dataclass, field, replace
from types import MappingProxyType

from arguebuf.model.analyst import Analyst
from arguebuf.model.edge import Edge
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.resource import Resource
from arguebuf.model.userdata import Userdata
from arguebuf.model.utils import Entity, uuid

__all__ = ("Graph",)


@dataclass(slots=True, eq=False)
class Graph[T = str]:
    """Argument graph consisting of atom nodes, scheme nodes, and edges.

    Elements are added and removed through the methods of the graph,
    all collections exposed by it are read-only.
    """

    name: str = field(default_factory=uuid)
    _: KW_ONLY
    metadata: Metadata = field(default_factory=Metadata, repr=False)
    userdata: Userdata = field(default_factory=dict, repr=False)
    library_version: str | None = None
    schema_version: int | None = None
    _nodes: dict[str, AbstractNode] = field(
        default_factory=dict, init=False, repr=False
    )
    _atom_nodes: dict[str, AtomNode[T]] = field(
        default_factory=dict, init=False, repr=False
    )
    _scheme_nodes: dict[str, SchemeNode] = field(
        default_factory=dict, init=False, repr=False
    )
    _edges: dict[str, Edge] = field(default_factory=dict, init=False, repr=False)
    _incoming_nodes: dict[AbstractNode, set[AbstractNode]] = field(
        default_factory=dict, init=False, repr=False
    )
    _incoming_edges: dict[AbstractNode, set[Edge]] = field(
        default_factory=dict, init=False, repr=False
    )
    _outgoing_nodes: dict[AbstractNode, set[AbstractNode]] = field(
        default_factory=dict, init=False, repr=False
    )
    _outgoing_edges: dict[AbstractNode, set[Edge]] = field(
        default_factory=dict, init=False, repr=False
    )
    _resources: dict[str, Resource[T]] = field(
        default_factory=dict, init=False, repr=False
    )
    _participants: dict[str, Participant] = field(
        default_factory=dict, init=False, repr=False
    )
    _analysts: dict[str, Analyst] = field(default_factory=dict, init=False, repr=False)
    _major_claim: AtomNode[T] | None = field(default=None, init=False, repr=False)

    @property
    def nodes(self) -> Mapping[str, AbstractNode]:
        return MappingProxyType(self._nodes)

    @property
    def atom_nodes(self) -> Mapping[str, AtomNode[T]]:
        return MappingProxyType(self._atom_nodes)

    @property
    def scheme_nodes(self) -> Mapping[str, SchemeNode]:
        return MappingProxyType(self._scheme_nodes)

    @property
    def edges(self) -> Mapping[str, Edge]:
        return MappingProxyType(self._edges)

    @property
    def resources(self) -> Mapping[str, Resource[T]]:
        return MappingProxyType(self._resources)

    @property
    def participants(self) -> Mapping[str, Participant]:
        return MappingProxyType(self._participants)

    @property
    def analysts(self) -> Mapping[str, Analyst]:
        return MappingProxyType(self._analysts)

    @property
    def major_claim(self) -> AtomNode[T] | None:
        return self._major_claim

    @major_claim.setter
    def major_claim(self, value: str | AtomNode[T] | None) -> None:
        self._major_claim = self._atom_nodes[value] if isinstance(value, str) else value

    @property
    def root_node(self) -> AtomNode[T] | None:
        """If there is a single node with no outgoing edges, return it, otherwise None"""
        candidates = self.root_nodes

        if len(candidates) == 1:
            return next(iter(candidates))

        return None

    @property
    def root_nodes(self) -> set[AtomNode[T]]:
        """Find all nodes with no outgoing edges"""
        return {
            node for node in self._atom_nodes.values() if not self._outgoing_nodes[node]
        }

    @property
    def leaf_nodes(self) -> set[AtomNode[T]]:
        """Find all nodes with no incoming edges"""
        return {
            node for node in self._atom_nodes.values() if not self._incoming_nodes[node]
        }

    def _node(self, node: str | AbstractNode) -> AbstractNode:
        return self._nodes[node] if isinstance(node, str) else node

    def incoming_nodes(self, node: str | AbstractNode) -> AbstractSet[AbstractNode]:
        return frozenset(self._incoming_nodes[self._node(node)])

    def outgoing_nodes(self, node: str | AbstractNode) -> AbstractSet[AbstractNode]:
        return frozenset(self._outgoing_nodes[self._node(node)])

    child_nodes = incoming_nodes
    parent_nodes = outgoing_nodes

    def incoming_edges(self, node: str | AbstractNode) -> AbstractSet[Edge]:
        return frozenset(self._incoming_edges[self._node(node)])

    def outgoing_edges(self, node: str | AbstractNode) -> AbstractSet[Edge]:
        return frozenset(self._outgoing_edges[self._node(node)])

    def incoming_atom_nodes(self, node: str | AbstractNode) -> set[AtomNode[T]]:
        """Find the closest atom nodes connected to `node` via incoming edges."""
        return self._neighbor_atom_nodes(node, self._incoming_nodes)

    def outgoing_atom_nodes(self, node: str | AbstractNode) -> set[AtomNode[T]]:
        """Find the closest atom nodes connected to `node` via outgoing edges."""
        return self._neighbor_atom_nodes(node, self._outgoing_nodes)

    def _neighbor_atom_nodes(
        self,
        node: str | AbstractNode,
        neighbors: Mapping[AbstractNode, AbstractSet[AbstractNode]],
    ) -> set[AtomNode[T]]:
        candidates = list(neighbors[self._node(node)])
        atom_nodes: set[AtomNode[T]] = set()

        while candidates:
            candidate = candidates.pop()

            # atom nodes are collected, all other nodes are expanded
            if candidate.id in self._atom_nodes:
                atom_nodes.add(self._atom_nodes[candidate.id])
            else:
                candidates.extend(neighbors[candidate])

        return atom_nodes

    def sibling_node_distances(
        self,
        node: str | AbstractNode,
        max_levels: int | None = None,
        node_type: type[AbstractNode] = AbstractNode,
    ) -> dict[AbstractNode, int]:
        """Find all sibling nodes of a node and their distance in the graph"""
        node = self._node(node)
        sibling_nodes: dict[AbstractNode, int] = {}
        parent_nodes: dict[AbstractNode, int] = {
            parent: 1 for parent in self._outgoing_nodes[node]
        }

        while parent_nodes:
            parent, level = parent_nodes.popitem()
            child_nodes: AbstractSet[AbstractNode] = self._incoming_nodes[parent]

            if max_levels is None or level < max_levels:
                parent_nodes.update(
                    {
                        grandparent: level + 1
                        for grandparent in self._outgoing_nodes[parent]
                    }
                )

            for _ in range(level - 1):
                if not child_nodes:
                    break

                child_nodes = {
                    grandchild
                    for child in child_nodes
                    for grandchild in self._incoming_nodes[child]
                }

            sibling_nodes.update(
                {
                    child: level
                    for child in child_nodes
                    if isinstance(child, node_type) and child not in sibling_nodes
                }
            )

        return sibling_nodes

    def sibling_nodes(
        self,
        node: str | AbstractNode,
        max_levels: int | None = 1,
        node_type: type[AbstractNode] = AbstractNode,
    ) -> AbstractSet[AbstractNode]:
        return self.sibling_node_distances(node, max_levels, node_type).keys()

    def scheme_between(
        self, premise: AtomNode[T], claim: AtomNode[T]
    ) -> SchemeNode | None:
        candidates = self._outgoing_nodes[premise] & self._incoming_nodes[claim]

        if len(candidates) == 1:
            return self._scheme_nodes.get(next(iter(candidates)).id)

        return None

    def _insert[V: Entity](self, store: dict[str, V], value: V) -> None:
        if value.id in store:
            raise ValueError(
                f"Graph '{self.name}' already contains an element with key '{value.id}'."
            )

        store[value.id] = value

    def _delete[V: Entity](self, store: dict[str, V], value: V) -> None:
        if value.id not in store:
            raise KeyError(
                f"Graph '{self.name}' does not contain an element with key '{value.id}'."
            )

        del store[value.id]

    def add_node(self, node: AtomNode[T] | SchemeNode) -> None:
        """Add a node to the graph.

        Args:
            node: Node object that is not already part of the graph.

        Examples:
            >>> g = Graph()
            >>> g.add_node(AtomNode("Exemplary node"))
            >>> len(g.nodes)
            1
            >>> g.add_node(SchemeNode())
            >>> len(g.nodes)
            2
        """
        self._insert(self._nodes, node)

        match node:
            case AtomNode():
                self._atom_nodes[node.id] = node

                if node.participant and node.participant.id not in self._participants:
                    self.add_participant(node.participant)

                if (
                    node.reference
                    and node.reference.resource
                    and node.reference.resource.id not in self._resources
                ):
                    self.add_resource(node.reference.resource)

            case SchemeNode():
                self._scheme_nodes[node.id] = node

        self._incoming_nodes[node] = set()
        self._incoming_edges[node] = set()
        self._outgoing_nodes[node] = set()
        self._outgoing_edges[node] = set()

    def remove_node(self, node: AbstractNode) -> None:
        """Remove a node and its corresponding edges from the graph.

        Args:
            node: Node object that is part of the graph.

        Examples:
            >>> g = Graph()
            >>> n1 = AtomNode("Node1")
            >>> n2 = SchemeNode()
            >>> g.add_edge(Edge(n1, n2))
            >>> g.remove_node(n1)
            >>> len(g.nodes)
            1
            >>> len(g.edges)
            0
            >>> g.remove_node(n1)
            Traceback (most recent call last):
            KeyError: ...
        """
        self._delete(self._nodes, node)
        self._atom_nodes.pop(node.id, None)
        self._scheme_nodes.pop(node.id, None)

        for edge in self._incoming_edges[node] | self._outgoing_edges[node]:
            self.remove_edge(edge)

        del self._incoming_nodes[node]
        del self._incoming_edges[node]
        del self._outgoing_nodes[node]
        del self._outgoing_edges[node]

    def add_edge(self, edge: Edge) -> None:
        """Add an edge and its nodes (if not already added).

        Args:
            edge: Edge object that is not part of the graph.

        Examples:
            >>> g = Graph()
            >>> n1 = AtomNode("Premise")
            >>> n2 = SchemeNode()
            >>> n3 = AtomNode("Claim")
            >>> g.add_edge(Edge(n1, n2))
            >>> g.add_edge(Edge(n2, n3))
            >>> len(g.edges)
            2
        """
        self._insert(self._edges, edge)

        for node in (edge.source, edge.target):
            if node.id not in self._nodes and isinstance(node, AtomNode | SchemeNode):
                self.add_node(node)

        self._outgoing_edges[edge.source].add(edge)
        self._incoming_edges[edge.target].add(edge)
        self._outgoing_nodes[edge.source].add(edge.target)
        self._incoming_nodes[edge.target].add(edge.source)

    def remove_edge(self, edge: Edge) -> None:
        """Remove an edge.

        Args:
            edge: Edge object that is part of the graph.

        Examples:
            >>> g = Graph()
            >>> e = Edge(AtomNode("Node1"), SchemeNode())
            >>> g.add_edge(e)
            >>> g.remove_edge(e)
            >>> len(g.edges)
            0
            >>> len(g.nodes)
            2
        """
        self._delete(self._edges, edge)

        self._outgoing_edges[edge.source].remove(edge)
        self._incoming_edges[edge.target].remove(edge)
        self._outgoing_nodes[edge.source].remove(edge.target)
        self._incoming_nodes[edge.target].remove(edge.source)

    def add_resource(self, resource: Resource[T]) -> None:
        """Add a resource.

        Examples:
            >>> g = Graph()
            >>> g.add_resource(Resource("Resource1"))
            >>> len(g.resources)
            1
        """
        self._insert(self._resources, resource)

    def remove_resource(self, resource: Resource[T]) -> None:
        """Remove a resource and the references of all nodes pointing to it.

        Examples:
            >>> g = Graph()
            >>> r1 = Resource("Resource1")
            >>> g.add_resource(r1)
            >>> g.remove_resource(r1)
            >>> len(g.resources)
            0
        """
        self._delete(self._resources, resource)

        for node in self._atom_nodes.values():
            if node.reference and node.reference.resource == resource:
                node.reference = replace(node.reference, resource=None, offset=None)

    def clean_resources(self) -> None:
        """Remove resources that are not referenced by any node."""
        used = {
            node.reference.resource.id
            for node in self._atom_nodes.values()
            if node.reference and node.reference.resource
        }

        for resource_id in self._resources.keys() - used:
            del self._resources[resource_id]

    def add_participant(self, participant: Participant) -> None:
        """Add a participant.

        Examples:
            >>> g = Graph()
            >>> g.add_participant(Participant("Participant1"))
            >>> len(g.participants)
            1
        """
        self._insert(self._participants, participant)

    def remove_participant(self, participant: Participant) -> None:
        """Remove a participant and unset it for all its nodes.

        Examples:
            >>> g = Graph()
            >>> p1 = Participant("Participant1")
            >>> g.add_participant(p1)
            >>> g.remove_participant(p1)
            >>> len(g.participants)
            0
        """
        self._delete(self._participants, participant)

        for node in self._atom_nodes.values():
            if node.participant == participant:
                node.participant = None

    def clean_participants(self) -> None:
        """Remove participants that are not assigned to any node."""
        used = {
            node.participant.id
            for node in self._atom_nodes.values()
            if node.participant
        }

        for participant_id in self._participants.keys() - used:
            del self._participants[participant_id]

    def add_analyst(self, analyst: Analyst) -> None:
        """Add an analyst.

        Examples:
            >>> g = Graph()
            >>> g.add_analyst(Analyst("Name"))
            >>> len(g.analysts)
            1
        """
        self._insert(self._analysts, analyst)

    def remove_analyst(self, analyst: Analyst) -> None:
        """Remove an analyst.

        Examples:
            >>> g = Graph()
            >>> a1 = Analyst("Name")
            >>> g.add_analyst(a1)
            >>> g.remove_analyst(a1)
            >>> len(g.analysts)
            0
        """
        self._delete(self._analysts, analyst)

    def remove_scheme_nodes(self) -> None:
        """Remove scheme nodes from graph to connect atom nodes directly

        Can be useful to analyze the structure of atom nodes
        without considering their relation types (i.e., the scheme nodes between them).
        """
        for scheme in list(self._scheme_nodes.values()):
            for incoming, outgoing in itertools.product(
                self.incoming_atom_nodes(scheme), self.outgoing_atom_nodes(scheme)
            ):
                self.add_edge(Edge(incoming, outgoing))

            self.remove_node(scheme)

    strip_scheme_nodes = remove_scheme_nodes

    def remove_empty_scheme_branches(self) -> None:
        """Remove scheme nodes without a scheme together with their descendants."""
        empty_schemes = [
            node for node in self._scheme_nodes.values() if node.scheme is None
        ]

        for scheme_node in empty_schemes:
            if scheme_node.id in self._scheme_nodes:
                self.remove_branch(scheme_node)

    def remove_branch(self, element: AbstractNode | Edge | str) -> None:
        """Remove an element and all its descendants from the graph.

        If the element is a string, it is interpreted as the id of a node.
        """
        match element:
            case str():
                node = self._nodes[element]
            case Edge():
                node = element.source
            case _:
                node = element

        descendants = list(self._incoming_nodes[node])
        self.remove_node(node)

        for descendant in descendants:
            if descendant.id in self._nodes:
                self.remove_branch(descendant)

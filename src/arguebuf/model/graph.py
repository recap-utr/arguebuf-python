import copy
import itertools
from collections.abc import Callable, Iterable, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import assert_never, overload

from arguebuf.model.analyst import Analyst
from arguebuf.model.edge import Edge
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AbstractNode, AtomNode, AtomOrSchemeNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.resource import Resource
from arguebuf.model.userdata import JSON_OBJECT, JsonObject, own
from arguebuf.model.utils import Entity
from arguebuf.traverse import dfs

__all__ = ("Graph",)


# lazily evaluated, so the overloads below can specialize the class they belong to
type _JsonGraph = Graph
type _ObjectGraph = Graph[object, object, object, object, object, object, object]


@dataclass(slots=True, eq=False)
class Graph[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
]:
    """Argument graph consisting of atom nodes, scheme nodes, and edges.

    Its read-only, insertion-ordered collections change only via its `add_*` methods,
    which raise a `ValueError` for taken ids and foreign references,
    and its `remove_*` methods, which raise a `KeyError` for unknown elements or ids
    and unset all references to them.
    The type parameters are the userdata types of atom nodes, scheme nodes, edges,
    the graph, resources, participants, and analysts (see `arguebuf.Codecs`).

    Attributes:
        name: Optional name, used for example as file name by `arguebuf.dump.file`.
    """

    name: str | None
    metadata: Metadata = field(repr=False)
    userdata: G = field(repr=False)
    _nodes: dict[str, AtomOrSchemeNode[A, S]] = field(repr=False)
    _atom_nodes: dict[str, AtomNode[A]] = field(repr=False)
    _scheme_nodes: dict[str, SchemeNode[S]] = field(repr=False)
    _edges: dict[str, Edge[E]] = field(repr=False)
    # adjacency stores edges since parallel edges may connect the same nodes,
    # dicts are used as insertion-ordered sets
    _incoming_edges: dict[str, dict[Edge[E], None]] = field(repr=False)
    _outgoing_edges: dict[str, dict[Edge[E], None]] = field(repr=False)
    _resources: dict[str, Resource[R]] = field(repr=False)
    _participants: dict[str, Participant[P]] = field(repr=False)
    _analysts: dict[str, Analyst[N]] = field(repr=False)
    _major_claim: AtomNode[A] | None = field(repr=False)

    # a JSON literal would otherwise infer a narrower userdata type like dict[str, str]
    @overload
    def __init__(
        self: _JsonGraph,
        name: str | None = None,
        *,
        metadata: Metadata | None = None,
        userdata: JsonObject,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str | None = None,
        *,
        metadata: Metadata | None = None,
        userdata: G = JSON_OBJECT,
    ) -> None: ...

    def __init__(
        self: _ObjectGraph,
        name: str | None = None,
        *,
        metadata: Metadata | None = None,
        userdata: object = JSON_OBJECT,
    ) -> None:
        self.name = name
        self.metadata = metadata or Metadata()
        self.userdata = own(userdata)
        self._nodes = {}
        self._atom_nodes = {}
        self._scheme_nodes = {}
        self._edges = {}
        self._incoming_edges = {}
        self._outgoing_edges = {}
        self._resources = {}
        self._participants = {}
        self._analysts = {}
        self._major_claim = None

    @property
    def nodes(self) -> Mapping[str, AtomOrSchemeNode[A, S]]:
        """Atom and scheme nodes by their id."""
        return MappingProxyType(self._nodes)

    @property
    def atom_nodes(self) -> Mapping[str, AtomNode[A]]:
        """Atom nodes by their id."""
        return MappingProxyType(self._atom_nodes)

    @property
    def scheme_nodes(self) -> Mapping[str, SchemeNode[S]]:
        """Scheme nodes by their id."""
        return MappingProxyType(self._scheme_nodes)

    @property
    def edges(self) -> Mapping[str, Edge[E]]:
        """Edges by their id."""
        return MappingProxyType(self._edges)

    @property
    def resources(self) -> Mapping[str, Resource[R]]:
        """Resources by their id."""
        return MappingProxyType(self._resources)

    @property
    def participants(self) -> Mapping[str, Participant[P]]:
        """Participants by their id."""
        return MappingProxyType(self._participants)

    @property
    def analysts(self) -> Mapping[str, Analyst[N]]:
        """Analysts by their id."""
        return MappingProxyType(self._analysts)

    @property
    def major_claim(self) -> AtomNode[A] | None:
        """Atom node of the graph representing its overall claim.

        It is set to an atom node of the graph given by itself or its id.

        Examples:
            >>> g = Graph()
            >>> g.add_node(AtomNode("Claim", id="a1"))
            >>> g.major_claim = "a1"
            >>> g.major_claim.text
            'Claim'
            >>> g.major_claim = AtomNode("Foreign")
            Traceback (most recent call last):
            ValueError: ...
        """
        return self._major_claim

    @major_claim.setter
    def major_claim(self, value: str | AbstractNode | None) -> None:
        if value is None:
            self._major_claim = None

            return

        id = value if isinstance(value, str) else value.id

        if id not in self._atom_nodes:
            raise ValueError(f"The graph does not contain the atom node '{id}'.")

        self._major_claim = self._atom_nodes[id]

    @property
    def root_node(self) -> AtomNode[A] | None:
        """The only atom node without outgoing edges, None if there is not exactly one."""
        candidates = self.root_nodes

        if len(candidates) == 1:
            return next(iter(candidates))

        return None

    @property
    def root_nodes(self) -> AbstractSet[AtomNode[A]]:
        """Atom nodes without outgoing edges."""
        return _ordered(
            node
            for node in self._atom_nodes.values()
            if not self._outgoing_edges[node.id]
        )

    @property
    def leaf_nodes(self) -> AbstractSet[AtomNode[A]]:
        """Atom nodes without incoming edges."""
        return _ordered(
            node
            for node in self._atom_nodes.values()
            if not self._incoming_edges[node.id]
        )

    def _node(self, node: str | AbstractNode) -> AtomOrSchemeNode[A, S]:
        return self._nodes[node if isinstance(node, str) else node.id]

    def incoming_nodes(
        self, node: str | AbstractNode
    ) -> AbstractSet[AtomOrSchemeNode[A, S]]:
        """Source nodes of the edges pointing to `node`."""
        return _ordered(self._node(edge.source) for edge in self.incoming_edges(node))

    def outgoing_nodes(
        self, node: str | AbstractNode
    ) -> AbstractSet[AtomOrSchemeNode[A, S]]:
        """Target nodes of the edges starting at `node`."""
        return _ordered(self._node(edge.target) for edge in self.outgoing_edges(node))

    def incoming_edges(self, node: str | AbstractNode) -> AbstractSet[Edge[E]]:
        """Edges pointing to `node`."""
        return _ordered(self._incoming_edges[self._node(node).id])

    def outgoing_edges(self, node: str | AbstractNode) -> AbstractSet[Edge[E]]:
        """Edges starting at `node`."""
        return _ordered(self._outgoing_edges[self._node(node).id])

    def incoming_atom_nodes(self, node: str | AbstractNode) -> AbstractSet[AtomNode[A]]:
        """Find the closest atom nodes connected to `node` via incoming edges."""
        return self._neighbor_atom_nodes(node, self.incoming_nodes)

    def outgoing_atom_nodes(self, node: str | AbstractNode) -> AbstractSet[AtomNode[A]]:
        """Find the closest atom nodes connected to `node` via outgoing edges."""
        return self._neighbor_atom_nodes(node, self.outgoing_nodes)

    def _neighbor_atom_nodes(
        self,
        node: str | AbstractNode,
        neighbors: Callable[[AbstractNode], AbstractSet[AtomOrSchemeNode[A, S]]],
    ) -> AbstractSet[AtomNode[A]]:
        start = self._node(node)
        visited: set[AbstractNode] = {start}
        candidates = list(neighbors(start))
        atom_nodes: dict[AtomNode[A], None] = {}

        while candidates:
            candidate = candidates.pop()

            if candidate in visited:
                continue

            visited.add(candidate)

            # atom nodes are collected, all other nodes are expanded
            if isinstance(candidate, AtomNode):
                atom_nodes[candidate] = None
            else:
                candidates.extend(neighbors(candidate))

        return atom_nodes.keys()

    def sibling_node_distances(
        self,
        node: str | AbstractNode,
        max_levels: int | None = 1,
        node_type: type[AbstractNode] = AbstractNode,
    ) -> dict[AtomOrSchemeNode[A, S], int]:
        """Find the nodes `n` levels below the ancestors at the shortest up-distance `n` of `node`.

        Up follows outgoing edges, each sibling gets its smallest `n`, `node` itself is excluded.

        Args:
            node: Node object or id that is part of the graph.
            max_levels: Maximum number of levels to go up, unlimited if None.
            node_type: Only include siblings of this type.

        Examples:
            >>> g = Graph()
            >>> claim, scheme = AtomNode("Claim"), SchemeNode()
            >>> p1, p2 = AtomNode("Premise 1"), AtomNode("Premise 2")
            >>> for n in (claim, scheme, p1, p2):
            ...     g.add_node(n)
            >>> for source, target in ((p1, scheme), (p2, scheme), (scheme, claim)):
            ...     g.add_edge(Edge(source, target))
            >>> g.sibling_node_distances(p1) == {p2: 1}
            True
        """
        start = self._node(node)
        distances: dict[AtomOrSchemeNode[A, S], int] = {}
        visited: set[AbstractNode] = {start}
        ancestors: AbstractSet[AtomOrSchemeNode[A, S]] = {start}
        level = 0

        while ancestors and (max_levels is None or level < max_levels):
            level += 1
            ancestors = _ordered(
                parent
                for ancestor in ancestors
                for parent in self.outgoing_nodes(ancestor)
                if parent not in visited
            )
            visited.update(ancestors)
            descendants = ancestors

            for _ in range(level):
                descendants = _ordered(
                    child
                    for descendant in descendants
                    for child in self.incoming_nodes(descendant)
                )

            for descendant in descendants:
                if (
                    descendant != start
                    and isinstance(descendant, node_type)
                    and descendant not in distances
                ):
                    distances[descendant] = level

        return distances

    def sibling_nodes(
        self,
        node: str | AbstractNode,
        max_levels: int | None = 1,
        node_type: type[AbstractNode] = AbstractNode,
    ) -> AbstractSet[AtomOrSchemeNode[A, S]]:
        """Find the sibling nodes of a node, see `sibling_node_distances`."""
        return self.sibling_node_distances(node, max_levels, node_type).keys()

    def scheme_between(
        self, premise: str | AbstractNode, claim: str | AbstractNode
    ) -> SchemeNode[S] | None:
        """Get the scheme node connecting `premise` to `claim` if it is unique."""
        candidates = [
            node
            for node in self.outgoing_nodes(premise) & self.incoming_nodes(claim)
            if isinstance(node, SchemeNode)
        ]

        return candidates[0] if len(candidates) == 1 else None

    def _insert[V: Entity](self, store: dict[str, V], value: V) -> None:
        if value.id in store:
            raise ValueError(
                f"The graph already contains an element with key '{value.id}'."
            )

        store[value.id] = value

    def _delete[V: Entity](self, store: dict[str, V], value: str | Entity) -> V:
        id = value if isinstance(value, str) else value.id

        if id not in store:
            raise KeyError(f"The graph does not contain an element with key '{id}'.")

        return store.pop(id)

    def _require[V: Entity](self, store: Mapping[str, V], value: V) -> None:
        if store.get(value.id) is not value:
            raise ValueError(
                f"The graph does not contain the {type(value).__name__} '{value.id}'."
            )

    def add_node(self, node: AtomOrSchemeNode[A, S]) -> None:
        """Add a node to the graph.

        Args:
            node: Node object that is not already part of the graph.
                The participant and the resource referenced by an atom node
                must already be part of the graph.

        Examples:
            >>> g = Graph()
            >>> g.add_node(AtomNode("Exemplary node"))
            >>> len(g.nodes)
            1
            >>> g.add_node(SchemeNode())
            >>> len(g.nodes)
            2
            >>> g.add_node(AtomNode("Node", participant=Participant("Unknown")))
            Traceback (most recent call last):
            ValueError: ...
        """
        if isinstance(node, AtomNode):
            if node.participant:
                self._require(self._participants, node.participant)

            if node.reference and node.reference.resource:
                self._require(self._resources, node.reference.resource)

        self._insert(self._nodes, node)

        match node:
            case AtomNode():
                self._atom_nodes[node.id] = node
            case SchemeNode():
                self._scheme_nodes[node.id] = node
            case _:
                assert_never(node)

        self._incoming_edges[node.id] = {}
        self._outgoing_edges[node.id] = {}

    def remove_node(self, node: str | AbstractNode) -> None:
        """Remove a node together with its edges and all references to it.

        The major claim is unset if it is the node
        and an atom node is removed from the premise descriptors of all scheme nodes.

        Args:
            node: Node object or id that is part of the graph.

        Examples:
            >>> g = Graph()
            >>> n1 = AtomNode("Node1")
            >>> n2 = SchemeNode()
            >>> g.add_node(n1)
            >>> g.add_node(n2)
            >>> g.add_edge(Edge(n1, n2))
            >>> g.major_claim = n1
            >>> g.remove_node(n1)
            >>> len(g.nodes), len(g.edges), g.major_claim
            (1, 0, None)
            >>> g.remove_node(n1)
            Traceback (most recent call last):
            KeyError: ...
        """
        removed = self._remove_node(node)

        # premise descriptors only reference atom nodes
        if isinstance(removed, AtomNode):
            self._remove_premise_descriptors({removed.id})

    def _remove_node(self, node: str | AbstractNode) -> AtomOrSchemeNode[A, S]:
        """Remove a node and its references except for premise descriptors."""
        removed = self._delete(self._nodes, node)
        self._atom_nodes.pop(removed.id, None)
        self._scheme_nodes.pop(removed.id, None)

        # the union removes duplicates of self-loops
        for edge in self._incoming_edges[removed.id] | self._outgoing_edges[removed.id]:
            self.remove_edge(edge)

        del self._incoming_edges[removed.id]
        del self._outgoing_edges[removed.id]

        if self._major_claim is removed:
            self._major_claim = None

        return removed

    def _remove_premise_descriptors(self, ids: AbstractSet[str]) -> None:
        for scheme in self._scheme_nodes.values():
            if not ids.isdisjoint(scheme.premise_descriptors):
                scheme.premise_descriptors = [
                    id for id in scheme.premise_descriptors if id not in ids
                ]

    def add_edge(self, edge: Edge[E]) -> None:
        """Add an edge between two nodes of the graph.

        Args:
            edge: Edge object that is not part of the graph.
                Its source and target must be nodes of the graph.

        Examples:
            >>> g = Graph()
            >>> n1 = AtomNode("Premise")
            >>> n2 = SchemeNode()
            >>> g.add_node(n1)
            >>> g.add_node(n2)
            >>> g.add_edge(Edge(n1, n2))
            >>> len(g.edges)
            1
            >>> g.add_edge(Edge(n2, AtomNode("Claim")))
            Traceback (most recent call last):
            ValueError: ...
        """
        self._require(self._nodes, edge.source)
        self._require(self._nodes, edge.target)
        self._insert(self._edges, edge)
        self._outgoing_edges[edge.source.id][edge] = None
        self._incoming_edges[edge.target.id][edge] = None

    def remove_edge(self, edge: str | Edge[E]) -> None:
        """Remove an edge.

        Args:
            edge: Edge object or id that is part of the graph.

        Examples:
            >>> g = Graph()
            >>> n1, n2 = AtomNode("Node1"), SchemeNode()
            >>> g.add_node(n1)
            >>> g.add_node(n2)
            >>> e = Edge(n1, n2)
            >>> g.add_edge(e)
            >>> g.remove_edge(e)
            >>> len(g.edges), len(g.nodes)
            (0, 2)
        """
        removed = self._delete(self._edges, edge)
        del self._outgoing_edges[removed.source.id][removed]
        del self._incoming_edges[removed.target.id][removed]

    def add_resource(self, resource: Resource[R]) -> None:
        """Add a resource.

        Examples:
            >>> g = Graph()
            >>> g.add_resource(Resource("Resource1"))
            >>> len(g.resources)
            1
        """
        self._insert(self._resources, resource)

    def remove_resource(self, resource: str | Resource[R]) -> None:
        """Remove a resource and unset it in the references of all atom nodes.

        Examples:
            >>> g = Graph()
            >>> r1 = Resource("Resource1")
            >>> g.add_resource(r1)
            >>> g.remove_resource(r1)
            >>> len(g.resources)
            0
        """
        removed = self._delete(self._resources, resource)

        for node in self._atom_nodes.values():
            if node.reference and node.reference.resource == removed:
                node.reference = copy.replace(
                    node.reference, resource=None, offset=None
                )

    def clean_resources(self) -> None:
        """Remove resources that are not referenced by any node."""
        used = {
            node.reference.resource.id
            for node in self._atom_nodes.values()
            if node.reference and node.reference.resource
        }

        for resource_id in self._resources.keys() - used:
            del self._resources[resource_id]

    def add_participant(self, participant: Participant[P]) -> None:
        """Add a participant.

        Examples:
            >>> g = Graph()
            >>> g.add_participant(Participant("Participant1"))
            >>> len(g.participants)
            1
        """
        self._insert(self._participants, participant)

    def remove_participant(self, participant: str | Participant[P]) -> None:
        """Remove a participant and unset it for all its atom nodes.

        Examples:
            >>> g = Graph()
            >>> p1 = Participant("Participant1")
            >>> g.add_participant(p1)
            >>> g.remove_participant(p1)
            >>> len(g.participants)
            0
        """
        removed = self._delete(self._participants, participant)

        for node in self._atom_nodes.values():
            if node.participant == removed:
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

    def add_analyst(self, analyst: Analyst[N]) -> None:
        """Add an analyst.

        Examples:
            >>> g = Graph()
            >>> g.add_analyst(Analyst("Name"))
            >>> len(g.analysts)
            1
        """
        self._insert(self._analysts, analyst)

    def remove_analyst(self, analyst: str | Analyst[N]) -> None:
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

    def remove_scheme_nodes(self, edge_userdata: Callable[[], E] = dict) -> None:
        """Remove scheme nodes from graph to connect atom nodes directly.

        Can be useful to analyze the structure of atom nodes
        without considering their relation types (i.e., the scheme nodes between them).
        Atom nodes that are already connected do not get an additional edge.

        Args:
            edge_userdata: Creates the userdata of each new edge,
                it can only be omitted for JSON object userdata.
        """
        for scheme in list(self._scheme_nodes.values()):
            for source, target in itertools.product(
                self.incoming_atom_nodes(scheme), self.outgoing_atom_nodes(scheme)
            ):
                if source != target and target not in self.outgoing_nodes(source):
                    self.add_edge(Edge(source, target, userdata=edge_userdata()))

            self.remove_node(scheme)

    def remove_empty_scheme_branches(self) -> None:
        """Remove scheme nodes without a scheme together with their descendants."""
        empty_schemes = [
            node for node in self._scheme_nodes.values() if node.scheme is None
        ]

        for scheme_node in empty_schemes:
            if scheme_node.id in self._scheme_nodes:
                self.remove_branch(scheme_node)

    def remove_branch(self, element: str | AbstractNode | Edge[E]) -> None:
        """Remove an element and all its descendants from the graph.

        If the element is a string, it is interpreted as the id of a node,
        an edge is interpreted as its source node.
        Descendants are the nodes reachable via incoming edges.
        """
        start = self._node(element.source if isinstance(element, Edge) else element)
        removed = dfs(start, self.incoming_nodes)

        for node in removed:
            self._remove_node(node)

        self._remove_premise_descriptors({node.id for node in removed})


def _ordered[T](elements: Iterable[T]) -> AbstractSet[T]:
    """Collect elements into a set that keeps their insertion order."""
    return dict.fromkeys(elements).keys()

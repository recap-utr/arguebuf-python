from abc import ABC
from collections.abc import Callable, Iterable, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from types import MappingProxyType

from arguebuf.model._graph_store import GraphStore
from arguebuf.model._graph_validation import edge_issue, get
from arguebuf.model.analyst import Analyst
from arguebuf.model.edge import Edge
from arguebuf.model.issue import Issue
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AbstractNode, AtomNode, Node, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.resource import Resource
from arguebuf.model.userdata import JsonObject
from arguebuf.model.utils import id_of

__all__ = ("Annotation", "AtomRelation", "GraphView")


@dataclass(slots=True, frozen=True)
class AtomRelation[A = JsonObject, S = JsonObject]:
    """Atom node connected to another one via a scheme node, see `Graph.atom_relations`."""

    source: AtomNode[A]
    target: AtomNode[A]
    scheme: SchemeNode[S]


@dataclass(slots=True, frozen=True)
class Annotation[A = JsonObject]:
    """Atom node whose reference is anchored in a resource, see `Graph.annotations`.

    Attributes:
        node: Atom node with the reference.
        start: Index of the first code point of the reference in the resource text.
        end: Index after the last code point of the reference in the resource text.
    """

    node: AtomNode[A]
    start: int
    end: int


def ordered[T](elements: Iterable[T]) -> AbstractSet[T]:
    """Collect elements into a set that keeps their insertion order."""
    return dict.fromkeys(elements).keys()


class GraphView[A, S, E, R, P, N, G](ABC):
    """Read access to the fields, elements, and queries of a graph.

    The base of `arguebuf.Graph` and `arguebuf.GraphDraft`, which declare its fields and store.
    Functions that only read a graph accept it to take both.

    Attributes:
        name: Optional name, used for example as file name by `arguebuf.dump.file`.
        metadata: Creation and modification times of the graph.
        userdata: Userdata of the graph.
    """

    __slots__ = ()

    _store: GraphStore[A, S, E, R, P, N]

    name: str | None
    metadata: Metadata
    userdata: G

    @property
    def nodes(self) -> Mapping[str, Node[A, S]]:
        """Atom and scheme nodes by their id."""
        return MappingProxyType(self._store.nodes)

    @property
    def atom_nodes(self) -> Mapping[str, AtomNode[A]]:
        """Atom nodes by their id."""
        return MappingProxyType(self._store.atom_nodes)

    @property
    def scheme_nodes(self) -> Mapping[str, SchemeNode[S]]:
        """Scheme nodes by their id."""
        return MappingProxyType(self._store.scheme_nodes)

    @property
    def edges(self) -> Mapping[str, Edge[E]]:
        """Edges by their id."""
        return MappingProxyType(self._store.edges)

    @property
    def resources(self) -> Mapping[str, Resource[R]]:
        """Resources by their id."""
        return MappingProxyType(self._store.resources)

    @property
    def participants(self) -> Mapping[str, Participant[P]]:
        """Participants by their id."""
        return MappingProxyType(self._store.participants)

    @property
    def analysts(self) -> Mapping[str, Analyst[N]]:
        """Analysts by their id."""
        return MappingProxyType(self._store.analysts)

    @property
    def major_claim(self) -> str | None:
        """Id of the atom node of the graph representing its overall claim.

        A draft sets it to an atom node of the graph given by itself or its id.

        Examples:
            >>> from arguebuf import AtomNode, GraphDraft
            >>> g = GraphDraft()
            >>> g.add_node(AtomNode("Claim", id="a1"))
            >>> g.major_claim = "a1"
            >>> g.atom_nodes[g.major_claim].text
            'Claim'
            >>> g.major_claim = AtomNode("Foreign")
            Traceback (most recent call last):
            arguebuf.model.issue.GraphError: ...
        """
        return self._store.major_claim

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
        return ordered(
            node
            for node in self._store.atom_nodes.values()
            if not self._store.outgoing[node.id]
        )

    @property
    def leaf_nodes(self) -> AbstractSet[AtomNode[A]]:
        """Atom nodes without incoming edges."""
        return ordered(
            node
            for node in self._store.atom_nodes.values()
            if not self._store.incoming[node.id]
        )

    def _node(self, node: str | AbstractNode) -> Node[A, S]:
        return get(self._store.nodes, node, "Node")

    def incoming_nodes(self, node: str | AbstractNode) -> AbstractSet[Node[A, S]]:
        """Source nodes of the edges pointing to `node`."""
        return ordered(self._node(edge.source) for edge in self.incoming_edges(node))

    def outgoing_nodes(self, node: str | AbstractNode) -> AbstractSet[Node[A, S]]:
        """Target nodes of the edges starting at `node`."""
        return ordered(self._node(edge.target) for edge in self.outgoing_edges(node))

    def incoming_edges(self, node: str | AbstractNode) -> AbstractSet[Edge[E]]:
        """Edges pointing to `node`."""
        store = self._store

        return ordered(store.edges[id] for id in store.incoming[self._node(node).id])

    def outgoing_edges(self, node: str | AbstractNode) -> AbstractSet[Edge[E]]:
        """Edges starting at `node`."""
        store = self._store

        return ordered(store.edges[id] for id in store.outgoing[self._node(node).id])

    def neighbor_nodes(self, node: str | AbstractNode) -> AbstractSet[Node[A, S]]:
        """Nodes connected to `node` via incoming or outgoing edges."""
        return ordered((*self.incoming_nodes(node), *self.outgoing_nodes(node)))

    def premise_nodes(self, scheme: str | AbstractNode) -> AbstractSet[AtomNode[A]]:
        """Atom nodes connected to `scheme` via incoming edges, i.e. its premises.

        Schemes targeting the scheme (e.g. undercutters) are not premises.
        """
        return ordered(
            node for node in self.incoming_nodes(scheme) if isinstance(node, AtomNode)
        )

    def incoming_atom_nodes(self, node: str | AbstractNode) -> AbstractSet[AtomNode[A]]:
        """Find the closest atom nodes connected to `node` via incoming edges."""
        return self._neighbor_atom_nodes(node, self.incoming_nodes)

    def outgoing_atom_nodes(self, node: str | AbstractNode) -> AbstractSet[AtomNode[A]]:
        """Find the closest atom nodes connected to `node` via outgoing edges."""
        return self._neighbor_atom_nodes(node, self.outgoing_nodes)

    def _neighbor_atom_nodes(
        self,
        node: str | AbstractNode,
        neighbors: Callable[[AbstractNode], AbstractSet[Node[A, S]]],
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
        *,
        max_levels: int | None = 1,
        node_type: type[AbstractNode] = AbstractNode,
    ) -> dict[Node[A, S], int]:
        """Find the nodes `n` levels below the ancestors at the shortest up-distance `n` of `node`.

        Up follows outgoing edges, each sibling gets its smallest `n`, `node` itself is excluded.

        Args:
            node: Node object or id that is part of the graph.
            max_levels: Maximum number of levels to go up, unlimited if None.
            node_type: Only include siblings of this type.

        Examples:
            >>> from arguebuf import AtomNode, GraphDraft, SchemeNode
            >>> g = GraphDraft()
            >>> claim, scheme = AtomNode("Claim"), SchemeNode()
            >>> p1, p2 = AtomNode("Premise 1"), AtomNode("Premise 2")
            >>> for n in (claim, scheme, p1, p2):
            ...     g.add_node(n)
            >>> g.connect([p1, p2], scheme, claim)
            >>> g.sibling_node_distances(p1) == {p2: 1}
            True
        """
        start = self._node(node)
        distances: dict[Node[A, S], int] = {}
        visited: set[AbstractNode] = {start}
        ancestors: AbstractSet[Node[A, S]] = {start}
        level = 0

        while ancestors and (max_levels is None or level < max_levels):
            level += 1
            ancestors = ordered(
                parent
                for ancestor in ancestors
                for parent in self.outgoing_nodes(ancestor)
                if parent not in visited
            )
            visited.update(ancestors)
            descendants = ancestors

            for _ in range(level):
                descendants = ordered(
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
        *,
        max_levels: int | None = 1,
        node_type: type[AbstractNode] = AbstractNode,
    ) -> AbstractSet[Node[A, S]]:
        """Find the sibling nodes of a node, see `sibling_node_distances`."""
        return self.sibling_node_distances(
            node, max_levels=max_levels, node_type=node_type
        ).keys()

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

    def check_link(
        self, source: str | AbstractNode, target: str | AbstractNode
    ) -> Issue | None:
        """The issue that prevents `GraphDraft.link` from connecting the nodes, if any.

        Nothing is raised, e.g. to validate a connection while it is drawn.

        Examples:
            >>> from arguebuf import AtomNode, GraphDraft
            >>> g = GraphDraft()
            >>> for node in (AtomNode("P", id="p"), AtomNode("C", id="c")):
            ...     g.add_node(node)
            >>> g.check_link("p", "c") is None
            True
            >>> g.check_link("p", "p").code
            'self-loop'
        """
        source_id, target_id = id_of(source), id_of(target)
        atoms = self._store.atom_nodes

        # atom nodes are connected through a new scheme node, which only rules out self-loops
        if source_id in atoms and target_id in atoms and source_id != target_id:
            return None

        return edge_issue(self._store, source_id, target_id)

    def atom_relations(self) -> list[AtomRelation[A, S]]:
        """Connections between atom nodes via scheme nodes, e.g. to render a graph without schemes.

        Each pair of atom nodes is listed once with the first scheme node connecting them,
        atom nodes are not related to themselves.

        Examples:
            >>> from arguebuf import AtomNode, GraphDraft, SchemeNode
            >>> g = GraphDraft()
            >>> for node in (AtomNode("P", id="p"), SchemeNode(id="s"), AtomNode("C", id="c")):
            ...     g.add_node(node)
            >>> g.connect(["p"], "s", "c")
            >>> [(r.source.id, r.target.id, r.scheme.id) for r in g.atom_relations()]
            [('p', 'c', 's')]
        """
        relations: dict[tuple[str, str], AtomRelation[A, S]] = {}

        for scheme in self._store.scheme_nodes.values():
            targets = self.outgoing_atom_nodes(scheme)

            for source in self.incoming_atom_nodes(scheme):
                for target in targets:
                    key = (source.id, target.id)

                    if source.id != target.id and key not in relations:
                        relations[key] = AtomRelation(source, target, scheme)

        return list(relations.values())

    def annotations(self, resource: str | Resource[R]) -> list[Annotation[A]]:
        """The atom nodes whose references are anchored in the resource, sorted by their position.

        References whose text is not found at their offset are skipped,
        see `GraphDraft.relocate_references`.

        Args:
            resource: Resource or id that is part of the graph.

        Examples:
            >>> from arguebuf import AtomNode, GraphDraft, Reference, Resource
            >>> g = GraphDraft()
            >>> g.add_resource(Resource("Cats are pets.", id="r"))
            >>> g.add_node(AtomNode("Pets", id="a", reference=Reference("pets", resource="r", offset=9)))
            >>> g.add_node(AtomNode("Cats", id="b", reference=Reference("Cats", resource="r", offset=0)))
            >>> [(item.node.id, item.start, item.end) for item in g.annotations("r")]
            [('b', 0, 4), ('a', 9, 13)]
        """
        current = get(self._store.resources, resource, "Resource")
        annotations = [
            Annotation(node, *span)
            for node in self._store.atom_nodes.values()
            if node.reference
            and node.reference.resource == current.id
            and (span := node.reference.span(current.text))
        ]

        return sorted(annotations, key=lambda item: (item.start, item.end))

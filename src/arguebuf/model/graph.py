import dataclasses
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, Self, Unpack, overload

from arguebuf.locate import DEFAULT_THRESHOLD
from arguebuf.model._graph_references import relocate_references
from arguebuf.model._graph_removal import (
    remove_branches,
    remove_elements,
    remove_participant,
    remove_resource,
)
from arguebuf.model._graph_store import GraphStore, touched
from arguebuf.model._graph_validation import get, vacate, validate_edge, validate_node
from arguebuf.model._graph_view import Annotation, AtomRelation, GraphView
from arguebuf.model.analyst import Analyst, AnalystChanges
from arguebuf.model.edge import Edge, EdgeChanges
from arguebuf.model.issue import GraphError, Issue, fail
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import (
    AbstractNode,
    AtomChanges,
    AtomNode,
    AtomOrSchemeNode,
    SchemeChanges,
    SchemeNode,
)
from arguebuf.model.participant import Participant, ParticipantChanges
from arguebuf.model.resource import Resource, ResourceChanges
from arguebuf.model.scheme import Scheme
from arguebuf.model.userdata import JSON_OBJECT, JsonObject, own
from arguebuf.model.utils import id_of, uuid

__all__ = (
    "AnalystChanges",
    "Annotation",
    "AtomChanges",
    "AtomRelation",
    "EdgeChanges",
    "Graph",
    "GraphDraft",
    "ParticipantChanges",
    "ResourceChanges",
    "SchemeChanges",
)


# lazily evaluated, so the overloads below can specialize the class they belong to
type _JsonGraph = _GraphBase
# lazily evaluated, so `Graph` can reference itself and the class defined after it
type _Draft[A, S, E, G, R, P, N] = GraphDraft[A, S, E, G, R, P, N]
type _Frozen[A, S, E, G, R, P, N] = Graph[A, S, E, G, R, P, N]


class _GraphBase[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
](GraphView[A, S, E, R, P, N]):
    """Construction of the fields that `Graph` and `GraphDraft` declare."""

    __slots__ = ()

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
        self,
        name: str | None = None,
        *,
        metadata: Metadata | None = None,
        userdata: object = JSON_OBJECT,
    ) -> None:
        self._assign(name, metadata or Metadata(), own(userdata), GraphStore())

    @classmethod
    def _of(
        cls,
        name: str | None,
        metadata: Metadata,
        userdata: G,
        store: GraphStore[A, S, E, R, P, N],
    ) -> Self:
        """Create a graph from its fields without copying them."""
        graph = cls.__new__(cls)
        graph._assign(name, metadata, userdata, store)

        return graph

    def _assign(
        self,
        name: str | None,
        metadata: Metadata,
        userdata: object,
        store: GraphStore[A, S, E, R, P, N],
    ) -> None:
        # frozen dataclasses can only be initialized via object.__setattr__
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "userdata", userdata)
        object.__setattr__(self, "_store", store)


@dataclass(slots=True, frozen=True, eq=False, init=False)
class Graph[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
](_GraphBase[A, S, E, G, R, P, N]):
    """Immutable argument graph consisting of atom nodes, scheme nodes, and edges.

    A graph never changes, so it can be shared freely, e.g. in an undo history.
    Changes are made on the `GraphDraft` returned by `draft`, whose `freeze` returns the new graph.
    Both take constant time, since graphs and drafts share their elements, userdata, and containers,
    and a draft clones a container only when it changes it first.
    Userdata is shared as is, so replace it via a draft instead of changing it in place.
    Elements reference each other by id.
    The type parameters are the userdata types of atom nodes, scheme nodes, edges,
    the graph, resources, participants, and analysts (see `arguebuf.Codecs`).

    Attributes:
        name: Optional name, used for example as file name by `arguebuf.dump.file`.
        metadata: Creation and modification times of the graph.
        userdata: Userdata of the graph.

    Examples:
        >>> empty = Graph("Example")
        >>> draft = empty.draft()
        >>> draft.add_node(AtomNode("Claim", id="c"))
        >>> graph = draft.freeze()
        >>> len(empty.nodes), len(graph.nodes), graph.name
        (0, 1, 'Example')
        >>> graph.name = "Changed"
        Traceback (most recent call last):
        dataclasses.FrozenInstanceError: ...
    """

    name: str | None
    metadata: Metadata = field(repr=False)
    userdata: G = field(repr=False)
    _store: GraphStore[A, S, E, R, P, N] = field(repr=False)

    def draft(self) -> _Draft[A, S, E, G, R, P, N]:
        """Start changing the graph, it stays unchanged itself."""
        return GraphDraft[A, S, E, G, R, P, N]._of(
            self.name, self.metadata, self.userdata, self._store.fork()
        )

    def edit(
        self, recipe: Callable[[_Draft[A, S, E, G, R, P, N]], Any]
    ) -> _Frozen[A, S, E, G, R, P, N]:
        """The graph changed by `recipe` on a draft, like `produce` of immer.

        The draft never escapes the recipe, whose return value is ignored.
        If it raises, nothing is changed.
        Use `draft` and `GraphDraft.freeze` for edits that span several steps.

        Args:
            recipe: Function changing the draft, e.g. a lambda or a nested function.

        Returns:
            The changed graph, it shares the unchanged elements with this one.

        Examples:
            >>> g = Graph().edit(lambda d: d.add_node(AtomNode("Claim", id="c")))
            >>> def rename(draft: GraphDraft) -> None:
            ...     draft.update_atom("c", text="Renamed")
            ...     draft.major_claim = "c"
            >>> renamed = g.edit(rename)
            >>> g.atom_nodes["c"].text, renamed.atom_nodes["c"].text, renamed.major_claim
            ('Claim', 'Renamed', 'c')
        """
        draft = self.draft()
        recipe(draft)

        return draft.freeze()


@dataclass(slots=True, eq=False, init=False)
class GraphDraft[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
](_GraphBase[A, S, E, G, R, P, N]):
    """Mutable argument graph that is turned into an immutable `Graph` by `freeze`.

    It is created empty like a `Graph` or from one via `Graph.draft`.
    Its read-only, insertion-ordered collections change only via its methods.
    The `add_*` and `update_*` methods reject taken or unknown ids and unknown references,
    edges must neither be self-loops, connect two atom nodes, nor duplicate a connection.
    The `remove_*` methods unset or remove all references to the removed element.
    Violations raise a `GraphError` whose `issue` describes the cause.

    Attributes:
        name: Optional name, used for example as file name by `arguebuf.dump.file`.
        metadata: Creation and modification times of the graph.
        userdata: Userdata of the graph.
    """

    name: str | None
    metadata: Metadata = field(repr=False)
    userdata: G = field(repr=False)
    _store: GraphStore[A, S, E, R, P, N] = field(repr=False)

    def freeze(self) -> Graph[A, S, E, G, R, P, N]:
        """The current state as immutable graph, the draft can still be changed afterwards.

        Examples:
            >>> draft = GraphDraft()
            >>> draft.add_node(AtomNode("Claim", id="c"))
            >>> graph = draft.freeze()
            >>> draft.update_atom("c", text="Changed")
            >>> graph.nodes["c"].text, draft.freeze().nodes["c"].text
            ('Claim', 'Changed')
        """
        store = self._store
        # the graph takes the containers, so the draft clones them before writing
        self._store = store.fork()

        return Graph[A, S, E, G, R, P, N]._of(
            self.name, self.metadata, self.userdata, store
        )

    @GraphView.major_claim.setter
    def major_claim(self, value: str | AbstractNode | None) -> None:
        if value is None:
            self._store.major_claim = None

            return

        node = self._node(value)

        if not isinstance(node, AtomNode):
            fail(
                "invalid-major-claim",
                f"Only atom nodes can be the major claim, '{node.id}' is a scheme node.",
                [node.id],
            )

        self._store.major_claim = node.id

    def add_node(self, node: AtomOrSchemeNode[A, S]) -> None:
        """Add a node to the graph.

        Args:
            node: Node object that is not already part of the graph.
                The participant and the resource referenced by an atom node
                must already be part of the graph.

        Examples:
            >>> g = GraphDraft()
            >>> g.add_node(AtomNode("Exemplary node"))
            >>> len(g.nodes)
            1
            >>> g.add_node(SchemeNode())
            >>> len(g.nodes)
            2
            >>> g.add_node(AtomNode("Node", participant="unknown"))
            Traceback (most recent call last):
            arguebuf.model.issue.GraphError: ...
        """
        validate_node(self._store, node)
        vacate(self._store.nodes, node, "Node")
        self._store.insert_node(node)

    def remove_node(self, node: str | AbstractNode) -> list[str]:
        """Remove a node together with its edges and all references to it.

        The major claim is unset if it is the node
        and an atom node is removed from the premise descriptors of all scheme nodes.
        Scheme nodes that are left without a premise or a conclusion are removed as well,
        recursively.

        Args:
            node: Node object or id that is part of the graph.

        Returns:
            The ids of all removed nodes and edges.

        Examples:
            >>> g = GraphDraft()
            >>> for n in (AtomNode("P", id="p"), SchemeNode(id="s"), AtomNode("C", id="c")):
            ...     g.add_node(n)
            >>> g.connect(["p"], "s", "c")
            >>> g.major_claim = "c"
            >>> len(g.remove_node("p"))
            4
            >>> list(g.nodes), len(g.edges), g.major_claim
            (['c'], 0, 'c')
            >>> g.remove_node("p")
            Traceback (most recent call last):
            arguebuf.model.issue.GraphError: ...
        """
        return self.remove_elements([self._node(node).id])

    def remove_elements(self, ids: Iterable[str]) -> list[str]:
        """Remove nodes, edges, resources, and participants by their ids at once.

        Removing a node cascades like `remove_node`,
        ids removed by such a cascade earlier in the same call are skipped.
        All ids are checked before anything is removed.

        Returns:
            The ids of all removed elements, including those of the cascades.

        Examples:
            >>> g = GraphDraft()
            >>> for n in (AtomNode("P", id="p"), SchemeNode(id="s"), AtomNode("C", id="c")):
            ...     g.add_node(n)
            >>> g.connect(["p"], "s", "c")
            >>> len(g.remove_elements(["p", "s"]))
            4
            >>> list(g.nodes)
            ['c']
            >>> g.remove_elements(["c", "unknown"])
            Traceback (most recent call last):
            arguebuf.model.issue.GraphError: ...
        """
        return remove_elements(self._store, ids)

    def update_atom(
        self, node: str | AtomNode[A], /, **changes: Unpack[AtomChanges[A]]
    ) -> None:
        """Change fields of an atom node, keeping its edges.

        The participant and the resource of the reference must be part of the graph.

        Examples:
            >>> g = GraphDraft()
            >>> g.add_node(AtomNode("Old", id="a"))
            >>> g.update_atom("a", text="New")
            >>> g.nodes["a"].text
            'New'
        """
        current = get(self._store.atom_nodes, node, "Atom node")
        changes.setdefault("metadata", touched(current.metadata))
        updated = dataclasses.replace(current, **changes)
        validate_node(self._store, updated)
        self._store.replace_node(updated)

    def update_scheme(
        self, node: str | SchemeNode[S], /, **changes: Unpack[SchemeChanges[S]]
    ) -> None:
        """Change fields of a scheme node, keeping its edges.

        Examples:
            >>> g = GraphDraft()
            >>> g.add_node(SchemeNode(id="s"))
            >>> g.update_scheme("s", userdata={"note": "Checked"})
            >>> g.nodes["s"].userdata
            {'note': 'Checked'}
        """
        current = get(self._store.scheme_nodes, node, "Scheme node")
        changes.setdefault("metadata", touched(current.metadata))
        self._store.replace_node(dataclasses.replace(current, **changes))

    def add_edge(self, edge: Edge[E]) -> None:
        """Add an edge between two nodes of the graph.

        Args:
            edge: Edge object that is not part of the graph.
                Its source and target must be nodes of the graph.

        Examples:
            >>> g = GraphDraft()
            >>> n1 = AtomNode("Premise")
            >>> n2 = SchemeNode()
            >>> g.add_node(n1)
            >>> g.add_node(n2)
            >>> g.add_edge(Edge(n1.id, n2.id))
            >>> len(g.edges)
            1
            >>> g.add_edge(Edge(n2.id, "unknown"))
            Traceback (most recent call last):
            arguebuf.model.issue.GraphError: ...
        """
        vacate(self._store.edges, edge, "Edge")
        validate_edge(self._store, edge)
        self._store.insert_edge(edge)

    def connect(
        self,
        premises: Iterable[str | AbstractNode],
        scheme: str | SchemeNode[S],
        conclusion: str | AbstractNode,
        edge_userdata: Callable[[], E] = dict,
    ) -> None:
        """Connect the premises to the conclusion via the scheme node, all part of the graph.

        Args:
            premises: Nodes or ids of the premises.
            scheme: Scheme node or id connecting them.
            conclusion: Node or id of the conclusion.
            edge_userdata: Creates the userdata of each new edge,
                it can only be omitted for JSON object userdata.

        Examples:
            >>> g = GraphDraft()
            >>> for node in (AtomNode("P", id="p"), SchemeNode(id="s"), AtomNode("C", id="c")):
            ...     g.add_node(node)
            >>> g.connect(["p"], "s", "c")
            >>> [node.id for node in g.outgoing_atom_nodes("p")]
            ['c']
        """
        link = lambda source, target: self.add_edge(
            Edge(id_of(source), id_of(target), userdata=edge_userdata())
        )

        for premise in premises:
            link(premise, scheme)

        link(scheme, conclusion)

    def link(
        self,
        source: str | AbstractNode,
        target: str | AbstractNode,
        *,
        scheme: Scheme | None = None,
        edge_userdata: Callable[[], E] = dict,
        scheme_userdata: Callable[[], S] = dict,
    ) -> SchemeNode[S] | None:
        """Connect two nodes of the graph, atom nodes through a new scheme node.

        Args:
            source: Node or id the link starts at.
            target: Node or id the link ends at.
            scheme: Scheme of the new scheme node, untyped by default.
            edge_userdata: Creates the userdata of each new edge,
                it can only be omitted for JSON object userdata.
            scheme_userdata: Creates the userdata of the new scheme node,
                it can only be omitted for JSON object userdata.

        Returns:
            The inserted scheme node or None if the nodes are connected directly.

        Raises:
            GraphError: The issue returned by `check_link`.

        Examples:
            >>> from arguebuf import Attack
            >>> g = GraphDraft()
            >>> for node in (AtomNode("P", id="p"), AtomNode("C", id="c")):
            ...     g.add_node(node)
            >>> node = g.link("p", "c", scheme=Attack.DEFAULT)
            >>> node is not None and node.scheme
            <Attack.DEFAULT: 'Default'>
            >>> [node.id for node in g.outgoing_atom_nodes("p")]
            ['c']
            >>> g.link("p", "p")
            Traceback (most recent call last):
            arguebuf.model.issue.GraphError: Node 'p' cannot be connected to itself.
        """
        source_id, target_id = id_of(source), id_of(target)

        if (found := self.check_link(source_id, target_id)) is not None:
            raise GraphError(found)

        if source_id in self._store.atom_nodes and target_id in self._store.atom_nodes:
            node = SchemeNode(scheme, userdata=scheme_userdata(), id=uuid())
            self.add_node(node)
            self.connect([source_id], node, target_id, edge_userdata)

            return node

        self.add_edge(Edge(source_id, target_id, userdata=edge_userdata()))

        return None

    def update_edge(
        self, edge: str | Edge[E], /, **changes: Unpack[EdgeChanges[E]]
    ) -> None:
        """Change the metadata or userdata of an edge."""
        current = get(self._store.edges, edge, "Edge")
        changes.setdefault("metadata", touched(current.metadata))
        self._store.own_edges()[current.id] = dataclasses.replace(current, **changes)

    def remove_edge(self, edge: str | Edge[E]) -> None:
        """Remove an edge.

        Args:
            edge: Edge object or id that is part of the graph.

        Examples:
            >>> g = GraphDraft()
            >>> n1, n2 = AtomNode("Node1"), SchemeNode()
            >>> g.add_node(n1)
            >>> g.add_node(n2)
            >>> e = Edge(n1.id, n2.id)
            >>> g.add_edge(e)
            >>> g.remove_edge(e)
            >>> len(g.edges), len(g.nodes)
            (0, 2)
        """
        self._store.delete_edge(get(self._store.edges, edge, "Edge").id)

    def add_resource(self, resource: Resource[R]) -> None:
        """Add a resource.

        Examples:
            >>> g = GraphDraft()
            >>> g.add_resource(Resource("Resource1"))
            >>> len(g.resources)
            1
        """
        vacate(self._store.resources, resource, "Resource")
        self._store.own_resources()[resource.id] = resource

    def update_resource(
        self,
        resource: str | Resource[R],
        /,
        *,
        threshold: float = DEFAULT_THRESHOLD,
        **changes: Unpack[ResourceChanges[R]],
    ) -> list[Issue]:
        """Change fields of a resource.

        If its text changes, the references to it are re-anchored, see `relocate_references`.

        Args:
            resource: Resource or id that is part of the graph.
            threshold: Minimal similarity of re-anchored references, see `arguebuf.locate`.
            changes: New values of the fields.

        Returns:
            The warnings of re-anchoring the references.

        Examples:
            >>> from arguebuf import Reference
            >>> g = GraphDraft()
            >>> g.add_resource(Resource("Cats are pets.", id="r"))
            >>> g.add_node(AtomNode("Pets", id="a", reference=Reference("pets", resource="r", offset=9)))
            >>> g.update_resource("r", text="Indeed, cats are pets.")
            [Issue(code='reference-mismatch', ...)]
            >>> g.atom_nodes["a"].reference.offset
            17
        """
        current = get(self._store.resources, resource, "Resource")
        changes.setdefault("metadata", touched(current.metadata))
        updated = dataclasses.replace(current, **changes)
        self._store.own_resources()[updated.id] = updated

        if updated.text == current.text:
            return []

        return self.relocate_references(resource=updated.id, threshold=threshold)

    def remove_resource(self, resource: str | Resource[R]) -> None:
        """Remove a resource and unset it in the references of all atom nodes.

        Examples:
            >>> g = GraphDraft()
            >>> r1 = Resource("Resource1")
            >>> g.add_resource(r1)
            >>> g.remove_resource(r1)
            >>> len(g.resources)
            0
        """
        remove_resource(
            self._store, get(self._store.resources, resource, "Resource").id
        )

    def clean_resources(self) -> None:
        """Remove resources that are not referenced by any node."""
        used = {
            node.reference.resource
            for node in self._store.atom_nodes.values()
            if node.reference and node.reference.resource
        }
        resources = self._store.own_resources()

        for resource_id in resources.keys() - used:
            del resources[resource_id]

    def add_participant(self, participant: Participant[P]) -> None:
        """Add a participant.

        Examples:
            >>> g = GraphDraft()
            >>> g.add_participant(Participant("Participant1"))
            >>> len(g.participants)
            1
        """
        vacate(self._store.participants, participant, "Participant")
        self._store.own_participants()[participant.id] = participant

    def update_participant(
        self,
        participant: str | Participant[P],
        /,
        **changes: Unpack[ParticipantChanges[P]],
    ) -> None:
        """Change fields of a participant."""
        current = get(self._store.participants, participant, "Participant")
        changes.setdefault("metadata", touched(current.metadata))
        self._store.own_participants()[current.id] = dataclasses.replace(
            current, **changes
        )

    def remove_participant(self, participant: str | Participant[P]) -> None:
        """Remove a participant and unset it for all its atom nodes.

        Examples:
            >>> g = GraphDraft()
            >>> p1 = Participant("Participant1")
            >>> g.add_participant(p1)
            >>> g.remove_participant(p1)
            >>> len(g.participants)
            0
        """
        remove_participant(
            self._store, get(self._store.participants, participant, "Participant").id
        )

    def clean_participants(self) -> None:
        """Remove participants that are not assigned to any node."""
        used = {
            node.participant
            for node in self._store.atom_nodes.values()
            if node.participant
        }
        participants = self._store.own_participants()

        for participant_id in participants.keys() - used:
            del participants[participant_id]

    def add_analyst(self, analyst: Analyst[N]) -> None:
        """Add an analyst.

        Examples:
            >>> g = GraphDraft()
            >>> g.add_analyst(Analyst("Name"))
            >>> len(g.analysts)
            1
        """
        vacate(self._store.analysts, analyst, "Analyst")
        self._store.own_analysts()[analyst.id] = analyst

    def update_analyst(
        self, analyst: str | Analyst[N], /, **changes: Unpack[AnalystChanges[N]]
    ) -> None:
        """Change fields of an analyst."""
        current = get(self._store.analysts, analyst, "Analyst")
        changes.setdefault("metadata", touched(current.metadata))
        self._store.own_analysts()[current.id] = dataclasses.replace(current, **changes)

    def remove_analyst(self, analyst: str | Analyst[N]) -> None:
        """Remove an analyst.

        Examples:
            >>> g = GraphDraft()
            >>> a1 = Analyst("Name")
            >>> g.add_analyst(a1)
            >>> g.remove_analyst(a1)
            >>> len(g.analysts)
            0
        """
        del self._store.own_analysts()[get(self._store.analysts, analyst, "Analyst").id]

    def relocate_references(
        self, *, resource: str | None = None, threshold: float = DEFAULT_THRESHOLD
    ) -> list[Issue]:
        """Re-anchor references whose text is not found at their offset in their resource.

        This repairs references after their resource has been edited
        and fills in missing offsets.
        A reference is moved to the most similar span near its old offset,
        if there is none, its offset is unset.

        Args:
            resource: Only relocate the references to the resource with this id.
            threshold: Minimal similarity of the new span, see `arguebuf.locate`.

        Returns:
            A warning for each changed reference.
        """
        return relocate_references(self._store, resource=resource, threshold=threshold)

    def remove_empty_scheme_branches(self) -> list[str]:
        """Remove scheme nodes without a scheme together with their descendants.

        Returns:
            The ids of all removed nodes and edges.
        """
        return remove_branches(
            self._store,
            [node for node in self._store.scheme_nodes.values() if node.scheme is None],
        )

    def remove_branch(self, element: str | AbstractNode | Edge[E]) -> list[str]:
        """Remove an element and all its descendants from the graph.

        If the element is a string, it is interpreted as the id of a node,
        an edge is interpreted as its source node.
        Descendants are the nodes reachable via incoming edges.

        Returns:
            The ids of all removed nodes and edges.
        """
        return remove_branches(
            self._store,
            [self._node(element.source if isinstance(element, Edge) else element)],
        )

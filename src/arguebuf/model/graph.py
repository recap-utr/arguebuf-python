import dataclasses
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Self, Unpack, overload

from arguebuf.locate import DEFAULT_THRESHOLD
from arguebuf.model._graph_references import relocate_references
from arguebuf.model._graph_removal import (
    remove_branch,
    remove_elements,
    remove_participant,
    remove_resource,
)
from arguebuf.model._graph_store import touched
from arguebuf.model._graph_validation import get, vacate, validate_edge, validate_node
from arguebuf.model._graph_view import AtomRelation, GraphView
from arguebuf.model.analyst import Analyst, AnalystChanges
from arguebuf.model.edge import Edge, EdgeChanges
from arguebuf.model.issue import Issue
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
from arguebuf.model.userdata import JSON_OBJECT, JsonObject, own
from arguebuf.model.utils import id_of, uuid

__all__ = (
    "AnalystChanges",
    "AtomChanges",
    "AtomRelation",
    "EdgeChanges",
    "Graph",
    "ParticipantChanges",
    "ResourceChanges",
    "SchemeChanges",
)


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
](GraphView[A, S, E, R, P, N]):
    """Argument graph consisting of atom nodes, scheme nodes, and edges.

    Its read-only, insertion-ordered collections change only via its methods.
    Elements reference each other by id.
    The `add_*` and `update_*` methods reject taken or unknown ids and unknown references,
    edges must neither be self-loops, connect two atom nodes, nor duplicate a connection.
    The `remove_*` methods unset or remove all references to the removed element.
    Violations raise a `GraphError` whose `issue` describes the cause.
    All elements are frozen, so `copy.copy` copies the structure of a graph cheaply
    while sharing its elements and userdata.
    The type parameters are the userdata types of atom nodes, scheme nodes, edges,
    the graph, resources, participants, and analysts (see `arguebuf.Codecs`).

    Attributes:
        name: Optional name, used for example as file name by `arguebuf.dump.file`.
    """

    name: str | None
    metadata: Metadata = field(repr=False)
    userdata: G = field(repr=False)

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
        GraphView.__init__(self)

    def copy(self) -> Self:
        """Copy the structure of the graph, sharing its frozen elements and userdata.

        This is cheap, so changes can be made on a copy while the original stays intact.
        `copy.copy(graph)` does the same, `copy.deepcopy(graph)` copies the userdata as well.

        Examples:
            >>> g = Graph()
            >>> g.add_node(AtomNode("Claim", id="c"))
            >>> gc = g.copy()
            >>> gc.update_atom("c", text="Changed")
            >>> g.nodes["c"].text, gc.nodes["c"].text
            ('Claim', 'Changed')
        """
        clone = type(self).__new__(type(self))
        clone.name = self.name
        clone.metadata = self.metadata
        clone.userdata = self.userdata
        # all containers are shared now, so both graphs clone them before writing
        clone._store = self._store.fork()

        return clone

    def __copy__(self) -> Self:
        """Copy the structure of the graph, see `Graph.copy`."""
        return self.copy()

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
            >>> g.add_node(AtomNode("Node", participant="unknown"))
            Traceback (most recent call last):
            arguebuf.model.issue.GraphError: ...
        """
        validate_node(self._store, node)
        vacate(self._store.nodes, node, "Node")
        self._store.insert_node(node)

    def remove_node(self, node: str | AbstractNode) -> None:
        """Remove a node together with its edges and all references to it.

        The major claim is unset if it is the node
        and an atom node is removed from the premise descriptors of all scheme nodes.
        Scheme nodes that are left without a premise or a conclusion are removed as well,
        recursively.

        Args:
            node: Node object or id that is part of the graph.

        Examples:
            >>> g = Graph()
            >>> for n in (AtomNode("P", id="p"), SchemeNode(id="s"), AtomNode("C", id="c")):
            ...     g.add_node(n)
            >>> g.connect(["p"], "s", "c")
            >>> g.major_claim = "c"
            >>> g.remove_node("p")
            >>> list(g.nodes), len(g.edges), g.major_claim
            (['c'], 0, 'c')
            >>> g.remove_node("p")
            Traceback (most recent call last):
            arguebuf.model.issue.GraphError: ...
        """
        self.remove_elements([self._node(node).id])

    def remove_elements(self, ids: Iterable[str]) -> None:
        """Remove nodes, edges, resources, and participants by their ids at once.

        Removing a node cascades like `remove_node`,
        ids removed by such a cascade earlier in the same call are skipped.
        All ids are checked before anything is removed.

        Examples:
            >>> g = Graph()
            >>> for n in (AtomNode("P", id="p"), SchemeNode(id="s"), AtomNode("C", id="c")):
            ...     g.add_node(n)
            >>> g.connect(["p"], "s", "c")
            >>> g.remove_elements(["p", "s"])
            >>> list(g.nodes)
            ['c']
            >>> g.remove_elements(["c", "unknown"])
            Traceback (most recent call last):
            arguebuf.model.issue.GraphError: ...
        """
        remove_elements(self._store, ids)

    def update_atom(self, node: str | AtomNode[A], /, **changes: Unpack[AtomChanges[A]]) -> None:
        """Change fields of an atom node, keeping its edges.

        The participant and the resource of the reference must be part of the graph.

        Examples:
            >>> g = Graph()
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
            >>> g = Graph()
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
            >>> g = Graph()
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
            >>> g = Graph()
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
        edge_userdata: Callable[[], E] = dict,
        scheme_userdata: Callable[[], S] = dict,
    ) -> SchemeNode[S] | None:
        """Connect two nodes of the graph, atom nodes through a new untyped scheme node.

        Args:
            source: Node or id the link starts at.
            target: Node or id the link ends at.
            edge_userdata: Creates the userdata of each new edge,
                it can only be omitted for JSON object userdata.
            scheme_userdata: Creates the userdata of the new scheme node,
                it can only be omitted for JSON object userdata.

        Returns:
            The inserted scheme node or None if the nodes are connected directly.

        Examples:
            >>> g = Graph()
            >>> for node in (AtomNode("P", id="p"), AtomNode("C", id="c")):
            ...     g.add_node(node)
            >>> scheme = g.link("p", "c")
            >>> scheme is not None and scheme.scheme is None
            True
            >>> [node.id for node in g.outgoing_atom_nodes("p")]
            ['c']
        """
        source_id, target_id = id_of(source), id_of(target)

        if source_id in self._store.atom_nodes and target_id in self._store.atom_nodes:
            scheme = SchemeNode(userdata=scheme_userdata(), id=uuid())
            self.add_node(scheme)
            self.connect([source_id], scheme, target_id, edge_userdata)

            return scheme

        self.add_edge(Edge(source_id, target_id, userdata=edge_userdata()))

        return None

    def update_edge(self, edge: str | Edge[E], /, **changes: Unpack[EdgeChanges[E]]) -> None:
        """Change the metadata or userdata of an edge."""
        current = get(self._store.edges, edge, "Edge")
        changes.setdefault("metadata", touched(current.metadata))
        self._store.own_edges()[current.id] = dataclasses.replace(current, **changes)

    def remove_edge(self, edge: str | Edge[E]) -> None:
        """Remove an edge.

        Args:
            edge: Edge object or id that is part of the graph.

        Examples:
            >>> g = Graph()
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
            >>> g = Graph()
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
            >>> g = Graph()
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
            >>> g = Graph()
            >>> r1 = Resource("Resource1")
            >>> g.add_resource(r1)
            >>> g.remove_resource(r1)
            >>> len(g.resources)
            0
        """
        remove_resource(self._store, get(self._store.resources, resource, "Resource").id)

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
            >>> g = Graph()
            >>> g.add_participant(Participant("Participant1"))
            >>> len(g.participants)
            1
        """
        vacate(self._store.participants, participant, "Participant")
        self._store.own_participants()[participant.id] = participant

    def update_participant(
        self, participant: str | Participant[P], /, **changes: Unpack[ParticipantChanges[P]]
    ) -> None:
        """Change fields of a participant."""
        current = get(self._store.participants, participant, "Participant")
        changes.setdefault("metadata", touched(current.metadata))
        self._store.own_participants()[current.id] = dataclasses.replace(current, **changes)

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
        remove_participant(
            self._store, get(self._store.participants, participant, "Participant").id
        )

    def clean_participants(self) -> None:
        """Remove participants that are not assigned to any node."""
        used = {node.participant for node in self._store.atom_nodes.values() if node.participant}
        participants = self._store.own_participants()

        for participant_id in participants.keys() - used:
            del participants[participant_id]

    def add_analyst(self, analyst: Analyst[N]) -> None:
        """Add an analyst.

        Examples:
            >>> g = Graph()
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
        self._store.own_analysts()[current.id] = dataclasses.replace(current, **changes)

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

    def remove_empty_scheme_branches(self) -> None:
        """Remove scheme nodes without a scheme together with their descendants."""
        empty_schemes = [
            node for node in self._store.scheme_nodes.values() if node.scheme is None
        ]

        for scheme_node in empty_schemes:
            if scheme_node.id in self._store.scheme_nodes:
                self.remove_branch(scheme_node)

    def remove_branch(self, element: str | AbstractNode | Edge[E]) -> None:
        """Remove an element and all its descendants from the graph.

        If the element is a string, it is interpreted as the id of a node,
        an edge is interpreted as its source node.
        Descendants are the nodes reachable via incoming edges.
        """
        remove_branch(
            self._store, self._node(element.source if isinstance(element, Edge) else element)
        )

from __future__ import absolute_import, annotations

import itertools
import logging
import typing as t

from arguebuf.models.analyst import Analyst
from arguebuf.models.edge import Edge
from arguebuf.models.metadata import Metadata
from arguebuf.models.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.models.participant import Participant
from arguebuf.models.resource import Resource
from arguebuf.models.typing import TextType
from arguebuf.models.userdata import Userdata
from arguebuf.services import traversal, utils
from arguebuf.services.utils import ImmutableDict, ImmutableSet

log = logging.getLogger(__name__)


# noinspection PyProtectedMember
class Graph(t.Generic[TextType]):
    """Graph in AIF format.

    No attribute is mandatory.
    All nodes and edges attributes are read-only.
    """

    __slots__ = (
        "name",
        "_nodes",
        "_atom_nodes",
        "_scheme_nodes",
        "_edges",
        "_incoming_nodes",
        "_incoming_edges",
        "_outgoing_nodes",
        "_outgoing_edges",
        "_major_claim",
        "_resources",
        "_participants",
        "_analysts",
        "metadata",
        "userdata",
        "library_version",
        "schema_version",
    )

    name: str
    _nodes: ImmutableDict[str, AbstractNode]
    _atom_nodes: ImmutableDict[str, AtomNode]
    _scheme_nodes: ImmutableDict[str, SchemeNode]
    _edges: ImmutableDict[str, Edge]
    _incoming_nodes: ImmutableDict[AbstractNode, ImmutableSet[AbstractNode]]
    _incoming_edges: ImmutableDict[AbstractNode, ImmutableSet[Edge]]
    _outgoing_nodes: ImmutableDict[AbstractNode, ImmutableSet[AbstractNode]]
    _outgoing_edges: ImmutableDict[AbstractNode, ImmutableSet[Edge]]
    _resources: ImmutableDict[str, Resource]
    _participants: ImmutableDict[str, Participant]
    _major_claim: t.Optional[AtomNode]
    _analysts: ImmutableDict[str, Analyst]
    library_version: t.Optional[str]
    schema_version: t.Optional[int]
    metadata: Metadata
    userdata: Userdata

    @property
    def edges(self) -> t.Mapping[str, Edge]:
        return self._edges

    @property
    def nodes(self) -> t.Mapping[str, AbstractNode]:
        return self._nodes

    @property
    def atom_nodes(self) -> t.Mapping[str, AtomNode]:
        return self._atom_nodes

    @property
    def scheme_nodes(self) -> t.Mapping[str, SchemeNode]:
        return self._scheme_nodes

    def incoming_nodes(
        self, node: t.Union[str, AbstractNode]
    ) -> t.AbstractSet[AbstractNode]:
        if isinstance(node, str):
            node = self._nodes[node]

        return self._incoming_nodes[node]

    def incoming_atom_nodes(
        self, node: t.Union[str, AbstractNode]
    ) -> t.AbstractSet[AtomNode]:
        if isinstance(node, str):
            node = self._nodes[node]

        incoming_nodes = list(self._incoming_nodes[node])
        incoming_atom_nodes: set[AtomNode] = set()

        while incoming_nodes:
            incoming_node = incoming_nodes.pop()

            if isinstance(incoming_node, AtomNode):
                incoming_atom_nodes.add(incoming_node)
            else:
                incoming_nodes.extend(self._incoming_nodes[incoming_node])

        return incoming_atom_nodes

    def outgoing_nodes(
        self, node: t.Union[str, AbstractNode]
    ) -> t.AbstractSet[AbstractNode]:
        if isinstance(node, str):
            node = self._nodes[node]

        return self._outgoing_nodes[node]

    def outgoing_atom_nodes(
        self, node: t.Union[str, AbstractNode]
    ) -> t.AbstractSet[AtomNode]:
        if isinstance(node, str):
            node = self._nodes[node]

        outgoing_nodes = list(self._outgoing_nodes[node])
        outgoing_atom_nodes: set[AtomNode] = set()

        while outgoing_nodes:
            outgoing_node = outgoing_nodes.pop()

            # If it is an Atom, just add it to our result set
            if isinstance(outgoing_node, AtomNode):
                outgoing_atom_nodes.add(outgoing_node)
            # Otherwise, add the outgoing nodes of the current node to the search path
            else:
                outgoing_nodes.extend(self._outgoing_nodes[outgoing_node])

        return outgoing_atom_nodes

    def incoming_edges(self, node: t.Union[str, AbstractNode]) -> t.AbstractSet[Edge]:
        if isinstance(node, str):
            node = self._nodes[node]

        return self._incoming_edges[node]

    def outgoing_edges(self, node: t.Union[str, AbstractNode]) -> t.AbstractSet[Edge]:
        if isinstance(node, str):
            node = self._nodes[node]

        return self._outgoing_edges[node]

    def scheme_between(
        self, premise: AtomNode, claim: AtomNode
    ) -> t.Optional[SchemeNode]:
        candidates = set(self._outgoing_nodes[premise]).intersection(
            self._incoming_nodes[claim]
        )

        if len(candidates) == 1:
            scheme = next(iter(candidates))

            if isinstance(scheme, SchemeNode):
                return scheme

        return None

    @property
    def resources(self) -> t.Mapping[str, Resource]:
        return self._resources

    @property
    def major_claim(self) -> t.Optional[AtomNode]:
        if self._major_claim:
            return self._major_claim

    @major_claim.setter
    def major_claim(self, value: t.Union[str, AtomNode, None]) -> None:
        if isinstance(value, str):
            value = self._atom_nodes[value]
        elif not (value is None or isinstance(value, AtomNode)):
            raise TypeError(utils.type_error(type(value), AtomNode))

        self._major_claim = value
        # self._metadata.update()

    @property
    def root_node(self) -> t.Optional[AtomNode]:
        """If there is a single node with no outgoing edges, return it, otherwise None"""
        candidates = self.root_nodes

        if len(candidates) == 1:
            return next(iter(candidates))

        return None

    @property
    def root_nodes(self) -> t.Set[AtomNode]:
        """Find all nodes with no outgoing edges"""
        return {
            node
            for node in self.atom_nodes.values()
            if len(self.outgoing_nodes(node)) == 0
        }

    @property
    def leaf_nodes(self) -> t.Set[AtomNode]:
        """Find all nodes with no incoming edges"""
        return {
            node
            for node in self.atom_nodes.values()
            if len(self.incoming_nodes(node)) == 0
        }

    @property
    def participants(self) -> t.Mapping[str, Participant]:
        return self._participants

    @property
    def analysts(self) -> t.Mapping[str, Analyst]:
        return self._analysts

    def __init__(self, name: t.Optional[str] = None):
        """Create a graph from scratch."""

        self.name = name or utils.uuid()
        self._nodes = ImmutableDict()
        self._atom_nodes = ImmutableDict()
        self._scheme_nodes = ImmutableDict()
        self._edges = ImmutableDict()
        self._analysts = ImmutableDict()
        self.userdata = {}
        self._resources = ImmutableDict()
        self._participants = ImmutableDict()
        self.metadata = Metadata()
        self._major_claim = None

        self._incoming_nodes = ImmutableDict()
        self._incoming_edges = ImmutableDict()
        self._outgoing_nodes = ImmutableDict()
        self._outgoing_edges = ImmutableDict()
        self.library_version = None
        self.schema_version = None

        self.__post_init__()

    def __post_init__(self):
        pass

    def __repr__(self):
        return utils.class_repr(self, [self.name])

    def add_node(self, node: AbstractNode) -> None:
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
            >>> g.add_node("Test")
            Traceback (most recent call last):
            TypeError: Expected type '<class 'arguebuf.node.Node'>', but got '<class 'str'>'. Make sure that you are passing the correct method arguments.
        """

        if not isinstance(node, AbstractNode):
            raise TypeError(utils.type_error(type(node), AbstractNode))

        if node.id in self._nodes:
            raise ValueError(utils.duplicate_key_error(self.name, node.id))

        self._nodes._store[node.id] = node

        if isinstance(node, AtomNode):
            self._atom_nodes._store[node.id] = node

            if node.participant and node.participant.id not in self._participants:
                self.add_participant(node.participant)

            if (
                node.reference
                and node.reference.resource
                and node.reference.resource.id not in self._resources
            ):
                self.add_resource(node.reference.resource)

        elif isinstance(node, SchemeNode):
            self._scheme_nodes._store[node.id] = node

        self._incoming_nodes._store[node] = ImmutableSet()
        self._incoming_edges._store[node] = ImmutableSet()
        self._outgoing_nodes._store[node] = ImmutableSet()
        self._outgoing_edges._store[node] = ImmutableSet()

    def remove_node(self, node: AbstractNode) -> None:
        """Remove a node and its corresponding edges from the graph.

        Args:
            node: Node object that is part of the graph.

        Examples:
            >>> g = Graph()
            >>> n1 = AtomNode("Node1")
            >>> n2 = SchemeNode()
            >>> e = Edge(n1, n2)
            >>> g.add_edge(e)
            >>> len(g.nodes)
            2
            >>> len(g.edges)
            1
            >>> g.remove_node(n1)
            >>> len(g.nodes)
            1
            >>> len(g.edges)
            0
            >>> g.remove_node(n1)
            Traceback (most recent call last):
            KeyError: Node not in graph.
        """

        if node.id not in self.nodes:
            raise KeyError(utils.missing_key_error(self.name, node.id))

        del self._nodes._store[node.id]

        if isinstance(node, AtomNode):
            del self._atom_nodes._store[node.id]
        elif isinstance(node, SchemeNode):
            del self._scheme_nodes._store[node.id]

        neighbor_edges = list(self._incoming_edges[node]) + list(
            self._outgoing_edges[node]
        )

        for edge in neighbor_edges:
            self.remove_edge(edge)

        del self._incoming_nodes._store[node]
        del self._incoming_edges._store[node]
        del self._outgoing_nodes._store[node]
        del self._outgoing_edges._store[node]

    def add_edge(self, edge: Edge) -> None:
        """Add an edge and its nodes (if not already added).

        Args:
            edge: Edge object that is not part of the graph.

        Examples:
            >>> g = Graph()
            >>> n1 = AtomNode("Premise")
            >>> n2 = SchemeNode()
            >>> n3 = AtomNode("Claim")
            >>> e1 = Edge(n1, n2)
            >>> e2 = Edge(n2, n3)
            >>> g.add_edge(e1)
            >>> len(g.edges)
            1
            >>> g.add_edge(e2)
            >>> len(g.edges)
            2
        """
        if not isinstance(edge, Edge):
            raise TypeError(utils.type_error(type(edge), Edge))

        if edge.id in self._edges:
            raise ValueError(utils.duplicate_key_error(self.name, edge.id))

        self._edges._store[edge.id] = edge

        if edge.source.id not in self.nodes:
            self.add_node(edge.source)

        if edge.target.id not in self.nodes:
            self.add_node(edge.target)

        self._outgoing_edges[edge.source]._store.add(edge)
        self._incoming_edges[edge.target]._store.add(edge)
        self._outgoing_nodes[edge.source]._store.add(edge.target)
        self._incoming_nodes[edge.target]._store.add(edge.source)

    def remove_edge(self, edge: Edge) -> None:
        """Remove an edge.

        Args:
            edge: Edge object that is part of the graph.

        Examples:
            >>> g = Graph()
            >>> n1 = AtomNode("Node1")
            >>> n2 = SchemeNode()
            >>> e = Edge(n1, n2)
            >>> g.add_edge(e)
            >>> len(g.edges)
            1
            >>> len(g.nodes)
            2
            >>> g.remove_edge(e)
            >>> len(g.edges)
            0
            >>> len(g.nodes)
            2
        """
        if not isinstance(edge, Edge):
            raise TypeError(utils.type_error(type(edge), Edge))

        if edge.id not in self._edges:
            raise KeyError(utils.missing_key_error(self.name, edge.id))

        del self._edges._store[edge.id]

        self._outgoing_edges[edge.source]._store.remove(edge)
        self._incoming_edges[edge.target]._store.remove(edge)
        self._outgoing_nodes[edge.source]._store.remove(edge.target)
        self._incoming_nodes[edge.target]._store.remove(edge.source)

    ##What does a Resource look like?
    def add_resource(self, resource: Resource) -> None:
        """Add a resource.

        Args:
            resource: Resource object that is not part of the graph.

        Examples:
            >>> g = Graph()
            >>> r1 = Resource("Resource1")
            >>> g.add_resource(r1)
            >>> len(g.resources)
            1
        """
        if not isinstance(resource, Resource):
            raise TypeError(utils.type_error(type(resource), Resource))

        if resource.id in self._resources:
            raise ValueError(utils.duplicate_key_error(self.name, resource.id))

        self._resources._store[resource.id] = resource

    def remove_resource(self, resource: Resource) -> None:
        """Add a resource.

        Args:
            resource: Resource object that is part of the graph.

        Examples:
            >>> g = Graph()
            >>> r1 = Resource("Resource1")
            >>> g.add_resource(r1)
            >>> len(g.resources)
            1
            >>> g.remove_resource(r1)
            >>> len(g.resources)
            0
        """
        if not isinstance(resource, Resource):
            raise TypeError(utils.type_error(type(resource), Resource))

        if resource.id not in self._resources:
            raise ValueError(utils.missing_key_error(self.name, resource.id))

        del self._resources._store[resource.id]

        for node in self._atom_nodes.values():
            if node.reference and node.reference.resource == resource:
                node.reference._resource = None
                node.reference.offset = None

    def clean_resources(self) -> None:
        """Remove resources from the graph that are used by no nodes"""

        node_resources = {
            node.reference.resource.id
            for node in self._atom_nodes.values()
            if node.reference and node.reference.resource
        }

        for resource_id in set(self._resources):
            if resource_id not in node_resources:
                del self._resources._store[resource_id]

    def add_participant(self, participant: Participant) -> None:
        """Add a resource.

        Args:
            participant: Participant object that is not part of the graph.

        Examples:
            >>> g = Graph()
            >>> p1 = Participant("Participant1")
            >>> g.add_participant(p1)
            >>> len(g.participants)
            1
        """
        if not isinstance(participant, Participant):
            raise TypeError(utils.type_error(type(participant), Participant))

        if participant.id in self._participants:
            raise ValueError(utils.duplicate_key_error(self.name, participant.id))

        self._participants._store[participant.id] = participant

    def remove_participant(self, participant: Participant) -> None:
        """Add a resource.

        Args:
            participant: Participant object that is part of the graph.

        Examples:
            >>> g = Graph()
            >>> p1 = Participant("Participant1")
            >>> g.add_participant(p1)
            >>> len(g.participants)
            1
            >>> g.remove_participant(p1)
            >>> len(g.participants)
            0
        """
        if not isinstance(participant, Participant):
            raise TypeError(utils.type_error(type(participant), Participant))

        if participant.id not in self._participants:
            raise ValueError(utils.missing_key_error(self.name, participant.id))

        del self._participants._store[participant.id]

        for node in self._atom_nodes.values():
            if node.participant == participant:
                node._participant = None

    def clean_participants(self) -> None:
        """Remove resources from the graph that are used by no nodes"""

        node_participants = {
            node.participant.id
            for node in self._atom_nodes.values()
            if node.participant
        }

        for participant in set(self._participants):
            if participant not in node_participants:
                del self._participants._store[participant]

    def add_analyst(self, analyst: Analyst) -> None:
        """Add a resource.

        Args:
            analyst: analyst object that is not part of the graph.

        Examples:
            >>> g = Graph()
            >>> p1 = Analyst("Name")
            >>> g.add_analyst(p1)
            >>> len(g.analysts)
            1
        """
        if not isinstance(analyst, Analyst):
            raise TypeError(utils.type_error(type(analyst), Analyst))

        if analyst.id in self._analysts:
            raise ValueError(utils.duplicate_key_error(self.name, analyst.id))

        self._analysts._store[analyst.id] = analyst

    def remove_analyst(self, analyst: Analyst) -> None:
        """Add a resource.

        Args:
            analyst: analyst object that is part of the graph.

        Examples:
            >>> import arguebuf
            >>> g = Graph()
            >>> p1 = Analyst("Name")
            >>> g.add_analyst(p1)
            >>> len(g.analysts)
            1
            >>> g.remove_analyst(p1)
            >>> len(g.analysts)
            0
        """
        if not isinstance(analyst, Analyst):
            raise TypeError(utils.type_error(type(analyst), Analyst))

        if analyst.id not in self._analysts:
            raise ValueError(utils.missing_key_error(self.name, analyst.id))

        del self._analysts._store[analyst.id]

    def strip_scheme_nodes(self) -> None:
        """Remove scheme nodes from graph to connect atom nodes directly

        Can be useful to analyze the structure of atom nodes
        without considering their relation types (i.e., the scheme nodes between them).
        """

        schemes = list(self._scheme_nodes.values())

        for scheme in schemes:
            for incoming, outgoing in itertools.product(
                self.incoming_atom_nodes(scheme), self.outgoing_atom_nodes(scheme)
            ):
                self.add_edge(
                    Edge(
                        incoming,
                        outgoing,
                    )
                )

            self.remove_node(scheme)

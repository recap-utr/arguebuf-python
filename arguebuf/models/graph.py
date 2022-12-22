from __future__ import absolute_import, annotations

import csv
import importlib.metadata
import itertools
import json
import logging
import re
import typing as t
import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path

import graphviz as gv
import networkx as nx
import pendulum
from arg_services.graph.v1 import graph_pb2
from google.protobuf.json_format import MessageToDict, ParseDict
from lxml import html

from arguebuf.models import Userdata
from arguebuf.models.analyst import Analyst
from arguebuf.models.edge import Edge, EdgeStyle
from arguebuf.models.metadata import Metadata
from arguebuf.models.node import AtomNode, Attack, Node, Rephrase, SchemeNode, Support
from arguebuf.models.participant import Participant
from arguebuf.models.reference import Reference
from arguebuf.models.resource import Resource
from arguebuf.schema import aif, aml, argdown_json, ova, sadface
from arguebuf.services import dt, utils
from arguebuf.services.utils import ImmutableDict, ImmutableSet

log = logging.getLogger(__name__)


class GraphFormat(str, Enum):
    ARGUEBUF = "arguebuf"
    AIF = "aif"


# noinspection PyProtectedMember
class Graph:
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
    _nodes: ImmutableDict[str, Node]
    _atom_nodes: ImmutableDict[str, AtomNode]
    _scheme_nodes: ImmutableDict[str, SchemeNode]
    _edges: ImmutableDict[str, Edge]
    _incoming_nodes: ImmutableDict[Node, ImmutableSet[Node]]
    _incoming_edges: ImmutableDict[Node, ImmutableSet[Edge]]
    _outgoing_nodes: ImmutableDict[Node, ImmutableSet[Node]]
    _outgoing_edges: ImmutableDict[Node, ImmutableSet[Edge]]
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
    def nodes(self) -> t.Mapping[str, Node]:
        return self._nodes

    @property
    def atom_nodes(self) -> t.Mapping[str, AtomNode]:
        return self._atom_nodes

    @property
    def scheme_nodes(self) -> t.Mapping[str, SchemeNode]:
        return self._scheme_nodes

    def incoming_nodes(self, node: t.Union[str, Node]) -> t.AbstractSet[Node]:
        if isinstance(node, str):
            node = self._nodes[node]

        return self._incoming_nodes[node]

    def incoming_atom_nodes(self, node: t.Union[str, Node]) -> t.AbstractSet[AtomNode]:
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

    def outgoing_nodes(self, node: t.Union[str, Node]) -> t.AbstractSet[Node]:
        if isinstance(node, str):
            node = self._nodes[node]

        return self._outgoing_nodes[node]

    def outgoing_atom_nodes(self, node: t.Union[str, Node]) -> t.AbstractSet[AtomNode]:
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

    def incoming_edges(self, node: t.Union[str, Node]) -> t.AbstractSet[Edge]:
        if isinstance(node, str):
            node = self._nodes[node]

        return self._incoming_edges[node]

    def outgoing_edges(self, node: t.Union[str, Node]) -> t.AbstractSet[Edge]:
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

    @property
    def root_node(self) -> t.Optional[AtomNode]:
        # If no major claim explicitly set, try to find one node with no outgoing edges.
        # It is only returned if there exists exactly one node without connections.
        # Otherwise, nothing is returned.
        nodes = {
            node
            for node in self._atom_nodes.values()
            if len(self._outgoing_nodes[node]) == 0
        }

        if len(nodes) == 1:
            return next(iter(nodes))

        return None

    @major_claim.setter
    def major_claim(self, value: t.Union[str, AtomNode, None]) -> None:
        if isinstance(value, str):
            value = self._atom_nodes[value]
        elif not (value is None or isinstance(value, AtomNode)):
            raise TypeError(utils.type_error(type(value), AtomNode))

        self._major_claim = value
        # self._metadata.update()

    @property
    def leaf_nodes(self) -> t.Set[Node]:
        return {
            node for node in self.nodes.values() if len(self.incoming_nodes(node)) == 0
        }

    @property
    def leaf_atom_nodes(self) -> t.Set[AtomNode]:
        return {
            node
            for node in self.atom_nodes.values()
            if len(self.incoming_nodes(node)) == 0
        }

    @property
    def leaf_scheme_nodes(self) -> t.Set[SchemeNode]:
        return {
            node
            for node in self.scheme_nodes.values()
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

    def add_node(self, node: Node) -> None:
        """Add a node to the graph.

        Args:
            node: Node object that is not already part of the graph.

        Examples:
            >>> g = Graph()
            >>> g.add_node(AtomNode("Exemplary node"))
            >>> len(g.nodes)
            1
            >>> g.add_node(SchemeNode(Support.DEFAULT))
            >>> len(g.nodes)
            2
            >>> g.add_node("Test")
            Traceback (most recent call last):
            TypeError: Expected type '<class 'arguebuf.node.Node'>', but got '<class 'str'>'. Make sure that you are passing the correct method arguments.
        """

        if not isinstance(node, Node):
            raise TypeError(utils.type_error(type(node), Node))

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

    def remove_node(self, node: Node) -> None:
        """Remove a node and its corresponding edges from the graph.

        Args:
            node: Node object that is part of the graph.

        Examples:
            >>> g = Graph()
            >>> n1 = AtomNode("Node1")
            >>> n2 = SchemeNode(Support.DEFAULT)
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
            >>> n2 = SchemeNode(Support.DEFAULT)
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
            >>> n2 = SchemeNode(Support.DEFAULT)
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

    def node_distance(
        self,
        start_node: Node,
        end_node: Node,
        max_distance: t.Optional[int] = None,
        directed: bool = True,
        ignore_schemes: bool = False,
    ) -> t.Optional[int]:
        """Get the distance between `start_node` and `end_node` in the graph.

        Args:
            start_node: Node object that is part of the graph.
            end_node: Node object that is part of the graph.
            max_distance: Only search for nodes having at most a distance of this argument.
                Especially helpful when dealing with large graphs where shorts paths are searched for.
            directed: If `False`, also search for the direction `end_node` -> `start_node`.

        Returns:
            `None` if no path between

        Examples:
            >>> g = Graph()
            >>> n1 = AtomNode("Premise")
            >>> n2 = SchemeNode(Support.DEFAULT)
            >>> n3 = AtomNode("Claim")
            >>> e1 = Edge(n1, n2)
            >>> e2 = Edge(n2, n3)
            >>> g.add_node(n1)
            >>> g.add_node(n2)
            >>> len(g.nodes)
            2
            >>> g.add_edge(e1)
            >>> g.add_edge(e2)
            >>> len(g.edges)
            2
            >>> g.node_distance(n1, n3)
            2
            >>> g.node_distance(n3, n1)
        """

        if start_node in self.nodes.values() and end_node in self.nodes.values():
            if start_node == end_node:
                return 0

            connections = (
                self.outgoing_atom_nodes if ignore_schemes else self.outgoing_nodes
            )

            dist = _node_distance(start_node, end_node, connections, max_distance)

            if dist is None and not directed:
                dist = _node_distance(end_node, start_node, connections, max_distance)

            return dist

        return None

    @classmethod
    def from_ova(
        cls,
        obj: ova.Graph,
        name: t.Optional[str] = None,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from OVA argument graph file (reference: http://ova.uni-trier.de/)."""
        g = cls(name)

        resource = Resource.from_ova(obj["analysis"], nlp)
        g.add_resource(resource)

        for participant in obj["participants"]:
            g.add_participant(Participant.from_ova(participant))

        if analyst_name := obj["analysis"].get("annotatorName"):
            g.add_analyst(Analyst(name=analyst_name))

        for ova_node in obj["nodes"]:
            node = (
                atom_class.from_ova(ova_node, nlp)
                if ova_node.get("type") == "I"
                else scheme_class.from_ova(ova_node, nlp)
            )

            if node:
                g.add_node(node)

            if ova_node.get("major_claim") and isinstance(node, AtomNode):
                g._major_claim = node

        for ova_edge in obj["edges"]:
            if edge := edge_class.from_ova(ova_edge, g._nodes):
                g.add_edge(edge)

        if (analysis := obj.get("analysis")) and (raw_text := analysis.get("txt")):
            _inject_original_text(raw_text, g._atom_nodes, resource, nlp)

        return g

    @classmethod
    def from_sadface(
        cls,
        obj: sadface.Graph,
        name: t.Optional[str] = None,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from SADFace argument graph file
        (reference: https://github.com/Open-Argumentation/SADFace/blob/master/examples/hangback/data.json).
        """
        g = cls(name)

        for sadface_node in obj["nodes"]:
            node = (
                atom_class.from_sadface(sadface_node, nlp)
                if sadface_node["type"] == "atom"
                else scheme_class.from_sadface(sadface_node, nlp)
            )

            if node:
                g.add_node(node)

        for sadface_edge in obj["edges"]:
            if edge := edge_class.from_sadface(sadface_edge, g._nodes):
                g.add_edge(edge)

        # create
        # object
        created = dt.from_format(
            obj["metadata"]["core"]["created"], sadface.DATE_FORMAT
        )
        updated = dt.from_format(obj["metadata"]["core"]["edited"], sadface.DATE_FORMAT)
        metadata = Metadata(created, updated)
        g.metadata = metadata

        # create Analyst object
        analyst = Analyst(
            name=obj["metadata"]["core"]["analyst_name"],
            email=obj["metadata"]["core"]["analyst_email"],
        )
        g.add_analyst(analyst)

        # create Userdata dict
        userdata = {
            "notes": obj["metadata"]["core"]["notes"],
            "description": obj["metadata"]["core"]["description"],
            "title": obj["metadata"]["core"]["title"],
            "sadfaceVersion": obj["metadata"]["core"]["version"],
        }
        g.userdata = userdata

        return g

    @classmethod
    def from_argdown_json(
        cls,
        obj: argdown_json.Graph,
        name: t.Optional[str] = None,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from JSON Argdown argument graph file
        (reference: https://argdown.org/).
        """
        g = cls(name)

        timestamp = pendulum.now()

        # Every node in obj["nodes"] is a atom node
        for argdown_node in obj["map"]["nodes"]:
            node = atom_class.from_argdown_json(argdown_node, nlp)

            if node:
                g.add_node(node)

        for argdown_edge in obj["map"]["edges"]:
            if edge := edge_class.from_argdown_json(argdown_edge, g._nodes):
                g.add_edge(edge)
                if argdown_edge["relationType"] == "support":
                    scheme = Support.DEFAULT
                elif argdown_edge["relationType"] == "attack":
                    scheme = Attack.DEFAULT
                elif argdown_edge["relationType"] == "contradictory":
                    scheme = Attack.DEFAULT
                elif argdown_edge["relationType"] == "undercut":
                    scheme = Support.DEFAULT
                else:
                    scheme = Support.DEFAULT
                # create scheme_node for edge
                scheme_node = SchemeNode(
                    metadata=Metadata(timestamp, timestamp),
                    scheme=scheme,
                )
                g.add_node(scheme_node)

                # create edge from source to scheme_node and an edge from scheme_node to target
                g.add_edge(Edge(edge.source, scheme_node))
                g.add_edge(Edge(scheme_node, edge.target))

        metadata = Metadata(timestamp, timestamp)
        g.metadata = metadata

        return g

    @classmethod
    def from_aif(
        cls,
        obj: aif.Graph,
        name: t.Optional[str] = None,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from AIF argument graph file
        (reference: http://www.wi2.uni-trier.de/shared/publications/2019_LenzOllingerSahitajBergmann_ICCBR.pdf)

        """
        g = cls(name)

        for aif_node in obj["nodes"]:
            node = (
                atom_class.from_aif(aif_node, nlp)
                if aif_node["type"] == "I"
                else scheme_class.from_aif(aif_node, nlp)
            )

            if node:
                g.add_node(node)

        for aif_edge in obj["edges"]:
            if edge := edge_class.from_aif(aif_edge, g._nodes):
                g.add_edge(edge)

        return g

    def to_aif(self) -> aif.Graph:
        """Export structure of Graph instance to AIF argument graph format."""
        return {
            "nodes": [node.to_aif() for node in self._nodes.values()],
            "edges": [edge.to_aif() for edge in self._edges.values()],
            "locutions": [],
        }

    def to_protobuf(self) -> graph_pb2.Graph:
        """Export structure of Graph instance to PROTOBUF argument graph format."""
        try:
            version = importlib.metadata.version("arg_services")
        except importlib.metadata.PackageNotFoundError:
            version = ""

        g = graph_pb2.Graph(
            schema_version=1,
            library_version=version,
            metadata=self.metadata.to_protobuf(),
        )

        for node_id, node in self._nodes.items():
            g.nodes[node_id].CopyFrom(node.to_protobuf())

        for edge_id, edge in self._edges.items():
            g.edges[edge_id].CopyFrom(edge.to_protobuf())

        if self._major_claim:
            g.major_claim = self._major_claim.id

        for resource_id, resource in self._resources.items():
            g.resources[resource_id].CopyFrom(resource.to_protobuf())

        for participant_id, participant in self._participants.items():
            g.participants[participant_id].CopyFrom(participant.to_protobuf())

        for analyst_id, analyst in self._analysts.items():
            g.analysts[analyst_id].CopyFrom(analyst.to_protobuf())

        g.userdata.update(self.userdata)

        return g

    @classmethod
    def from_protobuf(
        cls,
        obj: graph_pb2.Graph,
        name: t.Optional[str] = None,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        participant_class: t.Type[Participant] = Participant,
        analyst_class: t.Type[Analyst] = Analyst,
        resource_class: t.Type[Resource] = Resource,
        reference_class: t.Type[Reference] = Reference,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from PROTOBUF argument graph file.(Link?)"""
        g = cls(name)

        for resource_id, resource in obj.resources.items():
            g.add_resource(resource_class.from_protobuf(resource_id, resource, nlp))

        for participant_id, participant in obj.participants.items():
            g.add_participant(
                participant_class.from_protobuf(participant_id, participant)
            )

        for analyst_id, analyst in obj.analysts.items():
            g.add_analyst(analyst_class.from_protobuf(analyst_id, analyst))

        for node_id, node in obj.nodes.items():
            if node.WhichOneof("type") == "atom":
                g.add_node(
                    atom_class.from_protobuf(
                        node_id,
                        node,
                        g._resources,
                        g._participants,
                        reference_class,
                        nlp,
                    )
                )
            elif node.WhichOneof("type") == "scheme":
                g.add_node(
                    scheme_class.from_protobuf(
                        node_id,
                        node,
                        g._resources,
                        g._participants,
                        reference_class,
                        nlp,
                    )
                )
            # TODO: Raise error if node is neither scheme nor atom

        for edge_id, proto_edge in obj.edges.items():
            if edge := edge_class.from_protobuf(edge_id, proto_edge, g._nodes):
                g.add_edge(edge)

        major_claim = g._nodes[obj.major_claim] if obj.major_claim else None

        if major_claim and isinstance(major_claim, AtomNode):
            g._major_claim = major_claim

        g.userdata.update(obj.userdata)
        g.metadata = Metadata.from_protobuf(obj.metadata)
        g.library_version = obj.library_version
        g.schema_version = obj.schema_version

        return g

    @classmethod
    def from_dict(
        cls,
        obj: t.Mapping[str, t.Any],
        name: t.Optional[str] = None,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from DICT argument graph file(Link?)."""
        if "analysis" in obj:
            return cls.from_ova(
                t.cast(ova.Graph, obj),
                name,
                atom_class,
                scheme_class,
                edge_class,
                nlp,
            )

        if "locutions" in obj:
            return cls.from_aif(
                t.cast(aif.Graph, obj),
                name,
                atom_class,
                scheme_class,
                edge_class,
                nlp,
            )

        return cls.from_protobuf(
            ParseDict(obj, graph_pb2.Graph()),
            name,
            atom_class,
            scheme_class,
            edge_class,
            nlp=nlp,
        )

    def to_dict(self, format: GraphFormat) -> t.Dict[str, t.Any]:
        """Export structure of Graph instance to DICT argument graph format."""

        if format == GraphFormat.AIF:
            return t.cast(t.Dict[str, t.Any], self.to_aif())

        return MessageToDict(self.to_protobuf(), including_default_value_fields=False)

    @classmethod
    def from_json(
        cls,
        obj: t.TextIO,
        name: t.Optional[str] = None,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from JSON argument graph file(Link?)."""
        return cls.from_dict(
            json.load(obj), name, atom_class, scheme_class, edge_class, nlp
        )

    def to_json(
        self,
        obj: t.TextIO,
        format: GraphFormat = GraphFormat.ARGUEBUF,
        pretty: bool = False,
    ) -> None:
        """Export structure of Graph instance to JSON argument graph format."""
        json.dump(
            self.to_dict(format),
            obj,
            ensure_ascii=False,
            indent=4 if pretty else None,
        )

    @classmethod
    def from_brat(
        cls,
        obj: t.TextIO,
        name: t.Optional[str] = None,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from BRAT argument graph file (reference: https://brat.nlplab.org/)"""
        reader = csv.reader(obj, delimiter="\t")
        g = cls(name)

        atom_nodes = {}
        mc = atom_class(utils.parse("", nlp))
        g.add_node(mc)
        g._major_claim = mc

        for row in reader:
            userdata = row[1].split()

            if row[0].startswith("T"):
                if userdata[0] == "MajorClaim":
                    mc.text = utils.parse(f"{mc.plain_text}. {row[2]}", nlp)
                else:
                    atom = atom_class(utils.parse(row[2], nlp))
                    g.add_node(atom)
                    atom_nodes[row[0]] = atom

            elif row[0].startswith("A") or row[0].startswith("R"):
                if row[0].startswith("A"):
                    scheme_type = (
                        Attack.DEFAULT if userdata[2] == "Against" else Support.DEFAULT
                    )
                    source = atom_nodes[userdata[1]]
                    target = mc
                else:
                    scheme_type = (
                        Attack.DEFAULT if userdata[0] == "attacks" else Support.DEFAULT
                    )
                    source = atom_nodes[userdata[1].split(":")[1]]
                    target = atom_nodes[userdata[2].split(":")[1]]

                scheme = scheme_class(scheme_type)
                g.add_node(scheme)

                g.add_edge(edge_class(source, scheme))
                g.add_edge(edge_class(scheme, target))

        return g

    @classmethod
    def from_kialo(
        cls,
        obj: t.TextIO,
        name: t.Optional[str] = None,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        if name_match := re.search(r"Discussion Title: (.*)", obj.readline()):
            name = name_match[1]

        # After the title, an empty line should follow
        assert obj.readline().strip() == ""

        g = cls(name)

        # Example: 1.1. Pro: Gold is better than silver.
        # Pattern: {ID}.{ID}. {STANCE (OPTIONAL)}: {TEXT}
        pattern = re.compile(r"^(1\.(?:\d+\.)+) (?:(Con|Pro): )?(.*)")
        current_line = obj.readline()
        next_line = obj.readline()

        mc_match = re.search(r"^((?:\d+\.)+) (.*)", current_line)

        if not mc_match:
            raise ValueError("The major claim is not present in the third line!")

        mc_id = mc_match[1]
        mc_text = mc_match[2]

        # See in the following while loop for explanation of this block
        while next_line and not pattern.search(next_line):
            mc_text = f"{mc_text}\n{next_line.strip()}"
            next_line = obj.readline()

        mc = _kialo_atom_node(mc_id, mc_text, nlp, atom_class)
        g.add_node(mc)
        g.major_claim = mc

        current_line = next_line
        next_line = obj.readline()

        while current_line:
            if current_match := pattern.search(current_line):
                source_id = current_match[1]
                source_id_parts = source_id[:-1].split(".")
                level = len(source_id_parts)
                stance = current_match[2]
                text = current_match[3]

                # The text of a node is allowed to span multiple lines.
                # Thus, we need to look ahead to concatenate the complete text.
                # As long as the pattern is not found in the next line,
                # we assume that the text belongs to the previous statement.
                while next_line and not pattern.search(next_line):
                    text = f"{text}\n{next_line.strip()}"
                    next_line = obj.readline()

                assert source_id
                assert text

                if id_ref_match := re.search(r"^-> See ((?:\d+\.)+)", text):
                    id_ref = id_ref_match[1]
                    source = g.atom_nodes[id_ref]
                else:
                    source = _kialo_atom_node(source_id, text, nlp, atom_class)
                    g.add_node(source)

                if stance:
                    stance = stance.lower()
                    scheme = scheme_class(
                        Attack.DEFAULT if stance == "con" else Support.DEFAULT,
                        id=f"{source_id}scheme",
                    )
                else:
                    scheme = scheme_class(Rephrase.DEFAULT, id=f"{source_id}scheme")

                target_id = ".".join(source_id_parts[:-1] + [""])
                target = g.atom_nodes[target_id]

                g.add_node(scheme)
                g.add_edge(edge_class(source, scheme, id=f"{source.id}->{scheme.id}"))
                g.add_edge(edge_class(scheme, target, id=f"{scheme.id}->{target.id}"))

                current_line = next_line
                next_line = obj.readline()

        return g

    @classmethod
    def from_aml(
        cls,
        obj: t.IO,
        name: t.Optional[str] = None,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """
        Generate Graph structure from AML argument graph file
        ElementTree XML API: https://docs.python.org/3/library/xml.etree.elementtree.html#
        """

        tree = ET.parse(obj)
        root = tree.getroot()

        # create nodes and edges from AU element
        au = root.find("AU")
        g = cls(name)
        g = aml.read_au(au, g, nlp)

        # create edge objects and add to g

        # create Metadata object
        # create Analyst object
        # create Userdata

        return g

    @classmethod
    def from_io(
        cls,
        obj: t.TextIO,
        suffix: str,
        name: t.Optional[str] = None,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from IO argument graph file(Link?)."""
        args = (obj, name, atom_class, scheme_class, edge_class, nlp)

        if suffix == ".ann":
            return cls.from_brat(*args)
        if suffix == ".txt":
            return cls.from_kialo(*args)
        if suffix == ".aml":
            return cls.from_aml(*args)

        return cls.from_json(*args)

    def to_io(
        self,
        obj: t.TextIO,
        format: GraphFormat = GraphFormat.ARGUEBUF,
        pretty: bool = False,
    ) -> None:
        """Export structure of Graph instance to IO argument graph format."""
        self.to_json(obj, format, pretty)

    @classmethod
    def from_file(
        cls,
        path: t.Union[Path, str],
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from a File."""
        if isinstance(path, str):
            path = Path(path)

        with path.open("r", encoding="utf-8") as file:
            return cls.from_io(
                file,
                path.suffix,
                path.stem,
                atom_class,
                scheme_class,
                edge_class,
                nlp,
            )

    def to_file(
        self,
        path: t.Union[Path, str],
        format: GraphFormat = GraphFormat.ARGUEBUF,
        pretty: bool = False,
    ) -> None:
        """Export strucure of Graph instance into structure of File/Folder format."""
        if isinstance(path, str):
            path = Path(path)

        if path.is_dir() or not path.suffix:
            path = path / f"{self.name}.json"

        with path.open("w", encoding="utf-8") as file:
            self.to_io(file, format, pretty)

    to_folder = to_file

    @classmethod
    def from_folder(
        cls,
        path: t.Union[Path, str],
        pattern: str,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> t.Dict[Path, Graph]:
        """Load all graphs matching the specified `pattern` in `path`.

        Args:
            path: Folder containing the graphs to be loaded.
            pattern: Unix glob pattern to filter the available files.
                Recursive matching can be achieved by prepending `**/` to any pattern.
                For instance, all `json` files of a folder can be retrieved with `**/*.json`.
                Supports the following wildcards: <https://docs.python.org/3/library/fnmatch.html#module-fnmatch>
            atom_class: Allows to override the class used for atom nodes in case a specialized subclass has been created. Defaults to `AtomNode`.
            scheme_class: Allows to override the class used for scheme nodes in case a specialized subclass has been created. Defaults to `SchemeNode`.
            edge_class: Allows to override the class used for edges in case a specialized subclass has been created. Defaults to `Edge`.
            nlp: Optionally pass a function to transforms all texts of atom nodes and resources to arbitrary Python objects.
                Useful when using `spacy` to generate embeddings.
                In this case, you can load a model with `spacy.load(...)` and pass the resulting `nlp` function via this parameter.

        Returns:
            Dictionary containing all found file paths as well as the loaded graphs.
        """

        if isinstance(path, str):
            path = Path(path)

        return {
            file: cls.from_file(file, atom_class, scheme_class, edge_class, nlp)
            for file in sorted(path.glob(pattern))
        }

    def to_nx(
        self,
        graph_attrs: t.Optional[
            t.MutableMapping[str, t.Callable[[Graph], t.Any]]
        ] = None,
        atom_attrs: t.Optional[
            t.MutableMapping[str, t.Callable[[AtomNode], t.Any]]
        ] = None,
        scheme_attrs: t.Optional[
            t.MutableMapping[str, t.Callable[[SchemeNode], t.Any]]
        ] = None,
        edge_attrs: t.Optional[t.MutableMapping[str, t.Callable[[Edge], t.Any]]] = None,
    ) -> nx.DiGraph:
        """Transform the argument graph for use with the library `NetworkX`

        This library allows you to apply advanced graph-related algorithms directly on your argument graphs.
        For instance, shortest paths and various distances can be computed.
        [Documentation](https://networkx.org/documentation/stable/reference/index.html)

        It is possible to add arbitrary attributes to the resulting graph and its elements.
        For this, you need to pass a dictionary with the desired name of the attribute and a function that is used to compute the attribute's value.
        The function will be passed the corresponding element as its only parameter.
        For instance, you could pass `atom_attrs={"text": lambda node: node.plain_text}` to set a `text` attribute for atom nodes.

        Args:
            graph_attrs: Attribute functions for the whole graph.
            atom_attrs: Attribute functions for the atom nodes.
            scheme_attrs: Attribute functions for the scheme nodes.
            edge_attrs: Attribute functions for the edges.

        Returns:
            Instance of the *directed* `NetworkX` graph.

        Examples:
            >>> g = Graph("Test")
            >>> n1 = AtomNode("Node1")
            >>> n2 = AtomNode("Node2")
            >>> e = Edge(n1, n2)
            >>> g.add_edge(e)
            >>> gnx = g.to_nx()
            >>> gnx.number_of_nodes()
            2
        """

        if graph_attrs is None:
            graph_attrs = {}

        g = nx.DiGraph(None, **{key: func(self) for key, func in graph_attrs.items()})

        for node in self._atom_nodes.values():
            node.to_nx(g, atom_attrs)

        for node in self._scheme_nodes.values():
            node.to_nx(g, scheme_attrs)

        for edge in self._edges.values():
            edge.to_nx(g, edge_attrs)

        return g

    def to_gv(
        self,
        format: t.Optional[str] = None,
        engine: t.Optional[str] = None,
        nodesep: t.Optional[float] = None,
        ranksep: t.Optional[float] = None,
        wrap_col: t.Optional[int] = None,
        margin: t.Optional[t.Tuple[float, float]] = None,
        font_name: t.Optional[str] = None,
        font_size: t.Optional[float] = None,
        atom_label: t.Optional[t.Callable[[AtomNode], str]] = None,
        scheme_label: t.Optional[t.Callable[[SchemeNode], str]] = None,
        graph_attr: t.Optional[t.Mapping[str, str]] = None,
        node_attr: t.Optional[t.Mapping[str, str]] = None,
        edge_attr: t.Optional[t.Mapping[str, str]] = None,
        edge_style: t.Optional[EdgeStyle] = None,
    ) -> gv.Digraph:
        """Transform a Graph instance into an instance of GraphViz directed graph. Make sure that a GraphViz Executable path is set on your machine for visualization. Refer to the GraphViz library for additional information."""
        gv_margin: t.Callable[[t.Tuple[float, float]], str] = lambda x: f"{x[0]},{x[1]}"

        if not graph_attr:
            graph_attr = {}

        if not node_attr:
            node_attr = {}

        if not edge_attr:
            edge_attr = {}

        g = gv.Digraph(
            name=str(self.name),
            strict=True,
            format=format or "pdf",
            engine=engine or "dot",
            node_attr={
                "fontname": font_name or "Arial",
                "fontsize": str(font_size or 11),
                "margin": gv_margin(margin or (0.15, 0.1)),
                "style": "rounded,filled",
                "shape": "box",
                "width": "0",
                "height": "0",
                **node_attr,
            },
            edge_attr={"color": "#9E9E9E", **edge_attr},
            graph_attr={
                # "bgcolor": "#000000",
                "rankdir": "BT",
                "margin": "0",
                "nodesep": str(nodesep or 0.25),
                "ranksep": str(ranksep or 0.5),
                "overlap": "false",
                "splines": edge_style.value if edge_style else EdgeStyle.STEP.value,
                **graph_attr,
            },
        )

        for node in self._atom_nodes.values():
            node.to_gv(
                g,
                self.major_claim == node,
                label_func=atom_label,
                wrap_col=wrap_col or 36,
            )

        for node in self._scheme_nodes.values():
            node.to_gv(
                g,
                False,
                label_func=scheme_label,
                wrap_col=wrap_col or 36,
            )

        for edge in self._edges.values():
            edge.to_gv(g)

        return g

    to_dot = to_gv

    def strip_scheme_nodes(self) -> Graph:
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

        return self

    def copy(
        self,
        atom_class: t.Type[AtomNode] = AtomNode,
        scheme_class: t.Type[SchemeNode] = SchemeNode,
        edge_class: t.Type[Edge] = Edge,
        participant_class: t.Type[Participant] = Participant,
        analyst_class: t.Type[Analyst] = Analyst,
        resource_class: t.Type[Resource] = Resource,
        reference_class: t.Type[Reference] = Reference,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Contents of Graph instance are copied into new Graph object."""

        return Graph.from_protobuf(
            self.to_protobuf(),
            self.name,
            atom_class,
            scheme_class,
            edge_class,
            participant_class,
            analyst_class,
            resource_class,
            reference_class,
            nlp,
        )


def _node_distance(
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


def _kialo_atom_node(
    id: str,
    text: str,
    nlp: t.Optional[t.Callable[[str], t.Any]],
    atom_class: t.Type[AtomNode],
) -> AtomNode:
    # Remove backslashes before parentheses/brackets
    text = re.sub(r"\\([\[\]\(\)])", r"\1", text)

    # Remove markdown links
    text = re.sub(
        r"\[(.*?)\]\(.*?\)",
        r"\1",
        text,
    )

    # Apply user-provided nlp function
    text = utils.parse(text, nlp)

    return atom_class(text, id=id)


def render(
    g: t.Union[gv.Graph, gv.Digraph],
    path: t.Union[Path, str],
    view: bool = False,
) -> None:
    """Visualize a Graph instance using a GraphViz backend. Make sure that a GraphViz Executable path is set on your machine for visualization."""
    if isinstance(path, str):
        path = Path(path)

    if not isinstance(g, (gv.Graph, gv.Digraph)):
        raise ValueError(
            "This method expects a graph in the 'DOT' format."
            "Please use 'graph.to_gv()' to convert your argument graph to the 'DOT' format."
        )

    filename = path.stem
    directory = path.parent

    g.render(
        filename=filename,
        directory=str(directory),
        cleanup=True,
        view=view,
    )


def _inject_original_text(
    raw_text: str,
    nodes: t.Mapping[str, AtomNode],
    resource: Resource,
    nlp: t.Optional[t.Callable[[str], t.Any]],
) -> None:
    doc = html.fromstring(f"<html><head></head><body>{raw_text}</body></html>")
    text = ""

    for elem in doc.body.iter():
        # Span elements need special handling
        if elem.tag == "span":
            # The id is prefixed with 'node', e.g. 'node5'.
            node_key = elem.attrib["id"].replace("node", "")
            if node := nodes.get(node_key):
                node._reference = Reference(
                    resource, len(text), utils.parse(elem.text, nlp)
                )

            if elem.text:
                text += elem.text

        elif elem.tag == "br":
            text += "\n"

        elif elem.text:
            text += elem.text

        # Text after a tag should always be added to the overall text
        if elem.tail:
            text += elem.tail

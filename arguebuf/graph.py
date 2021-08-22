from __future__ import absolute_import, annotations

import csv
import itertools
import json
import logging
import typing as t
from enum import Enum
from pathlib import Path

import graphviz as gv
import networkx as nx
from arg_services.graph.v1 import graph_pb2
from google.protobuf.json_format import MessageToDict, ParseDict
from lxml import html

from arguebuf.data import Analyst, Anchor, Metadata, Resource, Userdata

from . import dt, utils
from .edge import Edge
from .node import AtomNode, Node, SchemeNode, SchemeType
from .utils import ImmutableDict, ImmutableSet

log = logging.getLogger(__name__)


class GraphFormat(Enum):
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
        "analysts",
        "_resources",
        "userdata",
        "_metadata",
        "version",
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
    _major_claim: t.Optional[Node]
    analysts: t.List[Analyst]
    _resources: ImmutableDict[str, Resource]
    userdata: Userdata
    _metadata: Metadata
    version: str

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

    def outgoing_nodes(self, node: t.Union[str, Node]) -> t.AbstractSet[Node]:
        if isinstance(node, str):
            node = self._nodes[node]

        return self._outgoing_nodes[node]

    def incoming_edges(self, node: t.Union[str, Node]) -> t.AbstractSet[Edge]:
        if isinstance(node, str):
            node = self._nodes[node]

        return self._incoming_edges[node]

    def outgoing_edges(self, node: t.Union[str, Node]) -> t.AbstractSet[Edge]:
        if isinstance(node, str):
            node = self._nodes[node]

        return self._outgoing_edges[node]

    @property
    def resources(self) -> t.Mapping[str, Resource]:
        return self._resources

    @property
    def major_claim(self) -> t.Optional[Node]:
        if self._major_claim:
            return self._major_claim

        # If no major claim explicitly set, try to find one node with no outgoing edges.
        # It is only returned if there exists exactly one node without connections.
        # Otherwise, nothing is returned.
        mc_candidates = {
            node
            for node in self._atom_nodes.values()
            if len(self._outgoing_nodes[node]) == 0
        }

        if len(mc_candidates) == 1:
            return next(iter(mc_candidates))

        return None

    @property
    def metadata(self) -> Metadata:
        return self._metadata

    def __init__(self, name: t.Optional[str] = None):
        """Create a graph from scratch."""

        self.name = name or ""
        self._nodes = ImmutableDict()
        self._atom_nodes = ImmutableDict()
        self._scheme_nodes = ImmutableDict()
        self._edges = ImmutableDict()
        self.analysts = []
        self._metadata = Metadata()
        self.userdata = {}
        self._resources = ImmutableDict()
        self._major_claim = None

        self._incoming_nodes = ImmutableDict()
        self._incoming_edges = ImmutableDict()
        self._outgoing_nodes = ImmutableDict()
        self._outgoing_edges = ImmutableDict()

        self.version = "TODO"

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
            >>> g = Graph("Test")
            >>> g.add_node(Node(g.idgen(), "Node", NodeCategory.I))
            >>> len(g.nodes)
            1
            >>> g.add_node(Node(1, "Node", NodeCategory.I))
            Traceback (most recent call last):
            ValueError: ID already used in graph.
            >>> g.add_node("Test")
            Traceback (most recent call last):
            TypeError: Only Node objects possible.
        """

        if not isinstance(node, Node):
            raise TypeError(utils.type_error(type(node), Node))

        if node.id in self._nodes:
            raise ValueError(utils.duplicate_key_error(self.name, node.id))

        self._nodes._store[node.id] = node

        if isinstance(node, AtomNode):
            self._atom_nodes._store[node.id] = node
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
            >>> g = Graph("")
            >>> n1 = Node(g.idgen(), "Node 1", NodeCategory.I)
            >>> n2 = Node(g.idgen(), "Node 2", NodeCategory.I)
            >>> e = Edge(g.idgen(), n1, n2)
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
            edge: Edge object that is part of the graph.

        Examples:
            >>> g = Graph("")
            >>> n1 = Node(g.idgen(), "Node 1", NodeCategory.I)
            >>> n2 = Node(g.idgen(), "Node 2", NodeCategory.I)
            >>> n3 = Node(g.idgen(), "Node 3", NodeCategory.I)
            >>> e1 = Edge(g.idgen(), n1, n2)
            >>> e2 = Edge(g.idgen(), n2, n3)
            >>> g.add_edge(e1)
            >>> print(len(g.edges))
            1
            >>> g.add_edge(e2)
            >>> print(len(g.edges))
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
            >>> g = Graph("")
            >>> n1 = Node(g.idgen(), "Node 1", NodeCategory.I)
            >>> n2 = Node(g.idgen(), "Node 2", NodeCategory.I)
            >>> e = Edge(g.idgen(), n1, n2)
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

    def add_resource(self, resource: Resource) -> None:
        if not isinstance(resource, Resource):
            raise TypeError(utils.type_error(type(resource), Resource))

        if resource.id in self._resources:
            raise ValueError(utils.duplicate_key_error(self.name, resource.id))

        self._resources._store[resource.id] = resource

    def remove_resource(self, resource: Resource) -> None:
        if not isinstance(resource, Resource):
            raise TypeError(utils.type_error(type(resource), Resource))

        if resource.id not in self._resources:
            raise ValueError(utils.missing_key_error(self.name, resource.id))

        del self._resources._store[resource.id]

        for node in self._atom_nodes.values():
            if node.anchor and node.anchor.resource == resource:
                node.anchor.resource = None
                node.anchor.offset = None

    def node_distance(self, node1: Node, node2) -> t.Optional[int]:
        """If node is in the graph, return the distance to the major claim (if set)."""

        # TODO: Currently, there is no differentiation between I-nodes and S-nodes.

        if node1 in self.nodes and node2 in self.nodes:
            if node1 == node2:
                return 0

            return _node_distance(node1, node2, self._incoming_nodes) or _node_distance(
                node1, node2, self._outgoing_nodes
            )

        return None

    @classmethod
    def from_ova(
        cls,
        obj: t.Mapping[str, t.Any],
        name: t.Optional[str] = None,
        atom_class=AtomNode,
        scheme_class=SchemeNode,
        edge_class=Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from OVA argument graph file (reference: http://ova.uni-trier.de/)."""
        analysis: t.Mapping[str, t.Any] = obj["analysis"]

        g = cls(name)

        # g.userdata = utils.parse_userdata(obj, include=["participants", "ovaVersion"])

        resource = Resource(
            utils.unique_id(),
            utils.parse(analysis.get("plain_txt"), nlp),
            analysis.get("documentTitle"),
            analysis.get("documentSource"),
            dt.from_analysis(analysis.get("documentDate")),
        )
        g.add_resource(resource)

        if analyst_name := analysis.get("annotatorName"):
            g.analysts.append(Analyst(analyst_name, ""))

        for ova_node in obj["nodes"]:
            node = (
                atom_class.from_ova(ova_node, nlp)
                if ova_node.get("type") == "I"
                else scheme_class.from_ova(ova_node, nlp)
            )
            g.add_node(node)

            if ova_node.get("major_claim"):
                g._major_claim = node

        for edge in obj["edges"]:
            g.add_edge(edge_class.from_ova(edge, g._nodes))

        if analysis and analysis.get("txt"):
            analysis_txt = analysis["txt"]
            doc = html.fromstring(
                f"<html><head></head><body>{analysis_txt}</body></html>"
            )
            text = ""

            for elem in doc.body.iter():
                # Span elements need special handling
                if elem.tag == "span":
                    # The id is prefixed with 'node', e.g. 'node5'.
                    node_key = elem.attrib["id"].replace("node", "")
                    node = g._atom_nodes.get(node_key)

                    if node:
                        node.anchor = Anchor(
                            resource, len(text), utils.parse(elem.text, nlp)
                        )

                    text += elem.text

                # A line break does not contain text, thus we only insert a newline
                elif elem.tag == "br":
                    text += "\n"

                # All other elements (e.g., the body tag) are just added to the text
                else:
                    text += elem.text

                # Text after a tag should always be added to the overall text
                text += elem.tail

        return g

    @classmethod
    def from_aif(
        cls,
        obj: t.Mapping[str, t.Any],
        name: t.Optional[str] = None,
        atom_class=AtomNode,
        scheme_class=SchemeNode,
        edge_class=Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from AIF argument graph file
        (reference: http://www.wi2.uni-trier.de/shared/publications/2019_LenzOllingerSahitajBergmann_ICCBR.pdf)

        """
        g = cls(name)

        for node in obj["nodes"]:
            g.add_node(
                atom_class.from_aif(node, nlp)
                if node["type"] == "I"
                else scheme_class.from_aif(node, nlp)
            )

        for edge in obj["edges"]:
            g.add_edge(edge_class.from_aif(edge, g._nodes))

        return g

    def to_aif(self) -> t.Dict[str, t.Any]:
        """Export structure of Graph instance to AIF argument graph format."""
        return {
            "nodes": [node.to_aif() for node in self._nodes.values()],
            "edges": [edge.to_aif() for edge in self._edges.values()],
            "locutions": [],
        }

    def to_protobuf(self) -> graph_pb2.Graph:
        g = graph_pb2.Graph()

        for node_id, node in self._nodes.items():
            g.nodes[node_id].CopyFrom(node.to_protobuf())

        for edge_id, edge in self._edges.items():
            g.edges[edge_id].CopyFrom(edge.to_protobuf())

        if self._major_claim:
            g.major_claim = self._major_claim.id

        if self.analysts:
            g.analysts.extend(analyst.to_protobuf() for analyst in self.analysts)

        for resource_id, resource in self._resources.items():
            g.resources[resource_id] = resource.to_protobuf()

        g.userdata.update(self.userdata)
        g.metadata.CopyFrom(self._metadata.to_protobuf())
        g.version = self.version

        return g

    @classmethod
    def from_protobuf(
        cls,
        obj: graph_pb2.Graph,
        name: t.Optional[str] = None,
        atom_class=AtomNode,
        scheme_class=SchemeNode,
        edge_class=Edge,
        analyst_class=Analyst,
        resource_class=Resource,
        anchor_class=Anchor,
        metadata_class=Metadata,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        g = cls(name)

        for node_id, node in obj.nodes.items():
            if node.WhichOneof("node") == "atom":
                g.add_node(
                    atom_class.from_protobuf(
                        node_id, node, metadata_class, anchor_class, nlp
                    )
                )
            elif node.WhichOneof("node") == "scheme":
                g.add_node(
                    scheme_class.from_protobuf(
                        node_id, node, metadata_class, anchor_class, nlp
                    )
                )

        for edge_id, edge in obj.edges.items():
            g.add_edge(
                edge_class.from_protobuf(edge_id, edge, g._nodes, metadata_class)
            )

        if major_claim := obj.major_claim:
            g._major_claim = g._nodes[major_claim]

        g.analysts = [analyst_class.from_protobuf(analyst) for analyst in obj.analysts]

        for resource_id, resource in obj.resources.items():
            g.add_resource(resource_class.from_protobuf(resource_id, resource, nlp))

        g.userdata.update(obj.userdata)
        g._metadata = metadata_class.from_protobuf(obj.metadata)
        g.version = obj.version

        return g

    @classmethod
    def from_dict(
        cls,
        obj: t.Mapping[str, t.Any],
        name: t.Optional[str] = None,
        atom_class=AtomNode,
        scheme_class=SchemeNode,
        edge_class=Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        # if "analysis" in obj:
        #     return cls.from_ova(obj, name, atom_class, scheme_class, edge_class, nlp)

        if "locutions" in obj:
            return cls.from_aif(obj, name, atom_class, scheme_class, edge_class, nlp)

        return cls.from_protobuf(
            ParseDict(obj, graph_pb2.Graph()),
            name,
            atom_class,
            scheme_class,
            edge_class,
            nlp,
        )

    def to_dict(self, format: GraphFormat) -> t.Dict[str, t.Any]:
        if format == GraphFormat.AIF:
            return self.to_aif()

        return MessageToDict(self.to_protobuf(), including_default_value_fields=True)

    @classmethod
    def from_json(
        cls,
        obj: t.IO,
        name: t.Optional[str] = None,
        atom_class=AtomNode,
        scheme_class=SchemeNode,
        edge_class=Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        return cls.from_dict(
            json.load(obj), name, atom_class, scheme_class, edge_class, nlp
        )

    def to_json(self, obj: t.IO, format: GraphFormat) -> None:
        json.dump(self.to_dict(format), obj, ensure_ascii=False, indent=4)

    @classmethod
    def from_brat(
        cls,
        obj: t.IO,
        name: t.Optional[str] = None,
        atom_class=AtomNode,
        scheme_class=SchemeNode,
        edge_class=Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Generate Graph structure from brat argument graph file (reference: https://brat.nlplab.org/)"""
        reader = csv.reader(obj, delimiter="\t")
        g = cls(name)

        inodes = {}
        mc: AtomNode = atom_class(utils.unique_id(), utils.parse("", nlp))
        g.add_node(mc)
        g._major_claim = mc

        for row in reader:
            metadata = row[1].split()

            if row[0].startswith("T"):
                if metadata[0] == "MajorClaim":
                    mc.text = utils.parse(mc.plain_text + ". " + row[2], nlp)
                else:
                    inode = atom_class(utils.unique_id(), utils.parse(row[2], nlp))
                    g.add_node(inode)
                    inodes[row[0]] = inode

            elif row[0].startswith("A") or row[0].startswith("R"):
                if row[0].startswith("A"):
                    scheme_type = (
                        SchemeType.ATTACK
                        if metadata[2] == "Against"
                        else SchemeType.SUPPORT
                    )
                    source_inode = inodes[metadata[1]]
                    target_inode = mc
                else:
                    scheme_type = (
                        SchemeType.ATTACK
                        if metadata[0] == "attacks"
                        else SchemeType.SUPPORT
                    )
                    source_inode = inodes[metadata[1].split(":")[1]]
                    target_inode = inodes[metadata[2].split(":")[1]]

                snode: SchemeNode = scheme_class(utils.unique_id(), scheme_type)
                g.add_node(snode)

                g.add_edge(edge_class(utils.unique_id(), source_inode, snode))
                g.add_edge(edge_class(utils.unique_id(), snode, target_inode))

        return g

    @classmethod
    def from_io(
        cls,
        obj: t.IO,
        suffix: str,
        name: t.Optional[str] = None,
        atom_class=AtomNode,
        scheme_class=SchemeNode,
        edge_class=Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        if suffix == ".ann":
            return cls.from_brat(obj, name, atom_class, scheme_class, edge_class, nlp)

        return cls.from_json(obj, name, atom_class, scheme_class, edge_class, nlp)

    def to_io(self, obj: t.IO, format: GraphFormat) -> None:
        self.to_json(obj, format)

    @classmethod
    def from_file(
        cls,
        path: Path,
        atom_class=AtomNode,
        scheme_class=SchemeNode,
        edge_class=Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        with path.open("r", encoding="utf-8") as file:
            return cls.from_io(
                file, path.suffix, path.stem, atom_class, scheme_class, edge_class, nlp
            )

    def to_file(self, path: Path, format: GraphFormat) -> None:
        if path.is_dir() or not path.suffix:
            path = path / f"{self.name}.json"

        with path.open("w", encoding="utf-8") as file:
            self.to_io(file, format)

    to_folder = to_file

    @classmethod
    def from_folder(
        cls,
        path: Path,
        atom_class=AtomNode,
        scheme_class=SchemeNode,
        edge_class=Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
        suffixes: t.Iterable[str] = (".json"),
    ) -> t.List[Graph]:
        graphs = []

        for suffix in suffixes:
            for file in sorted(path.rglob(f"*{suffix}")):
                graphs.append(
                    cls.from_file(file, atom_class, scheme_class, edge_class, nlp)
                )

        return graphs

    def to_nx(self) -> nx.DiGraph:
        """Transform a Graph instance into an instance of networkx directed graph. Refer to the networkx library for additional information.

        Examples:
            >>> g = Graph("")
            >>> n1 = Node(g.idgen(), "Node 1", NodeCategory.I)
            >>> n2 = Node(g.idgen(), "Node 2", NodeCategory.I)
            >>> e = Edge(g.idgen(), n1, n2)
            >>> g.add_edge(e)
            >>> gnx = g.to_nx()
            >>> gnx.number_of_nodes()
            2

        """
        g = nx.DiGraph()

        for node in self._nodes.values():
            node.to_nx(g)

        for edge in self._edges.values():
            edge.to_nx(g)

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
    ) -> gv.Digraph:
        """Transform a Graph instance into an instance of GraphViz directed graph. Make sure that a GraphViz Executable path is set on your machine for visualization. Refer to the GraphViz library for additional information."""
        gv_margin = lambda x: f"{x[0]},{x[1]}"

        g = gv.Digraph(
            name=str(self.name),
            strict=True,
            format=format or "pdf",
            engine=engine or "dot",
            node_attr={
                "fontname": font_name or "Arial",
                "fontsize": str(font_size or 11),
                "margin": gv_margin(margin or (0.15, 0.1)),
                "style": "filled",
                "shape": "box",
                "width": "0",
                "height": "0",
            },
            edge_attr={"color": "#666666"},
            graph_attr={
                "rankdir": "BT",
                "margin": "0",
                "nodesep": str(nodesep or 0.25),
                "ranksep": str(ranksep or 0.5),
            },
        )

        for node in self._nodes.values():
            node.to_gv(
                g,
                self.major_claim == node,
                wrap_col=wrap_col or 36,
            )

        for edge in self._edges.values():
            edge.to_gv(g)

        return g

    def strip_snodes(self) -> None:
        """Remove scheme nodes from graph and merge respective edges into singular edge"""
        snodes = list(self._scheme_nodes.values())

        for snode in snodes:
            for incoming, outgoing in itertools.product(
                self._incoming_edges[snode], self._outgoing_edges[snode]
            ):
                if isinstance(incoming.source, AtomNode) and isinstance(
                    outgoing.target, AtomNode
                ):
                    self.add_edge(
                        Edge(
                            f"{incoming.id}-{outgoing.id}",
                            incoming.source,
                            outgoing.target,
                        )
                    )

            self.remove_node(snode)

    def copy(
        self,
        node_class=Node,
        edge_class=Edge,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Graph:
        """Contents of Graph instance are copied into new Graph object."""
        return Graph.from_dict(self.to_dict(), self.name, node_class, edge_class, nlp)


def _node_distance(
    node1: Node, node2: Node, connections: t.Mapping[Node, t.Iterable[Node]]
) -> t.Optional[int]:
    expansion: t.List[t.Tuple[Node, int]] = [(n, 1) for n in connections[node1]]

    while len(expansion) > 0:
        candidate, distance = expansion.pop()

        if candidate == node2:
            return distance
        else:
            expansion.extend((n, distance + 1) for n in connections[candidate])

    return None


def render(
    g: gv.dot.Dot,
    path: Path,
    view: bool = False,
) -> None:
    """Visualize a Graph instance using a GraphViz backend. Make sure that a GraphViz Executable path is set on your machine for visualization."""
    filename = path.stem
    directory = path.parent

    try:
        g.render(
            filename=filename,
            directory=str(directory),
            cleanup=True,
            view=view,
        )
    except gv.ExecutableNotFound:
        log.error("Rendering not possible. GraphViz might not be installed.")

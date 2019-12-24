from __future__ import absolute_import, annotations

import itertools
import json
from dataclasses import dataclass, field, InitVar
from enum import Enum
from pathlib import Path
from typing import Any, Optional, List, Dict, Callable, Union, Generator, Iterator, Set

import graphviz as gv
import networkx as nx
import pendulum
from lxml import html
import logging

from . import utils, dt
from .edge import Edge
from .node import Node, NodeCategory
from .utils import ImmutableList, ImmutableDict, ImmutableSet, MISSING


class GraphCategory(Enum):
    AIF = "aif"
    OVA = "ova"
    OTHER = "other"


# TODO: Add __slots__


@dataclass(eq=False)
class Graph:
    """Graph in AIF format.

    No attribute is mandatory.
    All nodes and edges attributes are read-only.
    """

    __slots__ = (
        "name",
        "_node_mappings",
        "_inode_mappings",
        "_snode_mappings",
        "_edge_mappings",
        "_incoming_nodes",
        "_incoming_edges",
        "_outgoing_nodes",
        "_outgoing_edges",
        "participants",
        "category",
        "ova_version",
        "text",
        "highlighted_text",
        "annotator_name",
        "document_source",
        "document_title",
        "document_date",
        "_key_iterator",
    )

    name: str
    _node_mappings: ImmutableDict[int, Node]
    _inode_mappings: ImmutableDict[int, Node]
    _snode_mappings: ImmutableDict[int, Node]
    _edge_mappings: ImmutableDict[int, Edge]
    _incoming_nodes: ImmutableDict[Node, ImmutableSet[Node]]
    _incoming_edges: ImmutableDict[Node, ImmutableSet[Edge]]
    _outgoing_nodes: ImmutableDict[Node, ImmutableSet[Node]]
    _outgoing_edges: ImmutableDict[Node, ImmutableSet[Edge]]
    participants: Optional[List[Any]]
    category: GraphCategory
    ova_version: str
    text: Union[None, str, Any]
    highlighted_text: Optional[str]
    annotator_name: Optional[str]
    document_source: Optional[str]
    document_title: Optional[str]
    document_date: Optional[pendulum.DateTime]
    _key_iterator: Iterator[int]

    @property
    def nodes(self):
        return self._node_mappings.values()

    @property
    def inodes(self):
        return self._inode_mappings.values()

    @property
    def snodes(self):
        return self._snode_mappings.values()

    @property
    def edges(self):
        return self._edge_mappings.values()

    @property
    def node_keys(self):
        return self._node_mappings.keys()

    @property
    def inode_keys(self):
        return self._inode_mappings.keys()

    @property
    def snode_keys(self):
        return self._snode_mappings.keys()

    @property
    def edge_keys(self):
        return self._edge_mappings.keys()

    @property
    def node_mappings(self):
        return self._node_mappings

    @property
    def inode_mappings(self):
        return self._inode_mappings

    @property
    def snode_mappings(self):
        return self._snode_mappings

    @property
    def edge_mappings(self):
        return self._edge_mappings

    @property
    def incoming_nodes(self):
        return self._incoming_nodes

    @property
    def incoming_edges(self):
        return self._incoming_edges

    @property
    def outgoing_nodes(self):
        return self._outgoing_nodes

    @property
    def outgoing_edges(self):
        return self._outgoing_edges

    @property
    def keys(self) -> Set[int]:
        return set().union(self.node_keys, self.edge_keys)

    def __init__(
        self,
        name: str,
        category: GraphCategory = GraphCategory.OTHER,
        ova_version: str = None,
        text: Union[None, str, Any] = None,
        highlighted_text: Optional[str] = None,
        annotator_name: Optional[str] = None,
        document_source: Optional[str] = None,
        document_title: Optional[str] = None,
        document_date: Union[MISSING, None, pendulum.DateTime] = MISSING,
        participants: Optional[List[Any]] = None,
    ):
        self.name = name
        self.category = category
        self.ova_version = ova_version
        self.text = text
        self.highlighted_text = highlighted_text
        self.annotator_name = annotator_name
        self.document_source = document_source
        self.document_title = document_title
        self.document_date = (
            pendulum.now() if document_date is MISSING else document_date
        )
        self.participants = participants

        self._key_iterator = itertools.count(start=1)

        self._node_mappings = ImmutableDict()
        self._inode_mappings = ImmutableDict()
        self._snode_mappings = ImmutableDict()
        self._edge_mappings = ImmutableDict()

        self._incoming_nodes = ImmutableDict()
        self._incoming_edges = ImmutableDict()
        self._outgoing_nodes = ImmutableDict()
        self._outgoing_edges = ImmutableDict()

    def keygen(self):
        key = next(self._key_iterator)
        keys = self.keys

        while key in keys:
            key = next(self._key_iterator)

        return key

    def add_node(self, node: Node) -> None:
        """Add a node."""

        if not isinstance(node, Node):
            raise ValueError(f"Expected 'Node', but got '{type(node)}'")

        if node.key in self.node_keys:
            raise ValueError(
                f"Graph '{self.name}' already contains an element with key '{node.key}'."
            )

        self._node_mappings._store[node.key] = node

        if node.category == NodeCategory.I:
            self._inode_mappings._store[node.key] = node
        else:
            self._snode_mappings._store[node.key] = node

        self.incoming_nodes._store[node] = ImmutableSet()
        self.incoming_edges._store[node] = ImmutableSet()
        self.outgoing_nodes._store[node] = ImmutableSet()
        self.outgoing_edges._store[node] = ImmutableSet()

    def remove_node(self, node: Node) -> None:
        """Remove a node and its corresponding edges."""

        if not isinstance(node, Node):
            raise ValueError(f"Expected 'Node', but got '{type(node)}'")

        if node.key not in self.node_keys:
            raise ValueError(
                f"Graph '{self.name}' does not contain an element with key '{node.key}'."
            )

        del self._node_mappings._store[node]

        if node.category == NodeCategory.I:
            del self._inode_mappings._store[node]
        else:
            del self._snode_mappings._store[node]

        for edge in self.edges:
            if node == edge.start or node == edge.end:
                self.remove_edge(edge)

        del self.incoming_nodes._store[node]
        del self.incoming_edges._store[node]
        del self.outgoing_nodes._store[node]
        del self.outgoing_edges._store[node]

    def add_edge(self, edge: Edge) -> None:
        """Add an edge and its nodes (if not already added)."""

        if not isinstance(edge, Edge):
            raise ValueError(f"Expected 'Edge', but got '{type(edge)}'")

        if edge.key in self.edge_keys:
            raise ValueError(
                f"Graph '{self.name}' already contains an element with key '{edge.key}'."
            )

        self._edge_mappings._store[edge.key] = edge

        if edge.start.key not in self.node_keys:
            self.add_node(edge.start)

        if edge.end.key not in self.node_keys:
            self.add_node(edge.end)

        self.outgoing_edges[edge.start]._store.add(edge)
        self.incoming_edges[edge.end]._store.add(edge)
        self.outgoing_nodes[edge.start]._store.add(edge.end)
        self.incoming_nodes[edge.end]._store.add(edge.start)

    def remove_edge(self, edge: Edge) -> None:
        """Remove an edge."""

        if not isinstance(edge, Edge):
            raise ValueError(f"Expected 'Edge', but got '{type(edge)}'")

        if edge.key not in self.edge_keys:
            raise ValueError(
                f"Graph '{self.name}' does not contain an element with key '{edge.key}'."
            )

        self.outgoing_edges[edge.start]._store.remove(edge)
        self.incoming_edges[edge.end]._store.remove(edge)
        self.outgoing_nodes[edge.start]._store.remove(edge.end)
        self.incoming_nodes[edge.end]._store.remove(edge.start)

    @staticmethod
    def from_ova(
        obj: Dict[str, Any],
        name: Optional[str] = None,
        nlp: Optional[Callable[[str], Any]] = None,
    ) -> Graph:
        analysis = obj.get("analysis")

        g = Graph(
            name=name or utils.unique_id(),
            category=GraphCategory.OVA,
            participants=obj.get("participants"),
            ova_version=analysis.get("ovaVersion"),
            text=utils.parse(analysis.get("plain_txt"), nlp),
            highlighted_text=analysis.get("txt"),
            annotator_name=analysis.get("annotatorName"),
            document_source=analysis.get("documentSource"),
            document_title=analysis.get("documentTitle"),
            document_date=dt.from_analysis(analysis.get("documentDate")),
        )

        node_dict = {}

        for node_obj in obj.get("nodes"):
            node = Node.from_ova(node_obj, nlp)
            node_dict[node.key] = node
            g.add_node(node)

        for edge in obj.get("edges"):
            g.add_edge(Edge.from_ova(edge, g.keygen(), node_dict, nlp))

        if analysis and analysis.get("txt"):
            txt = analysis["txt"]
            doc = html.fromstring(f"<html><head></head><body>{txt}</body></html>")

            # Retain newlines.
            for br in doc.xpath("*//br"):
                br.tail = "\n" + br.tail if br.tail else "\n"

            # Highlights are always contained in one span.
            spans = doc.body.findall("span")

            for span in spans:
                # The id is prefixed with 'node', e.g. 'node5'.
                node_key = int(span.attrib["id"].replace("node", ""))
                node = node_dict.get(node_key)

                if node:
                    node.raw_text = span.text_content()

        return g

    def to_ova(self) -> dict:
        highlighted_text = self.highlighted_text

        if not highlighted_text:
            highlighted_text = utils.xstr(self.text)

            for node in self.nodes:
                highlighted_text = highlighted_text.replace(
                    node.raw_text,
                    f'<span class="highlighted" id="node{node.key}">{node.raw_text}</span>',
                )

            highlighted_text = highlighted_text.replace("\n", "<br>")

        return {
            "nodes": [node.to_ova() for node in self.nodes],
            "edges": [edge.to_ova() for edge in self.edges],
            "participants": self.participants if self.participants else [],
            "analysis": {
                "ovaVersion": self.ova_version or "",
                "txt": highlighted_text,
                "plain_txt": utils.xstr(self.text),
                "annotatorName": self.annotator_name or "",
                "documentSource": self.document_source or "",
                "documentTitle": self.document_title or "",
                "documentDate": dt.to_analysis(self.document_date),
            },
        }

    @staticmethod
    def from_aif(
        obj: Dict[str, Any],
        name: Optional[str] = None,
        nlp: Optional[Callable[[str], Any]] = None,
    ) -> Graph:

        g = Graph(
            name=name or utils.unique_id(),
            category=GraphCategory.AIF,
            document_date=None,
        )

        node_dict = {}

        for node_obj in obj.get("nodes"):
            node = Node.from_aif(node_obj, nlp)
            node_dict[node.key] = node
            g.add_node(node)

        for edge in obj.get("edges"):
            g.add_edge(Edge.from_aif(edge, node_dict, nlp))

        return g

    def to_aif(self) -> dict:
        return {
            "nodes": [node.to_aif() for node in self.nodes],
            "edges": [edge.to_aif() for edge in self.edges],
            "locutions": [],
        }

    @staticmethod
    def from_dict(
        obj: Dict[str, Any],
        name: Optional[str] = None,
        nlp: Optional[Callable[[str], Any]] = None,
    ) -> Graph:
        if "analysis" in obj:
            return Graph.from_ova(obj, name, nlp)
        else:
            return Graph.from_aif(obj, name, nlp)

    def to_dict(self) -> dict:
        if self.category == GraphCategory.OVA:
            return self.to_ova()
        elif self.category == GraphCategory.AIF:
            return self.to_aif()
        else:
            return self.to_ova()

    def to_nx(self) -> nx.DiGraph:
        g = nx.DiGraph()
        for edge in self.edges:
            edge.start.to_nx(g)
            edge.end.to_nx(g)
            edge.to_nx(g)

        return g

    def to_gv(self, format: str = "pdf", engine: str = "dot") -> gv.Digraph:
        g = gv.Digraph(name=str(self.name), strict=True, format=format, engine=engine,)
        g.attr(rankdir="BT")

        for edge in self.edges:
            edge.start.to_gv(g)
            edge.end.to_gv(g)
            edge.to_gv(g)

        return g

    @staticmethod
    def from_file(path: Path, nlp: Optional[Callable[[str], Any]] = None) -> Graph:
        with path.open("r") as file:
            return Graph.from_dict(json.load(file), path.stem, nlp)

    def to_file(self, path: Path) -> None:
        if path.is_dir():
            path = path / f"{self.name}.json"

        with path.open("w") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=4)

    @staticmethod
    def from_folder(
        path: Path, nlp: Optional[Callable[[str], Any]] = None, suffix: str = ".json"
    ) -> List[Graph]:
        files = path.rglob(f"*{suffix}")
        return [Graph.from_file(file, nlp) for file in sorted(files)]

    def render(
        self, path: Path, format: str = "pdf", engine: str = "dot", view: bool = False
    ) -> None:
        filename = self.name
        directory = path

        if path.is_file():
            filename = path.name
            directory = path.parent

        g = self.to_gv(format, engine)

        try:
            g.render(
                filename=str(filename),
                directory=str(directory),
                cleanup=True,
                view=view,
            )
        except Exception:
            logging.error("Rendering not possible. GraphViz might not be installed.")

    open = from_file
    open_folder = from_folder
    to_folder = to_file
    save = to_file

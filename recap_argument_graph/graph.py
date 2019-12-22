from __future__ import absolute_import, annotations

import json
from dataclasses import dataclass, field, InitVar
from enum import Enum
from pathlib import Path
from typing import Any, Optional, List, Dict, Callable, Union

import graphviz as gv
import networkx as nx
import pendulum
from lxml import html

from . import utils, dt
from .edge import Edge, Edges
from .node import Node, Nodes, NodeCategory


# TODO: How should duplicates be handled?
# TODO: Should id() be used for comparison?


class GraphCategory(Enum):
    AIF = "aif"
    OVA = "ova"
    OTHER = "other"


@dataclass
class Graph:
    """Graph in AIF format.

    Attributes `id`, `nodes` and `edges` are mandatory.

    **Important:** The attributes `nodes`, `inodes` and `snodes` are not in sync after init.
    In other word, `inodes` is not updated if a new element is added to `nodes`.
    Thus, all three list need to be updated manually.

    **However**, the initial value for `nodes` is parsed and the lists `inodes` and `snodes` are filled accordingly.
    Manual updates are therefore only necessary for update operations.
    """

    key: str = field(default_factory=utils.unique_id)
    nodes: Nodes = field(init=False, default_factory=Nodes)
    inodes: Nodes = field(init=False, default_factory=Nodes)
    snodes: Nodes = field(init=False, default_factory=Nodes)
    edges: Edges = field(init=False, default_factory=Edges)
    init_nodes: InitVar[List[Node]] = None
    init_edges: InitVar[List[Edge]] = None
    incoming_nodes: Dict[Node, Nodes] = field(init=False, default_factory=dict)
    incoming_edges: Dict[Node, Edges] = field(init=False, default_factory=dict)
    outgoing_nodes: Dict[Node, Nodes] = field(init=False, default_factory=dict)
    outgoing_edges: Dict[Node, Edges] = field(init=False, default_factory=dict)
    participants: Optional[List[Any]] = None
    category: GraphCategory = GraphCategory.OTHER
    ova_version: str = None
    text: Union[None, str, Any] = None
    highlighted_text: Optional[str] = None
    annotator_name: Optional[str] = None
    document_source: Optional[str] = None
    document_title: Optional[str] = None
    document_date: Optional[pendulum.DateTime] = field(default_factory=pendulum.now)

    @property
    def _uid(self):
        return self.key

    def __hash__(self):
        return hash(self._uid)

    def __post_init__(self, init_nodes: List[Node], init_edges: List[Edge]):
        if init_nodes:
            for node in init_nodes:
                self.add_node(node)

        if init_edges:
            for edge in init_edges:
                self.add_edge(edge)

    def add_node(self, node: Node) -> None:
        self.nodes._store.append(node)

        if node.category == NodeCategory.I:
            self.inodes._store.append(node)
        else:
            self.snodes._store.append(node)

        self.incoming_nodes[node] = Nodes()
        self.incoming_edges[node] = Edges()
        self.outgoing_nodes[node] = Nodes()
        self.outgoing_edges[node] = Edges()

    def remove_node(self, node: Node) -> None:
        self.nodes._store.remove(node)

        if node.category == NodeCategory.I:
            self.inodes._store.remove(node)
        else:
            self.snodes._store.remove(node)

        for edge in self.edges:
            if node == edge.start or node == edge.end:
                self.remove_edge(edge)

        del self.incoming_nodes[node]
        del self.incoming_edges[node]
        del self.outgoing_nodes[node]
        del self.outgoing_edges[node]

    def add_edge(self, edge: Edge) -> None:
        self.edges._store.append(edge)

        if edge.start not in self.nodes:
            self.add_node(edge.start)

        if edge.end not in self.nodes:
            self.add_node(edge.end)

        self.outgoing_edges[edge.start]._store.append(edge)
        self.incoming_edges[edge.end]._store.append(edge)
        self.outgoing_nodes[edge.start]._store.append(edge.end)
        self.outgoing_nodes[edge.end]._store.append(edge.start)

    def remove_edge(self, edge: Edge) -> None:
        self.edges._store.remove(edge)

        self.outgoing_edges[edge.start]._store.remove(edge)
        self.incoming_edges[edge.end]._store.remove(edge)
        self.outgoing_nodes[edge.start]._store.remove(edge.end)
        self.incoming_nodes[edge.end]._store.remove(edge.start)

    @staticmethod
    def from_ova(
        obj: Dict[str, Any],
        key: Optional[str] = None,
        nlp: Optional[Callable[[str], Any]] = None,
    ) -> Graph:
        analysis = obj.get("analysis")

        g = Graph(
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

        if key:
            g.key = key

        node_dict = {}

        for node_obj in obj.get("nodes"):
            node = Node.from_ova(node_obj, nlp)
            node_dict[node.key] = node
            g.add_node(node)

        for edge in obj.get("edges"):
            g.add_edge(Edge.from_ova(edge, node_dict, nlp))

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
        key: Optional[str] = None,
        nlp: Optional[Callable[[str], Any]] = None,
    ) -> Graph:

        g = Graph(category=GraphCategory.AIF, document_date=None)

        if key:
            g.key = key

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
        key: Optional[str] = None,
        nlp: Optional[Callable[[str], Any]] = None,
    ) -> Graph:
        if "analysis" in obj:
            return Graph.from_ova(obj, key, nlp)
        else:
            return Graph.from_aif(obj, key, nlp)

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
        g = gv.Digraph(name=str(self.key), strict=True, format=format, engine=engine,)
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
            path = path / f"{self.key}.json"

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
        filename = self.key
        directory = path

        if path.is_file():
            filename = path.name
            directory = path.parent

        g = self.to_gv(format, engine)
        g.render(
            filename=str(filename), directory=str(directory), cleanup=True, view=view
        )

    open = from_file
    open_folder = from_folder
    to_folder = to_file
    save = to_file

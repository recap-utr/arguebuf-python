from __future__ import absolute_import, annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Set, Callable
from pathlib import Path
import json

import networkx as nx
import graphviz as gv
from enum import Enum

from . import utils
from .node import Node, NodeCategory
from .edge import Edge
from .analysis import Analysis


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
    nodes: List[Node] = field(init=False, default_factory=list)
    inodes: List[Node] = field(init=False, default_factory=list)
    snodes: List[Node] = field(init=False, default_factory=list)
    edges: List[Edge] = field(init=False, default_factory=list)
    incoming_nodes: Dict[Node, List[Node]] = field(init=False, default_factory=dict)
    incoming_edges: Dict[Node, List[Edge]] = field(init=False, default_factory=dict)
    outgoing_nodes: Dict[Node, List[Node]] = field(init=False, default_factory=dict)
    outgoing_edges: Dict[Node, List[Edge]] = field(init=False, default_factory=dict)
    participants: List[Any] = None
    analysis: Analysis = None
    category: GraphCategory = GraphCategory.OTHER

    @property
    def _uid(self):
        return self.key

    def __hash__(self):
        return hash(self._uid)

    def add_node(self, node: Node) -> None:
        self.nodes.append(node)

        if node.category == NodeCategory.I:
            self.inodes.append(node)
        else:
            self.snodes.append(node)

        self.incoming_nodes[node] = []
        self.incoming_edges[node] = []
        self.outgoing_nodes[node] = []
        self.outgoing_edges[node] = []

    def remove_node(self, node: Node) -> None:
        self.nodes.remove(node)

        if node.category == NodeCategory.I:
            self.inodes.remove(node)
        else:
            self.snodes.remove(node)

        for edge in self.edges:
            if node == edge.start or node == edge.end:
                self.remove_edge(edge)

        del self.incoming_nodes[node]
        del self.incoming_edges[node]
        del self.outgoing_nodes[node]
        del self.outgoing_edges[node]

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

        if edge.start not in self.nodes:
            self.add_node(edge.start)
        if edge.end not in self.nodes:
            self.add_node(edge.end)

        self.outgoing_edges[edge.start].append(edge)
        self.incoming_edges[edge.end].append(edge)
        self.outgoing_nodes[edge.start] = edge.end
        self.outgoing_nodes[edge.end] = edge.start

    def remove_edge(self, edge: Edge) -> None:
        self.edges.remove(edge)

        self.outgoing_edges[edge.start].remove(edge)
        self.incoming_edges[edge.end].remove(edge)
        self.outgoing_nodes[edge.start].remove(edge.end)
        self.incoming_nodes[edge.end].remove(edge.start)

    @staticmethod
    def from_ova(
        obj: Dict[str, Any],
        key: Optional[str] = None,
        nlp: Optional[Callable[[str], Any]] = None,
    ) -> Graph:
        g = Graph(
            participants=obj.get("participants"),
            analysis=Analysis.from_ova(obj.get("analysis"), nlp),
            category=GraphCategory.OVA,
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

        return g

    def to_ova(self) -> dict:
        return {
            "nodes": [node.to_ova() for node in self.nodes],
            "edges": [edge.to_ova() for edge in self.edges],
            "participants": self.participants if self.participants else [],
            "analysis": self.analysis.to_ova() if self.analysis else {},
        }

    @staticmethod
    def from_aif(
        obj: Dict[str, Any],
        key: Optional[str] = None,
        nlp: Optional[Callable[[str], Any]] = None,
    ) -> Graph:

        g = Graph(category=GraphCategory.AIF)

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
    def open(path: Path, nlp: Optional[Callable[[str], Any]] = None) -> Graph:
        with path.open("r") as file:
            return Graph.from_dict(json.load(file), path.stem, nlp)

    def save(self, path: Path) -> None:
        if path.is_dir():
            path = path / f"{self.key}.json"

        with path.open("w") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=4)

    @staticmethod
    def open_folder(
        path: Path, nlp: Optional[Callable[[str], Any]] = None, suffix: str = ".json"
    ) -> List[Graph]:
        files = path.rglob(f"*{suffix}")
        return [Graph.open(file, nlp) for file in files]

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

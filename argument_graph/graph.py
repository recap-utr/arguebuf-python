from __future__ import absolute_import, annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Set
from pathlib import Path
import json

import networkx as nx
import pygraphviz as gv
from spacy.language import Language
from spacy.lang.en import English
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
    _nodes: List[Node] = field(init=False, default_factory=list)
    _inodes: List[Node] = field(init=False, default_factory=list)
    _snodes: List[Node] = field(init=False, default_factory=list)
    _edges: List[Edge] = field(init=False, default_factory=list)
    participants: List[Any] = None
    analysis: Analysis = None
    category: GraphCategory = GraphCategory.OTHER

    @property
    def nodes(self) -> List[Node]:
        return self._nodes

    @property
    def inodes(self) -> List[Node]:
        return self._inodes

    @property
    def snodes(self) -> List[Node]:
        return self._snodes

    @property
    def edges(self) -> List[Edge]:
        return self._edges

    def add_node(self, node: Node) -> None:
        self._nodes.append(node)

        if node.category == NodeCategory.I:
            self._inodes.append(node)
        else:
            self._snodes.append(node)

    def remove_node(self, node: Node) -> None:
        self._nodes.remove(node)

        if node.category == NodeCategory.I:
            self._inodes.remove(node)
        else:
            self._snodes.remove(node)

        for edge in self._edges:
            if node == edge.start or node == edge.end:
                self.remove_edge(edge)

    def add_edge(self, edge: Edge) -> None:
        self._edges.append(edge)

        if edge.start not in self._nodes:
            self.add_node(edge.start)
        if edge.end not in self._nodes:
            self.add_node(edge.end)

    def remove_edge(self, edge: Edge) -> None:
        self._edges.remove(edge)

    @staticmethod
    def from_ova(
        obj: Dict[str, Any], key: Optional[str] = None, nlp: Optional[Language] = None
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
            "participants": self.participants or [],
            "analysis": self.analysis.to_ova() or {},
        }

    @staticmethod
    def from_aif(
        obj: Dict[str, Any], key: Optional[str] = None, nlp: Optional[Language] = None
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
        obj: Dict[str, Any], key: Optional[str] = None, nlp: Optional[Language] = None
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

    @staticmethod
    def from_file(path: Path, nlp: Optional[Language] = None) -> Graph:
        with path.open("r") as file:
            return Graph.from_dict(json.load(file), path.stem, nlp)

    def to_file(self, path: Path) -> None:
        if path.is_dir():
            path = path / f"{self.key}.json"

        with path.open("w") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=4)

    @staticmethod
    def from_folder(
        path: Path, nlp: Optional[Language] = None, suffix: str = ".json"
    ) -> List[Graph]:
        files = path.rglob(f"*{suffix}")
        return [Graph.from_file(file, nlp) for file in files]

    def to_folder(self, path: Path) -> None:
        self.to_file(path)

    def to_nx(self) -> nx.DiGraph:
        g = nx.DiGraph()
        for edge in self.edges:
            edge.start.to_nx(g)
            edge.end.to_nx(g)
            edge.to_nx(g)

        return g

    def to_gv(self) -> gv.AGraph:
        g = gv.AGraph(strict=True, directed=True, rankdir="BT")
        for edge in self.edges:
            edge.start.to_gv(g)
            edge.end.to_gv(g)
            edge.to_gv(g)

        return g

    def draw(
        self, path: Path, format: str = "pdf", prog: str = "dot", args: str = ""
    ) -> None:
        g = self.to_gv()

        if path.is_dir():
            path = path / f"{self.key}.{format}"

        g.draw(path=str(path), format=format, prog=prog)

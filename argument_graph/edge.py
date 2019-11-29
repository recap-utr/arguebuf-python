from __future__ import absolute_import, annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Set

import networkx as nx
import pygraphviz as gv
from spacy.language import Language

from . import utils
from .node import Node
from .graph import Graph
from .analysis import Analysis


@dataclass
class Edge:
    """Edge in AIF format.

    Attributes `from` and `to` are mandatory.
    """

    nlp: Language
    start: Node
    end: Node
    key: int = field(default_factory=utils.unique_id)
    visible: bool = True
    annotator: str = ""
    date: str = ""

    @staticmethod
    def from_ova(obj: Any, nlp: Language, nodes: Dict[int, Node] = None) -> Edge:
        if not nodes:
            nodes = {}

        start_key = obj.get("from").get("id")
        end_key = obj.get("to").get("id")

        return Edge(
            start=nodes.get(start_key) or Node.from_ova(obj.get("from"), nlp),
            end=nodes.get(end_key) or Node.from_ova(obj.get("to"), nlp),
            visible=obj.get("visible"),
            annotator=obj.get("annotator"),
            date=obj.get("date"),
        )

    def to_ova(self) -> dict:
        return {
            "from": self.start.to_ova(),
            "to": self.end.to_ova(),
            "visible": self.visible,
            "annotator": self.annotator,
            "date": self.date or utils.ova_date(),
        }

    @staticmethod
    def from_aif(obj: Any, nlp: Language, nodes: Dict[int, Node]) -> Edge:
        start_key = obj.get("fromID")
        end_key = obj.get("toID")

        return Edge(
            nlp=nlp,
            start=nodes.get(start_key),
            end=nodes.get(end_key),
            key=obj.get("edgeID"),
        )

    def to_aif(self) -> dict:
        return {
            "edgeID": self.key,
            "fromID": self.start.to_aif(),
            "toID": self.end.to_aif(),
            "formEdgeID": None,
        }

    def to_nx(self, g: nx.DiGraph) -> None:
        g.add_edge(self.start.key, self.end.key)

    def to_gv(self, g: gv.AGraph, suffix: str = "") -> None:
        g.add_edge(f"{self.start.key}{suffix}", f"{self.end.key}{suffix}")

    def __eq__(self, other: Edge) -> bool:
        return self.start == other.start and self.end == other.end

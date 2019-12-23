from __future__ import absolute_import, annotations

from dataclasses import dataclass, field, InitVar
from typing import Any, Optional, Dict, Callable

import graphviz as gv
import networkx as nx
import pendulum

from . import dt
from .node import Node


@dataclass(eq=False)
class Edge:
    """Edge in AIF format."""

    key: int
    start: InitVar[Node]
    _start: Node = field(init=False)
    end: InitVar[Node]
    _end: Node = field(init=False)
    visible: bool = None
    annotator: str = None
    date: pendulum.DateTime = field(default_factory=pendulum.now)

    def __post_init__(self, start: Node, end: Node):
        self._start = start
        self._end = end

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @staticmethod
    def from_ova(
        obj: Any,
        key: int,
        nodes: Dict[int, Node] = None,
        nlp: Optional[Callable[[str], Any]] = None,
    ) -> Edge:
        if not nodes:
            nodes = {}

        start_key = int(obj.get("from").get("id"))
        end_key = int(obj.get("to").get("id"))

        return Edge(
            key=key,
            start=nodes.get(start_key) or Node.from_ova(obj.get("from"), nlp),
            end=nodes.get(end_key) or Node.from_ova(obj.get("to"), nlp),
            visible=obj.get("visible"),
            annotator=obj.get("annotator"),
            date=dt.from_ova(obj.get("date")),
        )

    def to_ova(self) -> dict:
        return {
            "from": self.start.to_ova(),
            "to": self.end.to_ova(),
            "visible": self.visible,
            "annotator": self.annotator,
            "date": dt.to_ova(self.date),
        }

    @staticmethod
    def from_aif(
        obj: Any, nodes: Dict[int, Node], nlp: Optional[Callable[[str], Any]] = None
    ) -> Edge:
        start_key = int(obj.get("fromID"))
        end_key = int(obj.get("toID"))

        return Edge(
            key=int(obj.get("edgeID")),
            start=nodes.get(start_key),
            end=nodes.get(end_key),
        )

    def to_aif(self) -> dict:
        return {
            "edgeID": str(self.key),
            "fromID": str(self.start.key),
            "toID": str(self.end.key),
            "formEdgeID": None,
        }

    def to_nx(self, g: nx.DiGraph) -> None:
        g.add_edge(self.start.key, self.end.key)

    def to_gv(
        self, g: gv.Digraph, color="#666666", prefix: str = "", suffix: str = ""
    ) -> None:
        g.edge(
            f"{prefix}{self.start.key}{suffix}",
            f"{prefix}{self.end.key}{suffix}",
            color=color,
        )

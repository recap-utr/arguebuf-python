from __future__ import absolute_import, annotations

import typing as t

import graphviz as gv
import networkx as nx
import pendulum

from . import dt
from .node import Node
from .utils import MISSING


class Edge:
    """Edge in AIF format."""

    __slots__ = (
        "_key",
        "_start",
        "_end",
        "visible",
        "annotator",
        "date",
    )

    _key: int
    _start: Node
    _end: Node
    visible: bool
    annotator: str
    date: pendulum.DateTime

    def __init__(
        self,
        key: int,
        start: Node,
        end: Node,
        visible: t.Optional[bool] = None,
        annotator: t.Optional[str] = None,
        date: t.Union[MISSING, None, pendulum.DateTime] = MISSING,
    ):
        self._key = key
        self._start = start
        self._end = end
        self.visible = visible
        self.annotator = annotator
        self.date = pendulum.now() if date is MISSING else date

    @property
    def key(self):
        return self._key

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @staticmethod
    def from_ova(
        obj: t.Any,
        key: int,
        nodes: t.Dict[int, Node] = None,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
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
        obj: t.Any,
        nodes: t.Dict[int, Node],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
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

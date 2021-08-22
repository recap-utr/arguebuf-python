from __future__ import absolute_import, annotations

import typing as t

import graphviz as gv
import networkx as nx
from arg_services.graph.v1 import graph_pb2

from arguebuf.data import Metadata, Userdata

from . import dt, utils
from .node import Node


class Edge:
    """Edge in AIF format."""

    __slots__ = (
        "_id",
        "_source",
        "_target",
        "_metadata",
        "userdata",
    )

    _id: str
    _source: Node
    _target: Node
    _metadata: Metadata
    userdata: Userdata

    def __init__(
        self,
        id: str,
        source: Node,
        target: Node,
        metadata: t.Optional[Metadata] = None,
        userdata: t.Optional[Userdata] = None,
    ):
        self._id = id
        self._source = source
        self._target = target
        self._metadata = metadata or Metadata()
        self.userdata = userdata or {}

        self.__post_init__()

    def __post_init__(self):
        pass

    def __repr__(self):
        return utils.class_repr(
            self,
            [str(self._id), f"{self._source.__repr__()}->{self._target.__repr__()}"],
        )

    @property
    def id(self) -> str:
        return self._id

    @property
    def source(self) -> Node:
        return self._source

    @property
    def target(self) -> Node:
        return self._target

    @classmethod
    def from_ova(
        cls,
        obj: t.Mapping[str, t.Any],
        nodes: t.Mapping[str, Node] = None,
    ) -> Edge:
        if not nodes:
            nodes = {}

        source_id = str(obj["from"]["id"])
        target_id = str(obj["to"]["id"])
        timestamp = dt.from_ova(obj.get("data"))

        return cls(
            id=utils.unique_id(),
            source=nodes[source_id],
            target=nodes[target_id],
            metadata=Metadata(timestamp, timestamp) if timestamp else Metadata(),
        )

    @classmethod
    def from_aif(
        cls,
        obj: t.Any,
        nodes: t.Mapping[str, Node],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Edge:
        start_id = obj.get("fromID")
        end_id = obj.get("toID")

        return cls(
            id=obj["edgeID"],
            source=nodes[start_id],
            target=nodes[end_id],
        )

    def to_aif(self) -> t.Dict[str, t.Any]:
        return {
            "edgeID": str(self.id),
            "fromID": str(self.source.id),
            "toID": str(self.target.id),
            "formEdgeID": None,
        }

    @classmethod
    def from_protobuf(
        cls,
        id: str,
        obj: graph_pb2.Edge,
        nodes: t.Mapping[str, Node],
        metadata_class: t.Type[Metadata],
    ) -> Edge:
        return cls(
            id,
            nodes[obj.source],
            nodes[obj.target],
            metadata_class.from_protobuf(obj.metadata),
            dict(obj.userdata.items()),
        )

    def to_protobuf(self) -> graph_pb2.Edge:
        obj = graph_pb2.Edge(
            source=self._source.id,
            target=self._target.id,
            metadata=self._metadata.to_protobuf(),
        )
        obj.userdata.update(self.userdata)

        return obj

    def to_nx(self, g: nx.DiGraph) -> None:
        g.add_edge(self.source.id, self.target.id)

    def to_gv(self, g: gv.Digraph) -> None:
        g.edge(
            self.source._id,
            self.target._id,
        )

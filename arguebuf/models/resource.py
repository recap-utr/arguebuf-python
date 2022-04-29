from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from arg_services.graph.v1 import graph_pb2
from arguebuf.models import Userdata
from arguebuf.models.metadata import Metadata
from arguebuf.schema import ova
from arguebuf.services import dt, utils
from pendulum.datetime import DateTime


@dataclass()
class Resource:
    text: t.Any
    title: t.Optional[str] = None
    source: t.Optional[str] = None
    timestamp: t.Optional[DateTime] = None
    metadata: Metadata = field(default_factory=Metadata)
    userdata: Userdata = field(default_factory=dict)
    _id: str = field(default_factory=utils.uuid)

    @property
    def id(self) -> str:
        return self._id

    @property
    def plain_text(self) -> str:
        """Generate a string from Resource object."""
        return utils.xstr(self.text)

    def to_protobuf(self) -> graph_pb2.Resource:
        """Export Resource object into a Graph's Resource object in PROTOBUF format."""
        obj = graph_pb2.Resource(
            text=self.plain_text, metadata=self.metadata.to_protobuf()
        )
        obj.userdata.update(self.userdata)

        if title := self.title:
            obj.title = title

        if source := self.source:
            obj.source = source

        return obj

    @classmethod
    def from_protobuf(
        cls,
        id: str,
        obj: graph_pb2.Resource,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Resource:
        """Generate Resource object from PROTOBUF format Graph's Resource object."""
        return cls(
            utils.parse(obj.text, nlp),
            obj.title,
            obj.source,
            dt.from_protobuf(obj.timestamp),
            Metadata.from_protobuf(obj.metadata),
            dict(obj.userdata.items()),
            id,
        )

    @classmethod
    def from_ova(
        cls, obj: ova.Analysis, nlp: t.Optional[t.Callable[[str], t.Any]]
    ) -> Resource:
        return cls(
            utils.parse(obj.get("plain_txt"), nlp),
            obj.get("documentTitle"),
            obj.get("documentSource"),
            dt.from_format(obj.get("documentDate"), ova.DATE_FORMAT_ANALYSIS),
        )

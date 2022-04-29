from __future__ import annotations

import typing as t

from arg_services.graph.v1 import graph_pb2
from arguebuf.models.resource import Resource
from arguebuf.services import utils


class Reference:
    _resource: t.Optional[Resource]
    offset: t.Optional[int]
    text: t.Any

    def __init__(
        self,
        resource: t.Optional[Resource] = None,
        offset: t.Optional[int] = None,
        text: t.Optional[t.Any] = None,
    ) -> None:
        self._resource = resource
        self.offset = offset
        self.text = text

    @property
    def plain_text(self) -> str:
        """Generate a string from Resource object."""
        return utils.xstr(self.text)

    @property
    def resource(self) -> t.Optional[Resource]:
        return self._resource

    def to_protobuf(self) -> graph_pb2.Reference:
        """Export Resource object into a Graph's Resource object in PROTOBUF format."""
        obj = graph_pb2.Reference(text=self.plain_text)

        if resource := self._resource:
            obj.resource = resource.id

        if offset := self.offset:
            obj.offset = offset

        return obj

    @classmethod
    def from_protobuf(
        cls,
        obj: graph_pb2.Reference,
        resources: t.Mapping[str, Resource],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> t.Optional[Reference]:
        """Generate Resource object from PROTOBUF format Graph's Resource object."""
        if obj.text:
            if obj.resource:
                return cls(
                    resources[obj.resource],
                    obj.offset,
                    utils.parse(obj.text, nlp),
                )

            else:
                return cls(
                    None,
                    None,
                    utils.parse(obj.text, nlp),
                )

        return None

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import pendulum
from arg_services.graph.v1 import graph_pb2

from arguebuf import dt, utils

Metadata = t.Dict[str, t.Any]


@dataclass()
class Participant:
    _id: str
    name: t.Optional[str] = None
    username: t.Optional[str] = None
    email: t.Optional[str] = None
    url: t.Optional[str] = None
    location: t.Optional[str] = None
    description: t.Optional[str] = None
    created: pendulum.DateTime = field(default_factory=pendulum.now)
    updated: pendulum.DateTime = field(default_factory=pendulum.now)
    metadata: Metadata = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self._id

    def to_protobuf(self) -> graph_pb2.Participant:
        obj = graph_pb2.Participant(
            name=self.name or "",
            username=self.username or "",
            email=self.email or "",
            url=self.url or "",
            location=self.location or "",
            description=self.description or "",
        )
        dt.to_protobuf(self.created, obj.created)
        dt.to_protobuf(self.updated, obj.updated)
        obj.metadata.update(self.metadata)

        return obj

    @classmethod
    def from_protobuf(cls, id: str, obj: graph_pb2.Participant) -> Participant:
        return cls(
            id,
            obj.name,
            obj.username,
            obj.email,
            obj.url,
            obj.location,
            obj.description,
            dt.from_protobuf(obj.created),
            dt.from_protobuf(obj.updated),
            dict(obj.metadata.items()),
        )


@dataclass()
class Resource:
    _id: str
    text: t.Any
    title: t.Optional[str] = None
    source: t.Optional[str] = None
    created: pendulum.DateTime = field(default_factory=pendulum.now)
    updated: pendulum.DateTime = field(default_factory=pendulum.now)
    metadata: Metadata = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self._id

    @property
    def plain_text(self) -> str:
        return utils.xstr(self.text)

    def to_protobuf(self) -> graph_pb2.Resource:
        obj = graph_pb2.Resource(text=self.plain_text)
        dt.to_protobuf(self.created, obj.created)
        dt.to_protobuf(self.updated, obj.updated)
        obj.metadata.update(self.metadata)

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
        return cls(
            id,
            utils.parse(obj.text, nlp),
            obj.title,
            obj.source,
            dt.from_protobuf(obj.created),
            dt.from_protobuf(obj.updated),
            dict(obj.metadata.items()),
        )


@dataclass()
class Reference:
    resource: t.Optional[Resource]
    offset: t.Optional[int]
    text: t.Any
    metadata: Metadata = field(default_factory=dict)

    @property
    def plain_text(self) -> str:
        return utils.xstr(self.text)

    def to_protobuf(self) -> graph_pb2.Reference:
        obj = graph_pb2.Reference(text=self.plain_text)

        if resource := self.resource:
            obj.resource = resource.id

        if offset := self.offset:
            obj.offset = offset

        obj.metadata.update(self.metadata)

        return obj

    @classmethod
    def from_protobuf(
        cls,
        obj: graph_pb2.Reference,
        resources: t.Mapping[str, Resource],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> t.Optional[Reference]:
        if obj.text:
            if obj.resource:
                return cls(
                    resources[obj.resource],
                    obj.offset,
                    utils.parse(obj.text, nlp),
                    dict(obj.metadata.items()),
                )

            else:
                return cls(
                    None,
                    None,
                    utils.parse(obj.text, nlp),
                    dict(obj.metadata.items()),
                )

        return None

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import pendulum
from arg_services.graph.v1 import graph_pb2

from arguebuf import utils

Userdata = t.Dict[str, t.Any]


@dataclass()
class Metadata:
    created: pendulum.DateTime = field(default_factory=pendulum.now)
    updated: pendulum.DateTime = field(default_factory=pendulum.now)

    def to_protobuf(self) -> graph_pb2.Metadata:
        obj = graph_pb2.Metadata()

        if self.created:
            obj.created.FromDatetime(self.created)

        if self.updated:
            obj.updated.FromDatetime(self.updated)

        return obj

    @classmethod
    def from_protobuf(cls, obj: graph_pb2.Metadata) -> Metadata:
        return cls(
            pendulum.instance(obj.created.ToDatetime()),
            pendulum.instance(obj.updated.ToDatetime()),
        )


@dataclass()
class Analyst:
    name: str
    email: str
    userdata: Userdata = field(default_factory=dict)

    def to_protobuf(self) -> graph_pb2.Analyst:
        obj = graph_pb2.Analyst(name=self.name, email=self.email)
        obj.userdata.update(self.userdata)

        return obj

    @classmethod
    def from_protobuf(cls, obj: graph_pb2.Analyst) -> Analyst:
        return cls(obj.name, obj.email, dict(obj.userdata.items()))


@dataclass()
class Resource:
    id: str
    text: t.Any
    title: t.Optional[str] = None
    source: t.Optional[str] = None
    timestamp: t.Optional[pendulum.DateTime] = None
    # metadata: Metadata = field(default_factory=Metadata)
    userdata: Userdata = field(default_factory=dict)

    @property
    def plain_text(self) -> str:
        return utils.xstr(self.text)

    def to_protobuf(self) -> graph_pb2.Resource:
        obj = graph_pb2.Resource(text=self.plain_text)
        obj.userdata.update(self.userdata)

        if title := self.title:
            obj.title = title

        if source := self.source:
            obj.source = source

        if timestamp := self.timestamp:
            obj.timestamp.FromDatetime(timestamp)

        return obj

    @classmethod
    def from_protobuf(
        cls, id: str, obj: graph_pb2.Resource, nlp: t.Callable[[str], t.Any]
    ) -> Resource:
        return cls(
            id,
            utils.parse(obj.text, nlp),
            obj.title,
            obj.source,
            pendulum.instance(obj.timestamp.ToDatetime()),
            dict(obj.userdata.items()),
        )


@dataclass()
class Anchor:
    resource: t.Optional[Resource]
    offset: t.Optional[int]
    text: t.Any
    userdata: Userdata = field(default_factory=dict)

    @property
    def plain_text(self) -> str:
        return utils.xstr(self.text)

    def to_protobuf(self) -> graph_pb2.Anchor:
        obj = graph_pb2.Anchor(text=self.plain_text)

        if resource := self.resource:
            obj.resource = resource.id

        if offset := self.offset:
            obj.offset = offset

        obj.userdata.update(self.userdata)

        return obj

    @classmethod
    def from_protobuf(
        cls,
        obj: graph_pb2.Anchor,
        resources: t.Mapping[str, Resource],
        nlp: t.Callable[[str], t.Any],
    ) -> Anchor:
        return cls(
            resources[obj.resource],
            obj.offset,
            utils.parse(obj.text, nlp),
            dict(obj.userdata.items()),
        )

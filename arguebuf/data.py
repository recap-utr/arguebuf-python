from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import pendulum
from arg_services.graph.v1 import graph_pb2
from pendulum.datetime import DateTime

from arguebuf import dt, ova, utils

Userdata = t.Dict[str, t.Any]


class Analyst:
    name: t.Optional[str]
    email: t.Optional[str]
    userdata: Userdata
    _id: str

    def __init__(
        self,
        name: t.Optional[str] = None,
        email: t.Optional[str] = None,
        userdata: t.Optional[Userdata] = None,
        id: t.Optional[str] = None,
    ) -> None:
        self.name = name
        self.email = email
        self.userdata = userdata or {}
        self._id = id or utils.uuid()

    @property
    def id(self) -> str:
        return self._id

    def to_protobuf(self) -> graph_pb2.Analyst:
        """Export Analyst object into a Graph's Analyst object in PROTOBUF format."""
        obj = graph_pb2.Analyst(
            name=self.name or "",
            email=self.email or "",
        )
        obj.userdata.update(self.userdata)

        return obj

    @classmethod
    def from_protobuf(cls, id: str, obj: graph_pb2.Analyst) -> Analyst:
        """Generate Analyst object from PROTOBUF format Graph's Analyst object."""
        return cls(
            obj.name,
            obj.email,
            dict(obj.userdata.items()),
            id,
        )


class Metadata:
    created: DateTime
    updated: DateTime
    # _analyst: t.Optional[Analyst] = None

    def __init__(
        self, created: t.Optional[DateTime] = None, updated: t.Optional[DateTime] = None
    ) -> None:
        now = pendulum.now()

        self.created = created or now
        self.updated = updated or now

    # @property
    # def analyst(self) -> t.Optional[Analyst]:
    #     return self._analyst

    def update(self) -> None:
        self.updated = pendulum.now()

    def to_protobuf(self) -> graph_pb2.Metadata:
        obj = graph_pb2.Metadata()

        # if analyst := self._analyst:
        #     obj.analyst = analyst.id

        dt.to_protobuf(self.created, obj.created)
        dt.to_protobuf(self.updated, obj.updated)

        return obj

    @classmethod
    def from_protobuf(cls, obj: graph_pb2.Metadata) -> Metadata:
        return cls(
            dt.from_protobuf(obj.created),
            dt.from_protobuf(obj.updated),
            # analysts[obj.analyst]
        )


class Participant:
    name: t.Optional[str]
    username: t.Optional[str]
    email: t.Optional[str]
    url: t.Optional[str]
    location: t.Optional[str]
    description: t.Optional[str]
    metadata: Metadata
    userdata: Userdata
    _id: str

    def __init__(
        self,
        name: t.Optional[str] = None,
        username: t.Optional[str] = None,
        email: t.Optional[str] = None,
        url: t.Optional[str] = None,
        location: t.Optional[str] = None,
        description: t.Optional[str] = None,
        metadata: t.Optional[Metadata] = None,
        userdata: t.Optional[Userdata] = None,
        id: t.Optional[str] = None,
    ) -> None:
        self.name = name
        self.username = username
        self.email = email
        self.url = url
        self.location = location
        self.description = description
        self.metadata = metadata or Metadata()
        self.userdata = userdata or {}
        self._id = id or utils.uuid()

    @property
    def id(self) -> str:
        return self._id

    def to_protobuf(self) -> graph_pb2.Participant:
        """Export Participant object into a Graph's Participant object in PROTOBUF format."""
        obj = graph_pb2.Participant(
            name=self.name or "",
            username=self.username or "",
            email=self.email or "",
            url=self.url or "",
            location=self.location or "",
            description=self.description or "",
            metadata=self.metadata.to_protobuf(),
        )
        obj.userdata.update(self.userdata)

        return obj

    @classmethod
    def from_protobuf(cls, id: str, obj: graph_pb2.Participant) -> Participant:
        """Generate Participant object from PROTOBUF format Graph's Participant object."""
        return cls(
            obj.name,
            obj.username,
            obj.email,
            obj.url,
            obj.location,
            obj.description,
            Metadata.from_protobuf(obj.metadata),
            dict(obj.userdata.items()),
            id,
        )

    @classmethod
    def from_ova(cls, obj: ova.Participant) -> Participant:
        return cls(name=f"{obj['firstname']} {obj['surname']}", id=str(obj["id"]))


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

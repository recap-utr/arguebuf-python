from __future__ import annotations

import typing as t

from arg_services.graph.v1 import graph_pb2
from arguebuf.models import Userdata
from arguebuf.models.metadata import Metadata
from arguebuf.schema import ova
from arguebuf.services import utils


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

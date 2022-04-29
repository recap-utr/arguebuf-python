from __future__ import annotations

import typing as t

from arg_services.graph.v1 import graph_pb2
from arguebuf.models import Userdata
from arguebuf.services import utils


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

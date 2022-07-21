from __future__ import annotations

import typing as t

import pendulum
from arg_services.graph.v1 import graph_pb2
from arguebuf.services import dt
from pendulum.datetime import DateTime


class Metadata:
    created: DateTime
    updated: DateTime
    # _analyst: t.Optional[Analyst] = None

    def __init__(
        self,
        created: t.Optional[DateTime] = None,
        updated: t.Optional[DateTime] = None,
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

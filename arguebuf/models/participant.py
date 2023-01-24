from __future__ import annotations

import typing as t


from arguebuf.models.metadata import Metadata
from arguebuf.models.userdata import Userdata
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

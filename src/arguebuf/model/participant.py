from dataclasses import dataclass, field
from typing import TypedDict, overload

from arguebuf.model.metadata import Metadata
from arguebuf.model.userdata import JSON_OBJECT, JsonObject, own
from arguebuf.model.utils import Entity, uuid

__all__ = (
    "Participant",
    "ParticipantChanges",
)


# lazily evaluated, so the overloads below can specialize the class they belong to
type _Participant[T] = Participant[T]


@dataclass(slots=True, frozen=True, eq=False)
class Participant[P = JsonObject](Entity):
    """Person who authored atom nodes of the argument graph."""

    name: str | None
    username: str | None
    email: str | None
    url: str | None
    location: str | None
    description: str | None
    metadata: Metadata = field(repr=False)
    userdata: P = field(repr=False)
    id: str

    @overload
    def __init__(
        self: _Participant[JsonObject],
        name: str | None = None,
        *,
        username: str | None = None,
        email: str | None = None,
        url: str | None = None,
        location: str | None = None,
        description: str | None = None,
        metadata: Metadata | None = None,
        userdata: JsonObject = ...,
        id: str | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str | None = None,
        *,
        username: str | None = None,
        email: str | None = None,
        url: str | None = None,
        location: str | None = None,
        description: str | None = None,
        metadata: Metadata | None = None,
        userdata: P,
        id: str | None = None,
    ) -> None: ...

    def __init__(
        self: _Participant[object],
        name: str | None = None,
        *,
        username: str | None = None,
        email: str | None = None,
        url: str | None = None,
        location: str | None = None,
        description: str | None = None,
        metadata: Metadata | None = None,
        userdata: object = JSON_OBJECT,
        id: str | None = None,
    ) -> None:
        # frozen dataclasses can only be initialized via object.__setattr__
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "username", username)
        object.__setattr__(self, "email", email)
        object.__setattr__(self, "url", url)
        object.__setattr__(self, "location", location)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "metadata", metadata or Metadata())
        object.__setattr__(self, "userdata", own(userdata))
        object.__setattr__(self, "id", uuid() if id is None else id)


class ParticipantChanges[P](TypedDict, total=False):
    """Fields of a participant that `Graph.update_participant` changes."""

    name: str | None
    username: str | None
    email: str | None
    url: str | None
    location: str | None
    description: str | None
    metadata: Metadata
    userdata: P

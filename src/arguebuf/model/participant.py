from dataclasses import KW_ONLY, dataclass, field
from typing import overload

from arguebuf.model.metadata import Metadata
from arguebuf.model.userdata import JSON_OBJECT, JsonObject, own
from arguebuf.model.utils import Entity, uuid

__all__ = ("AbstractParticipant", "Participant")


@dataclass(slots=True, frozen=True, eq=False)
class AbstractParticipant(Entity):
    """Participant without userdata, the type of references from atom nodes."""

    name: str | None = None
    _: KW_ONLY
    username: str | None = None
    email: str | None = None
    url: str | None = None
    location: str | None = None
    description: str | None = None
    metadata: Metadata = field(default_factory=Metadata, repr=False)
    _id: str = field(default_factory=uuid)


# lazily evaluated, so the overloads below can specialize the class they belong to
type _Participant[T] = Participant[T]


@dataclass(slots=True, frozen=True, eq=False)
class Participant[P = JsonObject](AbstractParticipant):
    """Person who authored atom nodes of the argument graph."""

    userdata: P = field(repr=False, kw_only=True)

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
        AbstractParticipant.__init__(
            self,
            name,
            username=username,
            email=email,
            url=url,
            location=location,
            description=description,
            metadata=metadata or Metadata(),
            _id=uuid() if id is None else id,
        )
        # frozen dataclasses can only be initialized via object.__setattr__
        object.__setattr__(self, "userdata", own(userdata))

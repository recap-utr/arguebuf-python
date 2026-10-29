from dataclasses import dataclass, field
from datetime import datetime
from typing import TypedDict, overload

from arguebuf.model.metadata import Metadata
from arguebuf.model.userdata import JSON_OBJECT, JsonObject, own
from arguebuf.model.utils import Entity, uuid

__all__ = (
    "Resource",
    "ResourceChanges",
)


# lazily evaluated, so the overloads below can specialize the class they belong to
type _Resource[T] = Resource[T]


@dataclass(slots=True, frozen=True, eq=False)
class Resource[R = JsonObject](Entity):
    """Source document that atom nodes may reference."""

    text: str
    title: str | None
    source: str | None
    timestamp: datetime | None
    metadata: Metadata = field(repr=False)
    userdata: R = field(repr=False)
    id: str

    @overload
    def __init__(
        self: _Resource[JsonObject],
        text: str,
        *,
        title: str | None = None,
        source: str | None = None,
        timestamp: datetime | None = None,
        metadata: Metadata | None = None,
        userdata: JsonObject = ...,
        id: str | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        text: str,
        *,
        title: str | None = None,
        source: str | None = None,
        timestamp: datetime | None = None,
        metadata: Metadata | None = None,
        userdata: R,
        id: str | None = None,
    ) -> None: ...

    def __init__(
        self: _Resource[object],
        text: str,
        *,
        title: str | None = None,
        source: str | None = None,
        timestamp: datetime | None = None,
        metadata: Metadata | None = None,
        userdata: object = JSON_OBJECT,
        id: str | None = None,
    ) -> None:
        # frozen dataclasses can only be initialized via object.__setattr__
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "timestamp", timestamp)
        object.__setattr__(self, "metadata", metadata or Metadata())
        object.__setattr__(self, "userdata", own(userdata))
        object.__setattr__(self, "id", uuid() if id is None else id)


class ResourceChanges[R](TypedDict, total=False):
    """Fields of a resource that `Graph.update_resource` changes."""

    text: str
    title: str | None
    source: str | None
    timestamp: datetime | None
    metadata: Metadata
    userdata: R

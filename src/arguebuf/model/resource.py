from dataclasses import KW_ONLY, dataclass, field
from datetime import datetime
from typing import overload

from arguebuf.model.metadata import Metadata
from arguebuf.model.userdata import JSON_OBJECT, JsonObject, own
from arguebuf.model.utils import Entity, uuid

__all__ = ("AbstractResource", "Resource")


@dataclass(slots=True, eq=False)
class AbstractResource(Entity):
    """Resource without userdata, the type of references from atom nodes."""

    text: str
    _: KW_ONLY
    title: str | None = None
    source: str | None = None
    timestamp: datetime | None = None
    metadata: Metadata = field(default_factory=Metadata, repr=False)
    _id: str = field(default_factory=uuid)


# lazily evaluated, so the overloads below can specialize the class they belong to
type _Resource[T] = Resource[T]


@dataclass(slots=True, eq=False)
class Resource[R = JsonObject](AbstractResource):
    """Source document that atom nodes may reference."""

    userdata: R = field(repr=False, kw_only=True)

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
        AbstractResource.__init__(
            self,
            text,
            title=title,
            source=source,
            timestamp=timestamp,
            metadata=metadata or Metadata(),
            _id=uuid() if id is None else id,
        )
        self.userdata = own(userdata)

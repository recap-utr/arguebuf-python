from dataclasses import dataclass, field
from typing import TypedDict, overload

from arguebuf.model.userdata import JSON_OBJECT, JsonObject, own
from arguebuf.model.utils import Entity, uuid

__all__ = (
    "Analyst",
    "AnalystChanges",
)


# lazily evaluated, so the overloads below can specialize the class they belong to
type _Analyst[T] = Analyst[T]


@dataclass(slots=True, frozen=True, eq=False)
class Analyst[N = JsonObject](Entity):
    """Person who annotated the argument graph."""

    name: str | None
    email: str | None
    userdata: N = field(repr=False)
    id: str

    @overload
    def __init__(
        self: _Analyst[JsonObject],
        name: str | None = None,
        *,
        email: str | None = None,
        userdata: JsonObject = ...,
        id: str | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str | None = None,
        *,
        email: str | None = None,
        userdata: N,
        id: str | None = None,
    ) -> None: ...

    def __init__(
        self: _Analyst[object],
        name: str | None = None,
        *,
        email: str | None = None,
        userdata: object = JSON_OBJECT,
        id: str | None = None,
    ) -> None:
        # frozen dataclasses can only be initialized via object.__setattr__
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "email", email)
        object.__setattr__(self, "userdata", own(userdata))
        object.__setattr__(self, "id", uuid() if id is None else id)


class AnalystChanges[N](TypedDict, total=False):
    """Fields of an analyst that `Graph.update_analyst` changes."""

    name: str | None
    email: str | None
    userdata: N

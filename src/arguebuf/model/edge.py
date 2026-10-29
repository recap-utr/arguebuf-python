from dataclasses import dataclass, field
from typing import TypedDict, overload

from arguebuf.model.metadata import Metadata
from arguebuf.model.userdata import JSON_OBJECT, JsonObject, own
from arguebuf.model.utils import Entity, uuid

__all__ = (
    "Edge",
    "EdgeChanges",
)


# lazily evaluated, so the overloads below can specialize the class they belong to
type _Edge[T] = Edge[T]


@dataclass(slots=True, frozen=True, eq=False)
class Edge[E = JsonObject](Entity):
    """Directed connection from a source node to a target node, given by their ids.

    The nodes are looked up via the graph, e.g. `graph.nodes[edge.source]`.
    """

    source: str
    target: str
    metadata: Metadata = field(repr=False)
    userdata: E = field(repr=False)
    id: str

    @overload
    def __init__(
        self: _Edge[JsonObject],
        source: str,
        target: str,
        *,
        metadata: Metadata | None = None,
        userdata: JsonObject = ...,
        id: str | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        source: str,
        target: str,
        *,
        metadata: Metadata | None = None,
        userdata: E,
        id: str | None = None,
    ) -> None: ...

    def __init__(
        self: _Edge[object],
        source: str,
        target: str,
        *,
        metadata: Metadata | None = None,
        userdata: object = JSON_OBJECT,
        id: str | None = None,
    ) -> None:
        # frozen dataclasses can only be initialized via object.__setattr__
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "metadata", metadata or Metadata())
        object.__setattr__(self, "userdata", own(userdata))
        object.__setattr__(self, "id", uuid() if id is None else id)


class EdgeChanges[E](TypedDict, total=False):
    """Fields of an edge that `Graph.update_edge` changes, its nodes are fixed."""

    metadata: Metadata
    userdata: E

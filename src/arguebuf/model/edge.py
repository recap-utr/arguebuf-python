from dataclasses import dataclass, field
from typing import overload

from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AbstractNode
from arguebuf.model.userdata import JSON_OBJECT, JsonObject, own
from arguebuf.model.utils import Entity, uuid

__all__ = ("Edge",)


# lazily evaluated, so the overloads below can specialize the class they belong to
type _Edge[T] = Edge[T]


@dataclass(slots=True, frozen=True, eq=False)
class Edge[E = JsonObject](Entity):
    """Directed connection from a source node to a target node.

    The userdata of the nodes is typed when they are accessed via the graph,
    e.g. `graph.nodes[edge.source.id]`.
    """

    source: AbstractNode
    target: AbstractNode
    metadata: Metadata = field(repr=False)
    userdata: E = field(repr=False)
    _id: str

    @overload
    def __init__(
        self: _Edge[JsonObject],
        source: AbstractNode,
        target: AbstractNode,
        *,
        metadata: Metadata | None = None,
        userdata: JsonObject = ...,
        id: str | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        source: AbstractNode,
        target: AbstractNode,
        *,
        metadata: Metadata | None = None,
        userdata: E,
        id: str | None = None,
    ) -> None: ...

    def __init__(
        self: _Edge[object],
        source: AbstractNode,
        target: AbstractNode,
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
        object.__setattr__(self, "_id", uuid() if id is None else id)

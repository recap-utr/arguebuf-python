"""Userdata of graph elements and the codecs that load and dump it.

Every kind of element has its own userdata type, a JSON object by default.
A `Codec` converts between the persisted JSON object and the in-memory value,
so the in-memory value may hold anything (e.g., numpy arrays),
while only the output of `Codec.dump_python` has to be JSON.
`pydantic.TypeAdapter` instances are codecs.

Parameters whose type depends on a type parameter (e.g., `userdata` or `codecs`)
default to the JSON variant.
basedpyright checks such defaults at every call against the solved type parameters,
so omitting them is only accepted for JSON userdata.
ty rejects these defaults where they are declared, so its rule `invalid-parameter-default` is disabled.
"""

import copy
from dataclasses import dataclass
from typing import Final, Literal, Protocol

__all__ = (
    "DEFAULT_CODECS",
    "JSON_CODEC",
    "Codec",
    "Codecs",
    "JsonCodec",
    "JsonObject",
    "JsonValue",
)

type JsonValue = (
    str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
)
type JsonObject = dict[str, JsonValue]

JSON_OBJECT: Final[JsonObject] = {}
"""Default of `userdata` parameters, never stored but copied by `own`."""


def own[T](userdata: T) -> T:
    """Copy the shared `JSON_OBJECT` default so that elements never share it."""
    return copy.copy(userdata) if userdata is JSON_OBJECT else userdata


class Codec[T](Protocol):
    """Conversion between persisted JSON objects and in-memory userdata of type `T`.

    The method names match `pydantic.TypeAdapter`, so its instances are codecs.
    """

    def validate_python(self, obj: JsonObject, /) -> T:
        """Load the in-memory userdata from its JSON object, validating it."""
        ...

    def dump_python(self, instance: T, /, *, mode: Literal["json"]) -> JsonObject:
        """Dump the userdata to the JSON object that is persisted."""
        ...


class JsonCodec:
    """Identity codec of JSON object userdata, it neither copies nor validates."""

    __slots__ = ()

    def validate_python(self, obj: JsonObject, /) -> JsonObject:
        return obj

    def dump_python(
        self, instance: JsonObject, /, *, mode: Literal["json"]
    ) -> JsonObject:
        return instance


JSON_CODEC: Final = JsonCodec()


@dataclass(slots=True, frozen=True)
class Codecs[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
]:
    """Codecs for the userdata of atom nodes, scheme nodes, edges, the graph,
    resources, participants, and analysts.

    Kinds without a codec keep JSON object userdata.

    Examples:
        >>> codecs = Codecs()
        >>> codecs.atom.validate_python({"a": 1})
        {'a': 1}
    """

    atom: Codec[A]
    scheme: Codec[S]
    edge: Codec[E]
    graph: Codec[G]
    resource: Codec[R]
    participant: Codec[P]
    analyst: Codec[N]

    def __init__(
        self,
        *,
        atom: Codec[A] = JSON_CODEC,
        scheme: Codec[S] = JSON_CODEC,
        edge: Codec[E] = JSON_CODEC,
        graph: Codec[G] = JSON_CODEC,
        resource: Codec[R] = JSON_CODEC,
        participant: Codec[P] = JSON_CODEC,
        analyst: Codec[N] = JSON_CODEC,
    ) -> None:
        # frozen dataclasses can only be initialized via object.__setattr__
        object.__setattr__(self, "atom", atom)
        object.__setattr__(self, "scheme", scheme)
        object.__setattr__(self, "edge", edge)
        object.__setattr__(self, "graph", graph)
        object.__setattr__(self, "resource", resource)
        object.__setattr__(self, "participant", participant)
        object.__setattr__(self, "analyst", analyst)


# shared default argument, safe since codecs are frozen
DEFAULT_CODECS: Final = Codecs()

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Self, TypedDict, overload, override

from arguebuf.model.metadata import Metadata
from arguebuf.model.reference import Reference
from arguebuf.model.scheme import (
    SCHEME_TYPE_LABELS,
    Attack,
    Preference,
    Rephrase,
    Scheme,
    Support,
    is_default_scheme,
)
from arguebuf.model.userdata import JSON_OBJECT, JsonObject, own
from arguebuf.model.utils import Entity, uuid

NO_SCHEME_LABEL = "Unknown"

__all__ = (
    "NO_SCHEME_LABEL",
    "SCHEME_COLORS",
    "AbstractNode",
    "AtomChanges",
    "AtomNode",
    "AtomOrSchemeNode",
    "Color",
    "SchemeChanges",
    "SchemeNode",
)


@dataclass(slots=True, frozen=True)
class Color:
    bg: str
    fg: str
    border: str

    @classmethod
    def filled(cls, bg: str) -> Self:
        return cls(bg=bg, fg="#ffffff", border=bg)


COLOR_MONOCHROME_LIGHT = Color(bg="#ffffff", fg="#000000", border="#000000")
COLOR_MONOCHROME_DARK = Color(bg="#000000", fg="#ffffff", border="#000000")
COLOR_SCHEME_FALLBACK = Color.filled("#9E9E9E")

SCHEME_COLORS: Final[Mapping[type[Scheme], Color]] = MappingProxyType(
    {
        Support: Color.filled("#4CAF50"),
        Attack: Color.filled("#F44336"),
        Rephrase: Color.filled("#009688"),
        Preference: Color.filled("#9C27B0"),
    }
)
"""Colors of scheme nodes by the type of their scheme, untyped ones are grey."""


@dataclass(slots=True, frozen=True, eq=False)
class AbstractNode(Entity, ABC):
    """Node of an argument graph, its subclasses add the userdata."""

    metadata: Metadata = field(repr=False)
    id: str

    def __init__(self, *, metadata: Metadata | None, id: str | None) -> None:
        # frozen dataclasses can only be initialized via object.__setattr__
        object.__setattr__(self, "metadata", metadata or Metadata())
        object.__setattr__(self, "id", uuid() if id is None else id)

    @property
    @abstractmethod
    def label(self) -> str:
        """Label used when rendering the node."""

    @abstractmethod
    def color(self, *, major_claim: bool = False, monochrome: bool = False) -> Color:
        """Color used when rendering the node."""


# lazily evaluated, so the overloads below can specialize the class they belong to
type _AtomNode[T] = AtomNode[T]


@dataclass(slots=True, frozen=True, eq=False)
class AtomNode[A = JsonObject](AbstractNode):
    """Node containing a claim or premise of an argument.

    The participant and the resource of the reference are stored by their id,
    they must be part of the graph before the node is added to it,
    e.g. `graph.participants[node.participant]`.
    """

    text: str
    reference: Reference | None
    participant: str | None
    userdata: A = field(repr=False)

    @overload
    def __init__(
        self: _AtomNode[JsonObject],
        text: str,
        *,
        reference: Reference | None = None,
        participant: str | None = None,
        metadata: Metadata | None = None,
        userdata: JsonObject = ...,
        id: str | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        text: str,
        *,
        reference: Reference | None = None,
        participant: str | None = None,
        metadata: Metadata | None = None,
        userdata: A,
        id: str | None = None,
    ) -> None: ...

    def __init__(
        self: _AtomNode[object],
        text: str,
        *,
        reference: Reference | None = None,
        participant: str | None = None,
        metadata: Metadata | None = None,
        userdata: object = JSON_OBJECT,
        id: str | None = None,
    ) -> None:
        AbstractNode.__init__(self, metadata=metadata, id=id)
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "reference", reference)
        object.__setattr__(self, "participant", participant)
        object.__setattr__(self, "userdata", own(userdata))

    @property
    @override
    def label(self) -> str:
        return self.text

    @override
    def color(self, *, major_claim: bool = False, monochrome: bool = False) -> Color:
        if monochrome:
            return COLOR_MONOCHROME_LIGHT

        return Color.filled("#0D47A1") if major_claim else Color.filled("#2196F3")


# lazily evaluated, so the overloads below can specialize the class they belong to
type _SchemeNode[T] = SchemeNode[T]


@dataclass(slots=True, frozen=True, eq=False)
class SchemeNode[S = JsonObject](AbstractNode):
    """Node describing the relation between atom nodes."""

    scheme: Scheme | None
    premise_descriptors: tuple[str, ...]
    userdata: S = field(repr=False)

    @overload
    def __init__(
        self: _SchemeNode[JsonObject],
        scheme: Scheme | None = None,
        *,
        premise_descriptors: Iterable[str] = (),
        metadata: Metadata | None = None,
        userdata: JsonObject = ...,
        id: str | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        scheme: Scheme | None = None,
        *,
        premise_descriptors: Iterable[str] = (),
        metadata: Metadata | None = None,
        userdata: S,
        id: str | None = None,
    ) -> None: ...

    def __init__(
        self: _SchemeNode[object],
        scheme: Scheme | None = None,
        *,
        premise_descriptors: Iterable[str] = (),
        metadata: Metadata | None = None,
        userdata: object = JSON_OBJECT,
        id: str | None = None,
    ) -> None:
        AbstractNode.__init__(self, metadata=metadata, id=id)
        object.__setattr__(self, "scheme", scheme)
        object.__setattr__(self, "premise_descriptors", tuple(premise_descriptors))
        object.__setattr__(self, "userdata", own(userdata))

    @property
    @override
    def label(self) -> str:
        if self.scheme is None:
            return NO_SCHEME_LABEL

        label = SCHEME_TYPE_LABELS[type(self.scheme)]

        if not is_default_scheme(self.scheme):
            label = f"{label}: {self.scheme.value}"

        return label

    @override
    def color(self, *, major_claim: bool = False, monochrome: bool = False) -> Color:
        if monochrome:
            return COLOR_MONOCHROME_DARK

        if self.scheme is None:
            return COLOR_SCHEME_FALLBACK

        return SCHEME_COLORS[type(self.scheme)]


type AtomOrSchemeNode[A = JsonObject, S = JsonObject] = AtomNode[A] | SchemeNode[S]


class AtomChanges[A](TypedDict, total=False):
    """Fields of an atom node that `GraphDraft.update_atom` changes."""

    text: str
    reference: Reference | None
    participant: str | None
    metadata: Metadata
    userdata: A


class SchemeChanges[S](TypedDict, total=False):
    """Fields of a scheme node that `GraphDraft.update_scheme` changes."""

    scheme: Scheme | None
    premise_descriptors: Iterable[str]
    metadata: Metadata
    userdata: S

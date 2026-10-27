from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Self, overload, override

from arguebuf.model.metadata import Metadata
from arguebuf.model.participant import AbstractParticipant
from arguebuf.model.reference import Reference
from arguebuf.model.scheme import (
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
    "AbstractNode",
    "AtomNode",
    "AtomOrSchemeNode",
    "Color",
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
COLOR_SCHEME_FALLBACK = Color.filled("#009688")

scheme2color: dict[type[Scheme], Color] = {
    Support: Color.filled("#4CAF50"),
    Attack: Color.filled("#F44336"),
    Rephrase: Color.filled("#009688"),
    Preference: Color.filled("#009688"),
}


@dataclass(slots=True, eq=False)
class AbstractNode(Entity, ABC):
    """Node of an argument graph, its subclasses add the userdata."""

    metadata: Metadata = field(repr=False)
    _id: str

    def __init__(self, *, metadata: Metadata | None, id: str | None) -> None:
        self.metadata = metadata or Metadata()
        self._id = uuid() if id is None else id

    @property
    @abstractmethod
    def label(self) -> str:
        """Label used when rendering the node."""

    @abstractmethod
    def color(self, major_claim: bool, monochrome: bool) -> Color:
        """Color used when rendering the node."""


# lazily evaluated, so the overloads below can specialize the class they belong to
type _AtomNode[T] = AtomNode[T]


@dataclass(slots=True, eq=False)
class AtomNode[A = JsonObject](AbstractNode):
    """Node containing a claim or premise of an argument.

    The participant and the resource of the reference must be registered
    in the graph before the node is added to it or they are assigned to it.
    Their userdata is typed when they are accessed via the graph,
    e.g. `graph.participants[node.participant.id]`.
    """

    text: str
    reference: Reference | None
    participant: AbstractParticipant | None
    userdata: A = field(repr=False)

    @overload
    def __init__(
        self: _AtomNode[JsonObject],
        text: str,
        *,
        reference: Reference | None = None,
        participant: AbstractParticipant | None = None,
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
        participant: AbstractParticipant | None = None,
        metadata: Metadata | None = None,
        userdata: A,
        id: str | None = None,
    ) -> None: ...

    def __init__(
        self: _AtomNode[object],
        text: str,
        *,
        reference: Reference | None = None,
        participant: AbstractParticipant | None = None,
        metadata: Metadata | None = None,
        userdata: object = JSON_OBJECT,
        id: str | None = None,
    ) -> None:
        AbstractNode.__init__(self, metadata=metadata, id=id)
        self.text = text
        self.reference = reference
        self.participant = participant
        self.userdata = own(userdata)

    @property
    @override
    def label(self) -> str:
        return self.text

    @override
    def color(self, major_claim: bool, monochrome: bool) -> Color:
        if monochrome:
            return COLOR_MONOCHROME_LIGHT

        return Color.filled("#0D47A1") if major_claim else Color.filled("#2196F3")


# lazily evaluated, so the overloads below can specialize the class they belong to
type _SchemeNode[T] = SchemeNode[T]


@dataclass(slots=True, eq=False)
class SchemeNode[S = JsonObject](AbstractNode):
    """Node describing the relation between atom nodes."""

    scheme: Scheme | None
    premise_descriptors: list[str]
    userdata: S = field(repr=False)

    @overload
    def __init__(
        self: _SchemeNode[JsonObject],
        scheme: Scheme | None = None,
        *,
        premise_descriptors: list[str] | None = None,
        metadata: Metadata | None = None,
        userdata: JsonObject = ...,
        id: str | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        scheme: Scheme | None = None,
        *,
        premise_descriptors: list[str] | None = None,
        metadata: Metadata | None = None,
        userdata: S,
        id: str | None = None,
    ) -> None: ...

    def __init__(
        self: _SchemeNode[object],
        scheme: Scheme | None = None,
        *,
        premise_descriptors: list[str] | None = None,
        metadata: Metadata | None = None,
        userdata: object = JSON_OBJECT,
        id: str | None = None,
    ) -> None:
        AbstractNode.__init__(self, metadata=metadata, id=id)
        self.scheme = scheme
        self.premise_descriptors = (
            [] if premise_descriptors is None else premise_descriptors
        )
        self.userdata = own(userdata)

    @property
    @override
    def label(self) -> str:
        if self.scheme is None:
            return NO_SCHEME_LABEL

        label = type(self.scheme).__name__

        if not is_default_scheme(self.scheme):
            label = f"{label}: {self.scheme.value}"

        return label

    @override
    def color(self, major_claim: bool, monochrome: bool) -> Color:
        if monochrome:
            return COLOR_MONOCHROME_DARK

        if self.scheme is None:
            return COLOR_SCHEME_FALLBACK

        return scheme2color[type(self.scheme)]


type AtomOrSchemeNode[A = JsonObject, S = JsonObject] = AtomNode[A] | SchemeNode[S]

from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, dataclass, field
from typing import Self

from arguebuf.model.metadata import Metadata
from arguebuf.model.participant import Participant
from arguebuf.model.reference import Reference
from arguebuf.model.scheme import Attack, Preference, Rephrase, Scheme, Support
from arguebuf.model.userdata import Userdata
from arguebuf.model.utils import Entity, uuid, xstr

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
    """Node of an argument graph."""

    _: KW_ONLY
    metadata: Metadata = field(default_factory=Metadata, repr=False)
    userdata: Userdata = field(default_factory=dict, repr=False)
    id: str = field(default_factory=uuid)

    @property
    @abstractmethod
    def label(self) -> str:
        """Label used when rendering the node."""

    @abstractmethod
    def color(self, major_claim: bool, monochrome: bool) -> Color:
        """Color used when rendering the node."""


@dataclass(slots=True, eq=False)
class AtomNode[T = str](AbstractNode):
    """Node containing a claim or premise of an argument."""

    text: T
    _: KW_ONLY
    reference: Reference[T] | None = None
    participant: Participant | None = None

    @property
    def plain_text(self) -> str:
        """Get the `text` as string."""
        return xstr(self.text)

    @property
    def label(self) -> str:
        return self.plain_text

    def color(self, major_claim: bool, monochrome: bool) -> Color:
        if monochrome:
            return COLOR_MONOCHROME_LIGHT

        return Color.filled("#0D47A1") if major_claim else Color.filled("#2196F3")


@dataclass(slots=True, eq=False)
class SchemeNode(AbstractNode):
    """Node describing the relation between atom nodes."""

    scheme: Scheme | None = None
    _: KW_ONLY
    premise_descriptors: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.scheme is None:
            return NO_SCHEME_LABEL

        label = type(self.scheme).__name__

        if self.scheme.value != "Default":
            label = f"{label}: {self.scheme.value}"

        return label

    def color(self, major_claim: bool, monochrome: bool) -> Color:
        if monochrome:
            return COLOR_MONOCHROME_DARK

        if self.scheme is None:
            return COLOR_SCHEME_FALLBACK

        return scheme2color[type(self.scheme)]


type AtomOrSchemeNode[T = str] = AtomNode[T] | SchemeNode

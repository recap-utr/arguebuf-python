from __future__ import absolute_import, annotations

import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pendulum

from arguebuf.model import utils
from arguebuf.model.metadata import Metadata
from arguebuf.model.participant import Participant
from arguebuf.model.reference import Reference
from arguebuf.model.scheme import Attack, Preference, Rephrase, Scheme, Support
from arguebuf.model.typing import TextType
from arguebuf.model.userdata import Userdata
from arguebuf.schemas import argdown

NO_SCHEME_LABEL = "Unknown"

__all__ = (
    "AbstractNode",
    "AtomNode",
    "SchemeNode",
    "AtomOrSchemeNode",
    "NO_SCHEME_LABEL",
)


@dataclass
class Color:
    bg: str
    fg: str
    border: str

    def __init__(
        self,
        bg: t.Optional[str] = None,
        fg: t.Optional[str] = None,
        border: t.Optional[str] = None,
    ) -> None:
        self.bg = bg or "#000000"
        self.fg = fg or "#ffffff"
        self.border = border or self.bg


COLOR_MONOCHROME = Color(bg="#ffffff", fg="#000000", border="#000000")


scheme2color: t.Dict[t.Type[Scheme], Color] = {
    Support: Color(bg="#4CAF50"),
    Attack: Color(bg="#F44336"),
    Rephrase: Color(bg="#009688"),
    Preference: Color(bg="#009688"),
}


class AbstractNode(ABC):
    """Node in the AIF format."""

    _id: str
    metadata: Metadata
    userdata: Userdata

    def __init__(
        self,
        metadata: t.Optional[Metadata] = None,
        userdata: t.Optional[Userdata] = None,
        id: t.Optional[str] = None,
    ):
        self._id = id or utils.uuid()
        self.metadata = metadata or Metadata()
        self.userdata = userdata or {}

        self.__post_init__()

    def __post_init__(self):
        pass

    def __eq__(self, other: AbstractNode) -> bool:
        if other is None:
            return False

        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return str(self.id)

    def __repr__(self):
        return utils.class_repr(self, [self.id])

    @property
    def id(self) -> str:
        return self._id

    @property
    @abstractmethod
    def label(self) -> str:
        """Generate a matching node label (e.g., for graphviz)"""

    @abstractmethod
    def color(self, major_claim: bool, monochrome: bool) -> Color:
        """Get the color used in OVA based on `category`."""


class AtomNode(AbstractNode, t.Generic[TextType]):
    __slots__ = (
        "_id",
        "metadata",
        "userdata",
        "text",
        "_reference",
        "_participant",
    )

    text: TextType
    _reference: t.Optional[Reference]
    _participant: t.Optional[Participant]

    def __init__(
        self,
        text: TextType,
        reference: t.Optional[Reference] = None,
        participant: t.Optional[Participant] = None,
        metadata: t.Optional[Metadata] = None,
        userdata: t.Optional[Userdata] = None,
        id: t.Optional[str] = None,
    ):
        super().__init__(metadata, userdata, id)
        self.text = text
        self._reference = reference
        self._participant = participant

    @property
    def plain_text(self) -> str:
        """Get the standard `text` as string."""

        return utils.xstr(self.text)

    @property
    def label(self) -> str:
        return self.plain_text

    @property
    def reference(self) -> t.Optional[Reference]:
        return self._reference

    @property
    def participant(self) -> t.Optional[Participant]:
        return self._participant

    def __repr__(self):
        return utils.class_repr(self, [self._id, self.plain_text])

    @classmethod
    def from_argdown_json(
        cls,
        obj: argdown.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> AtomNode:
        """Generate AtomNode object from Argdown JSON Node object."""
        timestamp = pendulum.now()
        return cls(
            id=obj["id"],
            text=utils.parse(obj["labelText"], nlp),
            metadata=Metadata(timestamp, timestamp),
        )

    def color(self, major_claim: bool, monochrome: bool) -> Color:
        """Get the color for rendering the node."""
        if monochrome:
            return COLOR_MONOCHROME

        return Color(bg="#0D47A1") if major_claim else Color(bg="#2196F3")


class SchemeNode(AbstractNode):
    __slots__ = (
        "_id",
        "created",
        "updated",
        "userdata",
        "scheme",
        "premise_descriptors",
    )

    scheme: t.Optional[Scheme]
    premise_descriptors: t.List[str]

    def __init__(
        self,
        scheme: t.Optional[Scheme] = None,
        premise_descriptors: t.Optional[t.List[str]] = None,
        metadata: t.Optional[Metadata] = None,
        userdata: t.Optional[Userdata] = None,
        id: t.Optional[str] = None,
    ):
        super().__init__(metadata, userdata, id)
        self.scheme = scheme
        self.premise_descriptors = premise_descriptors or []

    def __repr__(self):
        return utils.class_repr(
            self,
            [
                self._id,
                type(self.scheme).__name__ if self.scheme else NO_SCHEME_LABEL,
                self.scheme.value if self.scheme else "",
            ],
        )

    @property
    def label(self) -> str:
        label = NO_SCHEME_LABEL

        if self.scheme:
            label = type(self.scheme).__name__

            if self.scheme.value != "Default":
                label = f"{label}: {self.scheme.value}"

        return label

    def color(self, major_claim: bool, monochrome: bool) -> Color:
        """Get the color used in OVA based on `category`."""
        if monochrome:
            return COLOR_MONOCHROME

        return scheme2color[type(self.scheme)] if self.scheme else Color(bg="#009688")


AtomOrSchemeNode = t.Union[AtomNode, SchemeNode]

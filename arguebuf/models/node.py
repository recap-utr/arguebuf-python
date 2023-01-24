from __future__ import absolute_import, annotations

import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pendulum

from arguebuf.models.metadata import Metadata
from arguebuf.models.participant import Participant
from arguebuf.models.reference import Reference
from arguebuf.models.scheme import Attack, Preference, Rephrase, Scheme, Support
from arguebuf.models.typing import TextType
from arguebuf.models.userdata import Userdata
from arguebuf.schemas import argdown
from arguebuf.services import utils

NO_SCHEME_LABEL = "Unknown"


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

    def __repr__(self):
        return utils.class_repr(self, [self._id])

    @property
    def id(self) -> str:
        return self._id

    @property
    @abstractmethod
    def label(self) -> str:
        """Generate a matching node label (e.g., for graphviz)"""

    @abstractmethod
    def color(self, major_claim: bool) -> Color:
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

    def color(self, major_claim: bool) -> Color:
        """Get the color for rendering the node."""
        if major_claim:
            return Color(bg="#0D47A1")

        return Color(bg="#2196F3")


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

    def color(self, major_claim: bool) -> Color:
        """Get the color used in OVA based on `category`."""

        return scheme2color[type(self.scheme)] if self.scheme else Color(bg="#009688")


AtomOrSchemeNode = t.Union[AtomNode, SchemeNode]

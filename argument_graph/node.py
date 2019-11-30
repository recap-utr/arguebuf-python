from __future__ import absolute_import, annotations

import textwrap
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Set, Union
from enum import Enum

import networkx as nx
import pygraphviz as gv
from spacy.language import Language
from spacy.tokens import Doc, Span
import pendulum

from . import utils, dt
from .analysis import Analysis


class NodeCategory(Enum):
    """Enum for types of nodes.

    - CA: Conflict node.
    - I: Information node.
    - RA: Inference node.
    """

    CA = "CA"
    I = "I"
    RA = "RA"


# TODO: All OVA schemes need to be included.
schemes = {"Default Inference": 72, "Default Conflict": 71}


@dataclass
class Node:
    """Node in the AIF format.

    All elements that start with an underscore should not be accessed directly!
    The only exception is during init where you have to set _text.
    There are many property methods for convenience reasons.

    Required parameters for initialization are `id`, `text` and `type`.
    All other attributes have default values.
    One node per graph must have the attribute `major_claim = True`.

    Attributes `text` and `tokens` are updated accordingly when using the respective property method.
    If updating `_text` or `_tokens` directly, the other one refers to an old version.

    Attributes `text_begin` and `text_end` are a list for compatability with OVA, but there will always be exactly one start or end.
    """

    key: int = field(default_factory=utils.unique_id)
    text: Union[str, Doc, Span] = None
    category: NodeCategory = NodeCategory.I
    x: int = 0.0
    y: int = 0.0
    text_begin: int = 0
    text_end: int = 0
    comment: str = ""
    descriptors: dict = field(default_factory=dict)
    cqdesc: dict = field(default_factory=dict)
    visible: bool = True
    imgurl: str = ""
    annotator: str = ""
    date: pendulum.DateTime = field(default_factory=pendulum.now)
    participant_id: int = 0
    w: int = 0
    h: int = 0
    major_claim: bool = False

    @property
    def scheme(self) -> int:
        return schemes.get(self.text, 0)

    @property
    def text_length(self) -> int:
        return len(utils.xstr(self.text))

    @property
    def ova_color(self) -> str:
        if self.category == NodeCategory.RA:
            return "g"
        elif self.category == NodeCategory.CA:
            return "r"
        elif self.major_claim:
            return "m"
        return "b"

    @property
    def gv_color(self) -> str:
        if self.category == NodeCategory.RA:
            return "palegreen"
        elif self.category == NodeCategory.CA:
            return "tomato"
        elif self.major_claim:
            return "lightskyblue"
        return "aliceblue"

    @staticmethod
    def from_ova(obj: Any, nlp: Optional[Language] = None) -> Node:
        return Node(
            key=int(obj.get("id")),
            text=utils.parse(obj.get("text"), nlp),
            category=NodeCategory(obj.get("type")),
            x=obj.get("x"),
            y=obj.get("y"),
            text_begin=next(iter(obj.get("text_begin")), 0),
            text_end=next(iter(obj.get("text_end")), 0),
            comment=obj.get("comment"),
            descriptors=obj.get("descriptors"),
            cqdesc=obj.get("cqdesc"),
            visible=obj.get("visible"),
            imgurl=obj.get("imgurl"),
            annotator=obj.get("annotator"),
            date=dt.from_ova(obj.get("date")),
            participant_id=int(obj.get("participantID")),
            w=obj.get("w"),
            h=obj.get("h"),
            major_claim=obj.get("majorClaim"),
        )

    def to_ova(self) -> dict:
        return {
            "id": self.key,
            "x": self.x,
            "y": self.y,
            "text": self.text or "",
            "text_begin": [self.text_begin],
            "text_end": [self.text_end],
            "text_length": self.text_length,
            "comment": self.comment,
            "type": self.type.value,
            "descriptors": self.descriptors,
            "cqdesc": self.cqdesc,
            "visible": self.visible,
            "imgurl": self.imgurl,
            "annotator": self.annotator,
            "date": dt.to_ova(self.date),
            "participantID": str(self.participant_id),
            "w": self.w,
            "h": self.h,
            "majorClaim": self.major_claim,
            "color": self.ova_color,
        }

    @staticmethod
    def from_aif(obj: Any, nlp: Optional[Language] = None) -> Node:
        return Node(
            key=int(obj.get("nodeID")),
            text=utils.parse(obj.get("text"), nlp),
            category=NodeCategory(obj.get("type")),
            date=dt.from_aif(obj.get("timestamp")),
        )

    def to_aif(self) -> dict:
        return {
            "nodeID": self.key,
            "text": self.text or "",
            "type": self.type.value,
            "timestamp": dt.to_aif(self.date),
        }

    def to_nx(self, g: nx.DiGraph) -> None:
        g.add_node(
            self.key, label=self.text, type=self.category.value, mc=self.major_claim
        )

    def to_gv(
        self,
        g: gv.AGraph,
        bg_color: str = "",
        fg_color: str = "",
        label_prefix: str = "",
        label_suffix: str = "",
        key_prefix: str = "",
        key_suffix: str = "",
    ) -> None:
        g.add_node(
            f"{key_prefix}{self.key}{key_suffix}",
            label=f"{label_prefix}\n{textwrap.fill(self.text, 20)}\n{label_suffix}",
            fontcolor=fg_color or "black",
            fillcolor=bg_color or self.gv_color,
            style="filled",
            root=self.major_claim,
            shape="box",
        )

    def __eq__(self, other: Node) -> bool:
        return self.key == other.key

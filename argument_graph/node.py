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

    - I: Information
    - RA: Inference
    - CA: Conflict
    - MA: Rephrase
    - TA: Transition
    """

    I = "I"
    RA = "RA"
    CA = "CA"
    MA = "MA"
    TA = "TA"
    PA = "PA"


# TODO: Duplicate keys: 17, 251, 252, 61, 254, 253
ra_schemes = {
    "Alternatives (Cognitive Schemes)": 251,
    "Alternatives": 235,
    "Analogy": 1,
    "Arbitrary Verbal Classification": 59,
    "Argument From Authority": 160,
    "Argument From Goodwill": 184,
    "Argument From Moral Virtue": 182,
    "Argument From Practical Wisdom": 183,
    "Argument From Virtue/Goodwill": 402,
    "Argument From Wisdom/Goodwill": 401,
    "Argument From Wisdom/Virtue": 400,
    "Argument From Wisdom/Virtue/Goodwill": 403,
    "Bias": 2,
    "Causal Slippery Slope": 3,
    "Cause To Effect": 4,
    "Circumstantial Ad Hominem": 5,
    "Commitment": 6,
    "Composition": 236,
    "Consequences": 237,
    "Correlation To Cause": 7,
    "Danger Appeal": 17,  # ova.uni-trier.de
    # "Danger Appeal": 238, # ova.arg-tech.org
    "Default Inference": 72,
    "Definition To Verbal Classification": 239,
    "Dilemma": 9,
    "Direct Ad Hominem": 10,
    "Division": 240,
    "Established Rule": 61,
    "Ethotic": 12,
    "Evidence To Hypothesis": 13,
    "Example": 14,
    "Exceptional Case": 62,
    "Expert Opinion": 15,
    "Fairness": 254,
    "Falsification Of Hypothesis": 16,
    "Fear Appeal": 17,
    "Full Slippery Slope": 18,
    "Generic Ad Hominem": 250,
    # "Gradualism": 241, # ova.arg-tech.org
    "Gradualism": 63,  # ova.arg-tech.org
    "Ignorance": 19,
    "Inconsistent Commitment": 20,
    "Informant Report": 170,
    "Interaction Of Act And Person": 249,
    "Misplaced Priorities": 252,
    "Modus Ponens": 35,
    "Need For Help": 242,
    "Negative Consequences": 22,
    "Oppositions": 243,
    "Paraphrase": 102,
    "Perception": 244,
    "Popular Opinion": 24,
    "Popular Practice": 25,
    "Position To Know": 26,
    "Positive Consequences": 27,
    "Practical Reasoning From Analogy": 251,
    "Practical Reasoning": 28,
    "Pragmatic Argument From Alternatives": 252,
    "Pragmatic Inconsistency": 253,
    "Precedent Slippery Slope": 29,
    "Reframing": 121,
    "Rule": 61,
    "Rules": 245,
    "Sign": 30,
    "Two Person Practical Reasoning": 254,
    "Unfairness": 253,
    "Vague Verbal Classification": 60,
    "Vagueness Of Verbal Classification": 246,
    "Value Based Practical Reasoning": 81,
    "Values": 247,
    "Verbal Classification": 31,
    "Verbal Slippery Slope": 32,
    "Waste": 33,
    "Witness Testimony": 248,
}

ca_schemes = {
    "Ad hominem": 172,
    "Alternative Means": 34,
    "Biased Classification": 37,
    "Calling Out": 146,
    "Commitment Exception": 38,
    "Conflict From Goodwill": 181,
    "Conflict From Moral Virtue": 179,
    "Conflict From Practical Wisdom": 180,
    "Conflict From Virtue/Goodwill": 406,
    "Conflict From Wisdom/Goodwill": 405,
    "Conflict From Wisdom/Virtue": 404,
    "Conflict From Wisdom/Virtue/Goodwill": 407,
    "Conflicting Goals": 39,
    "Default Conflict": 71,
    "Differences Undermine Similarity": 40,
    "ERAd Hominem": 164,
    "Exception Similarity Case": 41,
    "Expertise Inconsistency": 42,
    "General Acceptance Doubt": 43,
    "Irrational Fear Appeal": 44,
    "Lack Of Complete Knowledge": 45,
    "Lack Of Expert Reliability": 46,
    "Logical": 36,
    "Opposed Commitment": 48,
    "Other Causal Factors Involved": 52,
    # "Other Causal Factors Involved": 53,
    "Property Not Existant": 54,
    "Required Steps": 55,
    "Resolving Inconsistency": 56,
    "Sign From Other Events": 57,
    "Vested Interest": 171,
    "Weakest Link": 58,
}

other_schemes = {
    "Default Rephrase": 144,
    "Default Transition": 82,
    "Default Preference": 161,
}

schemes = {**ra_schemes ** ca_schemes, **other_schemes}


def _int2list(value: Optional[int]) -> List[int]:
    return [value] if value else []


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
    text: Union[str, Doc, Span] = ""
    category: NodeCategory = NodeCategory.I
    x: Optional[int] = None
    y: Optional[int] = None
    text_begin: Optional[int] = None
    text_end: Optional[int] = None
    comment: Optional[str] = None
    descriptors: Optional[Dict[str, Any]] = None
    cqdesc: Optional[Dict[str, Any]] = None
    visible: Optional[bool] = None
    imgurl: Optional[str] = None
    annotator: Optional[str] = None
    date: pendulum.DateTime = field(default_factory=pendulum.now)
    participant_id: Optional[int] = None
    w: Optional[int] = None
    h: Optional[int] = None
    major_claim: Optional[bool] = None
    is_check_worthy: Optional[str] = None
    source: Optional[str] = None

    @property
    def scheme(self) -> int:
        return schemes.get(self.text, 0)

    @property
    def text_length(self) -> Optional[int]:
        if self.category == NodeCategory.I:
            return len(utils.xstr(self.text))
        return None

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
    def from_ova(obj: Dict[str, Any], nlp: Optional[Language] = None) -> Node:
        return Node(
            key=obj["id"],
            text=utils.parse(obj["text"], nlp),
            category=NodeCategory(obj["type"]),
            x=obj.get("x"),
            y=obj.get("y"),
            text_begin=next(iter(obj.get("text_begin")), None),
            text_end=next(iter(obj.get("text_end")), None),
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
            is_check_worthy=obj.get("is_check_worthy"),
            source=obj.get("source"),
        )

    # TODO: Check fallback value for date.
    def to_ova(self) -> dict:
        return {
            "id": self.key,
            "text": self.text,
            "type": self.category.value,
            "x": self.x or 0,
            "y": self.y or 0,
            "text_begin": _int2list(self.text_begin),
            "text_end": _int2list(self.text_end),
            "text_length": _int2list(self.text_length),
            "comment": self.comment or "",
            "scheme": str(self.scheme) or "0",
            "descriptors": self.descriptors or {},
            "cqdesc": self.cqdesc or {},
            "visible": self.visible or True,
            "imgurl": self.imgurl or "",
            "annotator": self.annotator or "",
            "date": dt.to_ova(self.date),
            "participantID": str(self.participant_id) or "0",
            "w": self.w or 0,
            "h": self.h or 0,
            "majorClaim": self.major_claim or False,
            "color": self.ova_color,
            "is_check_worthy": self.is_check_worthy or "no",
            "source": self.source or "",
        }

    @staticmethod
    def from_aif(obj: Any, nlp: Optional[Language] = None) -> Node:
        return Node(
            key=int(obj["nodeID"]),
            text=utils.parse(obj["text"], nlp),
            category=NodeCategory(obj["type"]),
            date=dt.from_aif(obj.get("timestamp")),
        )

    def to_aif(self) -> dict:
        return {
            "nodeID": str(self.key),
            "text": self.text,
            "type": self.category.value,
            "timestamp": dt.to_aif(self.date),
        }

    def to_nx(self, g: nx.DiGraph) -> None:
        g.add_node(
            self.key,
            label=self.text,
            type=self.category.value,
            mc=bool(self.major_claim),
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
            label=f"{label_prefix}\n{textwrap.fill(self.text, 20)}\n{label_suffix}".strip(),
            fontcolor=fg_color or "black",
            fillcolor=bg_color or self.gv_color,
            style="filled",
            root=bool(self.major_claim),
            shape="box",
        )

    def __eq__(self, other: Node) -> bool:
        return self.key == other.key

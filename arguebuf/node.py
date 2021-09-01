from __future__ import absolute_import, annotations

import textwrap
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import graphviz as gv
import networkx as nx
import pendulum
from arg_services.graph.v1 import graph_pb2

from arguebuf import dt, utils
from arguebuf.data import Metadata, Participant, Reference, Resource


class SchemeType(Enum):
    SUPPORT = graph_pb2.SCHEME_TYPE_SUPPORT
    ATTACK = graph_pb2.SCHEME_TYPE_ATTACK
    REPHRASE = graph_pb2.SCHEME_TYPE_REPHRASE
    TRANSITION = graph_pb2.SCHEME_TYPE_TRANSITION
    PREFERENCE = graph_pb2.SCHEME_TYPE_PREFERENCE
    ASSERTION = graph_pb2.SCHEME_TYPE_ASSERTION


scheme_type2aif = {
    SchemeType.SUPPORT: "RA",
    SchemeType.ATTACK: "CA",
    SchemeType.REPHRASE: "MA",
    SchemeType.TRANSITION: "TA",
    SchemeType.PREFERENCE: "PA",
    SchemeType.ASSERTION: "YA",
}

aif2scheme_type = {value: key for key, value in scheme_type2aif.items()}

scheme_type2text = {
    SchemeType.SUPPORT: "Support",
    SchemeType.ATTACK: "Attack",
    SchemeType.REPHRASE: "Rephrase",
    SchemeType.TRANSITION: "Transition",
    SchemeType.PREFERENCE: "Preference",
    SchemeType.ASSERTION: "Assertion",
}


class Scheme(Enum):
    AD_HOMINEM = graph_pb2.SCHEME_AD_HOMINEM
    ALTERNATIVE_MEANS = graph_pb2.SCHEME_ALTERNATIVE_MEANS
    ALTERNATIVES = graph_pb2.SCHEME_ALTERNATIVES
    ANALOGY = graph_pb2.SCHEME_ANALOGY
    ARBITRARY_VERBAL_CLASSIFICATION = graph_pb2.SCHEME_ARBITRARY_VERBAL_CLASSIFICATION
    AUTHORITY = graph_pb2.SCHEME_AUTHORITY
    BIAS = graph_pb2.SCHEME_BIAS
    BIASED_CLASSIFICATION = graph_pb2.SCHEME_BIASED_CLASSIFICATION
    CALLING_OUT = graph_pb2.SCHEME_CALLING_OUT
    CAUSAL_SLIPPERY_SLOPE = graph_pb2.SCHEME_CAUSAL_SLIPPERY_SLOPE
    CAUSE_TO_EFFECT = graph_pb2.SCHEME_CAUSE_TO_EFFECT
    CIRCUMSTANTIAL_AD_HOMINEM = graph_pb2.SCHEME_CIRCUMSTANTIAL_AD_HOMINEM
    COMMITMENT_EXCEPTION = graph_pb2.SCHEME_COMMITMENT_EXCEPTION
    COMMITMENT = graph_pb2.SCHEME_COMMITMENT
    COMPOSITION = graph_pb2.SCHEME_COMPOSITION
    CONFLICTING_GOALS = graph_pb2.SCHEME_CONFLICTING_GOALS
    CONSEQUENCES = graph_pb2.SCHEME_CONSEQUENCES
    CORRELATION_TO_CAUSE = graph_pb2.SCHEME_CORRELATION_TO_CAUSE
    DANGER_APPEAL = graph_pb2.SCHEME_DANGER_APPEAL
    DEFINITION_TO_VERBAL_CLASSIFICATION = (
        graph_pb2.SCHEME_DEFINITION_TO_VERBAL_CLASSIFICATION
    )
    DIFFERENCES_UNDERMINE_SIMILARITY = graph_pb2.SCHEME_DIFFERENCES_UNDERMINE_SIMILARITY
    DILEMMA = graph_pb2.SCHEME_DILEMMA
    DIRECT_AD_HOMINEM = graph_pb2.SCHEME_DIRECT_AD_HOMINEM
    DIVISION = graph_pb2.SCHEME_DIVISION
    ESTABLISHED_RULE = graph_pb2.SCHEME_ESTABLISHED_RULE
    ETHOTIC = graph_pb2.SCHEME_ETHOTIC
    EVIDENCE_TO_HYPOTHESIS = graph_pb2.SCHEME_EVIDENCE_TO_HYPOTHESIS
    EXAMPLE = graph_pb2.SCHEME_EXAMPLE
    EXCEPTION_SIMILARITY_CASE = graph_pb2.SCHEME_EXCEPTION_SIMILARITY_CASE
    EXCEPTIONAL_CASE = graph_pb2.SCHEME_EXCEPTIONAL_CASE
    EXPERT_OPINION = graph_pb2.SCHEME_EXPERT_OPINION
    EXPERTISE_INCONSISTENCY = graph_pb2.SCHEME_EXPERTISE_INCONSISTENCY
    FAIRNESS = graph_pb2.SCHEME_FAIRNESS
    FALSIFICATION_OF_HYPOTHESIS = graph_pb2.SCHEME_FALSIFICATION_OF_HYPOTHESIS
    FEAR_APPEAL = graph_pb2.SCHEME_FEAR_APPEAL
    FULL_SLIPPERY_SLOPE = graph_pb2.SCHEME_FULL_SLIPPERY_SLOPE
    GENERAL_ACCEPTANCE_DOUBT = graph_pb2.SCHEME_GENERAL_ACCEPTANCE_DOUBT
    GENERIC_AD_HOMINEM = graph_pb2.SCHEME_GENERIC_AD_HOMINEM
    GOODWILL = graph_pb2.SCHEME_GOODWILL
    GRADUALISM = graph_pb2.SCHEME_GRADUALISM
    IGNORANCE = graph_pb2.SCHEME_IGNORANCE
    INCONSISTENT_COMMITMENT = graph_pb2.SCHEME_INCONSISTENT_COMMITMENT
    INFORMANT_REPORT = graph_pb2.SCHEME_INFORMANT_REPORT
    INTERACTION_OF_ACT_AND_PERSON = graph_pb2.SCHEME_INTERACTION_OF_ACT_AND_PERSON
    IRRATIONAL_FEAR_APPEAL = graph_pb2.SCHEME_IRRATIONAL_FEAR_APPEAL
    LACK_OF_COMPLETE_KNOWLEDGE = graph_pb2.SCHEME_LACK_OF_COMPLETE_KNOWLEDGE
    LACK_OF_EXPERT_RELIABILITY = graph_pb2.SCHEME_LACK_OF_EXPERT_RELIABILITY
    LOGICAL = graph_pb2.SCHEME_LOGICAL
    MISPLACED_PRIORITIES = graph_pb2.SCHEME_MISPLACED_PRIORITIES
    MODUS_PONENS = graph_pb2.SCHEME_MODUS_PONENS
    MORAL_VIRTUE = graph_pb2.SCHEME_MORAL_VIRTUE
    NEED_FOR_HELP = graph_pb2.SCHEME_NEED_FOR_HELP
    NEGATIVE_CONSEQUENCES = graph_pb2.SCHEME_NEGATIVE_CONSEQUENCES
    OPPOSED_COMMITMENT = graph_pb2.SCHEME_OPPOSED_COMMITMENT
    OPPOSITIONS = graph_pb2.SCHEME_OPPOSITIONS
    CAUSAL_FACTORS_INVOLVED = graph_pb2.SCHEME_CAUSAL_FACTORS_INVOLVED
    PARAPHRASE = graph_pb2.SCHEME_PARAPHRASE
    PERCEPTION = graph_pb2.SCHEME_PERCEPTION
    POPULAR_OPINION = graph_pb2.SCHEME_POPULAR_OPINION
    POPULAR_PRACTICE = graph_pb2.SCHEME_POPULAR_PRACTICE
    POSITION_TO_KNOW = graph_pb2.SCHEME_POSITION_TO_KNOW
    POSITIVE_CONSEQUENCES = graph_pb2.SCHEME_POSITIVE_CONSEQUENCES
    PRACTICAL_REASONING_FROM_ANALOGY = graph_pb2.SCHEME_PRACTICAL_REASONING_FROM_ANALOGY
    PRACTICAL_REASONING = graph_pb2.SCHEME_PRACTICAL_REASONING
    PRACTICAL_WISDOM = graph_pb2.SCHEME_PRACTICAL_WISDOM
    PRAGMATIC_ALTERNATIVES = graph_pb2.SCHEME_PRAGMATIC_ALTERNATIVES
    PRAGMATIC_INCONSISTENCY = graph_pb2.SCHEME_PRAGMATIC_INCONSISTENCY
    PRECEDENT_SLIPPERY_SLOPE = graph_pb2.SCHEME_PRECEDENT_SLIPPERY_SLOPE
    PROPERTY_NOT_EXISTANT = graph_pb2.SCHEME_PROPERTY_NOT_EXISTANT
    REFRAMING = graph_pb2.SCHEME_REFRAMING
    REQUIRED_STEPS = graph_pb2.SCHEME_REQUIRED_STEPS
    RESOLVING_INCONSISTENCY = graph_pb2.SCHEME_RESOLVING_INCONSISTENCY
    RULE = graph_pb2.SCHEME_RULE
    RULES = graph_pb2.SCHEME_RULES
    SIGN_FROM_OTHER_EVENTS = graph_pb2.SCHEME_SIGN_FROM_OTHER_EVENTS
    SIGN = graph_pb2.SCHEME_SIGN
    TWO_PERSON_PRACTICAL_REASONING = graph_pb2.SCHEME_TWO_PERSON_PRACTICAL_REASONING
    UNFAIRNESS = graph_pb2.SCHEME_UNFAIRNESS
    VAGUE_VERBAL_CLASSIFICATION = graph_pb2.SCHEME_VAGUE_VERBAL_CLASSIFICATION
    VAGUENESS_OF_VERBAL_CLASSIFICATION = (
        graph_pb2.SCHEME_VAGUENESS_OF_VERBAL_CLASSIFICATION
    )
    VALUE_BASED_PRACTICAL_REASONING = graph_pb2.SCHEME_VALUE_BASED_PRACTICAL_REASONING
    VALUES = graph_pb2.SCHEME_VALUES
    VERBAL_CLASSIFICATION = graph_pb2.SCHEME_VERBAL_CLASSIFICATION
    VERBAL_SLIPPERY_SLOPE = graph_pb2.SCHEME_VERBAL_SLIPPERY_SLOPE
    VESTED_INTEREST = graph_pb2.SCHEME_VESTED_INTEREST
    VIRTUE_GOODWILL = graph_pb2.SCHEME_VIRTUE_GOODWILL
    WASTE = graph_pb2.SCHEME_WASTE
    WEAKEST_LINK = graph_pb2.SCHEME_WEAKEST_LINK
    WISDOM_GOODWILL = graph_pb2.SCHEME_WISDOM_GOODWILL
    WISDOM_VIRTUE = graph_pb2.SCHEME_WISDOM_VIRTUE
    WISDOM_VIRTUE_GOODWILL = graph_pb2.SCHEME_WISDOM_VIRTUE_GOODWILL
    WITNESS_TESTIMONY = graph_pb2.SCHEME_WITNESS_TESTIMONY


# TODO
scheme2text = {}

# TODO
text2scheme = {}


@dataclass
class ColorMapping:
    bg: str = "#ffffff"
    fg: str = "#000000"
    border: str = "#000000"


class Node(ABC):
    """Node in the AIF format."""

    _id: str
    created: pendulum.DateTime
    updated: pendulum.DateTime
    metadata: Metadata

    def __init__(
        self,
        id: str,
        created: t.Optional[pendulum.DateTime] = None,
        updated: t.Optional[pendulum.DateTime] = None,
        metadata: t.Optional[Metadata] = None,
    ):
        self._id = id
        self.created = created or pendulum.now()
        self.updated = updated or pendulum.now()
        self.metadata = metadata or {}

        self.__post_init__()

    def __post_init__(self):
        pass

    def __repr__(self):
        return utils.class_repr(self, [self._id])

    @property
    def id(self) -> str:
        return self._id

    @abstractmethod
    def color(self, major_claim: bool) -> ColorMapping:
        """Get the color used in OVA based on `category`."""

    @classmethod
    @abstractmethod
    def from_ova(
        cls,
        obj: t.Mapping[str, t.Any],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        pass

    @classmethod
    @abstractmethod
    def from_aif(
        cls,
        obj: t.Mapping[str, t.Any],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        pass

    @abstractmethod
    def to_aif(self) -> t.Dict[str, t.Any]:
        pass

    @classmethod
    @abstractmethod
    def from_protobuf(
        cls,
        id: str,
        obj: graph_pb2.Node,
        resources: t.Mapping[str, Resource],
        participants: t.Mapping[str, Participant],
        reference_class: t.Type[Reference],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        pass

    @abstractmethod
    def to_protobuf(self) -> graph_pb2.Node:
        pass

    @abstractmethod
    def to_nx(self, g: nx.DiGraph) -> None:
        pass

    @abstractmethod
    def to_gv(self, g: gv.Digraph, major_claim: bool, wrap_col: int) -> None:
        pass

    # @abstractmethod
    # def to_gv(
    #     self,
    #     g: gv.Digraph,
    #     major_claim: bool,
    #     labels: t.Optional[t.Iterable[str]] = None,
    #     color: t.Optional[ColorMapping] = None,
    #     label_prefix: str = "",
    #     label_suffix: str = "",
    #     key_prefix: str = "",
    #     key_suffix: str = "",
    #     wrap_col: t.Optional[int] = None,
    #     margin: t.Optional[t.Tuple[float, float]] = None,
    #     font_name: t.Optional[str] = None,
    #     font_size: t.Optional[float] = None,
    # ) -> None:
    #     if not color:
    #         color = self.color(major_claim)

    #     if not labels:
    #         labels = ["plain_text"]

    #     if not wrap_col:
    #         wrap_col = 36

    #     if not margin:
    #         margin = (0.15, 0.1)

    #     if not font_name:
    #         font_name = "Arial"

    #     if not font_size:
    #         font_size = 11

    #     label = "\n".join(str(getattr(self, attr)) for attr in labels)

    #     # https://stackoverflow.com/a/26538082/7626878
    #     label_wrapped = textwrap.fill(label, wrap_col)

    #     g.node(
    #         f"{key_prefix}{self._id}{key_suffix}",
    #         label=f"{label_prefix}\n{label_wrapped}\n{label_suffix}".strip(),
    #         fontname=font_name,
    #         fontsize=str(font_size),
    #         fontcolor=color.fg,
    #         fillcolor=color.bg,
    #         color=color.border,
    #         style="filled",
    #         root=str(bool(major_claim)),
    #         shape="box",
    #         width="0",
    #         height="0",
    #         margin=f"{margin[0]},{margin[1]}",
    #     )


class AtomNode(Node):
    __slots__ = (
        "_id",
        "created",
        "updated",
        "metadata",
        "text",
        "reference",
        "participant",
    )

    text: t.Any
    reference: t.Optional[Reference]
    participant: t.Optional[Participant]

    def __init__(
        self,
        id: str,
        text: t.Any,
        resource: t.Optional[Reference] = None,
        participant: t.Optional[Participant] = None,
        created: t.Optional[pendulum.DateTime] = None,
        updated: t.Optional[pendulum.DateTime] = None,
        metadata: t.Optional[Metadata] = None,
    ):
        super().__init__(id, created, updated, metadata)
        self.text = text
        self.reference = resource
        self.participant = participant

    @property
    def plain_text(self) -> str:
        """Get the standard `text` as string."""

        return utils.xstr(self.text)

    def __repr__(self):
        return utils.class_repr(self, [self._id, self.plain_text])

    @classmethod
    def from_aif(
        cls,
        obj: t.Mapping[str, t.Any],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        return cls(
            **_from_aif(obj),
            text=utils.parse(obj["text"], nlp),
        )

    def to_aif(self) -> t.Dict[str, t.Any]:
        return {
            **_to_aif(self),
            "text": self.plain_text,
            "type": "I",
        }

    @classmethod
    def from_ova(
        cls,
        obj: t.Mapping[str, t.Any],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        return cls(**_from_ova(obj), text=utils.parse(obj["text"], nlp))

    @classmethod
    def from_protobuf(
        cls,
        id: str,
        obj: graph_pb2.Node,
        resources: t.Mapping[str, Resource],
        participants: t.Mapping[str, Participant],
        reference_class: t.Type[Reference],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> AtomNode:
        return cls(
            id,
            utils.parse(obj.atom.text, nlp),
            reference_class.from_protobuf(obj.atom.reference, resources, nlp),
            participants[obj.atom.participant],
            dt.from_protobuf(obj.created),
            dt.from_protobuf(obj.updated),
            dict(obj.metadata.items()),
        )

    def to_protobuf(self) -> graph_pb2.Node:
        obj = graph_pb2.Node()
        obj.metadata.update(self.metadata)

        obj.atom.text = self.plain_text

        if reference := self.reference:
            obj.atom.reference.CopyFrom(reference.to_protobuf())

        if participant := self.participant:
            obj.atom.participant = participant.id

        if created := self.created:
            obj.created.FromDatetime(created)

        if updated := self.updated:
            obj.updated.FromDatetime(updated)

        return obj

    def to_nx(self, g: nx.DiGraph) -> None:
        g.add_node(
            self._id,
            label=self.plain_text,
        )

    def color(self, major_claim: bool) -> ColorMapping:
        if major_claim:
            return ColorMapping(bg="#3498db", border="#3498db")

        return ColorMapping(bg="#ddeef9", border="#3498db")

    def to_gv(self, g: gv.Digraph, major_claim: bool, wrap_col: int) -> None:
        color = self.color(major_claim)

        # TODO: Improve wrapping
        # https://stackoverflow.com/a/26538082/7626878
        g.node(
            self._id,
            label=textwrap.fill(self.plain_text, wrap_col).strip(),
            fontcolor=color.fg,
            fillcolor=color.bg,
            color=color.border,
            root=str(bool(major_claim)),
        )


class SchemeNode(Node):
    __slots__ = (
        "_id",
        "created",
        "updated",
        "metadata",
        "type",
        "argumentation_scheme",
        "descriptors",
    )

    type: SchemeType
    argumentation_scheme: t.Optional[Scheme]
    descriptors: t.Dict[str, str]

    def __init__(
        self,
        id: str,
        type: SchemeType,
        argumentation_scheme: t.Optional[Scheme] = None,
        descriptors: t.Optional[t.Mapping[str, str]] = None,
        created: t.Optional[pendulum.DateTime] = None,
        updated: t.Optional[pendulum.DateTime] = None,
        metadata: t.Optional[Metadata] = None,
    ):
        super().__init__(id, created, updated, metadata)
        self.type = type
        self.argumentation_scheme = argumentation_scheme
        self.descriptors = dict(descriptors) if descriptors else {}

    def __repr__(self):
        return utils.class_repr(
            self,
            [
                self._id,
                scheme_type2text[self.type],
                utils.xstr(scheme2text.get(self.argumentation_scheme)),
            ],
        )

    @classmethod
    def from_aif(
        cls,
        obj: t.Mapping[str, t.Any],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        node = cls(
            **_from_aif(obj),
            type=aif2scheme_type[obj["type"]],
        )
        text: str = obj["text"]

        if not text.startswith("Default "):
            node.argumentation_scheme = text2scheme[text]

        return node

    def to_aif(self) -> t.Dict[str, t.Any]:
        return {
            **_to_aif(self),
            "text": scheme_type2text[self.type],
            "type": scheme_type2aif[self.type],
        }

    @classmethod
    def from_ova(
        cls,
        obj: t.Mapping[str, t.Any],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        ova_desc = obj["descriptors"]
        descriptors = {}

        ova_key: str
        ova_value: int
        for ova_key, ova_value in ova_desc.items():
            value = utils.xstr(ova_value)
            key = ova_key.lstrip("s_").split("։")[0]

            descriptors[key] = value

        return cls(
            **_from_ova(obj),
            argumentation_scheme=text2scheme.get(obj["text"]),
            type=aif2scheme_type[obj["type"]],
            descriptors=descriptors,
        )

    @classmethod
    def from_protobuf(
        cls,
        id: str,
        obj: graph_pb2.Node,
        resources: t.Mapping[str, Resource],
        participants: t.Mapping[str, Participant],
        reference_class: t.Type[Reference],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> SchemeNode:
        return cls(
            id,
            SchemeType(obj.scheme.type)
            if obj.scheme.type != graph_pb2.SCHEME_TYPE_UNSPECIFIED
            else SchemeType.SUPPORT,
            Scheme(obj.scheme.argumentation_scheme),
            dict(obj.scheme.descriptors.items()),
            dt.from_protobuf(obj.created),
            dt.from_protobuf(obj.updated),
            dict(obj.metadata.items()),
        )

    def to_protobuf(self) -> graph_pb2.Node:
        obj = graph_pb2.Node()
        obj.metadata.update(self.metadata)

        obj.scheme.type = self.type.value
        obj.scheme.descriptors.update(self.descriptors)

        if arg_scheme := self.argumentation_scheme:
            obj.scheme.argumentation_scheme = arg_scheme.value

        if created := self.created:
            obj.created.FromDatetime(created)

        if updated := self.updated:
            obj.updated.FromDatetime(updated)

        return obj

    def to_nx(self, g: nx.DiGraph) -> None:
        g.add_node(
            self._id,
            label=scheme2text.get(
                self.argumentation_scheme, scheme_type2text[self.type]
            ),
        )

    def color(self, major_claim: bool) -> ColorMapping:

        if self.type == SchemeType.SUPPORT:
            return ColorMapping(bg="#def8e9", border="#2ecc71")
        elif self.type == SchemeType.ATTACK:
            return ColorMapping(bg="#fbdedb", border="#e74c3c")
        elif self.type == SchemeType.TRANSITION:
            return ColorMapping(bg="#eee3f3", border="#9b59b6")
        elif self.type == SchemeType.REPHRASE:
            return ColorMapping(bg="#fbeadb", border="#e67e22")
        elif self.type == SchemeType.PREFERENCE:
            return ColorMapping(bg="#dcfaf4", border="#1abc9c")
        elif self.type == SchemeType.ASSERTION:
            return ColorMapping(bg="#fdf6d9", border="#f1c40f")

        return ColorMapping(bg="#e9eded", border="#95a5a6")

    def to_gv(self, g: gv.Digraph, major_claim: bool, wrap_col: int) -> None:
        color = self.color(major_claim)
        label = scheme2text.get(self.argumentation_scheme, scheme_type2text[self.type])

        g.node(
            self._id,
            label=label.strip(),
            fontcolor=color.fg,
            fillcolor=color.bg,
            color=color.border,
        )


def _from_aif(obj: t.Mapping[str, t.Any]) -> t.Dict[str, t.Any]:
    timestamp = dt.from_aif(obj.get("timestamp"))

    return {"id": obj["nodeID"], "created": timestamp, "updated": timestamp}


def _to_aif(n: Node) -> t.Dict[str, t.Any]:
    return {
        "nodeID": n._id,
        "timestamp": dt.to_aif(n.created),
    }


def _from_ova(obj: t.Mapping[str, t.Any]) -> t.Dict[str, t.Any]:
    timestamp = dt.from_ova(obj.get("date"))

    return {"id": str(obj["id"]), "created": timestamp, "updated": timestamp}

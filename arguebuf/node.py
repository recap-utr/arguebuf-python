from __future__ import absolute_import, annotations

import re
import textwrap
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import graphviz as gv
import networkx as nx
import pendulum
from arg_services.graph.v1 import graph_pb2
from pendulum.datetime import DateTime

from arguebuf import dt, utils
from arguebuf.data import Metadata, Participant, Reference, Resource


class SchemeType(Enum):
    SUPPORT = graph_pb2.SCHEME_TYPE_SUPPORT
    ATTACK = graph_pb2.SCHEME_TYPE_ATTACK
    REPHRASE = graph_pb2.SCHEME_TYPE_REPHRASE
    TRANSITION = graph_pb2.SCHEME_TYPE_TRANSITION
    PREFERENCE = graph_pb2.SCHEME_TYPE_PREFERENCE
    ASSERTION = graph_pb2.SCHEME_TYPE_ASSERTION


scheme_type2aif_type = {
    SchemeType.SUPPORT: "RA",
    SchemeType.ATTACK: "CA",
    SchemeType.REPHRASE: "MA",
    SchemeType.TRANSITION: "TA",
    SchemeType.PREFERENCE: "PA",
    SchemeType.ASSERTION: "YA",
    None: "",
}

aif_type2scheme_type = {value: key for key, value in scheme_type2aif_type.items()}

scheme_type2text = {
    SchemeType.SUPPORT: "Support",
    SchemeType.ATTACK: "Attack",
    SchemeType.REPHRASE: "Rephrase",
    SchemeType.TRANSITION: "Transition",
    SchemeType.PREFERENCE: "Preference",
    SchemeType.ASSERTION: "Assertion",
    None: "Unspecified",
}

scheme_type2aif_text = {
    SchemeType.SUPPORT: "Default Inference",
    SchemeType.ATTACK: "Default Conflict",
    SchemeType.REPHRASE: "Default Rephrase",
    SchemeType.TRANSITION: "Default Transition",
    SchemeType.PREFERENCE: "Default Preference",
    SchemeType.ASSERTION: "Default Assertion",
    None: "",
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
scheme2text = {
    Scheme.AD_HOMINEM: "Ad Hominem",
    Scheme.ALTERNATIVE_MEANS: "Alternative Means",
    Scheme.ALTERNATIVES: "Alternatives",
    Scheme.ANALOGY: "Analogy",
    Scheme.ARBITRARY_VERBAL_CLASSIFICATION: "Arbitrary Verbal Classification",
    Scheme.AUTHORITY: "Authority",
    Scheme.BIAS: "Bias",
    Scheme.BIASED_CLASSIFICATION: "Biased_Classification",
    Scheme.CALLING_OUT: "Calling Out",
    Scheme.CAUSAL_SLIPPERY_SLOPE: "Causal Slippery Slope",
    Scheme.CAUSE_TO_EFFECT: "Cause To Effect",
    Scheme.CIRCUMSTANTIAL_AD_HOMINEM: "Circumstantial Ad Hominem",
    Scheme.COMMITMENT_EXCEPTION: "Commitment Exception",
    Scheme.COMMITMENT: "Commitment",
    Scheme.COMPOSITION: "Composition",
    Scheme.CONFLICTING_GOALS: "Conflicting Goals",
    Scheme.CONSEQUENCES: "Consequences",
    Scheme.CORRELATION_TO_CAUSE: "Correlation To Cause",
    Scheme.DANGER_APPEAL: "Danger Appeal",
    Scheme.DEFINITION_TO_VERBAL_CLASSIFICATION: "Definition To Verbal Classification",
    Scheme.DIFFERENCES_UNDERMINE_SIMILARITY: "Differences Undermine Similarity",
    Scheme.DILEMMA: "Dilemma",
    Scheme.DIRECT_AD_HOMINEM: "Direct Ad Hominem",
    Scheme.DIVISION: "Division",
    Scheme.ESTABLISHED_RULE: "Established Rule",
    Scheme.ETHOTIC: "Ethotic",
    Scheme.EVIDENCE_TO_HYPOTHESIS: "Evidence To Hypothesis",
    Scheme.EXAMPLE: "Example",
    Scheme.EXCEPTION_SIMILARITY_CASE: "Exception Similarity Case",
    Scheme.EXCEPTIONAL_CASE: "Exceptional Case",
    Scheme.EXPERT_OPINION: "Expert Opinion",
    Scheme.EXPERTISE_INCONSISTENCY: "Expertise Inconsistency",
    Scheme.FAIRNESS: "Fairness",
    Scheme.FALSIFICATION_OF_HYPOTHESIS: "Falsification Of Hypothesis",
    Scheme.FEAR_APPEAL: "Fear Appeal",
    Scheme.FULL_SLIPPERY_SLOPE: "Full Slippery Slope",
    Scheme.GENERAL_ACCEPTANCE_DOUBT: "General Acceptance Doubt",
    Scheme.GENERIC_AD_HOMINEM: "Generic Ad Hominem",
    Scheme.GOODWILL: "Goodwill",
    Scheme.GRADUALISM: "Gradualism",
    Scheme.IGNORANCE: "Ignorance",
    Scheme.INCONSISTENT_COMMITMENT: "Inconsistent Commitment",
    Scheme.INFORMANT_REPORT: "Informant Report",
    Scheme.INTERACTION_OF_ACT_AND_PERSON: "Interaction Of Act And Person",
    Scheme.IRRATIONAL_FEAR_APPEAL: "Irrational Fear Appeal",
    Scheme.LACK_OF_COMPLETE_KNOWLEDGE: "Lack Of Complete Knowledge",
    Scheme.LACK_OF_EXPERT_RELIABILITY: "Lack Of Expert Reliability",
    Scheme.LOGICAL: "Logical",
    Scheme.MISPLACED_PRIORITIES: "Misplaced Priorities",
    Scheme.MODUS_PONENS: "Modus Ponens",
    Scheme.MORAL_VIRTUE: "Moral Virtue",
    Scheme.NEED_FOR_HELP: "Need For Help",
    Scheme.NEGATIVE_CONSEQUENCES: "Negative Consequences",
    Scheme.OPPOSED_COMMITMENT: "Opposed Commitment",
    Scheme.OPPOSITIONS: "Oppositions",
    Scheme.CAUSAL_FACTORS_INVOLVED: "Causal Factors Involved",
    Scheme.PARAPHRASE: "Paraphrase",
    Scheme.PERCEPTION: "Perception",
    Scheme.POPULAR_OPINION: "Popular Opinion",
    Scheme.POPULAR_PRACTICE: "Popular Practice",
    Scheme.POSITION_TO_KNOW: "Position To Know",
    Scheme.POSITIVE_CONSEQUENCES: "Positive Consequences",
    Scheme.PRACTICAL_REASONING_FROM_ANALOGY: "Practical Reasoning From Analogy",
    Scheme.PRACTICAL_REASONING: "Practical Reasoning",
    Scheme.PRACTICAL_WISDOM: "Practical Wisdom",
    Scheme.PRAGMATIC_ALTERNATIVES: "Pragmatic Alternatives",
    Scheme.PRAGMATIC_INCONSISTENCY: "Pragmatic Inconsistency",
    Scheme.PRECEDENT_SLIPPERY_SLOPE: "Precedent Slippery Slope",
    Scheme.PROPERTY_NOT_EXISTANT: "Property Not Existant",
    Scheme.REFRAMING: "Reframing",
    Scheme.REQUIRED_STEPS: "Required Steps",
    Scheme.RESOLVING_INCONSISTENCY: "Resolving Inconsistency",
    Scheme.RULE: "Rule",
    Scheme.RULES: "Rules",
    Scheme.SIGN_FROM_OTHER_EVENTS: "Sign From Other Events",
    Scheme.SIGN: "Sign",
    Scheme.TWO_PERSON_PRACTICAL_REASONING: "Two Person Practical Reasoning",
    Scheme.UNFAIRNESS: "Unfairness",
    Scheme.VAGUE_VERBAL_CLASSIFICATION: "Vague Verbal Classification",
    Scheme.VAGUENESS_OF_VERBAL_CLASSIFICATION: "Vagueness Of Verbal Classification",
    Scheme.VALUE_BASED_PRACTICAL_REASONING: "Value Based Practical Reasoning",
    Scheme.VALUES: "Values",
    Scheme.VERBAL_CLASSIFICATION: "Verbal Classification",
    Scheme.VERBAL_SLIPPERY_SLOPE: "Verbal Slippery Slope",
    Scheme.VESTED_INTEREST: "Vested Interest",
    Scheme.VIRTUE_GOODWILL: "Virtue Goodwill",
    Scheme.WASTE: "Waste",
    Scheme.WEAKEST_LINK: "Weakest Link",
    Scheme.WISDOM_GOODWILL: "Wisdom Goodwill",
    Scheme.WISDOM_VIRTUE: "Wisdom Virtue",
    Scheme.WISDOM_VIRTUE_GOODWILL: "Wisdom Virtue Goodwill",
    Scheme.WITNESS_TESTIMONY: "Witness Testimony",
}

# TODO
text2scheme = {
    "Ad Hominem": Scheme.AD_HOMINEM,
    "Alternative Means": Scheme.ALTERNATIVE_MEANS,
    "Alternatives (Cognitive Schemes)": Scheme.ALTERNATIVES,
    "Alternatives": Scheme.ALTERNATIVES,
    "Analogy": Scheme.ANALOGY,
    "Arbitrary Verbal Classification": Scheme.ARBITRARY_VERBAL_CLASSIFICATION,
    "Argument From Authority": Scheme.AUTHORITY,
    "Bias": Scheme.BIAS,
    "Biased Classification": Scheme.BIASED_CLASSIFICATION,
    "Calling Out": Scheme.CALLING_OUT,
    "Causal Slippery Slope": Scheme.CAUSAL_SLIPPERY_SLOPE,
    "Cause To Effect": Scheme.CAUSE_TO_EFFECT,
    "Circumstantial Ad Hominem": Scheme.CIRCUMSTANTIAL_AD_HOMINEM,
    "Commitment Exception": Scheme.COMMITMENT_EXCEPTION,
    "Commitment": Scheme.COMMITMENT,
    "Composition": Scheme.COMPOSITION,
    "Conflicting Goals": Scheme.CONFLICTING_GOALS,
    "Consequences": Scheme.CONSEQUENCES,
    "Correlation To Cause": Scheme.CORRELATION_TO_CAUSE,
    "Danger Appeal": Scheme.DANGER_APPEAL,
    "Definition To Verbal Classification": Scheme.DEFINITION_TO_VERBAL_CLASSIFICATION,
    "Differences Undermine Similarity": Scheme.DIFFERENCES_UNDERMINE_SIMILARITY,
    "Dilemma": Scheme.DILEMMA,
    "Direct Ad Hominem": Scheme.DIRECT_AD_HOMINEM,
    "Division": Scheme.DIVISION,
    "Established Rule": Scheme.ESTABLISHED_RULE,
    "Ethotic": Scheme.ETHOTIC,
    "Evidence To Hypothesis": Scheme.EVIDENCE_TO_HYPOTHESIS,
    "Example": Scheme.EXAMPLE,
    "Exception Similarity Case": Scheme.EXCEPTION_SIMILARITY_CASE,
    "Exceptional Case": Scheme.EXCEPTIONAL_CASE,
    "Expert Opinion": Scheme.EXPERT_OPINION,
    "Expertise Inconsistency": Scheme.EXPERTISE_INCONSISTENCY,
    "Fairness": Scheme.FAIRNESS,
    "Falsification Of Hypothesis": Scheme.FALSIFICATION_OF_HYPOTHESIS,
    "Fear Appeal": Scheme.FEAR_APPEAL,
    "Full Slippery Slope": Scheme.FULL_SLIPPERY_SLOPE,
    "General Acceptance Doubt": Scheme.GENERAL_ACCEPTANCE_DOUBT,
    "Generic Ad Hominem": Scheme.GENERIC_AD_HOMINEM,
    "Argument From Goodwill": Scheme.GOODWILL,
    "Gradualism": Scheme.GRADUALISM,
    "Ignorance": Scheme.IGNORANCE,
    "Inconsistent Commitment": Scheme.INCONSISTENT_COMMITMENT,
    "Informant Report": Scheme.INFORMANT_REPORT,
    "Interaction Of Act And Person": Scheme.INTERACTION_OF_ACT_AND_PERSON,
    "Irrational Fear Appeal": Scheme.IRRATIONAL_FEAR_APPEAL,
    "Lack Of Complete Knowledge": Scheme.LACK_OF_COMPLETE_KNOWLEDGE,
    "Lack Of Expert Reliability": Scheme.LACK_OF_EXPERT_RELIABILITY,
    "Logical": Scheme.LOGICAL,
    "Misplaced Priorities": Scheme.MISPLACED_PRIORITIES,
    "Modus Ponens": Scheme.MODUS_PONENS,
    "Argument From Moral Virtue": Scheme.MORAL_VIRTUE,
    "Need For Help": Scheme.NEED_FOR_HELP,
    "Negative Consequences": Scheme.NEGATIVE_CONSEQUENCES,
    "Opposed Commitment": Scheme.OPPOSED_COMMITMENT,
    "Oppositions": Scheme.OPPOSITIONS,
    "Causal Factors Involved": Scheme.CAUSAL_FACTORS_INVOLVED,
    "Paraphrase": Scheme.PARAPHRASE,
    "Perception": Scheme.PERCEPTION,
    "Popular Opinion": Scheme.POPULAR_OPINION,
    "Popular Practice": Scheme.POPULAR_PRACTICE,
    "Position To Know": Scheme.POSITION_TO_KNOW,
    "Positive Consequences": Scheme.POSITIVE_CONSEQUENCES,
    "Practical Reasoning From Analogy": Scheme.PRACTICAL_REASONING_FROM_ANALOGY,
    "Practical Reasoning": Scheme.PRACTICAL_REASONING,
    "Argument From Practical Wisdom": Scheme.PRACTICAL_WISDOM,
    "Pragmatic Alternatives": Scheme.PRAGMATIC_ALTERNATIVES,
    "Pragmatic Inconsistency": Scheme.PRAGMATIC_INCONSISTENCY,
    "Precedent Slippery Slope": Scheme.PRECEDENT_SLIPPERY_SLOPE,
    "Property Not Existant": Scheme.PROPERTY_NOT_EXISTANT,
    "Reframing": Scheme.REFRAMING,
    "Required Steps": Scheme.REQUIRED_STEPS,
    "Resolving Inconsistency": Scheme.RESOLVING_INCONSISTENCY,
    "Rule": Scheme.RULE,
    "Rules": Scheme.RULES,
    "Sign From Other Events": Scheme.SIGN_FROM_OTHER_EVENTS,
    "Sign": Scheme.SIGN,
    "Two Person Practical Reasoning": Scheme.TWO_PERSON_PRACTICAL_REASONING,
    "Unfairness": Scheme.UNFAIRNESS,
    "Vague Verbal Classification": Scheme.VAGUE_VERBAL_CLASSIFICATION,
    "Vagueness Of Verbal Classification": Scheme.VAGUENESS_OF_VERBAL_CLASSIFICATION,
    "Value Based Practical Reasoning": Scheme.VALUE_BASED_PRACTICAL_REASONING,
    "Values": Scheme.VALUES,
    "Verbal Classification": Scheme.VERBAL_CLASSIFICATION,
    "Verbal Slippery Slope": Scheme.VERBAL_SLIPPERY_SLOPE,
    "Vested Interest": Scheme.VESTED_INTEREST,
    "Argument From Virtue/Goodwill": Scheme.VIRTUE_GOODWILL,
    "Waste": Scheme.WASTE,
    "Weakest Link": Scheme.WEAKEST_LINK,
    "Argument From Wisdom/Goodwill": Scheme.WISDOM_GOODWILL,
    "Argument From Wisdom/Virtue": Scheme.WISDOM_VIRTUE,
    "Argument From Wisdom/Virtue/Goodwill": Scheme.WISDOM_VIRTUE_GOODWILL,
    "Witness Testimony": Scheme.WITNESS_TESTIMONY,
    "Conflict From Wisdom/Goodwill": Scheme.WISDOM_GOODWILL,
    "Conflict From Wisdom/Virtue": Scheme.WISDOM_VIRTUE,
    "Conflict From Wisdom/Virtue/Goodwill": Scheme.WISDOM_VIRTUE_GOODWILL,
    "Conflict From Virtue/Goodwill": Scheme.VIRTUE_GOODWILL,
    "Conflict From Practical Wisdom": Scheme.PRACTICAL_WISDOM,
    "Conflict From Moral Virtue": Scheme.MORAL_VIRTUE,
    "Conflict From Goodwill": Scheme.GOODWILL,
    "ERAd Hominem": Scheme.AD_HOMINEM,
}


@dataclass
class ColorMapping:
    bg: str = "#ffffff"
    fg: str = "#000000"
    border: str = "#000000"


class Node(ABC):
    """Node in the AIF format."""

    _id: str
    created: DateTime
    updated: DateTime
    metadata: Metadata

    def __init__(
        self,
        created: t.Optional[DateTime] = None,
        updated: t.Optional[DateTime] = None,
        metadata: t.Optional[Metadata] = None,
        id: t.Optional[str] = None,
    ):
        self._id = id or utils.unique_id()
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
        pass

    @classmethod
    @abstractmethod
    def from_ova(
        cls,
        obj: t.Mapping[str, t.Any],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        """Generate Node object from OVA Node format."""
        pass

    @classmethod
    @abstractmethod
    def from_aif(
        cls,
        obj: t.Mapping[str, t.Any],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        """Generate Node object from AIF Node format."""
        pass

    @abstractmethod
    def to_aif(self) -> t.Dict[str, t.Any]:
        """Export Node object into AIF Node format."""
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
        """Generate Node object from PROTOBUF Node object."""
        pass

    @abstractmethod
    def to_protobuf(self) -> graph_pb2.Node:
        """Export Node object into PROTOBUF Node object."""
        pass

    @abstractmethod
    def to_nx(self, g: nx.DiGraph) -> None:
        """Submethod used to export Graph object g into NX Graph format."""
        pass

    @abstractmethod
    def to_gv(self, g: gv.Digraph, major_claim: bool, wrap_col: int) -> None:
        """Submethod used to export Graph object g into GV Graph format."""
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
        text: t.Any,
        resource: t.Optional[Reference] = None,
        participant: t.Optional[Participant] = None,
        created: t.Optional[DateTime] = None,
        updated: t.Optional[DateTime] = None,
        metadata: t.Optional[Metadata] = None,
        id: t.Optional[str] = None,
    ):
        super().__init__(created, updated, metadata, id)
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
    ) -> AtomNode:
        """Generate AtomNode object from AIF Node object."""
        return cls(
            **_from_aif(obj),
            text=utils.parse(obj["text"], nlp),
        )

    def to_aif(self) -> t.Dict[str, t.Any]:
        """Export AtomNode object into AIF Node object."""
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
    ) -> AtomNode:
        """Generate AtomNode object from OVA Node object."""
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
        """Generate AtomNode object from PROTOBUF Node object."""
        return cls(
            utils.parse(obj.atom.text, nlp),
            reference_class.from_protobuf(obj.atom.reference, resources, nlp),
            participants.get(obj.atom.participant),
            dt.from_protobuf(obj.created),
            dt.from_protobuf(obj.updated),
            dict(obj.metadata.items()),
            id=id,
        )

    def to_protobuf(self) -> graph_pb2.Node:
        """Export AtomNode object into PROTOBUF Node object."""
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
        """Submethod used to export Graph object g into NX Graph format."""
        g.add_node(
            self._id,
            label=self.plain_text,
        )

    def color(self, major_claim: bool) -> ColorMapping:
        """Get the color for rendering the node."""
        if major_claim:
            return ColorMapping(bg="#3498db", border="#3498db")

        return ColorMapping(bg="#ddeef9", border="#3498db")

    def to_gv(self, g: gv.Digraph, major_claim: bool, wrap_col: int) -> None:
        """Submethod used to export Graph object g into GV Graph format."""
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

    type: t.Optional[SchemeType]
    argumentation_scheme: t.Optional[Scheme]
    descriptors: t.Dict[str, str]

    def __init__(
        self,
        type: t.Optional[SchemeType],
        argumentation_scheme: t.Optional[Scheme] = None,
        descriptors: t.Optional[t.Mapping[str, str]] = None,
        created: t.Optional[DateTime] = None,
        updated: t.Optional[DateTime] = None,
        metadata: t.Optional[Metadata] = None,
        id: t.Optional[str] = None,
    ):
        super().__init__(created, updated, metadata, id)
        self.type = type
        self.argumentation_scheme = argumentation_scheme
        self.descriptors = dict(descriptors) if descriptors else {}

    def __repr__(self):
        return utils.class_repr(
            self,
            [
                self._id,
                scheme_type2text[self.type],
                utils.xstr(
                    scheme2text[self.argumentation_scheme]
                    if self.argumentation_scheme
                    else None
                ),
            ],
        )

    @classmethod
    def from_aif(
        cls,
        obj: t.Mapping[str, t.Any],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> t.Optional[SchemeNode]:
        """Generate SchemeNode object from AIF Node object."""

        if obj["type"] in aif_type2scheme_type:
            node = cls(
                **_from_aif(obj),
                type=aif_type2scheme_type[obj["type"]],
            )

            if scheme := obj.get("scheme"):
                # In araucaria, 'Expert Opinion' is written as 'ExpertOpinion'.
                # https://stackoverflow.com/a/199094/7626878
                scheme = re.sub("([A-Z])", r" \1", scheme)

                node.argumentation_scheme = text2scheme.get(scheme)

            elif not obj["text"].startswith("Default "):
                node.argumentation_scheme = text2scheme.get(obj["text"])

            return node

        return None

    def to_aif(self) -> t.Dict[str, t.Any]:
        """Export SchemeNode object into AIF Node object."""

        return {
            **_to_aif(self),
            "text": scheme2text[self.argumentation_scheme]
            if self.argumentation_scheme
            else scheme_type2aif_text[self.type],
            "type": scheme_type2aif_type[self.type],
        }

    @classmethod
    def from_ova(
        cls,
        obj: t.Mapping[str, t.Any],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> t.Optional[SchemeNode]:
        """Generate SchemeNode object from OVA Node object."""

        if obj["type"] in aif_type2scheme_type:
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
                type=aif_type2scheme_type[obj["type"]],
                descriptors=descriptors,
            )

        return None

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
        """Generate SchemeNode object from OVA Node object."""
        return cls(
            SchemeType(obj.scheme.type) if obj.scheme.type else None,
            Scheme(obj.scheme.argumentation_scheme)
            if obj.scheme.argumentation_scheme
            else None,
            dict(obj.scheme.descriptors.items()),
            dt.from_protobuf(obj.created),
            dt.from_protobuf(obj.updated),
            dict(obj.metadata.items()),
            id=id,
        )

    def to_protobuf(self) -> graph_pb2.Node:
        """Export SchemeNode object into PROTOBUF Node object."""
        obj = graph_pb2.Node()
        obj.metadata.update(self.metadata)
        obj.scheme.type = (
            self.type.value
            if self.type
            else graph_pb2.SchemeType.SCHEME_TYPE_UNSPECIFIED
        )
        obj.scheme.descriptors.update(self.descriptors)

        if arg_scheme := self.argumentation_scheme:
            obj.scheme.argumentation_scheme = arg_scheme.value

        if created := self.created:
            obj.created.FromDatetime(created)

        if updated := self.updated:
            obj.updated.FromDatetime(updated)

        return obj

    def to_nx(self, g: nx.DiGraph) -> None:
        """Submethod used to export Graph object g into NX Graph format."""
        g.add_node(
            self._id,
            label=scheme2text[self.argumentation_scheme]
            if self.argumentation_scheme
            else scheme_type2text[self.type],
        )

    def color(self, major_claim: bool) -> ColorMapping:
        """Get the color used in OVA based on `category`."""
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
        """Submethod used to export Graph object g into GV Graph format."""
        color = self.color(major_claim)

        g.node(
            self._id,
            label=scheme2text[self.argumentation_scheme]
            if self.argumentation_scheme
            else scheme_type2text[self.type],
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

from collections.abc import Mapping
from enum import StrEnum, auto
from types import MappingProxyType
from typing import Final, Literal, Protocol

from arg_services.graph.v1 import graph_pb2
from google.protobuf.descriptor import EnumValueDescriptor

from arguebuf.schemas import aif

__all__ = (
    "AIF_SCHEME_TYPES",
    "SCHEME_AIF_DEFAULTS",
    "SCHEME_AIF_TYPES",
    "SCHEME_CLASSES",
    "SCHEME_TYPE_LABELS",
    "SCHEME_TYPE_NAMES",
    "Attack",
    "Preference",
    "Rephrase",
    "Scheme",
    "SchemeType",
    "Support",
    "allows_multiple_premises",
    "resolve_aif_scheme",
    "resolve_scheme",
)


class _GenerateValue(Protocol):
    def __call__(
        self, name: str, start: int, count: int, last_values: list[str]
    ) -> str: ...


def _protobuf_value(enum: str, member: str) -> EnumValueDescriptor:
    """Value of a protobuf scheme enum, e.g. `SUPPORT_SIGN` for `Support` and `SIGN`."""
    values = graph_pb2.DESCRIPTOR.enum_types_by_name[enum].values_by_name

    return values[f"{enum.upper()}_{member}"]


def _labels(enum: str) -> _GenerateValue:
    """Generate the values of `auto()` members from the labels of a protobuf enum."""

    def label(name: str, start: int, count: int, last_values: list[str]) -> str:
        return _protobuf_value(enum, name).GetOptions().Extensions[graph_pb2.label]

    return label


class Support(StrEnum):
    """Supporting argumentation schemes according to Walton et al."""

    _generate_next_value_ = staticmethod(_labels("Support"))

    DEFAULT = auto()
    POSITION_TO_KNOW = auto()
    EXPERT_OPINION = auto()
    WITNESS_TESTIMONY = auto()
    POPULAR_OPINION = auto()
    POPULAR_PRACTICE = auto()
    EXAMPLE = auto()
    ANALOGY = auto()
    PRACTICAL_REASONING_FROM_ANALOGY = auto()
    COMPOSITION = auto()
    DIVISION = auto()
    OPPOSITIONS = auto()
    RHETORICAL_OPPOSITIONS = auto()
    ALTERNATIVES = auto()
    VERBAL_CLASSIFICATION = auto()
    VERBAL_CLASSIFICATION_DEFINITION = auto()
    VERBAL_CLASSIFICATION_VAGUENESS = auto()
    VERBAL_CLASSIFICATION_ARBITRARINESS = auto()
    INTERACTION_OF_ACT_AND_PERSON = auto()
    VALUES = auto()
    POSITIVE_VALUES = auto()
    NEGATIVE_VALUES = auto()
    SACRIFICE = auto()
    THE_GROUP_AND_ITS_MEMBERS = auto()
    PRACTICAL_REASONING = auto()
    TWO_PERSON_PRACTICAL_REASONING = auto()
    WASTE = auto()
    SUNK_COSTS = auto()
    IGNORANCE = auto()
    EPISTEMIC_IGNORANCE = auto()
    CAUSE_TO_EFFECT = auto()
    CORRELATION_TO_CAUSE = auto()
    SIGN = auto()
    ABDUCTIVE = auto()
    EVIDENCE_TO_HYPOTHESIS = auto()
    CONSEQUENCES = auto()
    POSITIVE_CONSEQUENCES = auto()
    NEGATIVE_CONSEQUENCES = auto()
    PRAGMATIC_ALTERNATIVES = auto()
    THREAT = auto()
    FEAR_APPEAL = auto()
    DANGER_APPEAL = auto()
    NEED_FOR_HELP = auto()
    DISTRESS = auto()
    COMMITMENT = auto()
    ETHOTIC = auto()
    GENERIC_AD_HOMINEM = auto()
    PRAGMATIC_INCONSISTENCY = auto()
    INCONSISTENT_COMMITMENT = auto()
    CIRCUMSTANTIAL_AD_HOMINEM = auto()
    BIAS = auto()
    BIAS_AD_HOMINEM = auto()
    GRADUALISM = auto()
    SLIPPERY_SLOPE = auto()
    PRECEDENT_SLIPPERY_SLOPE = auto()
    SORITES_SLIPPERY_SLOPE = auto()
    VERBAL_SLIPPERY_SLOPE = auto()
    FULL_SLIPPERY_SLOPE = auto()
    CONSTITUTIVE_RULE_CLAIMS = auto()
    RULES = auto()
    EXCEPTIONAL_CASE = auto()
    PRECEDENT = auto()
    PLEA_FOR_EXCUSE = auto()
    PERCEPTION = auto()
    MEMORY = auto()


class Attack(StrEnum):
    """Attacking argumentation schemes."""

    _generate_next_value_ = staticmethod(_labels("Attack"))

    DEFAULT = auto()


class Preference(StrEnum):
    """Preference argumentation schemes."""

    _generate_next_value_ = staticmethod(_labels("Preference"))

    DEFAULT = auto()


class Rephrase(StrEnum):
    """Rephrasing argumentation schemes."""

    _generate_next_value_ = staticmethod(_labels("Rephrase"))

    DEFAULT = auto()


type Scheme = Support | Attack | Rephrase | Preference

type SchemeType = Literal["support", "attack", "rephrase", "preference"]
"""Name of a scheme type, identical to the field of the protobuf `Scheme.type` oneof."""

SCHEME_CLASSES: Final[Mapping[SchemeType, type[Scheme]]] = MappingProxyType(
    {
        "support": Support,
        "attack": Attack,
        "rephrase": Rephrase,
        "preference": Preference,
    }
)
"""Scheme classes by their `SchemeType` name."""

SCHEME_TYPE_NAMES: Final[Mapping[type[Scheme], SchemeType]] = MappingProxyType(
    {scheme_type: name for name, scheme_type in SCHEME_CLASSES.items()}
)
"""`SchemeType` names by their scheme class."""

SCHEME_TYPE_LABELS: Final[Mapping[type[Scheme], str]] = MappingProxyType(
    {
        Support: "Support",
        Attack: "Attack",
        Rephrase: "Rephrase",
        Preference: "Preference",
    }
)
"""Human-readable labels of the scheme types."""

# field of the protobuf `Scheme.type` oneof and enum value of each scheme,
# keyed by type since members of different scheme types are equal strings
_SCHEME_PROTOBUF: Final[Mapping[type[Scheme], tuple[str, Mapping[Scheme, int]]]] = (
    MappingProxyType(
        {
            scheme_type: (
                name,
                MappingProxyType(
                    {
                        item: _protobuf_value(scheme_type.__name__, item.name).number
                        for item in scheme_type
                    }
                ),
            )
            for scheme_type, name in SCHEME_TYPE_NAMES.items()
        }
    )
)
# schemes by the field of the protobuf `Scheme.type` oneof and their enum value
_PROTOBUF_SCHEMES: Final[Mapping[str, Mapping[int, Scheme]]] = MappingProxyType(
    {
        field: MappingProxyType({value: item for item, value in values.items()})
        for field, values in _SCHEME_PROTOBUF.values()
    }
)

SCHEME_AIF_TYPES: Final[Mapping[type[Scheme], aif.SchemeType]] = MappingProxyType(
    {Support: "RA", Attack: "CA", Rephrase: "MA", Preference: "PA"}
)
"""AIF node types by their scheme class."""

AIF_SCHEME_TYPES: Final[Mapping[str, type[Scheme]]] = MappingProxyType(
    {aif_type: scheme_type for scheme_type, aif_type in SCHEME_AIF_TYPES.items()}
)
"""Scheme classes by their AIF node type."""

SCHEME_AIF_DEFAULTS: Final[Mapping[type[Scheme], str]] = MappingProxyType(
    {
        Support: "Default Inference",
        Attack: "Default Conflict",
        Rephrase: "Default Rephrase",
        Preference: "Default Preference",
    }
)
"""AIFdb labels of the default schemes."""


def allows_multiple_premises(scheme_type: type[Scheme]) -> bool:
    """Whether schemes of the type may have several premises, only supports may as in AIF.

    >>> allows_multiple_premises(Support), allows_multiple_premises(Attack)
    (True, False)
    """
    return scheme_type is Support


def is_default_scheme(scheme: Scheme) -> bool:
    """Check whether the scheme is the default one of its type.

    >>> is_default_scheme(Support.DEFAULT), is_default_scheme(Support.SIGN)
    (True, False)
    """
    return scheme is type(scheme).DEFAULT


def normalize_scheme_label(text: str) -> str:
    """Make scheme labels comparable regardless of case and separators.

    >>> normalize_scheme_label("Expert Opinion") == normalize_scheme_label("ExpertOpinion")
    True
    """
    return "".join(char for char in text.casefold() if char.isalnum())


_support_aliases: dict[str, Support] = {
    "Arbitrary Verbal Classification": Support.VERBAL_CLASSIFICATION_ARBITRARINESS,
    "Causal Slippery Slope": Support.SLIPPERY_SLOPE,
    "Direct Ad Hominem": Support.GENERIC_AD_HOMINEM,
    "From-alternatives": Support.ALTERNATIVES,
    "From-analogy": Support.ANALOGY,
    "From-opposition": Support.OPPOSITIONS,
    "From-parts-and-whole": Support.DIVISION,
    "Opposition": Support.OPPOSITIONS,
    "Pragmatic Argument From Alternatives": Support.PRAGMATIC_ALTERNATIVES,
    "Vague Verbal Classification": Support.VERBAL_CLASSIFICATION_VAGUENESS,
    "Vagueness Of Verbal Classification": Support.VERBAL_CLASSIFICATION_VAGUENESS,
    "Value Based Practical Reasoning": Support.PRACTICAL_REASONING,
}

_text2scheme: dict[type[Scheme], dict[str, Scheme]] = {
    scheme_type: {normalize_scheme_label(item.value): item for item in scheme_type}
    for scheme_type in SCHEME_AIF_TYPES
}
_text2scheme[Support] |= {
    normalize_scheme_label(text): item for text, item in _support_aliases.items()
}


def resolve_scheme(scheme_type: type[Scheme], text: str) -> Scheme:
    """Get the scheme of the given type whose label matches the text.

    Labels are compared regardless of case and separators,
    a leading "Argument from" (as used by Araucaria) is ignored,
    and unknown labels resolve to the default scheme.

    >>> resolve_scheme(Support, "ExpertOpinion")
    <Support.EXPERT_OPINION: 'Expert Opinion'>
    >>> resolve_scheme(Support, "Argument from Sign")
    <Support.SIGN: 'Sign'>
    >>> resolve_scheme(Attack, "Default Conflict")
    <Attack.DEFAULT: 'Default'>
    """
    key = normalize_scheme_label(text).removeprefix("argumentfrom")

    return _text2scheme[scheme_type].get(key, scheme_type.DEFAULT)


def resolve_aif_scheme(aif_type: str, text: str) -> Scheme:
    """Get the scheme of an AIF scheme node, refined by its text if possible.

    Callers must ensure that `aif_type` is a key of `AIF_SCHEME_TYPES`.
    """
    return resolve_scheme(AIF_SCHEME_TYPES[aif_type], text)

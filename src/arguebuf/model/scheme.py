from enum import StrEnum

from arg_services.graph.v1 import graph_pb2

from arguebuf.schemas import aif

__all__ = ("Attack", "Preference", "Rephrase", "Scheme", "Support")


class Support(StrEnum):
    """Supporting argumentation schemes according to Walton et al."""

    DEFAULT = "Default"
    POSITION_TO_KNOW = "Position to Know"
    EXPERT_OPINION = "Expert Opinion"
    WITNESS_TESTIMONY = "Witness Testimony"
    POPULAR_OPINION = "Popular Opinion"
    POPULAR_PRACTICE = "Popular Practice"
    EXAMPLE = "Example"
    ANALOGY = "Analogy"
    PRACTICAL_REASONING_FROM_ANALOGY = "Practical Reasoning from Analogy"
    COMPOSITION = "Composition"
    DIVISION = "Division"
    OPPOSITIONS = "Oppositions"
    RHETORICAL_OPPOSITIONS = "Rhetorical Oppositions"
    ALTERNATIVES = "Alternatives"
    VERBAL_CLASSIFICATION = "Verbal Classification"
    VERBAL_CLASSIFICATION_DEFINITION = "Definition to Verbal Classification"
    VERBAL_CLASSIFICATION_VAGUENESS = "Vagueness of a Verbal Classification"
    VERBAL_CLASSIFICATION_ARBITRARINESS = "Arbitrariness of a Verbal Classification"
    INTERACTION_OF_ACT_AND_PERSON = "Interaction of Act and Person"
    VALUES = "Values"
    POSITIVE_VALUES = "Positive Values"
    NEGATIVE_VALUES = "Negative Values"
    SACRIFICE = "Sacrifice"
    THE_GROUP_AND_ITS_MEMBERS = "The Group and its Members"
    PRACTICAL_REASONING = "Practical Reasoning"
    TWO_PERSON_PRACTICAL_REASONING = "Two-Person Practical Reasoning"
    WASTE = "Waste"
    SUNK_COSTS = "Sunk Costs"
    IGNORANCE = "Ignorance"
    EPISTEMIC_IGNORANCE = "Epistemic Ignorance"
    CAUSE_TO_EFFECT = "Cause to Effect"
    CORRELATION_TO_CAUSE = "Correlation to Cause"
    SIGN = "Sign"
    ABDUCTIVE = "Abductive"
    EVIDENCE_TO_HYPOTHESIS = "Evidence to Hypothesis"
    CONSEQUENCES = "Consequences"
    POSITIVE_CONSEQUENCES = "Positive Consequences"
    NEGATIVE_CONSEQUENCES = "Negative Consequences"
    PRAGMATIC_ALTERNATIVES = "Pragmatic Alternatives"
    THREAT = "Threat"
    FEAR_APPEAL = "Fear Appeal"
    DANGER_APPEAL = "Danger Appeal"
    NEED_FOR_HELP = "Need for Help"
    DISTRESS = "Distress"
    COMMITMENT = "Commitment"
    ETHOTIC = "Ethotic"
    GENERIC_AD_HOMINEM = "Generic ad Hominem"
    PRAGMATIC_INCONSISTENCY = "Pragmatic Inconsistency"
    INCONSISTENT_COMMITMENT = "Inconsistent Commitment"
    CIRCUMSTANTIAL_AD_HOMINEM = "Circumstantial Ad Hominem"
    BIAS = "Bias"
    BIAS_AD_HOMINEM = "Bias Ad Hominem"
    GRADUALISM = "Gradualism"
    SLIPPERY_SLOPE = "Slippery Slope"
    PRECEDENT_SLIPPERY_SLOPE = "Precedent Slippery Slope"
    SORITES_SLIPPERY_SLOPE = "Sorites Slippery Slope"
    VERBAL_SLIPPERY_SLOPE = "Verbal Slippery Slope"
    FULL_SLIPPERY_SLOPE = "Full Slippery Slope"
    CONSTITUTIVE_RULE_CLAIMS = "Constitutive Rule Claims"
    RULES = "Rules"
    EXCEPTIONAL_CASE = "Exceptional Case"
    PRECEDENT = "Precedent"
    PLEA_FOR_EXCUSE = "Plea for Excuse"
    PERCEPTION = "Perception"
    MEMORY = "Memory"
    # AUTHORITY = "Authority"
    # DILEMMA = "Dilemma"
    # MODUS_PONENS = "Modus Ponens"
    # DEFINITION = "Definition"


class Attack(StrEnum):
    """Attacking argumentation schemes."""

    DEFAULT = "Default"


class Preference(StrEnum):
    """Preference argumentation schemes."""

    DEFAULT = "Default"


class Rephrase(StrEnum):
    """Rephrasing argumentation schemes."""

    DEFAULT = "Default"


type Scheme = Support | Attack | Rephrase | Preference

support2protobuf = {
    item: graph_pb2.Support.Value(f"SUPPORT_{item.name}") for item in Support
}
protobuf2support = {value: key for key, value in support2protobuf.items()}

attack2protobuf = {
    item: graph_pb2.Attack.Value(f"ATTACK_{item.name}") for item in Attack
}
protobuf2attack = {value: key for key, value in attack2protobuf.items()}

rephrase2protobuf = {
    item: graph_pb2.Rephrase.Value(f"REPHRASE_{item.name}") for item in Rephrase
}
protobuf2rephrase = {value: key for key, value in rephrase2protobuf.items()}

preference2protobuf = {
    item: graph_pb2.Preference.Value(f"PREFERENCE_{item.name}") for item in Preference
}
protobuf2preference = {value: key for key, value in preference2protobuf.items()}

scheme2aif: dict[type[Scheme], aif.SchemeType] = {
    Support: "RA",
    Attack: "CA",
    Rephrase: "MA",
    Preference: "PA",
}
aif2scheme: dict[str, type[Scheme] | None] = {
    aif_type: scheme_type for scheme_type, aif_type in scheme2aif.items()
} | {"": None}
# AIFdb labels of the default schemes
scheme2aif_default: dict[type[Scheme], str] = {
    Support: "Default Inference",
    Attack: "Default Conflict",
    Rephrase: "Default Rephrase",
    Preference: "Default Preference",
}


def _normalize(text: str) -> str:
    """Make scheme labels comparable regardless of case and separators.

    >>> _normalize("Expert Opinion") == _normalize("ExpertOpinion")
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
    scheme_type: {_normalize(item.value): item for item in scheme_type}
    for scheme_type in scheme2aif
}
_text2scheme[Support] |= {
    _normalize(text): item for text, item in _support_aliases.items()
}


def resolve_scheme(scheme_type: type[Scheme], text: str) -> Scheme:
    """Get the scheme of the given type whose label matches the text.

    Labels are compared regardless of case and separators,
    unknown labels resolve to the default scheme.

    >>> resolve_scheme(Support, "ExpertOpinion")
    <Support.EXPERT_OPINION: 'Expert Opinion'>
    >>> resolve_scheme(Attack, "Default Conflict")
    <Attack.DEFAULT: 'Default'>
    """
    return _text2scheme[scheme_type].get(_normalize(text), scheme_type.DEFAULT)


def resolve_aif_scheme(aif_type: str, text: str) -> Scheme | None:
    """Get the scheme of an AIF scheme node, refined by its text if possible.

    Callers must ensure that `aif_type` is a key of `aif2scheme`.
    """
    scheme_type = aif2scheme[aif_type]

    return resolve_scheme(scheme_type, text) if scheme_type else None

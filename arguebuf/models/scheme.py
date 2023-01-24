from __future__ import absolute_import, annotations

import typing as t
from enum import Enum

from arg_services.graph.v1 import graph_pb2

from arguebuf.schemas import aif


class Support(Enum):
    """Enumeration of all available Argumentation Schemes (Walton et al.)

    .. autoclasssumm:: Support
        :autosummary-sections: Methods
    """

    DEFAULT = "Default"
    POSITION_TO_KNOW = "Position to Know"
    EXPERT_OPINION = "Expert Opinion"
    WITNESS_TESTIMONY = "Witness Testimony"
    POPULAR_OPINION = "Popular Opinion"
    POPULAR_PRACTICE = "Popular Practice"
    EXAMPLE = "Example"
    ANALOGY = "Analogy"
    PRACTICAL_REASONING_FROM_ANALOGY = "Practical Resoning from Analogy"
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


class Attack(Enum):
    """Enumeration of attacking schemes

    .. autoclasssumm:: Attack
        :autosummary-sections: Methods
    """

    DEFAULT = "Default"


class Preference(Enum):
    """Enumeration of preference schemes

    .. autoclasssumm:: Preference
        :autosummary-sections: Methods
    """

    DEFAULT = "Default"


class Rephrase(Enum):
    """Enumeration of rephrase schemes

    .. autoclasssumm:: Rephrase
        :autosummary-sections: Methods
    """

    DEFAULT = "Default"


Scheme = t.Union[Support, Attack, Rephrase, Preference]

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

scheme2aif: t.Dict[t.Type[Scheme], aif.SchemeType] = {
    Support: "RA",
    Attack: "CA",
    Rephrase: "MA",
    Preference: "PA",
}
aif2scheme: t.Dict[aif.SchemeType, t.Optional[Scheme]] = {
    "RA": Support.DEFAULT,
    "CA": Attack.DEFAULT,
    "MA": Rephrase.DEFAULT,
    "PA": Preference.DEFAULT,
    "": None,
}

text2support: t.Dict[str, Support] = {
    "Alternatives": Support.ALTERNATIVES,
    "Analogy": Support.ANALOGY,
    "Arbitrary Verbal Classification": Support.VERBAL_CLASSIFICATION,
    "Argument From Authority": Support.DEFAULT,  # AUTHORITY
    "Argument From Goodwill": Support.DEFAULT,
    "Argument From Moral Virtue": Support.DEFAULT,
    "Argument From Practical Wisdom": Support.DEFAULT,
    "Argument From Virtue/Goodwill": Support.DEFAULT,
    "Argument From Wisdom/Goodwill": Support.DEFAULT,
    "Argument From Wisdom/Virtue": Support.DEFAULT,
    "Argument From Wisdom/Virtue/Goodwill": Support.DEFAULT,
    "Authority": Support.DEFAULT,  # AUTHORITY
    "Bias": Support.BIAS,
    "Causal Slippery Slope": Support.SLIPPERY_SLOPE,
    "Cause To Effect": Support.CAUSE_TO_EFFECT,
    "Circumstantial Ad Hominem": Support.CIRCUMSTANTIAL_AD_HOMINEM,
    "Commitment": Support.COMMITMENT,
    "Composition": Support.COMPOSITION,
    "Consequences": Support.CONSEQUENCES,
    "Correlation To Cause": Support.CORRELATION_TO_CAUSE,
    "Danger Appeal": Support.DANGER_APPEAL,
    "Default Inference": Support.DEFAULT,
    "Definitional": Support.DEFAULT,  # DEFINITION
    "Definition To Verbal Classification": Support.VERBAL_CLASSIFICATION,
    "Dilemma": Support.DEFAULT,  # DILEMMA
    "Direct Ad Hominem": Support.GENERIC_AD_HOMINEM,
    "Division": Support.DIVISION,
    "Efficient Cause": Support.DEFAULT,
    "Established Rule": Support.DEFAULT,
    "Ethotic": Support.ETHOTIC,
    "Evidence To Hypothesis": Support.EVIDENCE_TO_HYPOTHESIS,
    "Example": Support.EXAMPLE,
    "Exceptional Case": Support.EXCEPTIONAL_CASE,
    "Expert Opinion": Support.EXPERT_OPINION,
    "Falsification Of Hypothesis": Support.DEFAULT,
    "Fear Appeal": Support.FEAR_APPEAL,
    "Final Cause": Support.DEFAULT,
    "Formal Cause": Support.DEFAULT,
    "From-all-the-more-so-OR-all-the-less-so": Support.DEFAULT,
    "From-alternatives": Support.ALTERNATIVES,
    "From-analogy": Support.ANALOGY,
    "From-authority": Support.DEFAULT,  # AUTHORITY
    "From-conjugates-OR-derivates": Support.DEFAULT,
    "From-correlates": Support.DEFAULT,
    "From-definition": Support.DEFAULT,  # DEFINITION
    "From-description": Support.DEFAULT,
    "From-efficient-cause": Support.DEFAULT,
    "From-final-OR-instrumental-cause": Support.DEFAULT,
    "From-formal-cause": Support.DEFAULT,
    "From-genus-and-species": Support.DEFAULT,
    "From-material-cause": Support.DEFAULT,
    "From-ontological-implications": Support.DEFAULT,
    "From-opposition": Support.OPPOSITIONS,
    "From-parts-and-whole": Support.DIVISION,
    "From-place": Support.DEFAULT,
    "From-promising-and-warning": Support.DEFAULT,
    "From-termination-and-inception": Support.DEFAULT,
    "From-time": Support.DEFAULT,
    "Full Slippery Slope": Support.FULL_SLIPPERY_SLOPE,
    "Generic Ad Hominem": Support.GENERIC_AD_HOMINEM,
    "Gradualism": Support.GRADUALISM,
    "Ignorance": Support.IGNORANCE,
    "Inconsistent Commitment": Support.INCONSISTENT_COMMITMENT,
    "Informant Report": Support.DEFAULT,
    "Interaction Of Act And Person": Support.INTERACTION_OF_ACT_AND_PERSON,
    "Material Cause": Support.DEFAULT,
    "Mereological": Support.DEFAULT,
    "Modus Ponens": Support.DEFAULT,  # MODUS_PONENS
    "Need For Help": Support.NEED_FOR_HELP,
    "Negative Consequences": Support.NEGATIVE_CONSEQUENCES,
    "Opposition": Support.OPPOSITIONS,
    "Paraphrase": Support.DEFAULT,
    "Perception": Support.PERCEPTION,
    "Popular Opinion": Support.POPULAR_OPINION,
    "Popular Practice": Support.POPULAR_PRACTICE,
    "Position To Know": Support.POSITION_TO_KNOW,
    "Positive Consequences": Support.POSITIVE_CONSEQUENCES,
    "Practical Evaluation": Support.DEFAULT,
    "Practical Reasoning": Support.PRACTICAL_REASONING,
    "Practical Reasoning From Analogy": Support.PRACTICAL_REASONING_FROM_ANALOGY,
    "Pragmatic Argument From Alternatives": Support.PRAGMATIC_ALTERNATIVES,
    "Pragmatic Inconsistency": Support.PRAGMATIC_INCONSISTENCY,
    "Precedent Slippery Slope": Support.PRECEDENT_SLIPPERY_SLOPE,
    "Reframing": Support.DEFAULT,
    "Rules": Support.RULES,
    "Sign": Support.SIGN,
    "Two Person Practical Reasoning": Support.TWO_PERSON_PRACTICAL_REASONING,
    "Vagueness Of Verbal Classification": Support.VERBAL_CLASSIFICATION,
    "Vague Verbal Classification": Support.VERBAL_CLASSIFICATION,
    "Value Based Practical Reasoning": Support.PRACTICAL_REASONING,
    "Values": Support.VALUES,
    "Verbal Classification": Support.VERBAL_CLASSIFICATION,
    "Verbal Slippery Slope": Support.VERBAL_SLIPPERY_SLOPE,
    "Waste": Support.WASTE,
    "Witness Testimony": Support.WITNESS_TESTIMONY,
}

text2scheme: t.Dict[
    t.Type[Scheme],
    t.Union[
        t.Dict[str, Support],
        t.Dict[str, Attack],
        t.Dict[str, Rephrase],
        t.Dict[str, Preference],
    ],
] = {
    Support: text2support,
    Attack: {},
    Rephrase: {},
    Preference: {},
}

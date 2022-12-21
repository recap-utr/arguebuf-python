from __future__ import absolute_import, annotations

import textwrap
import typing as t
import xml.etree.ElementTree as et
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

import networkx as nx
import pendulum
import pygraphviz as gv
from arg_services.graph.v1 import graph_pb2

from arguebuf.models import Userdata
from arguebuf.models.metadata import Metadata
from arguebuf.models.participant import Participant
from arguebuf.models.reference import Reference
from arguebuf.models.resource import Resource
from arguebuf.schema import aif, argdown_json, ova, sadface
from arguebuf.services import dt, utils

NO_SCHEME_LABEL = "Unknown"


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


class Node(ABC):
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

    @classmethod
    @abstractmethod
    def from_ova(
        cls,
        obj: ova.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        """Generate Node object from OVA Node format."""

    @classmethod
    @abstractmethod
    def from_aif(
        cls,
        obj: aif.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        """Generate Node object from AIF Node format."""

    @classmethod
    @abstractmethod
    def from_sadface(
        cls,
        obj: sadface.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        """Generate Node object from SADFace Node format."""

    @classmethod
    @abstractmethod
    def from_argdown_json(
        cls,
        obj: argdown_json.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        """Import argdown"""

    @classmethod
    @abstractmethod
    def from_aml(
        cls,
        obj: et.Element,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        """Generate Node object from AML Node format."""

    @abstractmethod
    def to_aif(self) -> aif.Node:
        """Export Node object into AIF Node format."""

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

    @abstractmethod
    def to_protobuf(self) -> graph_pb2.Node:
        """Export Node object into PROTOBUF Node object."""

    @abstractmethod
    def to_nx(
        self,
        g: nx.DiGraph,
        attrs: t.Optional[t.MutableMapping[str, t.Callable[[Node], t.Any]]] = None,
    ) -> None:
        """Submethod used to export Graph object g into NX Graph format."""


class AtomNode(Node):
    __slots__ = (
        "_id",
        "metadata",
        "userdata",
        "text",
        "_reference",
        "_participant",
    )

    text: t.Any
    _reference: t.Optional[Reference]
    _participant: t.Optional[Participant]

    def __init__(
        self,
        text: t.Any,
        resource: t.Optional[Reference] = None,
        participant: t.Optional[Participant] = None,
        metadata: t.Optional[Metadata] = None,
        userdata: t.Optional[Userdata] = None,
        id: t.Optional[str] = None,
    ):
        super().__init__(metadata, userdata, id)
        self.text = text
        self._reference = resource
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
    def from_sadface(
        cls,
        obj: sadface.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> AtomNode:
        """Generate AtomNode object from SADFace Node object."""
        timestamp = pendulum.now()
        return cls(
            id=obj["id"],
            text=utils.parse(obj["text"], nlp),
            userdata=obj["metadata"],
            metadata=Metadata(timestamp, timestamp),
        )

    @classmethod
    def from_argdown_json(
        cls,
        obj: argdown_json.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> AtomNode:
        """Generate AtomNode object from Argdown JSON Node object."""
        timestamp = pendulum.now()
        return cls(
            id=obj["id"],
            text=utils.parse(obj["labelText"], nlp),
            metadata=Metadata(timestamp, timestamp),
        )

    @classmethod
    def from_aml(
        cls,
        obj: et.Element,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> AtomNode:
        """
        Generate Node object from AML Node format. obj is a AML "PROP" element.
        """
        # get id of PROP
        if "identifier" in obj.attrib:
            id = obj.get("identifier")
        else:
            id = None

        # read text of PROP
        text = obj.find("PROPTEXT").text

        # read owners of PROP
        owner_list = obj.findall("OWNER")
        owners_lst = []
        if not owner_list:
            # if not empty, do something
            for owner in owner_list:
                owners_lst.append(owner.get("name"))
            owners = {"owners": ", ".join(owners_lst)}
        else:
            owners = {}

        # create timestamp
        timestamp = pendulum.now()

        return cls(
            id=id,
            text=utils.parse(text, nlp),
            metadata=Metadata(timestamp, timestamp),
            userdata=owners,
        )

    @classmethod
    def from_aif(
        cls,
        obj: aif.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> AtomNode:
        """Generate AtomNode object from AIF Node object."""
        timestamp = (
            dt.from_format(obj.get("timestamp"), aif.DATE_FORMAT) or pendulum.now()
        )

        return cls(
            id=obj["nodeID"],
            metadata=Metadata(timestamp, timestamp),
            text=utils.parse(obj["text"], nlp),
        )

    def to_aif(self) -> aif.Node:
        """Export AtomNode object into AIF Node object."""
        return {
            "nodeID": self._id,
            "timestamp": dt.to_format(self.metadata.updated, aif.DATE_FORMAT),
            "text": self.plain_text,
            "type": "I",
        }

    @classmethod
    def from_ova(
        cls,
        obj: ova.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> AtomNode:
        """Generate AtomNode object from OVA Node object."""
        timestamp = dt.from_format(obj.get("date"), ova.DATE_FORMAT) or pendulum.now()

        return cls(
            id=str(obj["id"]),
            metadata=Metadata(timestamp, timestamp),
            text=utils.parse(obj["text"], nlp),
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
    ) -> AtomNode:
        """Generate AtomNode object from PROTOBUF Node object."""
        return cls(
            utils.parse(obj.atom.text, nlp),
            reference_class.from_protobuf(obj.atom.reference, resources, nlp),
            participants.get(obj.atom.participant),
            Metadata.from_protobuf(obj.metadata),
            dict(obj.userdata.items()),
            id=id,
        )

    def to_protobuf(self) -> graph_pb2.Node:
        """Export AtomNode object into PROTOBUF Node object."""
        obj = graph_pb2.Node(metadata=self.metadata.to_protobuf())
        obj.userdata.update(self.userdata)

        obj.atom.text = self.plain_text

        if reference := self.reference:
            obj.atom.reference.CopyFrom(reference.to_protobuf())

        if participant := self.participant:
            obj.atom.participant = participant.id

        return obj

    def to_nx(
        self,
        g: nx.DiGraph,
        attrs: t.Optional[t.MutableMapping[str, t.Callable[[AtomNode], t.Any]]] = None,
    ) -> None:
        """Submethod used to export Graph object g into NX Graph format."""
        if attrs is None:
            attrs = {}

        if "label" not in attrs:
            attrs["label"] = lambda x: x.label

        g.add_node(self._id, **{key: func(self) for key, func in attrs.items()})

    def color(self, major_claim: bool) -> Color:
        """Get the color for rendering the node."""
        if major_claim:
            return Color(bg="#0D47A1")

        return Color(bg="#2196F3")


class SchemeNode(Node):
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

    @classmethod
    def from_sadface(
        cls,
        obj: sadface.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> SchemeNode:
        """Generate SchemeNode object from SADFace Node object."""
        name = None

        if obj["name"] == "support":
            name = Support.DEFAULT
        elif obj["name"] == "attack":
            name = Attack.DEFAULT
        elif obj["name"] == "rephrase":
            name = Rephrase.DEFAULT
        elif obj["name"] == "preference":
            name = Preference.DEFAULT

        timestamp = pendulum.now()

        return cls(
            id=obj["id"],
            userdata=obj["metadata"],
            metadata=Metadata(timestamp, timestamp),
            scheme=name,
        )

    @classmethod
    def from_aml(
        cls,
        obj: et.Element,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
        refutation=False,
    ) -> SchemeNode:
        """Generate SchemeNode object from AML Node format. obj is a AML "PROP" element."""

        # get id of PROP
        if "identifier" in obj.attrib:
            id = obj.get("identifier")
        else:
            id = None

        # read owners of PROP
        owner_list = obj.findall("OWNER")
        owners_lst = []
        if not owner_list:
            # if not empty, do something
            for owner in owner_list:
                owners_lst.append(owner.get("name"))
            owners = {"owners": ", ".join(owners_lst)}
        else:
            owners = {}

        # create timestamp
        timestamp = pendulum.now()

        # get scheme name
        scheme = None
        if refutation:
            scheme = Attack.DEFAULT
        else:
            inscheme = obj.find("INSCHEME")
            if inscheme is not None:  # if INSCHEME element is available
                # get scheme
                aml_scheme = inscheme.attrib["scheme"]
                contains_scheme = False
                for supp_scheme in Support:
                    if supp_scheme.value.lower().replace(
                        " ", ""
                    ) in aml_scheme.lower().replace(" ", ""):
                        scheme = supp_scheme
                        contains_scheme = True
                        break
                if not contains_scheme:
                    scheme = Support.DEFAULT
            else:  # if INSCHEME element is not available
                scheme = Support.DEFAULT

        return cls(
            metadata=Metadata(timestamp, timestamp),
            scheme=scheme,
            userdata=owners,
            id=id,
        )

    @classmethod
    def from_aif(
        cls,
        obj: aif.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> t.Optional[SchemeNode]:
        """Generate SchemeNode object from AIF Node object."""

        aif_type = obj["type"]
        aif_scheme: str = obj.get("scheme", obj["text"])

        if aif_type in aif2scheme:
            scheme = aif2scheme[t.cast(aif.SchemeType, aif_type)]

            # TODO: Handle formatting like capitalization, spaces, underscores, etc.
            # TODO: Araucaria does not use spaces between scheme names
            # aif_scheme = re.sub("([A-Z])", r" \1", aif_scheme)
            if scheme and (found_scheme := text2scheme[type(scheme)].get(aif_scheme)):
                scheme = found_scheme

            timestamp = (
                dt.from_format(obj.get("timestamp"), aif.DATE_FORMAT) or pendulum.now()
            )

            return cls(
                id=obj["nodeID"],
                metadata=Metadata(timestamp, timestamp),
                scheme=scheme,
            )

        return None

    def to_aif(self) -> aif.Node:
        """Export SchemeNode object into AIF Node object."""

        return {
            "nodeID": self._id,
            "timestamp": dt.to_format(self.metadata.updated, aif.DATE_FORMAT),
            "text": self.scheme.value if self.scheme else NO_SCHEME_LABEL,
            "type": scheme2aif[type(self.scheme)] if self.scheme else "",
        }

    @classmethod
    def from_ova(
        cls,
        obj: ova.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> t.Optional[SchemeNode]:
        """Generate SchemeNode object from OVA Node object."""

        ova_type = obj["type"]
        ova_scheme = obj["text"]

        if ova_type in aif2scheme:
            scheme = aif2scheme[t.cast(aif.SchemeType, ova_type)]

            if scheme and (found_scheme := text2scheme[type(scheme)].get(ova_scheme)):
                scheme = found_scheme

            premise_descriptors = [
                str(node_id)
                for description, node_id in obj["descriptors"].items()
                if not description.lower().startswith("s_conclusion")
            ]

            timestamp = (
                dt.from_format(obj.get("date"), ova.DATE_FORMAT) or pendulum.now()
            )

            return cls(
                id=str(obj["id"]),
                metadata=Metadata(timestamp, timestamp),
                scheme=scheme,
                premise_descriptors=premise_descriptors,
            )

        return None

    @classmethod
    def from_argdown_json(
        cls,
        obj: argdown_json.Node,
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> SchemeNode:
        # Currently not used
        return SchemeNode()

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

        scheme_type = obj.scheme.WhichOneof("type")
        scheme = None

        if scheme_type is None:
            scheme = None
        elif scheme_type == "support":
            scheme = protobuf2support[obj.scheme.support]
        elif scheme_type == "attack":
            scheme = protobuf2attack[obj.scheme.attack]
        elif scheme_type == "rephrase":
            scheme = protobuf2rephrase[obj.scheme.rephrase]
        elif scheme_type == "preference":
            scheme = protobuf2preference[obj.scheme.preference]

        return cls(
            scheme,
            list(obj.scheme.premise_descriptors),
            Metadata.from_protobuf(obj.metadata),
            dict(obj.userdata.items()),
            id=id,
        )

    def to_protobuf(self) -> graph_pb2.Node:
        """Export SchemeNode object into PROTOBUF Node object."""
        obj = graph_pb2.Node(metadata=self.metadata.to_protobuf())
        obj.userdata.update(self.userdata)

        if isinstance(self.scheme, Support):
            obj.scheme.support = support2protobuf[self.scheme]
        elif isinstance(self.scheme, Attack):
            obj.scheme.attack = attack2protobuf[self.scheme]
        elif isinstance(self.scheme, Rephrase):
            obj.scheme.rephrase = rephrase2protobuf[self.scheme]
        elif isinstance(self.scheme, Preference):
            obj.scheme.preference = preference2protobuf[self.scheme]

        obj.scheme.premise_descriptors.extend(self.premise_descriptors)

        return obj

    def to_nx(
        self,
        g: nx.DiGraph,
        attrs: t.Optional[
            t.MutableMapping[str, t.Callable[[SchemeNode], t.Any]]
        ] = None,
    ) -> None:
        """Submethod used to export Graph object g into NX Graph format."""

        if attrs is None:
            attrs = {}

        if "label" not in attrs:
            attrs["label"] = lambda x: x.label

        g.add_node(self._id, **{key: func(self) for key, func in attrs.items()})

    def color(self, major_claim: bool) -> Color:
        """Get the color used in OVA based on `category`."""

        return scheme2color[type(self.scheme)] if self.scheme else Color(bg="#009688")

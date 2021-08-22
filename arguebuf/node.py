from __future__ import absolute_import, annotations

import textwrap
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import graphviz as gv
import networkx as nx
from arg_services.graph.v1 import graph_pb2

from arguebuf import dt, utils
from arguebuf.data import Anchor, Metadata, Resource, Userdata


class SchemeType(Enum):
    SUPPORT = "RA"
    ATTACK = "CA"
    REPHRASE = "MA"
    TRANSITION = "TA"
    PREFERENCE = "PA"
    ASSERTION = "YA"


protobuf2scheme = {
    graph_pb2.SchemeType.SCHEME_TYPE_SUPPORT: SchemeType.SUPPORT,
    graph_pb2.SchemeType.SCHEME_TYPE_ATTACK: SchemeType.ATTACK,
    graph_pb2.SchemeType.SCHEME_TYPE_REPHRASE: SchemeType.REPHRASE,
    graph_pb2.SchemeType.SCHEME_TYPE_TRANSITION: SchemeType.TRANSITION,
    graph_pb2.SchemeType.SCHEME_TYPE_PREFERENCE: SchemeType.PREFERENCE,
    graph_pb2.SchemeType.SCHEME_TYPE_ASSERTION: SchemeType.ASSERTION,
}

scheme2protobuf = {v: k for k, v in protobuf2scheme.items()}


scheme2text = {
    SchemeType.SUPPORT: "Support",
    SchemeType.ATTACK: "Attack",
    SchemeType.REPHRASE: "Rephrase",
    SchemeType.TRANSITION: "Transition",
    SchemeType.PREFERENCE: "Preference",
    SchemeType.ASSERTION: "Assertion",
}


@dataclass
class ColorMapping:
    bg: str = "#ffffff"
    fg: str = "#000000"
    border: str = "#000000"


class Node(ABC):
    """Node in the AIF format."""

    _id: str
    userdata: Userdata
    _metadata: Metadata

    def __init__(
        self,
        id: str,
        metadata: t.Optional[Metadata] = None,
        userdata: t.Optional[Userdata] = None,
    ):
        self._id = id
        self._metadata = metadata or Metadata()
        self.userdata = userdata or {}

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
        "userdata",
        "_metadata",
        "text",
        "anchor",
    )

    text: t.Any
    anchor: t.Optional[Anchor]

    def __init__(
        self,
        id: str,
        text: t.Any,
        resource: t.Optional[Anchor] = None,
        metadata: t.Optional[Metadata] = None,
        userdata: t.Optional[Userdata] = None,
    ):
        super().__init__(id, metadata, userdata)
        self.text = text
        self.anchor = resource

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
        metadata_class: t.Type[Metadata],
        anchor_class: t.Type[Anchor],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> AtomNode:
        return cls(
            id,
            utils.parse(obj.atom.text, nlp),
            anchor_class.from_protobuf(obj.atom.anchor, resources, nlp),
            metadata_class.from_protobuf(obj.metadata),
            dict(obj.userdata.items()),
        )

    def to_protobuf(self) -> graph_pb2.Node:
        obj = graph_pb2.Node(metadata=self._metadata.to_protobuf())
        obj.userdata.update(self.userdata)

        obj.atom.text = self.plain_text

        if anchor := self.anchor:
            obj.atom.anchor.CopyFrom(anchor.to_protobuf())

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
        "userdata",
        "_metadata",
        "type",
        "argumentation_scheme",
        "descriptors",
    )

    type: SchemeType
    argumentation_scheme: t.Optional[str]
    descriptors: t.Dict[str, str]

    def __init__(
        self,
        id: str,
        type: SchemeType,
        argumentation_scheme: t.Optional[str] = None,
        descriptors: t.Optional[t.Mapping[str, str]] = None,
        metadata: t.Optional[Metadata] = None,
        userdata: t.Optional[Userdata] = None,
    ):
        super().__init__(id, metadata, userdata)
        self.type = type
        self.argumentation_scheme = argumentation_scheme
        self.descriptors = dict(descriptors) if descriptors else {}

    def __repr__(self):
        return utils.class_repr(
            self, [self._id, self.type.value, utils.xstr(self.argumentation_scheme)]
        )

    @classmethod
    def from_aif(
        cls,
        obj: t.Mapping[str, t.Any],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> Node:
        node = cls(
            **_from_aif(obj),
            type=SchemeType(obj["type"]),
        )
        text: str = obj["text"]

        if not text.startswith("Default "):
            node.argumentation_scheme = text

        return node

    def to_aif(self) -> t.Dict[str, t.Any]:
        return {
            **_to_aif(self),
            "text": scheme2text[self.type],
            "type": self.type.value,
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
            argumentation_scheme=obj["text"],
            type=SchemeType(obj["type"]),
            descriptors=descriptors,
        )

    @classmethod
    def from_protobuf(
        cls,
        id: str,
        obj: graph_pb2.Node,
        metadata_class: t.Type[Metadata],
        anchor_class: t.Type[Anchor],
        nlp: t.Optional[t.Callable[[str], t.Any]] = None,
    ) -> SchemeNode:
        return cls(
            id,
            protobuf2scheme[obj.scheme.type],
            obj.scheme.argumentation_scheme,
            dict(obj.scheme.descriptors.items()),
            metadata_class.from_protobuf(obj.metadata),
            dict(obj.userdata.items()),
        )

    def to_protobuf(self) -> graph_pb2.Node:
        obj = graph_pb2.Node(metadata=self._metadata.to_protobuf())
        obj.userdata.update(self.userdata)

        obj.scheme.type = scheme2protobuf[self.type]
        obj.scheme.descriptors.update(self.descriptors)

        if arg_scheme := self.argumentation_scheme:
            obj.scheme.argumentation_scheme = arg_scheme

        return obj

    def to_nx(self, g: nx.DiGraph) -> None:
        g.add_node(
            self._id,
            label=self.argumentation_scheme or self.type.value,
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
        label = self.argumentation_scheme or scheme2text[self.type]

        g.node(
            self._id,
            label=label.strip(),
            fontcolor=color.fg,
            fillcolor=color.bg,
            color=color.border,
        )


def _from_aif(obj: t.Mapping[str, t.Any]) -> t.Dict[str, t.Any]:
    timestamp = dt.from_aif(obj.get("timestamp"))
    metadata = Metadata(timestamp, timestamp) if timestamp else Metadata()

    return {"id": obj["nodeID"], "metadata": metadata}


def _to_aif(n: Node) -> t.Dict[str, t.Any]:
    return {
        "nodeID": n._id,
        "timestamp": dt.to_aif(n._metadata.updated),
    }


def _from_ova(obj: t.Mapping[str, t.Any]) -> t.Dict[str, t.Any]:
    timestamp = dt.from_ova(obj.get("date"))
    metadata = Metadata(timestamp, timestamp) if timestamp else Metadata()

    return {"id": str(obj["id"]), "metadata": metadata}

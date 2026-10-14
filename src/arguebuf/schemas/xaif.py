import typing as t

from arguebuf.schemas.aif import Graph as AifGraph
from arguebuf.schemas.aif import Id


class SchemeFulfillment(t.TypedDict):
    nodeID: Id
    schemeID: Id


class DescriptorFulfillment(t.TypedDict):
    nodeID: Id
    descriptorID: Id
    selectedID: Id | None


class Aif(AifGraph):
    schemefulfillments: list[SchemeFulfillment] | None
    descriptorfulfillments: t.NotRequired[list[DescriptorFulfillment] | None]
    cqdescriptorfulfillments: t.NotRequired[list[DescriptorFulfillment] | None]


class OvaNode(t.TypedDict):
    nodeID: Id
    visible: bool
    x: int
    y: int
    timestamp: str


class OvaEdge(t.TypedDict):
    fromID: Id
    toID: Id
    visible: bool


class Ova(t.TypedDict):
    firstname: str
    surname: str
    url: str
    nodes: list[OvaNode]
    edges: list[OvaEdge]


class Text(t.TypedDict, total=False):
    txt: str
    url: str


class Graph(t.TypedDict):
    AIF: Aif
    text: str | Text
    OVA: t.NotRequired[Ova]
    dialog: t.NotRequired[bool]

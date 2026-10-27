import typing as t

from arguebuf.schemas.aif import Graph as AifGraph
from arguebuf.schemas.aif import Id

__all__ = (
    "Aif",
    "DescriptorFulfillment",
    "Graph",
    "Ova",
    "OvaEdge",
    "OvaNode",
    "SchemeFulfillment",
    "Text",
)


class SchemeFulfillment(t.TypedDict):
    nodeID: t.ReadOnly[Id]
    schemeID: t.ReadOnly[Id]


class DescriptorFulfillment(t.TypedDict):
    nodeID: t.ReadOnly[Id]
    descriptorID: t.ReadOnly[Id]
    selectedID: t.ReadOnly[Id | None]


class Aif(AifGraph):
    schemefulfillments: t.ReadOnly[list[SchemeFulfillment] | None]
    descriptorfulfillments: t.NotRequired[
        t.ReadOnly[list[DescriptorFulfillment] | None]
    ]
    cqdescriptorfulfillments: t.NotRequired[
        t.ReadOnly[list[DescriptorFulfillment] | None]
    ]


class OvaNode(t.TypedDict):
    nodeID: t.ReadOnly[Id]
    visible: t.ReadOnly[bool]
    x: t.ReadOnly[int]
    y: t.ReadOnly[int]
    timestamp: t.ReadOnly[str]


class OvaEdge(t.TypedDict):
    fromID: t.ReadOnly[Id]
    toID: t.ReadOnly[Id]
    visible: t.ReadOnly[bool]


class Ova(t.TypedDict):
    firstname: t.ReadOnly[str]
    surname: t.ReadOnly[str]
    url: t.ReadOnly[str]
    nodes: t.ReadOnly[list[OvaNode]]
    edges: t.ReadOnly[list[OvaEdge]]


class Text(t.TypedDict, total=False):
    txt: t.ReadOnly[str]
    url: t.ReadOnly[str]


class Graph(t.TypedDict):
    AIF: t.ReadOnly[Aif]
    # a missing text yields no resource
    text: t.NotRequired[t.ReadOnly[str | Text | None]]
    OVA: t.NotRequired[t.ReadOnly[Ova]]
    dialog: t.NotRequired[t.ReadOnly[bool]]

import typing as t

NodeType = t.Literal["RA", "CA", "MA", "PA", "", "I", "TA", "YA", "L"]


class AifNode(t.TypedDict):
    nodeID: str
    text: str
    type: NodeType


class AifEdge(t.TypedDict):
    edgeID: str | int
    fromID: str
    toID: str


class AifSchemeFulfillment(t.TypedDict):
    nodeID: str
    schemeID: str


class AifLocution(t.TypedDict):
    nodeID: str
    schemeID: str


class AifParticipant(t.TypedDict):
    participantID: int
    firstname: str
    surname: str


class Aif(t.TypedDict):
    nodes: list[AifNode]
    edges: list[AifEdge]
    schemefulfillments: list[AifSchemeFulfillment]
    locutions: list[AifLocution]
    participants: list[AifParticipant]


class OvaNode(t.TypedDict):
    nodeID: str
    visible: bool
    x: int
    y: int
    timestamp: str


class OvaEdge(t.TypedDict):
    fromID: str
    toID: str
    visible: bool


class Ova(t.TypedDict):
    firstname: str
    surname: str
    url: str
    nodes: list[OvaNode]
    edges: list[OvaEdge]


class Graph(t.TypedDict):
    AIF: Aif
    OVA: Ova
    text: str
    # dialog: bool

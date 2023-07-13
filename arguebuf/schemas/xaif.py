import typing as t

NodeType = t.Literal["RA", "CA", "MA", "PA", "", "I", "TA", "YA", "L"]


class AifNode(t.TypedDict):
    nodeID: str
    text: str
    type: NodeType


class AifEdge(t.TypedDict):
    edgeID: t.Union[str, int]
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
    nodes: t.List[AifNode]
    edges: t.List[AifEdge]
    schemefulfillments: t.List[AifSchemeFulfillment]
    locutions: t.List[AifLocution]
    participants: t.List[AifParticipant]


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
    nodes: t.List[OvaNode]
    edges: t.List[OvaEdge]


class Graph(t.TypedDict):
    AIF: Aif
    OVA: Ova
    text: str
    # dialog: bool

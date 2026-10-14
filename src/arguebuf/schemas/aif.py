import typing as t

type SchemeType = t.Literal["RA", "CA", "MA", "PA", ""]
type DialogType = t.Literal["L", "TA", "YA"]
type NodeType = SchemeType | DialogType | t.Literal["I"]
# AIFdb uses strings, xAIF tools mostly integers
type Id = str | int
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DIALOG_TYPES: frozenset[str] = frozenset(("L", "TA", "YA"))


class Node(t.TypedDict):
    nodeID: Id
    text: str
    type: NodeType
    timestamp: t.NotRequired[str]
    scheme: t.NotRequired[str]
    schemeID: t.NotRequired[Id]


class Edge(t.TypedDict):
    edgeID: Id
    fromID: Id
    toID: Id
    formEdgeID: t.NotRequired[Id | None]


class Locution(t.TypedDict):
    nodeID: Id
    personID: Id
    timestamp: t.NotRequired[str]
    start: t.NotRequired[str | None]
    end: t.NotRequired[str | None]
    source: t.NotRequired[str | None]


class Participant(t.TypedDict):
    participantID: Id
    firstname: str
    surname: str


class Graph(t.TypedDict):
    nodes: list[Node]
    edges: list[Edge]
    locutions: list[Locution] | None
    # only part of xAIF, AIFdb stores the participants separately
    participants: t.NotRequired[list[Participant] | None]

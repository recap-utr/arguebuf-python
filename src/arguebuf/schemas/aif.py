import typing as t

__all__ = (
    "DATE_FORMAT",
    "DIALOG_TYPES",
    "DialogType",
    "Edge",
    "Graph",
    "Id",
    "Locution",
    "Node",
    "NodeType",
    "Participant",
    "SchemeType",
)

type SchemeType = t.Literal["RA", "CA", "MA", "PA", ""]
type DialogType = t.Literal["L", "TA", "YA"]
type NodeType = SchemeType | DialogType | t.Literal["I"]
# AIFdb uses strings, xAIF tools mostly integers, loaders convert them to strings
type Id = str | int
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DIALOG_TYPES: frozenset[str] = frozenset(("L", "TA", "YA"))


class Node(t.TypedDict):
    nodeID: t.ReadOnly[Id]
    text: t.ReadOnly[str]
    type: t.ReadOnly[NodeType]
    timestamp: t.NotRequired[str]
    scheme: t.NotRequired[t.ReadOnly[str | None]]
    schemeID: t.NotRequired[t.ReadOnly[Id]]


class Edge(t.TypedDict):
    edgeID: t.ReadOnly[Id]
    fromID: t.ReadOnly[Id]
    toID: t.ReadOnly[Id]
    formEdgeID: t.NotRequired[t.ReadOnly[Id | None]]


class Locution(t.TypedDict):
    nodeID: t.ReadOnly[Id]
    personID: t.ReadOnly[Id]
    timestamp: t.NotRequired[t.ReadOnly[str]]
    start: t.NotRequired[t.ReadOnly[str | None]]
    end: t.NotRequired[t.ReadOnly[str | None]]
    source: t.NotRequired[t.ReadOnly[str | None]]


class Participant(t.TypedDict):
    participantID: t.ReadOnly[Id]
    firstname: t.NotRequired[t.ReadOnly[str]]
    surname: t.NotRequired[t.ReadOnly[str]]


class Graph(t.TypedDict):
    nodes: t.ReadOnly[list[Node]]
    edges: t.ReadOnly[list[Edge]]
    locutions: t.NotRequired[t.ReadOnly[list[Locution] | None]]
    # only part of xAIF, AIFdb stores the participants separately
    participants: t.NotRequired[t.ReadOnly[list[Participant] | None]]
